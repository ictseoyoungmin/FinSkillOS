import type { Numeric } from "@/shared/lib/format";
import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

export type IndexKind = "INDEX_ETF" | "SECTOR_ETF" | "MACRO_PROXY";
export type DataStatus = "OK" | "PARTIAL" | "MISSING";

export interface IndexUniverseRow {
  ticker: string;
  label: string;
  kind: IndexKind;
  latestClose: Numeric | null;
  latestTime: string | null;
  rsi14: Numeric | null;
  ema20: Numeric | null;
  ema60: Numeric | null;
  bbPosition: Numeric | null;
  volumeZScore: Numeric | null;
  momentumScore: Numeric | null;
  trendState: string | null;
  dataStatus: DataStatus;
  relativeStrengthScore: Numeric | null;
  watchpoints: string[];
}

export interface TapeStrengthEntry {
  ticker: string;
  label: string;
  relativeStrengthScore: Numeric;
  trendState: string | null;
}

export interface RegimeDriver {
  label: string;
  value: string;
}

export interface RegimeContext {
  regime: string;
  confidence: Numeric;
  decisionMode: string;
  riskLevel: string;
  summary: string;
  whatHappened: string;
  whatItMeans: string;
  positiveFactors: string[];
  riskFactors: string[];
  watchNext: string[];
  snapshotTime: string | null;
  freshness?: "FRESH" | "STALE" | "UNKNOWN";
  // Slice 164: evidence attribution + confidence rationale (live only;
  // optional so fixtures stay unchanged).
  attribution?: RegimeDriver[];
  confidenceRationale?: string;
}

export interface AnalysisWorkspaceSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface AnalysisWorkspaceDataState {
  universeSource: "fixture" | "live";
  universeStatus: DataStatus;
  coverageLevel: "COMPLETE" | "PARTIAL" | "SPARSE" | "EMPTY";
  evidenceCoveragePercent: number;
  universeCount: number;
  okCount: number;
  partialCount: number;
  missingCount: number;
  rankedCount: number;
  rankedStatus: "READY" | "LIMITED" | "EMPTY";
  regimeStatus: "AVAILABLE" | "MISSING";
  latestSnapshotAt: string | null;
  missingPreview: string[];
  missingSummary: string;
  sourceNote: string;
  refreshNote: string;
}

export interface AnalysisWorkspaceData {
  generatedAt: string;
  systemStatus: AnalysisWorkspaceSystemStatus;
  dataState: AnalysisWorkspaceDataState;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  interpretation: IntegratedInterpretationData;
  watchpoints: EvidenceWatchpointData[];
  timeframe: string;
  universe: IndexUniverseRow[];
  strongest: TapeStrengthEntry[];
  weakest: TapeStrengthEntry[];
  missingData: string[];
  regime: RegimeContext | null;
  setupHint: string | null;
  safetyCaption: string;
  source: "fixture" | "live";
}
