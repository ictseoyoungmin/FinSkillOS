"""worker cycle run audit table

Revision ID: 0012_worker_cycle_runs
Revises: 0011_system_ops_protocol_runs
Create Date: 2026-05-27 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012_worker_cycle_runs"
down_revision = "0011_system_ops_protocol_runs"
branch_labels = None
depends_on = None

JSON_PAYLOAD = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "worker_cycle_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column(
            "market_status",
            sa.String(length=16),
            server_default="SKIPPED",
            nullable=False,
        ),
        sa.Column(
            "news_status",
            sa.String(length=16),
            server_default="SKIPPED",
            nullable=False,
        ),
        sa.Column(
            "indicator_status",
            sa.String(length=16),
            server_default="SKIPPED",
            nullable=False,
        ),
        sa.Column(
            "market_scope",
            sa.String(length=32),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column(
            "news_scope",
            sa.String(length=32),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column(
            "indicator_scope",
            sa.String(length=32),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("summary", JSON_PAYLOAD, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_worker_cycle_runs_started_at",
        "worker_cycle_runs",
        ["started_at"],
    )
    op.create_index(
        "idx_worker_cycle_runs_status_time",
        "worker_cycle_runs",
        ["status", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_worker_cycle_runs_status_time", table_name="worker_cycle_runs")
    op.drop_index("idx_worker_cycle_runs_started_at", table_name="worker_cycle_runs")
    op.drop_table("worker_cycle_runs")
