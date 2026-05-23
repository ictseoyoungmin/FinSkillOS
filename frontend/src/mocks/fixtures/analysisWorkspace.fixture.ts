import type { AnalysisWorkspaceData } from "@/features/analysis/types";

/**
 * Mirrors api/fixtures/analysis_workspace.py. The shape is checked by
 * tests/test_api_analysis_workspace.py so the React structural test
 * stays decoupled from the API container.
 */
export const analysisWorkspaceFixture: AnalysisWorkspaceData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 0 },
  judgment: {
    eyebrow: "MARKET STRUCTURE JUDGMENT",
    title: "Leadership is",
    accent: "Narrow",
    summary:
      "Semiconductor and mega-cap technology strength carries the tape while defensive groups lag.",
    confidence: 70,
  },
  drivers: [
    { score: "SMH", title: "Strongest tape", note: "Semiconductors lead the relative-strength table." },
    { score: "XLU", title: "Weakest tape", note: "Defensive utilities remain the weakest sector read." },
    { score: "0", title: "Missing series", note: "The fixture universe is complete for this snapshot." },
  ],
  conflicts: [
    { title: "Broad index strength vs narrow leadership", note: "Index-level support is present but concentrated in fewer groups." },
    { title: "Risk-on regime vs macro pressure", note: "Yield proxy pressure remains a review condition." },
  ],
  interpretation: {
    verdict: "Market structure remains constructive but leadership is narrow.",
    whyItMatters:
      "Breadth context helps separate broad participation from concentrated theme leadership.",
    whatRemainsUncertain:
      "Rotation or missing-data changes could weaken the judgment.",
  },
  watchpoints: [
    { title: "Leadership rotation", note: "Watch whether strength expands beyond AI / Semis." },
    { title: "Macro proxy pressure", note: "Track US10Y and VIX if risk tone changes." },
  ],
  timeframe: "1d",
  universe: [
    {
      ticker: "SPY",
      label: "S&P 500 ETF",
      kind: "INDEX_ETF",
      latestClose: 672.48,
      latestTime: "2026-05-19T00:00:00+00:00",
      rsi14: 62.1,
      ema20: 658.2,
      ema60: 642.1,
      bbPosition: 0.68,
      volumeZScore: 0.41,
      momentumScore: 4.2,
      trendState: "BULLISH",
      dataStatus: "OK",
      relativeStrengthScore: 4.92,
      watchpoints: ["Trend state is bullish; tape support is constructive."],
    },
    {
      ticker: "QQQ",
      label: "Nasdaq 100 ETF",
      kind: "INDEX_ETF",
      latestClose: 556.71,
      latestTime: "2026-05-19T00:00:00+00:00",
      rsi14: 65.3,
      ema20: 538.4,
      ema60: 514.2,
      bbPosition: 0.74,
      volumeZScore: 0.62,
      momentumScore: 6.8,
      trendState: "BULLISH",
      dataStatus: "OK",
      relativeStrengthScore: 5.18,
      watchpoints: ["Trend state is bullish; tape support is constructive."],
    },
    {
      ticker: "SMH",
      label: "Semiconductor ETF",
      kind: "SECTOR_ETF",
      latestClose: 304.55,
      latestTime: "2026-05-19T00:00:00+00:00",
      rsi14: 72.9,
      ema20: 297.4,
      ema60: 285.3,
      bbPosition: 0.87,
      volumeZScore: 1.34,
      momentumScore: 14.2,
      trendState: "BULLISH",
      dataStatus: "OK",
      relativeStrengthScore: 6.92,
      watchpoints: [
        "RSI is elevated; monitor overheat risk.",
        "Trend state is bullish; tape support is constructive.",
      ],
    },
    {
      ticker: "XLU",
      label: "Utilities Sector",
      kind: "SECTOR_ETF",
      latestClose: 74.2,
      latestTime: "2026-05-19T00:00:00+00:00",
      rsi14: 39.4,
      ema20: 75.1,
      ema60: 75.8,
      bbPosition: 0.32,
      volumeZScore: -0.42,
      momentumScore: -2.4,
      trendState: "BEARISH",
      dataStatus: "OK",
      relativeStrengthScore: -2.24,
      watchpoints: ["Trend state is bearish; treat this as a weak tape signal."],
    },
    {
      ticker: "VIX",
      label: "Volatility Index Proxy",
      kind: "MACRO_PROXY",
      latestClose: 14.62,
      latestTime: "2026-05-19T00:00:00+00:00",
      rsi14: 32.4,
      ema20: 15.4,
      ema60: 17.2,
      bbPosition: 0.21,
      volumeZScore: -0.18,
      momentumScore: -12.4,
      trendState: "WEAK_BEARISH",
      dataStatus: "OK",
      relativeStrengthScore: null,
      watchpoints: ["Volatility proxy is easing; macro stress is fading."],
    },
  ],
  strongest: [
    { ticker: "SMH", label: "Semiconductor ETF", relativeStrengthScore: 6.92, trendState: "BULLISH" },
    { ticker: "SOXX", label: "Semiconductor ETF (iShares)", relativeStrengthScore: 6.18, trendState: "BULLISH" },
    { ticker: "XLK", label: "Technology Sector", relativeStrengthScore: 5.48, trendState: "BULLISH" },
  ],
  weakest: [
    { ticker: "XLU", label: "Utilities Sector", relativeStrengthScore: -2.24, trendState: "BEARISH" },
    { ticker: "XLE", label: "Energy Sector", relativeStrengthScore: -0.18, trendState: "WEAK_BEARISH" },
    { ticker: "XLP", label: "Consumer Staples Sector", relativeStrengthScore: -0.08, trendState: "WEAK_BEARISH" },
  ],
  missingData: [],
  regime: {
    regime: "RISK_ON_OVERHEAT",
    confidence: 0.72,
    decisionMode: "HOLD_WINNERS",
    riskLevel: "YELLOW",
    summary:
      "Broad trend remains constructive while RSI and breadth flag an elevated state. " +
      "This view describes regime context, not a price prediction.",
    whatHappened:
      "Index leadership stayed with AI / Semis names while broader tape strength persisted.",
    whatItMeans:
      "Tape support remains intact but RSI elevation increases the odds of measured pullback windows.",
    positiveFactors: [
      "Multi-sector trend confirmation (SPY / QQQ / SMH).",
      "Volume z-score elevation on leading semis ETFs.",
    ],
    riskFactors: [
      "RSI elevation across leadership groups.",
      "Macro yield proxy bias is mildly upward.",
    ],
    watchNext: [
      "Monitor leadership-rotation signals if RSI cools.",
      "Track event-cluster impact across the next 7 sessions.",
    ],
    snapshotTime: "2026-05-19T00:00:00+00:00",
  },
  setupHint: null,
  safetyCaption: "Structural breadth read (not allocation call).",
};
