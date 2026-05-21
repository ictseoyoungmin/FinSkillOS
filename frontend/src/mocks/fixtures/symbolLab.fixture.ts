import type { SymbolLabData } from "@/features/symbol/types";

/**
 * Mirrors api/fixtures/symbol_lab.py for TSLA + NVDA.
 *
 * Backend is the source of truth — we only carry enough rows here so
 * the React placeholderData renders the cockpit visual baseline if
 * the API is unreachable.
 */
const TSLA: SymbolLabData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 1 },
  header: {
    ticker: "TSLA",
    timeframe: "1d",
    latestClose: 248.1,
    latestTime: "2026-05-19T00:00:00+00:00",
    dataStatus: "OK",
  },
  technical: {
    rsi14: 58.3,
    ema20: 246.4,
    ema60: 238.9,
    ema120: 224.3,
    bbPosition: 0.61,
    volumeZScore: 0.84,
    momentumScore: 4.8,
    trendState: "WEAK_BULLISH",
  },
  recentBars: Array.from({ length: 12 }, (_, i) => ({
    barTime: `2026-05-${(8 + i).toString().padStart(2, "0")}T00:00:00+00:00`,
    open: 246 + i * 0.1,
    high: 250 + i * 0.05,
    low: 244 + i * 0.08,
    close: 247 + i * 0.1,
    volume: 58_000_000 + i * 12_000,
  })),
  position: {
    ticker: "TSLA",
    sector: "Consumer Discretionary",
    theme: "EV / Robotaxi",
    strategyType: "CORE_HOLDING",
    marketValue: 12_400_000,
    portfolioWeight: 0.169,
    pnlPct: 8.4,
    quantity: 50,
    thesis:
      "Long-term EV / robotaxi exposure. Single-position size is above " +
      "the configured review threshold; size scaling is on watch, not a directive.",
    overSinglePositionLimit: true,
  },
  alerts: [
    {
      guardName: "SINGLE_POSITION_LIMIT_GUARD",
      severity: "WARN",
      title: "Single Position Limit",
      message: "TSLA exceeds configured ₩10M review threshold.",
      alertDate: "2026-05-19",
    },
  ],
  news: [
    {
      title: "Robotaxi pilot expansion: descriptive overview",
      source: "MockWire",
      publishedAt: "2026-05-18T18:00:00+00:00",
      sentimentLabel: "NEUTRAL",
      impactScore: 0.42,
      riskNote: "Headline risk — descriptive, not directive.",
      url: "https://example.com/news/tsla-robotaxi-overview",
    },
  ],
  regime: {
    regime: "RISK_ON_OVERHEAT",
    confidence: 0.72,
    decisionMode: "HOLD_WINNERS",
    riskLevel: "YELLOW",
    summary:
      "Broad trend remains constructive while RSI and breadth flag an elevated state.",
    whatHappened: "Index leadership stayed with AI / Semis names.",
    whatItMeans: "Tape support remains intact but RSI elevation increases pullback odds.",
    positiveFactors: ["Multi-sector trend confirmation."],
    riskFactors: ["RSI elevation across leadership groups."],
    watchNext: ["Monitor leadership-rotation signals if RSI cools."],
    snapshotTime: "2026-05-19T00:00:00+00:00",
  },
  watchpoints: [
    "Trend state is weak bullish; tape support remains intact.",
    "Position value is above the configured single-position limit; " +
      "review sizing before adding risk.",
  ],
  interpretation:
    "TSLA latest trend state is WEAK_BULLISH with RSI(14) near 58. " +
    "Position value is above the single-position limit; this view " +
    "describes exposure context, not a price prediction.",
  setupHint: null,
  safetyCaption: "Stored data only · not prediction · no execution",
};

export function symbolLabFixture(ticker: string): SymbolLabData {
  const t = ticker.toUpperCase();
  if (t === "TSLA") return TSLA;
  return {
    ...TSLA,
    header: { ...TSLA.header, ticker: t },
    position: null,
    alerts: [],
    news: [],
  };
}
