"""symbol subscriptions

Revision ID: 0008_symbol_subscriptions
Revises: 0007_trade_journal_fields
Create Date: 2026-05-25 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_symbol_subscriptions"
down_revision = "0007_trade_journal_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "symbol_subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="user",
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
        sa.UniqueConstraint("ticker", name="uq_symbol_subscriptions_ticker"),
    )
    op.create_index(
        "idx_symbol_subscriptions_active_ticker",
        "symbol_subscriptions",
        ["active", "ticker"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_symbol_subscriptions_active_ticker",
        table_name="symbol_subscriptions",
    )
    op.drop_table("symbol_subscriptions")
