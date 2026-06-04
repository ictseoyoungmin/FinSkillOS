import type { Numeric } from "@/shared/lib/format";

export type TradeSide = "LONG" | "SHORT" | "WATCH" | "EXIT_REVIEW" | "OTHER";

export type TradeJudgmentTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "success";

export type TradeConfidence = "LOW" | "MODERATE" | "HIGH";

export interface ProcessJudgmentHeader {
  headline: string;
  confidence: TradeConfidence;
  bestCondition: string;
  weakestCondition: string;
  repeatedMistake: string;
  reviewPriority: string;
  tone: TradeJudgmentTone;
}

export interface TradeDriver {
  label: string;
  value: string;
  detail: string;
}

export interface TradeConflict {
  label: string;
  description: string;
  tone: TradeJudgmentTone;
}

export interface TradeWatchpoint {
  label: string;
  description: string;
  tone: TradeJudgmentTone;
}

export interface TradeEntryVM {
  id: string;
  tradeDate: string;
  ticker: string;
  side: string;
  strategyType: string | null;
  amount: Numeric | null;
  marketRegime: string | null;
  emotionState: string | null;
  resultPnl: Numeric | null;
  resultPnlPct: Numeric | null;
  rMultiple: Numeric | null;
  mistakeTags: string[];
  catalyst: string | null;
  sector: string | null;
  theme: string | null;
  notes: string | null;
  thesis: string | null;
  reason: string | null;
}

export interface PerformanceBucketVM {
  key: string;
  tradeCount: number;
  totalPnl: Numeric;
  avgPnl: Numeric;
  avgRMultiple: Numeric | null;
  winRate: Numeric | null;
}

export interface MistakeFrequencyVM {
  tag: string;
  count: number;
  losingTradeCount: number;
  avgPnl: Numeric | null;
}

export interface WeeklyReviewVM {
  startDate: string;
  endDate: string;
  tradeCount: number;
  totalPnl: Numeric;
  winRate: Numeric | null;
  mostCommonMistakes: MistakeFrequencyVM[];
  bestRegime: PerformanceBucketVM | null;
  weakestRegime: PerformanceBucketVM | null;
  processNotes: string[];
  markdown: string;
}

export interface TradeFormRules {
  allowedSides: TradeSide[];
  defaultMistakeTags: string[];
  disclaimer: string;
}

export interface TradeMemorySystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface TradeMemoryData {
  generatedAt: string;
  today: string;
  systemStatus: TradeMemorySystemStatus;
  judgment: ProcessJudgmentHeader;
  drivers: TradeDriver[];
  conflicts: TradeConflict[];
  recentEntries: TradeEntryVM[];
  performanceByRegime: PerformanceBucketVM[];
  performanceBySectorTheme: PerformanceBucketVM[];
  performanceByStrategy: PerformanceBucketVM[];
  mistakeFrequency: MistakeFrequencyVM[];
  weeklyReview: WeeklyReviewVM;
  integratedInterpretation: string[];
  watchpoints: TradeWatchpoint[];
  formRules: TradeFormRules;
  safetyCaption: string;
  source: "fixture" | "live";
}

export type TradeEntryStatus = "OK" | "REJECTED" | "ERROR";

export interface TradeEntryInput {
  tradeDate: string;
  ticker: string;
  side: TradeSide;
  strategyType?: string | null;
  amount?: Numeric | null;
  quantity?: Numeric | null;
  price?: Numeric | null;
  fees?: Numeric | null;
  reason?: string | null;
  thesis?: string | null;
  catalyst?: string | null;
  marketRegime?: string | null;
  emotionState?: string | null;
  resultPnl?: Numeric | null;
  resultPnlPct?: Numeric | null;
  rMultiple?: Numeric | null;
  mistakeTags?: string[];
  notes?: string | null;
  sector?: string | null;
  theme?: string | null;
  eventKey?: string | null;
}

export interface TradeEntryResult {
  status: TradeEntryStatus;
  message: string;
  detail: string;
  entryId: string | null;
}

// --- Slice 160 (CSV import) ---------------------------------------------

export interface TradeImportRow {
  lineNo: number;
  tradeDate: string;
  ticker: string;
  side: string;
  status: "OK" | "INVALID";
  error: string;
}

export interface TradeImportResult {
  status: "PREVIEW" | "APPLIED" | "ERROR";
  valid: number;
  invalid: number;
  totalRows: number;
  rows: TradeImportRow[];
  errors: string[];
  detail: string;
}
