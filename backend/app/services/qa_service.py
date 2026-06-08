import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.qa import QAMessage, QASession
from app.rag.factory import generate_answer, get_embedding_provider
from app.rag.query_router import build_query_plan, classify_query_route
from app.rag.vector_store import ChromaVectorStore
from app.schemas.qa import AskRequest, AskResponse, QAReference, QAMessageResponse, QASessionDetailResponse
from app.utils import get_rag_config

logger = logging.getLogger("app.services.qa")


class QAService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = None
        self.vector_store = None

    def ask(self, user_id: int, payload: AskRequest) -> AskResponse:
        self._ensure_kb_access(user_id, payload.knowledge_base_id)
        logger.info(
            "qa_request_started user_id=%s knowledge_base_id=%s session_id=%s question_length=%s",
            user_id,
            payload.knowledge_base_id,
            payload.session_id,
            len(payload.question),
        )

        session = self._get_or_create_session(user_id, payload.knowledge_base_id, payload.session_id, payload.question)
        references = self._retrieve_references(
            user_id=user_id,
            knowledge_base_id=payload.knowledge_base_id,
            question=payload.question,
        )
        answer = generate_answer(payload.question, references)

        user_message = QAMessage(session_id=session.id, role="user", content=payload.question, references_json=None)
        assistant_message = QAMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            references_json=[item.model_dump() for item in references],
        )
        self.db.add_all([user_message, assistant_message])
        self.db.commit()
        logger.info(
            "qa_request_completed user_id=%s knowledge_base_id=%s session_id=%s references=%s answer_length=%s",
            user_id,
            payload.knowledge_base_id,
            session.id,
            len(references),
            len(answer),
        )
        return AskResponse(session_id=session.id, answer=answer, references=references)

    def retrieve_references_for_question(
        self,
        *,
        user_id: int,
        knowledge_base_id: int,
        question: str,
    ) -> list[QAReference]:
        self._ensure_kb_access(user_id, knowledge_base_id)
        return self._retrieve_references(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            question=question,
        )

    def list_sessions(self, user_id: int) -> list[QASession]:
        stmt = select(QASession).where(QASession.user_id == user_id).order_by(QASession.updated_at.desc())
        return list(self.db.scalars(stmt))

    def get_session_detail(self, user_id: int, session_id: int) -> QASessionDetailResponse | None:
        stmt = select(QASession).where(QASession.id == session_id, QASession.user_id == user_id)
        session = self.db.scalar(stmt)
        if not session:
            return None
        messages = [
            QAMessageResponse(
                role=message.role,
                content=message.content,
                references_json=message.references_json,
            )
            for message in sorted(session.messages, key=lambda item: item.id)
        ]
        return QASessionDetailResponse(
            id=session.id,
            knowledge_base_id=session.knowledge_base_id,
            title=session.title,
            messages=messages,
        )

    def delete_session(self, user_id: int, session_id: int) -> bool:
        stmt = select(QASession).where(QASession.id == session_id, QASession.user_id == user_id)
        session = self.db.scalar(stmt)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        logger.info("qa_session_deleted user_id=%s session_id=%s", user_id, session_id)
        return True

    def _ensure_kb_access(self, user_id: int, knowledge_base_id: int) -> None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.user_id == user_id)
        kb = self.db.scalar(stmt)
        if not kb:
            raise ValueError("Knowledge base not found")

    def _retrieve_references(self, user_id: int, knowledge_base_id: int, question: str) -> list[QAReference]:
        rag_config = get_rag_config()
        embedding_provider = self._get_embedding_provider()
        vector_store = self._get_vector_store()
        query_embedding = embedding_provider.embed_query(question)
        route = classify_query_route(question)
        query_plan = build_query_plan(route)
        candidates: list[dict] = []
        seen_chunks: set[tuple[int, int]] = set()

        logger.info(
            "qa_retrieval_route_selected intent=%s knowledge_base_id=%s plan_steps=%s",
            route.intent,
            knowledge_base_id,
            len(query_plan),
        )

        for plan_filters in query_plan:
            result = vector_store.query(
                query_embedding=query_embedding,
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                top_k=rag_config.retrieval.top_k,
                extra_filters=[plan_filters] if plan_filters else None,
            )
            candidates.extend(
                self._collect_candidates_from_result(
                    result=result,
                    max_snippet_length=rag_config.answering.max_reference_snippet_length,
                    seen_chunks=seen_chunks,
                    plan_filters=plan_filters,
                )
            )
            if len(candidates) >= rag_config.retrieval.top_k:
                break

        if rag_config.retrieval.enable_rerank:
            candidates = self._rerank_candidates(question=question, route=route, candidates=candidates)

        references = [candidate["reference"] for candidate in candidates[: rag_config.retrieval.top_k]]
        logger.info(
            "qa_retrieval_route_completed intent=%s references=%s rerank=%s",
            route.intent,
            len(references),
            rag_config.retrieval.enable_rerank,
        )
        return references

    def _collect_candidates_from_result(
        self,
        *,
        result: dict,
        max_snippet_length: int,
        seen_chunks: set[tuple[int, int]],
        plan_filters: dict[str, object],
    ) -> list[dict]:
        documents = result.get("documents", [[]])
        metadatas = result.get("metadatas", [[]])
        distances = result.get("distances", [[]])
        if not documents or not documents[0]:
            return []

        candidates: list[dict] = []
        for index, (doc_text, metadata) in enumerate(zip(documents[0], metadatas[0])):
            document_id = int(metadata.get("document_id", 0))
            chunk_index = int(metadata.get("chunk_index", 0))
            chunk_key = (document_id, chunk_index)
            if chunk_key in seen_chunks:
                continue
            seen_chunks.add(chunk_key)
            candidates.append(
                {
                    "reference": QAReference(
                        document_id=document_id,
                        file_name=str(metadata.get("file_name", "")),
                        chunk_index=chunk_index,
                        snippet=doc_text[:max_snippet_length],
                        section_title=str(metadata.get("section_title", "")).strip() or None,
                        content_type_hint=str(metadata.get("content_type_hint", "")).strip() or None,
                        document_kind=str(metadata.get("document_kind", "")).strip() or None,
                        starts_with_question=bool(metadata.get("starts_with_question", False)),
                        context_role=self._build_context_role(metadata),
                    ),
                    "metadata": metadata,
                    "distance": self._extract_distance(distances, index),
                    "plan_filters": plan_filters,
                    "raw_text": doc_text,
                    "retrieval_rank": index,
                }
            )
        return candidates

    def _rerank_candidates(self, *, question: str, route, candidates: list[dict]) -> list[dict]:
        question_tokens = self._tokenize_question(question)
        rescored: list[dict] = []
        for candidate in candidates:
            metadata = candidate["metadata"]
            content_type_hint = str(metadata.get("content_type_hint", "")).strip().lower()
            document_kind = str(metadata.get("document_kind", "")).strip().lower()
            starts_with_question = bool(metadata.get("starts_with_question", False))
            section_title = str(metadata.get("section_title", "")).strip().lower()
            raw_text = str(candidate.get("raw_text", "")).strip().lower()
            distance = candidate.get("distance")
            retrieval_rank = int(candidate.get("retrieval_rank", 0))

            score = 0.0

            score += self._ordered_match_score(content_type_hint, route.preferred_content_types, base=3.5, step=0.8)
            score += self._ordered_match_score(document_kind, route.preferred_document_kinds, base=2.5, step=0.6)
            if route.prefer_question_opening and starts_with_question:
                score += 1.5

            score += self._keyword_overlap_score(question_tokens, f"{section_title} {raw_text}")

            if distance is not None:
                score += max(0.0, 1.5 - float(distance))

            score += max(0.0, 1.0 - (retrieval_rank * 0.15))

            rescored.append({**candidate, "rerank_score": score})

        rescored.sort(
            key=lambda item: (
                float(item.get("rerank_score", 0.0)),
                -float(item.get("distance", 999.0)) if item.get("distance") is not None else -999.0,
                -int(item.get("retrieval_rank", 0)),
            ),
            reverse=True,
        )
        return rescored

    def _extract_distance(self, distances: list[list[float]] | list, index: int) -> float | None:
        if not distances:
            return None
        first_row = distances[0] if isinstance(distances[0], list) else distances
        if index >= len(first_row):
            return None
        value = first_row[index]
        if value is None:
            return None
        return float(value)

    def _tokenize_question(self, question: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]+", question.lower())
            if len(token) >= 2
        }

    def _keyword_overlap_score(self, question_tokens: set[str], candidate_text: str) -> float:
        if not question_tokens or not candidate_text:
            return 0.0
        matched = sum(1 for token in question_tokens if token in candidate_text)
        return min(2.5, matched * 0.5)

    def _ordered_match_score(
        self,
        candidate_value: str,
        preferred_values: tuple[str, ...],
        *,
        base: float,
        step: float,
    ) -> float:
        if not candidate_value:
            return 0.0
        for index, expected_value in enumerate(preferred_values):
            if candidate_value == expected_value:
                return max(0.0, base - (index * step))
        return 0.0

    def _build_context_role(self, metadata: dict) -> str:
        content_type_hint = str(metadata.get("content_type_hint", "")).strip().lower()
        if content_type_hint == "concept_explanation":
            return "concept"
        if content_type_hint == "design_discussion":
            return "design"
        if content_type_hint == "implementation_detail":
            return "implementation"
        if content_type_hint == "example_driven":
            return "example"
        if content_type_hint == "question_answer":
            if bool(metadata.get("starts_with_question", False)):
                return "core_answer"
            return "qa_pair"
        return "general"

    def _get_or_create_session(self, user_id: int, knowledge_base_id: int, session_id: int | None, question: str) -> QASession:
        if session_id is not None:
            stmt = select(QASession).where(QASession.id == session_id, QASession.user_id == user_id)
            session = self.db.scalar(stmt)
            if session:
                return session

        session = QASession(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            title=question[:50],
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _get_embedding_provider(self):
        if self.embedding_provider is None:
            self.embedding_provider = get_embedding_provider()
        return self.embedding_provider

    def _get_vector_store(self):
        if self.vector_store is None:
            self.vector_store = ChromaVectorStore()
        return self.vector_store
