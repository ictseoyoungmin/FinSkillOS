export type ProtocolKey =
  | "seed_sample_account"
  | "recompute_regime"
  | "run_risk_guards"
  | "seed_sample_events";

export type ProtocolStatus = "OK" | "NOOP" | "ERROR";
export type ProtocolTone = "info" | "warning" | "neutral" | "success";
export type DataSourceStatus = "LIVE" | "FIXTURE" | "MISSING";

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
  protocols: ProtocolCard[];
  dataSources: DataSourcePill[];
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
