"""symbol subscription folders

Revision ID: 0009_symbol_subscription_folders
Revises: 0008_symbol_subscriptions
Create Date: 2026-05-26 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_symbol_subscription_folders"
down_revision = "0008_symbol_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "symbol_subscription_folders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("name", name="uq_symbol_subscription_folders_name"),
    )
    op.create_index(
        "idx_symbol_subscription_folders_sort",
        "symbol_subscription_folders",
        ["sort_order", "name"],
    )

    op.create_table(
        "symbol_subscription_folder_memberships",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("folder_id", sa.Uuid(), nullable=False),
        sa.Column("subscription_id", sa.Uuid(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["symbol_subscription_folders.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["symbol_subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "folder_id",
            "subscription_id",
            name="uq_symbol_subscription_folder_membership",
        ),
    )
    op.create_index(
        "idx_symbol_subscription_folder_memberships_folder",
        "symbol_subscription_folder_memberships",
        ["folder_id", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_symbol_subscription_folder_memberships_folder",
        table_name="symbol_subscription_folder_memberships",
    )
    op.drop_table("symbol_subscription_folder_memberships")
    op.drop_index(
        "idx_symbol_subscription_folders_sort",
        table_name="symbol_subscription_folders",
    )
    op.drop_table("symbol_subscription_folders")
