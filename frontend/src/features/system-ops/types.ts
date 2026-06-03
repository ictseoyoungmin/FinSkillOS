import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

export type ProtocolKey =
  | "seed_sample_account"
  | "refresh_news"
  | "refresh_market_data"
  | "calculate_indicators"
  | "recompute_regime"
  | "run_risk_guards"
  | "seed_sample_events"
  | "refresh_events";

export type ProtocolStatus = "OK" | "NOOP" | "ERROR" | "QUEUED";
export type WorkerStatus = ProtocolStatus | "MISSING";
export type WorkerCadenceStatus = "FRESH" | "STALE" | "ERROR" | "MISSING";
export type ProtocolTone = "info" | "warning" | "neutral" | "success";
export type DataSourceStatus = "LIVE" | "FIXTURE" | "MISSING";
export type ApiStatus = "LIVE";
export type DbStatus = "LIVE" | "MISSING";
export type SystemStatusSource = "fixture" | "live";
export type DataCompleteness = "complete" | "partial" | "missing";
export type ProtocolAvailabilityStatus = "AVAILABLE" | "NOOP" | "UNAVAILABLE";

export interface ProtocolCard {
  key: ProtocolKey;
  title: string;
  description: string;
  idempotencyNote: string;
  buttonLabel: string;
  confirmLabel: string;
  tone: ProtocolTone;
  lastRunAt: string | null;
}

export interface DataSourcePill {
  label: string;
  status: DataSourceStatus;
  detail: string;
}

export interface SystemOpsSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface SystemOpsData {
  generatedAt: string;
  systemStatus: SystemOpsSystemStatus;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  interpretation: IntegratedInterpretationData;
  watchpoints: EvidenceWatchpointData[];
  protocols: ProtocolCard[];
  dataSources: DataSourcePill[];
  recentProtocolRuns: ProtocolRunRecord[];
  workerStatus: WorkerStatusSummary;
  runtimeSettings: SystemOpsRuntimeSettings;
  safetyCaption: string;
  source: "fixture" | "live";
}

export interface RuntimeSettingChange {
  key: string;
  oldValue: string | null;
  newValue: string | null;
  updatedBy: string;
  changedAt: string | null;
}

export interface SystemOpsRuntimeSettings {
  values: Record<string, string>;
  overrides: Record<string, string>;
  capturedAt: string;
  updatedAt?: string | null;
  updatedBy?: string | null;
  history?: RuntimeSettingChange[];
}

export interface ProtocolRunResult {
  protocol: ProtocolKey;
  status: ProtocolStatus;
  message: string;
  detail: string;
  detailEvidence: ProtocolDetailEvidence[];
  ranAt: string;
}

export interface ProtocolDetailEvidence {
  key: string;
  value: string;
}

export interface ProtocolRunRecord extends ProtocolRunResult {
  dbStatus: string;
  source: "fixture" | "live";
}

export interface WorkerCycleRecord {
  status: WorkerStatus;
  startedAt: string;
  finishedAt: string;
  timeframe: string;
  marketStatus: string;
  newsStatus: string;
  indicatorStatus: string;
  marketScope: string;
  newsScope: string;
  indicatorScope: string;
  barsWritten: number;
  articlesIngested: number;
  snapshotsWritten: number;
  failures: number;
  regime: string | null;
  outcome: string;
}

export interface WorkerJobRow {
  id: string;
  jobType: string;
  status: string;
  requestedBy: string;
  folderId: string | null;
  createdAt: string | null;
  finishedAt: string | null;
  error: string | null;
  retryable: boolean;
}

export interface FeedSourceCount {
  source: string;
  count: number;
}

export interface NewsCoverage {
  totalArticles: number;
  latestPublishedAt: string | null;
  recentArticles: number;
  freshnessStatus: "FRESH" | "STALE" | "EMPTY";
  sources: FeedSourceCount[];
}

export interface EventCoverage {
  totalEvents: number;
  upcomingEvents: number;
  latestEventDate: string | null;
  sources: FeedSourceCount[];
  dateStatus: FeedSourceCount[];
}

export interface FeedCoverageReport {
  generatedAt: string;
  source: "fixture" | "live";
  news: NewsCoverage;
  events: EventCoverage;
  detail: string;
}

export interface InvariantViolation {
  ticker: string;
  timeframe: string;
  at: string;
}

export interface DataInvariantReport {
  generatedAt: string;
  source: "fixture" | "live";
  status: "OK" | "VIOLATIONS" | "UNKNOWN";
  totalSnapshots: number;
  orphanSnapshotCount: number;
  orphanSamples: InvariantViolation[];
  detail: string;
}

export interface ProvenanceSource {
  source: string;
  barCount: number;
  synthetic: boolean;
}

export interface ProvenanceTicker {
  ticker: string;
  source: string;
  latestAt: string | null;
}

export interface DataProvenanceReport {
  generatedAt: string;
  source: "fixture" | "live";
  totalBars: number;
  realBars: number;
  realRatioPercent: number;
  distinctTickers: number;
  sources: ProvenanceSource[];
  syntheticTickers: ProvenanceTicker[];
  detail: string;
}

export interface ProviderHealthTicker {
  ticker: string;
  error: string;
}

export interface ProviderHealth {
  adapter: string;
  status: "HEALTHY" | "DEGRADED" | "FAILING" | "UNKNOWN";
  lastCycleAt: string | null;
  lastSuccessAt: string | null;
  lastFailureAt: string | null;
  consecutiveFailureCycles: number;
  affectedTickers: ProviderHealthTicker[];
  detail: string;
}

export interface WorkerStatusSummary {
  status: WorkerStatus;
  cadenceStatus: WorkerCadenceStatus;
  latestStartedAt: string | null;
  latestFinishedAt: string | null;
  expectedNextCycleAt: string | null;
  latestDetail: string;
  cadenceDetail: string;
  liveMode: boolean;
  recentCycles: WorkerCycleRecord[];
  jobCounts: Record<string, number>;
  recentJobs: WorkerJobRow[];
  providerHealth: ProviderHealth;
}

export interface WorkerLiveModeResult {
  liveMode: boolean;
  message: string;
  updatedAt: string | null;
}

export interface SystemOpsRuntimeSettingsPayload {
  values: Record<string, string | number | boolean | null>;
}

export interface ProtocolAvailability {
  key: ProtocolKey;
  status: ProtocolAvailabilityStatus;
  detail: string;
}

export interface SystemStatusData {
  generatedAt: string;
  mode: "READ_MODE";
  apiStatus: ApiStatus;
  dbStatus: DbStatus;
  source: SystemStatusSource;
  dataCompleteness: DataCompleteness;
  latestPortfolioSnapshotAt: string | null;
  latestMarketBarAt: string | null;
  latestIndicatorAt: string | null;
  latestRegimeAt: string | null;
  latestNewsAt: string | null;
  latestEventAt: string | null;
  staleFlags: string[];
  protocolAvailability: ProtocolAvailability[];
}
