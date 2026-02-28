from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    saldo: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    account: Mapped["Account"] = relationship(back_populates="user", uselist=False)
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_salt: Mapped[str | None] = mapped_column(String(64), nullable=True)
    password_algo: Mapped[str] = mapped_column(String(20), nullable=False, default="bcrypt")

    user: Mapped[User | None] = relationship(back_populates="account")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    preco: Mapped[float] = mapped_column(Float, nullable=False)

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")


class SiteConfig(Base):
    __tablename__ = "site_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    site_name: Mapped[str] = mapped_column(String(60), nullable=False)
    tagline: Mapped[str] = mapped_column(String(120), nullable=False)
    hero_title: Mapped[str] = mapped_column(String(80), nullable=False)
    hero_subtitle: Mapped[str] = mapped_column(String(180), nullable=False)
    accent_color: Mapped[str] = mapped_column(String(7), nullable=False)
    highlight_color: Mapped[str] = mapped_column(String(7), nullable=False)
