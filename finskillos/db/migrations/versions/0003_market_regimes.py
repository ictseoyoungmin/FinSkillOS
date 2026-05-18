"""market regime history — market_regimes

Revision ID: 0003_market_regimes
Revises: 0002_market_data_foundation
Create Date: 2026-05-18 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_market_regimes"
down_revision = "0002_market_data_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_payload = sa.JSON().with_variant(JSONB(), "postgresql")
    op.create_table(
        "market_regimes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("regime", sa.String(length=32), nullable=False),
        sa.Column(
            "confidence",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("decision_mode", sa.String(length=40), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("what_happened", sa.Text(), nullable=True),
        sa.Column("what_it_means", sa.Text(), nullable=True),
        sa.Column("watch_next", json_payload, nullable=True),
        sa.Column("evidence", json_payload, nullable=True),
        sa.Column("rule_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "snapshot_time",
            "rule_version",
            name="uq_market_regimes_snapshot_rule",
        ),
    )
    op.create_index(
        "idx_market_regimes_snapshot",
        "market_regimes",
        ["snapshot_time"],
    )


def downgrade() -> None:
    op.drop_index("idx_market_regimes_snapshot", table_name="market_regimes")
    op.drop_table("market_regimes")
