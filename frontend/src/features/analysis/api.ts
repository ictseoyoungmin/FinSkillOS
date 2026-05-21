import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { analysisWorkspaceFixture } from "@/mocks/fixtures/analysisWorkspace.fixture";
import type { AnalysisWorkspaceData } from "./types";

/**
 * Read the Analysis Workspace / Index Lab snapshot.
 *
 * Same fixture-fallback contract as the Control Room: 5xx errors
 * surface, 4xx / network errors degrade to the deterministic fixture
 * so the cockpit always renders. Track removal of the silent fallback
 * with the 13.6 cleanup §7 TODO.
 */
export async function fetchAnalysisWorkspace(
  signal?: AbortSignal,
): Promise<AnalysisWorkspaceData> {
  try {
    return await getJson<AnalysisWorkspaceData>(
      apiEndpoints.analysisWorkspace,
      { signal },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return analysisWorkspaceFixture;
  }
}
