from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.qa import QAMessage, QASession
from app.db.models.user import User
from app.services.qa_service import QAService


class QAServiceDeleteSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="qa-user", email="qa-user@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="QA KB")
        self.db.add(self.knowledge_base)
        self.db.commit()
        self.db.refresh(self.knowledge_base)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_delete_session_removes_session_and_messages(self) -> None:
        session = QASession(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            title="Explain CAP theorem",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        self.db.add_all(
            [
                QAMessage(session_id=session.id, role="user", content="What is CAP?", references_json=None),
                QAMessage(
                    session_id=session.id,
                    role="assistant",
                    content="Consistency, availability, partition tolerance.",
                    references_json=[],
                ),
            ]
        )
        self.db.commit()

        service = QAService(self.db)
        deleted = service.delete_session(self.user.id, session.id)

        self.assertTrue(deleted)
        self.assertIsNone(self.db.get(QASession, session.id))
        self.assertEqual(self.db.query(QAMessage).filter_by(session_id=session.id).all(), [])

    def test_delete_session_returns_false_when_missing(self) -> None:
        service = QAService(self.db)
        self.assertFalse(service.delete_session(self.user.id, 999999))


if __name__ == "__main__":
    unittest.main()
