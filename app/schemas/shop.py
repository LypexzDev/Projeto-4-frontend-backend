from __future__ import annotations

from pydantic import BaseModel, Field


class CheckoutPayload(BaseModel):
    produtos_ids: list[int] = Field(min_length=1)


class RecargaPayload(BaseModel):
    valor: float = Field(gt=0)

