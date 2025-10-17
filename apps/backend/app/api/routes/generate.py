from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from ...models.entities import JobType, Project, ProjectStatus, Render, Scene
from ...schemas.generate import GenerateRequest, GenerateResponse
from ...services.jobs import create_job, schedule_render_job
from ...utils.identifiers import new_id
from ..deps.db import get_db, get_rate_limiter_dependency

router = APIRouter(prefix="/v1", tags=["generation"])


@router.post("/generate", response_model=GenerateResponse)
def generate_project(
    payload: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _rate=Depends(get_rate_limiter_dependency()),
) -> GenerateResponse:
    project = Project(
        id=new_id(),
        name=payload.project_name,
        description=payload.description,
        status=ProjectStatus.processing,
    )
    db.add(project)

    for scene_input in sorted(payload.scenes, key=lambda item: item.order):
        scene = Scene(
            id=scene_input.id,
            project_id=project.id,
            order=scene_input.order,
            text=scene_input.text,
        )
        db.add(scene)

    render = Render(
        id=new_id(),
        project_id=project.id,
    )
    db.add(render)
    db.commit()
    db.refresh(render)
    db.refresh(project)

    job_request_id = new_id()
    job = create_job(
        db,
        job_type=JobType.render,
        request_id=job_request_id,
        render=render,
    )

    schedule_render_job(background_tasks, job.id)

    return GenerateResponse(
        project_id=project.id,
        render_id=render.id,
        job_id=job.id,
        request_id=job_request_id,
    )
