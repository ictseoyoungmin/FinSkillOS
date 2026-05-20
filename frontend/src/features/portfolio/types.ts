export interface MissionProgress {
  currentValue: number;
  targetValue: number;
  progressPct: number;
  phase: string;
  earlyStopTriggered: boolean;
  goalMode: string;
}

export interface PortfolioExposureSlice {
  label: string;
  weightPct: number;
}

export interface ReviewQueueItem {
  title: string;
  note: string;
  tag: "weekly" | "mistake" | "thesis" | "event";
}
