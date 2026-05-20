import type { Numeric } from "@/shared/lib/format";

export interface MissionProgress {
  currentValue: Numeric;
  targetValue: Numeric;
  progressPct: Numeric;
  phase: string;
  earlyStopTriggered: boolean;
  goalMode: string;
}

export interface PortfolioExposureSlice {
  label: string;
  weightPct: Numeric;
}

export interface ReviewQueueItem {
  title: string;
  note: string;
  tag: "weekly" | "mistake" | "thesis" | "event";
}
