import type { Numeric } from "@/shared/lib/format";

export type JudgmentTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "success";

export type ConfidenceLevel = "LOW" | "MODERATE" | "HIGH";
export type SentimentLabel =
  | "POSITIVE"
  | "NEGATIVE"
  | "NEUTRAL"
  | "MIXED"
  | "UNKNOWN";
export type RiskLevel = "GREEN" | "YELLOW" | "ORANGE" | "RED" | "UNKNOWN";

export interface NewsJudgmentHeader {
  headline: string;
  confidence: ConfidenceLevel;
  dominantTheme: string;
  portfolioRelevance: string;
  eventLinkage: string;
  sentimentTone: SentimentLabel;
  riskTone: RiskLevel;
  tone: JudgmentTone;
}

export interface NewsDriver {
  label: string;
  value: string;
  detail: string;
}

export interface NewsConflict {
  label: string;
  description: string;
  tone: JudgmentTone;
}

export interface NewsImpactVM {
  ticker: string | null;
  sector: string | null;
  theme: string | null;
  eventKey: string | null;
  impactScore: Numeric;
  sentimentLabel: SentimentLabel;
  riskLevel: RiskLevel;
  isEventLinked: boolean;
}

export interface NewsArticleVM {
  id: string;
  title: string;
  source: string;
  url: string;
  publishedAt: string;
  summary: string;
  impacts: NewsImpactVM[];
}

export interface NewsImpactMapEntry {
  label: string;
  dimension: "ticker" | "theme" | "sector";
  articleCount: number;
  sentiment: SentimentLabel;
  riskLevel: RiskLevel;
}

export interface NewsTickerIdentity {
  ticker: string;
  name: string;
  logoUrl: string | null;
  logoSource: "local_fallback" | "provider_cache" | "deferred";
  avatarText: string;
  brandColor: string;
}

export interface NewsWatchpoint {
  label: string;
  description: string;
  tone: JudgmentTone;
}

export interface NewsManualEntryRules {
  maxSummaryChars: number;
  forbidFullBody: boolean;
  disclaimer: string;
}

export interface NewsSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface NewsIntelligenceData {
  generatedAt: string;
  systemStatus: NewsSystemStatus;
  judgment: NewsJudgmentHeader;
  drivers: NewsDriver[];
  conflicts: NewsConflict[];
  holdingsRelevant: NewsArticleVM[];
  eventLinked: NewsArticleVM[];
  latestNews: NewsArticleVM[];
  impactMap: NewsImpactMapEntry[];
  tickerIdentities: NewsTickerIdentity[];
  integratedInterpretation: string[];
  watchpoints: NewsWatchpoint[];
  manualEntryRules: NewsManualEntryRules;
  safetyCaption: string;
  source: "fixture" | "live";
}

export type ManualArticleStatus = "OK" | "REJECTED" | "ERROR";

export interface ManualArticleInput {
  title: string;
  source: string;
  url: string;
  publishedAt: string;
  summary: string;
  affectedTickers: string[];
  theme: string | null;
  eventKey: string | null;
  sentiment: SentimentLabel;
  riskLevel: RiskLevel;
}

export interface ManualArticleResult {
  status: ManualArticleStatus;
  message: string;
  detail: string;
  articleId: string | null;
}
