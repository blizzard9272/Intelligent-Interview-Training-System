from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.responses import Response

from app.core.logging import reset_request_id, set_request_id

logger = logging.getLogger("app.middleware.request")


async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    token = set_request_id(request_id)
    request.state.request_id = request_id

    start_time = time.perf_counter()
    client_host = request.client.host if request.client else "-"

    logger.info("request_started method=%s path=%s client=%s", request.method, request.url.path, client_host)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(
            "request_failed method=%s path=%s duration_ms=%s",
            request.method,
            request.url.path,
            duration_ms,
        )
        reset_request_id(token)
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed method=%s path=%s status_code=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    reset_request_id(token)
    return response
