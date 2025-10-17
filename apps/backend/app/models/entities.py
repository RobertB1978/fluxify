from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RenderStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class JobStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"


class JobType(str, enum.Enum):
    render = "render"
    tts = "tts"
    export = "export"


class AssetType(str, enum.Enum):
    scene_audio = "scene_audio"
    export_zip = "export_zip"
    temporary = "temporary"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.draft, nullable=False
    )

    scenes: Mapped[List["Scene"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    renders: Mapped[List["Render"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Scene(TimestampMixin, Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)

    project: Mapped[Project] = relationship(back_populates="scenes")
    assets: Mapped[List["Asset"]] = relationship(
        back_populates="scene",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Render(TimestampMixin, Base):
    __tablename__ = "renders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[RenderStatus] = mapped_column(
        Enum(RenderStatus), default=RenderStatus.pending, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    project: Mapped[Project] = relationship(back_populates="renders")
    jobs: Mapped[List["Job"]] = relationship(
        back_populates="render",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assets: Mapped[List["Asset"]] = relationship(
        back_populates="render",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    render_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("renders.id", ondelete="CASCADE"), nullable=True
    )
    scene_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True
    )
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.pending, nullable=False
    )
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)

    render: Mapped[Optional[Render]] = relationship(back_populates="jobs")
    scene: Mapped[Optional[Scene]] = relationship(back_populates="jobs")


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    render_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("renders.id", ondelete="CASCADE"), nullable=True
    )
    scene_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    render: Mapped[Optional[Render]] = relationship(back_populates="assets")
    scene: Mapped[Optional[Scene]] = relationship(back_populates="assets")


Scene.jobs = relationship(
    "Job",
    back_populates="scene",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
