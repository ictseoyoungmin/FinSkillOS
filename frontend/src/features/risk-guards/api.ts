import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { riskFirewallFixture } from "@/mocks/fixtures/riskFirewall.fixture";
import type { RiskFirewallData } from "./types";

/**
 * Read the Risk Firewall snapshot. Slice 13.8 keeps the same
 * fallback strategy used by Slice 13.6 / 13.7: prefer the live API,
 * degrade to the deterministic fixture on network / 4xx errors so
 * the cockpit always renders the descriptive baseline. 5xx errors
 * still bubble so users notice a real API outage.
 */
export async function fetchRiskFirewall(
  signal?: AbortSignal,
): Promise<RiskFirewallData> {
  try {
    return await getJson<RiskFirewallData>(apiEndpoints.riskFirewall, {
      signal,
    });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return riskFirewallFixture;
  }
}
