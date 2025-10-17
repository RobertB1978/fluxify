from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from ...config import settings
from ...models.entities import Asset, AssetType, JobType
from ...schemas.tts import TTSRequest, TTSResponse
from ...services.jobs import create_job, schedule_tts_job
from ...utils.identifiers import new_id
from ..deps.db import get_db, get_rate_limiter_dependency

router = APIRouter(prefix="/v1", tags=["tts"])


@router.post("/audio/tts", response_model=TTSResponse)
def synthesize_speech(
    payload: TTSRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _rate=Depends(get_rate_limiter_dependency()),
) -> TTSResponse:
    request_id = payload.request_id or new_id()
    asset_id = new_id()
    normalized_path = (
        settings.data_directory
        / settings.assets_subdir
        / f"{asset_id}_normalized.wav"
    )

    asset = Asset(
        id=asset_id,
        asset_type=AssetType.scene_audio,
        path=str(normalized_path),
    )
    db.add(asset)
    db.commit()

    job = create_job(
        db,
        job_type=JobType.tts,
        request_id=request_id,
        message=f"voice={payload.voice}" if payload.voice else None,
    )

    schedule_tts_job(background_tasks, job.id, asset_id, payload.text, payload.voice)

    return TTSResponse(job_id=job.id, request_id=request_id, asset_id=asset_id)
