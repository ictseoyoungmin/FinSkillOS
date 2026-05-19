"""Slice 12 — Trade Memory / Trade Journal view-model assembly.

Pure read-model for the Trade Memory page. Reads ``trades`` and the
``ReflectionService`` aggregates and composes a deterministic
``TradeMemoryViewModel`` the Streamlit page can render without any
service-layer access.

Outputs stay interpretation-first: process notes, mistake-tag
frequency, regime / sector / strategy buckets — no buy/sell wording.
``assert_trade_memory_view_model_is_safe`` re-uses the hardened
forbidden-wording regex at the UI seam.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models import Trade
from finskillos.db.repositories import AccountRepository
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.services.reflection_service import (
    MistakeFrequency,
    PerformanceBucket,
    ReflectionService,
    WeeklyReview,
)
from finskillos.services.trade_journal_service import TradeJournalService

UTC = timezone.utc

_RECENT_LIMIT = 20


# ---------------------------------------------------------------------------
# View-model dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TradeEntryVM:
    id: uuid.UUID
    trade_date: date
    ticker: str
    side: str
    strategy_type: str | None
    amount: Decimal | None
    market_regime: str | None
    emotion_state: str | None
    result_pnl: Decimal | None
    result_pnl_pct: Decimal | None
    r_multiple: Decimal | None
    mistake_tags: tuple[str, ...]
    catalyst: str | None
    sector: str | None
    theme: str | None
    notes: str | None
    thesis: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class TradeMemoryViewModel:
    generated_at: datetime
    today: date
    recent_entries: tuple[TradeEntryVM, ...]
    performance_by_regime: tuple[PerformanceBucket, ...]
    performance_by_sector_theme: tuple[PerformanceBucket, ...]
    performance_by_strategy: tuple[PerformanceBucket, ...]
    mistake_frequency: tuple[MistakeFrequency, ...]
    weekly_review: WeeklyReview
    setup_hint: str | None = None
    weekly_review_markdown: str = ""

    def has_entries(self) -> bool:
        return bool(self.recent_entries)


# Empty default so the page can render even with zero trades.
_EMPTY_WEEKLY_REVIEW = WeeklyReview(
    start_date=date(1970, 1, 1),
    end_date=date(1970, 1, 1),
    trade_count=0,
    total_pnl=Decimal("0.00"),
    win_rate=None,
    most_common_mistakes=(),
    best_regime=None,
    weakest_regime=None,
    process_notes=(),
)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_trade_memory_view_model(
    session: Session,
    *,
    today: date | None = None,
    account_name: str | None = None,
    generated_at: datetime | None = None,
    limit: int = _RECENT_LIMIT,
) -> TradeMemoryViewModel:
    now = generated_at or datetime.now(tz=UTC)
    today = today or now.astimezone(UTC).date()

    account_id = _resolve_account_id(session=session, account_name=account_name)
    if account_id is None:
        return TradeMemoryViewModel(
            generated_at=now,
            today=today,
            recent_entries=(),
            performance_by_regime=(),
            performance_by_sector_theme=(),
            performance_by_strategy=(),
            mistake_frequency=(),
            weekly_review=WeeklyReview(
                start_date=today,
                end_date=today,
                trade_count=0,
                total_pnl=Decimal("0.00"),
                win_rate=None,
                most_common_mistakes=(),
                best_regime=None,
                weakest_regime=None,
                process_notes=(),
            ),
            weekly_review_markdown="",
            setup_hint=(
                "기본 계좌가 없습니다. System Ops에서 샘플 계좌를 생성하면 "
                "Trade Memory가 활성화됩니다."
            ),
        )

    journal = TradeJournalService(session)
    reflection = ReflectionService(session)

    recent = journal.list_recent_entries(account_id=account_id, limit=limit)
    recent_vms = tuple(_to_entry_vm(trade) for trade in recent)
    by_regime = reflection.performance_by_regime(account_id=account_id)
    by_sector = reflection.performance_by_sector_theme(account_id=account_id)
    by_strategy = reflection.performance_by_strategy_type(account_id=account_id)
    mistakes = reflection.mistake_tag_frequency(account_id=account_id)
    weekly = reflection.weekly_review(today=today, account_id=account_id)

    setup_hint: str | None = None
    if not recent_vms:
        setup_hint = (
            "저장된 매매 기록이 없습니다. 'Add journal entry' 폼으로 첫 "
            "엔트리를 등록하면 Trade Memory 분석이 활성화됩니다. "
            "현재 Slice 12에서는 브로커리지 자동 수집을 지원하지 않습니다."
        )

    markdown = render_weekly_review_markdown(weekly)

    return TradeMemoryViewModel(
        generated_at=now,
        today=today,
        recent_entries=recent_vms,
        performance_by_regime=by_regime,
        performance_by_sector_theme=by_sector,
        performance_by_strategy=by_strategy,
        mistake_frequency=mistakes,
        weekly_review=weekly,
        setup_hint=setup_hint,
        weekly_review_markdown=markdown,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _to_entry_vm(trade: Trade) -> TradeEntryVM:
    tags = trade.mistake_tags or []
    if not isinstance(tags, list):
        tags = []
    if trade.mistake_tag and trade.mistake_tag not in tags:
        tags = [*tags, trade.mistake_tag]
    return TradeEntryVM(
        id=trade.id,
        trade_date=trade.trade_date,
        ticker=trade.ticker,
        side=trade.side,
        strategy_type=trade.strategy_type,
        amount=trade.amount,
        market_regime=trade.market_regime,
        emotion_state=trade.emotion_state,
        result_pnl=trade.result_pnl,
        result_pnl_pct=trade.result_pnl_pct,
        r_multiple=trade.r_multiple,
        mistake_tags=tuple(tag for tag in tags if isinstance(tag, str)),
        catalyst=trade.catalyst,
        sector=trade.sector,
        theme=trade.theme,
        notes=trade.notes,
        thesis=trade.thesis,
        reason=trade.reason,
    )


def _resolve_account_id(
    *, session: Session, account_name: str | None
) -> uuid.UUID | None:
    accounts = AccountRepository(session)
    if account_name is not None:
        account = accounts.get_by_name(account_name)
        return account.id if account is not None else None
    rows = accounts.list_all()
    return rows[0].id if rows else None


def render_weekly_review_markdown(review: WeeklyReview) -> str:
    """Render the weekly review as a copyable markdown block.

    The block is intentionally short and process-focused — no
    direct-trading instructions, no future predictions. Lists are
    bullet-formatted so the user can paste it straight into a journal.
    """

    win_rate = (
        f"{(review.win_rate * Decimal('100')).quantize(Decimal('0.1'))}%"
        if review.win_rate is not None
        else "—"
    )
    lines: list[str] = []
    lines.append(
        f"# Weekly Review · {review.start_date.isoformat()} – "
        f"{review.end_date.isoformat()}"
    )
    lines.append("")
    lines.append(f"- Trade count: {review.trade_count}")
    lines.append(f"- Total P&L: {review.total_pnl}")
    lines.append(f"- Win rate: {win_rate}")
    if review.most_common_mistakes:
        lines.append("")
        lines.append("## Most common mistakes")
        for mistake in review.most_common_mistakes[:5]:
            avg = (
                f"avg {mistake.avg_pnl}"
                if mistake.avg_pnl is not None
                else "no realised P&L"
            )
            lines.append(
                f"- {mistake.tag} — {mistake.count} entries, "
                f"{mistake.losing_trade_count} losing · {avg}"
            )
    if review.best_regime is not None:
        lines.append("")
        lines.append(
            f"## Best regime: {review.best_regime.key} "
            f"(total {review.best_regime.total_pnl})"
        )
    if review.weakest_regime is not None and (
        review.best_regime is None
        or review.weakest_regime.key != review.best_regime.key
    ):
        lines.append(
            f"## Weakest regime: {review.weakest_regime.key} "
            f"(total {review.weakest_regime.total_pnl})"
        )
    if review.process_notes:
        lines.append("")
        lines.append("## Process notes")
        for note in review.process_notes:
            lines.append(f"- {note}")
    return "\n".join(lines).strip() + "\n"


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def assert_trade_memory_view_model_is_safe(
    vm: TradeMemoryViewModel,
) -> None:
    """Reject direct-advice wording at the UI seam."""

    if vm.setup_hint:
        _scan_text(vm.setup_hint, source="setup_hint")
    for entry in vm.recent_entries:
        if entry.reason:
            _scan_text(entry.reason, source=f"entry[{entry.id}].reason")
        if entry.thesis:
            _scan_text(entry.thesis, source=f"entry[{entry.id}].thesis")
        if entry.catalyst:
            _scan_text(entry.catalyst, source=f"entry[{entry.id}].catalyst")
        if entry.notes:
            _scan_text(entry.notes, source=f"entry[{entry.id}].notes")
        if entry.emotion_state:
            _scan_text(
                entry.emotion_state,
                source=f"entry[{entry.id}].emotion_state",
            )
        for tag in entry.mistake_tags:
            _scan_text(tag, source=f"entry[{entry.id}].mistake_tag")
    for note in vm.weekly_review.process_notes:
        _scan_text(note, source="weekly_review.process_notes")
    _scan_text(vm.weekly_review_markdown, source="weekly_review.markdown")


def _scan_text(text: str, *, source: str) -> None:
    placeholder = GuardResult(
        guard_name=f"TRADE_MEMORY:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)


# ---------------------------------------------------------------------------
# Module re-exports
# ---------------------------------------------------------------------------


__all__ = [
    "TradeEntryVM",
    "TradeMemoryViewModel",
    "assert_trade_memory_view_model_is_safe",
    "build_trade_memory_view_model",
    "render_weekly_review_markdown",
]


# Touch the otherwise-unused empty-week scaffold so it stays bound for
# debug introspection and ruff does not flag it.
_ = _EMPTY_WEEKLY_REVIEW
