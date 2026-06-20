import type { JudgmentHeaderData } from "@/shared/types/evidence";

export interface QuantSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface QuantStrategyOption {
  id: string;
  name: string;
  description: string;
}

export interface QuantStrategySummary {
  id: string;
  name: string;
  description: string;
  ticker: string;
  entryText: string;
  exitText: string;
}

export interface QuantEquityPoint {
  date: string;
  strategy: number;
  benchmark: number;
  exposure: boolean;
  regime: string | null;
}

export interface QuantSegment {
  start: string;
  end: string;
}

export interface QuantMetrics {
  totalReturn: number | null;
  cagr: number | null;
  annualVolatility: number | null;
  sharpe: number | null;
  sortino: number | null;
  maxDrawdown: number | null;
  calmar: number | null;
  exposurePct: number;
  roundTrips: number;
  winRate: number | null;
}

export interface QuantDataState {
  source: string;
  ticker: string;
  barCount: number;
  regimeCovered: boolean;
  dataNote: string;
}

export interface QuantLabData {
  generatedAt: string;
  systemStatus: QuantSystemStatus;
  judgment: JudgmentHeaderData;
  strategy: QuantStrategySummary;
  metrics: QuantMetrics;
  equityCurve: QuantEquityPoint[];
  exposureSegments: QuantSegment[];
  availableStrategies: QuantStrategyOption[];
  availableTickers: string[];
  safetyCaption: string;
  dataState: QuantDataState;
  warnings: string[];
}
