"""news intelligence — news_articles + news_impacts

Revision ID: 0005_news_intelligence
Revises: 0004_market_regime_factors
Create Date: 2026-05-19 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_news_intelligence"
down_revision = "0004_market_regime_factors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column(
            "published_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=True),
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
        sa.UniqueConstraint("url", name="uq_news_articles_url"),
    )
    op.create_index(
        "idx_news_articles_published", "news_articles", ["published_at"]
    )
    op.create_index("idx_news_articles_source", "news_articles", ["source"])

    op.create_table(
        "news_impacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "article_id",
            sa.Uuid(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(length=32), nullable=True),
        sa.Column("sector", sa.String(length=80), nullable=True),
        sa.Column("theme", sa.String(length=80), nullable=True),
        sa.Column("event_key", sa.String(length=80), nullable=True),
        sa.Column(
            "impact_score",
            sa.Numeric(precision=6, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "sentiment_label",
            sa.String(length=16),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column(
            "risk_level",
            sa.String(length=16),
            nullable=False,
            server_default="UNKNOWN",
        ),
        sa.Column("risk_note", sa.Text(), nullable=True),
        sa.Column("volatility_note", sa.Text(), nullable=True),
        sa.Column(
            "is_event_linked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
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
    op.create_index("idx_news_impacts_ticker", "news_impacts", ["ticker"])
    op.create_index("idx_news_impacts_sector", "news_impacts", ["sector"])
    op.create_index("idx_news_impacts_theme", "news_impacts", ["theme"])
    op.create_index(
        "idx_news_impacts_event_key", "news_impacts", ["event_key"]
    )
    op.create_index(
        "idx_news_impacts_event_linked", "news_impacts", ["is_event_linked"]
    )
    op.create_index(
        "idx_news_ticker_date",
        "news_impacts",
        ["ticker", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_news_ticker_date", table_name="news_impacts")
    op.drop_index("idx_news_impacts_event_linked", table_name="news_impacts")
    op.drop_index("idx_news_impacts_event_key", table_name="news_impacts")
    op.drop_index("idx_news_impacts_theme", table_name="news_impacts")
    op.drop_index("idx_news_impacts_sector", table_name="news_impacts")
    op.drop_index("idx_news_impacts_ticker", table_name="news_impacts")
    op.drop_table("news_impacts")

    op.drop_index("idx_news_articles_source", table_name="news_articles")
    op.drop_index("idx_news_articles_published", table_name="news_articles")
    op.drop_table("news_articles")
