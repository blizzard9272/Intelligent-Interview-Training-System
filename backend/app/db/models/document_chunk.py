from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.mixins import TimestampMixin
from app.rag.pgvector_sql import PGVector


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_chunk"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    knowledge_base_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer(), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON().with_variant(PGVector(1024), "postgresql"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_no: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    section_index: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    content_type_hint: Mapped[str | None] = mapped_column(String(40), nullable=True)
    starts_with_question: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    document = relationship("Document", back_populates="chunks")
    user = relationship("User")
    knowledge_base = relationship("KnowledgeBase")
