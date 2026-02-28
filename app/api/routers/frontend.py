from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.config import get_settings

router = APIRouter(tags=["frontend"])
PROJECT_ROOT = get_settings().project_root


def _file_response(path: Path, media_type: str | None = None):
    if media_type:
        return FileResponse(path, media_type=media_type)
    return FileResponse(path)


@router.get("/")
def frontend_index():
    return _file_response(PROJECT_ROOT / "index.html")


@router.get("/script.js")
def frontend_script():
    return _file_response(PROJECT_ROOT / "script.js", media_type="application/javascript")


@router.get("/apiClient.js")
def frontend_api_client():
    return _file_response(PROJECT_ROOT / "apiClient.js", media_type="application/javascript")


@router.get("/style.css")
def frontend_style():
    return _file_response(PROJECT_ROOT / "style.css", media_type="text/css")


@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    return {"ok": True}

