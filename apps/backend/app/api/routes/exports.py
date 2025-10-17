from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...config import settings
from ...models.entities import Asset, AssetType, JobType, Render
from ...schemas.export import ExportRequest, ExportResponse
from ...services.jobs import create_job, schedule_export_job
from ...utils.identifiers import new_id
from ..deps.db import get_db, get_rate_limiter_dependency

router = APIRouter(prefix="/v1", tags=["exports"])


@router.post("/export/mp3", response_model=ExportResponse)
def export_render(
    payload: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _rate=Depends(get_rate_limiter_dependency()),
) -> ExportResponse:
    render = db.get(Render, payload.render_id)
    if not render:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render not found")

    request_id = payload.request_id or new_id()
    export_id = new_id()
    export_path = (
        settings.data_directory
        / settings.exports_subdir
        / f"{export_id}.zip"
    )

    asset = Asset(
        id=export_id,
        render_id=render.id,
        asset_type=AssetType.export_zip,
        path=str(export_path),
    )
    db.merge(asset)
    db.commit()

    job = create_job(
        db,
        job_type=JobType.export,
        request_id=request_id,
        render=render,
        message=f"title={payload.title}",
    )

    schedule_export_job(
        background_tasks,
        job.id,
        export_id,
        payload.title,
        payload.author,
        payload.album,
    )

    return ExportResponse(export_id=export_id, job_id=job.id, request_id=request_id)


@router.get("/exports/{export_id}")
def download_export(
    export_id: str,
    db: Session = Depends(get_db),
    _rate=Depends(get_rate_limiter_dependency()),
):
    asset = db.get(Asset, export_id)
    if not asset or asset.asset_type != AssetType.export_zip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")

    file_path = Path(asset.path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file missing")

    def iter_file() -> bytes:
        with file_path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(8192), b""):
                yield chunk

    headers = {
        "Content-Disposition": f"attachment; filename={file_path.name}",
    }
    return StreamingResponse(iter_file(), media_type="application/zip", headers=headers)
