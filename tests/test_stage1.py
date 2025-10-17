from __future__ import annotations

import os
import shutil
from pathlib import Path

# Configure environment for tests before importing the app
os.environ["DATABASE_URL"] = "sqlite:///./test_stage1.sqlite3"
os.environ["DATA_DIRECTORY"] = "test_data"
os.environ["PIPER_ENABLE_FALLBACK"] = "true"
os.environ["RATE_LIMIT_REQUESTS"] = "2"
os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "1"

from fastapi.testclient import TestClient

from app.main import app
from app.models import Base
from app.database import engine


def setup_module(module: object) -> None:  # noqa: D401 - pytest hook
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    data_dir = Path("test_data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)


def teardown_module(module: object) -> None:
    db_path = Path("test_stage1.sqlite3")
    if db_path.exists():
        db_path.unlink()
    shutil.rmtree("test_data", ignore_errors=True)
    engine.dispose()


client = TestClient(app)


def wait_for_completion(job_id: str) -> dict:
    for _ in range(20):
        response = client.get(f"/v1/jobs/{job_id}")
        if response.status_code == 429:
            continue
        response.raise_for_status()
        payload = response.json()
        if payload["status"] in {"completed", "failed", "blocked"}:
            return payload
    raise AssertionError("Job did not finish")


def test_generate_to_export_flow() -> None:
    payload = {
        "project_name": "Testowa bajka",
        "description": "Opis",
        "scenes": [
            {"id": "scena-a", "order": 1, "text": "Żył smok o imieniu Ćwirek."},
            {"id": "scena-b", "order": 2, "text": "Smok polubił tańczyć na łące."},
        ],
    }
    response = client.post("/v1/generate", json=payload)
    response.raise_for_status()
    data = response.json()

    job = wait_for_completion(data["job_id"])
    assert job["status"] == "completed"

    export_payload = {
        "render_id": data["render_id"],
        "title": "Testowa bajka",
        "author": "PyTest",
        "album": "Suite",
    }
    export_response = client.post("/v1/export/mp3", json=export_payload)
    export_response.raise_for_status()
    export_data = export_response.json()

    export_job = wait_for_completion(export_data["job_id"])
    assert export_job["status"] == "completed"

    download = client.get(f"/v1/exports/{export_data['export_id']}")
    download.raise_for_status()
    assert download.headers["content-type"] == "application/zip"
    from zipfile import ZipFile
    from io import BytesIO

    with ZipFile(BytesIO(download.content)) as archive:
        assert any(name.endswith(".mp3") for name in archive.namelist())


def test_rate_limit_returns_429() -> None:
    for _ in range(2):
        client.get("/v1/jobs/non-existent")
    third = client.get("/v1/jobs/non-existent")
    assert third.status_code == 429
