import { expect, test } from "@playwright/test";
import { forceFixtureSnapshotApis, gotoControlRoom } from "../_helpers";

/**
 * Structural visual baseline. The screenshot is intentionally
 * loose-tolerant — Slice 13.6 does not require pixel-perfect parity
 * with the static v4.1 HTML mockup. We mask the clock + the
 * scrolling ticker strip (animations disabled isn't enough for
 * tickers with marquee transforms).
 *
 * The `@visual` tag in the title is filtered out of the default
 * `npm run test:e2e` script and included only by `npm run test:visual`
 * so a fresh clone without a committed baseline PNG does not break
 * structural runs (13.6 cleanup §5).
 */
test("control room visual baseline @visual", async ({ page }) => {
  await forceFixtureSnapshotApis(page);
  await gotoControlRoom(page);
  // Wait for the three columns + the new chart panel to render before
  // the snapshot.
  await page.waitForSelector('[data-testid="control-room-right"]');
  await page.waitForSelector('[data-testid="portfolio-market-tape"]');

  await expect(page).toHaveScreenshot("control-room-material.png", {
    fullPage: false,
    mask: [
      page.locator('[data-testid="clock"]'),
      page.locator('[data-testid="ticker-strip"]'),
    ],
    animations: "disabled",
  });
});
