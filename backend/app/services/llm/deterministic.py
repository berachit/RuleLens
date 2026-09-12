import asyncio
import re
from typing import List, Dict, Any, AsyncGenerator
from app.services.llm.base import LLMProvider


class DeterministicEvidenceProvider(LLMProvider):
    """Fallback provider that formulates answers strictly grounded in provided context."""

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

        # Conflict response
        if "CONFLICT:" in user_msg:
            lines = user_msg.split("\n")
            conflict_line = next((l for l in lines if l.startswith("CONFLICT:")), "")
            return (
                f"The academic regulations corpus presents directly contradictory rules on this matter: {conflict_line.replace('CONFLICT:', '').strip()}. "
                "RuleLens cannot arbitrarily decide between competing provisions. Both official provisions and their cited locations are presented below for institutional review."
            )

        # Refusal response
        if "NOT_COVERED:" in user_msg:
            return (
                "The academic regulations corpus for Demo University 2026 does not contain sufficient evidence to answer this question. "
                "Per RuleLens non-negotiable constraints, answers must not be fabricated or inferred from external general knowledge."
            )

        # Extract authoritative evidence excerpts from system prompt
        if "AUTHORITATIVE EVIDENCE:" in system_msg:
            evidence_block = system_msg.split("AUTHORITATIVE EVIDENCE:\n", 1)[1]
            excerpts = evidence_block.split("\n[Excerpt ")
            if excerpts:
                top_excerpt = excerpts[0].replace("[Excerpt 1] ", "")
                # Extract first clean sentences of evidence
                lines = [line.strip() for line in top_excerpt.split("\n") if line.strip() and not line.startswith("Document:")]
                summary_text = " ".join(lines[:4])
                return (
                    f"Based on the verified evidence from Demo University Academic Regulations 2026:\n\n"
                    f"{summary_text}"
                )

        return (
            "Based on the verified evidence from Demo University Academic & Student Regulations 2026, "
            "the official policy is documented in the retrieved citations below. Every claim is strictly grounded in the authoritative text."
        )

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        full_text = await self.generate(messages, **kwargs)
        for word in full_text.split(" "):
            yield word + " "
            await asyncio.sleep(0.01)
