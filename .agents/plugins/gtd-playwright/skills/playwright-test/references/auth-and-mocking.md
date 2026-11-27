# Authentication and External Network Mocking

## Authentication State Reuse

Avoid logging in through the UI before every test—authenticate once (via UI or API) and reuse `storageState`:

```ts
// Generate once in a setup project or helper
const context = await browser.newContext();
await context.request.post("/api/auth/login", {
  data: { email: process.env.TEST_EMAIL, password: process.env.TEST_PASSWORD },
});
await context.storageState({
  path: ".auth/user.json",
  indexedDB: true, // opt in when auth tokens live in IndexedDB (1.51+)
  opfs: true, // opt in when auth state lives in OPFS (1.63+)
});
await context.close();
```

- Load via `use: { storageState: '.auth/user.json' }` in `playwright.config.ts` (keep `.auth/` in `.gitignore`).
- **In-place role swap (1.59+):** `await context.setStorageState('.auth/admin.json'); await page.reload();` replaces cookies, localStorage, and IndexedDB without recreating the context.
- **Per-origin HTTP basic auth (1.63+):** Pass an array to `use.httpCredentials: [{ username, password, origin }]`.

## External Network Mocking

Register routes **before** `page.goto()`. Every handler must call exactly one of `route.fulfill()`, `route.continue()`, or `route.abort()`. Mock external services only—keep calls to your own backend real:

```ts
// Fulfill external service response
await page.route("https://api.stripe.com/**", (route) =>
  route.fulfill({ status: 200, json: { id: "ch_test_1" } }),
);

// Modify a real response in flight
await page.route("**/api/external-feed", async (route) => {
  const response = await route.fetch();
  const json = await response.json();
  await route.fulfill({ response, json: { ...json, flag: true } });
});

// Synchronize action with a real network response (register promise before clicking)
const responsePromise = page.waitForResponse("**/api/orders");
await page.getByRole("button", { name: "Place order" }).click();
await responsePromise;

// Replay recorded external fixtures from HAR
await page.routeFromHAR("tests/data/external.har", { url: "https://third-party.example/**" });
```
