from __future__ import annotations

import contextvars
import logging

from app.core.config import settings


request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get("-")
        return True


def set_request_id(request_id: str) -> contextvars.Token[str]:
    return request_id_ctx_var.set(request_id)


def reset_request_id(token: contextvars.Token[str]) -> None:
    request_id_ctx_var.reset(token)


def get_request_id() -> str:
    return request_id_ctx_var.get("-")


def setup_logging() -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_interview_agent_configured", False):
        return

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger._interview_agent_configured = True  # type: ignore[attr-defined]

