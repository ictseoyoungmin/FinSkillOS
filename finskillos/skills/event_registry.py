"""EVENT-domain skill registry (Phase 20.4)."""

from __future__ import annotations

from decimal import Decimal

from finskillos.skills.base import SkillContext
from finskillos.skills.library.event_score_skill import EVENT_SCORE_SKILL
from finskillos.skills.runner import SkillRegistry


def build_event_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(EVENT_SCORE_SKILL)
    return registry


def context_from_event_score(
    event_risk_score: Decimal | None,
    *,
    days_to_event: int | None = None,
    portfolio_exposure: Decimal | None = None,
    affected_tickers: tuple[str, ...] = (),
) -> SkillContext:
    """Snapshot for EVENT.SCORE — the service supplies the assembled score."""

    return SkillContext(
        values={
            "event_risk_score": event_risk_score,
            "days_to_event": days_to_event,
            "portfolio_exposure": portfolio_exposure,
            "affected_tickers": list(affected_tickers),
        }
    )
