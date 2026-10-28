import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import { App } from "./main";
import userEvent from "@testing-library/user-event";
const seed = {
  employees: [
    {
      id: 1,
      name: "Demo One",
      pod_id: 1,
      process_ids: [1],
      weekly_off: 6,
      max_work_days: 26,
      active: true,
    },
  ],
  brands: [
    {
      id: 1,
      name: "Brand One",
      pod_id: 1,
      operating_weekdays: [0, 1, 2, 3, 4],
      holidays_closed: true,
      holiday_dates: [],
    },
  ],
  pods: [{ id: 1, name: "Pod One" }],
  processes: [{ id: 1, name: "Support" }],
  demands: [
    { id: 1, brand_id: 1, process_id: 1, employee_ids: [1], min_staff: 1 },
  ],
  leaves: [],
  holidays: [],
};
const roster = {
  year: 2026,
  month: 11,
  revision: 1,
  slots: [{ day: "2026-11-02", employee_id: 1, demand_id: 1 }],
  valid: true,
  conflicts: [],
  shortages: [],
  workload: { 1: 1 },
  coverage_required: 1,
  coverage_filled: 1,
  optimal: true,
  solver_status: "OPTIMAL",
};
beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => ({
      ok: true,
      json: async () =>
        url.includes("/rosters/")
          ? { ...roster, ...(init?.method === "PUT" ? { revision: 2 } : {}) }
          : url.endsWith("/data")
            ? seed
            : { record: {} },
    })),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("dashboard integration", () => {
  it("renders overview and navigation", async () => {
    render(<App />);
    expect(
      await screen.findByText("A clearer view of your team."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Employees" }));
    expect(await screen.findByText("Demo One")).toBeInTheDocument();
  });
  it("submits employee form with API fields", async () => {
    render(<App />);
    await screen.findByText("A clearer view of your team.");
    fireEvent.click(screen.getByRole("button", { name: "Employees" }));
    await screen.findByText("Demo One");
    fireEvent.click(screen.getByRole("button", { name: "Add employee" }));
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "New Person" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save record" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "/api/employees",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("New Person"),
        }),
      ),
    );
  });
  it("renders calendar, filters and editor preview", async () => {
    render(<App />);
    await screen.findByText("A clearer view of your team.");
    fireEvent.click(screen.getByRole("button", { name: "Roster calendar" }));
    fireEvent.click(
      await screen.findByRole("button", { name: /Demo One Brand One/ }),
    );
    expect(
      screen.getByRole("dialog", { name: "Edit assignment" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Save assignment" }),
    ).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Preview impact" }));
    await screen.findByText("0 hard conflicts · 0 shortages");
    expect(
      screen.getByRole("button", { name: "Save assignment" }),
    ).not.toBeDisabled();
  });
  it("accepts typed comma-separated eligibility IDs", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("A clearer view of your team.");
    await user.click(screen.getByRole("button", { name: "Employees" }));
    await screen.findByText("Demo One");
    await user.click(screen.getByRole("button", { name: "Add employee" }));
    await user.type(screen.getByLabelText("Full name"), "Typing Test");
    await user.type(screen.getByLabelText(/^Eligible process IDs/), "1,2");
    await user.click(screen.getByRole("button", { name: "Save record" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "/api/employees",
        expect.objectContaining({
          body: expect.stringContaining('\"process_ids\":[1,2]'),
        }),
      ),
    );
  });
  it("displays API failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        json: async () => ({ detail: { message: "Database unavailable" } }),
      })),
    );
    render(<App />);
    expect((await screen.findAllByRole("alert"))[0]).toHaveTextContent(
      "Database unavailable",
    );
  });
});
