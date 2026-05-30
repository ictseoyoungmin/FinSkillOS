import { expect, test } from "@playwright/test";

/**
 * Slice 88 — when a product tab's live fetch fails, the page no longer silently
 * shows the fixture as if it were live. It renders the fixture *shape* plus an
 * explicit "live data unavailable" pill.
 */
test("Market Kernel shows a live-data-unavailable pill when its API fails", async ({
  page,
}) => {
  await page.route("**/api/market-kernel**", (route) => route.abort());

  await page.goto("/market-kernel");
  await expect(page.getByTestId("market-kernel-page")).toBeVisible();

  const pill = page.getByTestId("market-kernel-live-failed");
  await expect(pill).toBeVisible();
  await expect(pill).toContainText("Live data unavailable");
});

test("Analysis Workspace shows a live-data-unavailable pill when its API fails", async ({
  page,
}) => {
  await page.route("**/api/analysis-workspace**", (route) => route.abort());

  await page.goto("/analysis-workspace");
  await expect(page.getByTestId("analysis-workspace-page")).toBeVisible();

  const pill = page.getByTestId("analysis-workspace-live-failed");
  await expect(pill).toBeVisible();
  await expect(pill).toContainText("Live data unavailable");
});

test("no live-data-unavailable pill when the API responds", async ({ page }) => {
  await page.goto("/market-kernel");
  await page.waitForSelector('[data-testid="market-kernel-page"]');
  await expect(page.getByTestId("market-kernel-live-failed")).toHaveCount(0);
});
