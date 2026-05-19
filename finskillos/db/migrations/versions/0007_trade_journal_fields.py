"""trade journal fields — Slice 12

Revision ID: 0007_trade_journal_fields
Revises: 0006_event_radar
Create Date: 2026-05-19 00:00:00.000000

Extends the Slice-02 ``trades`` table with the reflection columns
called out in .devmd/12 (thesis, result_pnl, result_pnl_pct,
r_multiple, mistake_tags list, notes, sector, theme, event_key,
updated_at) and widens ``side`` / ``strategy_type`` /
``market_regime`` / ``emotion_state`` to fit the Slice-12 vocabulary
(LONG / SHORT / WATCH / EXIT_REVIEW / OTHER plus full regime / emotion
labels).

SQLite needs ``batch_alter_table`` to widen existing column types, so
the column widening pass uses a batch context. The ADD-column pass
runs through the normal ``op.add_column`` API because every new field
is nullable.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0007_trade_journal_fields"
down_revision = "0006_event_radar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Widen narrow columns to fit the Slice-12 journal vocabulary ---
    with op.batch_alter_table("trades") as batch_op:
        batch_op.alter_column(
            "side",
            existing_type=sa.String(length=8),
            type_=sa.String(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "strategy_type",
            existing_type=sa.String(length=32),
            type_=sa.String(length=80),
            existing_nullable=False,
            server_default="swing",
        )
        batch_op.alter_column(
            "market_regime",
            existing_type=sa.String(length=40),
            type_=sa.String(length=80),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "emotion_state",
            existing_type=sa.String(length=40),
            type_=sa.String(length=80),
            existing_nullable=True,
        )

    # --- Add the new reflection columns ---
    json_payload = sa.JSON().with_variant(JSONB(), "postgresql")
    op.add_column("trades", sa.Column("thesis", sa.Text(), nullable=True))
    op.add_column(
        "trades",
        sa.Column("result_pnl", sa.Numeric(precision=18, scale=2), nullable=True),
    )
    op.add_column(
        "trades",
        sa.Column(
            "result_pnl_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
        ),
    )
    op.add_column(
        "trades",
        sa.Column(
            "r_multiple",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
        ),
    )
    op.add_column(
        "trades",
        sa.Column("mistake_tags", json_payload, nullable=True),
    )
    op.add_column("trades", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "trades", sa.Column("sector", sa.String(length=80), nullable=True)
    )
    op.add_column(
        "trades", sa.Column("theme", sa.String(length=80), nullable=True)
    )
    op.add_column(
        "trades", sa.Column("event_key", sa.String(length=80), nullable=True)
    )
    op.add_column(
        "trades",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- Reflection indexes ---
    op.create_index("idx_trades_market_regime", "trades", ["market_regime"])
    op.create_index("idx_trades_strategy_type", "trades", ["strategy_type"])
    op.create_index("idx_trades_sector", "trades", ["sector"])
    op.create_index("idx_trades_theme", "trades", ["theme"])
    op.create_index("idx_trades_event_key", "trades", ["event_key"])


def downgrade() -> None:
    op.drop_index("idx_trades_event_key", table_name="trades")
    op.drop_index("idx_trades_theme", table_name="trades")
    op.drop_index("idx_trades_sector", table_name="trades")
    op.drop_index("idx_trades_strategy_type", table_name="trades")
    op.drop_index("idx_trades_market_regime", table_name="trades")

    op.drop_column("trades", "updated_at")
    op.drop_column("trades", "event_key")
    op.drop_column("trades", "theme")
    op.drop_column("trades", "sector")
    op.drop_column("trades", "notes")
    op.drop_column("trades", "mistake_tags")
    op.drop_column("trades", "r_multiple")
    op.drop_column("trades", "result_pnl_pct")
    op.drop_column("trades", "result_pnl")
    op.drop_column("trades", "thesis")

    with op.batch_alter_table("trades") as batch_op:
        batch_op.alter_column(
            "emotion_state",
            existing_type=sa.String(length=80),
            type_=sa.String(length=40),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "market_regime",
            existing_type=sa.String(length=80),
            type_=sa.String(length=40),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "strategy_type",
            existing_type=sa.String(length=80),
            type_=sa.String(length=32),
            existing_nullable=False,
            server_default="swing",
        )
        batch_op.alter_column(
            "side",
            existing_type=sa.String(length=16),
            type_=sa.String(length=8),
            existing_nullable=False,
        )
