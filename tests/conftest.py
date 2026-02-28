from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("db")
    db_file = db_dir / "test_loja.db"

    os.environ["LOJACONTROL_DATABASE_URL"] = f"sqlite:///{db_file.as_posix()}"
    os.environ["LOJACONTROL_JWT_SECRET"] = "test-secret-key"
    os.environ["LOJACONTROL_SKIP_LEGACY_IMPORT"] = "1"
    os.environ["LOJA_ADMIN_EMAIL"] = "admin@lojacontrol.local"
    os.environ["LOJA_ADMIN_PASSWORD"] = "admin123"

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

