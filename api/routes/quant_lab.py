"""GET /api/quant-lab — Quant Simulation Lab (Phase 21.2).

Runs a declarative ``StrategySpec`` over stored historical bars and returns the
descriptive read model (equity vs benchmark curve, simulated exposure windows,
the absorbed METRIC stats). Research / simulation only — never real trading, never
touches live positions or orders. Exposure ON/OFF vocabulary; not-advice caption.

Fixture-first: ``X-FSO-Use-Fixture: 1`` or an unreachable DB returns the
deterministic synthetic backtest; a reachable DB runs the spec on real bars.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures.quant_lab import build_quant_lab_response, quant_lab_fixture
from api.schemas.common import JudgmentHeader, SystemStatus
from api.schemas.quant_lab import (
    QuantLabDataState,
    QuantLabMetrics,
    QuantLabResponse,
    QuantLabRunRequest,
    QuantLabStrategyOption,
    QuantLabStrategySummary,
)
from finskillos.services.simulation_service import SimulationService, list_strategies
from finskillos.simulation import SIMULATION_CAPTION
from finskillos.simulation.library import condition_text, get_strategy
from finskillos.simulation.spec_json import SpecParseError, strategy_spec_from_json

router = APIRouter(tags=["quant-lab"])
UTC = timezone.utc
DEFAULT_STRATEGY = "SMA_50_CROSS"


@router.get(
    "/quant-lab",
    response_model=QuantLabResponse,
    summary="Run a descriptive strategy simulation over stored historical bars.",
)
def quant_lab(
    strategy: str | None = Query(
        default=None,
        description="Built-in strategy id (defaults to SMA_50_CROSS).",
    ),
    ticker: str | None = Query(
        default=None,
        description="Override the strategy's default ticker (must have stored bars).",
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> QuantLabResponse:
    if use_fixture:
        return quant_lab_fixture(strategy, ticker=ticker)
    return _read_quant_lab(strategy, ticker)


def _read_quant_lab(
    strategy: str | None, ticker: str | None
) -> QuantLabResponse:
    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(quant_lab_fixture(strategy, ticker=ticker))

        sid = strategy or DEFAULT_STRATEGY
        service = SimulationService(session)
        available = service.available_tickers()
        try:
            result = service.run(sid, ticker=ticker)
        except Exception as exc:  # live read failed → explicit live-error state
            return _state_response(
                sid,
                ticker,
                available,
                note=f"라이브 시뮬레이션 실행 실패 ({type(exc).__name__}). 픽스처로 대체하지 않음.",
            )
        if result is None or result.bar_count == 0:
            return _state_response(
                sid,
                ticker,
                available,
                note="라이브 DB는 연결됐으나 이 전략/티커의 저장된 바가 부족합니다.",
            )
        now = datetime.now(tz=UTC).isoformat()
        regime_covered = any(p.regime for p in result.equity_curve)
        return build_quant_lab_response(
            result,
            strategy_id=sid,
            available_tickers=available,
            source="live",
            generated_at=now,
            regime_covered=regime_covered,
        )


@router.post(
    "/quant-lab/run",
    response_model=QuantLabResponse,
    summary="Backtest an agent-authored free-form strategy over stored bars.",
)
def quant_lab_run(payload: QuantLabRunRequest) -> QuantLabResponse:
    spec_obj = {
        "name": payload.name,
        "description": payload.description,
        "ticker": payload.ticker,
        "entry": payload.entry,
        "exit": payload.exit_,
    }
    try:
        spec = strategy_spec_from_json(spec_obj)
    except SpecParseError as exc:
        return _state_response(
            "CUSTOM",
            payload.ticker,
            [],
            note=f"전략 정의 오류: {exc}",
            spec_name=payload.name or "사용자 전략",
        )
    with get_session_scope() as session:
        if session is None:
            return _state_response(
                "CUSTOM", payload.ticker, [], note="DB에 연결할 수 없습니다.",
                spec_name=spec.name,
            )
        service = SimulationService(session)
        available = service.available_tickers()
        try:
            result = service.run_spec(spec, timeframe=payload.timeframe)
        except Exception as exc:  # live read failed → explicit live-error state
            return _state_response(
                "CUSTOM", payload.ticker, available,
                note=f"백테스트 실행 실패 ({type(exc).__name__}).", spec_name=spec.name,
            )
        if result.bar_count == 0:
            return _state_response(
                "CUSTOM", payload.ticker, available,
                note=f"'{payload.ticker.upper()}'의 저장된 일봉 바가 부족합니다.",
                spec_name=spec.name,
            )
        now = datetime.now(tz=UTC).isoformat()
        regime_covered = any(p.regime for p in result.equity_curve)
        return build_quant_lab_response(
            result,
            strategy_id="CUSTOM",
            available_tickers=available,
            source="live",
            generated_at=now,
            regime_covered=regime_covered,
            spec=spec,
        )


def _state_response(
    strategy_id: str,
    ticker: str | None,
    available_tickers: list[str],
    *,
    note: str,
    spec_name: str | None = None,
) -> QuantLabResponse:
    """An explicit live-empty / live-error payload (source=live, never fixture)."""

    spec = get_strategy(strategy_id)
    title = spec.name if spec is not None else (spec_name or strategy_id)
    tk = (ticker or (spec.universe[0] if spec is not None else "")).upper()
    return QuantLabResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        system_status=SystemStatus(db="LIVE", guard_count=0),
        judgment=JudgmentHeader(
            eyebrow="QUANT LAB · 백테스트",
            title=title,
            accent=tk,
            summary=note,
            confidence=0,
        ),
        strategy=QuantLabStrategySummary(
            id=strategy_id,
            name=title,
            description=spec.description if spec is not None else "",
            ticker=tk,
            entry_text=condition_text(spec.entry) if spec is not None else "",
            exit_text=condition_text(spec.exit) if spec is not None else "",
        ),
        metrics=QuantLabMetrics(),
        equity_curve=[],
        exposure_segments=[],
        available_strategies=[
            QuantLabStrategyOption(**option) for option in list_strategies()
        ],
        available_tickers=available_tickers,
        safety_caption=SIMULATION_CAPTION,
        data_state=QuantLabDataState(
            source="live",
            ticker=tk,
            bar_count=0,
            regime_covered=False,
            data_note=note,
        ),
    )
