import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { QuantLabData } from "./types";

/**
 * Run a descriptive strategy simulation over stored historical bars.
 * Research / simulation only — never real trading.
 */
export async function fetchQuantLab(
  strategy?: string,
  ticker?: string,
  signal?: AbortSignal,
): Promise<QuantLabData> {
  const params = new URLSearchParams();
  if (strategy) params.set("strategy", strategy);
  if (ticker) params.set("ticker", ticker);
  const query = params.toString();
  const path = query
    ? `${apiEndpoints.quantLab}?${query}`
    : apiEndpoints.quantLab;
  return await getJson<QuantLabData>(path, { signal });
}
