import type { EventRadarData, EventRiskRow } from "@/features/events/types";

const linkedNews = [
  {
    title: "Tesla robotaxi event tentatively scheduled for next month",
    source: "Reuters",
    publishedAt: "2026-05-19T13:20:00+00:00",
    sentimentLabel: "NEUTRAL",
    riskLevel: "YELLOW",
    summary:
      "Tesla reportedly plans a robotaxi unveil within a tentative window. Details remain unconfirmed.",
    url: "https://example.com/news/tsla-robotaxi-window",
  },
  {
    title: "FOMC meeting window approaches with rates in focus",
    source: "WSJ",
    publishedAt: "2026-05-18T22:00:00+00:00",
    sentimentLabel: "NEUTRAL",
    riskLevel: "YELLOW",
    summary:
      "Macro calendar shows an approaching FOMC window. Market monitors inflation prints for direction signals.",
    url: "https://example.com/news/fomc-window",
  },
];

const upcoming: EventRiskRow[] = [
  {
    eventId: "evt-001",
    title: "NVIDIA earnings",
    eventType: "EARNINGS",
    dateStatus: "TENTATIVE",
    startDate: "2026-06-10",
    endDate: null,
    daysToEvent: 21,
    importanceScore: "4.0",
    eventRiskScore: "5.40",
    riskLabel: "HIGH",
    portfolioExposure: "0.1840",
    affectedTickers: ["NVDA"],
    affectedSectors: ["Semiconductors"],
    affectedThemes: ["AI"],
    description: "Tentative earnings window; verify against the IR calendar.",
    preEventNote:
      "Event window is within one month; monitor positioning and related news. Linked portfolio exposure is 18.4%.",
    postEventNote:
      "Monitor whether price reaction confirms the headline. Volume confirmation and reversal risk apply even when the headline is constructive.",
    links: [
      {
        ticker: "NVDA",
        sector: "Semiconductors",
        theme: "AI",
        eventKey: "EARNINGS",
      },
    ],
    linkedNews: [],
  },
  {
    eventId: "evt-002",
    title: "FOMC rate decision",
    eventType: "CENTRAL_BANK",
    dateStatus: "WINDOW",
    startDate: "2026-06-03",
    endDate: "2026-06-04",
    daysToEvent: 14,
    importanceScore: "3.5",
    eventRiskScore: "4.20",
    riskLabel: "HIGH",
    portfolioExposure: "0.0000",
    affectedTickers: [],
    affectedSectors: [],
    affectedThemes: ["Macro"],
    description: "FOMC date window approximated; verify with Fed calendar.",
    preEventNote:
      "Event window is within one month. Macro-level exposure applies even without a direct ticker overlap.",
    postEventNote:
      "Monitor whether price reaction confirms the headline. Volume confirmation and reversal risk apply.",
    links: [
      { ticker: null, sector: null, theme: "Macro", eventKey: "FED_DECISION" },
    ],
    linkedNews: [linkedNews[1]],
  },
  {
    eventId: "evt-003",
    title: "Tesla robotaxi event",
    eventType: "PRODUCT_EVENT",
    dateStatus: "TENTATIVE",
    startDate: "2026-06-19",
    endDate: null,
    daysToEvent: 30,
    importanceScore: "3.5",
    eventRiskScore: "3.85",
    riskLabel: "MODERATE",
    portfolioExposure: "0.1380",
    affectedTickers: ["TSLA"],
    affectedSectors: ["Consumer Discretionary"],
    affectedThemes: ["EV"],
    description: "Tentative event date; replace once announced.",
    preEventNote:
      "Event window is within one month. Linked portfolio exposure is 13.8%.",
    postEventNote:
      "Monitor whether price reaction confirms the headline. Volume confirmation and reversal risk apply.",
    links: [
      {
        ticker: "TSLA",
        sector: "Consumer Discretionary",
        theme: "EV",
        eventKey: null,
      },
    ],
    linkedNews: [linkedNews[0]],
  },
  {
    eventId: "evt-004",
    title: "CPI release",
    eventType: "INFLATION",
    dateStatus: "TENTATIVE",
    startDate: "2026-05-30",
    endDate: null,
    daysToEvent: 10,
    importanceScore: "3.0",
    eventRiskScore: "3.60",
    riskLabel: "MODERATE",
    portfolioExposure: "0.0000",
    affectedTickers: [],
    affectedSectors: [],
    affectedThemes: ["Macro"],
    description: "Tentative CPI release date; verify against the BLS calendar.",
    preEventNote:
      "Event window is within two weeks. Macro-level exposure applies without a direct ticker overlap.",
    postEventNote:
      "Monitor whether price reaction confirms the headline. Volume confirmation and reversal risk apply.",
    links: [
      { ticker: null, sector: null, theme: "Macro", eventKey: "MACRO_PRINT" },
    ],
    linkedNews: [],
  },
  {
    eventId: "evt-005",
    title: "SpaceX IPO expected window",
    eventType: "IPO_WINDOW",
    dateStatus: "SPECULATIVE",
    startDate: "2026-07-19",
    endDate: "2026-08-18",
    daysToEvent: 60,
    importanceScore: "3.0",
    eventRiskScore: "2.10",
    riskLabel: "MODERATE",
    portfolioExposure: "0.0000",
    affectedTickers: [],
    affectedSectors: [],
    affectedThemes: ["Space"],
    description: "Speculative placeholder; not a confirmed listing date.",
    preEventNote:
      "Event is further out than one month — this is a watch-list entry only. Date confidence is low (SPECULATIVE).",
    postEventNote:
      "Monitor whether price reaction confirms the headline. Volume confirmation and reversal risk apply.",
    links: [
      {
        ticker: null,
        sector: null,
        theme: "Space",
        eventKey: "SPACEX_IPO_WINDOW",
      },
    ],
    linkedNews: [],
  },
];

export const eventRadarFixture: EventRadarData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  today: "2026-05-20",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  dataState: {
    calendarSource: "fixture",
    calendarStatus: "fixture_first",
    calendarDetail:
      "Deterministic event catalog; live DB event read model has not been promoted for this tab yet.",
    eventCount: 5,
    linkedNewsCount: 2,
    confirmedCount: 0,
    uncertainCount: 5,
    nearestEventDays: 10,
    dateConfidenceStatus: "uncertain",
    dateConfidenceDetail: "0 CONFIRMED · 1 WINDOW · 3 TENTATIVE · 1 SPECULATIVE",
    sourceNote: "DB status is shown separately from Catalyst calendar source.",
  },
  judgment: {
    headline:
      "Event calendar shows clustered macro + earnings risk over the next 3 weeks; preparation, not prediction, drives the score.",
    confidence: "MODERATE",
    highestRiskEvent: "NVIDIA earnings · risk 5.40 · TENTATIVE",
    clusterStatus: "2 events within 14 days (FOMC, CPI)",
    portfolioLinkedExposure: "2 holdings linked (NVDA, TSLA)",
    dateConfidenceMix: "0 CONFIRMED · 1 WINDOW · 3 TENTATIVE · 1 SPECULATIVE",
    tone: "warning",
  },
  drivers: [
    {
      label: "Portfolio exposure",
      value: "18.4% NVDA · 13.8% TSLA",
      detail: "Two holdings overlap upcoming events directly.",
    },
    {
      label: "Days to nearest event",
      value: "10 days (CPI release)",
      detail: "Macro window enters the two-week zone.",
    },
    {
      label: "Date status mix",
      value: "1 WINDOW · 3 TENTATIVE · 1 SPECULATIVE",
      detail: "No CONFIRMED dates in the current set.",
    },
    {
      label: "Regime multiplier",
      value: "1.0 (no overheat bonus active)",
      detail: "Latest regime not RISK_ON_OVERHEAT; no multiplier bump.",
    },
    {
      label: "Linked news count",
      value: "2",
      detail: "FOMC window + Tesla robotaxi tentatively linked.",
    },
  ],
  conflicts: [
    {
      label: "Confirmed vs speculative",
      description:
        "No date is CONFIRMED yet — every row carries date uncertainty. Treat the schedule as approximate.",
      tone: "warning",
    },
    {
      label: "High news attention vs low date confidence",
      description:
        "Tesla robotaxi has news coverage but stays TENTATIVE; narrative confidence can outrun calendar confidence.",
      tone: "warning",
    },
    {
      label: "Score is preparation, not prediction",
      description:
        "A high event_risk_score signals exposure / preparation load, not a price direction. Interpret accordingly.",
      tone: "info",
    },
  ],
  upcoming,
  highRisk: upcoming.filter((row) => row.riskLabel === "HIGH" || row.riskLabel === "CRITICAL"),
  holdingsLinked: upcoming.filter((row) => row.affectedTickers.length > 0),
  linkedNews,
  integratedInterpretation: [
    "Why it deserves attention: a cluster of macro + earnings windows overlaps within 30 days, while two of the largest holdings sit on event-linked themes.",
    "How it relates to portfolio exposure: 32.2% of weight (NVDA + TSLA) is directly linked, so date status moving has a real impact on the preparation score.",
    "What makes the score uncertain: none of the events are CONFIRMED; the schedule could shift and re-rank the scores.",
  ],
  watchpoints: [
    {
      label: "Date status transition",
      description:
        "Watch for SPECULATIVE / TENTATIVE moving to REPORTED or CONFIRMED — this would raise confidence.",
      tone: "info",
    },
    {
      label: "Linked news count rising",
      description:
        "A surge in linked news count typically front-runs the event window.",
      tone: "info",
    },
    {
      label: "Regime multiplier shift",
      description:
        "If regime flips to RISK_ON_OVERHEAT / DISTRIBUTION_RISK / DEFENSIVE_TRANSITION, multipliers re-weight scores.",
      tone: "warning",
    },
  ],
  dateStatusBadgeTone: {
    CONFIRMED: "success",
    WINDOW: "info",
    TENTATIVE: "warning",
    REPORTED: "warning",
    SPECULATIVE: "purple",
  },
  safetyCaption:
    "Event risk score = preparation / exposure score only. It is not a price direction prediction.",
};
