from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import admin_service

router = APIRouter(tags=["site"])


@router.get("/site-config")
def get_site_config(db: Session = Depends(get_db)):
    return admin_service.get_site_config(db)

