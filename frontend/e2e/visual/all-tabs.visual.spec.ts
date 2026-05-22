import { expect, test, type Page } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS } from "../_helpers";

/**
 * Slice 13.10 — All-tabs visual + structural baseline.
 *
 * Every routed OS module gets:
 *  - A masked screenshot baseline (clock + ticker strip are masked
 *    because their content is time-dependent).
 *  - Structural assertions: OS tray + ticker strip persistence,
 *    the route title (h2 heading rendered by SectionHeader), and the
 *    route-specific primary panel.
 *  - A descriptive-only output check (no execution captions).
 *
 * The `@visual` tag keeps the screenshot specs out of the default
 * `npm run test:e2e` run (which stays structural). They are picked up
 * by `npm run test:visual` once baselines are committed, matching the
 * Slice 13.6 cleanup §5 convention.
 */

interface RouteSpec {
  /** Display label used in `test.describe`. */
  readonly label: string;
  /** Router path the test navigates to. */
  readonly path: string;
  /** Title rendered inside the page's <SectionHeader>. */
  readonly title: string;
  /**
   * testid that identifies the route-specific primary panel. The
   * structural test waits for this before asserting and the visual
   * test waits for it before snapshotting.
   */
  readonly primaryTestId: string;
  /** Filename committed under all-tabs.visual.spec.ts-snapshots/. */
  readonly screenshotName: string;
}

const ROUTES: readonly RouteSpec[] = [
  {
    label: "control-room",
    path: "/",
    title: "Control Room",
    primaryTestId: "control-room-grid",
    screenshotName: "control-room.png",
  },
  {
    label: "market-kernel",
    path: "/market-kernel",
    title: "Market Kernel",
    primaryTestId: "market-kernel-page",
    screenshotName: "market-kernel.png",
  },
  {
    label: "analysis-workspace",
    path: "/analysis-workspace",
    title: "Analysis Workspace",
    primaryTestId: "analysis-workspace-page",
    screenshotName: "analysis-workspace.png",
  },
  {
    label: "symbol-lab",
    path: "/symbol-lab",
    title: "Symbol Lab",
    primaryTestId: "symbol-lab-page",
    screenshotName: "symbol-lab.png",
  },
  {
    label: "risk-firewall",
    path: "/risk-firewall",
    title: "Risk Firewall",
    primaryTestId: "risk-firewall-page",
    screenshotName: "risk-firewall.png",
  },
  {
    label: "mission-control",
    path: "/mission-control",
    title: "Mission Control",
    primaryTestId: "mission-control-page",
    screenshotName: "mission-control.png",
  },
  {
    label: "news-intelligence",
    path: "/news-intel",
    title: "News Intelligence",
    primaryTestId: "news-intelligence-page",
    screenshotName: "news-intelligence.png",
  },
  {
    label: "catalyst-watch",
    path: "/catalyst-watch",
    title: "Catalyst Watch",
    primaryTestId: "catalyst-watch-page",
    screenshotName: "catalyst-watch.png",
  },
  {
    label: "trade-memory",
    path: "/trade-memory",
    title: "Trade Memory",
    primaryTestId: "trade-memory-page",
    screenshotName: "trade-memory.png",
  },
  {
    label: "system-ops",
    path: "/system-ops",
    title: "System Ops",
    primaryTestId: "system-ops-page",
    screenshotName: "system-ops.png",
  },
];

async function gotoRoute(page: Page, route: RouteSpec): Promise<void> {
  await page.goto(route.path);
  await page.waitForSelector(`[data-testid="${route.primaryTestId}"]`);
  // Ticker strip is rendered by OsShell and depends on the Control Room
  // React Query result. Wait for it to settle so masking + screenshot
  // diffing see a stable layout.
  await page.waitForSelector('[data-testid="ticker-strip"]');
}

test.describe("Slice 13.10 — All tabs structural baseline", () => {
  for (const route of ROUTES) {
    test(`${route.label} renders shell + title + primary panel`, async ({
      page,
    }) => {
      await gotoRoute(page, route);
      await expect(page.getByTestId("os-tray")).toBeVisible();
      await expect(page.getByTestId("ticker-strip")).toBeVisible();
      await expect(
        page.getByRole("heading", { name: route.title, exact: true }),
      ).toBeVisible();
      await expect(page.getByTestId(route.primaryTestId)).toBeVisible();

      const body = await page.locator("body").innerText();
      for (const forbidden of FORBIDDEN_EXECUTION_LABELS) {
        expect(body).not.toContain(forbidden);
      }
    });
  }
});

test.describe("Slice 13.10 — All tabs visual baseline @visual", () => {
  for (const route of ROUTES) {
    test(`${route.label} screenshot baseline @visual`, async ({ page }) => {
      await gotoRoute(page, route);

      await expect(page).toHaveScreenshot(route.screenshotName, {
        fullPage: false,
        mask: [
          page.locator('[data-testid="clock"]'),
          page.locator('[data-testid="ticker-strip"]'),
        ],
        animations: "disabled",
        maxDiffPixelRatio: 0.03,
      });
    });
  }
});
