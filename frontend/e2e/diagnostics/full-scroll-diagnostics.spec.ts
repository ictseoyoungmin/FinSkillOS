import { expect, test, type Page } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { forceFixtureSnapshotApis } from "../_helpers";

const OUTPUT_DIR = join(process.cwd(), "test-results", "diagnostics", "full-scroll");

const ROUTES = [
  { label: "control-room", path: "/", ready: "control-room-grid" },
  { label: "market-kernel", path: "/market-kernel", ready: "market-kernel-page" },
  {
    label: "analysis-workspace",
    path: "/analysis-workspace",
    ready: "analysis-workspace-page",
  },
  { label: "symbol-lab", path: "/symbol-lab", ready: "symbol-lab-page" },
  { label: "risk-firewall", path: "/risk-firewall", ready: "risk-firewall-page" },
  { label: "mission-control", path: "/mission-control", ready: "mission-control-page" },
  { label: "news-intelligence", path: "/news-intel", ready: "news-intelligence-page" },
  { label: "catalyst-watch", path: "/catalyst-watch", ready: "catalyst-watch-page" },
  { label: "trade-memory", path: "/trade-memory", ready: "trade-memory-page" },
  { label: "system-ops", path: "/system-ops", ready: "system-ops-page" },
] as const;

type RouteDiagnostic = {
  label: string;
  path: string;
  viewport: { width: number; height: number };
  document: {
    scrollHeight: number;
    clientHeight: number;
    scrollWidth: number;
    clientWidth: number;
    horizontalOverflow: boolean;
  };
  workspace: {
    scrollHeight: number;
    clientHeight: number;
    scrollTopMax: number;
    horizontalOverflow: boolean;
  } | null;
  scrollStops: number[];
  consoleErrors: string[];
  pageErrors: string[];
  clippedElements: Array<{
    tag: string;
    className: string;
    text: string;
    top: number;
    bottom: number;
    left: number;
    right: number;
  }>;
  suspiciousShortText: Array<{
    tag: string;
    className: string;
    text: string;
    width: number;
  }>;
};

test.describe("diagnostics — full scroll screenshots", () => {
  for (const route of ROUTES) {
    test(`${route.label} top-to-bottom render`, async ({ page }) => {
      test.setTimeout(60_000);
      mkdirSync(OUTPUT_DIR, { recursive: true });
      const consoleErrors: string[] = [];
      const pageErrors: string[] = [];

      page.on("console", (message) => {
        if (message.type() === "error") {
          consoleErrors.push(message.text());
        }
      });
      page.on("pageerror", (error) => {
        pageErrors.push(error.message);
      });

      await gotoRoute(page, route.path, route.ready);
      await expect(page.getByTestId(route.ready)).toBeVisible();

      const metrics = await collectMetrics(page);
      const scrollStops = scrollStopsFor(metrics.workspace, metrics.document.clientHeight);

      await page.screenshot({
        path: join(OUTPUT_DIR, `${route.label}-full-page.png`),
        fullPage: true,
        animations: "disabled",
      });

      for (const [index, top] of scrollStops.entries()) {
        await page.locator('[data-testid="os-workspace"]').evaluate(
          (element, scrollTop) => {
            element.scrollTo({ top: scrollTop });
          },
          top,
        );
        await page.waitForTimeout(80);
        await page.screenshot({
          path: join(OUTPUT_DIR, `${route.label}-viewport-${index}.png`),
          fullPage: false,
          animations: "disabled",
        });
      }

      const diagnostic: RouteDiagnostic = {
        label: route.label,
        path: route.path,
        viewport: page.viewportSize() ?? { width: 0, height: 0 },
        ...metrics,
        scrollStops,
        consoleErrors,
        pageErrors,
      };
      writeFileSync(
        join(OUTPUT_DIR, `${route.label}.json`),
        `${JSON.stringify(diagnostic, null, 2)}\n`,
      );

      expect(pageErrors).toEqual([]);
    });
  }
});

async function gotoRoute(page: Page, path: string, ready: string) {
  await forceFixtureSnapshotApis(page);
  await page.goto(path);
  await page.waitForSelector(`[data-testid="${ready}"]`);
  await page.waitForLoadState("networkidle");
}

function scrollStopsFor(
  workspace: RouteDiagnostic["workspace"],
  viewportHeight: number,
): number[] {
  const max = workspace?.scrollTopMax ?? 0;
  if (max <= 0) return [0];
  const step = Math.max(1, viewportHeight - 96);
  const stops = new Set<number>([0, max]);
  for (let top = step; top < max; top += step) {
    stops.add(top);
  }
  return [...stops].sort((a, b) => a - b);
}

async function collectMetrics(page: Page) {
  return await page.evaluate(() => {
    const workspace = document.querySelector<HTMLElement>('[data-testid="os-workspace"]');
    const viewportWidth = document.documentElement.clientWidth;
    const viewportHeight = document.documentElement.clientHeight;

    const clippedElements = Array.from(
      document.querySelectorAll<HTMLElement>("main *"),
    )
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          element,
          rect,
          text: (element.innerText ?? "").replace(/\s+/g, " ").trim(),
        };
      })
      .filter(({ rect }) => rect.width > 0 && rect.height > 0)
      .filter(
        ({ rect }) =>
          rect.left < -2 ||
          rect.right > viewportWidth + 2 ||
          rect.bottom < 0 ||
          rect.top > viewportHeight + 4,
      )
      .slice(0, 40)
      .map(({ element, rect, text }) => ({
        tag: element.tagName.toLowerCase(),
        className: String(element.className),
        text: text.slice(0, 120),
        top: Math.round(rect.top),
        bottom: Math.round(rect.bottom),
        left: Math.round(rect.left),
        right: Math.round(rect.right),
      }));

    const suspiciousShortText = Array.from(
      document.querySelectorAll<HTMLElement>(
        "button, a, .fso-tray-nav-btn, .fso-status-value, .fso-badge, strong, small",
      ),
    )
      .map((element) => {
        const rect = element.getBoundingClientRect();
        const text = (element.innerText ?? "").replace(/\s+/g, " ").trim();
        return { element, rect, text };
      })
      .filter(({ rect, text }) => rect.width > 0 && text.endsWith("…"))
      .slice(0, 40)
      .map(({ element, rect, text }) => ({
        tag: element.tagName.toLowerCase(),
        className: String(element.className),
        text,
        width: Math.round(rect.width),
      }));

    return {
      document: {
        scrollHeight: document.documentElement.scrollHeight,
        clientHeight: document.documentElement.clientHeight,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        horizontalOverflow:
          document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
      },
      workspace: workspace
        ? {
            scrollHeight: workspace.scrollHeight,
            clientHeight: workspace.clientHeight,
            scrollTopMax: Math.max(0, workspace.scrollHeight - workspace.clientHeight),
            horizontalOverflow: workspace.scrollWidth > workspace.clientWidth + 2,
          }
        : null,
      clippedElements,
      suspiciousShortText,
    };
  });
}
