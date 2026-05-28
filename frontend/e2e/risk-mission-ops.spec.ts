import { expect, test } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS } from "./_helpers";

test.describe("Slice 13.8 — Risk Firewall / Mission Control / System Ops", () => {
  test("Risk Firewall renders guard cards and the active alerts table", async ({
    page,
  }) => {
    await page.goto("/risk-firewall");
    await expect(page.getByTestId("risk-firewall-page")).toBeVisible();
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
    await expect(page.getByTestId("mission-capital-map-sector")).toBeVisible();
    await expect(page.getByTestId("mission-capital-map-theme")).toBeVisible();
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
