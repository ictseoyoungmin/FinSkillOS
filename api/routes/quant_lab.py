"""GET /api/quant-lab — Quant Simulation Lab (Phase 21.2).

Runs a declarative ``StrategySpec`` over stored historical bars and returns the
descriptive read model (equity vs benchmark curve, simulated exposure windows,
the absorbed METRIC stats). Research / simulation only — never real trading, never
touches live positions or orders. Exposure ON/OFF vocabulary; not-advice caption.

Fixture-first: ``X-FSO-Use-Fixture: 1`` or an unreachable DB returns the
deterministic synthetic backtest; a reachable DB runs the spec on real bars.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures.quant_lab import build_quant_lab_response, quant_lab_fixture
from api.schemas.common import JudgmentHeader, SystemStatus
from api.schemas.quant_lab import (
    QuantLabDataState,
    QuantLabMetrics,
    QuantLabPortfolioPoint,
    QuantLabPortfolioResponse,
    QuantLabResponse,
    QuantLabRunRequest,
    QuantLabSavedList,
    QuantLabSavedSummary,
    QuantLabScreenResponse,
    QuantLabScreenRow,
    QuantLabStrategyOption,
    QuantLabStrategySummary,
)
from finskillos.db.repositories import SavedStrategyRepository
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
    saved: str | None = Query(
        default=None, description="Run a saved (agent-authored) spec by its id."
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> QuantLabResponse:
    if use_fixture:
        return quant_lab_fixture(strategy, ticker=ticker)
    if saved:
        return _read_saved_quant_lab(saved)
    return _read_quant_lab(strategy, ticker)


def _read_saved_quant_lab(saved_id: str) -> QuantLabResponse:
    try:
        sid = uuid.UUID(saved_id)
    except ValueError:
        return _state_response("CUSTOM", None, [], note="저장된 전략 id가 올바르지 않습니다.")
    with get_session_scope() as session:
        if session is None:
            return _state_response("CUSTOM", None, [], note="DB에 연결할 수 없습니다.")
        row = SavedStrategyRepository(session).get(sid)
        if row is None:
            return _state_response("CUSTOM", None, [], note="저장된 전략을 찾을 수 없습니다.")
        try:
            spec = strategy_spec_from_json(row.spec)
        except SpecParseError as exc:
            return _state_response(
                "CUSTOM", row.ticker, [], note=f"저장된 전략 해석 오류: {exc}",
                spec_name=row.name,
            )
        service = SimulationService(session)
        available = service.available_tickers()
        result = service.run_spec(spec)
        if result.bar_count == 0:
            return _state_response(
                "CUSTOM", row.ticker, available,
                note=f"'{row.ticker}'의 저장된 일봉 바가 부족합니다.", spec_name=row.name,
            )
        now = datetime.now(tz=UTC).isoformat()
        regime_covered = any(p.regime for p in result.equity_curve)
        wf = service.walk_forward_spec(spec)
        return build_quant_lab_response(
            result,
            strategy_id="CUSTOM",
            available_tickers=available,
            source="live",
            generated_at=now,
            regime_covered=regime_covered,
            spec=spec,
            walk_forward=wf,
        )


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
        spec = get_strategy(sid)
        wf = (
            service.walk_forward_spec(spec, ticker=ticker)
            if spec is not None
            else []
        )
        return build_quant_lab_response(
            result,
            strategy_id=sid,
            available_tickers=available,
            source="live",
            generated_at=now,
            regime_covered=regime_covered,
            walk_forward=wf,
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
        wf = service.walk_forward_spec(spec, timeframe=payload.timeframe)
        return build_quant_lab_response(
            result,
            strategy_id="CUSTOM",
            walk_forward=wf,
            available_tickers=available,
            source="live",
            generated_at=now,
            regime_covered=regime_covered,
            spec=spec,
        )


def _metrics_vm(m) -> QuantLabMetrics:
    return QuantLabMetrics(
        total_return=m.total_return,
        cagr=m.cagr,
        annual_volatility=m.annual_volatility,
        sharpe=m.sharpe,
        sortino=m.sortino,
        max_drawdown=m.max_drawdown,
        calmar=m.calmar,
        exposure_pct=m.exposure_pct,
        round_trips=m.round_trips,
        win_rate=m.win_rate,
    )


def _portfolio_response(port, strategy_name: str) -> QuantLabPortfolioResponse:
    now = datetime.now(tz=UTC).isoformat()
    if port is None:
        return QuantLabPortfolioResponse(
            generated_at=now,
            system_status=SystemStatus(db="LIVE", guard_count=0),
            strategy_name=strategy_name,
            safety_caption=SIMULATION_CAPTION,
        )
    return QuantLabPortfolioResponse(
        generated_at=now,
        system_status=SystemStatus(db="LIVE", guard_count=0),
        strategy_name=strategy_name,
        source="live",
        tickers=list(port.tickers),
        weight=port.weight,
        curve=[
            QuantLabPortfolioPoint(
                date=p.date,
                strategy=p.strategy,
                benchmark=p.benchmark,
                exposure=p.exposure,
            )
            for p in port.curve
        ],
        metrics=_metrics_vm(port.metrics),
        safety_caption=SIMULATION_CAPTION,
    )


def _portfolio_tickers(service, raw: str | None) -> list[str]:
    if raw:
        named = [t.strip().upper() for t in raw.split(",") if t.strip()]
        if named:
            return named
    return service.available_tickers()[:8]


@router.get(
    "/quant-lab/portfolio",
    response_model=QuantLabPortfolioResponse,
    summary="Equal-weight portfolio of one built-in strategy across tickers.",
)
def quant_lab_portfolio(
    strategy: str | None = Query(default=None),
    tickers: str | None = Query(default=None),
    timeframe: str = Query(default="1d"),
) -> QuantLabPortfolioResponse:
    sid = strategy or DEFAULT_STRATEGY
    spec = get_strategy(sid)
    if spec is None:
        return _portfolio_response(None, sid)
    with get_session_scope() as session:
        if session is None:
            return _portfolio_response(None, spec.name)
        service = SimulationService(session)
        basket = _portfolio_tickers(service, tickers)
        port = service.portfolio_spec(spec, tickers=basket, timeframe=timeframe)
        return _portfolio_response(port, spec.name)


@router.post(
    "/quant-lab/portfolio",
    response_model=QuantLabPortfolioResponse,
    summary="Equal-weight portfolio of an agent-authored free-form strategy.",
)
def quant_lab_portfolio_custom(
    payload: QuantLabRunRequest,
    tickers: str | None = Query(default=None),
) -> QuantLabPortfolioResponse:
    spec_obj = {
        "name": payload.name,
        "description": payload.description,
        "ticker": payload.ticker,
        "entry": payload.entry,
        "exit": payload.exit_,
    }
    try:
        spec = strategy_spec_from_json(spec_obj)
    except SpecParseError:
        return _portfolio_response(None, payload.name or "사용자 전략")
    with get_session_scope() as session:
        if session is None:
            return _portfolio_response(None, spec.name)
        service = SimulationService(session)
        basket = _portfolio_tickers(service, tickers)
        port = service.portfolio_spec(
            spec, tickers=basket, timeframe=payload.timeframe
        )
        return _portfolio_response(port, spec.name)


def _saved_summary(row) -> QuantLabSavedSummary:
    return QuantLabSavedSummary(
        id=str(row.id),
        name=row.name,
        ticker=row.ticker,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


@router.get(
    "/quant-lab/specs",
    response_model=QuantLabSavedList,
    summary="List saved (agent-authored) strategies.",
)
def quant_lab_specs() -> QuantLabSavedList:
    with get_session_scope() as session:
        if session is None:
            return QuantLabSavedList()
        rows = SavedStrategyRepository(session).list_all()
        return QuantLabSavedList(specs=[_saved_summary(r) for r in rows])


@router.post(
    "/quant-lab/specs",
    response_model=QuantLabSavedSummary,
    summary="Save an agent-authored free-form strategy for later re-use.",
)
def quant_lab_save_spec(payload: QuantLabRunRequest) -> QuantLabSavedSummary:
    spec_obj = {
        "name": payload.name,
        "description": payload.description,
        "ticker": payload.ticker,
        "entry": payload.entry,
        "exit": payload.exit_,
    }
    # Validate before persisting so a saved spec always runs.
    try:
        spec = strategy_spec_from_json(spec_obj)
    except SpecParseError as exc:
        raise HTTPException(status_code=400, detail=f"전략 정의 오류: {exc}") from exc
    with get_session_scope() as session:
        if session is None:
            return QuantLabSavedSummary(
                id="", name=spec.name, ticker=spec.universe[0], created_at=""
            )
        row = SavedStrategyRepository(session).create(
            name=spec.name, ticker=spec.universe[0], spec=spec_obj
        )
        session.commit()
        return _saved_summary(row)


@router.delete(
    "/quant-lab/specs/{spec_id}",
    summary="Delete a saved strategy.",
)
def quant_lab_delete_spec(spec_id: str) -> dict:
    try:
        sid = uuid.UUID(spec_id)
    except ValueError:
        return {"ok": False}
    with get_session_scope() as session:
        if session is None:
            return {"ok": False}
        ok = SavedStrategyRepository(session).delete(sid)
        session.commit()
        return {"ok": ok}


def _screen_response(results, strategy_name: str) -> QuantLabScreenResponse:
    rows = [
        QuantLabScreenRow(
            ticker=r.ticker,
            bar_count=r.bar_count,
            total_return=r.metrics.total_return,
            sharpe=r.metrics.sharpe,
            max_drawdown=r.metrics.max_drawdown,
            exposure_pct=r.metrics.exposure_pct,
            round_trips=r.metrics.round_trips,
        )
        for r in results
    ]
    rows.sort(
        key=lambda x: x.total_return if x.total_return is not None else float("-inf"),
        reverse=True,
    )
    return QuantLabScreenResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        system_status=SystemStatus(db="LIVE", guard_count=0),
        strategy_name=strategy_name,
        source="live",
        rows=rows,
        safety_caption=SIMULATION_CAPTION,
    )


def _empty_screen(strategy_name: str, db: str = "LIVE") -> QuantLabScreenResponse:
    return QuantLabScreenResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        system_status=SystemStatus(db=db, guard_count=0),
        strategy_name=strategy_name,
        source="live",
        rows=[],
        safety_caption=SIMULATION_CAPTION,
    )


@router.get(
    "/quant-lab/screen",
    response_model=QuantLabScreenResponse,
    summary="Run one built-in strategy across many tickers, ranked (multi-asset).",
)
def quant_lab_screen(
    strategy: str | None = Query(default=None),
    timeframe: str = Query(default="1d"),
) -> QuantLabScreenResponse:
    sid = strategy or DEFAULT_STRATEGY
    spec = get_strategy(sid)
    if spec is None:
        return _empty_screen(sid)
    with get_session_scope() as session:
        if session is None:
            return _empty_screen(spec.name, db="MISSING")
        results = SimulationService(session).screen_spec(spec, timeframe=timeframe)
        return _screen_response(results, spec.name)


@router.post(
    "/quant-lab/screen",
    response_model=QuantLabScreenResponse,
    summary="Run an agent-authored free-form strategy across many tickers, ranked.",
)
def quant_lab_screen_custom(payload: QuantLabRunRequest) -> QuantLabScreenResponse:
    spec_obj = {
        "name": payload.name,
        "description": payload.description,
        "ticker": payload.ticker,
        "entry": payload.entry,
        "exit": payload.exit_,
    }
    try:
        spec = strategy_spec_from_json(spec_obj)
    except SpecParseError:
        return _empty_screen(payload.name or "사용자 전략")
    with get_session_scope() as session:
        if session is None:
            return _empty_screen(spec.name, db="MISSING")
        results = SimulationService(session).screen_spec(
            spec, timeframe=payload.timeframe
        )
        return _screen_response(results, spec.name)


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
