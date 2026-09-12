from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.rag.engine import rag_engine

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    query: str = Field(..., description="The user question regarding university regulations")
    conversation_id: Optional[str] = Field(None, description="Optional persistent conversation session ID")


class SourceMetadata(BaseModel):
    document: str
    page: int
    section: Optional[str] = None
    chunk_id: str
    text_snippet: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    status: str  # ANSWERED, NOT_COVERED, CONFLICT
    answer: str
    sources: List[SourceMetadata] = []
    conflict_details: Optional[Dict[str, Any]] = None
    suggested_questions: List[str] = []


@router.post("/chat", response_model=ChatResponse)
async def post_chat(req: ChatRequest):
    """Processes an academic regulation question through the verifiable RAG engine."""
    result = await rag_engine.process_query(req.query, req.conversation_id)
    return ChatResponse(
        conversation_id=result["conversation_id"],
        status=result["status"],
        answer=result["answer"],
        sources=[SourceMetadata(**s) for s in result["sources"]],
        conflict_details=result["conflict_details"],
        suggested_questions=result.get("suggested_questions", []),
    )


@router.post("/chat/stream")
async def post_chat_stream(req: ChatRequest):
    """Streams the verified grounded answer following evidence analysis."""
    async def event_generator():
        async for chunk in rag_engine.stream_query(req.query, req.conversation_id):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")
