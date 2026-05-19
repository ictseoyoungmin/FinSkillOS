"""EventRiskService — Slice 11 deterministic event risk scoring.

Pure read model. Given an ``Event`` row + its links it computes:

* ``portfolio_exposure``: per .devmd/11, the share of holdings that
  match the event's linked tickers (single-position weight from the
  latest PortfolioSnapshot when available, otherwise an indicator
  weight derived from the link/holding overlap).
* ``days_to_event_weight``: ladder by start_date - today.
* ``market_overheat_weight``: bumped under
  RISK_ON_OVERHEAT / DISTRIBUTION_RISK / DEFENSIVE_TRANSITION.
* ``event_risk_score``: clamped to 0–10, never described as a
  prediction.
* ``risk_label``: LOW / MODERATE / HIGH / CRITICAL.

This service does NOT mutate the DB. It does not emit buy/sell
directives — the view-model safety scan re-checks the strings to
keep the page interpretation-first.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Event
from finskillos.db.repositories import (
    AccountRepository,
    EventLinkRepository,
    MarketRegimeRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.regime.regime_rules import (
    REGIME_DEFENSIVE_TRANSITION,
    REGIME_DISTRIBUTION_RISK,
    REGIME_RISK_ON_OVERHEAT,
)

# --- Risk label ladder -----------------------------------------------------
RISK_LABEL_LOW = "LOW"
RISK_LABEL_MODERATE = "MODERATE"
RISK_LABEL_HIGH = "HIGH"
RISK_LABEL_CRITICAL = "CRITICAL"

_SCORE_FLOOR = Decimal("0")
_SCORE_CEILING = Decimal("10")

_OVERHEAT_BONUS = Decimal("1.3")
_DISTRIBUTION_BONUS = Decimal("1.2")
_DEFENSIVE_BONUS = Decimal("1.2")
_DEFAULT_REGIME_WEIGHT = Decimal("1.0")

_DAY_WINDOW_WEEK = 7
_DAY_WINDOW_MONTH = 30
_DAY_WINDOW_QUARTER = 90


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventRiskBreakdown:
    """Structured score breakdown for the view-model card."""

    event_id: uuid.UUID
    days_to_event: int | None
    importance_score: Decimal
    portfolio_exposure: Decimal
    days_to_event_weight: Decimal
    market_overheat_weight: Decimal
    portfolio_exposure_weight: Decimal
    event_risk_score: Decimal
    risk_label: str
    affected_tickers: tuple[str, ...] = field(default_factory=tuple)
    affected_sectors: tuple[str, ...] = field(default_factory=tuple)
    affected_themes: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class EventRiskService:
    """Deterministic event risk scorer + portfolio exposure mapper."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.links = EventLinkRepository(session)
        self.regime_repo = MarketRegimeRepository(session)
        self.portfolios = PortfolioRepository(session)
        self.positions = PositionRepository(session)
        self.accounts = AccountRepository(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(
        self,
        event: Event,
        *,
        today: date,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> EventRiskBreakdown:
        links = self.links.list_for_event(event.id)
        linked_tickers = tuple(
            sorted({link.ticker.upper() for link in links if link.ticker})
        )
        linked_sectors = tuple(
            sorted({link.sector for link in links if link.sector})
        )
        linked_themes = tuple(
            sorted({link.theme for link in links if link.theme})
        )

        days_to_event = _days_to_event(event, today=today)

        account_id = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        portfolio_exposure = self._compute_portfolio_exposure(
            account_id=account_id,
            linked_tickers=linked_tickers,
        )
        has_any_link = bool(
            linked_tickers or linked_sectors or linked_themes
        )
        portfolio_exposure_weight = self._portfolio_exposure_weight(
            has_any_link=has_any_link,
            portfolio_exposure=portfolio_exposure,
        )
        days_weight = _days_to_event_weight(days_to_event)
        market_weight = self._market_overheat_weight()

        raw = (
            event.importance_score
            * portfolio_exposure_weight
            * days_weight
            * market_weight
        )
        clamped = max(_SCORE_FLOOR, min(_SCORE_CEILING, raw))
        clamped = clamped.quantize(Decimal("0.01"))

        return EventRiskBreakdown(
            event_id=event.id,
            days_to_event=days_to_event,
            importance_score=event.importance_score,
            portfolio_exposure=portfolio_exposure.quantize(Decimal("0.0001")),
            days_to_event_weight=days_weight,
            market_overheat_weight=market_weight,
            portfolio_exposure_weight=portfolio_exposure_weight.quantize(
                Decimal("0.0001")
            ),
            event_risk_score=clamped,
            risk_label=risk_label_for_score(clamped),
            affected_tickers=linked_tickers,
            affected_sectors=linked_sectors,
            affected_themes=linked_themes,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_account_id(
        self,
        *,
        account_id: uuid.UUID | None,
        account_name: str | None,
    ) -> uuid.UUID | None:
        if account_id is not None:
            return account_id
        if account_name is not None:
            account = self.accounts.get_by_name(account_name)
            return account.id if account is not None else None
        rows = self.accounts.list_all()
        return rows[0].id if rows else None

    def _compute_portfolio_exposure(
        self,
        *,
        account_id: uuid.UUID | None,
        linked_tickers: Sequence[str],
    ) -> Decimal:
        if account_id is None or not linked_tickers:
            return Decimal("0")
        positions = self.positions.list_for_account(account_id)
        if not positions:
            return Decimal("0")
        matched = [
            p for p in positions if p.ticker.upper() in set(linked_tickers)
        ]
        if not matched:
            return Decimal("0")

        snapshot = self.portfolios.latest(account_id)
        total = snapshot.total_value if snapshot is not None else None
        if total is None or total <= 0:
            total = sum((p.market_value for p in positions), Decimal("0"))
        if total <= 0:
            return Decimal("0")
        matched_value = sum((p.market_value for p in matched), Decimal("0"))
        return matched_value / total

    def _portfolio_exposure_weight(
        self,
        *,
        has_any_link: bool,
        portfolio_exposure: Decimal,
    ) -> Decimal:
        """Map link status + portfolio overlap to a multiplier.

        Per .devmd/11 §6:
          0.0  if the event has no ticker / sector / theme link at all
          0.5  if linked (ticker / sector / theme) but no holding overlap
          1.0 + portfolio_weight  if the linked ticker is currently held

        Theme-only / sector-only events (FOMC / CPI / regulatory) still
        score because they describe market-level exposure even when no
        individual position is held.
        """

        if not has_any_link:
            return Decimal("0.0")
        if portfolio_exposure <= 0:
            return Decimal("0.5")
        return Decimal("1.0") + portfolio_exposure

    def _market_overheat_weight(self) -> Decimal:
        latest = self.regime_repo.latest()
        if latest is None:
            return _DEFAULT_REGIME_WEIGHT
        if latest.regime == REGIME_RISK_ON_OVERHEAT:
            return _OVERHEAT_BONUS
        if latest.regime == REGIME_DISTRIBUTION_RISK:
            return _DISTRIBUTION_BONUS
        if latest.regime == REGIME_DEFENSIVE_TRANSITION:
            return _DEFENSIVE_BONUS
        return _DEFAULT_REGIME_WEIGHT


# ---------------------------------------------------------------------------
# Pure helpers (also re-used by tests + view models)
# ---------------------------------------------------------------------------


def _days_to_event(event: Event, *, today: date) -> int | None:
    if event.start_date is None:
        return None
    delta = event.start_date - today
    return int(delta.days)


def _days_to_event_weight(days: int | None) -> Decimal:
    if days is None:
        return Decimal("1.0")
    if days <= _DAY_WINDOW_WEEK:
        return Decimal("1.5")
    if days <= _DAY_WINDOW_MONTH:
        return Decimal("1.2")
    if days <= _DAY_WINDOW_QUARTER:
        return Decimal("1.0")
    return Decimal("0.7")


def risk_label_for_score(score: Decimal) -> str:
    if score < Decimal("2.0"):
        return RISK_LABEL_LOW
    if score < Decimal("4.0"):
        return RISK_LABEL_MODERATE
    if score < Decimal("7.0"):
        return RISK_LABEL_HIGH
    return RISK_LABEL_CRITICAL
