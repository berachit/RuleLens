import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Represents an academic regulation source document."""
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)  # pdf, markdown, table
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(64), default="2026", nullable=False)

    # Upload tracking
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # path on disk
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    upload_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, indexed, failed

    pages: Mapped[List["Page"]] = relationship("Page", back_populates="document", cascade="all, delete-orphan")


class Page(Base, TimestampMixin):
    """Represents a discrete page or logical unit within a document."""
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(128), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    page_image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="pages")
    chunks: Mapped[List["Chunk"]] = relationship("Chunk", back_populates="page", cascade="all, delete-orphan")


class Chunk(Base, TimestampMixin):
    """Represents an evidence chunk with provenance and vector embedding."""
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id: Mapped[str] = mapped_column(String(128), ForeignKey("pages.id", ondelete="CASCADE"), index=True, nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(384), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    page: Mapped["Page"] = relationship("Page", back_populates="chunks")


class Conversation(Base, TimestampMixin):
    """Represents a user chat session."""
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    """Represents a turn in conversation with grounding state and citations."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # ANSWERED, NOT_COVERED, CONFLICT
    sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class RetrievalRecord(Base, TimestampMixin):
    """Debug and observability record for retrieval operations."""
    __tablename__ = "retrieval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
