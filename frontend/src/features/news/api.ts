import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { newsIntelligenceFixture } from "@/mocks/fixtures/newsIntelligence.fixture";
import type {
  ManualArticleInput,
  ManualArticleResult,
  NewsIntelligenceData,
} from "./types";

/**
 * Read the News Intelligence snapshot. Falls back to the deterministic
 * fixture on network / 4xx errors so the page always renders in
 * fixture-first mode. 5xx errors bubble so a real API outage is visible.
 */
export async function fetchNewsIntelligence(
  signal?: AbortSignal,
): Promise<NewsIntelligenceData> {
  try {
    return await getJson<NewsIntelligenceData>(apiEndpoints.newsIntelligence, {
      signal,
    });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return newsIntelligenceFixture;
  }
}

export async function submitManualArticle(
  input: ManualArticleInput,
  signal?: AbortSignal,
): Promise<ManualArticleResult> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}${apiEndpoints.newsManualArticle}`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as ManualArticleResult;
}
