"""system ops protocol run audit table

Revision ID: 0011_system_ops_protocol_runs
Revises: 0010_symbol_logo_cache
Create Date: 2026-05-27 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_system_ops_protocol_runs"
down_revision = "0010_symbol_logo_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_ops_protocol_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("protocol", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "db_status",
            sa.String(length=16),
            server_default="UNKNOWN",
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=16),
            server_default="live",
            nullable=False,
        ),
        sa.Column("ran_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_system_ops_protocol_runs_protocol_time",
        "system_ops_protocol_runs",
        ["protocol", "ran_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_system_ops_protocol_runs_protocol_time",
        table_name="system_ops_protocol_runs",
    )
    op.drop_table("system_ops_protocol_runs")
