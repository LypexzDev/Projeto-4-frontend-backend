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
    refresh_cookie_name: str


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
        cors_origins = [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]

    settings = Settings(
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
        refresh_cookie_name=os.getenv("LOJACONTROL_REFRESH_COOKIE_NAME", "lc_refresh_token"),
    )
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if settings.environment != "production":
        return

    if settings.jwt_secret_key in {"change-this-secret", "change-this-secret-in-production"}:
        raise RuntimeError("JWT secret inseguro para produção.")
    if len(settings.jwt_secret_key) < 32:
        raise RuntimeError("JWT secret muito curto para produção (mínimo 32 caracteres).")
    if settings.admin_password == "admin123":
        raise RuntimeError("Senha admin padrão não pode ser usada em produção.")
    if not settings.cors_origins or "*" in settings.cors_origins:
        raise RuntimeError("CORS em produção precisa de origens explícitas (sem '*').")
    if settings.auto_create_schema:
        raise RuntimeError("LOJACONTROL_AUTO_CREATE_SCHEMA deve ser 0 em produção.")
