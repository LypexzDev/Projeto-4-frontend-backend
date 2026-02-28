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
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    admin_email: str
    admin_password: str
    skip_legacy_import: bool


def _read_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    database_url = os.getenv("LOJACONTROL_DATABASE_URL")
    if not database_url:
        database_url = f"sqlite:///{(PROJECT_ROOT / 'loja.db').as_posix()}"

    return Settings(
        project_root=PROJECT_ROOT,
        database_url=database_url,
        jwt_secret_key=os.getenv("LOJACONTROL_JWT_SECRET", "change-this-secret"),
        jwt_algorithm=os.getenv("LOJACONTROL_JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("LOJACONTROL_ACCESS_TOKEN_EXPIRE_MINUTES", "720")),
        admin_email=os.getenv("LOJA_ADMIN_EMAIL", "admin@lojacontrol.local").strip().lower(),
        admin_password=os.getenv("LOJA_ADMIN_PASSWORD", "admin123"),
        skip_legacy_import=_read_bool(os.getenv("LOJACONTROL_SKIP_LEGACY_IMPORT"), False),
    )

