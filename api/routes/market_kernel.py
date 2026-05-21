"""GET /api/market-kernel — Slice 13.7.

Fixture-first wrapper around the existing Streamlit Market Kernel
view-model output (``finskillos.ui.view_models.symbol_lab_vm``-style
read model). The route is wired so a future slice can switch to live
DB by delegating to the underlying market / indicator / event-risk
services, but the default response stays fixture-first so the React
shell + Playwright visual baseline remain deterministic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import use_fixture_flag
from api.fixtures import market_kernel_fixture
from api.schemas.market_kernel import MarketKernelResponse

router = APIRouter(tags=["market-kernel"])


@router.get(
    "/market-kernel",
    response_model=MarketKernelResponse,
    summary="Market Kernel snapshot for a single ticker (fixture-first in v0).",
)
def market_kernel(
    ticker: str | None = Query(
        default=None,
        description=(
            "Uppercased focus ticker (NVDA / TSLA / AAPL / MSFT / SMH). "
            "Defaults to NVDA when omitted. Unknown tickers return a "
            "MISSING-status payload with a setup hint."
        ),
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> MarketKernelResponse:
    payload = market_kernel_fixture(ticker)
    if use_fixture:
        payload.source = "fixture"
    return payload


__all__ = ["router"]
