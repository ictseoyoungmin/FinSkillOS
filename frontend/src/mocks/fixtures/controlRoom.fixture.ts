import type { ControlRoomData } from "@/features/control-room/types";

/**
 * Mirrors api/fixtures.py::control_room_fixture so the Playwright
 * visual baseline stays deterministic even when the API is not
 * reachable.
 */
export const CONTROL_ROOM_FIXTURE_TIMESTAMP = "2026-05-20T12:00:00+09:00";

export const controlRoomFixture: ControlRoomData = {
  generatedAt: CONTROL_ROOM_FIXTURE_TIMESTAMP,
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  dataState: {
    source: "fixture",
    overviewStatus: "OK",
    systemStatus: "OK",
    missionStatus: "OK",
    marketTapeStatus: "OK",
    guardStatus: "OK",
    catalystStatus: "OK",
    watchlistStatus: "OK",
    marketTapePoints: 11,
    guardCount: 3,
    catalystCount: 3,
    watchlistCount: 4,
    latestMarketAt: "2026-05-19T00:00:00+00:00",
    latestEventAt: "2026-05-22",
    latestWatchlistAt: "2026-05-19T00:00:00+00:00",
    marketFreshnessStatus: "FRESH",
    catalystFreshnessStatus: "FRESH",
    watchlistFreshnessStatus: "FRESH",
    railFreshnessStatus: "FRESH",
    railFreshnessNote: "Fixture rail timestamps are deterministic.",
    marketStaleAfterDays: 3,
    watchlistStaleAfterDays: 3,
    sourceNote:
      "Control Room is a fixture-first operating overview; underlying tabs expose their own live/fixture evidence.",
    refreshNote:
      "Use dedicated Market, Risk, Mission, Catalyst, and Symbol tabs for promoted DB-backed read models.",
  },
  judgment: {
    eyebrow: "GLOBAL OPERATING VERDICT",
    title: "Risk-On but",
    accent: "Extended",
    summary:
      "Portfolio context remains constructive, but overheat and event-cluster flags keep the operating posture conditional.",
    confidence: 72,
  },
  drivers: [
    { score: "64", title: "Preparation score", note: "Risk-on state with measured exposure review." },
    { score: "3", title: "Active guard notes", note: "Concentration, single-name, and regime flags are visible." },
    { score: "7D", title: "Event cluster", note: "Earnings and macro windows sit inside the next review horizon." },
  ],
  conflicts: [
    { title: "Constructive tape vs overheat", note: "Trend support remains present while RSI elevation reduces comfort." },
    { title: "Portfolio relevance vs event timing", note: "AI / Semis exposure overlaps with near-term catalyst windows." },
  ],
  interpretation: {
    verdict: "Risk-On but Extended remains the working operating verdict.",
    whyItMatters:
      "The dashboard combines tape, guard, mission, and event context before the user reviews exposure.",
    whatRemainsUncertain:
      "Fixture freshness and event date certainty can still change the posture.",
  },
  watchpoints: [
    { title: "Overheat persistence", note: "Review if RSI elevation remains active across leadership names." },
    { title: "Event cluster", note: "Recheck catalyst status when linked news or date confidence changes." },
    { title: "Guard escalation", note: "Any RED guard keeps the posture in review mode." },
  ],
  safetyCaption: "Global operating posture (not execution).",
  tickerScore: 64,
  tickerStrip: [
    { symbol: "NVDA", price: "172", change: "+1.8%", direction: "up", currency: "USD", logoUrl: null, held: true },
    { symbol: "TSLA", price: "248", change: "-0.7%", direction: "down", currency: "USD", logoUrl: null, held: true },
    { symbol: "SPY", price: "672", change: "+0.4%", direction: "up", currency: "USD", logoUrl: null, held: false },
    { symbol: "QQQ", price: "557", change: "+0.6%", direction: "up", currency: "USD", logoUrl: null, held: false },
    { symbol: "AAPL", price: "232", change: "+0.2%", direction: "up", currency: "USD", logoUrl: null, held: false },
    { symbol: "MSFT", price: "439", change: "-0.1%", direction: "flat", currency: "USD", logoUrl: null, held: false },
    { symbol: "SMH", price: "305", change: "+1.1%", direction: "up", currency: "USD", logoUrl: null, held: false },
    { symbol: "VIX", price: "15", change: "-3.2%", direction: "down", currency: "USD", logoUrl: null, held: false },
    { symbol: "DXY", price: "103", change: "+0.1%", direction: "flat", currency: "USD", logoUrl: null, held: false },
    { symbol: "US10Y", price: "4", change: "+0.0%", direction: "up", currency: "USD", logoUrl: null, held: false },
  ],
  mission: {
    currentValue: 73_420_000,
    targetValue: 100_000_000,
    progressPct: 73.4,
    phase: "Phase 3 / 5",
    earlyStopTriggered: false,
    goalMode: "COMPLETION_GUARD",
  },
  operatingState: {
    title: "Risk-On but Extended",
    regime: "RISK_ON_OVERHEAT",
    decisionMode: "HOLD_WINNERS",
    preparationScore: 64,
    tags: [
      "Trend Support",
      "Overheat Watch",
      "Stored Data Only",
      "Event Cluster",
    ],
    summary:
      "Broad trend remains constructive while RSI and breadth flag an elevated state. Prepare for event-driven volatility; this view describes exposure, not a price prediction.",
    stateVector: [
      { label: "Decision Mode", value: "Hold Winners", tone: "info" },
      { label: "Confidence", value: "64%", tone: "neutral" },
      {
        label: "Strength",
        value: "Broad trend stack remains constructive",
        tone: "success",
      },
      {
        label: "Risk Factor",
        value: "RSI and breadth flag an elevated state",
        tone: "warning",
      },
    ],
  },
  portfolioExposure: [
    { label: "AI / Semis", weightPct: 42.6 },
    { label: "EV / Robotaxi", weightPct: 18.4 },
    { label: "Mega-Cap Tech", weightPct: 16.8 },
    { label: "Cash", weightPct: 22.2 },
  ],
  allocation: [
    { ticker: "NVDA", value: "15000000", weightPct: 20.4 },
    { ticker: "TSLA", value: "12000000", weightPct: 16.3 },
    { ticker: "AAPL", value: "9000000", weightPct: 12.3 },
    { ticker: "MSFT", value: "7000000", weightPct: 9.5 },
    { ticker: "AVGO", value: "5000000", weightPct: 6.8 },
  ],
  reviewQueue: [
    {
      title: "Weekly review · Week 20",
      note: "3 entries pending; Chasing tag repeats from Week 19.",
      tag: "weekly",
    },
    {
      title: "Thesis check · NVDA",
      note: "Reconfirm AI-cycle thesis before next earnings window.",
      tag: "thesis",
    },
    {
      title: "Event prep · FOMC",
      note: "Macro window inside 7 sessions; review cash buffer.",
      tag: "event",
    },
  ],
  interpretationCards: [
    "Trend stack remains constructive across SPY / QQQ / SMH.",
    "RSI elevation and overheat flags suggest measured sizing only.",
    "Earnings + macro cluster inside the next 7 sessions; this is a preparation cue, not a directional call.",
  ],
  riskFirewall: [
    {
      name: "SINGLE_POSITION_LIMIT_GUARD",
      status: "WARN",
      riskLevel: "YELLOW",
      title: "Single Position Limit",
      message: "TSLA exceeds configured ₩10M review threshold.",
    },
    {
      name: "DRAWDOWN_GUARD",
      status: "PASS",
      riskLevel: "GREEN",
      title: "Drawdown Guard",
      message: "Current drawdown is below defensive threshold.",
    },
    {
      name: "SECTOR_CONCENTRATION_GUARD",
      status: "FAIL",
      riskLevel: "RED",
      title: "Sector Concentration",
      message: "AI / Semis exposure requires monitoring before adding risk.",
    },
  ],
  catalystWatch: [
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
    {
      daysToEvent: 9,
      title: "SpaceX IPO chatter",
      subtitle: "Speculative placeholder · not confirmed",
      tag: "Speculative",
      tone: "purple",
    },
  ],
  watchlist: [
    {
      symbol: "NVDA",
      label: "NVIDIA",
      note: "Above EMA20 / EMA60; watch RSI elevation.",
      tone: "info",
    },
    {
      symbol: "TSLA",
      label: "Tesla",
      note: "Position above single-position-limit review threshold.",
      tone: "warning",
    },
    {
      symbol: "SMH",
      label: "Semis ETF",
      note: "Tape strength leadership; theme exposure high.",
      tone: "info",
    },
    {
      symbol: "VIX",
      label: "Volatility Proxy",
      note: "Compressed; mean-reversion risk into events.",
      tone: "neutral",
    },
  ],
  marketTape: [
    { label: "T-90", portfolio: 100.0, benchmark: 100.0 },
    { label: "T-75", portfolio: 101.4, benchmark: 100.9 },
    { label: "T-60", portfolio: 103.2, benchmark: 101.8 },
    { label: "T-45", portfolio: 104.8, benchmark: 102.4 },
    { label: "T-30", portfolio: 106.6, benchmark: 103.1 },
    { label: "T-21", portfolio: 108.9, benchmark: 104.0 },
    { label: "T-14", portfolio: 110.2, benchmark: 104.7 },
    { label: "T-10", portfolio: 109.4, benchmark: 104.3 },
    { label: "T-7", portfolio: 112.1, benchmark: 105.6 },
    { label: "T-3", portfolio: 113.6, benchmark: 106.2 },
    { label: "T-0", portfolio: 115.2, benchmark: 106.8 },
  ],
};
