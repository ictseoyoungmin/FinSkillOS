"""add regime factor columns

Revision ID: 0004_market_regime_factors
Revises: 0003_market_regimes
Create Date: 2026-05-18 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_market_regime_factors"
down_revision = "0003_market_regimes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_payload = sa.JSON().with_variant(JSONB(), "postgresql")
    op.add_column(
        "market_regimes",
        sa.Column("positive_factors", json_payload, nullable=True),
    )
    op.add_column(
        "market_regimes",
        sa.Column("risk_factors", json_payload, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("market_regimes", "risk_factors")
    op.drop_column("market_regimes", "positive_factors")
