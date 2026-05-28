import { expect, test, type Page, type TestInfo } from "@playwright/test";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { forceFixtureSnapshotApis } from "../_helpers";

interface RouteLayoutSpec {
  readonly label: string;
  readonly path: string;
  readonly mockupId: string;
  readonly leftTestId: string;
  readonly centerTestId: string;
  readonly rightTestId: string;
}

interface LayoutBox {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

type Landmark =
  | "tray"
  | "ticker"
  | "judgment"
  | "drivers"
  | "conflicts"
  | "left"
  | "center"
  | "right";

type LayoutSnapshot = Partial<Record<Landmark, LayoutBox>>;

const VIEWPORT = { width: 1440, height: 900 };

const MOCKUP_HTML = resolve(
  process.cwd(),
  "../prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html",
);

const ROUTES: readonly RouteLayoutSpec[] = [
  {
    label: "control-room",
    path: "/",
    mockupId: "control",
    leftTestId: "control-room-left",
    centerTestId: "control-room-center",
    rightTestId: "control-room-right",
  },
  {
    label: "market-kernel",
    path: "/market-kernel",
    mockupId: "kernel",
    leftTestId: "symbol-universe-rail",
    centerTestId: "chart-panel",
    rightTestId: "market-interpretation",
  },
  {
    label: "analysis-workspace",
    path: "/analysis-workspace",
    mockupId: "analysis",
    leftTestId: "index-universe-table",
    centerTestId: "tape-strength-cards",
    rightTestId: "regime-context",
  },
  {
    label: "symbol-lab",
    path: "/symbol-lab",
    mockupId: "symbol",
    leftTestId: "position-context",
    centerTestId: "technical-snapshot",
    rightTestId: "ticker-news",
  },
  {
    label: "risk-firewall",
    path: "/risk-firewall",
    mockupId: "firewall",
    leftTestId: "guard-result-cards",
    centerTestId: "risk-protocol-panel",
    rightTestId: "active-alerts",
  },
  {
    label: "mission-control",
    path: "/mission-control",
    mockupId: "mission",
    leftTestId: "goal-tracker",
    centerTestId: "capital-map",
    rightTestId: "portfolio-snapshot",
  },
  {
    label: "news-intelligence",
    path: "/news-intel",
    mockupId: "news",
    leftTestId: "holdings-relevant-news",
    centerTestId: "news-impact-map",
    rightTestId: "event-linked-news",
  },
  {
    label: "catalyst-watch",
    path: "/catalyst-watch",
    mockupId: "catalyst",
    leftTestId: "event-risk-table",
    centerTestId: "event-score-drivers",
    rightTestId: "event-catalog-evidence",
  },
  {
    label: "trade-memory",
    path: "/trade-memory",
    mockupId: "memory",
    leftTestId: "recent-entries",
    centerTestId: "mistake-frequency",
    rightTestId: "markdown-export",
  },
  {
    label: "system-ops",
    path: "/system-ops",
    mockupId: "ops",
    leftTestId: "system-health",
    centerTestId: "protocol-cards",
    rightTestId: "data-source-strip",
  },
];

const REFERENCE_SCREENSHOTS: Readonly<Record<string, string>> = {
  control: "01_control_room.png",
  kernel: "02_market_kernel.png",
  analysis: "03_analysis_workspace.png",
  symbol: "04_symbol_lab.png",
  firewall: "05_risk_firewall.png",
  mission: "06_mission_control.png",
  news: "07_news_intelligence.png",
  catalyst: "08_catalyst_watch.png",
  memory: "09_trade_memory.png",
  ops: "10_system_ops.png",
};

function toFileUrl(path: string): string {
  return `file://${path}`;
}

function normalizeBox(box: LayoutBox): LayoutBox {
  return {
    x: Number((box.x / VIEWPORT.width).toFixed(4)),
    y: Number((box.y / VIEWPORT.height).toFixed(4)),
    width: Number((box.width / VIEWPORT.width).toFixed(4)),
    height: Number((box.height / VIEWPORT.height).toFixed(4)),
  };
}

async function getBox(page: Page, selector: string): Promise<LayoutBox> {
  return page.locator(selector).first().evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return {
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
    };
  });
}

async function getMockupLayout(
  page: Page,
  route: RouteLayoutSpec,
): Promise<LayoutSnapshot> {
  await page.goto(toFileUrl(MOCKUP_HTML));
  await page.locator(`[data-page="${route.mockupId}"]`).first().click();
  await page.locator(`#page-${route.mockupId}.active`).waitFor();

  const pageRoot = `#page-${route.mockupId}`;
  return {
    tray: normalizeBox(await getBox(page, ".tray")),
    ticker: normalizeBox(await getBox(page, ".ticker-strip")),
    judgment: normalizeBox(await getBox(page, `${pageRoot} .judgment`)),
    drivers: normalizeBox(
      await getBox(page, `${pageRoot} .judgment > .panel:nth-child(2)`),
    ),
    conflicts: normalizeBox(
      await getBox(page, `${pageRoot} .judgment > .panel:nth-child(3)`),
    ),
    left: normalizeBox(
      await getBox(page, `${pageRoot} .detail-grid > .column:nth-child(1)`),
    ),
    center: normalizeBox(
      await getBox(page, `${pageRoot} .detail-grid > .column:nth-child(2)`),
    ),
    right: normalizeBox(
      await getBox(page, `${pageRoot} .detail-grid > .column:nth-child(3)`),
    ),
  };
}

async function getReactLayout(
  page: Page,
  route: RouteLayoutSpec,
): Promise<LayoutSnapshot> {
  await forceFixtureSnapshotApis(page);
  await page.goto(route.path);
  await page.getByTestId("judgment-header").waitFor();

  return {
    tray: normalizeBox(await getBox(page, '[data-testid="os-tray"]')),
    ticker: normalizeBox(await getBox(page, '[data-testid="ticker-strip"]')),
    judgment: normalizeBox(await getBox(page, '[data-testid="judgment-header"]')),
    drivers: normalizeBox(await getBox(page, '[data-testid="drivers-panel"]')),
    conflicts: normalizeBox(await getBox(page, '[data-testid="conflicts-panel"]')),
    left: normalizeBox(await getBox(page, `[data-testid="${route.leftTestId}"]`)),
    center: normalizeBox(
      await getBox(page, `[data-testid="${route.centerTestId}"]`),
    ),
    right: normalizeBox(await getBox(page, `[data-testid="${route.rightTestId}"]`)),
  };
}

function delta(a: LayoutBox, b: LayoutBox): LayoutBox {
  return {
    x: Number(Math.abs(a.x - b.x).toFixed(4)),
    y: Number(Math.abs(a.y - b.y).toFixed(4)),
    width: Number(Math.abs(a.width - b.width).toFixed(4)),
    height: Number(Math.abs(a.height - b.height).toFixed(4)),
  };
}

function compareLayouts(mockup: LayoutSnapshot, react: LayoutSnapshot) {
  const result: Partial<Record<Landmark, LayoutBox>> = {};
  for (const key of Object.keys(mockup) as Landmark[]) {
    const mockupBox = mockup[key];
    const reactBox = react[key];
    if (mockupBox && reactBox) {
      result[key] = delta(mockupBox, reactBox);
    }
  }
  return result;
}

async function attachLayoutReport(
  testInfo: TestInfo,
  route: RouteLayoutSpec,
  report: unknown,
): Promise<void> {
  await testInfo.attach(`${route.label}-layout-report.json`, {
    body: JSON.stringify(report, null, 2),
    contentType: "application/json",
  });
}

test.describe("Slice 13.11 — v4.2 prototype layout comparison @visual", () => {
  test.describe.configure({ timeout: 90_000 });

  test.beforeAll(() => {
    expect(
      existsSync(MOCKUP_HTML),
      `Missing v4.2 mockup HTML at ${MOCKUP_HTML}`,
    ).toBe(true);
  });

  for (const route of ROUTES) {
    test(`${route.label} layout report vs v4.2 mockup @visual`, async ({
      browser,
    }, testInfo) => {
      const mockupPage = await browser.newPage({ viewport: VIEWPORT });
      const reactPage = await browser.newPage({ viewport: VIEWPORT });

      const mockupLayout = await getMockupLayout(mockupPage, route);
      const reactLayout = await getReactLayout(reactPage, route);
      const layoutDelta = compareLayouts(mockupLayout, reactLayout);

      await testInfo.attach(`${route.label}-mockup.png`, {
        body: await mockupPage.screenshot({ fullPage: false }),
        contentType: "image/png",
      });
      await testInfo.attach(`${route.label}-react.png`, {
        body: await reactPage.screenshot({ fullPage: false }),
        contentType: "image/png",
      });

      const screenshotPath = resolve(
        process.cwd(),
        `../prototypes/ui/enhanced_dashboard_mockup/v4_2/screenshots/${
          REFERENCE_SCREENSHOTS[route.mockupId]
        }`,
      );
      if (existsSync(screenshotPath)) {
        await testInfo.attach(`${route.label}-reference-screenshot.png`, {
          body: readFileSync(screenshotPath),
          contentType: "image/png",
        });
      }

      await attachLayoutReport(testInfo, route, {
        route: route.label,
        viewport: VIEWPORT,
        mockup: mockupLayout,
        react: reactLayout,
        delta: layoutDelta,
      });

      await expect(reactPage.getByTestId("judgment-header")).toBeVisible();
      await expect(mockupPage.locator(`#page-${route.mockupId}.active`)).toBeVisible();

      await mockupPage.close();
      await reactPage.close();
    });
  }
});
