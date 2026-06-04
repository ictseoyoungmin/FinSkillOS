import type { Numeric } from "@/shared/lib/format";
import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

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

// --- Slice 13.8 (Mission Control) ---------------------------------------

export type MilestoneState = "PENDING" | "APPROACHING" | "COMPLETED";

export type CapitalMapTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "success";

export interface GoalTracker {
  currentValue: Numeric;
  targetValue: Numeric;
  remainingValue: Numeric;
  progressPct: Numeric;
  progressRatio: Numeric;
  goalMode: string;
  earlyStopTriggered: boolean;
  phase: string;
  challengeLabel: string;
}

export interface MilestoneItem {
  pct: number;
  label: string;
  state: MilestoneState;
}

export interface PortfolioSnapshotPanelData {
  totalValue: Numeric;
  cashValue: Numeric;
  positionCount: number;
  largestPositionTicker: string | null;
  largestPositionWeightPct: Numeric;
  overSingleLimitTickers: string[];
}

export interface CapitalMapSlice {
  label: string;
  weightPct: Numeric;
  tone: CapitalMapTone;
}

export interface PortfolioReconciliation {
  status: "OK" | "MISMATCH" | "NO_BASELINE";
  snapshotTotal: Numeric;
  positionsValue: Numeric;
  cashValue: Numeric;
  reconciledTotal: Numeric;
  drift: Numeric;
  driftPct: Numeric;
  detail: string;
}

// --- Slice 158 (manual entry / edit) ------------------------------------

export interface PositionRow {
  id: string;
  ticker: string;
  quantity: Numeric;
  marketValue: Numeric;
  averageCost: Numeric | null;
  pnlPct: Numeric | null;
  sector: string | null;
  theme: string | null;
  strategyType: string;
  thesis: string | null;
}

export interface PositionInput {
  ticker: string;
  quantity: Numeric;
  marketValue: Numeric;
  averageCost?: Numeric | null;
  sector?: string | null;
  theme?: string | null;
  strategyType?: string;
  thesis?: string | null;
}

export interface SnapshotBaselineInput {
  totalValue?: Numeric | null;
  cashValue?: Numeric | null;
}

export interface MissionControlSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface MissionControlData {
  generatedAt: string;
  systemStatus: MissionControlSystemStatus;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  interpretation: IntegratedInterpretationData;
  watchpoints: EvidenceWatchpointData[];
  goal: GoalTracker;
  milestones: MilestoneItem[];
  portfolio: PortfolioSnapshotPanelData;
  reconciliation?: PortfolioReconciliation;
  positions?: PositionRow[];
  capitalMap: CapitalMapSlice[];
  themeMap: CapitalMapSlice[];
  challengeStatusCaption: string;
  safetyCaption: string;
  source: "fixture" | "live";
}
