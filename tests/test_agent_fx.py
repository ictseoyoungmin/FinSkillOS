"""FX rate + USD→KRW ingestion conversion — v3. Offline (env / injected)."""

from __future__ import annotations

from decimal import Decimal

import finskillos.agent.fx as fx_mod
from finskillos.agent.chat import ChatMessage, run_chat
from finskillos.agent.fx import DEFAULT_USD_KRW, usd_krw_rate
from finskillos.agent.ingest import parse_portfolio_paste, proposal_from_records
from finskillos.llm.provider import EchoProvider


def test_env_override_forces_a_fixed_rate(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1400")
    assert usd_krw_rate() == Decimal("1400")


def test_injected_fetcher_used_when_no_env(monkeypatch) -> None:
    monkeypatch.delenv("FINSKILLOS_USD_KRW_RATE", raising=False)
    fx_mod._CACHE["rate"] = None
    assert usd_krw_rate(fetcher=lambda: Decimal("1300")) == Decimal("1300")


def test_fetcher_failure_falls_back(monkeypatch) -> None:
    monkeypatch.delenv("FINSKILLOS_USD_KRW_RATE", raising=False)
    fx_mod._CACHE["rate"] = None

    def boom():
        raise RuntimeError("network")

    assert usd_krw_rate(fetcher=boom) == DEFAULT_USD_KRW


def test_parse_converts_usd_lines_keeps_krw() -> None:
    proposal = parse_portfolio_paste(
        "ASTX 111 $3,527.14\nNVDA 10 ₩25,000,000", usd_krw_rate=Decimal("1350")
    )
    rows = {r.ticker: r.market_value for r in proposal.rows}
    assert rows["ASTX"] == "4761639"  # 3527.14 * 1350
    assert rows["NVDA"] == "25000000"  # KRW line untouched


def test_records_convert_on_usd_currency_flag() -> None:
    proposal = proposal_from_records(
        [{"ticker": "MU", "quantity": 2, "market_value": 1807.07, "currency": "USD"}],
        usd_krw_rate=Decimal("1350"),
    )
    assert proposal.rows[0].market_value == "2439544"


def test_chat_usd_paste_is_converted(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_USD_KRW_RATE", "1350")
    reply = run_chat(
        [ChatMessage("user", "ASTX 111 $3,527.14\nNVDL 27 $2,596.09")],
        provider=EchoProvider(),
    )
    action = reply.proposed_action
    assert action is not None and action.kind == "portfolio_import"
    # Converted to KRW (millions), not the raw dollar figures.
    assert "4761639" in action.normalized_csv
