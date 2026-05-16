"""Generate synthetic FinSkillOS sample datasets.

The generated files implement AUTO-SAMPLE-001 through AUTO-SAMPLE-003 from
`FinSkillOS_skills/skills/05_vibecoding_automation.md` and include an
allocation sample for DATA-STRUCT-004.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"
SEED = 20260430


def business_dates(periods: int = 252) -> pd.DatetimeIndex:
    return pd.bdate_range("2025-01-02", periods=periods)


def price_path(
    rng: np.random.Generator,
    periods: int,
    start: float,
    drift: float,
    volatility: float,
    shock_start: int | None = None,
    shock_end: int | None = None,
    shock_return: float = 0.0,
) -> np.ndarray:
    returns = rng.normal(loc=drift, scale=volatility, size=periods)
    if shock_start is not None and shock_end is not None:
        returns[shock_start:shock_end] += shock_return
    prices = start * np.cumprod(1.0 + returns)
    return np.round(prices, 2)


def write_single_asset(rng: np.random.Generator) -> None:
    dates = business_dates()
    close = price_path(
        rng,
        periods=len(dates),
        start=100.0,
        drift=0.00035,
        volatility=0.011,
        shock_start=115,
        shock_end=142,
        shock_return=-0.006,
    )
    volume_base = rng.normal(loc=1_250_000, scale=180_000, size=len(dates))
    volume = np.maximum(volume_base, 450_000).round().astype(int)
    df = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "close": close,
            "volume": volume,
        }
    )
    df.to_csv(SAMPLE_DIR / "single_asset_price.csv", index=False)


def write_multi_asset(rng: np.random.Generator) -> None:
    dates = business_dates()
    assets = {
        "Growth Equity": {"start": 100.0, "drift": 0.00055, "vol": 0.014, "shock": -0.004},
        "Defensive Bond": {"start": 100.0, "drift": 0.00012, "vol": 0.0035, "shock": 0.0005},
        "Commodity": {"start": 100.0, "drift": 0.00025, "vol": 0.010, "shock": 0.002},
        "Global Tech": {"start": 100.0, "drift": 0.00070, "vol": 0.018, "shock": -0.006},
    }
    rows: list[dict[str, object]] = []
    market_factor = rng.normal(loc=0.0002, scale=0.006, size=len(dates))

    for asset, params in assets.items():
        idiosyncratic = rng.normal(loc=params["drift"], scale=params["vol"], size=len(dates))
        returns = 0.45 * market_factor + 0.55 * idiosyncratic
        returns[125:148] += params["shock"]
        prices = np.round(params["start"] * np.cumprod(1.0 + returns), 2)
        for date, price in zip(dates, prices):
            rows.append({"date": date.strftime("%Y-%m-%d"), "asset": asset, "price": price})

    pd.DataFrame(rows).to_csv(SAMPLE_DIR / "multi_asset_portfolio.csv", index=False)


def write_mixed_schema(rng: np.random.Generator) -> None:
    dates = business_dates()
    assets = {
        "Alpha Income Fund": {"start": 1000.0, "drift": 0.00018, "vol": 0.004},
        "Beta Growth ETF": {"start": 1000.0, "drift": 0.00048, "vol": 0.012},
        "Gamma Balanced": {"start": 1000.0, "drift": 0.00030, "vol": 0.007},
    }
    rows: list[dict[str, object]] = []
    for asset, params in assets.items():
        nav = price_path(
            rng,
            periods=len(dates),
            start=params["start"],
            drift=params["drift"],
            volatility=params["vol"],
            shock_start=110,
            shock_end=132,
            shock_return=-0.002 if "Growth" in asset else -0.0005,
        )
        trading_amount = rng.normal(loc=850_000_000, scale=180_000_000, size=len(dates))
        trading_amount = np.maximum(trading_amount, 120_000_000).round().astype(int)
        for date, value, amount in zip(dates, nav, trading_amount):
            rows.append(
                {
                    "trade_dt": date.strftime("%Y-%m-%d"),
                    "ticker_name": asset,
                    "nav_value": value,
                    "trading_amount": amount,
                }
            )

    pd.DataFrame(rows).to_csv(SAMPLE_DIR / "mixed_schema_assets.csv", index=False)


def write_allocation_sample() -> None:
    df = pd.DataFrame(
        [
            {"asset": "US Equity Core", "weight": 0.34, "sector": "Equity", "region": "North America"},
            {"asset": "Global Tech Tilt", "weight": 0.22, "sector": "Equity", "region": "Global"},
            {"asset": "Investment Grade Bond", "weight": 0.18, "sector": "Fixed Income", "region": "Global"},
            {"asset": "Short Duration Bond", "weight": 0.10, "sector": "Fixed Income", "region": "North America"},
            {"asset": "Commodity Basket", "weight": 0.08, "sector": "Commodity", "region": "Global"},
            {"asset": "Cash Reserve", "weight": 0.08, "sector": "Cash", "region": "Local"},
        ]
    )
    df.to_csv(SAMPLE_DIR / "allocation_sample.csv", index=False)


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    write_single_asset(rng)
    write_multi_asset(rng)
    write_mixed_schema(rng)
    write_allocation_sample()


if __name__ == "__main__":
    main()
