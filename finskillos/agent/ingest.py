"""Agent ingestion parser — v3 Phase 11 / Slice 189.

Turns free-form pasted text (a portfolio dump, a broker holdings table, a few
typed lines) into a **structured proposal** the user can review before anything
touches the database. Deterministic and offline — no model call — so a paste
always parses the same way and tests are reproducible. An LLM provider (Phase 10)
may later pre-clean messy input, but the safe default is this parser.

The proposal carries normalized rows + per-line warnings + a `normalized_csv` in
exactly the shape the existing portfolio import endpoint accepts, so applying the
proposal reuses the audited dry-run → confirm import path (no new mutation code).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation

__all__ = [
    "IngestRow",
    "IngestProposal",
    "parse_portfolio_paste",
    "proposal_from_records",
    "TradeRow",
    "TradeIngestProposal",
    "parse_trades_paste",
    "trades_from_records",
    "WatchlistOp",
    "parse_watchlist_request",
    "watchlist_from_block",
    "PROTOCOL_KEYS",
    "PROTOCOL_LABELS",
    "parse_protocol_request",
    "parse_protocol_requests",
    "protocol_from_block",
]

_TICKER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9.\-]{0,31}$")
_CSV_COLUMNS = (
    "ticker",
    "quantity",
    "market_value",
    "average_cost",
    "sector",
    "theme",
    "strategy_type",
)


@dataclass(frozen=True)
class IngestRow:
    ticker: str
    quantity: str
    market_value: str
    average_cost: str | None = None
    sector: str | None = None
    theme: str | None = None
    strategy_type: str = "swing"


@dataclass(frozen=True)
class IngestProposal:
    rows: list[IngestRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def normalized_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_CSV_COLUMNS)
        for row in self.rows:
            writer.writerow(
                [
                    row.ticker,
                    row.quantity,
                    row.market_value,
                    row.average_cost or "",
                    row.sector or "",
                    row.theme or "",
                    row.strategy_type,
                ]
            )
        return buffer.getvalue()


def _to_krw(value: str | None, rate) -> str | None:
    """Convert a numeric string from USD to KRW (rounded), or pass through."""

    if value is None or rate is None:
        return value
    try:
        return str(int((Decimal(value) * Decimal(str(rate))).to_integral_value()))
    except (InvalidOperation, ValueError, TypeError):
        return value


def _row_to_krw(row: IngestRow, rate) -> IngestRow:
    return replace(
        row,
        market_value=_to_krw(row.market_value, rate),
        average_cost=_to_krw(row.average_cost, rate) if row.average_cost else None,
    )


def _clean_number(token: str) -> str | None:
    """Strip currency symbols / thousands separators; return a numeric string."""

    stripped = token.strip().replace(",", "")
    stripped = re.sub(r"[₩$€£¥\s]", "", stripped)
    if stripped in ("", "-"):
        return None
    if re.fullmatch(r"-?\d+(\.\d+)?", stripped):
        return stripped
    return None


def _split_line(line: str) -> list[str]:
    # Remove only true thousands-separator commas (digit , exactly-3-digits then a
    # non-digit or end), so "₩25,000,000" collapses but a CSV field comma like
    # "5,1000000" is preserved.
    line = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", line)
    if "\t" in line:
        parts = line.split("\t")
    elif "," in line:
        parts = line.split(",")
    else:
        parts = re.split(r"\s{2,}|\s", line.strip())
    return [p.strip() for p in parts if p.strip() != ""]


def _looks_like_header(parts: list[str]) -> bool:
    lowered = [p.lower() for p in parts]
    return "ticker" in lowered and any(
        key in lowered for key in ("quantity", "qty", "market_value", "value")
    )


def _row_from_header(parts: list[str], header: list[str]) -> tuple[IngestRow | None, str | None]:
    record = {header[i]: parts[i] for i in range(min(len(header), len(parts)))}

    def pick(*keys: str) -> str | None:
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return value
        return None

    ticker = pick("ticker", "symbol")
    quantity = pick("quantity", "qty", "shares")
    value = pick("market_value", "value", "marketvalue")
    if not ticker or not _TICKER_RE.match(ticker):
        return None, f"No valid ticker in: {parts}"
    qty = _clean_number(quantity or "")
    val = _clean_number(value or "")
    if qty is None or val is None:
        return None, f"Missing quantity / market value for {ticker}."
    avg = _clean_number(pick("average_cost", "avg_cost", "cost") or "")
    return (
        IngestRow(
            ticker=ticker.upper(),
            quantity=qty,
            market_value=val,
            average_cost=avg,
            sector=pick("sector"),
            theme=pick("theme"),
            strategy_type=pick("strategy_type", "strategy") or "swing",
        ),
        None,
    )


def _row_positional(parts: list[str]) -> tuple[IngestRow | None, str | None]:
    if not parts:
        return None, None
    ticker, rest = parts[0], parts[1:]
    if not _TICKER_RE.match(ticker):
        return None, f"First token is not a ticker: {parts}"
    numbers: list[str] = []
    text: list[str] = []
    for token in rest:
        cleaned = _clean_number(token)
        if cleaned is not None:
            numbers.append(cleaned)
        else:
            text.append(token)
    if len(numbers) < 2:
        return None, f"Could not read quantity + market value for {ticker.upper()}."
    return (
        IngestRow(
            ticker=ticker.upper(),
            quantity=numbers[0],
            market_value=numbers[1],
            average_cost=numbers[2] if len(numbers) > 2 else None,
            sector=text[0] if text else None,
            theme=text[1] if len(text) > 1 else None,
        ),
        None,
    )


def parse_portfolio_paste(text: str, *, usd_krw_rate=None) -> IngestProposal:
    """Parse free-form pasted holdings into a structured, reviewable proposal.

    When a line is in USD (a ``$`` appears) and ``usd_krw_rate`` is given, the
    row's market value / average cost are converted to KRW for storage."""

    rows: list[IngestRow] = []
    warnings: list[str] = []
    header: list[str] | None = None
    seen_tickers: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = _split_line(line)
        if header is None and _looks_like_header(parts):
            header = [p.lower().replace(" ", "_") for p in parts]
            continue
        if header is not None:
            row, warning = _row_from_header(parts, header)
        else:
            row, warning = _row_positional(parts)
        if warning:
            warnings.append(warning)
            continue
        if row is None:
            continue
        if row.ticker in seen_tickers:
            warnings.append(f"Duplicate ticker {row.ticker} — kept the first.")
            continue
        seen_tickers.add(row.ticker)
        if usd_krw_rate is not None and "$" in raw_line:
            row = _row_to_krw(row, usd_krw_rate)
        rows.append(row)

    if not rows and not warnings:
        warnings.append("No holdings could be read from the pasted text.")
    return IngestProposal(rows=rows, warnings=warnings)


# --- trades ------------------------------------------------------------------

_TRADE_CSV_COLUMNS = (
    "trade_date",
    "ticker",
    "side",
    "strategy_type",
    "result_pnl",
    "result_pnl_pct",
    "r_multiple",
    "mistake_tags",
    "sector",
    "theme",
    "notes",
)
_SIDE_ALIASES = {
    "long": "LONG",
    "buy": "BUY",
    "bought": "BUY",
    "short": "SHORT",
    "sell": "SELL",
    "sold": "SELL",
    "watch": "WATCH",
    "exit": "EXIT_REVIEW",
    "exit_review": "EXIT_REVIEW",
    "other": "OTHER",
}
_VALID_SIDES = {"LONG", "SHORT", "WATCH", "EXIT_REVIEW", "OTHER", "BUY", "SELL"}
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class TradeRow:
    trade_date: str
    ticker: str
    side: str
    result_pnl: str | None = None
    strategy_type: str | None = None
    notes: str | None = None
    sector: str | None = None
    theme: str | None = None


@dataclass(frozen=True)
class TradeIngestProposal:
    rows: list[TradeRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def normalized_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_TRADE_CSV_COLUMNS)
        for row in self.rows:
            writer.writerow(
                [
                    row.trade_date,
                    row.ticker,
                    row.side,
                    row.strategy_type or "",
                    row.result_pnl or "",
                    "",  # result_pnl_pct
                    "",  # r_multiple
                    "",  # mistake_tags
                    row.sector or "",
                    row.theme or "",
                    row.notes or "",
                ]
            )
        return buffer.getvalue()


def _normalize_side(raw: str) -> str | None:
    token = str(raw).strip()
    upper = token.upper()
    if upper in _VALID_SIDES:
        return upper
    return _SIDE_ALIASES.get(token.lower())


def _today_iso() -> str:
    from datetime import date as _date

    return _date.today().isoformat()


def trades_from_records(records: list[dict]) -> TradeIngestProposal:
    """Build a trade-journal proposal from structured records (LLM-extracted)."""

    rows: list[TradeRow] = []
    warnings: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        ticker = str(record.get("ticker", "")).strip().upper()
        if not _TICKER_RE.match(ticker):
            warnings.append(f"Skipped a trade with no valid ticker: {record!r}")
            continue
        side = _normalize_side(record.get("side", ""))
        if side is None:
            warnings.append(
                f"{ticker}: unknown side {record.get('side')!r} "
                "(use long/short/buy/sell/watch/exit)."
            )
            continue
        raw_date = str(record.get("trade_date") or record.get("date") or "").strip()
        trade_date = raw_date if _ISO_DATE_RE.fullmatch(raw_date) else _today_iso()
        pnl = record.get("result_pnl", record.get("pnl"))
        rows.append(
            TradeRow(
                trade_date=trade_date,
                ticker=ticker,
                side=side,
                result_pnl=_clean_number(str(pnl)) if pnl not in (None, "") else None,
                strategy_type=(str(record["strategy_type"]).strip() or None)
                if record.get("strategy_type")
                else None,
                notes=(str(record["notes"]).strip() or None)
                if record.get("notes")
                else None,
                sector=(str(record["sector"]).strip() or None)
                if record.get("sector")
                else None,
                theme=(str(record["theme"]).strip() or None)
                if record.get("theme")
                else None,
            )
        )
    return TradeIngestProposal(rows=rows, warnings=warnings)


def parse_trades_paste(text: str) -> TradeIngestProposal:
    """Light deterministic parse of pasted trades — header CSV or
    ``TICKER SIDE [YYYY-MM-DD] [pnl]`` lines. Free-form is better handled by the
    LLM extraction; this is the offline fallback."""

    records: list[dict] = []
    header: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = _split_line(line)
        lowered = [p.lower() for p in parts]
        if header is None and "ticker" in lowered and "side" in lowered:
            header = [p.lower().replace(" ", "_") for p in parts]
            continue
        if header is not None:
            records.append(
                {header[i]: parts[i] for i in range(min(len(header), len(parts)))}
            )
            continue
        # positional: ticker, side, [date], [pnl]
        if len(parts) < 2:
            continue
        record: dict = {"ticker": parts[0], "side": parts[1]}
        for token in parts[2:]:
            if _ISO_DATE_RE.fullmatch(token):
                record["trade_date"] = token
            elif _clean_number(token) is not None:
                record["result_pnl"] = token
        records.append(record)
    proposal = trades_from_records(records)
    if not proposal.rows and not proposal.warnings:
        proposal = TradeIngestProposal(
            rows=[], warnings=["No trades could be read from the pasted text."]
        )
    return proposal


# --- watchlist ---------------------------------------------------------------

_DEFAULT_WATCH_FOLDER = "Watchlist"
# Require an explicit watchlist intent (not a bare "watch", which false-fires on
# "watch out …"). The LLM block handles looser phrasing for capable models.
_WATCH_KW = re.compile(
    r"\bwatch\s?list\b|관심\s?종목|워치\s?리스트|워치리스트", re.IGNORECASE
)
_WATCH_REMOVE_KW = re.compile(r"\bremove\b|\bdelete\b|\bdrop\b|빼|삭제|제외", re.IGNORECASE)
_WATCH_STOP = {
    "ADD", "REMOVE", "DELETE", "DROP", "TO", "FROM", "MY", "THE", "A", "AN",
    "AND", "OR", "LIST", "WATCH", "PLEASE", "ON", "IN", "OF", "FOLDER",
}


@dataclass(frozen=True)
class WatchlistOp:
    add: tuple[str, ...] = ()
    remove: tuple[str, ...] = ()
    folder: str = _DEFAULT_WATCH_FOLDER


def _watch_tickers(text: str) -> list[str]:
    out: list[str] = []
    for token in re.findall(r"\b[A-Z]{1,6}\b", text):
        if token not in _WATCH_STOP and token not in out:
            out.append(token)
    return out


def parse_watchlist_request(
    text: str, *, folder: str = _DEFAULT_WATCH_FOLDER
) -> WatchlistOp | None:
    """Deterministic watch intent: requires a watch keyword + uppercase tickers."""

    if not _WATCH_KW.search(text):
        return None
    tickers = tuple(_watch_tickers(text))
    if not tickers:
        return None
    if _WATCH_REMOVE_KW.search(text):
        return WatchlistOp(remove=tickers, folder=folder)
    return WatchlistOp(add=tickers, folder=folder)


def _valid_tickers(values) -> tuple[str, ...]:
    out: list[str] = []
    for value in values or []:
        ticker = str(value).strip().upper()
        if _TICKER_RE.match(ticker) and ticker not in out:
            out.append(ticker)
    return tuple(out)


def watchlist_from_block(data: dict) -> WatchlistOp | None:
    """Parse a `{"watchlist": [...] | {add, remove, folder}}` block."""

    watchlist = data.get("watchlist") if isinstance(data, dict) else None
    if watchlist is None:
        return None
    if isinstance(watchlist, list):
        add = _valid_tickers(watchlist)
        return WatchlistOp(add=add) if add else None
    if isinstance(watchlist, dict):
        add = _valid_tickers(watchlist.get("add"))
        remove = _valid_tickers(watchlist.get("remove"))
        folder = str(watchlist.get("folder") or _DEFAULT_WATCH_FOLDER).strip()
        if add or remove:
            return WatchlistOp(
                add=add, remove=remove, folder=folder or _DEFAULT_WATCH_FOLDER
            )
    return None


# --- operational protocols ---------------------------------------------------

# The idempotent System Ops protocols an agent may trigger (operational, not
# trading). Setup-only protocols (seed_*) are intentionally excluded.
PROTOCOL_LABELS: dict[str, str] = {
    "refresh_market_data": "refresh market data",
    "refresh_news": "refresh news",
    "calculate_indicators": "recalculate indicators",
    "recompute_regime": "recompute the market regime",
    "run_risk_guards": "re-run the risk guards",
    "refresh_events": "refresh catalyst events",
}
PROTOCOL_KEYS = tuple(PROTOCOL_LABELS)

# Conservative intent patterns: each needs an explicit refresh/recompute/run verb
# next to its target, so "what's my regime?" does not trigger a recompute.
_PROTOCOL_INTENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"recompute.*regime|regime.*(recompute|re-?evaluate)"
            r"|(레짐|국면|regime).*(재계산|재평가|다시\s*계산)",
            re.IGNORECASE,
        ),
        "recompute_regime",
    ),
    (
        re.compile(
            r"(re-?run|rerun).*(risk\s*guard|guard)|run.*risk\s*guard"
            r"|(risk\s*guard|guard|가드|리스크\s*가드).*(재실행|다시\s*(돌려|실행|평가)|재평가)"
            r"|가드.*다시",
            re.IGNORECASE,
        ),
        "run_risk_guards",
    ),
    (
        re.compile(
            r"refresh.*news|news.*(refresh|update)|(뉴스).*(새로고침|갱신|업데이트)",
            re.IGNORECASE,
        ),
        "refresh_news",
    ),
    (
        re.compile(
            r"refresh.*event|event.*(refresh|update)"
            r"|(이벤트|카탈리스트|catalyst).*(새로고침|갱신|업데이트)",
            re.IGNORECASE,
        ),
        "refresh_events",
    ),
    (
        re.compile(
            r"(re-?calculate|recompute).*indicator|indicator.*(recalculate|update)"
            r"|(지표).*(계산|재계산|업데이트)",
            re.IGNORECASE,
        ),
        "calculate_indicators",
    ),
    (
        re.compile(
            r"refresh.*market.*data|(market|price)\s*data.*(refresh|update)"
            r"|(시장|시세|가격).*(데이터)?.*(새로고침|갱신|업데이트)",
            re.IGNORECASE,
        ),
        "refresh_market_data",
    ),
)


def parse_protocol_request(text: str) -> str | None:
    """Deterministic operational-protocol intent → first protocol key, or None."""

    for pattern, key in _PROTOCOL_INTENTS:
        if pattern.search(text):
            return key
    return None


# Sensible execution order for multi-step: refresh sources → derive → evaluate.
_PROTOCOL_PIPELINE = (
    "refresh_market_data",
    "refresh_news",
    "refresh_events",
    "calculate_indicators",
    "recompute_regime",
    "run_risk_guards",
)


def parse_protocol_requests(text: str) -> list[str]:
    """All operational-protocol intents in the text (for multi-step requests like
    'refresh data and re-run the guards'), de-duplicated and ordered as a pipeline
    (refresh sources first, evaluate last)."""

    found = {key for pattern, key in _PROTOCOL_INTENTS if pattern.search(text)}
    return [key for key in _PROTOCOL_PIPELINE if key in found]


def protocol_from_block(data: dict) -> str | None:
    """Parse a `{"protocol": "recompute_regime"}` block."""

    key = data.get("protocol") if isinstance(data, dict) else None
    if isinstance(key, str) and key in PROTOCOL_LABELS:
        return key
    return None


def proposal_from_records(records: list[dict], *, usd_krw_rate=None) -> IngestProposal:
    """Build a proposal from already-structured records (e.g. LLM-extracted).

    Same validation as the text parser, so an LLM extraction can never bypass
    the ticker / numeric checks. A record with ``currency == "USD"`` is converted
    to KRW with ``usd_krw_rate`` when supplied.
    """

    rows: list[IngestRow] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        ticker = str(record.get("ticker", "")).strip().upper()
        if not _TICKER_RE.match(ticker):
            warnings.append(f"Skipped a record with no valid ticker: {record!r}")
            continue
        qty = _clean_number(str(record.get("quantity", "")))
        value = _clean_number(
            str(record.get("market_value", record.get("value", "")))
        )
        if qty is None or value is None:
            warnings.append(f"Missing quantity / market value for {ticker}.")
            continue
        if ticker in seen:
            warnings.append(f"Duplicate ticker {ticker} — kept the first.")
            continue
        seen.add(ticker)
        avg_raw = record.get("average_cost") or record.get("avg_cost")
        row = IngestRow(
            ticker=ticker,
            quantity=qty,
            market_value=value,
            average_cost=_clean_number(str(avg_raw)) if avg_raw else None,
            sector=(str(record["sector"]).strip() or None)
            if record.get("sector")
            else None,
            theme=(str(record["theme"]).strip() or None)
            if record.get("theme")
            else None,
            strategy_type=str(record.get("strategy_type") or "swing"),
        )
        if usd_krw_rate is not None and str(record.get("currency", "")).upper() == "USD":
            row = _row_to_krw(row, usd_krw_rate)
        rows.append(row)
    return IngestProposal(rows=rows, warnings=warnings)
