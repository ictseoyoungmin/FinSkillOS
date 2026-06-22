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
  // Most tabs use the shared JudgmentHeader (testId "judgment-header"). News Intel
  // carries a richer custom NewsJudgmentHeader, so it overrides the testId the
  // eyebrow assertion targets.
  readonly judgmentTestId?: string;
  // Most tabs use the shared SafetyCaption (testId "safety-caption"). Mission
  // Control renders its own caption paragraph with a page-specific testId.
  readonly safetyTestId?: string;
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
      "interpretation-cards",
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
      "symbol-watchpoints",
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
    // v4.2 pilot replaced the generic Drivers/Conflicts topline with the asset
    // chart + allocation hero (mission-top-row) and dropped the Capital Map panel.
    requiredTestIds: [
      "mission-control-page",
      "judgment-header",
      "mission-top-row",
      "goal-tracker",
      "milestone-timeline",
      "portfolio-snapshot",
      "mission-control-safety-caption",
    ],
    safetyTestId: "mission-control-safety-caption",
    screenshotName: "mission-control.png",
  },
  {
    label: "news-intelligence",
    path: "/news-intel",
    // News Intel uses the custom NewsJudgmentHeader (eyebrow copy "Narrative
    // Judgment") + the NewsSignalSummary "Feed Status" panel instead of the
    // generic Drivers/Conflicts topline.
    eyebrow: "Narrative Judgment",
    judgmentTestId: "news-judgment-header",
    safetyCategory: "Descriptive narrative view only",
    requiredTestIds: [
      "news-intelligence-page",
      "news-judgment-header",
      "news-feed-status",
      "holdings-relevant-news",
      "news-impact-map",
      "event-linked-news",
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
    label: "quant-lab",
    path: "/quant-lab",
    eyebrow: "QUANT LAB",
    safetyCategory: "백테스트",
    requiredTestIds: [
      "quant-lab-page",
      "judgment-header",
      "safety-caption",
      "quant-controls",
      "quant-equity-chart",
      "quant-metrics",
      "quant-strategy",
    ],
    screenshotName: "quant-lab.png",
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
      "recent-protocol-runs",
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

      await expect(
        page.getByTestId(route.judgmentTestId ?? "judgment-header"),
      ).toContainText(route.eyebrow);
      await expect(
        page.getByTestId(route.safetyTestId ?? "safety-caption"),
      ).toContainText(route.safetyCategory);

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
