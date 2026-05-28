import { expect, test, type Page } from "@playwright/test";
import {
  forceFixtureSnapshotApis,
  FORBIDDEN_EXECUTION_LABELS,
} from "../_helpers";

interface RouteSpec {
  readonly label: string;
  readonly path: string;
  readonly eyebrow: string;
  readonly safetyCategory: string;
  readonly requiredTestIds: readonly string[];
  readonly screenshotName: string;
}

const ROUTES: readonly RouteSpec[] = [
  {
    label: "control-room",
    path: "/",
    eyebrow: "GLOBAL OPERATING VERDICT",
    safetyCategory: "Global operating posture",
    requiredTestIds: [
      "control-room-grid",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "operating-state-hero",
      "portfolio-market-tape",
      "risk-firewall-summary",
      "catalyst-watch-summary",
      "watchlist-card",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "control-room.png",
  },
  {
    label: "market-kernel",
    path: "/market-kernel",
    eyebrow: "TECHNICAL SIGNAL JUDGMENT",
    safetyCategory: "Technical interpretation",
    requiredTestIds: [
      "market-kernel-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "symbol-universe-rail",
      "ticker-search",
      "chart-panel",
      "indicator-snapshot",
      "market-interpretation",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "market-kernel.png",
  },
  {
    label: "analysis-workspace",
    path: "/analysis-workspace",
    eyebrow: "MARKET STRUCTURE JUDGMENT",
    safetyCategory: "Structural breadth read",
    requiredTestIds: [
      "analysis-workspace-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "index-universe-table",
      "relative-strength-ranking",
      "tape-strength-cards",
      "regime-context",
      "missing-data-panel",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "analysis-workspace.png",
  },
  {
    label: "symbol-lab",
    path: "/symbol-lab",
    eyebrow: "SYMBOL JUDGMENT · TSLA",
    safetyCategory: "Symbol interpretation",
    requiredTestIds: [
      "symbol-lab-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "symbol-search",
      "position-context",
      "technical-snapshot",
      "ticker-news",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "symbol-lab.png",
  },
  {
    label: "risk-firewall",
    path: "/risk-firewall",
    eyebrow: "RISK PERMISSION JUDGMENT",
    safetyCategory: "Read-only",
    requiredTestIds: [
      "risk-firewall-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "guard-result-cards",
      "active-alerts",
      "risk-protocol-panel",
      "protocol-matrix-explanation",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "risk-firewall.png",
  },
  {
    label: "mission-control",
    path: "/mission-control",
    eyebrow: "MISSION RISK JUDGMENT",
    safetyCategory: "Goal interpretation",
    requiredTestIds: [
      "mission-control-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "goal-tracker",
      "milestone-timeline",
      "capital-map",
      "portfolio-snapshot",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "mission-control.png",
  },
  {
    label: "news-intelligence",
    path: "/news-intel",
    eyebrow: "NARRATIVE JUDGMENT",
    safetyCategory: "Descriptive narrative view only",
    requiredTestIds: [
      "news-intelligence-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "holdings-relevant-news",
      "news-impact-map",
      "event-linked-news",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "news-intelligence.png",
  },
  {
    label: "catalyst-watch",
    path: "/catalyst-watch",
    eyebrow: "EVENT EXPOSURE JUDGMENT",
    safetyCategory: "preparation / exposure score",
    requiredTestIds: [
      "catalyst-watch-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "event-risk-table",
      "date-status-badges",
      "event-score-drivers",
      "event-catalog-evidence",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "catalyst-watch.png",
  },
  {
    label: "trade-memory",
    path: "/trade-memory",
    eyebrow: "PROCESS JUDGMENT",
    safetyCategory: "Reflection / process review",
    requiredTestIds: [
      "trade-memory-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "recent-entries",
      "weekly-review",
      "mistake-frequency",
      "markdown-export",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "trade-memory.png",
  },
  {
    label: "system-ops",
    path: "/system-ops",
    eyebrow: "SYSTEM TRUST JUDGMENT",
    safetyCategory: "Operational protocols only",
    requiredTestIds: [
      "system-ops-page",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "system-health",
      "migration-status",
      "protocol-cards",
      "data-source-strip",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "system-ops.png",
  },
];

async function gotoRoute(page: Page, route: RouteSpec): Promise<void> {
  await forceFixtureSnapshotApis(page);
  await page.goto(route.path);
  await page.waitForSelector(`[data-testid="${route.requiredTestIds[0]}"]`);
  await page.waitForSelector('[data-testid="ticker-strip"]');
}

test.describe("Slice 13.11 — All tabs v4.2 structural contract", () => {
  for (const route of ROUTES) {
    test(`${route.label} renders required Evidence-to-Judgment panels`, async ({
      page,
    }) => {
      await gotoRoute(page, route);

      await expect(page.getByTestId("os-tray")).toBeVisible();
      await expect(page.getByTestId("ticker-strip")).toBeVisible();

      for (const testId of route.requiredTestIds) {
        await expect(page.getByTestId(testId).first()).toBeVisible();
      }

      await expect(page.getByTestId("judgment-header")).toContainText(
        route.eyebrow,
      );
      await expect(page.getByTestId("safety-caption")).toContainText(
        route.safetyCategory,
      );

      const body = await page.locator("body").innerText();
      const bodyWithoutIdioms = body.replace(/sell-the-news/gi, "");
      for (const forbidden of FORBIDDEN_EXECUTION_LABELS) {
        expect(bodyWithoutIdioms).not.toContain(forbidden);
      }
    });
  }
});

test.describe("Slice 13.11 — All tabs visual baseline @visual", () => {
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
        timeout: 10_000,
      });
    });
  }
});
