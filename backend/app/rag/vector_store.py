from __future__ import annotations

import json
import math

from sqlalchemy import and_, delete, select, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.db.models.document_chunk import DocumentChunk
from app.db.session import SessionLocal


class PGVectorStore:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def add_chunks(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        del ids
        session, should_close = self._get_session()
        try:
            rows = []
            for content, embedding, metadata in zip(documents, embeddings, metadatas, strict=False):
                rows.append(
                    DocumentChunk(
                        user_id=int(metadata["user_id"]),
                        knowledge_base_id=int(metadata["knowledge_base_id"]),
                        document_id=int(metadata["document_id"]),
                        chunk_index=int(metadata["chunk_index"]),
                        content=content,
                        embedding=[float(item) for item in embedding],
                        file_name=str(metadata.get("file_name", "")),
                        file_type=str(metadata.get("file_type", "")),
                        document_kind=str(metadata.get("document_kind", "general") or "general"),
                        section_title=self._optional_text(metadata.get("section_title")),
                        page_no=self._optional_int(metadata.get("page_no")),
                        section_index=self._optional_int(metadata.get("section_index")),
                        content_type_hint=self._optional_text(metadata.get("content_type_hint")),
                        starts_with_question=bool(metadata.get("starts_with_question", False)),
                    )
                )
            session.add_all(rows)
            session.commit()
        finally:
            if should_close:
                session.close()

    def delete_document_chunks(self, document_id: int) -> None:
        session, should_close = self._get_session()
        try:
            session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            session.commit()
        finally:
            if should_close:
                session.close()

    def get_document_chunks(self, user_id: int, document_id: int) -> dict:
        session, should_close = self._get_session()
        try:
            stmt = (
                select(DocumentChunk)
                .where(
                    DocumentChunk.user_id == user_id,
                    DocumentChunk.document_id == document_id,
                )
                .order_by(DocumentChunk.chunk_index.asc())
            )
            rows = list(session.scalars(stmt))
            return {
                "documents": [row.content for row in rows],
                "metadatas": [self._build_metadata(row) for row in rows],
            }
        finally:
            if should_close:
                session.close()

    def query(
        self,
        query_embedding: list[float],
        user_id: int,
        knowledge_base_id: int,
        top_k: int | None = None,
        extra_filters: list[dict[str, object]] | None = None,
    ) -> dict:
        session, should_close = self._get_session()
        try:
            limit = top_k or 4
            merged_filters = self._merge_filters(extra_filters)
            if session.bind and session.bind.dialect.name == "postgresql":
                rows = self._query_postgres(
                    session=session,
                    query_embedding=query_embedding,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    top_k=limit,
                    extra_filters=merged_filters,
                )
            else:
                rows = self._query_python_fallback(
                    session=session,
                    query_embedding=query_embedding,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    top_k=limit,
                    extra_filters=merged_filters,
                )

            return {
                "documents": [[row.content for row, _ in rows]],
                "metadatas": [[self._build_metadata(row) for row, _ in rows]],
                "distances": [[distance for _, distance in rows]],
            }
        finally:
            if should_close:
                session.close()

    def count_chunks(self) -> int:
        session, should_close = self._get_session()
        try:
            try:
                return len(list(session.scalars(select(DocumentChunk.id))))
            except (OperationalError, ProgrammingError):
                return 0
        finally:
            if should_close:
                session.close()

    def list_chunk_metadatas(self, *, limit: int = 10) -> list[dict]:
        session, should_close = self._get_session()
        try:
            stmt = select(DocumentChunk).order_by(DocumentChunk.id.desc()).limit(limit)
            try:
                return [self._build_metadata(row) for row in session.scalars(stmt)]
            except (OperationalError, ProgrammingError):
                return []
        finally:
            if should_close:
                session.close()

    def _query_postgres(
        self,
        *,
        session: Session,
        query_embedding: list[float],
        user_id: int,
        knowledge_base_id: int,
        top_k: int,
        extra_filters: dict[str, object],
    ) -> list[tuple[DocumentChunk, float]]:
        where_clauses = [
            "user_id = :user_id",
            "knowledge_base_id = :knowledge_base_id",
        ]
        params: dict[str, object] = {
            "user_id": user_id,
            "knowledge_base_id": knowledge_base_id,
            "query_embedding": self._vector_literal(query_embedding),
            "top_k": top_k,
        }
        for index, (key, value) in enumerate(sorted(extra_filters.items())):
            param_name = f"filter_{index}"
            where_clauses.append(f"{key} = :{param_name}")
            params[param_name] = value

        sql = text(
            f"""
            SELECT id, (embedding <=> CAST(:query_embedding AS vector)) AS distance
            FROM document_chunks
            WHERE {' AND '.join(where_clauses)}
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """
        )
        scored_ids = session.execute(sql, params).all()
        if not scored_ids:
            return []

        ids = [int(row.id) for row in scored_ids]
        stmt = select(DocumentChunk).where(DocumentChunk.id.in_(ids))
        chunk_map = {row.id: row for row in session.scalars(stmt)}
        return [(chunk_map[int(row.id)], float(row.distance)) for row in scored_ids if int(row.id) in chunk_map]

    def _query_python_fallback(
        self,
        *,
        session: Session,
        query_embedding: list[float],
        user_id: int,
        knowledge_base_id: int,
        top_k: int,
        extra_filters: dict[str, object],
    ) -> list[tuple[DocumentChunk, float]]:
        conditions = [
            DocumentChunk.user_id == user_id,
            DocumentChunk.knowledge_base_id == knowledge_base_id,
        ]
        for key, value in extra_filters.items():
            conditions.append(getattr(DocumentChunk, key) == value)
        stmt = select(DocumentChunk).where(and_(*conditions))
        rows = list(session.scalars(stmt))
        scored = [
            (row, self._cosine_distance(query_embedding, row.embedding))
            for row in rows
        ]
        scored.sort(key=lambda item: item[1])
        return scored[:top_k]

    def _get_session(self) -> tuple[Session, bool]:
        if self.db is not None:
            return self.db, False
        return SessionLocal(), True

    def _build_metadata(self, row: DocumentChunk) -> dict:
        return {
            "user_id": row.user_id,
            "knowledge_base_id": row.knowledge_base_id,
            "document_id": row.document_id,
            "file_name": row.file_name,
            "file_type": row.file_type,
            "document_kind": row.document_kind,
            "chunk_index": row.chunk_index,
            "section_title": row.section_title or "",
            "page_no": row.page_no or 0,
            "section_index": row.section_index or 0,
            "content_type_hint": row.content_type_hint or "general",
            "starts_with_question": bool(row.starts_with_question),
        }

    def _merge_filters(self, extra_filters: list[dict[str, object]] | None) -> dict[str, object]:
        merged: dict[str, object] = {}
        for item in extra_filters or []:
            merged.update(item)
        return merged

    def _vector_literal(self, embedding: list[float]) -> str:
        return json.dumps([float(item) for item in embedding], ensure_ascii=False)

    def _cosine_distance(self, left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 1.0
        dot = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 1.0
        similarity = dot / (left_norm * right_norm)
        return 1.0 - similarity

    def _optional_text(self, value: object) -> str | None:
        if value is None:
            return None
        text_value = str(value).strip()
        return text_value or None

    def _optional_int(self, value: object) -> int | None:
        if value in (None, "", 0):
            return None
        return int(value)


VectorStore = PGVectorStore
