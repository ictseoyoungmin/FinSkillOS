import { expect, test } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS } from "./_helpers";

test.describe("Slice 13.8 — Risk Firewall / Mission Control / System Ops", () => {
  test("Risk Firewall renders guard cards and the active alerts table", async ({
    page,
  }) => {
    await page.goto("/risk-firewall");
    await expect(page.getByTestId("risk-firewall-page")).toBeVisible();
    await expect(page.getByTestId("risk-firewall-data-state")).toBeVisible();
    await expect(page.getByTestId("risk-firewall-data-state")).toContainText(
      /Evaluation/i,
    );
    await expect(page.getByTestId("risk-firewall-guard-results")).toBeVisible();
    await expect(
      page.getByTestId("risk-firewall-active-alerts"),
    ).toBeVisible();
    await expect(
      page.getByTestId("risk-firewall-active-alerts-table"),
    ).toBeVisible();
    await expect(page.getByTestId("risk-firewall-protocol")).toBeVisible();
    await expect(
      page.getByTestId("risk-firewall-safety-caption"),
    ).toContainText("Read mode");
    // At least one guard card must render.
    await expect(
      page.getByTestId("guard-SINGLE_POSITION_LIMIT_GUARD"),
    ).toBeVisible();
  });

  test("Mission Control renders goal tracker and milestone timeline", async ({
    page,
  }) => {
    await page.goto("/mission-control");
    await expect(page.getByTestId("mission-control-page")).toBeVisible();
    await expect(page.getByTestId("mission-goal-tracker")).toBeVisible();
    await expect(page.getByTestId("mission-milestone-timeline")).toBeVisible();
    await expect(page.getByTestId("mission-portfolio-snapshot")).toBeVisible();
    await expect(page.getByTestId("mission-state-band")).toBeVisible();
    await expect(page.getByTestId("mission-state-band")).toContainText(/Source/i);
    await expect(page.getByTestId("mission-evidence-digest")).toBeVisible();
    await expect(page.getByTestId("mission-evidence-digest")).toContainText(
      /Drivers|Review/i,
    );
    // v4.2: the asset chart + allocation pie lead the tab (replacing the
    // all-unclassified sector/theme exposure panels).
    await expect(page.getByTestId("mission-top-row")).toBeVisible();
    await expect(page.getByTestId("mission-asset-chart")).toBeVisible();
    await expect(page.getByTestId("mission-allocation")).toBeVisible();
    await expect(page.getByTestId("mission-control-caption")).toContainText(
      "challenge",
    );
    await expect(
      page.getByTestId("mission-control-safety-caption"),
    ).toContainText("Read mode");
    await expect(page.getByTestId("mission-challenge-label")).toContainText(
      "1억",
    );
  });

  test("System Ops renders protocol cards and operational caption", async ({
    page,
  }) => {
    await page.goto("/system-ops");
    await expect(page.getByTestId("system-ops-page")).toBeVisible();
    await expect(page.getByTestId("system-ops-data-sources")).toBeVisible();
    await expect(page.getByTestId("system-ops-protocols")).toBeVisible();
    await expect(
      page.getByTestId("system-ops-protocol-seed-sample-account"),
    ).toBeVisible();
    await expect(
      page.getByTestId("system-ops-protocol-recompute-regime"),
    ).toBeVisible();
    await expect(
      page.getByTestId("system-ops-protocol-run-risk-guards"),
    ).toBeVisible();
    await expect(
      page.getByTestId("system-ops-protocol-seed-sample-events"),
    ).toBeVisible();
    await expect(
      page.getByTestId("system-ops-safety-caption"),
    ).toContainText("Operational protocols only");

    await page.getByTestId("system-ops-tab-worker").click();
    await expect(page.getByTestId("worker-status-dashboard")).toBeVisible();
  });

  test("System Ops confirm dialog gates the protocol run", async ({ page }) => {
    await page.goto("/system-ops");
    const triggerButton = page.getByTestId(
      "system-ops-protocol-seed-sample-account-button",
    );
    await triggerButton.click();
    const confirm = page.getByTestId(
      "system-ops-protocol-seed-sample-account-confirm",
    );
    await expect(confirm).toBeVisible();
    // Cancel returns to idle without firing the request.
    await confirm.getByRole("button", { name: "Cancel" }).click();
    await expect(confirm).toBeHidden();
  });

  test("System Ops protocol result renders structured evidence detail", async ({
    page,
  }) => {
    await page.route("**/api/system-ops/seed-sample-events", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          protocol: "seed_sample_events",
          status: "OK",
          message: "3 event catalog rows loaded through System Ops.",
          detail: "legacy_detail",
          detailEvidence: [
            { key: "detail", value: "events_seeded" },
            { key: "created_count", value: "3" },
            { key: "date_statuses", value: "TENTATIVE+WINDOW" },
            { key: "boundary", value: "system_ops" },
          ],
          ranAt: "2026-05-29T10:00:00+09:00",
        }),
      });
    });

    await page.goto("/system-ops");
    await page
      .getByTestId("system-ops-protocol-seed-sample-events-button")
      .click();
    await page
      .getByTestId("system-ops-protocol-seed-sample-events-confirm-button")
      .click();

    await expect(
      page.getByTestId("system-ops-protocol-seed-sample-events-result"),
    ).toContainText("OK");
    await expect(
      page.getByTestId("system-ops-protocol-seed-sample-events-result-meta"),
    ).toContainText("ran_at");

    const evidence = page.getByTestId(
      "system-ops-protocol-seed-sample-events-result-evidence",
    );
    await expect(evidence).toContainText("created_count");
    await expect(evidence).toContainText("3");
    await expect(evidence).toContainText("date_statuses");
    await expect(evidence).toContainText("TENTATIVE+WINDOW");
    await expect(evidence).toContainText("boundary");
    await expect(evidence).toContainText("system_ops");
  });

  test("System Ops history renders structured detail evidence per run", async ({
    page,
  }) => {
    await page.route("**/api/system-ops", async (route) => {
      const response = await route.fetch();
      const json = await response.json();
      json.recentProtocolRuns = [
        {
          protocol: "seed_sample_events",
          status: "OK",
          message: "3 event catalog rows loaded through System Ops.",
          detail: "events_seeded",
          detailEvidence: [
            { key: "created_count", value: "3" },
            { key: "date_statuses", value: "TENTATIVE+WINDOW" },
            { key: "boundary", value: "system_ops" },
          ],
          ranAt: "2026-05-29T10:00:00+09:00",
          dbStatus: "LIVE",
          source: "live",
        },
        {
          protocol: "refresh_market_data",
          status: "OK",
          message: "Stored bars refreshed.",
          detail: "bars=120",
          detailEvidence: [],
          ranAt: "2026-05-29T09:00:00+09:00",
          dbStatus: "LIVE",
          source: "live",
        },
      ];
      await route.fulfill({ json });
    });

    await page.goto("/system-ops");

    const history = page.getByTestId("recent-protocol-runs");
    await expect(history).toBeVisible();

    const seededEvidence = page.getByTestId(
      "recent-protocol-run-evidence-seed-sample-events",
    );
    await expect(seededEvidence).toContainText("created_count");
    await expect(seededEvidence).toContainText("3");
    await expect(seededEvidence).toContainText("date_statuses");
    await expect(seededEvidence).toContainText("boundary");
    await expect(seededEvidence).toContainText("system_ops");

    // The legacy `detail` string is parsed into chips when detailEvidence is
    // empty, so older audit rows still render structured evidence.
    const refreshEvidence = page.getByTestId(
      "recent-protocol-run-evidence-refresh-market-data",
    );
    await expect(refreshEvidence).toContainText("bars");
    await expect(refreshEvidence).toContainText("120");
  });

  test("Slice 13.8 routes never expose forbidden execution captions", async ({
    page,
  }) => {
    for (const path of [
      "/risk-firewall",
      "/mission-control",
      "/system-ops",
    ]) {
      await page.goto(path);
      const body = await page.locator("body").innerText();
      for (const forbidden of FORBIDDEN_EXECUTION_LABELS) {
        expect(body, `${path} body should not include ${forbidden}`).not.toContain(
          forbidden,
        );
      }
    }
  });
});
