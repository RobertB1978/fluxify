from __future__ import annotations

import shutil
import subprocess

from fastapi import APIRouter, Depends, HTTPException, status

from ...tts.piper_provider import PiperTTSProvider
from ..deps.db import get_rate_limiter_dependency

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health/audio")
def audio_health(_rate=Depends(get_rate_limiter_dependency())) -> dict[str, str]:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ffmpeg not found")

    try:
        result = subprocess.run([ffmpeg_path, "-codecs"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ffmpeg execution failed"
        ) from exc

    if "libmp3lame" not in result.stdout:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="libmp3lame codec unavailable",
        )

    return {"status": "healthy"}


@router.get("/health/tts")
def tts_health(_rate=Depends(get_rate_limiter_dependency())) -> dict[str, str]:
    provider = PiperTTSProvider()
    health = provider.healthcheck()
    if health.get("status") != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health.get("reason", "TTS unavailable"),
        )
    return health
