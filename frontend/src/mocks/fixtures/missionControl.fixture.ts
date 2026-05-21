import type { MissionControlData } from "@/features/portfolio/types";

/**
 * Mirrors api/fixtures/mission_control.py. Numbers line up with the
 * Control Room fixture so the two pages tell the same story when
 * the API is offline.
 */
export const missionControlFixture: MissionControlData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  goal: {
    currentValue: 73_420_000,
    targetValue: 100_000_000,
    remainingValue: 26_580_000,
    progressPct: 73.4,
    progressRatio: 0.734,
    goalMode: "BALANCED",
    earlyStopTriggered: false,
    phase: "Phase 3 / 5",
    challengeLabel: "1억 KRW challenge",
  },
  milestones: [
    { pct: 25, label: "Foundation", state: "COMPLETED" },
    { pct: 50, label: "Acceleration", state: "COMPLETED" },
    { pct: 75, label: "Approaching", state: "APPROACHING" },
    { pct: 100, label: "Challenge Complete", state: "PENDING" },
  ],
  portfolio: {
    totalValue: 73_420_000,
    cashValue: 9_200_000,
    positionCount: 4,
    largestPositionTicker: "TSLA",
    largestPositionWeightPct: 13.8,
    overSingleLimitTickers: ["TSLA"],
  },
  capitalMap: [
    { label: "AI / Semis", weightPct: 31.4, tone: "warning" },
    { label: "Mega Cap Tech", weightPct: 24.8, tone: "info" },
    { label: "EV / Robotaxi", weightPct: 13.8, tone: "warning" },
    { label: "Space / Launch", weightPct: 9.1, tone: "info" },
    { label: "Cash", weightPct: 12.5, tone: "neutral" },
    { label: "Other", weightPct: 8.4, tone: "neutral" },
  ],
  themeMap: [
    { label: "AI Infrastructure", weightPct: 28.2, tone: "warning" },
    { label: "Robotaxi", weightPct: 13.8, tone: "warning" },
    { label: "Cloud / SaaS", weightPct: 14.6, tone: "info" },
    { label: "Macro Hedge", weightPct: 5.4, tone: "info" },
  ],
  challengeStatusCaption:
    "1억 KRW challenge active · 73.4% progress · challenge complete + early-stop state remain pending.",
  safetyCaption: "Read mode — descriptive view only.",
};
