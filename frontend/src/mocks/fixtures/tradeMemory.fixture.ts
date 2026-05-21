import type { TradeMemoryData } from "@/features/trades/types";

const fixtureMarkdown = `# Weekly Review · 2026-05-14 – 2026-05-20

- Trade count: 4
- Total P&L: 320000.00
- Win rate: 50.0%

## Most common mistakes
- Chasing — 2 entries, 2 losing · avg -120000.00
- Late Exit — 1 entries, 1 losing · avg -80000.00

## Best regime: HEALTHY_BULL (total 520000.00)
## Weakest regime: RISK_ON_OVERHEAT (total -200000.00)

## Process notes
- Most frequent mistake tag this week: Chasing (2 entries, 2 losing).
- Best regime by P&L: HEALTHY_BULL (total 520000.00 across 2 entries).
- Weakest regime by P&L: RISK_ON_OVERHEAT (total -200000.00).
- Realised win rate this week: 50.0%.
- Review process quality, not just P&L — revisit thesis and mistake tags before adding new risk.
`;

export const tradeMemoryFixture: TradeMemoryData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  today: "2026-05-20",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  judgment: {
    headline:
      "Process pattern: wins clustered in HEALTHY_BULL, losses cluster around chasing entries in overheat regime.",
    confidence: "MODERATE",
    bestCondition: "HEALTHY_BULL regime entries",
    weakestCondition: "RISK_ON_OVERHEAT regime entries",
    repeatedMistake: "Chasing (2 of 4 entries this week)",
    reviewPriority: "Reduce chasing during overheat windows.",
    tone: "warning",
  },
  drivers: [
    { label: "Recent entries", value: "4 this week", detail: "2 wins · 2 losses · win rate 50.0%." },
    { label: "P&L by regime", value: "HEALTHY_BULL +520k · RISK_ON_OVERHEAT -200k", detail: "Regime explains most of the spread." },
    { label: "P&L by sector / theme", value: "AI / Semis +420k · EV -200k", detail: "Sector concentration confirms the regime read." },
    { label: "P&L by strategy", value: "swing +320k · day_trade 0", detail: "Swing remains the dominant strategy bucket." },
    { label: "Mistake frequency", value: "Chasing 2 · Late Exit 1", detail: "Two repeated tags vs no clean entries." },
    { label: "Emotion tags before losses", value: "FOMO · Hesitation", detail: "Loss-side emotions cluster on event days." },
  ],
  conflicts: [
    {
      label: "Good regime vs poor process",
      description:
        "Even within HEALTHY_BULL windows, chasing entries still appeared. Regime alone does not explain the outcome.",
      tone: "warning",
    },
    {
      label: "Win rate vs clustered mistakes",
      description:
        "50.0% win rate looks balanced, but losses cluster around two repeated tags — the process risk is concentrated.",
      tone: "warning",
    },
    {
      label: "Sample size",
      description:
        "4 trades is a small sample. Process notes apply to behaviour patterns, not statistical edge.",
      tone: "info",
    },
  ],
  recentEntries: [
    {
      id: "trd-001",
      tradeDate: "2026-05-19",
      ticker: "TSLA",
      side: "LONG",
      strategyType: "swing",
      amount: "3500000",
      marketRegime: "RISK_ON_OVERHEAT",
      emotionState: "FOMO",
      resultPnl: "-200000.00",
      resultPnlPct: "-5.71",
      rMultiple: "-1.0000",
      mistakeTags: ["Chasing", "Late Exit"],
      catalyst: "robotaxi rumor",
      sector: "Consumer Discretionary",
      theme: "EV",
      notes: "Entered late after gap-up; should have skipped.",
      thesis: "Robotaxi headline catalyst chase.",
      reason: "Wanted to participate in the news flow.",
    },
    {
      id: "trd-002",
      tradeDate: "2026-05-18",
      ticker: "NVDA",
      side: "LONG",
      strategyType: "swing",
      amount: "4200000",
      marketRegime: "HEALTHY_BULL",
      emotionState: "Calm",
      resultPnl: "320000.00",
      resultPnlPct: "7.62",
      rMultiple: "1.5000",
      mistakeTags: [],
      catalyst: "data center upgrade",
      sector: "Semiconductors",
      theme: "AI",
      notes: "Plan executed; trimmed at first resistance.",
      thesis: "Data-center demand momentum.",
      reason: "Aligned with regime + thesis.",
    },
    {
      id: "trd-003",
      tradeDate: "2026-05-16",
      ticker: "MSFT",
      side: "LONG",
      strategyType: "swing",
      amount: "2200000",
      marketRegime: "HEALTHY_BULL",
      emotionState: "Calm",
      resultPnl: "200000.00",
      resultPnlPct: "9.10",
      rMultiple: "1.0000",
      mistakeTags: [],
      catalyst: "cloud guidance",
      sector: "Technology",
      theme: "Cloud",
      notes: "Hold-then-trim worked as planned.",
      thesis: "Cloud guidance follow-through.",
      reason: "Healthy regime confirmation.",
    },
    {
      id: "trd-004",
      tradeDate: "2026-05-15",
      ticker: "TSLA",
      side: "LONG",
      strategyType: "swing",
      amount: "2900000",
      marketRegime: "RISK_ON_OVERHEAT",
      emotionState: "Hesitation",
      resultPnl: "0.00",
      resultPnlPct: "0.00",
      rMultiple: "0.0000",
      mistakeTags: ["Chasing"],
      catalyst: "news flow",
      sector: "Consumer Discretionary",
      theme: "EV",
      notes: "Entered for narrative, no edge.",
      thesis: "Narrative chase.",
      reason: "Did not respect overheat regime.",
    },
  ],
  performanceByRegime: [
    {
      key: "HEALTHY_BULL",
      tradeCount: 2,
      totalPnl: "520000.00",
      avgPnl: "260000.00",
      avgRMultiple: "1.2000",
      winRate: "1.0000",
    },
    {
      key: "RISK_ON_OVERHEAT",
      tradeCount: 2,
      totalPnl: "-200000.00",
      avgPnl: "-100000.00",
      avgRMultiple: "-0.8000",
      winRate: "0.0000",
    },
  ],
  performanceBySectorTheme: [
    {
      key: "Semiconductors / AI",
      tradeCount: 1,
      totalPnl: "320000.00",
      avgPnl: "320000.00",
      avgRMultiple: "1.5000",
      winRate: "1.0000",
    },
    {
      key: "Technology / Cloud",
      tradeCount: 1,
      totalPnl: "200000.00",
      avgPnl: "200000.00",
      avgRMultiple: "1.0000",
      winRate: "1.0000",
    },
    {
      key: "Consumer Discretionary / EV",
      tradeCount: 2,
      totalPnl: "-200000.00",
      avgPnl: "-100000.00",
      avgRMultiple: "-1.0000",
      winRate: "0.0000",
    },
  ],
  performanceByStrategy: [
    {
      key: "swing",
      tradeCount: 4,
      totalPnl: "320000.00",
      avgPnl: "80000.00",
      avgRMultiple: "0.3750",
      winRate: "0.5000",
    },
  ],
  mistakeFrequency: [
    {
      tag: "Chasing",
      count: 2,
      losingTradeCount: 2,
      avgPnl: "-120000.00",
    },
    {
      tag: "Late Exit",
      count: 1,
      losingTradeCount: 1,
      avgPnl: "-80000.00",
    },
  ],
  weeklyReview: {
    startDate: "2026-05-14",
    endDate: "2026-05-20",
    tradeCount: 4,
    totalPnl: "320000.00",
    winRate: "0.5000",
    mostCommonMistakes: [
      {
        tag: "Chasing",
        count: 2,
        losingTradeCount: 2,
        avgPnl: "-120000.00",
      },
      {
        tag: "Late Exit",
        count: 1,
        losingTradeCount: 1,
        avgPnl: "-80000.00",
      },
    ],
    bestRegime: {
      key: "HEALTHY_BULL",
      tradeCount: 2,
      totalPnl: "520000.00",
      avgPnl: "260000.00",
      avgRMultiple: "1.2000",
      winRate: "1.0000",
    },
    weakestRegime: {
      key: "RISK_ON_OVERHEAT",
      tradeCount: 2,
      totalPnl: "-200000.00",
      avgPnl: "-100000.00",
      avgRMultiple: "-0.8000",
      winRate: "0.0000",
    },
    processNotes: [
      "Most frequent mistake tag this week: Chasing (2 entries, 2 losing).",
      "Best regime by P&L: HEALTHY_BULL (total 520000.00 across 2 entries).",
      "Weakest regime by P&L: RISK_ON_OVERHEAT (total -200000.00).",
      "Realised win rate this week: 50.0%.",
      "Review process quality, not just P&L — revisit thesis and mistake tags before adding new risk.",
    ],
    markdown: fixtureMarkdown,
  },
  integratedInterpretation: [
    "Pattern this week: regime-aligned entries produced gains; narrative chases in overheat regime produced losses.",
    "What helped: respecting HEALTHY_BULL alignment + thesis-led entries with clear catalyst.",
    "What harmed: chasing entries during RISK_ON_OVERHEAT and Late Exit on the losing trade.",
    "Next review condition: define a pre-entry checklist that flags overheat regime + news-only catalyst before sizing.",
  ],
  watchpoints: [
    {
      label: "Chasing before event windows",
      description:
        "Repeat occurrences of 'Chasing' tag near event windows mean the process check failed.",
      tone: "warning",
    },
    {
      label: "Oversizing in overheat regime",
      description:
        "Watch RISK_ON_OVERHEAT entries for sizing relative to single-position limits.",
      tone: "warning",
    },
    {
      label: "Emotion tag clustering",
      description:
        "FOMO / Hesitation tags before losses indicate the emotion check needs to be earlier in the flow.",
      tone: "info",
    },
  ],
  formRules: {
    allowedSides: ["LONG", "SHORT", "WATCH", "EXIT_REVIEW", "OTHER"],
    defaultMistakeTags: [
      "Chasing",
      "No Stop",
      "Oversized",
      "Wrong Thesis",
      "Overtrading",
      "Revenge Trade",
      "Early Entry",
      "Late Exit",
      "Ignored Regime",
      "Event FOMO",
    ],
    disclaimer: "Reflection / process review — no execution controls.",
  },
  safetyCaption: "Reflection / process review only — no execution controls.",
};
