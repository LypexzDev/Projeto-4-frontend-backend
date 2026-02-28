from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_legacy_pbkdf2_password,
    verify_password,
)
from app.db.models import Account, User
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

    token = create_access_token(account.id, account.role)
    return {"token": token, "account": account_public_payload(account)}


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
