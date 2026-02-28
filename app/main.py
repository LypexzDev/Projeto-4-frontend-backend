from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, auth, frontend, shop, site
from app.db.bootstrap import initialize_database


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database()
        yield

    api = FastAPI(title="LojaControl API", lifespan=lifespan)

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api.include_router(site.router)
    api.include_router(auth.router)
    api.include_router(shop.router)
    api.include_router(admin.router)
    api.include_router(frontend.router)
    return api


app = create_app()
