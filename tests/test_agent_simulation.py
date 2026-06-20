"""Phase 21.4 — agent runs a quant simulation on intent (read-only, descriptive).

The agent "designs" by routing a free-text request onto a built-in StrategySpec,
runs it over stored bars via the same query-context reader, and answers with a
simulation observation (exposure ON/OFF, never buy/sell)."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.agent.context import (
    _match_strategy_id,
    build_query_context,
    detected_query_sources,
)
from finskillos.data_sources import MockMarketDataAdapter
from finskillos.db.base import Base
from finskillos.db.seed import seed_default_account
from finskillos.guards.base import find_forbidden_term
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService


def _session_with_bars(ticker: str = "NVDA", bars: int = 80):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    seed_default_account(session)
    MarketDataService(
        session,
        adapter=MockMarketDataAdapter(default_bars=bars),
        universe=[ticker],
    ).refresh_bars([ticker])
    SignalService(session).compute_for_universe([ticker])
    session.commit()
    return session


def test_match_strategy_id_routes_keywords() -> None:
    assert _match_strategy_id("골든크로스 돌려봐") == "SMA_GOLDEN_20_50"
    assert _match_strategy_id("RSI 과매도 반등 전략") == "RSI_MEAN_REVERT"
    assert _match_strategy_id("회복 국면 전략 시뮬") == "RECOVERY_OVERSOLD"
    assert _match_strategy_id("추세 상태 추종") == "TREND_STATE_FOLLOW"
    assert _match_strategy_id("그냥 추세 추종 전략") == "SMA_50_CROSS"
    # An explicit id wins.
    assert _match_strategy_id("RSI_MEAN_REVERT 돌려") == "RSI_MEAN_REVERT"


def test_simulation_intent_detected() -> None:
    sources = dict(detected_query_sources("NVDA 추세 추종 전략 시뮬레이션 해줘"))
    assert "simulation" in sources


def test_query_context_runs_simulation_on_intent() -> None:
    session = _session_with_bars("NVDA", bars=80)
    out = build_query_context(session, "NVDA 추세 추종 전략 백테스트 해줘")
    assert "시뮬레이션" in out
    assert "NVDA" in out
    assert "노출 비중" in out and "Sharpe" in out
    # Descriptive-only — no buy/sell wording anywhere in the generated line.
    assert find_forbidden_term(out) is None
    # No simulation intent → no simulation section.
    assert "시뮬레이션 [" not in build_query_context(session, "안녕하세요")


def test_simulation_block_becomes_open_quant_lab_action() -> None:
    from finskillos.agent.chat import _extract_llm_actions

    reply = (
        "QQQ 추세 상태 추종 시뮬레이션 관측치입니다.\n"
        '```json\n{"simulation": {"strategy": "TREND_STATE_FOLLOW", "ticker": "qqq"}}\n```'
    )
    cleaned, actions = _extract_llm_actions(reply)
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == "open_simulation"
    assert action.nav_path == "/quant-lab?strategy=TREND_STATE_FOLLOW&ticker=QQQ"
    assert action.apply_endpoint == ""  # navigation only, never a mutation
    assert "```" not in cleaned
    assert find_forbidden_term(action.summary) is None


def test_simulation_block_routes_loose_name_and_defaults_ticker() -> None:
    from finskillos.agent.chat import _simulation_action

    # A loose name routes onto the closest spec; ticker defaults to the spec's.
    action = _simulation_action({"strategy": "골든크로스"})
    assert action is not None
    assert action.nav_path == "/quant-lab?strategy=SMA_GOLDEN_20_50&ticker=AAPL"
    # A non-dict block is ignored.
    assert _simulation_action("nope") is None


def test_simulation_section_handles_missing_bars() -> None:
    session = _session_with_bars("NVDA", bars=80)
    out = build_query_context(session, "ZZZZ 전략 시뮬레이션")
    # Names a ticker without bars → falls back to the default ticker's run or a
    # graceful note; either way it stays descriptive and non-empty.
    assert out and find_forbidden_term(out) is None
