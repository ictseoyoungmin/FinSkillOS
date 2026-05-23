import type { Numeric } from "@/shared/lib/format";
import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

export type UniverseKind = "FOCUS" | "INDEX_ETF" | "SECTOR_ETF" | "MACRO_PROXY";

export interface UniverseTicker {
  symbol: string;
  label: string;
  kind: UniverseKind;
}

export interface MarketBarPoint {
  barTime: string;
  open: Numeric | null;
  high: Numeric | null;
  low: Numeric | null;
  close: Numeric;
  volume: Numeric | null;
}

export interface IndicatorSnapshot {
  rsi14: Numeric | null;
  ema20: Numeric | null;
  ema60: Numeric | null;
  ema120: Numeric | null;
  bbPosition: Numeric | null;
  volumeZScore: Numeric | null;
  momentumScore: Numeric | null;
  trendState: string | null;
}

export type EventOverlayTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "purple";

export interface EventOverlayItem {
  daysToEvent: number | null;
  title: string;
  subtitle: string;
  tag: string;
  tone: EventOverlayTone;
}

export interface MarketKernelHeader {
  ticker: string;
  label: string;
  timeframe: string;
  latestClose: Numeric | null;
  latestTime: string | null;
  dataStatus: "OK" | "PARTIAL" | "MISSING";
}

export interface MarketKernelSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface MarketKernelData {
  generatedAt: string;
  systemStatus: MarketKernelSystemStatus;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  integratedInterpretation: IntegratedInterpretationData;
  reviewWatchpoints: EvidenceWatchpointData[];
  universe: UniverseTicker[];
  header: MarketKernelHeader;
  bars: MarketBarPoint[];
  indicators: IndicatorSnapshot;
  events: EventOverlayItem[];
  watchpoints: string[];
  interpretation: string;
  setupHint: string | null;
  safetyCaption: string;
  source: "fixture" | "live";
}
