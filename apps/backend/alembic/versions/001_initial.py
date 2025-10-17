from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


PROJECT_STATUS = sa.Enum("draft", "processing", "completed", "failed", name="projectstatus")
RENDER_STATUS = sa.Enum("pending", "in_progress", "completed", "failed", name="renderstatus")
JOB_STATUS = sa.Enum(
    "pending",
    "in_progress",
    "completed",
    "failed",
    "blocked",
    name="jobstatus",
)
JOB_TYPE = sa.Enum("render", "tts", "export", name="jobtype")
ASSET_TYPE = sa.Enum("scene_audio", "export_zip", "temporary", name="assettype")


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", PROJECT_STATUS, nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "renders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", RENDER_STATUS, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "scenes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("audio_path", sa.String(length=512), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("render_id", sa.String(length=36), sa.ForeignKey("renders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scene_id", sa.String(length=36), sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("job_type", JOB_TYPE, nullable=False),
        sa.Column("status", JOB_STATUS, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("progress", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("render_id", sa.String(length=36), sa.ForeignKey("renders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scene_id", sa.String(length=36), sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("asset_type", ASSET_TYPE, nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index("ix_scenes_project_order", "scenes", ["project_id", "order"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_scenes_project_order", table_name="scenes")
    op.drop_table("assets")
    op.drop_table("jobs")
    op.drop_table("scenes")
    op.drop_table("renders")
    op.drop_table("projects")
    ASSET_TYPE.drop(op.get_bind(), checkfirst=False)
    JOB_TYPE.drop(op.get_bind(), checkfirst=False)
    JOB_STATUS.drop(op.get_bind(), checkfirst=False)
    RENDER_STATUS.drop(op.get_bind(), checkfirst=False)
    PROJECT_STATUS.drop(op.get_bind(), checkfirst=False)
