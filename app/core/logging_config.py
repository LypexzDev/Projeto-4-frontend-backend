from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.config import Settings


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }

        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        path = getattr(record, "path", None)
        if path:
            payload["path"] = path

        method = getattr(record, "method", None)
        if method:
            payload["method"] = method

        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            payload["status_code"] = status_code

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms

        user_id = getattr(record, "user_id", None)
        if user_id is not None:
            payload["user_id"] = user_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    logger = logging.getLogger()
    logger.setLevel(settings.log_level)

    if logger.handlers:
        return

    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = JsonLogFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
