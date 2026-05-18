"""Slice 05 — RegimeService integration tests.

Seeds the slice-02/04 repositories with indicator snapshots and the
latest VIX bar, then verifies that:

* `RegimeService.build_input` reads SPY/QQQ/SMH trend + RSI, plus
  VIX close, plus DXY/US10Y trend, into a `RegimeInput`.
* `evaluate_today_regime` produces a deterministic `RegimeOutput`
  whose `regime` matches the seeded indicator picture.
* Persistence is wired correctly — calling `evaluate_today_regime`
  twice at the same `snapshot_time` upserts a single `market_regimes`
  row (no constraint violations).
* Missing ticker data does not crash; the service falls through to
  `UNKNOWN` and `latest_close` returning `None` is tolerated.
* The service output never carries buy/sell wording (SAFE-AC-001).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.data_sources.dto import IndicatorSnapshotDTO, MarketBarDTO
from finskillos.db.repositories import (
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
)
from finskillos.regime import FORBIDDEN_WORDS, RegimeOutput
from finskillos.regime.regime_rules import (
    REGIME_HEALTHY_BULL,
    REGIME_RISK_OFF,
    REGIME_RISK_ON_OVERHEAT,
    REGIME_UNKNOWN,
)
from finskillos.services.regime_service import RegimeService

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_indicator(
    session: Session,
    ticker: str,
    *,
    snapshot_time: datetime,
    trend_state: str | None,
    rsi_14: Decimal | None,
    momentum_score: Decimal | None = None,
    timeframe: str = "1d",
) -> None:
    repo = IndicatorRepository(session)
    repo.upsert_snapshot(
        IndicatorSnapshotDTO(
            ticker=ticker,
            timeframe=timeframe,
            snapshot_time=snapshot_time,
            rsi_14=rsi_14,
            trend_state=trend_state,
            momentum_score=momentum_score,
        )
    )


def _seed_vix_bar(
    session: Session,
    *,
    bar_time: datetime,
    close: Decimal,
    timeframe: str = "1d",
) -> None:
    MarketRepository(session).upsert_bar(
        MarketBarDTO(
            ticker="VIX",
            timeframe=timeframe,
            bar_time=bar_time,
            open=close,
            high=close,
            low=close,
            close=close,
            volume=Decimal("0"),
            source="test",
        )
    )


def _seed_overheat_picture(session: Session, *, ts: datetime) -> None:
    """RSI > 70 on QQQ/SMH/SPY + bullish trend + low VIX → RISK_ON_OVERHEAT."""

    for ticker, rsi in (
        ("SPY", Decimal("70.5")),
        ("QQQ", Decimal("74")),
        ("SMH", Decimal("77")),
    ):
        _seed_indicator(
            session,
            ticker,
            snapshot_time=ts,
            trend_state="BULLISH",
            rsi_14=rsi,
            momentum_score=Decimal("18"),
        )
    _seed_indicator(session, "DXY", snapshot_time=ts, trend_state="NEUTRAL", rsi_14=Decimal("50"))
    _seed_indicator(session, "US10Y", snapshot_time=ts, trend_state="NEUTRAL", rsi_14=Decimal("50"))
    _seed_vix_bar(session, bar_time=ts, close=Decimal("13"))


def _seed_healthy_bull_picture(session: Session, *, ts: datetime) -> None:
    _seed_indicator(session, "SPY", snapshot_time=ts, trend_state="BULLISH", rsi_14=Decimal("58"))
    _seed_indicator(session, "QQQ", snapshot_time=ts, trend_state="BULLISH", rsi_14=Decimal("60"))
    _seed_indicator(
        session, "SMH", snapshot_time=ts, trend_state="WEAK_BULLISH", rsi_14=Decimal("55")
    )
    _seed_indicator(session, "DXY", snapshot_time=ts, trend_state="NEUTRAL", rsi_14=Decimal("50"))
    _seed_indicator(session, "US10Y", snapshot_time=ts, trend_state="NEUTRAL", rsi_14=Decimal("50"))
    _seed_vix_bar(session, bar_time=ts, close=Decimal("14"))


def _seed_risk_off_picture(session: Session, *, ts: datetime) -> None:
    _seed_indicator(session, "SPY", snapshot_time=ts, trend_state="BEARISH", rsi_14=Decimal("35"))
    _seed_indicator(
        session, "QQQ", snapshot_time=ts, trend_state="WEAK_BEARISH", rsi_14=Decimal("38")
    )
    _seed_indicator(session, "SMH", snapshot_time=ts, trend_state="BEARISH", rsi_14=Decimal("33"))
    _seed_indicator(session, "DXY", snapshot_time=ts, trend_state="BULLISH", rsi_14=Decimal("60"))
    _seed_indicator(
        session, "US10Y", snapshot_time=ts, trend_state="BULLISH", rsi_14=Decimal("62")
    )
    _seed_vix_bar(session, bar_time=ts, close=Decimal("28"))


def _assert_no_forbidden_wording(output: RegimeOutput) -> None:
    blob = " ".join(
        [
            output.regime,
            output.decision_mode,
            output.risk_level,
            output.summary,
            output.what_happened,
            output.what_it_means,
            *output.watch_next,
            *output.positive_factors,
            *output.risk_factors,
        ]
    )
    for forbidden in FORBIDDEN_WORDS:
        assert forbidden not in blob, f"forbidden term {forbidden!r}: {blob!r}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_service_builds_input_from_latest_indicators(db_session: Session) -> None:
    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_overheat_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    inputs = service.build_input()

    assert inputs.spy_trend_state == "BULLISH"
    assert inputs.qqq_trend_state == "BULLISH"
    assert inputs.smh_trend_state == "BULLISH"
    assert inputs.spy_rsi_14 == Decimal("70.5000")
    assert inputs.qqq_rsi_14 == Decimal("74.0000")
    assert inputs.smh_rsi_14 == Decimal("77.0000")
    assert inputs.vix_close == Decimal("13")
    assert inputs.dxy_trend_state == "NEUTRAL"
    assert inputs.us10y_trend_state == "NEUTRAL"


def test_service_classifies_overheat_picture(db_session: Session) -> None:
    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_overheat_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    output = service.evaluate_today_regime(snapshot_time=ts)

    assert output.regime == REGIME_RISK_ON_OVERHEAT
    assert output.decision_mode == "HOLD_WINNERS"
    assert Decimal("0") <= output.confidence <= Decimal("100")
    _assert_no_forbidden_wording(output)


def test_service_classifies_healthy_bull_picture(db_session: Session) -> None:
    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_healthy_bull_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    output = service.evaluate_today_regime(snapshot_time=ts)

    assert output.regime == REGIME_HEALTHY_BULL
    _assert_no_forbidden_wording(output)


def test_service_classifies_risk_off_picture(db_session: Session) -> None:
    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_risk_off_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    output = service.evaluate_today_regime(snapshot_time=ts)

    assert output.regime == REGIME_RISK_OFF
    assert output.decision_mode == "DEFENSIVE"
    _assert_no_forbidden_wording(output)


def test_service_missing_data_returns_unknown_without_crashing(
    db_session: Session,
) -> None:
    """FAIL-AC-004 — sparse indicator history must not raise."""

    service = RegimeService(db_session)
    output = service.evaluate_today_regime(
        snapshot_time=datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    )

    assert output.regime == REGIME_UNKNOWN
    assert output.confidence == Decimal("0")
    _assert_no_forbidden_wording(output)


def test_service_persists_and_upserts_market_regime_row(db_session: Session) -> None:
    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_healthy_bull_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    service.evaluate_today_regime(snapshot_time=ts)

    # Re-running at the same snapshot_time must upsert, not duplicate.
    service.evaluate_today_regime(snapshot_time=ts)

    rows = MarketRegimeRepository(db_session).list_recent(limit=10)
    assert len(rows) == 1
    assert rows[0].regime == REGIME_HEALTHY_BULL
    assert rows[0].snapshot_time.replace(tzinfo=UTC) == ts
    # evidence + watch_next persisted as JSON-friendly structures.
    assert isinstance(rows[0].watch_next, list)
    assert isinstance(rows[0].evidence, dict)
    assert rows[0].evidence["spy_trend_state"] == "BULLISH"
    # 05-cleanup: positive/risk factors persisted as JSON lists.
    assert isinstance(rows[0].positive_factors, list)
    assert isinstance(rows[0].risk_factors, list)
    assert rows[0].positive_factors or rows[0].risk_factors


def test_service_upsert_updates_factors_when_indicators_change(
    db_session: Session,
) -> None:
    """Same snapshot_time + rule_version with new indicators must overwrite factors."""

    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_healthy_bull_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    service.evaluate_today_regime(snapshot_time=ts)
    first = MarketRegimeRepository(db_session).latest()
    assert first is not None
    first_positive = list(first.positive_factors or [])
    first_risk = list(first.risk_factors or [])

    # Reseed the same tickers with an overheat picture and re-evaluate.
    _seed_overheat_picture(db_session, ts=ts)
    service.evaluate_today_regime(snapshot_time=ts)

    rows = MarketRegimeRepository(db_session).list_recent(limit=10)
    assert len(rows) == 1, "upsert must not duplicate at same (snapshot_time, rule_version)"
    updated = rows[0]
    assert updated.regime == REGIME_RISK_ON_OVERHEAT
    # Factor lists were rewritten — the new payload must reflect the
    # overheat narrative, not the original healthy-bull narrative.
    assert (
        list(updated.positive_factors or []) != first_positive
        or list(updated.risk_factors or []) != first_risk
    )
    assert any(
        "RSI" in f or "과열" in f for f in (updated.risk_factors or [])
    )


def test_service_persist_false_skips_db_write(db_session: Session) -> None:
    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    _seed_healthy_bull_picture(db_session, ts=ts)

    service = RegimeService(db_session)
    service.evaluate_today_regime(snapshot_time=ts, persist=False)

    assert service.get_latest_regime() is None


def test_service_get_latest_returns_most_recent_classification(
    db_session: Session,
) -> None:
    first_ts = datetime(2026, 5, 17, 21, 0, tzinfo=UTC)
    second_ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)

    _seed_healthy_bull_picture(db_session, ts=first_ts)
    service = RegimeService(db_session)
    service.evaluate_today_regime(snapshot_time=first_ts)

    # Overwrite the same tickers with overheat values for the next day.
    _seed_overheat_picture(db_session, ts=second_ts)
    service.evaluate_today_regime(snapshot_time=second_ts)

    latest = service.get_latest_regime()
    assert latest is not None
    assert latest.regime == REGIME_RISK_ON_OVERHEAT
    history = service.get_regime_history(limit=5)
    assert [row.regime for row in history] == [
        REGIME_RISK_ON_OVERHEAT,
        REGIME_HEALTHY_BULL,
    ]


def test_service_tolerates_missing_vix_bar(db_session: Session) -> None:
    """If VIX bars haven't been collected yet, build_input must still return."""

    ts = datetime(2026, 5, 18, 21, 0, tzinfo=UTC)
    # Seed indices but skip VIX entirely.
    _seed_indicator(
        db_session, "SPY", snapshot_time=ts, trend_state="BULLISH", rsi_14=Decimal("58")
    )
    _seed_indicator(
        db_session, "QQQ", snapshot_time=ts, trend_state="BULLISH", rsi_14=Decimal("60")
    )
    _seed_indicator(
        db_session, "SMH", snapshot_time=ts, trend_state="WEAK_BULLISH", rsi_14=Decimal("55")
    )

    service = RegimeService(db_session)
    inputs = service.build_input()
    assert inputs.vix_close is None

    # And the classifier should still produce a valid output, not raise.
    output = service.evaluate_today_regime(snapshot_time=ts, persist=False)
    assert output.regime in {REGIME_HEALTHY_BULL, REGIME_UNKNOWN}
    _assert_no_forbidden_wording(output)
