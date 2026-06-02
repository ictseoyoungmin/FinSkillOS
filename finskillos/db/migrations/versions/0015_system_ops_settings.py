"""persistent runtime settings override table for Ops tab"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015_system_ops_settings"
down_revision = "0014_worker_control"
branch_labels = None
depends_on = None

JSON_PAYLOAD = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "system_ops_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("values", JSON_PAYLOAD, nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_by",
            sa.String(length=32),
            server_default="system",
            nullable=False,
        ),
    )
    op.execute(
        'INSERT INTO system_ops_settings (id, "values", updated_by) '
        "VALUES (1, '{}', 'migration')"
    )


def downgrade() -> None:
    op.drop_table("system_ops_settings")
