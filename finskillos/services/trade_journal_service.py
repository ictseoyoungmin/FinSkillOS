"""TradeJournalService — Slice 12 application layer for Trade Memory.

Reflection-first wrapper over ``TradeRepository``:

* Normalises ticker / mistake_tags / sector / theme / event_key.
* Defaults market_regime to the latest persisted ``MarketRegime`` when
  the caller omits it (.devmd/12 §4).
* Optionally derives sector / theme from a current open position so
  reflection buckets stay populated for swing trades.
* Refuses to expose direct-execution wording from the journal seam —
  ``DIRECT_ADVICE_PATTERNS`` from Slice 06 catches anything that
  leaks through.

Side vocabulary: ``LONG / SHORT / WATCH / EXIT_REVIEW / OTHER`` (.devmd/12).
The legacy Slice-02 ``BUY`` / ``SELL`` values still load from the DB
unchanged so existing trades remain searchable; ``BUY`` / ``SELL`` are
ALSO accepted as input but the UI page must not surface them as
execution triggers.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Trade
from finskillos.db.repositories import (
    AccountRepository,
    MarketRegimeRepository,
    PositionRepository,
    TradeRepository,
)

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

SIDE_LONG = "LONG"
SIDE_SHORT = "SHORT"
SIDE_WATCH = "WATCH"
SIDE_EXIT_REVIEW = "EXIT_REVIEW"
SIDE_OTHER = "OTHER"

SLICE_12_SIDES: tuple[str, ...] = (
    SIDE_LONG,
    SIDE_SHORT,
    SIDE_WATCH,
    SIDE_EXIT_REVIEW,
    SIDE_OTHER,
)

# Legacy values kept loadable for Slice-02 / 06 compatibility.
LEGACY_SIDES: tuple[str, ...] = ("BUY", "SELL")

ALL_ALLOWED_SIDES: tuple[str, ...] = SLICE_12_SIDES + LEGACY_SIDES

DEFAULT_MISTAKE_TAGS: tuple[str, ...] = (
    "Chasing",
    "No Stop",
    "Oversized",
    "Wrong Thesis",
    "Overtrading",
    "Revenge Trade",
    "Early Entry",
    "Late Exit",
    "Ignored Regime",
    "Event FOMO",
)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TradeJournalInput:
    trade_date: date
    ticker: str
    side: str
    strategy_type: str | None = None
    amount: Decimal | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    fees: Decimal | None = None
    reason: str | None = None
    thesis: str | None = None
    catalyst: str | None = None
    market_regime: str | None = None
    emotion_state: str | None = None
    result_pnl: Decimal | None = None
    result_pnl_pct: Decimal | None = None
    r_multiple: Decimal | None = None
    mistake_tags: tuple[str, ...] = ()
    notes: str | None = None
    sector: str | None = None
    theme: str | None = None
    event_key: str | None = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TradeJournalService:
    """Application-layer facade for Trade Memory."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.trades = TradeRepository(session)
        self.accounts = AccountRepository(session)
        self.regime_repo = MarketRegimeRepository(session)
        self.positions = PositionRepository(session)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create_entry(
        self,
        entry: TradeJournalInput,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> Trade:
        account_id = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        if account_id is None:
            raise LookupError(
                "No account is configured. Run sample-account seed in System Ops first."
            )

        ticker = _normalize_ticker(entry.ticker)
        if not ticker:
            raise ValueError("ticker is required")
        side = _validate_side(entry.side)
        regime = entry.market_regime or self._capture_latest_regime()
        sector, theme = self._derive_sector_theme(
            account_id=account_id,
            ticker=ticker,
            sector=entry.sector,
            theme=entry.theme,
        )
        mistake_tags = _normalize_mistake_tags(entry.mistake_tags)

        return self.trades.create(
            account_id=account_id,
            ticker=ticker,
            trade_date=entry.trade_date,
            side=side,
            quantity=entry.quantity or Decimal("0"),
            price=entry.price or Decimal("0"),
            amount=entry.amount or Decimal("0"),
            strategy_type=entry.strategy_type or "swing",
            fees=entry.fees,
            reason=entry.reason,
            thesis=entry.thesis,
            catalyst=entry.catalyst,
            emotion_state=entry.emotion_state,
            market_regime=regime,
            mistake_tags=mistake_tags,
            result_pnl=entry.result_pnl,
            result_pnl_pct=entry.result_pnl_pct,
            r_multiple=entry.r_multiple,
            notes=entry.notes,
            sector=sector,
            theme=theme,
            event_key=entry.event_key,
        )

    def update_entry(
        self,
        trade_id: uuid.UUID,
        entry: TradeJournalInput,
    ) -> Trade:
        side = _validate_side(entry.side)
        mistake_tags = _normalize_mistake_tags(entry.mistake_tags)
        return self.trades.update(
            trade_id,
            ticker=entry.ticker,
            trade_date=entry.trade_date,
            side=side,
            quantity=entry.quantity,
            price=entry.price,
            amount=entry.amount,
            strategy_type=entry.strategy_type,
            fees=entry.fees,
            reason=entry.reason,
            thesis=entry.thesis,
            catalyst=entry.catalyst,
            emotion_state=entry.emotion_state,
            market_regime=entry.market_regime,
            mistake_tags=mistake_tags,
            result_pnl=entry.result_pnl,
            result_pnl_pct=entry.result_pnl_pct,
            r_multiple=entry.r_multiple,
            notes=entry.notes,
            sector=entry.sector,
            theme=entry.theme,
            event_key=entry.event_key,
        )

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def list_recent_entries(
        self,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
        limit: int = 20,
    ) -> list[Trade]:
        account_id = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        if account_id is None:
            return []
        return self.trades.list_recent(account_id, limit=limit)

    def list_by_mistake_tag(
        self,
        tag: str,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> list[Trade]:
        account_id = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        if account_id is None:
            return []
        return self.trades.list_by_mistake_tag(account_id, tag)

    def list_by_regime(
        self,
        regime: str,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> list[Trade]:
        account_id = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        if account_id is None:
            return []
        return self.trades.list_by_regime(account_id, regime)

    def list_by_strategy_type(
        self,
        strategy_type: str,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> list[Trade]:
        account_id = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        if account_id is None:
            return []
        return self.trades.list_by_strategy_type(account_id, strategy_type)

    # ------------------------------------------------------------------
    # Helpers
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

    def _capture_latest_regime(self) -> str | None:
        latest = self.regime_repo.latest()
        return latest.regime if latest is not None else None

    def _derive_sector_theme(
        self,
        *,
        account_id: uuid.UUID,
        ticker: str,
        sector: str | None,
        theme: str | None,
    ) -> tuple[str | None, str | None]:
        if sector is not None and theme is not None:
            return sector, theme
        position = self.positions.get_by_account_and_ticker(account_id, ticker)
        if position is None:
            return sector, theme
        return (sector or position.sector, theme or position.theme)


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------


def _validate_side(side: str | None) -> str:
    if side is None:
        raise ValueError("side is required")
    cleaned = side.strip().upper().replace(" ", "_")
    if cleaned not in ALL_ALLOWED_SIDES:
        raise ValueError(
            f"unknown side {side!r}; expected one of {ALL_ALLOWED_SIDES}"
        )
    return cleaned


def _normalize_ticker(ticker: str | None) -> str | None:
    if ticker is None:
        return None
    cleaned = ticker.strip()
    return cleaned.upper() if cleaned else None


def _normalize_mistake_tags(
    tags: Iterable[str] | None,
) -> tuple[str, ...]:
    """Trim / drop empties / dedupe while preserving order.

    Display casing from ``DEFAULT_MISTAKE_TAGS`` is preserved when an
    input matches case-insensitively (so ``"chasing"`` becomes
    ``"Chasing"``). Custom tags keep the caller's casing.
    """

    if not tags:
        return ()
    default_lookup = {tag.lower(): tag for tag in DEFAULT_MISTAKE_TAGS}
    seen: set[str] = set()
    cleaned: list[str] = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        stripped = tag.strip()
        if not stripped:
            continue
        canonical = default_lookup.get(stripped.lower(), stripped)
        if canonical.lower() in seen:
            continue
        seen.add(canonical.lower())
        cleaned.append(canonical)
    return tuple(cleaned)


# Re-exports for the UI layer.
__all__ = [
    "ALL_ALLOWED_SIDES",
    "DEFAULT_MISTAKE_TAGS",
    "LEGACY_SIDES",
    "SIDE_EXIT_REVIEW",
    "SIDE_LONG",
    "SIDE_OTHER",
    "SIDE_SHORT",
    "SIDE_WATCH",
    "SLICE_12_SIDES",
    "TradeJournalInput",
    "TradeJournalService",
]
