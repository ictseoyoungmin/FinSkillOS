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
  | "seed_sample_events";

export type ProtocolStatus = "OK" | "NOOP" | "ERROR";
export type WorkerStatus = ProtocolStatus | "MISSING";
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
  safetyCaption: string;
  source: "fixture" | "live";
}

export interface ProtocolRunResult {
  protocol: ProtocolKey;
  status: ProtocolStatus;
  message: string;
  detail: string;
  ranAt: string;
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
}

export interface WorkerStatusSummary {
  status: WorkerStatus;
  latestStartedAt: string | null;
  latestFinishedAt: string | null;
  latestDetail: string;
  recentCycles: WorkerCycleRecord[];
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
