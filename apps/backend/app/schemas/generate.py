from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, constr, validator

from .common import generate_uuid


class SceneInput(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    order: int
    text: constr(min_length=1, max_length=5000)


class GenerateRequest(BaseModel):
    project_name: constr(min_length=1, max_length=255)
    description: Optional[constr(max_length=1024)] = None
    scenes: List[SceneInput]

    @validator("scenes")
    def validate_scenes(cls, value: List[SceneInput]) -> List[SceneInput]:
        if not value:
            raise ValueError("At least one scene is required")
        return value


class GenerateResponse(BaseModel):
    project_id: str
    render_id: str
    job_id: str
    request_id: str
