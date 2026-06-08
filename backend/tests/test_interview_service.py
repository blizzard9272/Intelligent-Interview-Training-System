from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models.document import Document
from app.db.models.interview import InterviewTurn
from app.db.models.interview import InterviewSession
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.question_bank import QuestionBank
from app.db.models.user import User
from app.schemas.interview import InterviewAnswerRequest, InterviewStartRequest
from app.services.interview_service import InterviewService


class InterviewServiceStartSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="tester", email="tester@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.flush()

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="Python KB", description="Test KB")
        self.db.add(self.knowledge_base)
        self.db.flush()

        self.document_a = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="doc-a.md",
            file_type="md",
            file_path="/tmp/doc-a.md",
            file_size=100,
            status="completed",
            chunk_count=3,
        )
        self.document_b = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="doc-b.md",
            file_type="md",
            file_path="/tmp/doc-b.md",
            file_size=100,
            status="completed",
            chunk_count=3,
        )
        self.db.add_all([self.document_a, self.document_b])
        self.db.flush()

        self.question_a = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document_a.id,
            question="Explain Python decorators.",
            reference_answer="Decorator basics.",
            tags=["concept"],
            difficulty="easy",
        )
        self.question_b = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document_b.id,
            question="Explain async event loops.",
            reference_answer="Event loop basics.",
            tags=["concept"],
            difficulty="medium",
        )
        self.db.add_all([self.question_a, self.question_b])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_start_session_filters_by_source_document(self) -> None:
        service = InterviewService(self.db)

        result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                source_document_id=self.document_b.id,
                question_strategy="recent_first",
            ),
        )

        self.assertEqual(result.question_id, self.question_b.id)
        self.assertEqual(result.source_document_id, self.document_b.id)
        self.assertEqual(result.source_document_name, "doc-b.md")
        self.assertEqual(result.question_strategy, "recent_first")
        self.assertEqual(result.drill_mode, "single_question")
        self.assertEqual(result.question_count, 1)
        self.assertEqual(result.active_question_number, 1)

    def test_start_session_avoid_recent_skips_recent_question(self) -> None:
        recent_session = InterviewSession(
            id="recent-session",
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            question_id=self.question_b.id,
            question=self.question_b.question,
            reference_answer=self.question_b.reference_answer,
            status="completed",
            strengths=[],
            improvements=[],
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            finished_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        self.db.add(recent_session)
        self.db.commit()

        service = InterviewService(self.db)
        result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_strategy="avoid_recent",
            ),
        )

        self.assertEqual(result.question_id, self.question_a.id)
        self.assertEqual(result.source_document_id, self.document_a.id)
        self.assertEqual(result.question_strategy, "avoid_recent")

    def test_start_session_rejects_unavailable_source_document(self) -> None:
        pending_document = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="pending.md",
            file_type="md",
            file_path="/tmp/pending.md",
            file_size=50,
            status="pending",
            chunk_count=0,
        )
        self.db.add(pending_document)
        self.db.commit()

        service = InterviewService(self.db)

        with self.assertRaisesRegex(ValueError, "source document"):
            service.start_session(
                self.user.id,
                InterviewStartRequest(
                    knowledge_base_id=self.knowledge_base.id,
                    source_document_id=pending_document.id,
                ),
            )

    def test_start_session_recent_first_picks_latest_question(self) -> None:
        latest_question = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document_a.id,
            question="Explain Python context managers.",
            reference_answer="Context manager basics.",
            tags=["concept"],
            difficulty="hard",
            created_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            updated_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        self.db.add(latest_question)
        self.db.commit()

        service = InterviewService(self.db)
        result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_strategy="recent_first",
            ),
        )

        self.assertEqual(result.question_id, latest_question.id)
        self.assertEqual(result.difficulty, "hard")
        self.assertEqual(result.question_strategy, "recent_first")

    def test_start_session_reports_no_matching_filtered_question(self) -> None:
        service = InterviewService(self.db)

        with self.assertRaisesRegex(ValueError, "No interview question matches the current filters"):
            service.start_session(
                self.user.id,
                InterviewStartRequest(
                    knowledge_base_id=self.knowledge_base.id,
                    source_document_id=self.document_a.id,
                    difficulty="hard",
                ),
            )

    def test_start_session_question_set_selects_multiple_questions(self) -> None:
        latest_question = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document_a.id,
            question="Explain Python context managers.",
            reference_answer="Context manager basics.",
            tags=["concept"],
            difficulty="hard",
            created_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            updated_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        self.db.add(latest_question)
        self.db.commit()

        service = InterviewService(self.db)
        result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                drill_mode="question_set",
                question_count=3,
                question_strategy="recent_first",
            ),
        )

        self.assertEqual(result.drill_mode, "question_set")
        self.assertEqual(result.question_count, 3)
        self.assertEqual(result.active_question_number, 1)
        self.assertEqual(result.question_id, latest_question.id)

    def test_start_session_focus_topic_prioritizes_matching_question(self) -> None:
        focused_question = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document_a.id,
            question="How do you discuss architecture trade-offs in Python services?",
            reference_answer="Compare options, constraints, and operational risks.",
            tags=["design", "trade-off"],
            difficulty="hard",
            created_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            updated_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        self.db.add(focused_question)
        self.db.commit()

        service = InterviewService(self.db)
        result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                focus_topic="trade-off discussion",
                question_strategy="recent_first",
            ),
        )

        self.assertEqual(result.question_id, focused_question.id)
        self.assertEqual(result.focus_topic, "trade-off discussion")


class InterviewServiceSubmitAnswerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="answerer", email="answerer@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.flush()

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="Interview KB", description="Test KB")
        self.db.add(self.knowledge_base)
        self.db.flush()

        self.document = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="summary-source.md",
            file_type="md",
            file_path="/tmp/summary-source.md",
            file_size=120,
            status="completed",
            chunk_count=2,
        )
        self.db.add(self.document)
        self.db.flush()

        self.question = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document.id,
            question="What is dependency injection?",
            reference_answer="Dependency injection is a pattern that supplies dependencies from the outside.",
            tags=["concept"],
            difficulty="easy",
        )
        self.db.add(self.question)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_submit_answer_creates_local_summary_when_model_summary_fails(self) -> None:
        service = InterviewService(self.db)
        start_result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question.id,
            ),
        )

        with patch.object(InterviewService, "_max_rounds", return_value=1), patch.object(
            InterviewService,
            "_generate_session_summary_with_model",
            side_effect=ValueError("summary model unavailable"),
        ):
            result = service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=start_result.session_id,
                    answer="Dependency injection passes dependencies into a component instead of constructing them inside it.",
                ),
            )

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.can_continue)
        self.assertIsNotNone(result.summary)
        self.assertIn("overall score", result.summary.lower())
        self.assertIsInstance(result.summary_meta, dict)
        self.assertIn("next_actions", result.summary_meta)
        self.assertEqual(result.summary_meta["overall_score"], result.overall_score)

    def test_submit_answer_uses_suggested_followup_when_available(self) -> None:
        service = InterviewService(self.db)
        start_result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question.id,
            ),
        )

        with patch.object(InterviewService, "_max_rounds", return_value=2), patch.object(
            InterviewService,
            "_generate_feedback",
            return_value={
                "feedback": "Solid answer with room for a concrete example.",
                "overall_score": 8,
                "strengths": ["Clear explanation"],
                "improvements": ["Add an implementation example"],
                "suggested_followup": "Can you give a concrete service-layer example?",
            },
        ):
            result = service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=start_result.session_id,
                    answer="It means dependencies are provided externally.",
                ),
            )

        self.assertEqual(result.status, "awaiting_followup_answer")
        self.assertTrue(result.can_continue)
        self.assertEqual(result.next_question, "Can you give a concrete service-layer example?")
        self.assertEqual(result.suggested_followup, "Can you give a concrete service-layer example?")

    def test_submit_answer_question_set_advances_to_next_primary_question(self) -> None:
        question_two = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document.id,
            question="What are the trade-offs of dependency injection?",
            reference_answer="It improves testability but adds indirection.",
            tags=["design"],
            difficulty="medium",
            created_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            updated_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        self.db.add(question_two)
        self.db.commit()

        service = InterviewService(self.db)
        start_result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                drill_mode="question_set",
                question_count=2,
                question_strategy="recent_first",
            ),
        )

        with patch.object(InterviewService, "_generate_followup_question", return_value=None):
            result = service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=start_result.session_id,
                    answer="Dependency injection keeps construction outside the class and improves testing.",
                ),
            )

        self.assertTrue(result.can_continue)
        self.assertEqual(result.status, "awaiting_answer")
        self.assertEqual(result.drill_mode, "question_set")
        self.assertEqual(result.question_count, 2)
        self.assertEqual(result.active_question_number, 2)
        self.assertEqual(result.next_prompt_type, "next_question")
        self.assertEqual(result.next_question, self.question.question)

        detail = service.get_session(self.user.id, start_result.session_id)
        assert detail is not None
        self.assertEqual(detail.question_id, self.question.id)
        self.assertEqual(detail.question, self.question.question)
        self.assertEqual(detail.active_question_number, 2)
        self.assertEqual(detail.question_count, 2)
        self.assertEqual(detail.drill_mode, "question_set")


class InterviewServiceTrainingAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="analyst", email="analyst@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.flush()

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="Analysis KB", description="Analysis KB")
        self.db.add(self.knowledge_base)
        self.db.flush()

        self.document = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="analysis-doc.md",
            file_type="md",
            file_path="/tmp/analysis-doc.md",
            file_size=150,
            status="completed",
            chunk_count=4,
        )
        self.db.add(self.document)
        self.db.flush()

        self.question_a = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document.id,
            question="Explain dependency injection.",
            reference_answer="Dependency injection provides dependencies from outside the class.",
            tags=["concept"],
            difficulty="easy",
        )
        self.question_b = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document.id,
            question="Design a plugin loading system.",
            reference_answer="Discuss contracts, lifecycle, and failure handling.",
            tags=["design"],
            difficulty="medium",
            created_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            updated_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        self.db.add_all([self.question_a, self.question_b])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_analyze_training_aggregates_completed_sessions(self) -> None:
        service = InterviewService(self.db)

        first = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question_a.id,
            ),
        )
        second = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question_b.id,
            ),
        )

        with patch.object(InterviewService, "_max_rounds", return_value=1), patch.object(
            InterviewService,
            "_generate_feedback",
            return_value={
                "feedback": "Strong baseline explanation.",
                "overall_score": 8,
                "strengths": ["Clear fundamentals"],
                "improvements": ["Add a concrete implementation example"],
                "suggested_followup": None,
            },
        ), patch.object(
            InterviewService,
            "_generate_session_summary_with_model",
            side_effect=ValueError("summary unavailable"),
        ):
            service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=first.session_id,
                    answer="Dependencies are passed into the class from outside.",
                ),
            )

        with patch.object(InterviewService, "_max_rounds", return_value=1), patch.object(
            InterviewService,
            "_generate_feedback",
            return_value={
                "feedback": "Good structure but mention more trade-offs.",
                "overall_score": 7,
                "strengths": ["Clear answer structure"],
                "improvements": ["Add more trade-off discussion"],
                "suggested_followup": None,
            },
        ), patch.object(
            InterviewService,
            "_generate_session_summary_with_model",
            return_value=(
                "A solid system-design style answer overall.",
                {
                    "highlights": ["Clear answer structure"],
                    "weak_points": ["Add more trade-off discussion"],
                    "next_actions": ["Practice discussing architecture trade-offs"],
                    "overall_score": 7,
                },
            ),
        ):
            service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=second.session_id,
                    answer="A plugin system needs contracts, loading isolation, and failure handling.",
                ),
            )

        second_session = service._get_session_entity(self.user.id, second.session_id)
        assert second_session is not None
        second_session.started_at = datetime.now(timezone.utc) + timedelta(minutes=2)
        second_session.updated_at = second_session.started_at
        self.db.commit()

        analysis = service.analyze_training(self.user.id, self.knowledge_base.id)

        self.assertEqual(analysis.total_sessions, 2)
        self.assertEqual(analysis.completed_sessions, 2)
        self.assertEqual(analysis.average_score, 7.5)
        self.assertEqual(analysis.latest_score, 7)
        self.assertTrue(any(item.label == "Concept" for item in analysis.question_type_breakdown))
        self.assertTrue(any(item.label == "Design" for item in analysis.question_type_breakdown))
        self.assertTrue(any(item.label == "analysis-doc.md" for item in analysis.source_document_breakdown))
        self.assertTrue(any("trade-off" in item.label.lower() for item in analysis.common_weak_points))
        self.assertTrue(any("structure" in item.label.lower() for item in analysis.common_strengths))
        self.assertGreaterEqual(len(analysis.recommended_focus), 1)
        self.assertGreaterEqual(len(analysis.focus_drills), 1)
        self.assertEqual(analysis.focus_drills[0].drill_mode, "question_set")
        self.assertEqual(analysis.focus_drills[0].question_count, 3)
        self.assertEqual(analysis.focus_drills[0].question_strategy, "avoid_recent")
        self.assertEqual(analysis.focus_drills[0].knowledge_base_id, self.knowledge_base.id)

    def test_analyze_training_reports_focus_drill_effects(self) -> None:
        service = InterviewService(self.db)

        first = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question_b.id,
                focus_topic="trade-off discussion",
            ),
        )
        second = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question_b.id,
                focus_topic="trade-off discussion",
            ),
        )

        with patch.object(InterviewService, "_max_rounds", return_value=1), patch.object(
            InterviewService,
            "_generate_feedback",
            return_value={
                "feedback": "Needs more trade-off depth.",
                "overall_score": 5,
                "strengths": ["Basic structure"],
                "improvements": ["Explain trade-offs more concretely"],
                "suggested_followup": None,
            },
        ), patch.object(
            InterviewService,
            "_generate_session_summary_with_model",
            side_effect=ValueError("summary unavailable"),
        ):
            service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=first.session_id,
                    answer="It needs more explicit trade-off discussion.",
                ),
            )

        with patch.object(InterviewService, "_max_rounds", return_value=1), patch.object(
            InterviewService,
            "_generate_feedback",
            return_value={
                "feedback": "Trade-off coverage improved significantly.",
                "overall_score": 8,
                "strengths": ["Good trade-off explanation"],
                "improvements": ["Add one more production example"],
                "suggested_followup": None,
            },
        ), patch.object(
            InterviewService,
            "_generate_session_summary_with_model",
            side_effect=ValueError("summary unavailable"),
        ):
            service.submit_answer(
                self.user.id,
                InterviewAnswerRequest(
                    session_id=second.session_id,
                    answer="Now I can compare alternatives, constraints, and operational risks clearly.",
                ),
            )

        second_session = service._get_session_entity(self.user.id, second.session_id)
        assert second_session is not None
        second_session.started_at = datetime.now(timezone.utc) + timedelta(minutes=3)
        second_session.updated_at = second_session.started_at
        self.db.commit()

        analysis = service.analyze_training(self.user.id, self.knowledge_base.id)

        matching_effect = next(
            (item for item in analysis.focus_drill_effects if item.focus_label == "trade-off discussion"),
            None,
        )
        self.assertIsNotNone(matching_effect)
        assert matching_effect is not None
        self.assertEqual(matching_effect.session_count, 2)
        self.assertEqual(matching_effect.average_score, 6.5)
        self.assertEqual(matching_effect.latest_score, 8)
        self.assertEqual(matching_effect.best_score, 8)
        self.assertEqual(matching_effect.score_delta, 3.0)


class InterviewServiceDeleteSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)
        self.db = self.session_factory()

        self.user = User(username="deleter", email="deleter@example.com", password_hash="hashed")
        self.db.add(self.user)
        self.db.flush()

        self.knowledge_base = KnowledgeBase(user_id=self.user.id, name="Delete KB", description="Delete KB")
        self.db.add(self.knowledge_base)
        self.db.flush()

        self.document = Document(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            file_name="delete-doc.md",
            file_type="md",
            file_path="/tmp/delete-doc.md",
            file_size=64,
            status="completed",
            chunk_count=1,
        )
        self.db.add(self.document)
        self.db.flush()

        self.question = QuestionBank(
            user_id=self.user.id,
            knowledge_base_id=self.knowledge_base.id,
            source_document_id=self.document.id,
            question="Explain Python packaging basics.",
            reference_answer="Packages group modules and support distribution.",
            tags=["concept"],
            difficulty="easy",
        )
        self.db.add(self.question)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_delete_session_removes_session_and_turns(self) -> None:
        service = InterviewService(self.db)
        start_result = service.start_session(
            self.user.id,
            InterviewStartRequest(
                knowledge_base_id=self.knowledge_base.id,
                question_id=self.question.id,
            ),
        )

        session = service._get_session_entity(self.user.id, start_result.session_id)
        assert session is not None
        self.assertGreaterEqual(len(session.turns), 1)

        deleted = service.delete_session(self.user.id, start_result.session_id)

        self.assertTrue(deleted)
        self.assertIsNone(service._get_session_entity(self.user.id, start_result.session_id))
        remaining_turns = self.db.query(InterviewTurn).filter_by(session_id=start_result.session_id).all()
        self.assertEqual(remaining_turns, [])

    def test_delete_session_returns_false_when_missing(self) -> None:
        service = InterviewService(self.db)
        self.assertFalse(service.delete_session(self.user.id, "missing-session"))


if __name__ == "__main__":
    unittest.main()
