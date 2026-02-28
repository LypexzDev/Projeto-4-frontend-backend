from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import (
    create_token_pair,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    now_utc,
    verify_legacy_pbkdf2_password,
    verify_password,
)
from app.db.models import Account, RefreshToken, User
from app.schemas.auth import LoginPayload, RegisterUserPayload


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _round_money(value: float) -> float:
    return round(float(value), 2)


def account_public_payload(account: Account) -> dict:
    payload = {
        "id": account.id,
        "nome": account.nome,
        "email": account.email,
        "role": account.role,
    }
    if account.role == "user" and account.user:
        payload["usuario_id"] = account.user.id
        payload["saldo"] = _round_money(account.user.saldo)
    return payload


def _verify_account_password(db: Session, account: Account, password: str) -> bool:
    if account.password_algo == "pbkdf2":
        if not account.password_salt:
            return False
        valid = verify_legacy_pbkdf2_password(password, account.password_salt, account.password_hash)
        if valid:
            account.password_hash = hash_password(password)
            account.password_algo = "bcrypt"
            account.password_salt = None
            db.add(account)
            db.commit()
            db.refresh(account)
        return valid

    return verify_password(password, account.password_hash)


def _to_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _store_refresh_token(db: Session, account_id: int, jti: str, expires_at: datetime) -> None:
    db.add(
        RefreshToken(
            account_id=account_id,
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
    )


def _cleanup_expired_refresh_tokens(db: Session) -> None:
    now = now_utc()
    db.query(RefreshToken).filter(RefreshToken.expires_at < now).delete(synchronize_session=False)


def _issue_token_bundle(db: Session, account: Account) -> dict:
    pair = create_token_pair(account.id, account.role)
    _store_refresh_token(db, account.id, pair["refresh_jti"], pair["refresh_expires_at"])
    db.flush()
    return {
        "token": pair["access_token"],  # backward compatibility
        "access_token": pair["access_token"],
        "refresh_token": pair["refresh_token"],
        "token_type": "bearer",
    }


def register_user(db: Session, payload: RegisterUserPayload) -> dict:
    email = normalize_email(payload.email)
    existing_account = db.scalar(select(Account).where(Account.email == email))
    if existing_account:
        raise HTTPException(status_code=409, detail="Ja existe uma conta com este e-mail.")

    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            nome=payload.nome.strip(),
            email=email,
            saldo=_round_money(payload.saldo_inicial),
        )
        db.add(user)
        db.flush()
    else:
        user.nome = payload.nome.strip()
        user.saldo = _round_money(payload.saldo_inicial)

    account = Account(
        nome=payload.nome.strip(),
        email=email,
        role="user",
        usuario_id=user.id,
        password_hash=hash_password(payload.password),
        password_salt=None,
        password_algo="bcrypt",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"message": "Conta criada com sucesso.", "account": account_public_payload(account)}


def login_by_role(db: Session, payload: LoginPayload, role: str) -> dict:
    email = normalize_email(payload.email)
    account = db.scalar(select(Account).where(Account.email == email))
    if not account or account.role != role:
        raise HTTPException(status_code=401, detail="Credenciais invalidas.")

    if not _verify_account_password(db, account, payload.password):
        raise HTTPException(status_code=401, detail="Credenciais invalidas.")

    _cleanup_expired_refresh_tokens(db)
    bundle = _issue_token_bundle(db, account)
    db.commit()
    return {**bundle, "account": account_public_payload(account)}


def refresh_session(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_refresh_token(refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Refresh token invalido ou expirado.") from exc

    subject = payload.get("sub")
    jti = payload.get("jti")
    if not subject or not jti:
        raise HTTPException(status_code=401, detail="Refresh token invalido ou expirado.")

    try:
        account_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Refresh token invalido ou expirado.")

    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=401, detail="Conta nao encontrada.")

    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == str(jti)))
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token nao reconhecido.")
    if stored.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revogado.")
    if _to_aware_utc(stored.expires_at) < now_utc():
        raise HTTPException(status_code=401, detail="Refresh token expirado.")

    stored.revoked = True
    db.add(stored)

    bundle = _issue_token_bundle(db, account)
    db.commit()
    return {**bundle, "account": account_public_payload(account)}


def logout_account(db: Session, account: Account) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.account_id == account.id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    db.commit()


def get_account_from_token(db: Session, token: str) -> Account:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada.") from exc

    subject = payload.get("sub")
    try:
        account_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada.")

    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=401, detail="Conta nao encontrada.")
    return account
