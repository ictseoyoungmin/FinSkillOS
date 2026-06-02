import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { RiskFirewallData } from "./types";

/**
 * Read the Risk Firewall snapshot.
 *
 * Slice 119: errors surface to React Query so fixture-shaped content is never
 * shown as if it were live guard evidence.
 */
export async function fetchRiskFirewall(
  signal?: AbortSignal,
): Promise<RiskFirewallData> {
  return await getJson<RiskFirewallData>(apiEndpoints.riskFirewall, { signal });
}
