"""Optional price-history enrichment for holdings snapshots."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional dependency path
    yf = None


HOLDINGS_MARKERS = {
    "quantity",
    "avg_buy_price",
    "current_price",
    "market_value",
    "cost_basis",
    "unrealized_pnl",
    "unrealized_return",
    "portfolio_weight",
    "effective_exposure",
}


def is_holdings_snapshot(df: pd.DataFrame | None) -> bool:
    """Return True when a dataframe looks like a current holdings snapshot."""

    if df is None or df.empty:
        return False
    names = {str(column).lower() for column in df.columns}
    has_ticker = bool(names & {"ticker", "yahoo_ticker", "symbol"})
    has_weight_or_value = bool(names & {"portfolio_weight", "effective_exposure_weight", "market_value_net", "market_value_gross"})
    has_marker = any(any(marker in name for marker in HOLDINGS_MARKERS) for name in names)
    return has_ticker and has_weight_or_value and has_marker


def _first_existing(row: pd.Series, columns: tuple[str, ...]) -> Any:
    for column in columns:
        if column in row.index and pd.notna(row[column]) and str(row[column]).strip():
            return row[column]
    return None


def _holding_ticker_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        yahoo_ticker = _first_existing(row, ("yahoo_ticker", "ticker", "symbol"))
        if yahoo_ticker is None:
            continue
        asset = _first_existing(row, ("ticker", "asset_name", "yahoo_ticker", "symbol")) or yahoo_ticker
        weight = _first_existing(row, ("effective_exposure_weight", "portfolio_weight"))
        rows.append(
            {
                "yahoo_ticker": str(yahoo_ticker).strip(),
                "asset": str(asset).strip(),
                "weight": pd.to_numeric(pd.Series([weight]), errors="coerce").iloc[0] if weight is not None else pd.NA,
                "sector": _first_existing(row, ("sector",)),
                "region": _first_existing(row, ("region",)),
            }
        )

    table = pd.DataFrame(rows)
    if table.empty:
        return table
    table = table.drop_duplicates(subset=["yahoo_ticker", "asset"]).reset_index(drop=True)
    weights = pd.to_numeric(table["weight"], errors="coerce")
    if weights.notna().any() and weights.sum(skipna=True) > 0:
        table["weight"] = weights / weights.sum(skipna=True)
    return table


def _history_bounds(df: pd.DataFrame, lookback_days: int) -> tuple[str, str]:
    dates = pd.Series(dtype="datetime64[ns]")
    for column in ("as_of_date", "date"):
        if column in df.columns:
            dates = pd.to_datetime(df[column], errors="coerce").dropna()
            if not dates.empty:
                break
    end = dates.max() if not dates.empty else pd.Timestamp.today().normalize()
    # yfinance end is exclusive, so include the snapshot date by adding one day.
    start = end - timedelta(days=lookback_days)
    return start.date().isoformat(), (end + timedelta(days=1)).date().isoformat()


def fetch_history_for_holdings(df: pd.DataFrame, lookback_days: int = 370) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch daily price history and return a long dataframe plus fetch log."""

    if yf is None:
        return pd.DataFrame(), pd.DataFrame([{"status": "error", "message": "yfinance is not installed."}])

    ticker_table = _holding_ticker_table(df)
    if ticker_table.empty:
        return pd.DataFrame(), pd.DataFrame([{"status": "warning", "message": "No ticker values were available for history enrichment."}])

    start, end = _history_bounds(df, lookback_days)
    frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for row in ticker_table.to_dict("records"):
        ticker = str(row["yahoo_ticker"]).strip()
        try:
            hist = yf.Ticker(ticker).history(start=start, end=end, interval="1d", auto_adjust=False)
            if hist is None or hist.empty:
                logs.append({"yahoo_ticker": ticker, "status": "warning", "message": "No history rows returned."})
                continue
            hist = hist.reset_index()
            date_col = "Date" if "Date" in hist.columns else hist.columns[0]
            price = hist["Adj Close"] if "Adj Close" in hist.columns and hist["Adj Close"].notna().any() else hist.get("Close")
            frame = pd.DataFrame(
                {
                    "date": pd.to_datetime(hist[date_col], errors="coerce"),
                    "asset": row["asset"],
                    "price": pd.to_numeric(price, errors="coerce"),
                    "weight": row.get("weight"),
                    "sector": row.get("sector"),
                    "region": row.get("region"),
                    "source_ticker": ticker,
                }
            ).dropna(subset=["date", "price"])
            if frame.empty:
                logs.append({"yahoo_ticker": ticker, "status": "warning", "message": "History returned no valid price rows."})
                continue
            frames.append(frame)
            logs.append({"yahoo_ticker": ticker, "status": "ok", "message": f"{len(frame)} history rows fetched."})
        except Exception as exc:  # pragma: no cover - depends on external provider state
            logs.append({"yahoo_ticker": ticker, "status": "error", "message": str(exc)})

    if not frames:
        return pd.DataFrame(), pd.DataFrame(logs)
    enriched = pd.concat(frames, ignore_index=True).sort_values(["asset", "date"])
    return enriched, pd.DataFrame(logs)
