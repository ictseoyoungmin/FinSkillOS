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

async function assertTickerWorkspaceBoundary(page: Page): Promise<void> {
  const boundary = await page.evaluate(() => {
    const ticker = document.querySelector<HTMLElement>(
      '[data-testid="ticker-strip"]',
    );
    const workspace = document.querySelector<HTMLElement>(
      '[data-testid="os-workspace"]',
    );
    if (!ticker || !workspace) {
      return null;
    }
    const tickerStyle = window.getComputedStyle(ticker);
    const workspaceStyle = window.getComputedStyle(workspace);
    return {
      tickerShadow: tickerStyle.boxShadow,
      workspaceBorderTopWidth: workspaceStyle.borderTopWidth,
      workspacePaddingTop: workspaceStyle.paddingTop,
      gap: Math.round(
        workspace.getBoundingClientRect().top - ticker.getBoundingClientRect().bottom,
      ),
    };
  });

  expect(boundary).not.toBeNull();
  expect(boundary?.tickerShadow).not.toBe("none");
  expect(boundary?.workspaceBorderTopWidth).toBe("1px");
  expect(
    Number.parseFloat(boundary?.workspacePaddingTop ?? "0"),
  ).toBeGreaterThanOrEqual(20);
  expect(boundary?.gap).toBe(0);
}

async function assertControlRoomUsesWorkspaceScroll(page: Page): Promise<void> {
  const columnOverflow = await page
    .locator(".fso-control-column")
    .evaluateAll((columns) =>
      columns.map((column) => {
        const style = window.getComputedStyle(column);
        return {
          overflowX: style.overflowX,
          overflowY: style.overflowY,
        };
      }),
    );

  expect(columnOverflow).toHaveLength(3);
  for (const overflow of columnOverflow) {
    expect(overflow.overflowX).toBe("visible");
    expect(overflow.overflowY).toBe("visible");
  }
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
      await assertTickerWorkspaceBoundary(page);
      await assertControlRoomUsesWorkspaceScroll(page);
    });
  }
});
