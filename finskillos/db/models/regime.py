"""MarketRegime model — historical regime classifications (Slice 05).

One row per (snapshot_time, rule_version) representing a single
classification by the Regime Engine. `evidence`, `positive_factors`,
`risk_factors`, and `watch_next` keep the rule rationale alongside the
verdict so a future drilldown can answer "why was the market in
RISK_ON_OVERHEAT yesterday?" without recomputing.

JSON columns use the cross-dialect variant pattern from
`finskillos.db.models.alert` — JSONB on PostgreSQL, plain JSON on
SQLite (used by repo / engine tests).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base

JSONPayload = JSON().with_variant(JSONB(), "postgresql")


class MarketRegime(Base):
    __tablename__ = "market_regimes"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_time",
            "rule_version",
            name="uq_market_regimes_snapshot_rule",
        ),
        Index(
            "idx_market_regimes_snapshot",
            "snapshot_time",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid.uuid4
    )
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    regime: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    decision_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    what_happened: Mapped[str | None] = mapped_column(Text)
    what_it_means: Mapped[str | None] = mapped_column(Text)
    watch_next: Mapped[list | None] = mapped_column(JSONPayload)
    evidence: Mapped[dict | None] = mapped_column(JSONPayload)
    rule_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
