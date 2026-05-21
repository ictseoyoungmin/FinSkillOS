import type { MarketKernelData } from "@/features/market/kernel-types";

/**
 * Mirrors api/fixtures/market_kernel.py. Used when the API is offline
 * so the cockpit + Playwright structural baseline still render. Kept
 * in sync by hand; tests assert the shapes match.
 */
const NVDA: MarketKernelData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 0 },
  universe: [
    { symbol: "NVDA", label: "NVIDIA", kind: "FOCUS" },
    { symbol: "TSLA", label: "Tesla", kind: "FOCUS" },
    { symbol: "AAPL", label: "Apple", kind: "FOCUS" },
    { symbol: "MSFT", label: "Microsoft", kind: "FOCUS" },
    { symbol: "SMH", label: "Semiconductor ETF", kind: "SECTOR_ETF" },
    { symbol: "SPY", label: "S&P 500 ETF", kind: "INDEX_ETF" },
    { symbol: "QQQ", label: "Nasdaq 100 ETF", kind: "INDEX_ETF" },
    { symbol: "VIX", label: "Volatility Proxy", kind: "MACRO_PROXY" },
    { symbol: "DXY", label: "USD Index Proxy", kind: "MACRO_PROXY" },
    { symbol: "US10Y", label: "10Y Yield Proxy", kind: "MACRO_PROXY" },
  ],
  header: {
    ticker: "NVDA",
    label: "NVIDIA",
    timeframe: "1d",
    latestClose: 172.34,
    latestTime: "2026-05-19T00:00:00+00:00",
    dataStatus: "OK",
  },
  bars: Array.from({ length: 22 }, (_, i) => ({
    barTime: `2026-04-${(20 + i).toString().padStart(2, "0")}T00:00:00+00:00`,
    open: 152 + i * 0.9,
    high: 154 + i * 0.95,
    low: 150 + i * 0.85,
    close: 152 + i * 0.92,
    volume: 42_000_000 + i * 12_000,
  })),
  indicators: {
    rsi14: 71.4,
    ema20: 166.2,
    ema60: 158.4,
    ema120: 145.2,
    bbPosition: 0.82,
    volumeZScore: 1.62,
    momentumScore: 12.4,
    trendState: "BULLISH",
  },
  events: [
    {
      daysToEvent: 2,
      title: "NVDA Earnings",
      subtitle: "Semis / AI exposure · event-linked news active",
      tag: "High",
      tone: "danger",
    },
    {
      daysToEvent: 5,
      title: "FOMC Window",
      subtitle: "Macro event · rate-path sensitivity",
      tag: "Window",
      tone: "warning",
    },
  ],
  watchpoints: [
    "RSI is elevated; monitor short-term overheat risk.",
    "Trend state is bullish; tape support is constructive.",
  ],
  interpretation:
    "NVDA latest trend state is BULLISH with RSI(14) near 71. " +
    "Earnings event is inside the catalyst window; this view describes " +
    "exposure context, not a price prediction.",
  setupHint: null,
  safetyCaption: "Stored data only · not prediction · no execution",
};

export function marketKernelFixture(ticker: string): MarketKernelData {
  // The mock fixture only ships NVDA for now; other tickers reuse it
  // with the header rewritten. The live API has per-ticker series.
  if (ticker.toUpperCase() === "NVDA") return NVDA;
  return {
    ...NVDA,
    header: { ...NVDA.header, ticker: ticker.toUpperCase(), label: ticker.toUpperCase() },
  };
}
