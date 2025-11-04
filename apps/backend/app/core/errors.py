from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class DomainError(Exception):
    def __init__(self, message: str, *, extra: dict | None = None) -> None:
        super().__init__(message)
        self.extra = extra or {}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError):  # type: ignore
        return JSONResponse(status_code=400, content={"error": "domain", "message": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):  # type: ignore
        logger.exception("unhandled-error", extra={"event": "exception"})
        return JSONResponse(status_code=500, content={"error": "internal", "message": "Something went wrong"})
