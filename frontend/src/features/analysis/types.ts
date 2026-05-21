import type { Numeric } from "@/shared/lib/format";

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
}

export interface AnalysisWorkspaceSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface AnalysisWorkspaceData {
  generatedAt: string;
  systemStatus: AnalysisWorkspaceSystemStatus;
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
