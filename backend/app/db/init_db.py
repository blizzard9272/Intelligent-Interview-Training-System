from app.db.base import Base
from app.db.models import document, ingestion_task, knowledge_base, qa, question_bank, user  # noqa: F401
from app.db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
