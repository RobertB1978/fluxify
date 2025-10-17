from __future__ import annotations

import os
import time
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

# Ensure fallback is enabled for local smoke run
os.environ.setdefault("PIPER_ENABLE_FALLBACK", "true")

from fastapi.testclient import TestClient  # noqa: E402
from mutagen.easyid3 import EasyID3  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


def wait_for_job(client: TestClient, job_id: str, timeout_seconds: float = 15.0) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/v1/jobs/{job_id}")
        response.raise_for_status()
        payload = response.json()
        if payload["status"] in {"completed", "failed", "blocked"}:
            return payload
        time.sleep(0.5)
    raise TimeoutError(f"Job {job_id} did not complete in time")


def main() -> None:
    client = TestClient(app)

    generate_payload = {
        "project_name": "Bajka testowa",
        "description": "Generacja testowa",
        "scenes": [
            {"id": "scene-1", "order": 1, "text": "Dawno dawno temu żył mały smok."},
            {"id": "scene-2", "order": 2, "text": "Smok uwielbiał latać nad zielonym lasem."},
        ],
    }

    generate_response = client.post("/v1/generate", json=generate_payload)
    generate_response.raise_for_status()
    generate_data = generate_response.json()

    render_job = wait_for_job(client, generate_data["job_id"])
    if render_job["status"] != "completed":
        raise SystemExit(f"Render job failed: {render_job}")

    export_payload = {
        "render_id": generate_data["render_id"],
        "title": "Bajka testowa",
        "author": "Test",
        "album": "Smoke",
    }
    export_response = client.post("/v1/export/mp3", json=export_payload)
    export_response.raise_for_status()
    export_data = export_response.json()

    export_job = wait_for_job(client, export_data["job_id"])
    if export_job["status"] != "completed":
        raise SystemExit(f"Export job failed: {export_job}")

    download_response = client.get(f"/v1/exports/{export_data['export_id']}")
    download_response.raise_for_status()

    with ZipFile(BytesIO(download_response.content)) as archive:
        mp3_files = [name for name in archive.namelist() if name.endswith(".mp3")]
        if not mp3_files:
            raise SystemExit("MP3 not found in export archive")
        mp3_name = mp3_files[0]
        with archive.open(mp3_name) as mp3_data:
            temp_path = Path(settings.data_directory) / "smoke_test.mp3"
            temp_path.write_bytes(mp3_data.read())
            tags = EasyID3(temp_path)
            assert tags.get("title", [None])[0] == "Bajka testowa"
            temp_path.unlink(missing_ok=True)

    print("Smoke test completed successfully")


if __name__ == "__main__":
    main()
