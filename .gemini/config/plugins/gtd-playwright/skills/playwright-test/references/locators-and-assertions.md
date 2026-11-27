# Locators and Assertions

## Locator Priority Order

Use the first strategy that uniquely identifies the element:

```ts
page.getByRole("button", { name: "Submit" }); // 1. Accessible role (default)
page.getByLabel("Email address"); // 2. Form label
page.getByText("Welcome back"); // 3. Visible text
page.getByPlaceholder("Search..."); // 4. Placeholder
page.getByAltText("Company logo"); // 5. Image alt text
page.getByTitle("Close dialog"); // 6. Title attribute
page.getByTestId("checkout-summary"); // 7. Explicit test contract
page.locator(".legacy-widget button"); // 8. CSS/XPath (last resort)
```

## Modern Locator Combinators (Check Installed Version)

- **`locator.visible()` (1.63+):** Use only for genuinely duplicated responsive UI (e.g., hidden mobile nav + visible desktop nav); never use it to hide a strict-mode collision between two visible elements.
- **`locator.within(container)` (1.64+):** Combine reusable locators or resolve relative selectors per parent row:
  ```ts
  const thirdColumn = page.getByRole("cell").nth(2).within(page.getByRole("row"));
  await expect(thirdColumn).toHaveText(["Apple", "Banana", "Cherry"]);
  ```
- **`locator.normalize()` / `page.pickLocator()` (1.59+):** Useful during refactors/exploration to convert brittle CSS selectors, then review for user intent.

## Web-First vs. Non-Retrying Assertions

Always use **web-first (auto-retrying)** assertions for DOM/page state so Playwright retries until the condition holds or times out:

```ts
await expect(page.getByRole("heading", { name: "Products" })).toBeVisible();
await expect(page.getByTestId("total")).toHaveText(/Total: \$\d+\.\d{2}/);
await expect(page.getByRole("listitem")).toHaveCount(5);
await expect(page.getByRole("dialog")).not.toBeVisible();
await expect(label).toHaveCSS("content", '"*"', { pseudo: "after" }); // 1.60+

// Non-DOM async conditions and atomic multi-assertion blocks
await expect.poll(() => getUserCount()).toBe(10);
await expect(async () => {
  const res = await page.request.get("/api/status");
  expect(res.status()).toBe(200);
}).toPass();
```

Use non-retrying assertions (`expect(value).toBe(...)`) only on values already resolved from API responses or static computations—never `expect(await locator.textContent()).toBe(...)` on dynamic DOM.
