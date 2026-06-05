"""Agent ingestion parser + endpoint tests — v3 Phase 11 / Slice 189."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app
from finskillos.agent.ingest import (
    parse_portfolio_paste,
    parse_trades_paste,
    proposal_from_records,
    trades_from_records,
)


def test_parse_trades_paste_positional_and_csv() -> None:
    proposal = parse_trades_paste(
        "NVDA long 2026-06-01 250000\nTSLA sold 2026-05-20 -120000"
    )
    assert [(r.ticker, r.side, r.trade_date) for r in proposal.rows] == [
        ("NVDA", "LONG", "2026-06-01"),
        ("TSLA", "SELL", "2026-05-20"),
    ]
    assert proposal.normalized_csv.startswith("trade_date,ticker,side")


def test_trades_from_records_normalizes_side_and_warns() -> None:
    proposal = trades_from_records(
        [
            {"ticker": "aapl", "side": "buy", "date": "2026-06-05", "pnl": "50000"},
            {"ticker": "MSFT", "side": "nonsense"},  # bad side → warn
        ]
    )
    assert [r.ticker for r in proposal.rows] == ["AAPL"]
    assert proposal.rows[0].side == "BUY"
    assert any("side" in w for w in proposal.warnings)


def test_proposal_from_records_validates_like_the_parser() -> None:
    proposal = proposal_from_records(
        [
            {"ticker": "nvda", "quantity": 10, "market_value": 25000000, "sector": "Semis"},
            {"ticker": "", "quantity": 1, "market_value": 2},  # no ticker → warn
            {"ticker": "TSLA", "quantity": "x", "market_value": "y"},  # bad nums → warn
            {"ticker": "NVDA", "quantity": 9, "market_value": 9},  # dup → warn
        ]
    )
    assert [r.ticker for r in proposal.rows] == ["NVDA"]
    assert proposal.rows[0].market_value == "25000000"
    assert len(proposal.warnings) == 3


def test_parses_freeform_with_currency_and_thousands() -> None:
    proposal = parse_portfolio_paste("NVDA 10 ₩25,000,000 Semiconductors AI")
    assert len(proposal.rows) == 1
    row = proposal.rows[0]
    assert row.ticker == "NVDA"
    assert row.quantity == "10"
    assert row.market_value == "25000000"
    assert row.sector == "Semiconductors"
    assert row.theme == "AI"


def test_parses_comma_separated() -> None:
    proposal = parse_portfolio_paste("TSLA, 12, 12000000, Consumer, EV")
    assert proposal.rows[0].ticker == "TSLA"
    assert proposal.rows[0].market_value == "12000000"


def test_parses_header_csv_by_column() -> None:
    text = "ticker,quantity,market_value,sector\nAAPL,5,1000000,Tech"
    proposal = parse_portfolio_paste(text)
    assert proposal.rows[0].ticker == "AAPL"
    assert proposal.rows[0].sector == "Tech"


def test_duplicate_and_bad_lines_warn_not_crash() -> None:
    proposal = parse_portfolio_paste("NVDA 1 100\nNVDA 9 9\njust-words-here")
    assert len(proposal.rows) == 1
    assert any("Duplicate" in w for w in proposal.warnings)
    assert any("quantity" in w.lower() for w in proposal.warnings)


def test_empty_text_warns() -> None:
    proposal = parse_portfolio_paste("   \n  ")
    assert proposal.rows == []
    assert proposal.warnings


def test_normalized_csv_has_the_import_header() -> None:
    csv = parse_portfolio_paste("NVDA 10 25000000").normalized_csv
    header = csv.splitlines()[0]
    assert header.startswith("ticker,quantity,market_value")


def test_ingest_endpoint_previews_without_mutation() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/api/agent/ingest",
        json={"target": "portfolio", "text": "NVDA 10 25000000 Semis\nTSLA 12 12000000"},
    ).json()
    assert body["target"] == "portfolio"
    assert body["rowCount"] == 2
    assert {r["ticker"] for r in body["rows"]} == {"NVDA", "TSLA"}
    assert body["normalizedCsv"].startswith("ticker,quantity,market_value")
    assert body["applyEndpoint"] == "/api/mission-control/import-positions"
    assert "preview only" in body["boundary"].lower()


def test_ingest_endpoint_reports_warnings() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/api/agent/ingest", json={"target": "portfolio", "text": "garbage line"}
    ).json()
    assert body["rowCount"] == 0
    assert body["warnings"]
