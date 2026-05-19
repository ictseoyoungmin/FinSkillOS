"""event radar — events + event_links

Revision ID: 0006_event_radar
Revises: 0005_news_intelligence
Create Date: 2026-05-19 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_event_radar"
down_revision = "0005_news_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column(
            "date_status",
            sa.String(length=16),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "importance_score",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="1.0",
        ),
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
    op.create_index("idx_events_date", "events", ["start_date"])
    op.create_index("idx_events_end_date", "events", ["end_date"])
    op.create_index("idx_events_type", "events", ["event_type"])
    op.create_index("idx_events_date_status", "events", ["date_status"])

    op.create_table(
        "event_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "event_id",
            sa.Uuid(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(length=32), nullable=True),
        sa.Column("sector", sa.String(length=80), nullable=True),
        sa.Column("theme", sa.String(length=80), nullable=True),
        sa.Column("event_key", sa.String(length=80), nullable=True),
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
    op.create_index("idx_event_links_ticker", "event_links", ["ticker"])
    op.create_index("idx_event_links_sector", "event_links", ["sector"])
    op.create_index("idx_event_links_theme", "event_links", ["theme"])
    op.create_index(
        "idx_event_links_event_key", "event_links", ["event_key"]
    )


def downgrade() -> None:
    op.drop_index("idx_event_links_event_key", table_name="event_links")
    op.drop_index("idx_event_links_theme", table_name="event_links")
    op.drop_index("idx_event_links_sector", table_name="event_links")
    op.drop_index("idx_event_links_ticker", table_name="event_links")
    op.drop_table("event_links")

    op.drop_index("idx_events_date_status", table_name="events")
    op.drop_index("idx_events_type", table_name="events")
    op.drop_index("idx_events_end_date", table_name="events")
    op.drop_index("idx_events_date", table_name="events")
    op.drop_table("events")
