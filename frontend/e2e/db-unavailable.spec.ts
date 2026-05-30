import { expect, test } from "@playwright/test";

/**
 * Slice 86 — when `/api/system-status` reports the DB is unreachable, a global
 * banner makes the offline fixture-shape explicit so it is never read as live
 * data. The explicit `X-FSO-Use-Fixture` demo keeps `dbStatus = "LIVE"`, so the
 * banner does not appear during intentional demos / visual baselines.
 */
test("global DB-unavailable banner appears when system-status reports MISSING", async ({
  page,
}) => {
  await page.route("**/api/system-status", async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    json.dbStatus = "MISSING";
    json.source = "fixture";
    json.dataCompleteness = "missing";
    json.staleFlags = ["db_unavailable"];
    await route.fulfill({ json });
  });

  await page.goto("/");

  const banner = page.getByTestId("db-unavailable-banner");
  await expect(banner).toBeVisible();
  await expect(banner).toContainText("Database unavailable");
  await expect(banner).toContainText("sample shape, not");
});

test("no DB-unavailable banner when system-status DB is live", async ({
  page,
}) => {
  await page.goto("/");
  await page.waitForSelector('[data-testid="control-room-grid"]');
  // system-status is live in the e2e stack, so the banner must never render.
  await expect(page.getByTestId("db-unavailable-banner")).toHaveCount(0);
});
