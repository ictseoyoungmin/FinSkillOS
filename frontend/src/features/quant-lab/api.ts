import { getJson, sendJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { QuantLabData, QuantScreenData } from "./types";

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

/** Backtest an agent-authored free-form spec (decoded from the ?spec= deep-link). */
export async function runQuantLabSpec(
  spec: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<QuantLabData> {
  return await sendJson<QuantLabData>(
    `${apiEndpoints.quantLab}/run`,
    "POST",
    spec,
    { signal },
  );
}

/** Run one built-in strategy across many tickers, ranked (multi-asset screen). */
export async function fetchQuantLabScreen(
  strategy?: string,
  signal?: AbortSignal,
): Promise<QuantScreenData> {
  const q = strategy ? `?strategy=${encodeURIComponent(strategy)}` : "";
  return await getJson<QuantScreenData>(
    `${apiEndpoints.quantLab}/screen${q}`,
    { signal },
  );
}

/** Screen an agent-authored free-form spec across many tickers. */
export async function screenQuantLabSpec(
  spec: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<QuantScreenData> {
  return await sendJson<QuantScreenData>(
    `${apiEndpoints.quantLab}/screen`,
    "POST",
    spec,
    { signal },
  );
}

/** Decode the base64-encoded spec carried by the Quant Lab ?spec= deep-link. */
export function decodeSpecParam(raw: string): Record<string, unknown> | null {
  try {
    const bytes = Uint8Array.from(atob(raw), (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as Record<string, unknown>;
  } catch {
    return null;
  }
}
