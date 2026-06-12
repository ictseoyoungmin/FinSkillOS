"""trade native currency

Adds a ``currency`` column to ``trades`` so realized P&L can be computed in the
trade's *native* currency (USD for US tickers, KRW for KR), instead of relying on
sync-time KRW conversion. Nullable + no server default: legacy rows stay NULL and
analytics infer the currency from the ticker until a Toss re-sync backfills it.

Revision ID: 0019_trade_currency
Revises: 0018_settings_history
Create Date: 2026-06-12 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0019_trade_currency"
down_revision = "0018_settings_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trades", sa.Column("currency", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("trades", "currency")
