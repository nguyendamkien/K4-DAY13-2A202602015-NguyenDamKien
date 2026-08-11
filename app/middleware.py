from __future__ import annotations

import time
import uuid
import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        # Accept a caller supplied ID when it is safe to echo in a response
        # header. Otherwise generate the lab's canonical request ID format.
        incoming_id = request.headers.get("x-request-id", "").strip()
        if incoming_id and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", incoming_id):
            correlation_id = incoming_id
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = f"{elapsed_ms:.2f}"
            return response
        finally:
            # Context variables are task-local, but clearing them explicitly
            # prevents request metadata from leaking into later middleware
            # logs when a server reuses an execution context.
            clear_contextvars()
