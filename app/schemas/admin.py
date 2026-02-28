from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProdutoCreatePayload(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    descricao: str = Field(default="", max_length=300)
    preco: float = Field(gt=0)


class ProdutoUpdatePayload(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=2, max_length=120)
    descricao: Optional[str] = Field(default=None, max_length=300)
    preco: Optional[float] = Field(default=None, gt=0)


class SiteConfigPayload(BaseModel):
    site_name: str = Field(min_length=2, max_length=60)
    tagline: str = Field(min_length=2, max_length=120)
    hero_title: str = Field(min_length=2, max_length=80)
    hero_subtitle: str = Field(min_length=2, max_length=180)
    accent_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")

