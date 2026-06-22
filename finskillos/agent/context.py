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
from dataclasses import dataclass
from datetime import datetime, timezone

from finskillos.config import get_settings

_RISK_WEIGHT = {"RED": 0.6, "ORANGE": 0.4, "YELLOW": 0.2}
_SENTIMENT_WEIGHT = {"NEGATIVE": 0.3, "MIXED": 0.2, "POSITIVE": 0.15}
_RECENCY_HALF_LIFE_DAYS = 3.0  # today ≈ 0.5, 3d ≈ 0.25, 6d ≈ 0.125
# Material catalysts — these move a stock far more than routine coverage.
_MATERIAL_KEYWORDS = re.compile(
    r"earnings|guidance|revenue|profit|miss(?:es|ed)?|beat|upgrade|downgrade|"
    r"lawsuit|sued|investigat|\bsec\b|\bfda\b|approv|recall|halt|bankrupt|default|"
    r"merger|acquir|acquisition|buyback|dividend|delist|fraud|probe|"
    r"실적|가이던스|인수|합병|감자|유상증자|무상증자|상장폐지|소송|배당|자사주",
    re.IGNORECASE,
)


def _news_importance(article, impacts) -> float:
    """Heuristic importance: classifier impact + risk + sentiment + materiality +
    recency (3-day half-life). yfinance holdings news often has impact_score 0 (no
    keyword rule), so risk / sentiment / materiality / recency carry the weight.

    The heuristic narrows to a shortlist; the LLM re-ranks it into the final answer
    (the system prompt asks it to summarise the most important items)."""

    published = getattr(article, "published_at", None)
    recency = 0.0
    if published is not None:
        pub = published if published.tzinfo else published.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (datetime.now(tz=timezone.utc) - pub).total_seconds() / 86400)
        recency = 0.5 * (0.5 ** (age_days / _RECENCY_HALF_LIFE_DAYS))
    impact = max((float(i.impact_score) for i in impacts), default=0.0)
    risk = max((_RISK_WEIGHT.get(i.risk_level, 0.0) for i in impacts), default=0.0)
    sentiment = max(
        (_SENTIMENT_WEIGHT.get(i.sentiment_label, 0.0) for i in impacts), default=0.0
    )
    title = getattr(article, "title", "") or ""
    materiality = 0.35 if _MATERIAL_KEYWORDS.search(title) else 0.0
    return impact + risk + sentiment + materiality + recency


def _dedupe_news(ranked):
    """Drop near-duplicate headlines (same first 6 words) — the same wire story is
    often linked to several holdings."""

    seen: set[str] = set()
    out = []
    for article, impacts in ranked:
        key = " ".join((getattr(article, "title", "") or "").lower().split()[:6])
        if key and key in seen:
            continue
        seen.add(key)
        out.append((article, impacts))
    return out

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
# "Which skill rule fired / why this risk verdict?" — the Applied Skill Rules audit.
_RULES_Q = re.compile(
    r"rule|skill|guard|firewall|규칙|스킬|가드|방화벽|발화", re.IGNORECASE
)
# "Simulate / backtest a quant strategy over the stored bars" — the Quant Lab.
_SIM_Q = re.compile(
    r"시뮬|simulat|백테스트|backtest|퀀트|quant|전략", re.IGNORECASE
)
# Uppercase words that are not tickers (kept short; the data-exists check catches
# the rest). Avoids needless lookups on common acronyms.
_SYMBOL_STOP = {
    "RSI", "EMA", "PNL", "AND", "THE", "FOR", "USD", "KRW", "OK", "DB", "API",
    "FOMC", "CPI", "PPI", "ETF", "IPO", "CEO", "AI", "NEW", "ALL", "ANY",
}


def _match_strategy_id_opt(question: str) -> str | None:
    """Map free text onto a built-in StrategySpec id, or None if nothing matches.

    The agent "designs" by selecting the hypothesis the user describes; an
    explicit id wins, otherwise Korean/English keywords route to the closest
    library spec."""

    from finskillos.simulation.library import STRATEGY_LIBRARY

    upper = question.upper()
    for spec in STRATEGY_LIBRARY:
        if spec.strategy_id in upper:
            return spec.strategy_id
    q = question.lower()
    if "골든" in question or "golden" in q or "데드" in question:
        return "SMA_GOLDEN_20_50"
    if "rsi" in q or "과매도" in question or "평균 회귀" in question or "mean rever" in q:
        return "RSI_MEAN_REVERT"
    if "회복" in question or "recovery" in q:
        return "RECOVERY_OVERSOLD"
    if "추세 상태" in question or "trend_state" in q or "trend state" in q:
        return "TREND_STATE_FOLLOW"
    if "추세" in question or "sma" in q or "이동평균" in question or "moving average" in q:
        return "SMA_50_CROSS"
    return None


def _match_strategy_id(question: str) -> str:
    """Anchored variant used by loose deep-link blocks — always resolves."""

    return _match_strategy_id_opt(question) or "SMA_50_CROSS"


@dataclass(frozen=True)
class SimQueryResult:
    """A resolved simulation request (Phase 21.6) — what the deterministic chat
    responder needs to narrate the result, render the inline mini-chart, and
    deep-link the Quant Lab tab. ``result`` is the full SimulationResult (or None
    when nothing ran)."""

    strategy_id: str
    ticker: str
    line: str
    ran: bool
    result: object | None = None


def _detect_sim_ticker(service, question: str) -> tuple[str | None, str | None]:
    """(ticker_with_bars, named_ticker_without_bars) from the question.

    A user-named ticker that has stored bars wins; if they named something
    ticker-shaped that has no bars, surface it so we never silently swap."""

    named_missing: str | None = None
    for token in re.findall(r"\b[A-Z]{2,6}\b", question.upper()):
        if token in _SYMBOL_STOP:
            continue
        if service.market.count_for(token, "1d") >= 60:
            return token, None
        named_missing = named_missing or token
    return None, named_missing


def resolve_simulation_query(
    session, question: str, *, require_anchor: bool = True
) -> SimQueryResult | None:
    """Run the matched built-in strategy over stored bars and return a structured
    descriptive result (exposure ON/OFF, never buy/sell). ``require_anchor`` (the
    default) returns None unless the user named a concrete strategy or ticker — so
    the deterministic responder only fires on a real simulation request."""

    if session is None or not (question or "").strip():
        return None
    from finskillos.services.simulation_service import SimulationService

    service = SimulationService(session)
    sid_opt = _match_strategy_id_opt(question)
    ticker, missing = _detect_sim_ticker(service, question)
    if require_anchor and sid_opt is None and ticker is None and missing is None:
        return None
    sid = sid_opt or "SMA_50_CROSS"

    if ticker is None and missing is not None:
        line = (
            f"'{missing}' 의 저장된 일봉 바가 부족해(60개 미만) 시뮬레이션할 수 "
            "없습니다 — Quant Lab 탭에서 데이터가 있는 종목을 선택하거나 먼저 "
            "수집하세요. 매매 권유가 아닙니다."
        )
        return SimQueryResult(sid, missing, line, ran=False)

    result = service.run(sid, ticker=ticker)
    if result is None or result.bar_count == 0:
        line = (
            f"전략 {sid}: 시뮬레이션할 저장된 일봉 바가 부족합니다 "
            "(Quant Lab 탭에서 다른 종목을 선택하거나 데이터를 더 수집하세요)."
        )
        return SimQueryResult(sid, ticker or "", line, ran=False)

    m = result.metrics

    def _pct(v: float | None) -> str:
        return "n/a" if v is None else f"{v * 100:.1f}%"

    def _r(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.2f}"

    line = (
        f"시뮬레이션 [{result.strategy_id} · {result.name}] on {result.ticker} "
        f"({result.bar_count} 일봉 바): 노출 비중 {_pct(m.exposure_pct)}, "
        f"누적 {_pct(m.total_return)} (벤치마크=동일 종목 보유 대비 관측치), "
        f"Sharpe {_r(m.sharpe)}, 최대 낙폭 {_pct(m.max_drawdown)}, "
        f"라운드트립 {m.round_trips}회. 저장된 과거 바 리플레이 관측 결과이며 "
        "매매 권유가 아닙니다 — Quant Lab 탭에서 곡선을 시각적으로 확인할 수 있습니다."
    )
    return SimQueryResult(
        result.strategy_id, result.ticker, line, ran=True, result=result
    )


def _simulation_section(session, question: str) -> str | None:
    """Lenient wrapper for the LLM fetch-context path (defaults when unanchored)."""

    res = resolve_simulation_query(session, question, require_anchor=False)
    return res.line if res else None


def detected_query_sources(question: str) -> list[tuple[str, str]]:
    """Which query sources a question will hit → [(key, human label)] for the
    streaming step display. Mirrors the intent gates in build_query_context."""

    q = question or ""
    out: list[tuple[str, str]] = []
    if _EVENT_Q.search(q):
        out.append(("events", "카탈리스트 이벤트 조회"))
    if _NEWS_Q.search(q):
        out.append(("news", "보유종목 뉴스 조회"))
    if _TRADE_Q.search(q):
        out.append(("trades", "거래 기록 조회"))
    if _SIM_Q.search(q):
        out.append(("simulation", "퀀트 전략 시뮬레이션"))
    if re.search(r"\b[A-Z]{2,6}\b", q):
        out.append(("symbol", "종목 데이터 분석"))
    return out


def build_query_context(session, question: str, *, only: str | None = None) -> str:
    """Question-aware read: fetch the specific read models the question is about
    (events / news / recent trades) and return a descriptive block for this turn.
    Empty when the question matches none or nothing is stored. Read-only.

    ``only`` (events / news / trades / symbol) restricts to a single source so the
    streaming endpoint can fetch + time each source as its own step."""

    if session is None or not (question or "").strip():
        return ""

    try:
        account = _account(session)
    except Exception:  # noqa: BLE001
        account = None

    sections: list[str] = []

    if only in (None, "events") and _EVENT_Q.search(question):
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

    if only in (None, "news") and _NEWS_Q.search(question) and account is not None:
        try:
            from finskillos.services.news_service import NewsService

            rows = NewsService(session).list_holdings_relevant_articles(
                account_id=account.id, limit=30
            )
            if rows:
                ranked = _dedupe_news(
                    sorted(
                        rows, key=lambda r: _news_importance(r[0], r[1]), reverse=True
                    )
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

    if only in (None, "trades") and _TRADE_Q.search(question) and account is not None:
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

    if only in (None, "rules") and _RULES_Q.search(question) and account is not None:
        try:
            from finskillos.services.risk_guard_service import RiskGuardService

            records = RiskGuardService(session).applied_rules(account.id)
            if records:
                items = "; ".join(
                    f"{r.skill_id} → {r.fired_rule_ids[0]} ({r.status})"
                    for r in records
                )
                sections.append(
                    "Applied skill rules — which rule fired per risk skill in the "
                    f"live evaluation: {items} (descriptive audit, not a signal)."
                )
        except Exception:  # noqa: BLE001
            pass

    if only in (None, "rules") and _RULES_Q.search(question):
        # The regime classification rule that fired (Phase 20.3c) — the same
        # audit affordance for the REGIME domain, evaluated read-only on demand.
        try:
            from finskillos.services.regime_service import RegimeService

            out = RegimeService(session).evaluate_today_regime(persist=False)
            if out.classification_rule_id:
                sections.append(
                    f"Regime classification: {out.regime} classified by rule "
                    f"{out.classification_rule_id} (risk {out.risk_level}) — "
                    "descriptive audit, not a signal."
                )
        except Exception:  # noqa: BLE001
            pass

    if only in (None, "simulation") and _SIM_Q.search(question):
        try:
            line = _simulation_section(session, question)
            if line:
                sections.append(line)
        except Exception:  # noqa: BLE001
            pass

    # Per-symbol detail when the question names a ticker that has stored data
    # (the data-exists filter removes non-ticker uppercase words like RSI/FOMC).
    try:
        from finskillos.data_sources.dto import DEFAULT_TIMEFRAME
        from finskillos.db.repositories import IndicatorRepository, MarketRepository

        candidates = (
            []
            if only not in (None, "symbol")
            else [
                t
                for t in dict.fromkeys(re.findall(r"\b[A-Z]{2,6}\b", question))
                if t not in _SYMBOL_STOP
            ]
        )
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
