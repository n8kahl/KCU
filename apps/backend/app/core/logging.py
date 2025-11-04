from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

SENSITIVE_KEYS = {"api_key", "polygon_api_key", "authorization"}


def _redact_processor(logger: logging.Logger, method_name: str, event_dict: dict[str, Any]):
    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = "***"
    return event_dict


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            _redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
