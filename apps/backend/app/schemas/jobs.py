from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel

from ..models.entities import JobStatus, JobType


class JobResponse(BaseModel):
    id: str
    job_type: JobType
    status: JobStatus
    progress: float
    message: Optional[str]
    request_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.astimezone(timezone.utc).isoformat(),
        }
        orm_mode = True
