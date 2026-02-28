from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from threading import Lock
from typing import DefaultDict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import decode_access_token

logger = logging.getLogger("app.middleware")


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        request.state.auth_payload = None

        authorization = request.headers.get("Authorization")
        if authorization:
            prefix, _, token = authorization.partition(" ")
            if prefix.lower() == "bearer" and token.strip():
                try:
                    request.state.auth_payload = decode_access_token(token.strip())
                except ValueError:
                    request.state.auth_payload = None

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = getattr(request.state, "request_id", "")
            return response
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            auth_payload = getattr(request.state, "auth_payload", None)
            user_id = auth_payload.get("sub") if isinstance(auth_payload, dict) else None
            logger.info(
                "http_request",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code if response else 500,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                },
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_limit: int, window_seconds: int):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.lock = Lock()
        self.hits: DefaultDict[str, list[float]] = defaultdict(list)

    @staticmethod
    def _client_key(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        now = time.time()
        key = self._client_key(request)

        with self.lock:
            timestamps = self.hits[key]
            threshold = now - self.window_seconds
            while timestamps and timestamps[0] < threshold:
                timestamps.pop(0)

            if len(timestamps) >= self.requests_limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Muitas requisicoes. Tente novamente em instantes."},
                    headers={
                        "Retry-After": str(self.window_seconds),
                        "X-Request-ID": getattr(request.state, "request_id", ""),
                    },
                )

            timestamps.append(now)
            remaining = max(0, self.requests_limit - len(timestamps))

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window-Seconds"] = str(self.window_seconds)
        return response
