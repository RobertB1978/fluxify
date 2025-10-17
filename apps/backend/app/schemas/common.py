from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from ..utils.identifiers import new_id


def generate_uuid() -> str:
    return new_id()


class TimestampedModel(BaseModel):
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.astimezone(timezone.utc).isoformat(),
        }


class JobBase(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    request_id: str = Field(default_factory=generate_uuid)
