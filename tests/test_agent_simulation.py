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
from finskillos.guards.base import find_coercive_term
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


def test_resolve_simulation_requires_anchor() -> None:
    from finskillos.agent.context import resolve_simulation_query

    session = _session_with_bars("NVDA", bars=80)
    # No concrete strategy or ticker → no deterministic run (LLM would handle it).
    assert resolve_simulation_query(session, "백테스트가 뭐야?", require_anchor=True) is None
    # A named ticker with bars is enough of an anchor.
    res = resolve_simulation_query(session, "NVDA 시뮬레이션", require_anchor=True)
    assert res is not None and res.ran and res.ticker == "NVDA"


def test_resolve_simulation_named_ticker_without_bars_is_explicit() -> None:
    from finskillos.agent.context import resolve_simulation_query

    session = _session_with_bars("NVDA", bars=80)
    res = resolve_simulation_query(session, "ZZZZ 추세 추종 시뮬레이션", require_anchor=True)
    assert res is not None and not res.ran and res.ticker == "ZZZZ"
    assert "부족" in res.line  # never silently swaps to another ticker


def test_available_tickers_reflects_stored_bars() -> None:
    from finskillos.services.simulation_service import SimulationService

    session = _session_with_bars("TSLL", bars=80)
    tickers = SimulationService(session).available_tickers()
    assert tickers == ["TSLL"]  # dynamic, not a hardcoded candidate list


def test_query_context_runs_simulation_on_intent() -> None:
    session = _session_with_bars("NVDA", bars=80)
    out = build_query_context(session, "NVDA 추세 추종 전략 백테스트 해줘")
    assert "백테스트" in out
    assert "NVDA" in out
    assert "보유 비중" in out and "Sharpe" in out
    # Descriptive-only — no buy/sell wording anywhere in the generated line.
    assert find_coercive_term(out) is None
    # No simulation intent → no simulation section.
    assert "백테스트 [" not in build_query_context(session, "안녕하세요")


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
    assert find_coercive_term(action.summary) is None


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
    assert out and find_coercive_term(out) is None


def test_extract_strategy_spec_block() -> None:
    from finskillos.agent.chat import extract_strategy_spec_block

    reply = (
        "이렇게 설계했습니다.\n"
        '```json\n{"strategy_spec": {"ticker": "QQQ", '
        '"entry": {"compare": ["rsi_14", "<", 30]}, '
        '"exit": {"compare": ["rsi_14", ">", 70]}}}\n```'
    )
    cleaned, spec = extract_strategy_spec_block(reply)
    assert spec is not None and spec["ticker"] == "QQQ"
    assert "```" not in cleaned


def test_chat_authors_free_form_spec(monkeypatch, tmp_path) -> None:
    """When the LLM authors a {"strategy_spec": ...} block, the route backtests it
    and returns the inline preview + a ?spec= deep-link."""

    from fastapi.testclient import TestClient

    from api.main import create_app
    from finskillos.agent.chat import ChatReply
    from finskillos.config import reset_settings_cache

    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        seed_default_account(session)
        MarketDataService(
            session, adapter=MockMarketDataAdapter(default_bars=90), universe=["NVDA"]
        ).refresh_bars(["NVDA"])
        SignalService(session).compute_for_universe(["NVDA"])
        session.commit()

    authored = (
        "NVDA에 SMA20 돌파 전략을 설계했어요.\n"
        '```json\n{"strategy_spec": {"name": "SMA20 돌파", "ticker": "NVDA", '
        '"entry": {"cross": ["close", "above", "sma_20"]}, '
        '"exit": {"cross": ["close", "below", "sma_20"]}}}\n```'
    )
    monkeypatch.setattr(
        "api.routes.agent.run_chat",
        lambda *a, **k: ChatReply(reply=authored, provider="stub", ready=True),
    )
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).post(
            "/api/agent/chat",
            json={"messages": [{"role": "user", "content": "SMA20 돌파 전략 설계해줘"}]},
        ).json()
        assert "```" not in body["reply"]
        assert "백테스트" in body["reply"]
        sim = body["simulation"]
        assert sim is not None and sim["ticker"] == "NVDA"
        assert sim["navPath"].startswith("/quant-lab?spec=")
        assert body["proposedAction"]["kind"] == "open_simulation"
        assert find_coercive_term(body["reply"]) is None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_chat_endpoint_runs_simulation_without_the_llm(monkeypatch, tmp_path) -> None:
    """A simulation request is answered deterministically — no provider call — so
    it works even when the model gateway is down."""

    from fastapi.testclient import TestClient

    from api.main import create_app
    from finskillos.config import reset_settings_cache

    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        seed_default_account(session)
        MarketDataService(
            session, adapter=MockMarketDataAdapter(default_bars=90), universe=["NVDA"]
        ).refresh_bars(["NVDA"])
        SignalService(session).compute_for_universe(["NVDA"])
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).post(
            "/api/agent/chat",
            json={"messages": [{"role": "user", "content": "NVDA 추세 추종 전략 시뮬레이션 해줘"}]},
        ).json()
        assert "백테스트" in body["reply"] and "NVDA" in body["reply"]
        action = body["proposedAction"]
        assert action is not None
        assert action["kind"] == "open_simulation"
        assert action["navPath"] == "/quant-lab?strategy=SMA_50_CROSS&ticker=NVDA"
        assert find_coercive_term(body["reply"]) is None
        # Inline mini-chart payload for the chat (price series + markers).
        sim = body["simulation"]
        assert sim is not None
        assert sim["ticker"] == "NVDA"
        assert len(sim["closes"]) == sim["barCount"] > 0
        assert len(sim["exposures"]) == len(sim["closes"])
        assert sim["navPath"] == "/quant-lab?strategy=SMA_50_CROSS&ticker=NVDA"
        for mk in sim["markers"]:
            assert mk["kind"] in {"ENTER", "EXIT"}
            assert 0 <= mk["index"] < len(sim["closes"])

        # Bare intent (no strategy/ticker) → deterministic menu, never the
        # generic LLM-down fallback; offers to open the Quant Lab tab.
        bare = TestClient(create_app()).post(
            "/api/agent/chat",
            json={"messages": [{"role": "user", "content": "퀀트 시뮬레이션 해줘"}]},
        ).json()
        assert "내장 전략" in bare["reply"]
        assert "language model is unreachable" not in bare["reply"]
        assert bare["proposedAction"]["navPath"] == "/quant-lab"
        assert find_coercive_term(bare["reply"]) is None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
