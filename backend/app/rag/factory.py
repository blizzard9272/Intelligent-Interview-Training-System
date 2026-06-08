import logging

from app.core.config import settings
from app.rag.embeddings.hash_embedding import HashEmbeddingProvider
from app.rag.embeddings.qwen_embedding import QwenEmbeddingProvider
from app.rag.generators.local_generator import build_grounded_answer
from app.rag.generators.qwen_chat import ChatProviderError, QwenChatProvider
from app.schemas.qa import QAReference
from app.utils import get_model_config

logger = logging.getLogger("app.rag.factory")


def get_embedding_provider():
    model_config = get_model_config()
    qwen_provider = model_config.providers.get("qwen")
    if (
        model_config.embedding.provider == "qwen"
        and settings.dashscope_api_key
        and qwen_provider
        and qwen_provider.enabled
    ):
        logger.info("embedding_provider_selected provider=qwen model=%s", model_config.embedding.model_name)
        return QwenEmbeddingProvider()
    logger.info("embedding_provider_selected provider=local model=hash-embedding-dev")
    return HashEmbeddingProvider()


def generate_answer(question: str, references: list[QAReference]) -> str:
    model_config = get_model_config()
    qwen_provider = model_config.providers.get("qwen")
    should_prefix_general_knowledge = len(references) == 0
    if (
        model_config.chat.provider == "qwen"
        and settings.dashscope_api_key
        and qwen_provider
        and qwen_provider.enabled
    ):
        try:
            logger.info(
                "chat_provider_selected provider=qwen model=%s references=%s question_length=%s",
                model_config.chat.model_name,
                len(references),
                len(question),
            )
            answer = QwenChatProvider().answer_question(question, references)
            if should_prefix_general_knowledge:
                return _prefix_general_knowledge_answer(answer)
            return answer
        except (ValueError, ChatProviderError) as exc:
            logger.warning(
                "chat_provider_fallback provider=qwen fallback=local reason=%s references=%s",
                exc,
                len(references),
            )
            return build_grounded_answer(question, references)
    logger.info(
        "chat_provider_selected provider=local model=%s references=%s question_length=%s",
        model_config.chat.model_name,
        len(references),
        len(question),
    )
    answer = build_grounded_answer(question, references)
    if should_prefix_general_knowledge:
        return _prefix_general_knowledge_answer(answer)
    return answer


def _prefix_general_knowledge_answer(answer: str) -> str:
    normalized = answer.strip()
    if not normalized:
        return "据我所知，当前暂时无法生成可用回答。"
    if normalized.startswith("据我所知"):
        return normalized
    if normalized.startswith("⚠️") or normalized.startswith(">"):
        return f"据我所知，以下内容基于通用知识补充，仅供参考。\n\n{normalized}"
    return f"据我所知，以下内容基于通用知识补充，仅供参考。\n\n{normalized}"
