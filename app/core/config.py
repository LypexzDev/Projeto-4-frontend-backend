from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DATA_FILE = PROJECT_ROOT / "loja_db.json"


@dataclass(frozen=True)
class Settings:
    project_root: Path
    environment: str
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    admin_email: str
    admin_password: str
    cors_origins: list[str]
    skip_legacy_import: bool
    log_level: str
    log_file: str
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window_seconds: int
    auto_create_schema: bool


def _read_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_csv_list(value: str | None, default: list[str] | None = None) -> list[str]:
    if value is None:
        return default or []
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("LOJACONTROL_ENV", "development").strip().lower()
    if environment not in {"development", "production", "test"}:
        environment = "development"

    database_url = os.getenv("LOJACONTROL_DATABASE_URL")
    if not database_url:
        database_url = f"sqlite:///{(PROJECT_ROOT / 'loja.db').as_posix()}"

    cors_origins = _read_csv_list(os.getenv("LOJACONTROL_CORS_ORIGINS"))
    if not cors_origins:
        cors_origins = ["*"] if environment != "production" else []

    return Settings(
        project_root=PROJECT_ROOT,
        environment=environment,
        database_url=database_url,
        jwt_secret_key=os.getenv("LOJACONTROL_JWT_SECRET", "change-this-secret"),
        jwt_algorithm=os.getenv("LOJACONTROL_JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("LOJACONTROL_ACCESS_TOKEN_EXPIRE_MINUTES", "720")),
        refresh_token_expire_days=int(os.getenv("LOJACONTROL_REFRESH_TOKEN_EXPIRE_DAYS", "14")),
        admin_email=os.getenv("LOJA_ADMIN_EMAIL", "admin@lojacontrol.local").strip().lower(),
        admin_password=os.getenv("LOJA_ADMIN_PASSWORD", "admin123"),
        cors_origins=cors_origins,
        skip_legacy_import=_read_bool(os.getenv("LOJACONTROL_SKIP_LEGACY_IMPORT"), False),
        log_level=os.getenv("LOJACONTROL_LOG_LEVEL", "INFO").upper(),
        log_file=os.getenv("LOJACONTROL_LOG_FILE", str(PROJECT_ROOT / "logs" / "app.log")),
        rate_limit_enabled=_read_bool(os.getenv("LOJACONTROL_RATE_LIMIT_ENABLED"), True),
        rate_limit_requests=int(os.getenv("LOJACONTROL_RATE_LIMIT_REQUESTS", "120")),
        rate_limit_window_seconds=int(os.getenv("LOJACONTROL_RATE_LIMIT_WINDOW_SECONDS", "60")),
        auto_create_schema=_read_bool(os.getenv("LOJACONTROL_AUTO_CREATE_SCHEMA"), True),
    )
