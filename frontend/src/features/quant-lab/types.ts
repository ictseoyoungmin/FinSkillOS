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
  close: number;
  regime: string | null;
}

export interface QuantSegment {
  start: string;
  end: string;
}

export interface QuantMarker {
  date: string;
  kind: "ENTER" | "EXIT";
  price: number;
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

export interface QuantPortfolioPoint {
  date: string;
  strategy: number;
  benchmark: number;
  exposure: number;
}

export interface QuantPortfolioData {
  generatedAt: string;
  strategyName: string;
  source: string;
  tickers: string[];
  weight: number;
  curve: QuantPortfolioPoint[];
  metrics: QuantMetrics;
  safetyCaption: string;
}

export interface QuantScreenRow {
  ticker: string;
  barCount: number;
  totalReturn: number | null;
  sharpe: number | null;
  maxDrawdown: number | null;
  exposurePct: number;
  roundTrips: number;
}

export interface QuantScreenData {
  generatedAt: string;
  strategyName: string;
  source: string;
  rows: QuantScreenRow[];
  safetyCaption: string;
}

export interface QuantWindow {
  index: number;
  dateStart: string;
  dateEnd: string;
  barCount: number;
  totalReturn: number | null;
  sharpe: number | null;
  exposurePct: number;
  roundTrips: number;
}

export interface QuantFeatureCoverage {
  name: string;
  bars: number;
  pct: number;
}

export interface QuantCoverage {
  dateStart: string;
  dateEnd: string;
  barCount: number;
  features: QuantFeatureCoverage[];
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
  markers: QuantMarker[];
  availableStrategies: QuantStrategyOption[];
  availableTickers: string[];
  safetyCaption: string;
  dataState: QuantDataState;
  coverage: QuantCoverage;
  walkForward: QuantWindow[];
  warnings: string[];
}
