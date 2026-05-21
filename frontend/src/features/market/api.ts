import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { marketKernelFixture } from "@/mocks/fixtures/marketKernel.fixture";
import type { MarketKernelData } from "./kernel-types";

/**
 * Read the Market Kernel snapshot for a single ticker.
 *
 * Slice 13.7 mirrors the 13.6 Control Room strategy: prefer the live
 * payload but degrade to the deterministic fixture on network / 4xx
 * errors so the cockpit always renders. 5xx errors still surface so
 * users notice a real API outage.
 *
 * TODO(13.8+): swap the silent fallback for an explicit failure pill
 * once the route reads live DB. Tracking lives in
 * .devmd/13_6_Frontend_Migration_Shell.md §7.
 */
export async function fetchMarketKernel(
  ticker: string,
  signal?: AbortSignal,
): Promise<MarketKernelData> {
  try {
    const path = `${apiEndpoints.marketKernel}?ticker=${encodeURIComponent(ticker)}`;
    return await getJson<MarketKernelData>(path, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return marketKernelFixture(ticker);
  }
}
