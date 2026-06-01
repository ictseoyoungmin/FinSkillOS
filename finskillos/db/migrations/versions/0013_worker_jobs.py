"""worker job queue table

Revision ID: 0013_worker_jobs
Revises: 0012_worker_cycle_runs
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0013_worker_jobs"
down_revision = "0012_worker_cycle_runs"
branch_labels = None
depends_on = None

JSON_PAYLOAD = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "worker_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default="QUEUED", nullable=False
        ),
        sa.Column("dedup_key", sa.String(length=128), nullable=True),
        sa.Column(
            "requested_by",
            sa.String(length=32),
            server_default="system",
            nullable=False,
        ),
        sa.Column("payload", JSON_PAYLOAD, nullable=True),
        sa.Column("result", JSON_PAYLOAD, nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_worker_jobs_status_created", "worker_jobs", ["status", "created_at"]
    )
    op.create_index(
        "idx_worker_jobs_type_dedup_status",
        "worker_jobs",
        ["job_type", "dedup_key", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_worker_jobs_type_dedup_status", table_name="worker_jobs")
    op.drop_index("idx_worker_jobs_status_created", table_name="worker_jobs")
    op.drop_table("worker_jobs")
