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
  dataState: {
    chartStatus: "OK",
    chartEvidence: "fixture",
    barCount: 22,
    latestBarAt: "2026-05-19T00:00:00+00:00",
    indicatorStatus: "AVAILABLE",
    eventOverlayStatus: "AVAILABLE",
    sourceNote: "Deterministic fixture snapshot; not a live provider feed.",
    refreshNote:
      "Use System Ops market refresh and indicator calculation for DB-backed technical evidence.",
  },
  judgment: {
    eyebrow: "TECHNICAL SIGNAL JUDGMENT",
    title: "Constructive Tape",
    accent: "with Overheat Risk",
    summary:
      "NVDA keeps a constructive trend stack while momentum and event proximity make the signal conditional.",
    confidence: 68,
  },
  drivers: [
    { score: "71.4", title: "RSI(14)", note: "Elevated momentum requires context." },
    { score: "BULLISH", title: "Trend state", note: "Stored indicator snapshot remains constructive." },
    { score: "2", title: "Linked events", note: "Catalyst overlays are part of the interpretation." },
  ],
  conflicts: [
    { title: "Trend support vs overheat", note: "EMA alignment is constructive while RSI is elevated." },
    { title: "Stored bars vs live tape", note: "The fixture snapshot is deterministic and not a live feed." },
  ],
  integratedInterpretation: {
    verdict: "Technical signal is constructive but constrained by overheat risk.",
    whyItMatters:
      "The view separates chart evidence, indicator state, and event overlays before forming context.",
    whatRemainsUncertain:
      "Fresh market bars or event updates may alter the confidence level.",
  },
  reviewWatchpoints: [
    { title: "RSI cooldown", note: "Watch whether momentum normalizes without breaking the trend stack." },
    { title: "Event proximity", note: "Recheck overlays when event timing or linked news changes." },
  ],
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
  safetyCaption:
    "Technical interpretation (not entry signal). Stored data only · not prediction.",
};

export function marketKernelFixture(ticker: string): MarketKernelData {
  // The mock fixture only ships NVDA for now; other tickers reuse it
  // with the header rewritten. The live API has per-ticker series.
  if (ticker.toUpperCase() === "NVDA") return NVDA;
  return {
    ...NVDA,
    judgment: {
      ...NVDA.judgment,
      summary:
        `${ticker.toUpperCase()} reuses the deterministic NVDA fixture snapshot for offline rendering.`,
    },
    header: { ...NVDA.header, ticker: ticker.toUpperCase(), label: ticker.toUpperCase() },
  };
}
