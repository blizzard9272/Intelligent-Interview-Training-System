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
            return QwenChatProvider().answer_question(question, references)
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
    return build_grounded_answer(question, references)
