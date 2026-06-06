"""Agent read-context — v3 Phase 11 (read-scope expansion).

Assembles a compact, **descriptive** snapshot of the user's current account state
so the chat agent can answer grounded questions ("what's my biggest position?",
"what regime are we in?", "which guards are active?") instead of guessing. This
is read-only and factual — no advice, no predictions. Every read is defensive: a
missing piece is simply omitted, never an error.
"""

from __future__ import annotations

from collections import Counter

from finskillos.config import get_settings

__all__ = ["build_state_context"]


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
