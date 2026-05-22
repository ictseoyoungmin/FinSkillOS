import { expect, test, type Page, type ViewportSize } from "@playwright/test";
import { gotoControlRoom } from "./_helpers";

/**
 * Slice 13.10 — Responsive smoke for the Control Room route.
 *
 * The v4.1 mockup CSS collapses to a single column at ≤ 980 px. This
 * suite only verifies that the layout still holds together at the two
 * canonical viewports — it does not commit a separate screenshot
 * baseline per viewport (that is intentionally deferred so we do not
 * pin DPI-sensitive PNGs to mobile layouts in this slice).
 *
 * Assertions per viewport:
 *  - No horizontal scrollbar on the workspace
 *    (documentElement.scrollWidth ≤ innerWidth + 8 px tolerance).
 *  - OS tray, ticker strip, and the Control Room grid stay visible.
 *  - No element extends past scrollWidth + 8 px.
 */

const VIEWPORTS: readonly { name: string; size: ViewportSize }[] = [
  { name: "desktop-1440x900", size: { width: 1440, height: 900 } },
  { name: "narrow-980x720", size: { width: 980, height: 720 } },
];

const OVERFLOW_TOLERANCE_PX = 8;

async function assertNoHorizontalOverflow(page: Page): Promise<void> {
  const { scrollWidth, innerWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  expect(scrollWidth).toBeLessThanOrEqual(innerWidth + OVERFLOW_TOLERANCE_PX);
}

async function assertNoElementOverflowsViewport(page: Page): Promise<void> {
  const overflowingCount = await page.evaluate((tolerance) => {
    const limit = document.documentElement.scrollWidth + tolerance;
    const elements = Array.from(document.body.querySelectorAll<HTMLElement>("*"));
    let overflowing = 0;
    for (const element of elements) {
      const rect = element.getBoundingClientRect();
      if (rect.right > limit) {
        overflowing += 1;
      }
    }
    return overflowing;
  }, OVERFLOW_TOLERANCE_PX);
  expect(overflowingCount).toBe(0);
}

test.describe("Slice 13.10 — Control Room responsive smoke", () => {
  for (const viewport of VIEWPORTS) {
    test(`layout holds at ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize(viewport.size);
      await gotoControlRoom(page);

      await expect(page.getByTestId("os-tray")).toBeVisible();
      await expect(page.getByTestId("ticker-strip")).toBeVisible();
      await expect(page.getByTestId("control-room-grid")).toBeVisible();

      await assertNoHorizontalOverflow(page);
      await assertNoElementOverflowsViewport(page);
    });
  }
});
