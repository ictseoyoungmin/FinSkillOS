"""ReflectionService — Slice 12 deterministic trade-journal analytics.

Reads the ``trades`` table and returns aggregated buckets the Trade
Memory page renders. All output is purely descriptive: performance
buckets, mistake-tag frequency, and a weekly review. The service does
NOT emit buy/sell directives — the view-model safety scan re-checks
the strings to keep the page interpretation-first.

Slice 12 v0 deliberately keeps every aggregation deterministic and
LLM-free so a fixture set produces the same numbers every run.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Trade
from finskillos.db.repositories import AccountRepository, TradeRepository

# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerformanceBucket:
    key: str
    trade_count: int
    total_pnl: Decimal
    avg_pnl: Decimal
    avg_r_multiple: Decimal | None
    win_rate: Decimal | None


@dataclass(frozen=True)
class MistakeFrequency:
    tag: str
    count: int
    losing_trade_count: int
    avg_pnl: Decimal | None


@dataclass(frozen=True)
class WeeklyReview:
    start_date: date
    end_date: date
    trade_count: int
    total_pnl: Decimal
    win_rate: Decimal | None
    most_common_mistakes: tuple[MistakeFrequency, ...]
    best_regime: PerformanceBucket | None
    weakest_regime: PerformanceBucket | None
    process_notes: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ReflectionService:
    """Stateless analytics over the trade journal."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.trades = TradeRepository(session)
        self.accounts = AccountRepository(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def performance_by_regime(
        self,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> tuple[PerformanceBucket, ...]:
        return _bucket_by(
            self._load_trades(account_id=account_id, account_name=account_name),
            key_fn=lambda t: t.market_regime,
        )

    def performance_by_sector_theme(
        self,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> tuple[PerformanceBucket, ...]:
        return _bucket_by(
            self._load_trades(account_id=account_id, account_name=account_name),
            key_fn=_sector_theme_key,
        )

    def performance_by_strategy_type(
        self,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> tuple[PerformanceBucket, ...]:
        return _bucket_by(
            self._load_trades(account_id=account_id, account_name=account_name),
            key_fn=lambda t: t.strategy_type,
        )

    def mistake_tag_frequency(
        self,
        *,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> tuple[MistakeFrequency, ...]:
        rows = self._load_trades(
            account_id=account_id, account_name=account_name
        )
        return _aggregate_mistake_tags(rows)

    def weekly_review(
        self,
        *,
        today: date,
        account_id: uuid.UUID | None = None,
        account_name: str | None = None,
    ) -> WeeklyReview:
        start = today - timedelta(days=6)
        rows = self._load_trades(
            account_id=account_id, account_name=account_name
        )
        weekly_rows = [t for t in rows if start <= t.trade_date <= today]
        trade_count = len(weekly_rows)
        total_pnl = sum(
            (_pnl_or_zero(t) for t in weekly_rows), Decimal("0")
        ).quantize(Decimal("0.01"))
        win_rate = _win_rate(weekly_rows)
        mistakes = _aggregate_mistake_tags(weekly_rows)
        regime_buckets = _bucket_by(
            weekly_rows, key_fn=lambda t: t.market_regime
        )
        best = (
            max(regime_buckets, key=lambda b: b.total_pnl)
            if regime_buckets
            else None
        )
        weakest = (
            min(regime_buckets, key=lambda b: b.total_pnl)
            if regime_buckets
            else None
        )
        notes = _build_process_notes(
            trade_count=trade_count,
            win_rate=win_rate,
            most_common=mistakes,
            best=best,
            weakest=weakest,
        )
        return WeeklyReview(
            start_date=start,
            end_date=today,
            trade_count=trade_count,
            total_pnl=total_pnl,
            win_rate=win_rate,
            most_common_mistakes=mistakes,
            best_regime=best,
            weakest_regime=weakest,
            process_notes=notes,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_trades(
        self,
        *,
        account_id: uuid.UUID | None,
        account_name: str | None,
    ) -> list[Trade]:
        resolved = self._resolve_account_id(
            account_id=account_id, account_name=account_name
        )
        if resolved is None:
            return []
        return self.trades.list_for_account(resolved)

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


# ---------------------------------------------------------------------------
# Module-level helpers (pure)
# ---------------------------------------------------------------------------


def _pnl_or_zero(trade: Trade) -> Decimal:
    return trade.result_pnl if trade.result_pnl is not None else Decimal("0")


def _bucket_by(
    trades: Iterable[Trade],
    *,
    key_fn,
) -> tuple[PerformanceBucket, ...]:
    grouped: dict[str, list[Trade]] = {}
    for trade in trades:
        key = key_fn(trade)
        if key is None:
            continue
        grouped.setdefault(key, []).append(trade)
    buckets: list[PerformanceBucket] = []
    for key, rows in sorted(grouped.items()):
        total = sum((_pnl_or_zero(t) for t in rows), Decimal("0"))
        count = len(rows)
        avg = (total / count).quantize(Decimal("0.01")) if count else Decimal("0")
        r_values = [t.r_multiple for t in rows if t.r_multiple is not None]
        if r_values:
            avg_r = (sum(r_values, Decimal("0")) / len(r_values)).quantize(
                Decimal("0.0001")
            )
        else:
            avg_r = None
        buckets.append(
            PerformanceBucket(
                key=key,
                trade_count=count,
                total_pnl=total.quantize(Decimal("0.01")),
                avg_pnl=avg,
                avg_r_multiple=avg_r,
                win_rate=_win_rate(rows),
            )
        )
    return tuple(buckets)


def _sector_theme_key(trade: Trade) -> str | None:
    if trade.sector and trade.theme:
        return f"{trade.sector} / {trade.theme}"
    return trade.sector or trade.theme


def _win_rate(trades: Iterable[Trade]) -> Decimal | None:
    rows = [t for t in trades if t.result_pnl is not None]
    if not rows:
        return None
    wins = sum(1 for t in rows if t.result_pnl > 0)
    return (Decimal(wins) / Decimal(len(rows))).quantize(Decimal("0.0001"))


def _aggregate_mistake_tags(
    trades: Iterable[Trade],
) -> tuple[MistakeFrequency, ...]:
    grouped: dict[str, list[Trade]] = {}
    for trade in trades:
        for tag in _trade_mistake_tags(trade):
            grouped.setdefault(tag, []).append(trade)
    result: list[MistakeFrequency] = []
    for tag, rows in grouped.items():
        losing = sum(
            1 for t in rows if t.result_pnl is not None and t.result_pnl < 0
        )
        pnl_rows = [t.result_pnl for t in rows if t.result_pnl is not None]
        avg = (
            (sum(pnl_rows, Decimal("0")) / len(pnl_rows)).quantize(Decimal("0.01"))
            if pnl_rows
            else None
        )
        result.append(
            MistakeFrequency(
                tag=tag,
                count=len(rows),
                losing_trade_count=losing,
                avg_pnl=avg,
            )
        )
    result.sort(key=lambda r: (-r.count, r.tag))
    return tuple(result)


def _trade_mistake_tags(trade: Trade) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    listing = trade.mistake_tags or []
    if isinstance(listing, list):
        for tag in listing:
            if isinstance(tag, str) and tag.strip() and tag not in seen:
                tags.append(tag)
                seen.add(tag)
    if trade.mistake_tag and trade.mistake_tag not in seen:
        tags.append(trade.mistake_tag)
    return tags


def _build_process_notes(
    *,
    trade_count: int,
    win_rate: Decimal | None,
    most_common: tuple[MistakeFrequency, ...],
    best: PerformanceBucket | None,
    weakest: PerformanceBucket | None,
) -> tuple[str, ...]:
    notes: list[str] = []
    if trade_count == 0:
        notes.append("No trades recorded this week — schedule a review session.")
        return tuple(notes)

    if most_common:
        top = most_common[0]
        notes.append(
            f"Most frequent mistake tag this week: {top.tag} "
            f"({top.count} entries, {top.losing_trade_count} losing)."
        )
    else:
        notes.append("No mistake tags recorded this week.")

    if best is not None and best.trade_count >= 1:
        notes.append(
            f"Best regime by P&L: {best.key} "
            f"(total {best.total_pnl} across {best.trade_count} entries)."
        )
    if weakest is not None and weakest.trade_count >= 1 and (
        best is None or weakest.key != best.key
    ):
        notes.append(
            f"Weakest regime by P&L: {weakest.key} "
            f"(total {weakest.total_pnl})."
        )

    if win_rate is not None:
        notes.append(
            f"Realised win rate this week: "
            f"{(win_rate * Decimal('100')).quantize(Decimal('0.1'))}%."
        )

    notes.append(
        "Review process quality, not just P&L — revisit thesis and "
        "mistake tags before adding new risk."
    )
    return tuple(notes)


__all__ = [
    "MistakeFrequency",
    "PerformanceBucket",
    "ReflectionService",
    "WeeklyReview",
]
