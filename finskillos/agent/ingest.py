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
from dataclasses import dataclass, field

__all__ = [
    "IngestRow",
    "IngestProposal",
    "parse_portfolio_paste",
    "proposal_from_records",
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


def parse_portfolio_paste(text: str) -> IngestProposal:
    """Parse free-form pasted holdings into a structured, reviewable proposal."""

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
        rows.append(row)

    if not rows and not warnings:
        warnings.append("No holdings could be read from the pasted text.")
    return IngestProposal(rows=rows, warnings=warnings)


def proposal_from_records(records: list[dict]) -> IngestProposal:
    """Build a proposal from already-structured records (e.g. LLM-extracted).

    Same validation as the text parser, so an LLM extraction can never bypass
    the ticker / numeric checks before reaching the import.
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
        rows.append(
            IngestRow(
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
        )
    return IngestProposal(rows=rows, warnings=warnings)
