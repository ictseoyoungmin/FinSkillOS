"""runtime settings change history

Revision ID: 0018_settings_history
Revises: 0017_widen_worker_cycle_scopes
Create Date: 2026-06-03 00:00:00.000000

Append-only change log for runtime-setting overlay edits (Slice 149). `create_table`
is portable across SQLite and Postgres (no ALTER), so the alembic SQLite smoke
passes alongside the compose Postgres apply.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0018_settings_history"
down_revision = "0017_widen_worker_cycle_scopes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_ops_settings_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("setting_key", sa.String(length=64), nullable=False),
        sa.Column("old_value", sa.String(length=512), nullable=True),
        sa.Column("new_value", sa.String(length=512), nullable=True),
        sa.Column(
            "updated_by",
            sa.String(length=32),
            nullable=False,
            server_default="system",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_system_ops_settings_history_created",
        "system_ops_settings_history",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_system_ops_settings_history_created",
        table_name="system_ops_settings_history",
    )
    op.drop_table("system_ops_settings_history")
