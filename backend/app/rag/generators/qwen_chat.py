from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.qa import QAReference
from app.utils import get_model_config, get_prompt_text


class ChatProviderError(RuntimeError):
    """Raised when an online chat provider cannot produce a usable response."""


logger = logging.getLogger("app.rag.qwen_chat")


class QwenChatProvider:
    def __init__(self) -> None:
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        model_config = get_model_config()
        qwen_provider = model_config.providers.get("qwen")
        if not qwen_provider or not qwen_provider.enabled:
            raise ValueError("Qwen chat provider is disabled in model.yaml")
        self.api_key = settings.dashscope_api_key
        self.base_url = (qwen_provider.api_base or settings.dashscope_base_url).rstrip("/")
        self.model_name = model_config.chat.model_name
        self.temperature = model_config.chat.temperature
        self.max_tokens = model_config.chat.max_tokens

    def answer_question(self, question: str, references: list[QAReference]) -> str:
        system_prompt = get_prompt_text("qa").strip()
        context_lines = []
        for index, reference in enumerate(references, start=1):
            context_lines.append(
                f"[{index}] file={reference.file_name}, chunk={reference.chunk_index}\n{reference.snippet}"
            )
        context_text = "\n\n".join(context_lines) if context_lines else "No retrieved context."

        messages = [
            {
                "role": "system",
                "content": (
                    f"{system_prompt}\n\n"
                    "When you use retrieved context, cite it with [1], [2], etc. "
                    "If the retrieved context is insufficient, say so clearly instead of inventing facts."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nRetrieved context:\n{context_text}",
            },
        ]
        logger.info(
            "qwen_chat_request_started model=%s references=%s temperature=%s",
            self.model_name,
            len(references),
            self.temperature,
        )
        response = self._request_chat(messages)
        try:
            answer = response["choices"][0]["message"]["content"].strip()
            logger.info("qwen_chat_request_completed model=%s answer_length=%s", self.model_name, len(answer))
            return answer
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise ChatProviderError("Qwen chat response is missing message content") from exc

    def _request_chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            logger.warning("qwen_chat_request_timeout model=%s", self.model_name)
            raise ChatProviderError("Qwen chat request timed out") from exc
        except httpx.HTTPStatusError as exc:
            response_text = exc.response.text.strip()
            detail = response_text[:300] if response_text else str(exc)
            logger.warning(
                "qwen_chat_request_http_error model=%s status_code=%s detail=%s",
                self.model_name,
                exc.response.status_code,
                detail,
            )
            raise ChatProviderError(f"Qwen chat request failed: {detail}") from exc
        except httpx.RequestError as exc:
            logger.warning("qwen_chat_request_network_error model=%s detail=%s", self.model_name, exc)
            raise ChatProviderError(f"Qwen chat request failed: {exc}") from exc
