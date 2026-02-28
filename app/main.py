from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, auth, frontend, shop, site
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import AuthContextMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
from app.db.bootstrap import initialize_database

settings = get_settings()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        configure_logging(settings)
        initialize_database()
        yield

    api = FastAPI(
        title="LojaControl API",
        description="API fullstack com autenticacao JWT, painel admin e fluxo de compras.",
        version="2.0.0",
        lifespan=lifespan,
        contact={"name": "Felipe", "email": "felipecardoso1328@gmail.com"},
        openapi_tags=[
            {"name": "auth", "description": "Cadastro, login e refresh de tokens"},
            {"name": "shop", "description": "Fluxos do usuario cliente"},
            {"name": "admin", "description": "Gestao administrativa"},
            {"name": "site", "description": "Configuracoes publicas da loja"},
            {"name": "frontend", "description": "Arquivos estaticos da interface"},
        ],
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.add_middleware(AuthContextMiddleware)
    api.add_middleware(RequestLoggingMiddleware)
    if settings.rate_limit_enabled:
        api.add_middleware(
            RateLimitMiddleware,
            requests_limit=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

    register_exception_handlers(api)

    api.include_router(site.router)
    api.include_router(auth.router)
    api.include_router(shop.router)
    api.include_router(admin.router)
    api.include_router(frontend.router)
    return api


app = create_app()
