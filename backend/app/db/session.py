"""
数据库会话模块，定义了SQLAlchemy的数据库引擎和会话工厂，以及一个生成器函数get_db，用于在FastAPI的依赖项中提供数据库会话对象。
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
