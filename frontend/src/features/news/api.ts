import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { NewsIntelligenceData } from "./types";

/**
 * Read the News Intelligence snapshot.
 *
 * Slice 119: errors surface to React Query so fixture-shaped news evidence is
 * marked as sample shape when live reads fail.
 */
export async function fetchNewsIntelligence(
  signal?: AbortSignal,
): Promise<NewsIntelligenceData> {
  return await getJson<NewsIntelligenceData>(apiEndpoints.newsIntelligence, {
    signal,
  });
}
