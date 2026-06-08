from __future__ import annotations

import json
import logging
import random
import re
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.interview import InterviewSession, InterviewTurn
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.question_bank import QuestionBank
from app.rag.generators.qwen_chat import ChatProviderError, QwenChatProvider
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewFeedbackResponse,
    InterviewSessionDetailResponse,
    InterviewSessionListItemResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    TrainingAnalysisCountItem,
    TrainingDrillRecommendation,
    TrainingFocusEffectItem,
    TrainingAnalysisResponse,
    TrainingAnalysisScorePoint,
    InterviewTurnResponse,
)
from app.utils import get_agent_config, get_prompt_text

logger = logging.getLogger("app.services.interview")


class InterviewService:
    DEFAULT_QUESTION_STRATEGY = "random"
    SUPPORTED_QUESTION_STRATEGIES = {"random", "recent_first", "avoid_recent"}
    DEFAULT_DRILL_MODE = "single_question"
    SUPPORTED_DRILL_MODES = {"single_question", "question_set"}
    DEFAULT_QUESTION_SET_COUNT = 3
    MAX_QUESTION_SET_COUNT = 10

    def __init__(self, db: Session):
        self.db = db

    def start_session(self, user_id: int, payload: InterviewStartRequest) -> InterviewStartResponse:
        self._ensure_kb_access(user_id, payload.knowledge_base_id)
        selected_strategy = self._normalize_question_strategy(payload.question_strategy)
        selected_drill_mode = self._normalize_drill_mode(payload.drill_mode)
        selected_question_count = self._normalize_question_count(
            drill_mode=selected_drill_mode,
            question_count=payload.question_count,
        )

        if payload.source_document_id is not None:
            self._ensure_document_access(user_id, payload.knowledge_base_id, payload.source_document_id)

        if payload.question_id is not None and selected_drill_mode == "question_set" and selected_question_count > 1:
            raise ValueError("question_id cannot be combined with multi-question drill mode.")

        selected_questions = self._select_questions(
            user_id=user_id,
            knowledge_base_id=payload.knowledge_base_id,
            question_id=payload.question_id,
            source_document_id=payload.source_document_id,
            focus_topic=payload.focus_topic,
            difficulty=payload.difficulty,
            question_type=payload.question_type,
            question_strategy=selected_strategy,
            question_count=selected_question_count,
        )
        if not selected_questions:
            if payload.difficulty or payload.question_type or payload.source_document_id is not None:
                raise ValueError("No interview question matches the current filters. Try relaxing the document, difficulty, or question type filters.")
            raise ValueError("No interview questions are available for this knowledge base yet. Generate questions first.")

        first_question = selected_questions[0]
        now = datetime.now(timezone.utc)
        session = InterviewSession(
            id=uuid4().hex,
            user_id=user_id,
            knowledge_base_id=payload.knowledge_base_id,
            question_id=first_question.id,
            question=first_question.question,
            reference_answer=first_question.reference_answer,
            status="awaiting_answer",
            started_at=now,
            strengths=[],
            improvements=[],
        )
        self.db.add(session)
        self.db.flush()

        session_plan = {
            "drill_mode": selected_drill_mode,
            "question_count": len(selected_questions),
            "question_strategy": selected_strategy,
            "focus_topic": self._normalize_focus_topic(payload.focus_topic),
            "selected_question_ids": [item.id for item in selected_questions],
            "current_question_index": 0,
        }
        self.db.add(
            InterviewTurn(
                session_id=session.id,
                role="interviewer",
                content=first_question.question,
                meta_json={
                    "round": 1,
                    "question_id": first_question.id,
                    "reference_answer": first_question.reference_answer,
                    "question_type": "initial",
                    "source_document_id": first_question.source_document_id,
                    "source_document_name": first_question.source_document.file_name if first_question.source_document else None,
                    "question_strategy": selected_strategy,
                    "question_number": 1,
                    "selection_filters": {
                        "source_document_id": payload.source_document_id,
                        "focus_topic": payload.focus_topic,
                        "difficulty": payload.difficulty,
                        "question_type": payload.question_type,
                    },
                    "session_plan": session_plan,
                },
                created_at=now,
            )
        )
        self.db.commit()
        self.db.refresh(session)
        logger.info(
            "interview_session_started user_id=%s knowledge_base_id=%s question_id=%s session_id=%s source_document_id=%s strategy=%s drill_mode=%s question_count=%s",
            user_id,
            payload.knowledge_base_id,
            first_question.id,
            session.id,
            first_question.source_document_id,
            selected_strategy,
            selected_drill_mode,
            len(selected_questions),
        )
        return InterviewStartResponse(
            session_id=session.id,
            knowledge_base_id=session.knowledge_base_id,
            question_id=session.question_id,
            question=session.question,
            source_document_id=first_question.source_document_id,
            source_document_name=first_question.source_document.file_name if first_question.source_document else None,
            focus_topic=self._normalize_focus_topic(payload.focus_topic),
            difficulty=first_question.difficulty,
            question_tags=self._question_tags(first_question),
            question_strategy=selected_strategy,
            drill_mode=selected_drill_mode,
            question_count=len(selected_questions),
            active_question_number=1,
            status=session.status,
            started_at=session.started_at,
        )

    def submit_answer(self, user_id: int, payload: InterviewAnswerRequest) -> InterviewFeedbackResponse:
        session = self._get_session_entity(user_id, payload.session_id)
        if not session:
            raise ValueError("Interview session does not exist.")
        if session.status == "completed":
            raise ValueError("This interview session is already completed.")

        session_plan = self._get_session_plan(session)
        current_round = self._current_round(session)
        max_rounds = self._max_rounds()
        feedback = self._generate_feedback(
            question=session.question,
            reference_answer=session.reference_answer,
            answer=payload.answer,
        )

        now = datetime.now(timezone.utc)
        self.db.add(
            InterviewTurn(
                session_id=session.id,
                role="candidate",
                content=payload.answer,
                meta_json={
                    "round": current_round,
                    "question_number": self._active_question_number(session_plan),
                },
                created_at=now,
            )
        )
        self.db.add(
            InterviewTurn(
                session_id=session.id,
                role="interviewer_feedback",
                content=feedback["feedback"],
                meta_json={
                    "round": current_round,
                    "question_number": self._active_question_number(session_plan),
                    "overall_score": feedback["overall_score"],
                    "strengths": feedback["strengths"],
                    "improvements": feedback["improvements"],
                    "suggested_followup": feedback.get("suggested_followup"),
                },
                created_at=now,
            )
        )

        session.overall_score = feedback["overall_score"]
        session.strengths = feedback["strengths"]
        session.improvements = feedback["improvements"]
        session.suggested_followup = feedback.get("suggested_followup")

        next_question: str | None = None
        next_prompt_type: str | None = None
        summary_text: str | None = None
        summary_meta: dict | None = None
        can_continue = current_round < max_rounds

        if can_continue:
            next_question = self._generate_followup_question(
                question=session.question,
                answer=payload.answer,
                feedback=feedback["feedback"],
                suggested_followup=feedback.get("suggested_followup"),
                current_round=current_round,
            )
            if next_question:
                next_prompt_type = "followup"
                self.db.add(
                    InterviewTurn(
                        session_id=session.id,
                        role="interviewer_followup",
                        content=next_question,
                        meta_json={
                            "round": current_round + 1,
                            "question_type": "followup",
                            "question_number": self._active_question_number(session_plan),
                        },
                        created_at=now,
                    )
                )
                session.question = next_question
                session.reference_answer = None
                session.status = "awaiting_followup_answer"
            else:
                can_continue = False

        if not can_continue:
            next_primary_question = self._advance_to_next_primary_question(
                session=session,
                session_plan=session_plan,
                current_round=current_round,
                timestamp=now,
            )
            if next_primary_question:
                session.status = "awaiting_answer"
                next_question = next_primary_question.question
                next_prompt_type = "next_question"
                can_continue = True
            else:
                session.status = "completed"
                session.finished_at = now
                next_question = None
                next_prompt_type = None
                summary_text, summary_meta = self._create_or_update_summary_turn(
                    session=session,
                    latest_answer=payload.answer,
                    latest_feedback=feedback,
                )

        session.updated_at = now
        self.db.commit()
        self.db.refresh(session)
        active_plan = self._get_session_plan(session)
        logger.info(
            "interview_feedback_generated user_id=%s session_id=%s round=%s score=%s can_continue=%s active_question_number=%s question_count=%s",
            user_id,
            session.id,
            current_round,
            session.overall_score,
            can_continue,
            self._active_question_number(active_plan),
            self._planned_question_count(active_plan),
        )
        return InterviewFeedbackResponse(
            session_id=session.id,
            question_id=session.question_id,
            question=self._question_for_round(session, current_round),
            difficulty=session.question_bank_item.difficulty if session.question_bank_item else None,
            question_tags=self._question_tags(session.question_bank_item),
            answer=payload.answer,
            feedback=feedback["feedback"],
            overall_score=feedback["overall_score"],
            strengths=feedback["strengths"],
            improvements=feedback["improvements"],
            suggested_followup=feedback.get("suggested_followup"),
            next_question=next_question,
            next_prompt_type=next_prompt_type,
            current_round=current_round,
            max_rounds=max_rounds,
            can_continue=can_continue,
            drill_mode=self._plan_value(active_plan, "drill_mode", self.DEFAULT_DRILL_MODE),
            question_count=self._planned_question_count(active_plan),
            active_question_number=self._active_question_number(active_plan),
            status=session.status,
            summary=summary_text,
            summary_meta=summary_meta,
            updated_at=session.updated_at,
        )

    def list_sessions(self, user_id: int, knowledge_base_id: int | None = None) -> list[InterviewSessionListItemResponse]:
        stmt = select(InterviewSession).where(InterviewSession.user_id == user_id)
        if knowledge_base_id is not None:
            stmt = stmt.where(InterviewSession.knowledge_base_id == knowledge_base_id)
        stmt = stmt.order_by(InterviewSession.updated_at.desc())
        sessions = list(self.db.scalars(stmt))
        return [
            self._build_session_list_item(item)
            for item in sessions
        ]

    def analyze_training(self, user_id: int, knowledge_base_id: int | None = None) -> TrainingAnalysisResponse:
        stmt = select(InterviewSession).where(InterviewSession.user_id == user_id)
        if knowledge_base_id is not None:
            stmt = stmt.where(InterviewSession.knowledge_base_id == knowledge_base_id)
        stmt = stmt.order_by(InterviewSession.started_at.desc())
        sessions = list(self.db.scalars(stmt))

        completed_sessions = [session for session in sessions if session.status == "completed" and session.overall_score is not None]
        weak_point_counter: Counter[str] = Counter()
        strength_counter: Counter[str] = Counter()
        question_type_counter: Counter[str] = Counter()
        source_document_counter: Counter[str] = Counter()
        source_document_id_counter: Counter[int] = Counter()
        source_document_names_by_id: dict[int, str] = {}
        focus_sessions_by_topic: dict[str, list[InterviewSession]] = {}
        recent_scores: list[TrainingAnalysisScorePoint] = []

        for session in completed_sessions:
            weak_points, strengths = self._session_analysis_lists(session)
            weak_point_counter.update(weak_points)
            strength_counter.update(strengths)
            session_plan = self._get_session_plan(session)
            focus_topic = self._plan_value(session_plan, "focus_topic", None)
            if focus_topic:
                focus_sessions_by_topic.setdefault(focus_topic, []).append(session)

            if session.question_bank_item:
                source_document_name = (
                    session.question_bank_item.source_document.file_name
                    if session.question_bank_item.source_document
                    else "Unknown document"
                )
                source_document_counter.update([source_document_name])
                if session.question_bank_item.source_document_id is not None:
                    source_document_id_counter.update([session.question_bank_item.source_document_id])
                    source_document_names_by_id[session.question_bank_item.source_document_id] = source_document_name
                question_tags = self._question_tags(session.question_bank_item)
                normalized_types = [
                    self._format_question_type_label(tag)
                    for tag in question_tags
                    if tag.lower() in {"concept", "scenario", "followup", "design"}
                ]
                if normalized_types:
                    question_type_counter.update(normalized_types)

            recent_scores.append(
                TrainingAnalysisScorePoint(
                    session_id=session.id,
                    score=session.overall_score,
                    started_at=session.started_at,
                )
            )

        average_score = None
        latest_score = None
        if completed_sessions:
            total_score = sum(session.overall_score or 0 for session in completed_sessions)
            average_score = round(total_score / len(completed_sessions), 2)
            latest_score = completed_sessions[0].overall_score

        return TrainingAnalysisResponse(
            knowledge_base_id=knowledge_base_id,
            total_sessions=len(sessions),
            completed_sessions=len(completed_sessions),
            average_score=average_score,
            latest_score=latest_score,
            common_weak_points=self._counter_to_items(weak_point_counter),
            common_strengths=self._counter_to_items(strength_counter),
            question_type_breakdown=self._counter_to_items(question_type_counter),
            source_document_breakdown=self._counter_to_items(source_document_counter),
            recent_scores=recent_scores[:5],
            recommended_focus=self._build_recommended_focus(
                average_score=average_score,
                weak_point_counter=weak_point_counter,
                question_type_counter=question_type_counter,
                source_document_counter=source_document_counter,
            ),
            focus_drills=self._build_focus_drills(
                knowledge_base_id=knowledge_base_id,
                weak_point_counter=weak_point_counter,
                question_type_counter=question_type_counter,
                source_document_id_counter=source_document_id_counter,
                source_document_names_by_id=source_document_names_by_id,
            ),
            focus_drill_effects=self._build_focus_drill_effects(focus_sessions_by_topic),
        )

    def get_session(self, user_id: int, session_id: str) -> InterviewSessionDetailResponse | None:
        session = self._get_session_entity(user_id, session_id)
        if not session:
            return None

        turns = sorted(session.turns, key=lambda item: item.created_at)
        answer_turn = next((turn for turn in reversed(turns) if turn.role == "candidate"), None)
        feedback_turn = next((turn for turn in reversed(turns) if turn.role == "interviewer_feedback"), None)
        summary_turn = next((turn for turn in reversed(turns) if turn.role == "interview_summary"), None)
        session_plan = self._get_session_plan(session)
        current_round = self._current_round(session)
        max_rounds = self._max_rounds()
        next_question, next_prompt_type = self._pending_prompt(session)
        can_continue = session.status != "completed"

        return InterviewSessionDetailResponse(
            session_id=session.id,
            knowledge_base_id=session.knowledge_base_id,
            question_id=session.question_id,
            question=session.question,
            source_document_id=session.question_bank_item.source_document_id if session.question_bank_item else None,
            source_document_name=(
                session.question_bank_item.source_document.file_name
                if session.question_bank_item and session.question_bank_item.source_document
                else None
            ),
            focus_topic=self._plan_value(session_plan, "focus_topic", None),
            difficulty=session.question_bank_item.difficulty if session.question_bank_item else None,
            question_tags=self._question_tags(session.question_bank_item),
            question_strategy=self._plan_value(session_plan, "question_strategy", self.DEFAULT_QUESTION_STRATEGY),
            drill_mode=self._plan_value(session_plan, "drill_mode", self.DEFAULT_DRILL_MODE),
            question_count=self._planned_question_count(session_plan),
            active_question_number=self._active_question_number(session_plan),
            reference_answer=session.reference_answer,
            answer=answer_turn.content if answer_turn else None,
            feedback=feedback_turn.content if feedback_turn else None,
            overall_score=session.overall_score,
            strengths=list(session.strengths or []),
            improvements=list(session.improvements or []),
            suggested_followup=session.suggested_followup,
            next_question=next_question,
            next_prompt_type=next_prompt_type,
            current_round=current_round,
            max_rounds=max_rounds,
            can_continue=can_continue,
            status=session.status,
            summary=summary_turn.content if summary_turn else None,
            summary_meta=summary_turn.meta_json if summary_turn and isinstance(summary_turn.meta_json, dict) else None,
            started_at=session.started_at,
            updated_at=session.updated_at,
            turns=[InterviewTurnResponse.model_validate(turn) for turn in turns],
        )

    def delete_session(self, user_id: int, session_id: str) -> bool:
        session = self._get_session_entity(user_id, session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        logger.info("interview_session_deleted user_id=%s session_id=%s", user_id, session_id)
        return True

    def _build_session_list_item(self, session: InterviewSession) -> InterviewSessionListItemResponse:
        session_plan = self._get_session_plan(session)
        return InterviewSessionListItemResponse(
            session_id=session.id,
            knowledge_base_id=session.knowledge_base_id,
            question_id=session.question_id,
            question=session.question,
            source_document_id=session.question_bank_item.source_document_id if session.question_bank_item else None,
            source_document_name=(
                session.question_bank_item.source_document.file_name
                if session.question_bank_item and session.question_bank_item.source_document
                else None
            ),
            focus_topic=self._plan_value(session_plan, "focus_topic", None),
            difficulty=session.question_bank_item.difficulty if session.question_bank_item else None,
            question_tags=self._question_tags(session.question_bank_item),
            question_strategy=self._plan_value(session_plan, "question_strategy", self.DEFAULT_QUESTION_STRATEGY),
            drill_mode=self._plan_value(session_plan, "drill_mode", self.DEFAULT_DRILL_MODE),
            question_count=self._planned_question_count(session_plan),
            active_question_number=self._active_question_number(session_plan),
            status=session.status,
            overall_score=session.overall_score,
            started_at=session.started_at,
            updated_at=session.updated_at,
            current_round=self._current_round(session),
        )

    def _get_session_entity(self, user_id: int, session_id: str) -> InterviewSession | None:
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def _ensure_kb_access(self, user_id: int, knowledge_base_id: int) -> None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.user_id == user_id)
        kb = self.db.scalar(stmt)
        if not kb:
            raise ValueError("Knowledge base not found.")

    def _ensure_document_access(self, user_id: int, knowledge_base_id: int, document_id: int) -> None:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == "completed",
        )
        document = self.db.scalar(stmt)
        if not document:
            raise ValueError("The selected source document is unavailable or has not finished ingestion.")

    def _select_questions(
        self,
        *,
        user_id: int,
        knowledge_base_id: int,
        question_id: int | None,
        source_document_id: int | None,
        focus_topic: str | None,
        difficulty: str | None = None,
        question_type: str | None = None,
        question_strategy: str = DEFAULT_QUESTION_STRATEGY,
        question_count: int = 1,
    ) -> list[QuestionBank]:
        stmt = select(QuestionBank).where(
            QuestionBank.user_id == user_id,
            QuestionBank.knowledge_base_id == knowledge_base_id,
        )
        if question_id is not None:
            stmt = stmt.where(QuestionBank.id == question_id)
            question = self.db.scalar(stmt)
            return [question] if question else []

        normalized_difficulty = self._normalize_optional_filter(difficulty)
        normalized_question_type = self._normalize_optional_filter(question_type)
        if source_document_id is not None:
            stmt = stmt.where(QuestionBank.source_document_id == source_document_id)
        if normalized_difficulty:
            stmt = stmt.where(QuestionBank.difficulty == normalized_difficulty)

        items = list(self.db.scalars(stmt.order_by(QuestionBank.created_at.desc())))
        if normalized_question_type:
            items = [
                item
                for item in items
                if normalized_question_type in {tag.lower() for tag in self._question_tags(item)}
            ]
        if not items:
            return []

        ordered_items = self._apply_question_strategy(
            user_id=user_id,
            items=items,
            question_strategy=question_strategy,
        )
        ordered_items = self._apply_focus_topic_priority(ordered_items, focus_topic)
        if not ordered_items:
            return []

        return ordered_items[: max(1, question_count)]

    def _apply_question_strategy(
        self,
        *,
        user_id: int,
        items: list[QuestionBank],
        question_strategy: str,
    ) -> list[QuestionBank]:
        normalized_strategy = self._normalize_question_strategy(question_strategy)
        if normalized_strategy == "recent_first":
            return items

        if normalized_strategy == "avoid_recent":
            recent_question_ids = self._recent_question_ids(user_id=user_id, limit=min(len(items), 5))
            filtered_items = [item for item in items if item.id not in recent_question_ids]
            return filtered_items or items

        shuffled_items = list(items[: min(10, len(items))])
        random.shuffle(shuffled_items)
        return shuffled_items

    def _apply_focus_topic_priority(self, items: list[QuestionBank], focus_topic: str | None) -> list[QuestionBank]:
        normalized_focus = self._normalize_focus_topic(focus_topic)
        if not normalized_focus:
            return items

        focus_tokens = self._tokenize(normalized_focus)
        if not focus_tokens:
            return items

        scored_items = [
            (self._focus_match_score(item, normalized_focus, focus_tokens), index, item)
            for index, item in enumerate(items)
        ]
        max_score = max(score for score, _index, _item in scored_items)
        if max_score <= 0:
            return items

        scored_items.sort(key=lambda entry: (-entry[0], entry[1]))
        return [item for _score, _index, item in scored_items]

    def _focus_match_score(self, item: QuestionBank, focus_topic: str, focus_tokens: set[str]) -> int:
        score = 0
        text_parts = [
            item.question or "",
            item.reference_answer or "",
            " ".join(self._question_tags(item)),
            item.source_document.file_name if item.source_document else "",
        ]
        searchable_text = " ".join(text_parts).lower()
        if focus_topic.lower() in searchable_text:
            score += 5

        item_tokens = self._tokenize(searchable_text)
        overlap = len(focus_tokens & item_tokens)
        score += overlap * 2

        normalized_tags = {tag.lower() for tag in self._question_tags(item)}
        if any(token in normalized_tags for token in focus_tokens):
            score += 2
        return score

    def _advance_to_next_primary_question(
        self,
        *,
        session: InterviewSession,
        session_plan: dict,
        current_round: int,
        timestamp: datetime,
    ) -> QuestionBank | None:
        selected_question_ids = session_plan.get("selected_question_ids")
        if not isinstance(selected_question_ids, list):
            return None

        next_index = int(session_plan.get("current_question_index", 0)) + 1
        if next_index >= len(selected_question_ids):
            return None

        next_question_id = selected_question_ids[next_index]
        next_question = self.db.get(QuestionBank, next_question_id)
        if not next_question:
            return None

        session.question_id = next_question.id
        session.question = next_question.question
        session.reference_answer = next_question.reference_answer
        session_plan["current_question_index"] = next_index
        self._update_session_plan(session, session_plan)
        self.db.add(
            InterviewTurn(
                session_id=session.id,
                role="interviewer",
                content=next_question.question,
                meta_json={
                    "round": current_round + 1,
                    "question_id": next_question.id,
                    "reference_answer": next_question.reference_answer,
                    "question_type": "planned",
                    "source_document_id": next_question.source_document_id,
                    "source_document_name": next_question.source_document.file_name if next_question.source_document else None,
                    "question_number": next_index + 1,
                },
                created_at=timestamp,
            )
        )
        return next_question

    def _recent_question_ids(self, *, user_id: int, limit: int) -> set[int]:
        stmt = (
            select(InterviewSession.question_id)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
            .limit(limit)
        )
        return {question_id for question_id in self.db.scalars(stmt) if question_id is not None}

    def _generate_feedback(self, *, question: str, reference_answer: str | None, answer: str) -> dict:
        try:
            return self._generate_feedback_with_model(question=question, reference_answer=reference_answer, answer=answer)
        except (ValueError, ChatProviderError, json.JSONDecodeError) as exc:
            logger.warning("interview_feedback_model_fallback reason=%s", exc)
            return self._generate_feedback_locally(question=question, reference_answer=reference_answer, answer=answer)

    def _generate_feedback_with_model(self, *, question: str, reference_answer: str | None, answer: str) -> dict:
        agent_config = get_agent_config().interview_agent
        system_prompt = "You are an interview evaluator. Review the candidate answer and return strict JSON only."
        user_prompt = (
            "Please review the candidate answer and return a JSON object only.\n"
            "Required keys: feedback, overall_score, strengths, improvements, suggested_followup.\n"
            "overall_score must be an integer from 1 to 10. strengths and improvements must be string arrays.\n"
            "suggested_followup should be one natural follow-up question, or an empty string when no follow-up is needed.\n"
            "Do not output anything outside JSON.\n\n"
            f"Question: {question}\n\n"
            f"Reference answer: {reference_answer or 'N/A'}\n\n"
            f"Candidate answer: {answer}\n\n"
            f"Focus dimensions: {', '.join(agent_config.score_dimensions) if agent_config.score_dimensions else 'logic, completeness, expression'}"
        )
        raw = QwenChatProvider().generate_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Interview feedback model did not return a JSON object")

        overall_score = int(data.get("overall_score", 0))
        return {
            "feedback": str(data.get("feedback", "")).strip() or "The answer has been reviewed.",
            "overall_score": max(1, min(overall_score, 10)) if overall_score else 6,
            "strengths": [str(item).strip() for item in data.get("strengths", []) if str(item).strip()],
            "improvements": [str(item).strip() for item in data.get("improvements", []) if str(item).strip()],
            "suggested_followup": str(data.get("suggested_followup", "")).strip() or None,
        }

    def _generate_feedback_locally(self, *, question: str, reference_answer: str | None, answer: str) -> dict:
        normalized_answer = self._tokenize(answer)
        normalized_reference = self._tokenize(reference_answer or "")
        overlap = len(normalized_answer & normalized_reference)
        reference_size = max(len(normalized_reference), 1)
        ratio = overlap / reference_size

        if ratio >= 0.5:
            score = 8
            strengths = [
                "The answer covers a good portion of the expected reference points.",
                "The response direction is aligned with the question.",
            ]
            improvements = ["Add one or two concrete examples or implementation details."]
        elif ratio >= 0.25:
            score = 6
            strengths = [
                "The answer captures part of the core concept.",
                "A basic response structure is present.",
            ]
            improvements = [
                "Fill in the missing edge cases and key details.",
                "Use a clearer structure to organize the answer.",
            ]
        else:
            score = 4
            strengths = ["The candidate has started addressing the topic."]
            improvements = [
                "The overlap with the expected reference points is limited.",
                "Define the concept first, then explain scenarios, details, and trade-offs.",
            ]

        feedback = (
            f"Question: {question}\n"
            f"Current estimated score: {score}/10.\n"
            "A stronger answer should clarify the definition, use cases, key mechanism, and likely follow-up angles."
        )
        followup = "If you had to explain this through a real project example, how would you describe the implementation and trade-offs?"
        return {
            "feedback": feedback,
            "overall_score": score,
            "strengths": strengths,
            "improvements": improvements,
            "suggested_followup": followup,
        }

    def _create_or_update_summary_turn(
        self,
        *,
        session: InterviewSession,
        latest_answer: str,
        latest_feedback: dict,
    ) -> tuple[str, dict]:
        summary_text, summary_meta = self._generate_session_summary(
            session=session,
            latest_answer=latest_answer,
            latest_feedback=latest_feedback,
        )
        now = datetime.now(timezone.utc)
        existing_summary_turn = next((turn for turn in reversed(session.turns) if turn.role == "interview_summary"), None)
        if existing_summary_turn:
            existing_summary_turn.content = summary_text
            existing_summary_turn.meta_json = summary_meta
            existing_summary_turn.created_at = now
        else:
            self.db.add(
                InterviewTurn(
                    session_id=session.id,
                    role="interview_summary",
                    content=summary_text,
                    meta_json=summary_meta,
                    created_at=now,
                )
            )
        return summary_text, summary_meta

    def _generate_session_summary(
        self,
        *,
        session: InterviewSession,
        latest_answer: str,
        latest_feedback: dict,
    ) -> tuple[str, dict]:
        try:
            return self._generate_session_summary_with_model(
                session=session,
                latest_answer=latest_answer,
                latest_feedback=latest_feedback,
            )
        except (ValueError, ChatProviderError, json.JSONDecodeError) as exc:
            logger.warning("interview_summary_model_fallback session_id=%s reason=%s", session.id, exc)
            return self._generate_session_summary_locally(
                session=session,
                latest_answer=latest_answer,
                latest_feedback=latest_feedback,
            )

    def _generate_session_summary_with_model(
        self,
        *,
        session: InterviewSession,
        latest_answer: str,
        latest_feedback: dict,
    ) -> tuple[str, dict]:
        system_prompt = get_prompt_text("interview_summary").strip()
        transcript = self._build_interview_transcript(session)
        user_prompt = (
            "Please summarize the interview transcript below and return a JSON object only.\n"
            "Required keys: summary, highlights, weak_points, next_actions.\n"
            "summary should be one concise paragraph. The other keys must be arrays of strings.\n"
            "Do not output anything outside JSON.\n\n"
            f"Session status: {session.status}\n"
            f"Overall score: {session.overall_score or latest_feedback.get('overall_score') or 0}/10\n"
            f"Latest answer: {latest_answer}\n"
            f"Latest feedback: {latest_feedback.get('feedback', '')}\n\n"
            f"Transcript:\n{transcript}"
        )
        raw = QwenChatProvider().generate_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Interview summary model did not return a JSON object")

        summary = str(data.get("summary", "")).strip()
        if not summary:
            raise ValueError("Interview summary is empty")
        meta = {
            "highlights": [str(item).strip() for item in data.get("highlights", []) if str(item).strip()],
            "weak_points": [str(item).strip() for item in data.get("weak_points", []) if str(item).strip()],
            "next_actions": [str(item).strip() for item in data.get("next_actions", []) if str(item).strip()],
            "overall_score": session.overall_score or latest_feedback.get("overall_score"),
        }
        return summary, meta

    def _generate_session_summary_locally(
        self,
        *,
        session: InterviewSession,
        latest_answer: str,
        latest_feedback: dict,
    ) -> tuple[str, dict]:
        score = session.overall_score or latest_feedback.get("overall_score") or 0
        strengths = list(session.strengths or latest_feedback.get("strengths") or [])
        improvements = list(session.improvements or latest_feedback.get("improvements") or [])
        suggested_followup = session.suggested_followup or latest_feedback.get("suggested_followup")
        answered_rounds = max(len([turn for turn in session.turns if turn.role == "candidate"]), 1)

        summary = (
            f"This interview session is complete after {answered_rounds} answer rounds, with an overall score of {score}/10. "
            f"Main strengths: {self._join_items(strengths, fallback='a workable baseline answer structure')}. "
            f"Main improvements: {self._join_items(improvements, fallback='more complete coverage and deeper detail')}. "
            "For the next round of practice, strengthen examples, trade-offs, and edge-case handling."
        )
        next_actions = list(improvements[:2]) or [
            "Review the core concept, workflow, and boundary conditions.",
            "Prepare one or two project examples that can be narrated clearly.",
        ]
        if suggested_followup:
            next_actions.append(f"Self-drill follow-up: {suggested_followup}")

        meta = {
            "highlights": strengths or ["A baseline response direction is present."],
            "weak_points": improvements or ["The answer can be more structured and more detailed."],
            "next_actions": next_actions,
            "overall_score": score,
            "latest_answer_excerpt": latest_answer[:120],
        }
        return summary, meta

    def _generate_followup_question(
        self,
        *,
        question: str,
        answer: str,
        feedback: str,
        suggested_followup: str | None,
        current_round: int,
    ) -> str | None:
        if suggested_followup:
            return suggested_followup

        try:
            return self._generate_followup_with_model(
                question=question,
                answer=answer,
                feedback=feedback,
                current_round=current_round,
            )
        except (ValueError, ChatProviderError) as exc:
            logger.warning("interview_followup_model_fallback round=%s reason=%s", current_round, exc)
            return self._generate_followup_locally(question=question, feedback=feedback)

    def _generate_followup_with_model(self, *, question: str, answer: str, feedback: str, current_round: int) -> str:
        system_prompt = (
            "You are an interview agent that asks one concise follow-up question at a time. "
            "The follow-up should probe depth, trade-offs, concrete examples, or edge cases."
        )
        user_prompt = (
            f"Current round: {current_round}\n"
            f"Original or current question: {question}\n"
            f"Candidate answer: {answer}\n"
            f"Feedback summary: {feedback}\n\n"
            "Generate exactly one short follow-up question in Chinese."
        )
        response = QwenChatProvider().generate_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        followup = response.strip().strip('"')
        return followup or None

    def _generate_followup_locally(self, *, question: str, feedback: str) -> str:
        lowered_feedback = feedback.lower()
        if "scenario" in lowered_feedback or "example" in lowered_feedback:
            return "Can you walk through one real project scenario and explain how you would implement this in practice?"
        if "edge" in lowered_feedback or "risk" in lowered_feedback:
            return "How would you handle edge cases, risks, or failure scenarios for this topic in a production system?"
        return f"For the topic '{question}', can you add one more concrete example and explain the trade-offs involved?"

    def _build_interview_transcript(self, session: InterviewSession) -> str:
        role_labels = {
            "interviewer": "Interviewer question",
            "interviewer_followup": "Interviewer follow-up",
            "candidate": "Candidate answer",
            "interviewer_feedback": "System feedback",
        }
        turns = sorted(session.turns, key=lambda item: item.created_at)
        lines = []
        for turn in turns:
            if turn.role == "interview_summary":
                continue
            lines.append(f"{role_labels.get(turn.role, turn.role)}: {turn.content}")
        return "\n".join(lines)

    def _pending_prompt(self, session: InterviewSession) -> tuple[str | None, str | None]:
        if session.status == "completed":
            return None, None

        turns = sorted(session.turns, key=lambda item: item.created_at)
        latest_question_turn = next(
            (turn for turn in reversed(turns) if turn.role in {"interviewer", "interviewer_followup"}),
            None,
        )
        latest_answer_turn = next((turn for turn in reversed(turns) if turn.role == "candidate"), None)
        if not latest_question_turn or not latest_answer_turn:
            return None, None
        if latest_question_turn.created_at <= latest_answer_turn.created_at:
            return None, None
        return (
            latest_question_turn.content,
            "followup" if latest_question_turn.role == "interviewer_followup" else "next_question",
        )

    def _session_analysis_lists(self, session: InterviewSession) -> tuple[list[str], list[str]]:
        summary_turn = next((turn for turn in reversed(session.turns) if turn.role == "interview_summary"), None)
        meta = summary_turn.meta_json if summary_turn and isinstance(summary_turn.meta_json, dict) else {}

        weak_points = list(session.improvements or [])
        strengths = list(session.strengths or [])

        meta_weak_points = meta.get("weak_points")
        if isinstance(meta_weak_points, list):
            weak_points.extend(str(item).strip() for item in meta_weak_points if str(item).strip())

        meta_highlights = meta.get("highlights")
        if isinstance(meta_highlights, list):
            strengths.extend(str(item).strip() for item in meta_highlights if str(item).strip())

        return self._dedupe_non_empty(weak_points), self._dedupe_non_empty(strengths)

    def _get_session_plan(self, session: InterviewSession) -> dict:
        turns = sorted(session.turns, key=lambda item: item.created_at)
        initial_turn = next((turn for turn in turns if turn.role == "interviewer"), None)
        if not initial_turn or not isinstance(initial_turn.meta_json, dict):
            return self._default_session_plan(session.question_id)

        plan = initial_turn.meta_json.get("session_plan")
        if not isinstance(plan, dict):
            return self._default_session_plan(session.question_id)
        return dict(plan)

    def _update_session_plan(self, session: InterviewSession, session_plan: dict) -> None:
        turns = sorted(session.turns, key=lambda item: item.created_at)
        initial_turn = next((turn for turn in turns if turn.role == "interviewer"), None)
        if not initial_turn:
            return
        meta = dict(initial_turn.meta_json or {})
        meta["session_plan"] = session_plan
        initial_turn.meta_json = meta

    def _default_session_plan(self, question_id: int) -> dict:
        return {
            "drill_mode": self.DEFAULT_DRILL_MODE,
            "question_count": 1,
            "question_strategy": self.DEFAULT_QUESTION_STRATEGY,
            "focus_topic": None,
            "selected_question_ids": [question_id],
            "current_question_index": 0,
        }

    def _plan_value(self, session_plan: dict, key: str, default: str | None) -> str | None:
        value = session_plan.get(key)
        return str(value) if value is not None else default

    def _planned_question_count(self, session_plan: dict) -> int:
        selected_question_ids = session_plan.get("selected_question_ids")
        if isinstance(selected_question_ids, list) and selected_question_ids:
            return len(selected_question_ids)
        value = session_plan.get("question_count")
        if isinstance(value, int) and value > 0:
            return value
        return 1

    def _active_question_number(self, session_plan: dict) -> int:
        current_index = session_plan.get("current_question_index")
        if not isinstance(current_index, int):
            return 1
        return current_index + 1

    def _counter_to_items(self, counter: Counter[str], limit: int = 5) -> list[TrainingAnalysisCountItem]:
        return [
            TrainingAnalysisCountItem(label=label, count=count)
            for label, count in counter.most_common(limit)
        ]

    def _build_recommended_focus(
        self,
        *,
        average_score: float | None,
        weak_point_counter: Counter[str],
        question_type_counter: Counter[str],
        source_document_counter: Counter[str],
    ) -> list[str]:
        recommendations: list[str] = []
        if average_score is not None:
            if average_score < 6:
                recommendations.append("Average interview scores are still below 6.0, so prioritize answer structure, completeness, and concrete examples.")
            elif average_score < 8:
                recommendations.append("Scores are stable but still have room to grow. Focus on deeper trade-offs, edge cases, and implementation detail.")

        top_weak_points = [label for label, _count in weak_point_counter.most_common(2)]
        if top_weak_points:
            recommendations.append(f"Most repeated weak points: {', '.join(top_weak_points)}.")

        top_question_type = next(iter(question_type_counter.most_common(1)), None)
        if top_question_type:
            recommendations.append(f"Spend one dedicated drill block on {top_question_type[0]} questions to improve consistency in that category.")

        top_document = next(iter(source_document_counter.most_common(1)), None)
        if top_document:
            recommendations.append(f"Review the source material '{top_document[0]}' because it appears most often in your recent interview practice.")

        if not recommendations:
            recommendations.append("Complete more interview sessions to unlock stable training analysis and focus suggestions.")
        return recommendations[:4]

    def _build_focus_drills(
        self,
        *,
        knowledge_base_id: int | None,
        weak_point_counter: Counter[str],
        question_type_counter: Counter[str],
        source_document_id_counter: Counter[int],
        source_document_names_by_id: dict[int, str],
    ) -> list[TrainingDrillRecommendation]:
        top_document = next(iter(source_document_id_counter.most_common(1)), None)
        source_document_id = top_document[0] if top_document else None
        source_document_name = source_document_names_by_id.get(source_document_id) if source_document_id is not None else None
        fallback_question_type = self._format_question_type_value(next(iter(question_type_counter.most_common(1)), ("Concept", 0)))[0]

        recommendations: list[TrainingDrillRecommendation] = []
        for weak_point, count in weak_point_counter.most_common(3):
            suggested_question_type = self._infer_question_type_from_weak_point(weak_point) or fallback_question_type
            recommendations.append(
                TrainingDrillRecommendation(
                    focus_label=weak_point,
                    title=f"Weak-Point Drill: {self._shorten_label(weak_point)}",
                    description=(
                        f"This issue appeared in {count} completed sessions. "
                        f"Start a focused {self._format_question_type_label(suggested_question_type)} drill to practice this weakness with repeated interview questions."
                    ),
                    knowledge_base_id=knowledge_base_id,
                    source_document_id=source_document_id,
                    source_document_name=source_document_name,
                    question_type=suggested_question_type,
                    drill_mode="question_set",
                    question_count=3,
                    question_strategy="avoid_recent",
                )
            )

        return recommendations

    def _build_focus_drill_effects(
        self,
        focus_sessions_by_topic: dict[str, list[InterviewSession]],
    ) -> list[TrainingFocusEffectItem]:
        effects: list[TrainingFocusEffectItem] = []
        for focus_label, sessions in focus_sessions_by_topic.items():
            completed_scores = [session.overall_score for session in sessions if session.overall_score is not None]
            if not completed_scores:
                continue

            ordered_sessions = sorted(sessions, key=lambda item: item.started_at)
            latest_session = max(sessions, key=lambda item: item.started_at)
            first_score = ordered_sessions[0].overall_score or 0
            latest_score = latest_session.overall_score or 0
            average_score = round(sum(completed_scores) / len(completed_scores), 2)
            best_score = max(completed_scores)
            score_delta = round(latest_score - first_score, 2)

            effects.append(
                TrainingFocusEffectItem(
                    focus_label=focus_label,
                    session_count=len(completed_scores),
                    average_score=average_score,
                    latest_score=latest_score,
                    best_score=best_score,
                    score_delta=score_delta,
                    last_practiced_at=latest_session.started_at,
                )
            )

        effects.sort(key=lambda item: item.last_practiced_at, reverse=True)
        return effects[:6]

    def _dedupe_non_empty(self, values: list[str]) -> list[str]:
        deduped: list[str] = []
        for value in values:
            normalized = str(value).strip()
            if normalized and normalized not in deduped:
                deduped.append(normalized)
        return deduped

    def _current_round(self, session: InterviewSession) -> int:
        question_turns = [turn for turn in session.turns if turn.role in {"interviewer", "interviewer_followup"}]
        return max(len(question_turns), 1)

    def _question_for_round(self, session: InterviewSession, round_number: int) -> str:
        turns = sorted(session.turns, key=lambda item: item.created_at)
        question_turns = [turn for turn in turns if turn.role in {"interviewer", "interviewer_followup"}]
        index = min(max(round_number - 1, 0), len(question_turns) - 1)
        return question_turns[index].content if question_turns else session.question

    def _max_rounds(self) -> int:
        return max(1, get_agent_config().interview_agent.max_followup_rounds + 1)

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]+", text.lower())
        return {word for word in words if len(word) >= 2}

    def _join_items(self, items: list[str], *, fallback: str) -> str:
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            return fallback
        return "; ".join(cleaned[:3])

    def _normalize_optional_filter(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    def _normalize_focus_topic(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _normalize_question_strategy(self, value: str | None) -> str:
        normalized = self._normalize_optional_filter(value)
        if not normalized:
            return self.DEFAULT_QUESTION_STRATEGY
        if normalized not in self.SUPPORTED_QUESTION_STRATEGIES:
            supported = ", ".join(sorted(self.SUPPORTED_QUESTION_STRATEGIES))
            raise ValueError(f"Unsupported question strategy '{value}'. Supported values: {supported}.")
        return normalized

    def _normalize_drill_mode(self, value: str | None) -> str:
        normalized = self._normalize_optional_filter(value)
        if not normalized:
            return self.DEFAULT_DRILL_MODE
        if normalized not in self.SUPPORTED_DRILL_MODES:
            supported = ", ".join(sorted(self.SUPPORTED_DRILL_MODES))
            raise ValueError(f"Unsupported drill mode '{value}'. Supported values: {supported}.")
        return normalized

    def _normalize_question_count(self, *, drill_mode: str, question_count: int | None) -> int:
        if drill_mode == "single_question":
            return 1

        if question_count is None:
            return self.DEFAULT_QUESTION_SET_COUNT
        normalized = max(1, min(int(question_count), self.MAX_QUESTION_SET_COUNT))
        return normalized

    def _format_question_type_label(self, value: str) -> str:
        normalized = value.strip().lower()
        mapping = {
            "concept": "Concept",
            "scenario": "Scenario",
            "followup": "Follow-up",
            "design": "Design",
        }
        return mapping.get(normalized, value)

    def _format_question_type_value(self, item: tuple[str, int]) -> tuple[str, int]:
        label, count = item
        normalized = label.strip().lower()
        reverse_mapping = {
            "concept": "concept",
            "scenario": "scenario",
            "follow-up": "followup",
            "followup": "followup",
            "design": "design",
        }
        return reverse_mapping.get(normalized, normalized), count

    def _infer_question_type_from_weak_point(self, weak_point: str) -> str | None:
        normalized = weak_point.lower()
        if any(keyword in normalized for keyword in ["trade-off", "architecture", "design", "权衡", "设计"]):
            return "design"
        if any(keyword in normalized for keyword in ["example", "scenario", "project", "场景", "案例", "例子"]):
            return "scenario"
        if any(keyword in normalized for keyword in ["follow-up", "追问", "deeper", "depth"]):
            return "followup"
        if any(keyword in normalized for keyword in ["structure", "definition", "concept", "完整", "结构", "定义", "概念", "细节"]):
            return "concept"
        return None

    def _shorten_label(self, value: str, limit: int = 60) -> str:
        normalized = value.strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    def _question_tags(self, question: QuestionBank | None) -> list[str]:
        if not question or not isinstance(question.tags, list):
            return []
        return [str(tag).strip() for tag in question.tags if str(tag).strip()]
