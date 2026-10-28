import { test, expect } from "@playwright/test";
test("employee, eligibility, generation, conflict rejection, edit and persistence", async ({
  page,
  request,
}) => {
  page.on("dialog", (d) => d.accept());
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A clearer view of your team." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Employees", exact: true }).click();
  await page.getByRole("button", { name: "Add employee" }).click();
  await page.getByLabel("Record ID").fill("99");
  await page.getByLabel("Full name").fill("Demo Test Operator");
  await page.getByLabel("Eligible process IDs").fill("1, 2");
  await page.getByLabel("Weekly off").fill("1");
  await page.getByLabel("Active", { exact: true }).uncheck();
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(
    page.getByRole("cell", { name: "Demo Test Operator", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Assignments", exact: true }).click();
  const row = page
    .getByRole("row")
    .filter({ has: page.getByRole("cell", { name: "#1", exact: true }) });
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel("Assigned employee IDs").fill("1, 99");
  await page.getByRole("button", { name: "Save record" }).click();
  await page
    .getByRole("button", { name: "Generate roster", exact: true })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "Roster generated" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Employees", exact: true }).click();
  const backup = page
    .getByRole("row")
    .filter({
      has: page.getByRole("cell", { name: "Demo Test Operator", exact: true }),
    });
  await backup.getByRole("button", { name: "Edit", exact: true }).click();
  await page.getByLabel("Active", { exact: true }).check();
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(
    page.getByRole("cell", { name: "Demo Test Operator", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Roster calendar", exact: true })
    .click();
  await page.getByLabel("Filter employee_id").selectOption("1");
  await expect(page.locator("button.slot").first()).toBeVisible();
  await page.locator("button.slot").first().click();
  await page.getByLabel("Assigned employee").selectOption("11");
  await page.getByRole("button", { name: "Preview impact" }).click();
  await expect(page.getByRole("dialog").getByRole("status")).toContainText(
    "hard conflicts",
  );
  await expect(
    page.getByRole("button", { name: "Save assignment" }),
  ).toBeDisabled();
  await page.getByLabel("Assigned employee").selectOption("99");
  await page.getByRole("button", { name: "Preview impact" }).click();
  await expect(page.getByRole("dialog").getByRole("status")).toContainText(
    "0 hard conflicts",
  );
  await page.getByRole("button", { name: "Save assignment" }).click();
  await expect(
    page.getByText("Assignment saved and constraints verified."),
  ).toBeVisible();
  await page.reload();
  await page
    .getByRole("button", { name: "Roster calendar", exact: true })
    .click();
  await page.getByLabel("Filter employee_id").selectOption("99");
  await expect(page.locator("button.slot").first()).toContainText(
    "Demo Test Operator",
  );
  await page.getByLabel("Filter pod_id").selectOption("1");
  await expect(page.getByText("Pod lead: Demo Employee 01")).toBeVisible();
  await page.getByLabel("Filter process_id").selectOption("1");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: "../docs/roster-desktop.png", fullPage: true });
  await page.getByRole("button", { name: /^Conflicts/ }).click();
  await expect(
    page.getByRole("heading", { name: "Schedule validation" }),
  ).toBeVisible();
  await page.locator("summary").first().click();
  await expect(page.locator("details").first()).toHaveAttribute("open", "");
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../docs/dashboard-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../docs/dashboard-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
  // Verify backend storage independently of rendered UI.
  const saved = await request.get("/api/rosters/2026/11?employee_id=99");
  expect(saved.ok()).toBeTruthy();
  expect((await saved.json()).slots.length).toBeGreaterThan(0);
});
