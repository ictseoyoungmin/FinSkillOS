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
  timeframe = "1d",
  signal?: AbortSignal,
): Promise<SymbolLabData> {
  try {
    const params = new URLSearchParams({
      ticker,
      timeframe,
    });
    const path = `${apiEndpoints.symbolLab}?${params.toString()}`;
    return await getJson<SymbolLabData>(path, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return symbolLabFixture(ticker);
  }
}

export async function setSymbolSubscription(
  ticker: string,
  subscribed: boolean,
  timeframe = "1d",
  signal?: AbortSignal,
): Promise<SymbolLabData> {
  const action = subscribed ? "subscribe" : "unsubscribe";
  const params = new URLSearchParams({ timeframe });
  const path = `${apiEndpoints.symbolLab}/${encodeURIComponent(
    ticker,
  )}/${action}?${params.toString()}`;
  return await getJson<SymbolLabData>(path, {
    method: "POST",
    signal,
  });
}
