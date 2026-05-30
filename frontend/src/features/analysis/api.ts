import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { AnalysisWorkspaceData } from "./types";

/**
 * Read the Analysis Workspace / Index Lab snapshot.
 *
 * Slice 88: errors surface to React Query instead of degrading silently to the
 * fixture. The page renders the deterministic fixture *shape* with an explicit
 * "live data unavailable" pill so sample data is never shown as if it were
 * live. The backend already returns explicit live/empty/error states, so a
 * thrown error here means the API itself is unreachable.
 */
export async function fetchAnalysisWorkspace(
  signal?: AbortSignal,
): Promise<AnalysisWorkspaceData> {
  return await getJson<AnalysisWorkspaceData>(apiEndpoints.analysisWorkspace, {
    signal,
  });
}
