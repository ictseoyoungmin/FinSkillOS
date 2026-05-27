import type { NewsIntelligenceData } from "@/features/news/types";

/**
 * Mirrors api/fixtures/news_intelligence.py. Used when the API is
 * offline so the News Intelligence page still renders. Kept in sync
 * by hand; backend tests assert the camelCase shape stays consistent.
 */
export const newsIntelligenceFixture: NewsIntelligenceData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  judgment: {
    headline:
      "Narrative leans constructive on AI demand while macro calendar keeps two-way risk in play.",
    confidence: "MODERATE",
    dominantTheme: "AI / Data Center",
    portfolioRelevance: "3 of 4 holdings touched by recent headlines.",
    eventLinkage: "2 articles linked to upcoming events (FOMC, robotaxi).",
    sentimentTone: "MIXED",
    riskTone: "YELLOW",
    tone: "info",
  },
  drivers: [
    {
      label: "Affected holdings",
      value: "TSLA · NVDA · MSFT",
      detail: "3 of 4 active holdings appear in today's coverage.",
    },
    {
      label: "Theme exposure",
      value: "AI · Data Center · EV",
      detail: "AI / Data Center cluster dominates the latest pulls.",
    },
    {
      label: "Linked event count",
      value: "2",
      detail: "FOMC window + Tesla robotaxi tentatively linked.",
    },
    {
      label: "Source quality / freshness",
      value: "3 sources · last 24h",
      detail: "Reuters / Bloomberg / WSJ within the last day.",
    },
  ],
  conflicts: [
    {
      label: "Positive narrative vs event volatility",
      description:
        "Constructive AI tone exists alongside an approaching FOMC window that historically amplifies two-way moves.",
      tone: "warning",
    },
    {
      label: "Article count vs source confidence",
      description:
        "Article count is moderate, but only three distinct sources confirm the theme — beware single-source bias.",
      tone: "warning",
    },
    {
      label: "Broad market vs holding-specific relevance",
      description:
        "Macro / FOMC coverage applies broadly; ticker-specific headlines remain sparse for AAPL and AMZN today.",
      tone: "info",
    },
  ],
  holdingsRelevant: [
    {
      id: "nws-001",
      title: "Tesla robotaxi event tentatively scheduled for next month",
      source: "Reuters",
      url: "https://example.com/news/tsla-robotaxi-window",
      publishedAt: "2026-05-19T13:20:00+00:00",
      summary:
        "Tesla reportedly plans a robotaxi unveil within a tentative window. Details remain unconfirmed and the date may shift.",
      impacts: [
        {
          ticker: "TSLA",
          sector: "Consumer Discretionary",
          theme: "EV",
          eventKey: "EARNINGS",
          impactScore: "0.5",
          sentimentLabel: "NEUTRAL",
          riskLevel: "YELLOW",
          isEventLinked: true,
        },
      ],
    },
    {
      id: "nws-002",
      title: "NVIDIA upgrade cycle accelerates across hyperscalers",
      source: "Bloomberg",
      url: "https://example.com/news/nvda-data-center",
      publishedAt: "2026-05-19T09:05:00+00:00",
      summary:
        "Reports highlight broad data-center demand growth, but sustainability of order momentum remains debated.",
      impacts: [
        {
          ticker: "NVDA",
          sector: "Semiconductors",
          theme: "AI",
          eventKey: null,
          impactScore: "0.6",
          sentimentLabel: "POSITIVE",
          riskLevel: "GREEN",
          isEventLinked: false,
        },
      ],
    },
  ],
  eventLinked: [
    {
      id: "nws-001",
      title: "Tesla robotaxi event tentatively scheduled for next month",
      source: "Reuters",
      url: "https://example.com/news/tsla-robotaxi-window",
      publishedAt: "2026-05-19T13:20:00+00:00",
      summary:
        "Tesla reportedly plans a robotaxi unveil within a tentative window. Details remain unconfirmed and the date may shift.",
      impacts: [
        {
          ticker: "TSLA",
          sector: "Consumer Discretionary",
          theme: "EV",
          eventKey: "EARNINGS",
          impactScore: "0.5",
          sentimentLabel: "NEUTRAL",
          riskLevel: "YELLOW",
          isEventLinked: true,
        },
      ],
    },
    {
      id: "nws-003",
      title: "FOMC meeting window approaches with rates in focus",
      source: "WSJ",
      url: "https://example.com/news/fomc-window",
      publishedAt: "2026-05-18T22:00:00+00:00",
      summary:
        "Macro calendar shows an approaching FOMC window. Market is monitoring inflation prints for direction signals.",
      impacts: [
        {
          ticker: null,
          sector: null,
          theme: "Macro",
          eventKey: "FED_DECISION",
          impactScore: "0.4",
          sentimentLabel: "NEUTRAL",
          riskLevel: "YELLOW",
          isEventLinked: true,
        },
      ],
    },
  ],
  latestNews: [
    {
      id: "nws-001",
      title: "Tesla robotaxi event tentatively scheduled for next month",
      source: "Reuters",
      url: "https://example.com/news/tsla-robotaxi-window",
      publishedAt: "2026-05-19T13:20:00+00:00",
      summary:
        "Tesla reportedly plans a robotaxi unveil within a tentative window. Details remain unconfirmed and the date may shift.",
      impacts: [],
    },
    {
      id: "nws-002",
      title: "NVIDIA upgrade cycle accelerates across hyperscalers",
      source: "Bloomberg",
      url: "https://example.com/news/nvda-data-center",
      publishedAt: "2026-05-19T09:05:00+00:00",
      summary:
        "Reports highlight broad data-center demand growth, but sustainability of order momentum remains debated.",
      impacts: [],
    },
    {
      id: "nws-003",
      title: "FOMC meeting window approaches with rates in focus",
      source: "WSJ",
      url: "https://example.com/news/fomc-window",
      publishedAt: "2026-05-18T22:00:00+00:00",
      summary:
        "Macro calendar shows an approaching FOMC window. Market is monitoring inflation prints for direction signals.",
      impacts: [],
    },
  ],
  impactMap: [
    {
      label: "NVDA",
      dimension: "ticker",
      articleCount: 1,
      sentiment: "POSITIVE",
      riskLevel: "GREEN",
    },
    {
      label: "TSLA",
      dimension: "ticker",
      articleCount: 1,
      sentiment: "NEUTRAL",
      riskLevel: "YELLOW",
    },
    {
      label: "AI",
      dimension: "theme",
      articleCount: 1,
      sentiment: "POSITIVE",
      riskLevel: "GREEN",
    },
    {
      label: "Macro",
      dimension: "theme",
      articleCount: 1,
      sentiment: "NEUTRAL",
      riskLevel: "YELLOW",
    },
    {
      label: "Semiconductors",
      dimension: "sector",
      articleCount: 1,
      sentiment: "POSITIVE",
      riskLevel: "GREEN",
    },
  ],
  tickerIdentities: [
    {
      ticker: "NVDA",
      name: "NVIDIA",
      logoUrl: null,
      logoSource: "local_fallback",
      avatarText: "NV",
      brandColor: "#16a34a",
    },
    {
      ticker: "TSLA",
      name: "Tesla",
      logoUrl: null,
      logoSource: "local_fallback",
      avatarText: "TS",
      brandColor: "#dc2626",
    },
  ],
  integratedInterpretation: [
    "Today's news mix reinforces an AI / Data Center read for the portfolio while keeping a macro overlay active.",
    "It matters because two of the largest holdings (TSLA, NVDA) sit on event-linked themes — date confidence drives the narrative confidence.",
    "Uncertain elements: robotaxi date remains tentative, FOMC window has not yet started; both can shift confidence quickly.",
  ],
  watchpoints: [
    {
      label: "Source confirmation",
      description:
        "Watch for a second source confirming the Tesla robotaxi window before treating it as a base case.",
      tone: "info",
    },
    {
      label: "Event status change",
      description:
        "Linked-event status moving from TENTATIVE → CONFIRMED would lift narrative confidence.",
      tone: "info",
    },
    {
      label: "Theme cluster",
      description:
        "A sudden cluster of negative AI / chip headlines would re-rank the dominant theme tone.",
      tone: "warning",
    },
  ],
  manualEntryRules: {
    maxSummaryChars: 500,
    forbidFullBody: true,
    disclaimer: "Short summaries only — no full article body stored.",
  },
  safetyCaption: "Descriptive narrative view only — no execution controls.",
};
