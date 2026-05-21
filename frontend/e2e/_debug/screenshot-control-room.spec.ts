import { test, expect } from "@playwright/test";

/**
 * Debug-only screenshot pass for Slice 13.7 follow-up overflow fix.
 *
 * Verifies that:
 *   - Risk Firewall / Catalyst Watch / Watchlist render in full at a
 *     standard desktop viewport (≥ 1400px wide).
 *   - When the viewport is too short for all three panels to fit,
 *     the column scrolls instead of clipping individual panels.
 *   - Market Kernel / Symbol Lab pages do not regress.
 */

test("control-room right column @ 1440x900 (no clipping)", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForSelector(
    '[data-testid="control-room-right"] [data-testid="risk-firewall-summary"]',
  );
  await page.screenshot({ path: "screenshots/cr-tall-full.png" });
  await page.getByTestId("control-room-right").screenshot({
    path: "screenshots/cr-tall-right.png",
  });
  // Sector Concentration must render with its full message — that
  // string was the most-clipped item in the user's bug report.
  await expect(page.getByText("Sector Concentration")).toBeVisible();
  await expect(
    page.getByText("AI / Semis exposure requires monitoring before adding risk."),
  ).toBeVisible();
  // SpaceX IPO catalyst was the second clipped item.
  await expect(page.getByText("SpaceX IPO chatter")).toBeVisible();
});

test("control-room right column @ 1440x600 (forced scroll)", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 600 });
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForSelector(
    '[data-testid="control-room-right"] [data-testid="risk-firewall-summary"]',
  );
  await page.screenshot({ path: "screenshots/cr-short-full.png" });
  await page.getByTestId("control-room-right").screenshot({
    path: "screenshots/cr-short-right.png",
  });
  // At 600px height the right column must scroll to expose content
  // further down. The Watchlist panel sits at the bottom — scrolling
  // the column should make it visible.
  const column = page.getByTestId("control-room-right");
  await column.evaluate((el) => {
    el.scrollTop = el.scrollHeight;
  });
  await page.waitForTimeout(200);
  await column.screenshot({ path: "screenshots/cr-short-right-scrolled.png" });
  await expect(page.getByTestId("watchlist-card")).toBeVisible();
});

test("market-kernel viewport @ 1440x900", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/market-kernel", { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="market-kernel-page"]');
  await page.screenshot({ path: "screenshots/mk-1440x900.png" });
});

test("symbol-lab viewport @ 1440x900", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/symbol-lab", { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="symbol-lab-page"]');
  await page.screenshot({ path: "screenshots/sl-1440x900.png" });
});
