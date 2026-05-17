"""initial foundation — accounts, snapshots, positions, trades, alerts

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-05-17 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial_foundation"
down_revision = None
branch_labels = None
depends_on = None


# Portable JSON column: JSONB on Postgres, JSON elsewhere (SQLite test runs).
JSON_PAYLOAD = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column(
            "base_currency",
            sa.String(length=8),
            nullable=False,
            server_default="KRW",
        ),
        sa.Column("target_value", sa.Numeric(precision=18, scale=2), nullable=False),
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
    )

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "cash_value",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("peak_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("drawdown_pct", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "account_id",
            "snapshot_date",
            name="uq_portfolio_snapshot_account_date",
        ),
    )
    op.create_index(
        "idx_snapshots_account_date",
        "portfolio_snapshots",
        ["account_id", "snapshot_date"],
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("sector", sa.String(length=80), nullable=True),
        sa.Column("theme", sa.String(length=80), nullable=True),
        sa.Column(
            "strategy_type",
            sa.String(length=32),
            nullable=False,
            server_default="swing",
        ),
        sa.Column("quantity", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("average_cost", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("market_value", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("pnl_pct", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("stop_loss", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("take_profit", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("thesis", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("account_id", "ticker", name="uq_positions_account_ticker"),
    )
    op.create_index(
        "idx_positions_account_ticker", "positions", ["account_id", "ticker"]
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column(
            "strategy_type",
            sa.String(length=32),
            nullable=False,
            server_default="swing",
        ),
        sa.Column("quantity", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("fees", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("catalyst", sa.String(length=160), nullable=True),
        sa.Column("emotion_state", sa.String(length=40), nullable=True),
        sa.Column("market_regime", sa.String(length=40), nullable=True),
        sa.Column("mistake_tag", sa.String(length=40), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_trades_account_date", "trades", ["account_id", "trade_date"]
    )
    op.create_index(
        "idx_trades_ticker_date", "trades", ["ticker", "trade_date"]
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("alert_date", sa.Date(), nullable=False),
        sa.Column("guard_name", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("payload", JSON_PAYLOAD, nullable=True),
        sa.Column(
            "resolved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_alerts_date_severity", "alerts", ["alert_date", "severity"]
    )
    op.create_index(
        "idx_alerts_active", "alerts", ["resolved", "severity", "alert_date"]
    )


def downgrade() -> None:
    op.drop_index("idx_alerts_active", table_name="alerts")
    op.drop_index("idx_alerts_date_severity", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("idx_trades_ticker_date", table_name="trades")
    op.drop_index("idx_trades_account_date", table_name="trades")
    op.drop_table("trades")

    op.drop_index("idx_positions_account_ticker", table_name="positions")
    op.drop_table("positions")

    op.drop_index("idx_snapshots_account_date", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")

    op.drop_table("accounts")
