"""folder collection-control flags

Revision ID: 0016_folder_collection_flags
Revises: 0015_system_ops_settings
Create Date: 2026-06-02 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_folder_collection_flags"
down_revision = "0015_system_ops_settings"
branch_labels = None
depends_on = None

_FLAGS = (
    ("is_active", sa.true()),
    ("track_market", sa.true()),
    ("track_indicators", sa.true()),
    ("track_news", sa.true()),
    ("is_system", sa.false()),
)


def upgrade() -> None:
    for name, default in _FLAGS:
        op.add_column(
            "symbol_subscription_folders",
            sa.Column(
                name, sa.Boolean(), server_default=default, nullable=False
            ),
        )


def downgrade() -> None:
    for name, _ in reversed(_FLAGS):
        op.drop_column("symbol_subscription_folders", name)
