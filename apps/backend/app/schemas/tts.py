from __future__ import annotations

from pydantic import BaseModel, Field, constr

from .common import generate_uuid


class TTSRequest(BaseModel):
    text: constr(min_length=1, max_length=5000)
    voice: str | None = None
    request_id: str = Field(default_factory=generate_uuid)


class TTSResponse(BaseModel):
    job_id: str
    request_id: str
    asset_id: str
