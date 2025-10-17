from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, constr

from .common import generate_uuid


class ExportRequest(BaseModel):
    render_id: constr(min_length=1)
    title: constr(min_length=1, max_length=255)
    author: Optional[constr(max_length=255)] = None
    album: Optional[constr(max_length=255)] = None
    request_id: str = Field(default_factory=generate_uuid)


class ExportResponse(BaseModel):
    export_id: str
    job_id: str
    request_id: str
