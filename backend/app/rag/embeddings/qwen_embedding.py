from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.utils import get_model_config

logger = logging.getLogger("app.rag.qwen_embedding")


class QwenEmbeddingProvider:
    def __init__(self) -> None:
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        model_config = get_model_config()
        self.api_key = settings.dashscope_api_key
        self.base_url = (model_config.providers.get("qwen").api_base or settings.dashscope_base_url).rstrip("/")
        self.model_name = model_config.embedding.model_name
        self.dimensions = model_config.embedding.dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        logger.info("qwen_embedding_documents_started model=%s batch_size=%s", self.model_name, len(texts))
        if self._is_multimodal_model():
            embeddings: list[list[float]] = []
            for start in range(0, len(texts), 10):
                batch = texts[start : start + 10]
                response = self._request_multimodal_embeddings(batch)
                data = response.get("output", {}).get("embeddings", [])
                embeddings.extend(item["embedding"] for item in data)
            logger.info("qwen_embedding_documents_completed model=%s vectors=%s", self.model_name, len(embeddings))
            return embeddings

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), 10):
            batch = texts[start : start + 10]
            response = self._request_text_embeddings(batch)
            data = response.get("data", [])
            embeddings.extend(item["embedding"] for item in data)
        logger.info("qwen_embedding_documents_completed model=%s vectors=%s", self.model_name, len(embeddings))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        logger.info("qwen_embedding_query_started model=%s text_length=%s", self.model_name, len(text))
        if self._is_multimodal_model():
            response = self._request_multimodal_embeddings([text])
            data = response.get("output", {}).get("embeddings", [])
            if not data:
                raise ValueError("Multimodal embedding response is empty")
            logger.info("qwen_embedding_query_completed model=%s dimensions=%s", self.model_name, len(data[0]["embedding"]))
            return data[0]["embedding"]

        response = self._request_text_embeddings([text])
        data = response.get("data", [])
        if not data:
            raise ValueError("Embedding response is empty")
        logger.info("qwen_embedding_query_completed model=%s dimensions=%s", self.model_name, len(data[0]["embedding"]))
        return data[0]["embedding"]

    def _request_text_embeddings(self, inputs: list[str]) -> dict[str, Any]:
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model_name,
            "input": inputs,
            "dimensions": self.dimensions,
            "encoding_format": "float",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _request_multimodal_embeddings(self, inputs: list[str]) -> dict[str, Any]:
        url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        payload = {
            "model": self.model_name,
            "input": {
                "contents": [{"text": item} for item in inputs],
            },
            "parameters": {
                "dimension": self.dimensions,
                "output_type": "dense",
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _is_multimodal_model(self) -> bool:
        return (
            "embedding-vision" in self.model_name
            or "vl-embedding" in self.model_name
            or "multimodal-embedding" in self.model_name
        )
