from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def verify_legacy_pbkdf2_password(password: str, salt: str, password_hash: str) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 140000).hex()
    return hmac.compare_digest(digest, password_hash)


def create_access_token(subject: int, role: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: Dict[str, Any] = {"sub": str(subject), "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token invalido.") from exc
