import type { NewsArticleVM } from "../types";

function normalizeArticleText(value: string): string {
  return value
    .toLowerCase()
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[^a-z0-9가-힣]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function shouldShowArticleSummary(article: NewsArticleVM): boolean {
  const summary = normalizeArticleText(article.summary);
  if (!summary) {
    return false;
  }

  const title = normalizeArticleText(article.title);
  return title !== summary && !title.includes(summary) && !summary.includes(title);
}
