import { getJson, sendJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { QuantLabData, QuantPortfolioData, QuantScreenData } from "./types";

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

/** Equal-weight portfolio synthesis of one built-in strategy across tickers. */
export async function fetchQuantLabPortfolio(
  strategy?: string,
  tickers?: string,
  signal?: AbortSignal,
): Promise<QuantPortfolioData> {
  const p = new URLSearchParams();
  if (strategy) p.set("strategy", strategy);
  if (tickers) p.set("tickers", tickers);
  const q = p.toString();
  return await getJson<QuantPortfolioData>(
    `${apiEndpoints.quantLab}/portfolio${q ? `?${q}` : ""}`,
    { signal },
  );
}

/** Portfolio synthesis of an agent-authored free-form spec. */
export async function portfolioQuantLabSpec(
  spec: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<QuantPortfolioData> {
  return await sendJson<QuantPortfolioData>(
    `${apiEndpoints.quantLab}/portfolio`,
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
