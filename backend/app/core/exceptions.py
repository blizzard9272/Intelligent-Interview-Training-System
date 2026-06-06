from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.exceptions")


def _request_id_from(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _message_from_detail(detail: Any, fallback: str) -> str:
    if isinstance(detail, str) and detail.strip():
      return detail
    if isinstance(detail, list) and detail:
      return "请求参数校验失败"
    if isinstance(detail, dict):
      message = detail.get("message")
      if isinstance(message, str) and message.strip():
        return message
    return fallback


def _error_response(
    *,
    request: Request,
    status_code: int,
    detail: str,
    error_type: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "detail": detail,
        "request_id": _request_id_from(request),
        "error_type": error_type,
    }
    if extra:
        payload.update(extra)
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = _message_from_detail(exc.detail, "请求处理失败")
        logger.warning(
            "http_exception method=%s path=%s status_code=%s detail=%s request_id=%s",
            request.method,
            request.url.path,
            exc.status_code,
            detail,
            _request_id_from(request),
        )
        return _error_response(
            request=request,
            status_code=exc.status_code,
            detail=detail,
            error_type="http_error",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(
            "validation_exception method=%s path=%s errors=%s request_id=%s",
            request.method,
            request.url.path,
            exc.errors(),
            _request_id_from(request),
        )
        return _error_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请求参数校验失败",
            error_type="validation_error",
            extra={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception method=%s path=%s request_id=%s",
            request.method,
            request.url.path,
            _request_id_from(request),
            exc_info=exc,
        )
        return _error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误，请稍后重试",
            error_type="internal_error",
        )
