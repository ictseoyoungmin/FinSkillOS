import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { symbolLabFixture } from "@/mocks/fixtures/symbolLab.fixture";
import type { SymbolLabData } from "./types";

/**
 * Read the Symbol Lab snapshot for a single ticker. Same fixture
 * fallback contract as Market Kernel + Control Room.
 */
export async function fetchSymbolLab(
  ticker: string,
  signal?: AbortSignal,
): Promise<SymbolLabData> {
  try {
    const path = `${apiEndpoints.symbolLab}?ticker=${encodeURIComponent(ticker)}`;
    return await getJson<SymbolLabData>(path, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return symbolLabFixture(ticker);
  }
}
