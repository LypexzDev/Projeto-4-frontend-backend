from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterUserPayload(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=100)
    saldo_inicial: float = Field(default=0, ge=0)


class LoginPayload(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=100)

