import { expect, test } from "@playwright/test";
import { gotoControlRoom } from "../_helpers";

/**
 * Structural visual baseline. The screenshot is intentionally
 * loose-tolerant — Slice 13.6 does not require pixel-perfect parity
 * with the static v4.1 HTML mockup. We mask the clock + the
 * scrolling ticker strip (animations disabled isn't enough for
 * tickers with marquee transforms).
 */
test("control room visual baseline", async ({ page }) => {
  await gotoControlRoom(page);
  // Wait for the three columns to render before the snapshot.
  await page.waitForSelector('[data-testid="control-room-right"]');

  await expect(page).toHaveScreenshot("control-room-material.png", {
    fullPage: false,
    mask: [
      page.locator('[data-testid="clock"]'),
      page.locator('[data-testid="ticker-strip"]'),
    ],
    animations: "disabled",
  });
});
