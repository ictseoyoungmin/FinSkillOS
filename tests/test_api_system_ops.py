"""Slice 13.8 — FastAPI /api/system-ops contract tests.

Covers:

* The GET protocol catalogue (camelCase shape, safe wording).
* Every POST /api/system-ops/<protocol> endpoint returns a
  structured ``ProtocolRunResult`` even in fixture-first mode (no
  DB session available) — the API contract forbids HTML / raw stack
  trace responses.
* Forbidden execution captions never appear in protocol metadata.
"""

from __future__ import annotations

import json
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.data_sources import MockMarketDataAdapter
from finskillos.db.base import Base
from finskillos.db.repositories import (
    AccountRepository,
    IndicatorRepository,
    MarketRepository,
    NewsArticleRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.services.market_data_service import MarketDataService

_PROTOCOL_KEYS = {
    "seed_sample_account",
    "refresh_news",
    "refresh_market_data",
    "calculate_indicators",
    "recompute_regime",
    "run_risk_guards",
    "seed_sample_events",
}

_POST_ENDPOINTS = (
    ("/api/system-ops/seed-sample-account", "seed_sample_account"),
    ("/api/system-ops/refresh-news", "refresh_news"),
    ("/api/system-ops/refresh-market-data", "refresh_market_data"),
    ("/api/system-ops/calculate-indicators", "calculate_indicators"),
    ("/api/system-ops/recompute-regime", "recompute_regime"),
    ("/api/system-ops/run-risk-guards", "run_risk_guards"),
    ("/api/system-ops/seed-sample-events", "seed_sample_events"),
)

_FORBIDDEN_WORDS = (
    "buy",
    "sell",
    "execute",
    "place order",
    "trade now",
    "지금 사라",
    "지금 팔아라",
    "매수",
    "매도",
)


def _client() -> TestClient:
    return TestClient(create_app())


def test_system_ops_get_returns_full_payload() -> None:
    response = _client().get("/api/system-ops")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "protocols",
        "dataSources",
        "recentProtocolRuns",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP
    assert {p["key"] for p in body["protocols"]} == _PROTOCOL_KEYS


def test_system_ops_protocols_have_camelcase_fields() -> None:
    body = _client().get("/api/system-ops").json()
    expected_fields = {
        "key",
        "title",
        "description",
        "idempotencyNote",
        "buttonLabel",
        "confirmLabel",
        "tone",
    }
    for protocol in body["protocols"]:
        assert expected_fields.issubset(protocol.keys()), protocol


def test_system_ops_data_sources_use_safe_status_values() -> None:
    body = _client().get("/api/system-ops").json()
    assert len(body["dataSources"]) >= 3
    for pill in body["dataSources"]:
        assert pill["status"] in {"LIVE", "FIXTURE", "MISSING"}


def test_system_ops_safety_caption_excludes_trading() -> None:
    body = _client().get("/api/system-ops").json()
    caption = body["safetyCaption"].lower()
    assert "operational" in caption
    assert "no trading" in caption


def test_system_ops_payload_contains_no_forbidden_wording() -> None:
    raw = json.dumps(_client().get("/api/system-ops").json()).lower()
    for forbidden in _FORBIDDEN_WORDS:
        assert forbidden not in raw, (
            f"System Ops payload leaks forbidden wording: {forbidden!r}"
        )


def test_system_ops_post_endpoints_return_structured_json() -> None:
    client = _client()
    for path, expected_key in _POST_ENDPOINTS:
        response = client.post(path)
        # Response is always JSON — never HTML, never a 5xx with a
        # raw stack trace.
        assert response.status_code == 200, (
            f"{path} responded {response.status_code}: {response.text}"
        )
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        assert body["protocol"] == expected_key
        assert body["status"] in {"OK", "NOOP", "ERROR"}
        assert "message" in body and isinstance(body["message"], str)
        assert "ranAt" in body and body["ranAt"]
        # No raw stack-trace material in the message.
        for marker in ("Traceback", "File \"", "line "):
            assert marker not in body["message"], (
                f"{path} message contains stack-trace marker {marker!r}"
            )


def test_system_ops_post_endpoints_use_safe_messages() -> None:
    client = _client()
    for path, _ in _POST_ENDPOINTS:
        body = client.post(path).json()
        blob = (body["message"] + " " + body.get("detail", "")).lower()
        for forbidden in _FORBIDDEN_WORDS:
            assert forbidden not in blob, (
                f"{path} message leaks forbidden wording: {forbidden!r}"
            )


def test_use_fixture_header_is_accepted_on_system_ops() -> None:
    response = _client().get(
        "/api/system-ops", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_system_ops_protocol_runs_are_audited_to_jsonl(monkeypatch, tmp_path) -> None:
    audit_path = tmp_path / "ops_runs.jsonl"
    monkeypatch.setenv("FINSKILLOS_SYSTEM_OPS_AUDIT_LOG", str(audit_path))

    client = _client()
    post_body = client.post("/api/system-ops/seed-sample-account").json()
    assert post_body["protocol"] == "seed_sample_account"

    assert audit_path.exists()
    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 1
    raw_record = json.loads(audit_lines[0])
    assert raw_record["protocol"] == "seed_sample_account"
    assert raw_record["status"] in {"OK", "NOOP", "ERROR"}
    assert raw_record["dbStatus"] in {"LIVE", "MISSING"}
    assert raw_record["source"] in {"fixture", "live"}

    get_body = client.get("/api/system-ops").json()
    assert get_body["recentProtocolRuns"][0]["protocol"] == "seed_sample_account"
    assert get_body["recentProtocolRuns"][0]["ranAt"] == post_body["ranAt"]


def test_refresh_market_data_protocol_writes_mock_bars(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "mock")
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_TICKERS", "SPY,QQQ")
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-market-data").json()

        assert body["protocol"] == "refresh_market_data"
        assert body["status"] == "OK"
        assert "2 symbols available" in body["message"]
        assert "bars=" in body["detail"]

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            repo = MarketRepository(session)
            assert repo.count_for("SPY", "1d") > 0
            assert repo.count_for("QQQ", "1d") > 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_seed_sample_account_repairs_snapshot_only_seed_state(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account",
            target_value=100000000,
        )
        PortfolioRepository(session).create_snapshot(
            account_id=account.id,
            snapshot_date=date(2026, 5, 27),
            total_value=57000000,
            cash_value=7000000,
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/seed-sample-account").json()

        assert body["protocol"] == "seed_sample_account"
        assert body["status"] == "OK"
        assert "positions_created=5" in body["detail"]

        with factory() as session:
            positions = PositionRepository(session).list_for_account(account.id)
            assert len(positions) == 5
            assert sum(p.market_value for p in positions) == 50000000
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_market_data_protocol_rejects_unknown_adapter(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "unknown")
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-market-data").json()

        assert body["protocol"] == "refresh_market_data"
        assert body["status"] == "ERROR"
        assert "Unsupported adapter" in body["message"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_news_protocol_ingests_configured_rss_feed(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    feed_path = tmp_path / "feed.xml"
    feed_path.write_text(
        """\
<rss version="2.0">
  <channel>
    <title>Market Desk</title>
    <item>
      <title>TSLA delivery numbers top expectations</title>
      <link>https://news.example.com/tsla-deliveries</link>
      <pubDate>Tue, 26 May 2026 12:30:00 GMT</pubDate>
      <description>TSLA delivery update was strong.</description>
    </item>
  </channel>
</rss>
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_NEWS_REFRESH_ADAPTER", "rss")
    monkeypatch.setenv("FINSKILLOS_NEWS_RSS_FEEDS", feed_path.resolve().as_uri())
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-news").json()

        assert body["protocol"] == "refresh_news"
        assert body["status"] == "OK"
        assert "1 articles ingested" in body["message"]
        assert "feeds=1" in body["detail"]
        assert "generated=False" in body["detail"]

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            rows = NewsArticleRepository(session).latest()
            assert len(rows) == 1
            assert rows[0].url == "https://news.example.com/tsla-deliveries"
            assert rows[0].summary == "TSLA delivery update was strong."
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_calculate_indicators_protocol_writes_latest_snapshots(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        MarketDataService(
            session,
            adapter=MockMarketDataAdapter(default_bars=40),
            universe=["SPY", "QQQ"],
        ).refresh_bars(["SPY", "QQQ"])
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_INDICATOR_REFRESH_TICKERS", "SPY,QQQ")
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/calculate-indicators").json()

        assert body["protocol"] == "calculate_indicators"
        assert body["status"] == "OK"
        assert "2 symbols available" in body["message"]
        assert "snapshots=2" in body["detail"]

        with factory() as session:
            repo = IndicatorRepository(session)
            assert repo.latest_for("SPY", "1d") is not None
            assert repo.latest_for("QQQ", "1d") is not None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_calculate_indicators_protocol_noops_without_bars(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_INDICATOR_REFRESH_TICKERS", "SPY")
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/calculate-indicators").json()

        assert body["protocol"] == "calculate_indicators"
        assert body["status"] == "NOOP"
        assert "failed=1" in body["detail"]
        assert "failedSymbols=SPY" in body["detail"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
