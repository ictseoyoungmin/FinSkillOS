"""symbol logo cache

Revision ID: 0010_symbol_logo_cache
Revises: 0009_symbol_subscription_folders
Create Date: 2026-05-26 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_symbol_logo_cache"
down_revision = "0009_symbol_subscription_folders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "symbol_logo_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ticker", sa.String(length=24), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("logo_url", sa.String(length=1024), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("ticker", name="uq_symbol_logo_cache_ticker"),
    )
    op.create_index(
        "idx_symbol_logo_cache_provider",
        "symbol_logo_cache",
        ["provider", "ticker"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_symbol_logo_cache_provider",
        table_name="symbol_logo_cache",
    )
    op.drop_table("symbol_logo_cache")
