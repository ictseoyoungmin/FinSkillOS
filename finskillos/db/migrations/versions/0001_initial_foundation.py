"""initial foundation

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-05-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("base_currency", sa.String(length=3), nullable=False, server_default="KRW"),
        sa.Column("target_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("cash_value", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "snapshot_date", name="uq_portfolio_snapshot_account_date"),
    )
    op.create_table(
        "portfolio_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_id", sa.Integer(), sa.ForeignKey("portfolio_snapshots.id"), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("asset_class", sa.String(length=40), nullable=False, server_default="equity"),
        sa.Column("sector", sa.String(length=80), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("market_value", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("cost_basis", sa.Numeric(precision=18, scale=2), nullable=True),
    )
    op.create_index("ix_portfolio_positions_symbol", "portfolio_positions", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_portfolio_positions_symbol", table_name="portfolio_positions")
    op.drop_table("portfolio_positions")
    op.drop_table("portfolio_snapshots")
    op.drop_table("accounts")
