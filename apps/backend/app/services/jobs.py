from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from ..audio.pipeline import add_id3_tags, concatenate_scenes, convert_to_mp3, normalize_wav
from ..config import settings
from ..database import SessionLocal
from ..logging import get_logger
from ..models.entities import (
    Asset,
    AssetType,
    Job,
    JobStatus,
    JobType,
    ProjectStatus,
    Render,
    RenderStatus,
    Scene,
)
from ..tts.piper_provider import PiperTTSProvider
from ..tts.provider import TTSModelUnavailableError, TTSProviderError
from ..utils.identifiers import new_id
from ..utils.time import utcnow

logger = get_logger(__name__)


@contextmanager
def new_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_job(
    session: Session,
    *,
    job_type: JobType,
    request_id: str,
    render: Render | None = None,
    scene: Scene | None = None,
    message: str | None = None,
) -> Job:
    job = Job(
        id=new_id(),
        request_id=request_id,
        job_type=job_type,
        status=JobStatus.pending,
        progress=0.0,
        render=render,
        scene=scene,
        message=message,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    logger.info(
        "Created job",
        extra={"job_id": job.id, "request_id": request_id, "job_type": job.job_type.value},
    )
    return job


def process_render_job(job_id: str) -> None:
    provider = PiperTTSProvider()
    with new_session() as session:
        job = session.get(Job, job_id)
        if not job or not job.render_id:
            logger.error("Render job missing job or render", extra={"job_id": job_id})
            return
        render = session.get(Render, job.render_id)
        if not render:
            logger.error("Render not found", extra={"render_id": job.render_id})
            return
        scenes = (
            session.query(Scene)
            .filter(Scene.project_id == render.project_id)
            .order_by(Scene.order.asc())
            .all()
        )
        try:
            render.status = RenderStatus.in_progress
            render.started_at = utcnow()
            job.status = JobStatus.in_progress
            session.commit()

            total = len(scenes)
            for index, scene in enumerate(scenes, start=1):
                wav_output = (
                    settings.data_directory
                    / settings.assets_subdir
                    / f"{scene.id}.wav"
                )
                normalized_output = (
                    settings.data_directory
                    / settings.assets_subdir
                    / f"{scene.id}_normalized.wav"
                )
                try:
                    provider.synthesize(scene.text, wav_output)
                    normalize_wav(wav_output, normalized_output)
                except TTSModelUnavailableError as exc:
                    job.status = JobStatus.blocked
                    job.message = str(exc)
                    render.status = RenderStatus.failed
                    session.commit()
                    return
                except TTSProviderError as exc:
                    job.status = JobStatus.failed
                    job.message = str(exc)
                    render.status = RenderStatus.failed
                    session.commit()
                    return

                scene.audio_path = str(normalized_output)
                session.add(
                    Asset(
                        id=new_id(),
                        render_id=render.id,
                        scene_id=scene.id,
                        asset_type=AssetType.scene_audio,
                        path=str(normalized_output),
                    )
                )
                job.progress = index / total
                session.commit()

            render.status = RenderStatus.completed
            render.completed_at = utcnow()
            if render.project:
                render.project.status = ProjectStatus.completed
            job.status = JobStatus.completed
            job.progress = 1.0
            session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error during render", extra={"job_id": job_id})
            job.status = JobStatus.failed
            job.message = str(exc)
            render.status = RenderStatus.failed
            if render.project:
                render.project.status = ProjectStatus.failed
            session.commit()


def process_tts_job(job_id: str, asset_id: str, text: str, voice: str | None) -> None:
    provider = PiperTTSProvider()
    with new_session() as session:
        job = session.get(Job, job_id)
        if not job:
            logger.error("TTS job missing", extra={"job_id": job_id})
            return

        destination_raw = (
            settings.data_directory
            / settings.assets_subdir
            / f"{asset_id}.wav"
        )
        destination_normalized = (
            settings.data_directory
            / settings.assets_subdir
            / f"{asset_id}_normalized.wav"
        )

        try:
            job.status = JobStatus.in_progress
            session.commit()

            provider.synthesize(text, destination_raw, voice)
            normalize_wav(destination_raw, destination_normalized)

            asset = session.get(Asset, asset_id)
            if asset is None:
                asset = Asset(
                    id=asset_id,
                    asset_type=AssetType.scene_audio,
                    path=str(destination_normalized),
                )
            asset.path = str(destination_normalized)
            session.merge(asset)

            job.status = JobStatus.completed
            job.progress = 1.0
            job.message = "TTS complete"
            session.commit()
        except TTSModelUnavailableError as exc:
            job.status = JobStatus.blocked
            job.message = str(exc)
            session.commit()
        except TTSProviderError as exc:
            job.status = JobStatus.failed
            job.message = str(exc)
            session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected TTS failure", extra={"job_id": job_id})
            job.status = JobStatus.failed
            job.message = str(exc)
            session.commit()


def process_export_job(
    job_id: str,
    asset_id: str,
    title: str,
    author: str | None,
    album: str | None,
) -> None:
    with new_session() as session:
        job = session.get(Job, job_id)
        if not job or not job.render_id:
            logger.error("Export job missing job or render", extra={"job_id": job_id})
            return
        render = session.get(Render, job.render_id)
        if not render:
            logger.error("Render not found for export", extra={"render_id": job.render_id})
            return
        scenes = (
            session.query(Scene)
            .filter(Scene.project_id == render.project_id)
            .order_by(Scene.order.asc())
            .all()
        )
        wav_paths = [Path(scene.audio_path) for scene in scenes if scene.audio_path]
        if not wav_paths:
            job.status = JobStatus.failed
            job.message = "No audio available for export"
            session.commit()
            return

        combined_wav = (
            settings.data_directory
            / settings.exports_subdir
            / f"{render.id}_combined.wav"
        )
        mp3_output = (
            settings.data_directory
            / settings.exports_subdir
            / f"{render.id}.mp3"
        )
        export_zip = (
            settings.data_directory
            / settings.exports_subdir
            / f"{asset_id}.zip"
        )

        try:
            job.status = JobStatus.in_progress
            session.commit()

            concatenate_scenes(wav_paths, combined_wav)
            convert_to_mp3(combined_wav, mp3_output)
            add_id3_tags(mp3_output, title=title, artist=author, album=album)

            import zipfile

            export_zip.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(export_zip, "w") as archive:
                archive.write(mp3_output, arcname=mp3_output.name)
                for scene in scenes:
                    if scene.audio_path:
                        audio_path = Path(scene.audio_path)
                        if audio_path.exists():
                            archive.write(audio_path, arcname=audio_path.name)

            asset = session.get(Asset, asset_id)
            if asset is None:
                asset = Asset(
                    id=asset_id,
                    render_id=render.id,
                    asset_type=AssetType.export_zip,
                    path=str(export_zip),
                )
            asset.render_id = render.id
            asset.asset_type = AssetType.export_zip
            asset.path = str(export_zip)
            session.merge(asset)

            job.status = JobStatus.completed
            job.progress = 1.0
            session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Export job failed", extra={"job_id": job_id})
            job.status = JobStatus.failed
            job.message = str(exc)
            session.commit()


def schedule_render_job(background_tasks: BackgroundTasks, job_id: str) -> None:
    background_tasks.add_task(process_render_job, job_id)


def schedule_tts_job(
    background_tasks: BackgroundTasks,
    job_id: str,
    asset_id: str,
    text: str,
    voice: str | None,
) -> None:
    background_tasks.add_task(process_tts_job, job_id, asset_id, text, voice)


def schedule_export_job(
    background_tasks: BackgroundTasks,
    job_id: str,
    asset_id: str,
    title: str,
    author: str | None,
    album: str | None,
) -> None:
    background_tasks.add_task(process_export_job, job_id, asset_id, title, author, album)
