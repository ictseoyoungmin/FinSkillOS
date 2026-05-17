"""market data foundation — market_bars + indicator_snapshots

Revision ID: 0002_market_data_foundation
Revises: 0001_initial_foundation
Create Date: 2026-05-17 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_market_data_foundation"
down_revision = "0001_initial_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_bars",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("bar_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("high", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("low", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("adj_close", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("volume", sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="mock",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "ticker",
            "timeframe",
            "bar_time",
            name="uq_market_bars_ticker_tf_time",
        ),
    )
    op.create_index(
        "idx_market_bars_lookup",
        "market_bars",
        ["ticker", "timeframe", "bar_time"],
    )

    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rsi_14", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("ema_20", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("ema_60", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("ema_120", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("bb_mid", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("bb_upper", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("bb_lower", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("volume_zscore", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("momentum_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("trend_state", sa.String(length=32), nullable=True),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="internal",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "ticker",
            "timeframe",
            "snapshot_time",
            name="uq_indicator_snapshots_ticker_tf_time",
        ),
    )
    op.create_index(
        "idx_indicators_lookup",
        "indicator_snapshots",
        ["ticker", "timeframe", "snapshot_time"],
    )


def downgrade() -> None:
    op.drop_index("idx_indicators_lookup", table_name="indicator_snapshots")
    op.drop_table("indicator_snapshots")

    op.drop_index("idx_market_bars_lookup", table_name="market_bars")
    op.drop_table("market_bars")
