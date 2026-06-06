from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Infrastructure and environment-level settings for the backend."""

    app_name: str = "Interview Agent API"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 10080
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/interview_agent"
    redis_url: str = "redis://localhost:6379/0"
    chroma_persist_directory: str = "./storage/chroma"
    upload_dir: str = "./storage/uploads"
    db_auto_create: bool = False
    chunk_size: int = 700
    chunk_overlap: int = 100
    vector_collection_name: str = "document_chunks"
    dashscope_api_key: str | None = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_chat_provider: str = "qwen"
    default_chat_model: str = "qwen3.6-plus-2026-04-02"
    default_embedding_provider: str = "qwen"
    default_embedding_model: str = "text-embedding-v4"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "0", "false", "no", "off"}:
                return False
            if normalized in {"development", "dev", "1", "true", "yes", "on"}:
                return True
        return value

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def resolve_backend_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return (self.backend_dir / path).resolve()

    @property
    def upload_path(self) -> Path:
        return self.resolve_backend_path(self.upload_dir)

    @property
    def chroma_persist_path(self) -> Path:
        return self.resolve_backend_path(self.chroma_persist_directory)


settings = Settings()
