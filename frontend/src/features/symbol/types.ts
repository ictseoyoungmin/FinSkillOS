import type { Numeric } from "@/shared/lib/format";
import type { IndicatorSnapshot } from "@/features/market/kernel-types";
import type { RegimeContext } from "@/features/analysis/types";

export type DataStatus = "OK" | "PARTIAL" | "MISSING";

export interface SymbolPosition {
  ticker: string;
  sector: string | null;
  theme: string | null;
  strategyType: string | null;
  marketValue: Numeric | null;
  portfolioWeight: Numeric | null;
  pnlPct: Numeric | null;
  quantity: Numeric | null;
  thesis: string | null;
  overSinglePositionLimit: boolean;
}

export interface SymbolRecentBar {
  barTime: string;
  open: Numeric | null;
  high: Numeric | null;
  low: Numeric | null;
  close: Numeric;
  volume: Numeric | null;
}

export interface SymbolAlert {
  guardName: string;
  severity: string;
  title: string;
  message: string;
  alertDate: string;
}

export interface SymbolNewsItem {
  title: string;
  source: string;
  publishedAt: string;
  sentimentLabel: string;
  impactScore: Numeric;
  riskNote: string | null;
  url: string;
}

export interface SymbolLabHeader {
  ticker: string;
  timeframe: string;
  latestClose: Numeric | null;
  latestTime: string | null;
  dataStatus: DataStatus;
}

export interface SymbolLabSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface SymbolLabData {
  generatedAt: string;
  systemStatus: SymbolLabSystemStatus;
  header: SymbolLabHeader;
  technical: IndicatorSnapshot;
  recentBars: SymbolRecentBar[];
  position: SymbolPosition | null;
  alerts: SymbolAlert[];
  news: SymbolNewsItem[];
  regime: RegimeContext | null;
  watchpoints: string[];
  interpretation: string;
  setupHint: string | null;
  safetyCaption: string;
  source: "fixture" | "live";
}
