import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.qa import QAMessage, QASession
from app.rag.factory import generate_answer, get_embedding_provider
from app.rag.vector_store import ChromaVectorStore
from app.schemas.qa import AskRequest, AskResponse, QAReference, QAMessageResponse, QASessionDetailResponse
from app.utils import get_rag_config

logger = logging.getLogger("app.services.qa")


class QAService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = get_embedding_provider()
        self.vector_store = ChromaVectorStore()

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

    def _ensure_kb_access(self, user_id: int, knowledge_base_id: int) -> None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.user_id == user_id)
        kb = self.db.scalar(stmt)
        if not kb:
            raise ValueError("Knowledge base not found")

    def _retrieve_references(self, user_id: int, knowledge_base_id: int, question: str) -> list[QAReference]:
        rag_config = get_rag_config()
        query_embedding = self.embedding_provider.embed_query(question)
        result = self.vector_store.query(
            query_embedding=query_embedding,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            top_k=rag_config.retrieval.top_k,
        )

        documents = result.get("documents", [[]])
        metadatas = result.get("metadatas", [[]])
        if not documents or not documents[0]:
            return []

        references: list[QAReference] = []
        for doc_text, metadata in zip(documents[0], metadatas[0]):
            references.append(
                QAReference(
                    document_id=int(metadata.get("document_id", 0)),
                    file_name=str(metadata.get("file_name", "")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    snippet=doc_text[: rag_config.answering.max_reference_snippet_length],
                )
            )
        return references

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
