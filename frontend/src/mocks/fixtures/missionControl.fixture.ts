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
  judgment: {
    eyebrow: "MISSION RISK JUDGMENT",
    title: "Progress Strong,",
    accent: "Risk Budget Narrows",
    summary:
      "Challenge progress is high enough that portfolio and guard context matter more than raw growth pace.",
    confidence: 74,
  },
  drivers: [
    { score: "73.4%", title: "Goal progress", note: "The challenge is approaching the 75% milestone." },
    { score: "TSLA", title: "Largest position", note: "Single-name weight remains a review factor." },
    { score: "3", title: "Guard count", note: "Risk context is active beside mission progress." },
  ],
  conflicts: [
    { title: "Strong progress vs narrowing budget", note: "Higher completion progress increases sensitivity to drawdown review." },
    { title: "Theme exposure vs cash buffer", note: "AI / EV exposure remains meaningful while cash is finite." },
  ],
  interpretation: {
    verdict: "Mission progress is strong, but the risk budget narrows.",
    whyItMatters:
      "The page connects goal progress, milestones, portfolio composition, and guard context.",
    whatRemainsUncertain:
      "Future portfolio value and concentration changes can alter the review priority.",
  },
  watchpoints: [
    { title: "75% milestone", note: "Recheck mission state as the next milestone is approached." },
    { title: "Largest position", note: "Monitor any single-name review threshold." },
    { title: "Cash buffer", note: "Track whether cash remains adequate for the current goal mode." },
  ],
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
  safetyCaption: "Read mode — Goal interpretation (not return forecast).",
};
