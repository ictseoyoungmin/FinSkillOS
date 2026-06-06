"""Agent read-context — v3 Phase 11 (read-scope expansion).

Assembles a compact, **descriptive** snapshot of the user's current account state
so the chat agent can answer grounded questions ("what's my biggest position?",
"what regime are we in?", "which guards are active?") instead of guessing. This
is read-only and factual — no advice, no predictions. Every read is defensive: a
missing piece is simply omitted, never an error.
"""

from __future__ import annotations

import re
from collections import Counter

from finskillos.config import get_settings

__all__ = ["build_state_context", "build_query_context"]


def _account(session):
    from finskillos.db.repositories import AccountRepository

    settings = get_settings()
    return AccountRepository(session).get_by_name(settings.default_account_name)


def build_state_context(session) -> str:
    """Return a short descriptive state summary, or "" when nothing is readable."""

    if session is None:
        return ""

    try:
        from finskillos.db.repositories import AccountRepository

        settings = get_settings()
        account = AccountRepository(session).get_by_name(
            settings.default_account_name
        )
    except Exception:  # noqa: BLE001 - no DB / no account → no context
        return ""
    if account is None:
        return ""

    lines: list[str] = []

    # Portfolio summary.
    try:
        from finskillos.services.portfolio_service import PortfolioService

        summary = PortfolioService(session).get_portfolio_summary(account.id)
        largest = ""
        if summary.largest_position_ticker:
            weight_pct = float(summary.largest_position_weight) * 100
            largest = (
                f", largest {summary.largest_position_ticker} "
                f"({weight_pct:.1f}%)"
            )
        lines.append(
            f"Portfolio: total {summary.total_value}, cash {summary.cash_value}, "
            f"{summary.position_count} positions{largest}."
        )
    except Exception:  # noqa: BLE001
        pass

    # Latest market regime (+ its descriptive interpretation).
    try:
        from finskillos.services.regime_service import RegimeService

        regime = RegimeService(session).get_latest_regime()
        if regime is not None:
            regime_line = (
                f"Market regime: {regime.regime} (mode {regime.decision_mode}, "
                f"risk {regime.risk_level})."
            )
            if regime.what_it_means:
                regime_line += f" {regime.what_it_means.strip()}"
            lines.append(regime_line)
    except Exception:  # noqa: BLE001
        pass

    # Risk guard ladder — per-guard status + reason, so the agent can explain
    # *why* each guard is in its state (descriptive, no advice).
    try:
        from finskillos.services.risk_guard_service import RiskGuardService

        report = RiskGuardService(session).evaluate(account.id)
        counts = Counter(result.status for result in report.results)
        breakdown = ", ".join(f"{n} {status}" for status, n in counts.items())
        lines.append(
            f"Risk guards ({breakdown}; overall {report.overall_status}):"
        )
        for result in report.results:
            reason = (result.message or result.title or "").strip()
            lines.append(
                f"  · [{result.status}] {result.title}"
                + (f" — {reason}" if reason and reason != result.title else "")
            )
    except Exception:  # noqa: BLE001
        pass

    # Watch folders + tracked tickers.
    try:
        from finskillos.db.repositories import SymbolSubscriptionFolderRepository

        folders = SymbolSubscriptionFolderRepository(session).list_snapshots()
        ticker_count = len({m.ticker for f in folders for m in f.members})
        lines.append(
            f"Watchlist: {len(folders)} folders, {ticker_count} tickers tracked."
        )
    except Exception:  # noqa: BLE001
        pass

    # Trade journal size.
    try:
        from finskillos.db.repositories import TradeRepository

        recent = TradeRepository(session).list_recent(account.id, limit=1)
        if recent:
            lines.append(
                f"Trade journal: latest entry {recent[0].trade_date.isoformat()}."
            )
    except Exception:  # noqa: BLE001
        pass

    if not lines:
        return ""
    body = "\n".join(f"- {line}" for line in lines)
    return (
        "Current account state (descriptive, read-only — use it to answer "
        "questions accurately; never turn it into advice):\n" + body
    )


_EVENT_Q = re.compile(r"event|이벤트|카탈리스트|catalyst|일정", re.IGNORECASE)
_NEWS_Q = re.compile(r"news|뉴스|기사|헤드라인|headline", re.IGNORECASE)
_TRADE_Q = re.compile(r"trade|거래|매매|journal|저널|내역|체결", re.IGNORECASE)


def build_query_context(session, question: str) -> str:
    """Question-aware read: fetch the specific read models the question is about
    (events / news / recent trades) and return a descriptive block for this turn.
    Empty when the question matches none or nothing is stored. Read-only."""

    if session is None or not (question or "").strip():
        return ""

    try:
        account = _account(session)
    except Exception:  # noqa: BLE001
        account = None

    sections: list[str] = []

    if _EVENT_Q.search(question):
        try:
            from datetime import date

            from finskillos.services.event_service import EventService

            events = EventService(session).list_upcoming(today=date.today(), limit=5)
            if events:
                items = "; ".join(
                    f"{e.title} ({e.start_date.isoformat()})" for e in events
                )
                sections.append(f"Upcoming events: {items}.")
        except Exception:  # noqa: BLE001
            pass

    if _NEWS_Q.search(question) and account is not None:
        try:
            from finskillos.services.news_service import NewsService

            rows = NewsService(session).list_holdings_relevant_articles(
                account_id=account.id, limit=5
            )
            if rows:
                items = "; ".join(
                    f"{article.title} ({article.source}, {article.sentiment_label})"
                    for article, _ in rows
                )
                sections.append(f"Recent holdings-relevant news: {items}.")
        except Exception:  # noqa: BLE001
            pass

    if _TRADE_Q.search(question) and account is not None:
        try:
            from finskillos.db.repositories import TradeRepository

            trades = TradeRepository(session).list_recent(account.id, limit=5)
            if trades:
                items = "; ".join(
                    f"{t.trade_date.isoformat()} {t.ticker} {t.side}"
                    + (f" pnl {t.result_pnl}" if t.result_pnl is not None else "")
                    for t in trades
                )
                sections.append(f"Recent trades: {items}.")
        except Exception:  # noqa: BLE001
            pass

    if not sections:
        return ""
    return "Relevant data for this question (descriptive, read-only):\n" + "\n".join(
        f"- {section}" for section in sections
    )
