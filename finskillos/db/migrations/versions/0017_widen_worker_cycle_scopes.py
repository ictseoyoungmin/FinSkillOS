"""widen worker_cycle_runs scope columns for folder-scoped labels

Revision ID: 0017_widen_worker_cycle_scopes
Revises: 0016_folder_collection_flags
Create Date: 2026-06-03 00:00:00.000000

Slice 134 (F3) records folder-scoped refresh audit labels like
``collection:indicator:folder=<uuid>`` (~63 chars), which overflowed the
original ``VARCHAR(32)`` scope columns on PostgreSQL (SQLite ignores the length,
so offline tests did not catch it). Widen to ``VARCHAR(80)``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_widen_worker_cycle_scopes"
down_revision = "0016_folder_collection_flags"
branch_labels = None
depends_on = None

_COLUMNS = ("market_scope", "news_scope", "indicator_scope")


def upgrade() -> None:
    # batch_alter_table keeps this portable: SQLite has no ALTER COLUMN TYPE, so
    # alembic recreates the table there; Postgres issues a normal ALTER.
    with op.batch_alter_table("worker_cycle_runs") as batch_op:
        for name in _COLUMNS:
            batch_op.alter_column(
                name,
                existing_type=sa.String(length=32),
                type_=sa.String(length=80),
                existing_nullable=False,
                existing_server_default="unknown",
            )


def downgrade() -> None:
    with op.batch_alter_table("worker_cycle_runs") as batch_op:
        for name in _COLUMNS:
            batch_op.alter_column(
                name,
                existing_type=sa.String(length=80),
                type_=sa.String(length=32),
                existing_nullable=False,
                existing_server_default="unknown",
            )
