import { expect, test, type Page } from "@playwright/test";

const signIn = async (page: Page) => {
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
});

test("requires sign-in with valid credentials", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await expect(page.getByTestId("column-col-backlog")).not.toBeVisible();

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("The username or password is incorrect.")).toBeVisible();

  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("persists sign-in through refresh and logs out", async ({ page }) => {
  await signIn(page);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await expect(page.getByTestId("column-col-backlog")).not.toBeVisible();
});

test("persists a board edit through refresh", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid="column-col-backlog"]');
  const title = firstColumn.getByLabel("Column title");
  await title.fill("Queued");
  await expect(title).toHaveValue("Queued");
  await page.reload();

  await expect(page.locator('[data-testid="column-col-backlog"] input[aria-label="Column title"]')).toHaveValue("Queued");
});

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const cardTitle = `Playwright card ${Date.now()}`;
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(cardTitle);
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(cardTitle, { exact: true })).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await signIn(page);
  const card = page.locator('[data-testid^="column-"]').first().locator('[data-testid^="card-"]').first();
  const cardTestId = await card.getAttribute("data-testid");
  if (!cardTestId) {
    throw new Error("Unable to identify a card in the source column.");
  }
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId(cardTestId)).toBeVisible();
});

test("asks the board assistant and reconciles an AI board update", async ({ page }) => {
  await page.route("**/api/ai/board", async (route) => {
    const board = {
      columns: [
        { id: "col-backlog", title: "Queued", cardIds: ["card-1", "card-2"] },
        { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
        { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
        { id: "col-review", title: "Review", cardIds: ["card-6"] },
        { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
      ],
      cards: {
        "card-1": { id: "card-1", title: "Align roadmap themes", details: "Draft quarterly themes with impact statements and metrics." },
        "card-2": { id: "card-2", title: "Gather customer signals", details: "Review support tags, sales notes, and churn feedback." },
        "card-3": { id: "card-3", title: "Prototype analytics view", details: "Sketch initial dashboard layout and key drill-downs." },
        "card-4": { id: "card-4", title: "Refine status language", details: "Standardize column labels and tone across the board." },
        "card-5": { id: "card-5", title: "Design card layout", details: "Add hierarchy and spacing for scanning dense lists." },
        "card-6": { id: "card-6", title: "QA micro-interactions", details: "Verify hover, focus, and loading states." },
        "card-7": { id: "card-7", title: "Ship marketing page", details: "Final copy approved and asset pack delivered." },
        "card-8": { id: "card-8", title: "Close onboarding sprint", details: "Document release notes and share internally." },
      },
    };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistant_response: "I renamed the backlog column to Queued.",
        board_updated: true,
        board,
        version: 2,
        updated_at: "2026-01-01T00:00:00Z",
      }),
    });
  });

  await signIn(page);
  await page.getByLabel("Ask the board assistant").fill("Rename backlog to Queued");
  await page.getByRole("button", { name: "Send question" }).click();

  await expect(page.getByText("I renamed the backlog column to Queued.")).toBeVisible();
  await expect(page.getByTestId("column-col-backlog").getByLabel("Column title")).toHaveValue("Queued");
});
