from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)
    endpoints = ["/v1/health/audio", "/v1/health/tts"]
    for endpoint in endpoints:
        response = client.get(endpoint)
        print(f"{endpoint} -> {response.status_code} {response.text}")
        response.raise_for_status()


if __name__ == "__main__":
    main()
