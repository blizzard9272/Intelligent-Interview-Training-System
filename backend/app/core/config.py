from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Interview Agent API"
    app_env: str = "development"
    debug: bool = True
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
    default_chat_provider: str = "qwen"
    default_chat_model: str = "qwen-plus"
    default_embedding_provider: str = "qwen"
    default_embedding_model: str = "text-embedding-v4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
