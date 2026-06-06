from __future__ import annotations

import json
import logging
import random
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

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
    InterviewTurnResponse,
)
from app.utils import get_agent_config, get_prompt_text

logger = logging.getLogger("app.services.interview")


class InterviewService:
    def __init__(self, db: Session):
        self.db = db

    def start_session(self, user_id: int, payload: InterviewStartRequest) -> InterviewStartResponse:
        self._ensure_kb_access(user_id, payload.knowledge_base_id)
        question = self._select_question(
            user_id,
            payload.knowledge_base_id,
            payload.question_id,
            payload.difficulty,
            payload.question_type,
        )
        if not question:
            if payload.difficulty or payload.question_type:
                raise ValueError("当前筛选条件下没有可用题目，请调整难度或题型后重试。")
            raise ValueError("当前知识库下还没有题目，请先生成题目。")

        now = datetime.now(timezone.utc)
        session = InterviewSession(
            id=uuid4().hex,
            user_id=user_id,
            knowledge_base_id=payload.knowledge_base_id,
            question_id=question.id,
            question=question.question,
            reference_answer=question.reference_answer,
            status="awaiting_answer",
            started_at=now,
            strengths=[],
            improvements=[],
        )
        self.db.add(session)
        self.db.flush()
        self.db.add(
            InterviewTurn(
                session_id=session.id,
                role="interviewer",
                content=question.question,
                meta_json={
                    "round": 1,
                    "question_id": question.id,
                    "reference_answer": question.reference_answer,
                    "question_type": "initial",
                },
                created_at=now,
            )
        )
        self.db.commit()
        self.db.refresh(session)
        logger.info(
            "interview_session_started user_id=%s knowledge_base_id=%s question_id=%s session_id=%s",
            user_id,
            payload.knowledge_base_id,
            question.id,
            session.id,
        )
        return InterviewStartResponse(
            session_id=session.id,
            knowledge_base_id=session.knowledge_base_id,
            question_id=session.question_id,
            question=session.question,
            difficulty=question.difficulty,
            question_tags=self._question_tags(question),
            status=session.status,
            started_at=session.started_at,
        )

    def submit_answer(self, user_id: int, payload: InterviewAnswerRequest) -> InterviewFeedbackResponse:
        session = self._get_session_entity(user_id, payload.session_id)
        if not session:
            raise ValueError("面试会话不存在或已失效。")
        if session.status == "completed":
            raise ValueError("当前面试会话已经结束，请开始新的面试。")

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
                meta_json={"round": current_round},
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
                self.db.add(
                    InterviewTurn(
                        session_id=session.id,
                        role="interviewer_followup",
                        content=next_question,
                        meta_json={
                            "round": current_round + 1,
                            "question_type": "followup",
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
            session.status = "completed"
            session.finished_at = now
            next_question = None
            summary_text, summary_meta = self._create_or_update_summary_turn(
                session=session,
                latest_answer=payload.answer,
                latest_feedback=feedback,
            )

        session.updated_at = now
        self.db.commit()
        self.db.refresh(session)
        logger.info(
            "interview_feedback_generated user_id=%s session_id=%s round=%s score=%s can_continue=%s",
            user_id,
            session.id,
            current_round,
            session.overall_score,
            can_continue,
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
            current_round=current_round,
            max_rounds=max_rounds,
            can_continue=can_continue,
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
            InterviewSessionListItemResponse(
                session_id=item.id,
                knowledge_base_id=item.knowledge_base_id,
                question_id=item.question_id,
                question=item.question,
                difficulty=item.question_bank_item.difficulty if item.question_bank_item else None,
                question_tags=self._question_tags(item.question_bank_item),
                status=item.status,
                overall_score=item.overall_score,
                started_at=item.started_at,
                updated_at=item.updated_at,
                current_round=self._current_round(item),
            )
            for item in sessions
        ]

    def get_session(self, user_id: int, session_id: str) -> InterviewSessionDetailResponse | None:
        session = self._get_session_entity(user_id, session_id)
        if not session:
            return None

        turns = sorted(session.turns, key=lambda item: item.created_at)
        answer_turn = next((turn for turn in reversed(turns) if turn.role == "candidate"), None)
        feedback_turn = next((turn for turn in reversed(turns) if turn.role == "interviewer_feedback"), None)
        followup_turn = next((turn for turn in reversed(turns) if turn.role == "interviewer_followup"), None)
        summary_turn = next((turn for turn in reversed(turns) if turn.role == "interview_summary"), None)
        current_round = self._current_round(session)
        max_rounds = self._max_rounds()
        can_continue = session.status in {"awaiting_answer", "awaiting_followup_answer"} and current_round <= max_rounds

        return InterviewSessionDetailResponse(
            session_id=session.id,
            knowledge_base_id=session.knowledge_base_id,
            question_id=session.question_id,
            question=session.question,
            difficulty=session.question_bank_item.difficulty if session.question_bank_item else None,
            question_tags=self._question_tags(session.question_bank_item),
            reference_answer=session.reference_answer,
            answer=answer_turn.content if answer_turn else None,
            feedback=feedback_turn.content if feedback_turn else None,
            overall_score=session.overall_score,
            strengths=list(session.strengths or []),
            improvements=list(session.improvements or []),
            suggested_followup=session.suggested_followup,
            next_question=followup_turn.content if session.status == "awaiting_followup_answer" and followup_turn else None,
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
            raise ValueError("知识库不存在。")

    def _select_question(
        self,
        user_id: int,
        knowledge_base_id: int,
        question_id: int | None,
        difficulty: str | None = None,
        question_type: str | None = None,
    ) -> QuestionBank | None:
        stmt = select(QuestionBank).where(
            QuestionBank.user_id == user_id,
            QuestionBank.knowledge_base_id == knowledge_base_id,
        )
        if question_id is not None:
            stmt = stmt.where(QuestionBank.id == question_id)
            return self.db.scalar(stmt)

        normalized_difficulty = self._normalize_optional_filter(difficulty)
        normalized_question_type = self._normalize_optional_filter(question_type)
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
            return None
        return random.choice(items[: min(10, len(items))])

    def _generate_feedback(self, *, question: str, reference_answer: str | None, answer: str) -> dict:
        try:
            return self._generate_feedback_with_model(question=question, reference_answer=reference_answer, answer=answer)
        except (ValueError, ChatProviderError, json.JSONDecodeError) as exc:
            logger.warning("interview_feedback_model_fallback reason=%s", exc)
            return self._generate_feedback_locally(question=question, reference_answer=reference_answer, answer=answer)

    def _generate_feedback_with_model(self, *, question: str, reference_answer: str | None, answer: str) -> dict:
        agent_config = get_agent_config().interview_agent
        system_prompt = (
            "You are an interview evaluator. Review the candidate answer and return strict JSON only."
        )
        user_prompt = (
            "请你作为面试官评估候选人的回答，并严格输出 JSON 对象。"
            "必须包含 feedback、overall_score、strengths、improvements、suggested_followup 五个字段。"
            "overall_score 只能是 1 到 10 的整数。strengths 和 improvements 必须是字符串数组。"
            "suggested_followup 应该是一句自然的追问问题；如果你认为无需继续追问，返回空字符串即可。"
            "不要输出 JSON 以外的任何内容。\n\n"
            f"题目：{question}\n\n"
            f"参考答案：{reference_answer or '暂无参考答案'}\n\n"
            f"候选人回答：{answer}\n\n"
            f"重点评分维度：{', '.join(agent_config.score_dimensions) if agent_config.score_dimensions else 'logic, completeness, expression'}"
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
            "feedback": str(data.get("feedback", "")).strip() or "本次回答已完成评估。",
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
            strengths = ["回答覆盖了较多参考要点", "整体表达方向与题目较为匹配"]
            improvements = ["可以再补充更具体的案例或工程细节"]
        elif ratio >= 0.25:
            score = 6
            strengths = ["回答抓住了部分核心概念", "具备基本作答框架"]
            improvements = ["需要补全关键细节和边界条件", "建议用更清晰的结构组织回答"]
        else:
            score = 4
            strengths = ["已经开始尝试围绕题目作答"]
            improvements = ["与参考要点的重合度较低", "建议先定义概念，再说明场景、细节和风险点"]

        feedback = (
            f"题目：{question}\n"
            f"整体评价：当前回答得分约为 {score}/10。"
            "建议优先补足定义、适用场景、关键机制和常见追问这几个部分。"
        )
        followup = "如果让你结合一个真实项目场景继续展开，你会如何说明这个知识点的落地方式？"
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
            "请你根据下面的模拟面试记录生成一个结构化总结，并严格输出 JSON 对象。"
            "必须包含 summary、highlights、weak_points、next_actions 四个字段。"
            "summary 是一段中文总结；其余三个字段必须是字符串数组。"
            "不要输出 JSON 以外的内容。\n\n"
            f"会话状态：{session.status}\n"
            f"当前总分：{session.overall_score or latest_feedback.get('overall_score') or 0}/10\n"
            f"最近一次回答：{latest_answer}\n"
            f"最近一次反馈：{latest_feedback.get('feedback', '')}\n\n"
            f"面试记录：\n{transcript}"
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
            f"本次模拟面试已完成，共进行了 {answered_rounds} 轮问答，当前综合评分为 {score}/10。"
            f" 主要亮点包括：{self._join_items(strengths, fallback='能够围绕题目进行基本作答')}。"
            f" 仍需重点提升：{self._join_items(improvements, fallback='回答的完整性与细节展开')}。"
            " 建议下一轮训练继续结合真实项目案例补充背景、方案权衡与边界处理。"
        )
        next_actions = list(improvements[:2]) or ["围绕核心概念补齐定义、流程和边界条件", "结合项目经历准备一到两个可复述的案例"]
        if suggested_followup:
            next_actions.append(f"可继续自我追问：{suggested_followup}")

        meta = {
            "highlights": strengths or ["已经形成基本作答框架"],
            "weak_points": improvements or ["答案还可以进一步增强结构化与细节深度"],
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
        if "场景" in feedback or "案例" in feedback:
            return "你能结合一个真实项目场景，把刚才的回答进一步展开到实现细节吗？"
        if "边界" in feedback or "风险" in feedback:
            return "如果把这个问题放到复杂边界条件下，你会如何处理风险和异常情况？"
        return f"围绕“{question}”，你能再补充一个更具体的例子，并说明其中的权衡吗？"

    def _build_interview_transcript(self, session: InterviewSession) -> str:
        role_labels = {
            "interviewer": "面试官题目",
            "interviewer_followup": "面试官追问",
            "candidate": "候选人回答",
            "interviewer_feedback": "系统反馈",
        }
        turns = sorted(session.turns, key=lambda item: item.created_at)
        lines = []
        for turn in turns:
            if turn.role == "interview_summary":
                continue
            lines.append(f"{role_labels.get(turn.role, turn.role)}: {turn.content}")
        return "\n".join(lines)

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
        return "；".join(cleaned[:3])

    def _normalize_optional_filter(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    def _question_tags(self, question: QuestionBank | None) -> list[str]:
        if not question or not isinstance(question.tags, list):
            return []
        return [str(tag).strip() for tag in question.tags if str(tag).strip()]
