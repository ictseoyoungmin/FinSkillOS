import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { systemOpsFixture } from "@/mocks/fixtures/systemOps.fixture";
import type {
  ProtocolKey,
  ProtocolRunResult,
  SystemOpsData,
  SystemOpsRuntimeSettings,
  SystemOpsRuntimeSettingsPayload,
  SystemStatusData,
  WorkerLiveModeResult,
  WorkerStatusSummary,
} from "./types";

const PROTOCOL_PATHS: Record<ProtocolKey, string> = {
  seed_sample_account: "/system-ops/seed-sample-account",
  refresh_news: "/system-ops/refresh-news",
  refresh_market_data: "/system-ops/refresh-market-data",
  calculate_indicators: "/system-ops/calculate-indicators",
  recompute_regime: "/system-ops/recompute-regime",
  run_risk_guards: "/system-ops/run-risk-guards",
  seed_sample_events: "/system-ops/seed-sample-events",
  refresh_events: "/system-ops/refresh-events",
};

/**
 * Read the System Ops protocol catalogue.
 *
 * Slice 119: the main catalogue read surfaces live failures to React Query.
 * System status keeps its explicit MISSING fallback because it powers the
 * global DB-unavailable shell contract.
 */
export async function fetchSystemOps(
  signal?: AbortSignal,
): Promise<SystemOpsData> {
  return await getJson<SystemOpsData>(apiEndpoints.systemOps, { signal });
}

export async function fetchSystemStatus(
  signal?: AbortSignal,
): Promise<SystemStatusData> {
  try {
    return await getJson<SystemStatusData>(apiEndpoints.systemStatus, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return systemStatusFallback();
  }
}

/**
 * Run one operational protocol. The backend always responds with a
 * structured ProtocolRunResult — never raw HTML or stack traces. The
 * React confirm dialog quotes the result back to the user.
 */
export async function runSystemOpsProtocol(
  key: ProtocolKey,
  signal?: AbortSignal,
): Promise<ProtocolRunResult> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}${PROTOCOL_PATHS[key]}`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as ProtocolRunResult;
}

/** Toggle the worker's automatic live refresh on/off. */
export async function setWorkerLiveMode(
  liveMode: boolean,
  signal?: AbortSignal,
): Promise<WorkerLiveModeResult> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}/system-ops/worker-live-mode`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ liveMode }),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as WorkerLiveModeResult;
}

/** Re-enqueue a finished worker job to recover a failed (or re-run a done) refresh. */
export async function retryWorkerJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<WorkerStatusSummary> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}/system-ops/worker-jobs/${jobId}/retry`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as WorkerStatusSummary;
}

export async function fetchRuntimeSettings(
  signal?: AbortSignal,
): Promise<SystemOpsRuntimeSettings> {
  return await getJson<SystemOpsRuntimeSettings>(
    `${apiEndpoints.systemOps}/runtime-settings`,
    { signal },
  );
}

export async function updateRuntimeSettings(
  values: Record<string, string | number | boolean | null>,
  signal?: AbortSignal,
): Promise<SystemOpsRuntimeSettings> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}/system-ops/runtime-settings`;
  const response = await fetch(url, {
    method: "PATCH",
    credentials: "omit",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      values,
    } as SystemOpsRuntimeSettingsPayload),
    signal,
  });
  if (!response.ok) {
    let detail = "Could not update runtime settings.";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string" && payload.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = `${response.status} ${response.statusText}`;
    }
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText}: ${detail} for ${url}`,
    );
  }
  return (await response.json()) as SystemOpsRuntimeSettings;
}

function systemStatusFallback(): SystemStatusData {
  return {
    generatedAt: systemOpsFixture.generatedAt,
    mode: "READ_MODE",
    apiStatus: "LIVE",
    dbStatus: "MISSING",
    source: "fixture",
    dataCompleteness: "missing",
    latestPortfolioSnapshotAt: null,
    latestMarketBarAt: null,
    latestIndicatorAt: null,
    latestRegimeAt: null,
    latestNewsAt: null,
    latestEventAt: null,
    staleFlags: ["system_status_unavailable"],
    protocolAvailability: systemOpsFixture.protocols.map((protocol) => ({
      key: protocol.key,
      status: "UNAVAILABLE",
      detail: "System status endpoint is unavailable; fixture fallback is shown.",
    })),
  };
}
