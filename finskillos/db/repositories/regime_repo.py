"""MarketRegimeRepository — append + read access for `market_regimes`.

History is append-only (one row per evaluation). Uniqueness is on
`(snapshot_time, rule_version)` so two evaluations from different rule
versions can coexist at the same point in time; same-version reruns
upsert in place so a developer can re-evaluate a fixture without
multiplying rows.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import MarketRegime
from finskillos.regime import RegimeOutput


class MarketRegimeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        snapshot_time: datetime,
        output: RegimeOutput,
    ) -> MarketRegime:
        existing = self._get(snapshot_time, output.rule_version)
        if existing is None:
            row = MarketRegime(
                snapshot_time=snapshot_time,
                regime=output.regime,
                confidence=output.confidence,
                decision_mode=output.decision_mode,
                risk_level=output.risk_level,
                summary=output.summary,
                what_happened=output.what_happened,
                what_it_means=output.what_it_means,
                watch_next=list(output.watch_next),
                evidence=_jsonable_evidence(output.evidence),
                positive_factors=list(output.positive_factors),
                risk_factors=list(output.risk_factors),
                rule_version=output.rule_version,
            )
            self.session.add(row)
            self.session.flush()
            return row

        existing.regime = output.regime
        existing.confidence = output.confidence
        existing.decision_mode = output.decision_mode
        existing.risk_level = output.risk_level
        existing.summary = output.summary
        existing.what_happened = output.what_happened
        existing.what_it_means = output.what_it_means
        existing.watch_next = list(output.watch_next)
        existing.evidence = _jsonable_evidence(output.evidence)
        existing.positive_factors = list(output.positive_factors)
        existing.risk_factors = list(output.risk_factors)
        self.session.flush()
        return existing

    def latest(self) -> MarketRegime | None:
        stmt = (
            select(MarketRegime)
            .order_by(MarketRegime.snapshot_time.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).one_or_none()

    def list_recent(self, *, limit: int = 30) -> list[MarketRegime]:
        stmt = (
            select(MarketRegime)
            .order_by(MarketRegime.snapshot_time.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def _get(
        self, snapshot_time: datetime, rule_version: str
    ) -> MarketRegime | None:
        stmt = select(MarketRegime).where(
            MarketRegime.snapshot_time == snapshot_time,
            MarketRegime.rule_version == rule_version,
        )
        return self.session.scalars(stmt).one_or_none()


def _jsonable_evidence(evidence: dict) -> dict:
    """Convert Decimal values to floats so JSON columns serialise cleanly.

    The engine emits Decimal scores; SQLAlchemy's JSON column on SQLite
    cannot encode Decimal directly. Floats give us deterministic round-
    tripping for the values we actually care about (scores, RSIs, VIX).
    """

    return {
        k: (float(v) if isinstance(v, Decimal) else v)
        for k, v in evidence.items()
    }
