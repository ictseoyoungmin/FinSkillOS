import { getJson, sendJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type {
  MissionControlData,
  PositionInput,
  SnapshotBaselineInput,
} from "./types";

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
