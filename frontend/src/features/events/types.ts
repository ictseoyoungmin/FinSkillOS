import type { Numeric } from "@/shared/lib/format";

export type CatalystTone = "info" | "warning" | "danger" | "neutral" | "purple";

/** Slice 13.6 Control Room — Catalyst summary row (kept for that page). */
export interface CatalystSummary {
  daysToEvent: number | null;
  title: string;
  subtitle: string;
  tag: string;
  tone: CatalystTone;
}

// --- Slice 13.9 ----------------------------------------------------------

export type EventDateStatus =
  | "CONFIRMED"
  | "WINDOW"
  | "TENTATIVE"
  | "REPORTED"
  | "SPECULATIVE";

export type EventRiskLabel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
export type EventJudgmentTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "success";
export type EventBadgeTone =
  | "success"
  | "info"
  | "warning"
  | "purple"
  | "danger";
export type EventConfidence = "LOW" | "MODERATE" | "HIGH";

export interface EventExposureJudgment {
  headline: string;
  confidence: EventConfidence;
  highestRiskEvent: string;
  clusterStatus: string;
  portfolioLinkedExposure: string;
  dateConfidenceMix: string;
  tone: EventJudgmentTone;
}

export interface EventDriver {
  label: string;
  value: string;
  detail: string;
}

export interface EventConflict {
  label: string;
  description: string;
  tone: EventJudgmentTone;
}

export interface EventLinkVM {
  ticker: string | null;
  sector: string | null;
  theme: string | null;
  eventKey: string | null;
}

export interface EventLinkedNewsVM {
  title: string;
  source: string;
  publishedAt: string;
  sentimentLabel: string;
  riskLevel: string;
  summary: string;
  url: string;
}

export interface EventRiskRow {
  eventId: string;
  title: string;
  eventType: string;
  dateStatus: EventDateStatus;
  startDate: string;
  endDate: string | null;
  daysToEvent: number | null;
  importanceScore: Numeric;
  eventRiskScore: Numeric;
  riskLabel: EventRiskLabel;
  portfolioExposure: Numeric;
  affectedTickers: string[];
  affectedSectors: string[];
  affectedThemes: string[];
  description: string | null;
  preEventNote: string;
  postEventNote: string;
  links: EventLinkVM[];
  linkedNews: EventLinkedNewsVM[];
}

export interface EventWatchpoint {
  label: string;
  description: string;
  tone: EventJudgmentTone;
}

export type EventRadarCalendarStatus =
  | "fixture_first"
  | "db_backed"
  | "empty";
export type EventRadarDateConfidenceStatus =
  | "confirmed"
  | "mixed"
  | "uncertain"
  | "missing";

export interface EventRadarDataState {
  calendarSource: "fixture" | "live";
  calendarStatus: EventRadarCalendarStatus;
  calendarDetail: string;
  eventCount: number;
  linkedNewsCount: number;
  confirmedCount: number;
  uncertainCount: number;
  nearestEventDays: number | null;
  dateConfidenceStatus: EventRadarDateConfidenceStatus;
  dateConfidenceDetail: string;
  sourceNote: string;
}

export interface EventRadarSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface EventRadarData {
  generatedAt: string;
  today: string;
  systemStatus: EventRadarSystemStatus;
  dataState: EventRadarDataState;
  judgment: EventExposureJudgment;
  drivers: EventDriver[];
  conflicts: EventConflict[];
  upcoming: EventRiskRow[];
  highRisk: EventRiskRow[];
  holdingsLinked: EventRiskRow[];
  linkedNews: EventLinkedNewsVM[];
  integratedInterpretation: string[];
  watchpoints: EventWatchpoint[];
  dateStatusBadgeTone: Record<string, EventBadgeTone>;
  safetyCaption: string;
  source: "fixture" | "live";
}
