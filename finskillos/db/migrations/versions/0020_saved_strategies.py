"""saved quant strategies

Revision ID: 0020_saved_strategies
Revises: 0019_trade_currency
Create Date: 2026-06-22 00:00:00.000000

Persists agent-authored / custom Quant Lab specs (Slice 333). `create_table` is
portable across SQLite and Postgres (no ALTER), so the alembic SQLite smoke
passes alongside the compose Postgres apply.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0020_saved_strategies"
down_revision = "0019_trade_currency"
branch_labels = None
depends_on = None

_JSON = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "saved_strategies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("spec", _JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_saved_strategies_created", "saved_strategies", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_saved_strategies_created", table_name="saved_strategies")
    op.drop_table("saved_strategies")
