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
from datetime import datetime, timezone

from finskillos.config import get_settings

_RISK_WEIGHT = {"RED": 0.6, "ORANGE": 0.4, "YELLOW": 0.2}
_SENTIMENT_WEIGHT = {"NEGATIVE": 0.3, "MIXED": 0.2, "POSITIVE": 0.15}


def _news_importance(article, impacts) -> float:
    """Heuristic importance: classifier impact + risk + sentiment + recency.

    yfinance holdings news often has impact_score 0 (no keyword rule), so risk /
    sentiment (from signal inference) and recency carry most of the weight."""

    published = getattr(article, "published_at", None)
    recency = 0.0
    if published is not None:
        pub = published if published.tzinfo else published.replace(tzinfo=timezone.utc)
        age_days = max(0, (datetime.now(tz=timezone.utc) - pub).days)
        recency = max(0.0, 0.5 - 0.05 * age_days)
    impact = max((float(i.impact_score) for i in impacts), default=0.0)
    risk = max((_RISK_WEIGHT.get(i.risk_level, 0.0) for i in impacts), default=0.0)
    sentiment = max(
        (_SENTIMENT_WEIGHT.get(i.sentiment_label, 0.0) for i in impacts), default=0.0
    )
    return impact + risk + sentiment + recency

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
# Uppercase words that are not tickers (kept short; the data-exists check catches
# the rest). Avoids needless lookups on common acronyms.
_SYMBOL_STOP = {
    "RSI", "EMA", "PNL", "AND", "THE", "FOR", "USD", "KRW", "OK", "DB", "API",
    "FOMC", "CPI", "PPI", "ETF", "IPO", "CEO", "AI", "NEW", "ALL", "ANY",
}


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
                account_id=account.id, limit=30
            )
            if rows:
                ranked = sorted(
                    rows, key=lambda r: _news_importance(r[0], r[1]), reverse=True
                )[:5]
                lines = []
                for idx, (article, impacts) in enumerate(ranked, start=1):
                    ticker = next(
                        (i.ticker for i in impacts if i.ticker), "?"
                    )
                    risk = next(
                        (i.risk_level for i in impacts if i.risk_level != "UNKNOWN"),
                        "",
                    )
                    date = article.published_at.date().isoformat()
                    tag = f", {risk}" if risk else ""
                    lines.append(
                        f"{idx}. [{ticker}] {article.title} "
                        f"({article.source}, {date}{tag})"
                    )
                joined = " ".join(lines)
                sections.append(
                    "Holdings news, ranked by importance (top 5): "
                    f"{joined} (descriptive — not a buy/sell signal)."
                )
            else:
                sections.append(
                    "No holdings-relevant news is stored yet — it can be refreshed "
                    "with the refresh_holdings_news protocol."
                )
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

    # Per-symbol detail when the question names a ticker that has stored data
    # (the data-exists filter removes non-ticker uppercase words like RSI/FOMC).
    try:
        from finskillos.data_sources.dto import DEFAULT_TIMEFRAME
        from finskillos.db.repositories import IndicatorRepository, MarketRepository

        candidates = [
            t
            for t in dict.fromkeys(re.findall(r"\b[A-Z]{2,6}\b", question))
            if t not in _SYMBOL_STOP
        ]
        if candidates:
            indicators = IndicatorRepository(session)
            market = MarketRepository(session)
            for ticker in candidates[:3]:
                close = market.latest_close(ticker, DEFAULT_TIMEFRAME)
                snapshot = indicators.latest_for(ticker, DEFAULT_TIMEFRAME)
                if close is None and snapshot is None:
                    continue
                bits: list[str] = []
                if close is not None:
                    bits.append(f"close {close}")
                if snapshot is not None:
                    if snapshot.rsi_14 is not None:
                        bits.append(f"RSI {snapshot.rsi_14}")
                    if snapshot.trend_state:
                        bits.append(f"trend {snapshot.trend_state}")
                    if snapshot.momentum_score is not None:
                        bits.append(f"momentum {snapshot.momentum_score}")
                sections.append(
                    f"{ticker}: {', '.join(bits)} "
                    "(stored indicators, descriptive — not a signal)."
                )
    except Exception:  # noqa: BLE001
        pass

    if not sections:
        return ""
    return "Relevant data for this question (descriptive, read-only):\n" + "\n".join(
        f"- {section}" for section in sections
    )
