from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.question_bank import QuestionBank
from app.rag.generators.qwen_chat import ChatProviderError, QwenChatProvider
from app.schemas.question_bank import (
    QuestionBankGenerateRequest,
    QuestionBankGenerateResponse,
    QuestionBankItemResponse,
)
from app.services.document_service import DocumentService
from app.utils import get_agent_config, get_prompt_text

logger = logging.getLogger("app.services.question_bank")


QUESTION_TYPE_TAGS = {"concept", "scenario", "followup", "design"}


@dataclass
class GeneratedQuestionDraft:
    question: str
    reference_answer: str
    tags: list[str]
    difficulty: str


class QuestionBankService:
    def __init__(self, db: Session):
        self.db = db

    def generate_questions(self, user_id: int, payload: QuestionBankGenerateRequest) -> QuestionBankGenerateResponse:
        knowledge_base = self._get_knowledge_base(user_id, payload.knowledge_base_id)
        if not knowledge_base:
            raise ValueError("知识库不存在")

        documents = self._get_target_documents(user_id, payload)
        if not documents:
            raise ValueError("当前知识库下没有可用于抽题的已完成文档")

        generation_config = get_agent_config().question_generation
        requested_max = payload.max_questions or generation_config.max_questions_per_document
        max_questions = max(1, min(requested_max, generation_config.max_questions_per_document))

        existing_questions = {
            item.question.strip()
            for item in self.list_items(
                user_id=user_id,
                knowledge_base_id=payload.knowledge_base_id,
                document_id=payload.document_id,
            )
        }

        generated_items: list[QuestionBank] = []
        per_document_limit = max(1, max_questions // max(len(documents), 1))
        remaining = max_questions

        for index, document in enumerate(documents):
            if remaining <= 0:
                break

            current_limit = remaining if index == len(documents) - 1 else min(remaining, per_document_limit)
            document_items = self._generate_for_document(
                user_id=user_id,
                document=document,
                difficulty=generation_config.default_difficulty,
                existing_questions=existing_questions,
                limit=current_limit,
            )
            generated_items.extend(document_items)
            remaining -= len(document_items)

        if generated_items:
            self.db.add_all(generated_items)
            self.db.commit()
            for item in generated_items:
                self.db.refresh(item)

        message = (
            f"已生成 {len(generated_items)} 道题目。"
            if generated_items
            else "没有生成新的题目，请尝试上传内容更完整的资料或放宽文档范围。"
        )
        return QuestionBankGenerateResponse(
            status="completed",
            message=message,
            knowledge_base_id=payload.knowledge_base_id,
            document_id=payload.document_id,
            generated_count=len(generated_items),
            items=[QuestionBankItemResponse.model_validate(item) for item in generated_items],
        )

    def list_items(self, user_id: int, knowledge_base_id: int | None, document_id: int | None) -> list[QuestionBank]:
        stmt = select(QuestionBank).where(QuestionBank.user_id == user_id)
        if knowledge_base_id is not None:
            stmt = stmt.where(QuestionBank.knowledge_base_id == knowledge_base_id)
        if document_id is not None:
            stmt = stmt.where(QuestionBank.source_document_id == document_id)
        stmt = stmt.order_by(QuestionBank.created_at.desc())
        return list(self.db.scalars(stmt))

    def _get_knowledge_base(self, user_id: int, knowledge_base_id: int) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def _get_target_documents(self, user_id: int, payload: QuestionBankGenerateRequest) -> list[Document]:
        stmt = select(Document).where(
            Document.user_id == user_id,
            Document.knowledge_base_id == payload.knowledge_base_id,
            Document.status == "completed",
        )
        if payload.document_id is not None:
            stmt = stmt.where(Document.id == payload.document_id)
        stmt = stmt.order_by(Document.updated_at.desc())
        return list(self.db.scalars(stmt))

    def _generate_for_document(
        self,
        *,
        user_id: int,
        document: Document,
        difficulty: str,
        existing_questions: set[str],
        limit: int,
    ) -> list[QuestionBank]:
        chunks = DocumentService(self.db).get_chunks(user_id, document.id)
        if not chunks:
            return []

        generated: list[QuestionBank] = []
        for chunk in chunks:
            if len(generated) >= limit:
                break

            remaining = limit - len(generated)
            drafts = self._generate_chunk_drafts(
                document=document,
                chunk=chunk,
                difficulty=difficulty,
                limit=min(remaining, 2),
            )

            for draft in drafts:
                question_text = draft.question.strip()
                if not question_text or question_text in existing_questions:
                    continue

                generated.append(
                    QuestionBank(
                        user_id=user_id,
                        knowledge_base_id=document.knowledge_base_id,
                        source_document_id=document.id,
                        question=question_text,
                        reference_answer=draft.reference_answer.strip() or None,
                        tags=draft.tags,
                        difficulty=draft.difficulty,
                    )
                )
                existing_questions.add(question_text)

                if len(generated) >= limit:
                    break

        return generated

    def _generate_chunk_drafts(
        self,
        *,
        document: Document,
        chunk: dict,
        difficulty: str,
        limit: int,
    ) -> list[GeneratedQuestionDraft]:
        try:
            drafts = self._generate_with_model(document=document, chunk=chunk, difficulty=difficulty, limit=limit)
            if drafts:
                return drafts
        except (ValueError, ChatProviderError, json.JSONDecodeError) as exc:
            logger.warning(
                "question_generation_model_fallback document_id=%s chunk_index=%s reason=%s",
                document.id,
                chunk.get("chunk_index"),
                exc,
            )
        return self._generate_with_local_rules(document=document, chunk=chunk, difficulty=difficulty, limit=limit)

    def _generate_with_model(
        self,
        *,
        document: Document,
        chunk: dict,
        difficulty: str,
        limit: int,
    ) -> list[GeneratedQuestionDraft]:
        system_prompt = get_prompt_text("question_generation").strip()
        section_title = str(chunk.get("section_title") or "未命名章节").strip()
        content = str(chunk.get("content") or "").strip()
        if not content:
            return []

        document_kind = document.document_kind or "general"
        content_type_hint = str(chunk.get("content_type_hint") or "general").strip()
        question_shape = "yes" if chunk.get("starts_with_question") else "no"

        user_prompt = (
            "请基于下面的文档片段生成面试题，并严格输出 JSON 数组。"
            "每个元素必须包含 question、reference_answer、tags 四个字段。"
            "tags 至少包含一个题型标签，可选值为 concept、scenario、followup、design。"
            "如果文档本身不是问答格式，也要从概念、原理、区别、场景、权衡和实现细节中抽取出合适的面试题。"
            "不要输出任何 JSON 以外的解释。\n\n"
            f"文档名：{document.file_name}\n"
            f"文档类型：{document_kind}\n"
            f"章节：{section_title}\n"
            f"片段类型提示：{content_type_hint}\n"
            f"是否以问句或问答形式开头：{question_shape}\n"
            f"难度：{difficulty}\n"
            f"最多生成题目数：{limit}\n\n"
            f"文档片段：\n{content}"
        )
        raw = QwenChatProvider().generate_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = self._parse_model_output(raw)

        drafts: list[GeneratedQuestionDraft] = []
        for item in parsed[:limit]:
            question = str(item.get("question", "")).strip()
            reference_answer = str(item.get("reference_answer", "")).strip()
            tags = [str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()]
            if not question or not reference_answer:
                continue
            drafts.append(
                GeneratedQuestionDraft(
                    question=question,
                    reference_answer=reference_answer,
                    tags=self._normalize_tags(tags, document, chunk),
                    difficulty=difficulty,
                )
            )
        return drafts

    def _generate_with_local_rules(
        self,
        *,
        document: Document,
        chunk: dict,
        difficulty: str,
        limit: int,
    ) -> list[GeneratedQuestionDraft]:
        normalized = self._normalize_text(chunk.get("content") or "")
        if not normalized:
            return []

        summary = self._extract_summary_line(normalized)
        top_points = self._extract_bullet_points(normalized, limit=3)
        section_title = str(chunk.get("section_title") or "").strip()
        topic = section_title or summary or document.file_name
        content_type_hint = str(chunk.get("content_type_hint") or "general").strip().lower()
        templates = self._build_local_templates(topic=topic, top_points=top_points, content_type_hint=content_type_hint)

        drafts: list[GeneratedQuestionDraft] = []
        for category, question, answer_lines in templates[:limit]:
            drafts.append(
                GeneratedQuestionDraft(
                    question=question,
                    reference_answer="参考答案：\n" + "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(answer_lines)),
                    tags=self._normalize_tags([category], document, chunk),
                    difficulty=difficulty,
                )
            )
        return drafts

    def _build_local_templates(
        self,
        *,
        topic: str,
        top_points: list[str],
        content_type_hint: str,
    ) -> list[tuple[str, str, list[str]]]:
        concept_lines = [
            f"先给出“{topic}”的定义。",
            "再说明它解决什么问题，以及适用在什么场景。",
            *[f"补充要点：{point}" for point in top_points[:2]],
        ]
        scenario_lines = [
            f"结合资料说明“{topic}”的典型使用场景。",
            "再说明落地时需要关注的输入、输出、约束和风险。",
            *[f"资料依据：{point}" for point in top_points[:2]],
        ]
        followup_lines = [
            "指出这个知识点最容易被继续追问的细节。",
            "补充常见误区、边界条件或实现风险。",
            *[f"可展开方向：{point}" for point in top_points[:2]],
        ]
        design_lines = [
            "建议按背景、核心方案、关键权衡、风险控制的结构作答。",
            f"核心方案部分需要紧扣“{topic}”的关键机制。",
            *[f"设计依据：{point}" for point in top_points[:2]],
        ]

        templates = [
            ("concept", f"请解释“{topic}”的核心概念，并说明它为什么重要。", concept_lines),
            ("scenario", f"如果在实际项目中需要使用“{topic}”，你会如何说明它的适用场景与落地方式？", scenario_lines),
            ("followup", f"围绕“{topic}”，面试官最可能继续追问哪些风险点或易错点？", followup_lines),
            ("design", f"如果让你基于“{topic}”设计一个方案，你会如何组织答案结构？", design_lines),
        ]

        if content_type_hint == "design_discussion":
            return [templates[3], templates[1], templates[2], templates[0]]
        if content_type_hint == "implementation_detail":
            return [templates[1], templates[2], templates[0], templates[3]]
        if content_type_hint == "question_answer":
            return [templates[0], templates[2], templates[1], templates[3]]
        return templates

    def _parse_model_output(self, raw: str) -> list[dict]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Question generation model did not return a JSON array")
        return [item for item in data if isinstance(item, dict)]

    def _normalize_tags(self, tags: list[str], document: Document, chunk: dict) -> list[str]:
        normalized: list[str] = []
        for tag in tags:
            compact = tag.strip().lower()
            if compact and compact not in normalized:
                normalized.append(compact)

        if document.file_type.lower() not in normalized:
            normalized.append(document.file_type.lower())
        if document.document_kind and document.document_kind.lower() not in normalized:
            normalized.append(document.document_kind.lower())

        content_type_hint = str(chunk.get("content_type_hint") or "").strip().lower()
        if content_type_hint and content_type_hint not in normalized:
            normalized.append(content_type_hint)

        if chunk.get("section_title"):
            section = str(chunk["section_title"]).strip()
            if section and section not in normalized:
                normalized.append(section)

        if not any(tag in QUESTION_TYPE_TAGS for tag in normalized):
            normalized.insert(0, "concept")
        return normalized

    def _extract_summary_line(self, text: str) -> str:
        sentences = re.split(r"[。！？!?;\n]", text)
        for sentence in sentences:
            normalized = sentence.strip(" -:\t")
            if len(normalized) >= 12:
                return normalized[:120]
        return text[:120]

    def _extract_bullet_points(self, text: str, limit: int) -> list[str]:
        lines = [line.strip(" -:\t") for line in text.splitlines()]
        valid_lines = [line for line in lines if len(line) >= 12]
        deduped: list[str] = []
        for line in valid_lines:
            if line not in deduped:
                deduped.append(line[:120])
            if len(deduped) >= limit:
                break
        return deduped

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
