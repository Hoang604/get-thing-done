# Configuration, Parallelism, and CI Sharding

## Baseline `playwright.config.ts`

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  fullyParallel: true,
  workers: process.env.CI ? '50%' : undefined,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['blob'], ['github']] : [['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: process.env.CI ? 'retain-on-failure-and-retries' : 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

- Use `test.describe.configure({ mode: 'serial' })` only for inherently ordered multi-step flows inside a file.
- Use `{ lock: 'resource-name' }` / `test.describe.configure({ lock: 'resource-name' })` (1.63/1.64+) to serialize tests that contend on one shared external resource without forcing `--workers=1`.
- Use `retryStrategy: 'isolated'` (1.62+, config-only) to run retries at the end on a single worker to isolate concurrency flakiness.

## Worker-Scoped Fixtures

Create expensive per-worker resources once per worker process rather than per test:

```ts
export const test = base.extend<{}, { db: DbClient }>({
  db: [async ({}, use) => {
    const db = await DbClient.connect(process.env.DB_URL!);
    await use(db);
    await db.disconnect();
  }, { scope: 'worker' }],
});
```

## CI Sharding and Report Merging

Split large suites across machines with `--shard=1/4` ... `--shard=4/4` using the `blob` reporter, then merge all downloaded `blob-report/` artifacts in a final job:

```bash
npx playwright merge-reports --reporter=html ./all-blob-reports
```
