from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


class ChatModelConfig(BaseModel):
    provider: str = "local"
    model_name: str = "local-grounded-answer"
    temperature: float = 0.2
    max_tokens: int = 1200


class EmbeddingModelConfig(BaseModel):
    provider: str = "local"
    model_name: str = "hash-embedding-dev"
    dimensions: int = 256


class ProviderConfig(BaseModel):
    enabled: bool = False
    api_base: str | None = None


class ModelConfig(BaseModel):
    chat: ChatModelConfig = Field(default_factory=ChatModelConfig)
    embedding: EmbeddingModelConfig = Field(default_factory=EmbeddingModelConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


class RetrievalConfig(BaseModel):
    top_k: int = 4
    enable_rerank: bool = False
    enable_hybrid_retrieval: bool = False
    min_reference_count: int = 1


class ChunkingConfig(BaseModel):
    chunk_size: int = 700
    chunk_overlap: int = 100
    markdown_respect_headers: bool = True
    pdf_split_by_page: bool = True


class AnsweringConfig(BaseModel):
    include_references: bool = True
    fallback_when_empty: bool = True
    max_reference_snippet_length: int = 300


class RAGConfig(BaseModel):
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    answering: AnsweringConfig = Field(default_factory=AnsweringConfig)


class UploadConfig(BaseModel):
    max_file_size_mb: int = 20


class PipelineConfig(BaseModel):
    clean_text: bool = True
    chunk_before_embedding: bool = True
    async_mode: str = "background_tasks"


class StatusMessagesConfig(BaseModel):
    queued: str = "Queued for ingestion"
    running: str = "Running ingestion"
    completed: str = "Vector ingestion completed"
    failed: str = "Ingestion failed"


class IngestionConfig(BaseModel):
    supported_types: list[str] = Field(default_factory=lambda: ["txt", "md", "pdf"])
    upload: UploadConfig = Field(default_factory=UploadConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    status_messages: StatusMessagesConfig = Field(default_factory=StatusMessagesConfig)


class PromptSection(BaseModel):
    system_prompt: str


class PromptConfig(BaseModel):
    qa: PromptSection
    question_generation: PromptSection
    interview_summary: PromptSection


class InterviewAgentConfig(BaseModel):
    enabled: bool = False
    mode: str = "text"
    max_followup_rounds: int = 2
    summary_enabled: bool = True
    score_dimensions: list[str] = Field(default_factory=list)


class QuestionGenerationConfig(BaseModel):
    enabled: bool = False
    default_difficulty: str = "medium"
    max_questions_per_document: int = 10


class AgentConfig(BaseModel):
    interview_agent: InterviewAgentConfig = Field(default_factory=InterviewAgentConfig)
    question_generation: QuestionGenerationConfig = Field(default_factory=QuestionGenerationConfig)


class ChromaStorageConfig(BaseModel):
    collection_name: str = "document_chunks"


class ChromaRetrievalConfig(BaseModel):
    default_top_k: int = 4
    max_top_k: int = 8
    metadata_filters: dict[str, bool] = Field(default_factory=dict)


class ChromaConfig(BaseModel):
    storage: ChromaStorageConfig = Field(default_factory=ChromaStorageConfig)
    retrieval: ChromaRetrievalConfig = Field(default_factory=ChromaRetrievalConfig)


def _load_yaml(file_name: str) -> dict:
    config_path = CONFIG_DIR / file_name
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Config file {config_path} must contain a mapping at the root level")
    return data


@lru_cache(maxsize=1)
def get_model_config() -> ModelConfig:
    return ModelConfig.model_validate(_load_yaml("model.yaml"))


@lru_cache(maxsize=1)
def get_rag_config() -> RAGConfig:
    return RAGConfig.model_validate(_load_yaml("rag.yaml"))


@lru_cache(maxsize=1)
def get_ingestion_config() -> IngestionConfig:
    return IngestionConfig.model_validate(_load_yaml("ingestion.yaml"))


@lru_cache(maxsize=1)
def get_prompt_config() -> PromptConfig:
    return PromptConfig.model_validate(_load_yaml("prompt.yaml"))


@lru_cache(maxsize=1)
def get_agent_config() -> AgentConfig:
    return AgentConfig.model_validate(_load_yaml("agent.yaml"))


@lru_cache(maxsize=1)
def get_chroma_config() -> ChromaConfig:
    return ChromaConfig.model_validate(_load_yaml("chroma.yaml"))


def clear_config_caches() -> None:
    get_model_config.cache_clear()
    get_rag_config.cache_clear()
    get_ingestion_config.cache_clear()
    get_prompt_config.cache_clear()
    get_agent_config.cache_clear()
    get_chroma_config.cache_clear()
