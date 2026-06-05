"""Weekly Evidence Report builder — Slice 168 (Phase 4 capstone).

Assembles one descriptive markdown report from the live read models: market
regime, portfolio state, upcoming catalysts, and the weekly trade-process
review. Pure aggregation of existing services — process review only, never a
return forecast or trade directive. The assembled text is re-scanned with the
Slice-06 forbidden-wording guard before it leaves the seam.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.repositories import AccountRepository, MarketRegimeRepository
from finskillos.guards.base import (
    DEFAULT_SINGLE_POSITION_LIMIT_KRW,
    GuardResult,
    assert_no_forbidden_wording,
)
from finskillos.services.portfolio_service import PortfolioService
from finskillos.services.reflection_service import ReflectionService
from finskillos.ui.view_models.event_radar_vm import build_event_radar_view_model
from finskillos.ui.view_models.trade_memory_vm import render_weekly_review_markdown

__all__ = [
    "build_weekly_evidence_markdown",
    "build_daily_brief_markdown",
    "build_report_markdown",
]


def build_weekly_evidence_markdown(session: Session, *, today: date) -> str:
    """Render the weekly evidence report markdown for the default account."""

    account = _resolve_account(session)
    if account is None:
        return _no_account_report("Weekly Evidence Report")

    sections = [
        _regime_section(session),
        _portfolio_section(session, account.id),
        _catalyst_section(session, today=today),
        _trade_review_section(session, today=today, account_id=account.id),
    ]
    body = "\n\n".join(sections)
    markdown = (
        f"# Weekly Evidence Report\n"
        f"_Week ending {today.isoformat()} · descriptive evidence summary_\n\n"
        f"{body}\n\n---\n"
        "_Process review only — not a return forecast or trade directive._\n"
    )
    _assert_safe(markdown)
    return markdown


def build_daily_brief_markdown(session: Session, *, today: date) -> str:
    """Render the shorter daily brief (regime + portfolio + catalysts) — Slice 174.

    Same descriptive sections as the weekly report minus the trade-process
    review; intended for a daily cadence."""

    account = _resolve_account(session)
    if account is None:
        return _no_account_report("Daily Brief")

    sections = [
        _regime_section(session),
        _portfolio_section(session, account.id),
        _catalyst_section(session, today=today),
    ]
    body = "\n\n".join(sections)
    markdown = (
        f"# Daily Brief\n"
        f"_{today.isoformat()} · descriptive evidence summary_\n\n"
        f"{body}\n\n---\n"
        "_Descriptive evidence only — not a return forecast or trade directive._\n"
    )
    _assert_safe(markdown)
    return markdown


def build_report_markdown(session: Session, *, period: str, today: date) -> str:
    """Dispatch to the daily / weekly builder by ``period`` (Slice 174)."""
    if period == "weekly":
        return build_weekly_evidence_markdown(session, today=today)
    if period == "daily":
        return build_daily_brief_markdown(session, today=today)
    raise ValueError(f"unknown report period {period!r} (expected daily|weekly)")


def _no_account_report(title: str) -> str:
    return (
        f"# {title}\n\n"
        "No account baseline is stored yet. Seed a sample account or import a "
        "portfolio to populate this report.\n"
    )


def _resolve_account(session: Session):
    rows = AccountRepository(session).list_all()
    return rows[0] if rows else None


def _regime_section(session: Session) -> str:
    latest = MarketRegimeRepository(session).latest()
    if latest is None:
        return "## Market Regime\n- No stored regime snapshot yet."
    lines = [
        "## Market Regime",
        f"- **{latest.regime}** · confidence {_num(latest.confidence)}/100 · "
        f"risk {latest.risk_level}",
    ]
    positive = list(latest.positive_factors or ())
    risk = list(latest.risk_factors or ())
    if positive:
        lines.append(f"- Supporting: {positive[0]}")
    if risk:
        lines.append(f"- Watch: {risk[0]}")
    return "\n".join(lines)


def _portfolio_section(session: Session, account_id) -> str:
    summary = PortfolioService(session).get_portfolio_summary(account_id)
    cash_pct = (
        (summary.cash_value / summary.total_value * Decimal("100")).quantize(
            Decimal("0.1")
        )
        if summary.total_value > 0
        else Decimal("0")
    )
    largest_pct = (summary.largest_position_weight * Decimal("100")).quantize(
        Decimal("0.1")
    )
    lines = [
        "## Portfolio",
        f"- Total {_num(summary.total_value)} KRW · cash {_num(summary.cash_value)} "
        f"KRW ({cash_pct}%)",
        f"- {summary.position_count} position(s)"
        + (
            f" · largest {summary.largest_position_ticker} ({largest_pct}%)"
            if summary.largest_position_ticker
            else ""
        ),
    ]
    if summary.over_single_limit_tickers:
        lines.append(
            "- Over the "
            f"{_num(DEFAULT_SINGLE_POSITION_LIMIT_KRW)} KRW single-position limit: "
            + ", ".join(summary.over_single_limit_tickers)
        )
    else:
        lines.append("- No position over the single-position limit.")
    return "\n".join(lines)


def _catalyst_section(session: Session, *, today: date) -> str:
    vm = build_event_radar_view_model(session, today=today)
    lines = [
        "## Upcoming Catalysts",
        f"- {len(vm.high_risk)} high-risk · {len(vm.holdings_linked)} touch "
        "current holdings",
    ]
    for event in vm.high_risk[:3]:
        proximity = (
            f"in {event.days_to_event}d"
            if event.days_to_event is not None
            else "date TBD"
        )
        lines.append(
            f"- {event.title} ({proximity}, score {_num(event.event_risk_score)})"
        )
    if not vm.high_risk:
        lines.append("- No high-risk events in the current window.")
    return "\n".join(lines)


def _trade_review_section(session: Session, *, today: date, account_id) -> str:
    weekly = ReflectionService(session).weekly_review(
        today=today, account_id=account_id
    )
    return "## Trade Process Review\n\n" + render_weekly_review_markdown(weekly)


def _assert_safe(markdown: str) -> None:
    assert_no_forbidden_wording(
        GuardResult(
            guard_name="WEEKLY_EVIDENCE_REPORT",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=markdown,
        )
    )


def _num(value: Decimal) -> str:
    normalised = value.normalize()
    if normalised == normalised.to_integral_value():
        return f"{normalised.to_integral_value():,}"
    return f"{normalised:,}"
