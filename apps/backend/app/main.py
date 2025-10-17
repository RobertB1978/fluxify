from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import exports, generate, health, jobs, tts
from .config import settings
from .logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin for origin in settings.allowed_origins] or ["*"],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    app.include_router(generate.router)
    app.include_router(tts.router)
    app.include_router(jobs.router)
    app.include_router(exports.router)
    app.include_router(health.router)

    return app


app = create_app()
