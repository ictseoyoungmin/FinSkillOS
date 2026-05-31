import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { MarketKernelData } from "./kernel-types";

/**
 * Read the Market Kernel snapshot for a single ticker.
 *
 * Slice 88: errors are no longer swallowed into a silent fixture fallback. The
 * error surfaces to React Query so the page renders the deterministic fixture
 * *shape* with an explicit "live data unavailable" pill, instead of presenting
 * sample data as if it were live. The backend already returns explicit
 * live-empty / live-error / db-unavailable states (Slices 80/82), so a thrown
 * error here means the API itself is unreachable.
 */
export async function fetchMarketKernel(
  ticker: string,
  timeframe?: string,
  signal?: AbortSignal,
): Promise<MarketKernelData> {
  const params = new URLSearchParams({ ticker });
  if (timeframe) {
    params.set("timeframe", timeframe);
  }
  return await getJson<MarketKernelData>(
    `${apiEndpoints.marketKernel}?${params.toString()}`,
    { signal },
  );
}
