import uuid
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.services.retrieval import retrieval_service
from app.services.rag.sufficiency import analyze_evidence_sufficiency
from app.services.rag.citation_validator import validate_citations
from app.services.llm.factory import get_llm_provider

logger = logging.getLogger("rulelens.rag")

SYSTEM_PROMPT = """You are RuleLens, an authoritative and verifiable university academic regulations assistant.
Your sole mission is to explain academic regulations based strictly on the provided retrieved excerpts.

CRITICAL NON-NEGOTIABLES:
1. The provided regulation excerpts are your SOLE authority.
2. Never answer from prior knowledge, external university practices, or general assumptions.
3. If the excerpts do not contain the answer, you must state clearly that the regulations do not cover it.
4. If the excerpts contradict each other, expose both sides clearly without favoring either.
5. Never invent or alter citations, sections, or numbers.

FORMATTING & WRITING GUIDELINES:
- Deliver clear, well-structured prose with clean paragraphs, bullet points, and bold terms where helpful.
- Avoid using commas before 'and' or 'or' (no Oxford commas; write 'A, B and C', never 'A, B, and C').
- Do not use em dashes (long hyphens like '—'); use standard punctuation like parentheses, commas or clean bullet points instead.
- Avoid heavy jargon like 'corpus' or 'provenance'; use plain, clear language like 'university rules' or 'official sources'.
- When referencing provisions, cite naturally by document name, chapter, section or page (e.g. *Chapter 15, Section 15.1* or *academic_regulations.md, Page 61*). Avoid awkward raw strings like '【Excerpt 3】'.
- Maintain a direct, helpful, polite tone."""


class RAGEngine:
    """End-to-end verifiable RAG pipeline executing:
    Retrieval -> Evidence Sufficiency -> Contradiction Check -> Grounded Generation -> Citation Validation.
    """

    def __init__(self):
        self.llm = get_llm_provider()

    async def process_query(self, query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Executes full grounding workflow for a user query."""
        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:10]}"

        # 1. Retrieval
        candidate_chunks = retrieval_service.search(query, top_k=12, min_similarity=0.35)

        # 2. Sufficiency & Contradiction Analysis
        status, conflict_details, summary = analyze_evidence_sufficiency(query, candidate_chunks)

        # 3. Handle NOT_COVERED
        if status == "NOT_COVERED":
            return {
                "conversation_id": conv_id,
                "status": "NOT_COVERED",
                "answer": (
                    f"The official regulations for Demo University 2026 do not mention '{query}'. "
                    "RuleLens only provides verified rules and does not make assumptions."
                ),
                "sources": [],
                "conflict_details": None,
                "suggested_questions": [
                    "What is the minimum cumulative GPA required to maintain Good Academic Standing?",
                    "What is the minimum attendance required to appear for final examinations?",
                    "What is the deadline for late course drop with full fee refund?",
                ],
            }

        # 4. Handle CONFLICT
        if status == "CONFLICT":
            validated_sources = validate_citations(candidate_chunks, max_citations=4)
            conflict_msg = (
                f"The university rules have conflicting statements on this matter.\n\n"
                f"* {conflict_details['provision_a']}\n"
                f"* {conflict_details['provision_b']}\n\n"
                f"Summary: {conflict_details['explanation']}\n\n"
                "Both rules are shown above so you can compare the original sources."
            )
            return {
                "conversation_id": conv_id,
                "status": "CONFLICT",
                "answer": conflict_msg,
                "sources": validated_sources,
                "conflict_details": conflict_details,
                "suggested_questions": [
                    "What does Chapter 7 of Academic Regulations say about attendance?",
                    "What does the Student Handbook specify regarding this requirement?",
                    "Which authority resolves contradictory policies?",
                ],
            }

        # 5. Handle ANSWERED
        validated_sources = validate_citations(candidate_chunks, max_citations=4)

        # Construct grounded context
        context_parts = []
        for i, chunk in enumerate(candidate_chunks[:4], start=1):
            context_parts.append(
                f"[Excerpt {i}] Document: {chunk['document_name']} | Page: {chunk['page_number']} | Section: {chunk['section']}\n"
                f"{chunk['text']}\n"
            )
        context_str = "\n".join(context_parts)

        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nAUTHORITATIVE EVIDENCE:\n{context_str}"},
            {"role": "user", "content": f"Question: {query}\n\nPlease provide an accurate, grounded answer citing the evidence above."},
        ]

        try:
            answer = await self.llm.generate(messages)
        except Exception as e:
            logger.warning(f"LLM generation warning: {e}. Falling back to deterministic summary.")
            # Deterministic fallback text directly from top chunk
            top = candidate_chunks[0]
            answer = f"According to {top['document_name']} (Page {top['page_number']}, {top['section']}):\n\n{top['text'][:350]}..."

        # Reconcile status: If the generated answer itself explicitly declares that the regulations
        # do not cover or contain the requested topic, set status to NOT_COVERED
        ans_lower = answer.lower()
        if any(phrase in ans_lower for phrase in [
            "do not contain any definition",
            "do not cover this",
            "do not mention",
            "does not mention",
            "not covered in the",
            "no regulation in the excerpts",
            "do not specify a general",
        ]):
            final_status = "NOT_COVERED"
            final_sources = []
        else:
            final_status = "ANSWERED"
            final_sources = validated_sources

        # Generate contextual suggested follow-up questions
        suggested: List[str] = []
        if final_status == "ANSWERED":
            # Extract relevant follow-ups based on query context
            q_lower = query.lower()
            if "grade" in q_lower or "gpa" in q_lower or "standing" in q_lower or "academic" in q_lower:
                suggested = [
                    "What happens if a student is placed on academic probation?",
                    "What is the time limit for lodging a grade appeal?",
                    "How is SGPA and CGPA calculated?",
                ]
            elif "attendance" in q_lower or "absent" in q_lower:
                suggested = [
                    "What are valid grounds for an excused absence?",
                    "What happens if absences exceed 25 percent of classes?",
                    "Does the student handbook require 80 percent attendance?",
                ]
            elif "fee" in q_lower or "refund" in q_lower or "drop" in q_lower:
                suggested = [
                    "What is the fee refund policy if a course is dropped in Week 3?",
                    "What is the late registration penalty fee?",
                    "Is laboratory fee refundable after classes start?",
                ]
            else:
                suggested = [
                    "What is the minimum cumulative GPA for Good Academic Standing?",
                    "What is the minimum attendance required for final examinations?",
                    "How many weeks does a student have to resolve an Incomplete grade?",
                ]
        elif final_status == "NOT_COVERED":
            suggested = [
                "What is the minimum cumulative GPA required to maintain Good Academic Standing?",
                "What is the minimum attendance required to appear for final examinations?",
                "What is the deadline for late course drop with full fee refund?",
            ]
        elif final_status == "CONFLICT":
            suggested = [
                "What does Chapter 7 of Academic Regulations say about attendance?",
                "What does the Student Handbook specify regarding this requirement?",
                "Which authority resolves contradictory policies?",
            ]

        return {
            "conversation_id": conv_id,
            "status": final_status,
            "answer": answer,
            "sources": final_sources,
            "conflict_details": None,
            "suggested_questions": suggested,
        }

    async def stream_query(self, query: str, conversation_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Streams the response tokens following evidence verification."""
        res = await self.process_query(query, conversation_id)
        # Stream response
        words = res["answer"].split(" ")
        for word in words:
            yield word + " "


rag_engine = RAGEngine()
