"""worker control (live-mode toggle) singleton

Revision ID: 0014_worker_control
Revises: 0013_worker_jobs
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_worker_control"
down_revision = "0013_worker_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_control",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "live_mode", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_by",
            sa.String(length=32),
            server_default="system",
            nullable=False,
        ),
    )
    # Seed the singleton row (id=1) so the worker / API always find it.
    op.execute(
        "INSERT INTO worker_control (id, live_mode, updated_by) "
        "VALUES (1, true, 'migration')"
    )


def downgrade() -> None:
    op.drop_table("worker_control")
