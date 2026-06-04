import { getJson, sendJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type {
  MissionControlData,
  PortfolioImportResult,
  PositionInput,
  SnapshotBaselineInput,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

/**
 * Read the Mission Control snapshot.
 *
 * Slice 119: errors surface to React Query. The page may keep the deterministic
 * placeholder shape, but failed live evidence must be visible.
 */
export async function fetchMissionControl(
  signal?: AbortSignal,
): Promise<MissionControlData> {
  return await getJson<MissionControlData>(apiEndpoints.missionControl, {
    signal,
  });
}

// --- Slice 158: descriptive portfolio editing (no execution) ---------------
// Each mutation returns the refreshed Mission Control snapshot so the page
// (and the reconciliation line) updates in place.

export async function createPosition(
  input: PositionInput,
): Promise<MissionControlData> {
  return await sendJson<MissionControlData>(
    `${apiEndpoints.missionControl}/positions`,
    "POST",
    input,
  );
}

export async function updatePosition(
  positionId: string,
  input: PositionInput,
): Promise<MissionControlData> {
  return await sendJson<MissionControlData>(
    `${apiEndpoints.missionControl}/positions/${positionId}`,
    "PUT",
    input,
  );
}

export async function deletePosition(
  positionId: string,
): Promise<MissionControlData> {
  return await sendJson<MissionControlData>(
    `${apiEndpoints.missionControl}/positions/${positionId}`,
    "DELETE",
  );
}

export async function clearPositions(): Promise<MissionControlData> {
  return await sendJson<MissionControlData>(
    `${apiEndpoints.missionControl}/clear-positions`,
    "POST",
  );
}

export async function updateSnapshotBaseline(
  input: SnapshotBaselineInput,
): Promise<MissionControlData> {
  return await sendJson<MissionControlData>(
    `${apiEndpoints.missionControl}/snapshot`,
    "PATCH",
    input,
  );
}

// --- Slice 159: CSV import / export ----------------------------------------

/** Fetch the current holdings as CSV and trigger a browser download. */
export async function downloadPositionsCsv(): Promise<void> {
  const url = `${API_BASE}${apiEndpoints.missionControl}/positions/export.csv`;
  const response = await fetch(url, {
    credentials: "omit",
    headers: { Accept: "text/csv" },
  });
  if (!response.ok) {
    throw new Error(`Export failed: ${response.status} ${response.statusText}`);
  }
  const blob = await response.blob();
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = "portfolio_positions.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(href);
}

/** Dry-run an import (preview adds/updates); never mutates. */
export async function previewImportPositions(
  csvText: string,
): Promise<PortfolioImportResult> {
  return await sendJson<PortfolioImportResult>(
    `${apiEndpoints.missionControl}/import-positions`,
    "POST",
    { csvText },
  );
}

/** Apply an import (upsert). Returns the result with the refreshed snapshot. */
export async function applyImportPositions(
  csvText: string,
): Promise<PortfolioImportResult> {
  return await sendJson<PortfolioImportResult>(
    `${apiEndpoints.missionControl}/import-positions?confirm=true`,
    "POST",
    { csvText },
  );
}
