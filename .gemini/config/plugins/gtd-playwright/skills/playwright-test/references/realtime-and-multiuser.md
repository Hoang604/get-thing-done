# Multi-User, WebSockets, and Canvas Testing

## Multi-User Collaboration (`BrowserContext` Isolation)

Simulate multiple independent users in one test via separate `browser.newContext()` instances (isolated cookies, storage, and sockets). Wrap repeated setups in `test.extend()` fixtures so contexts always close on teardown:

```ts
const aliceCtx = await browser.newContext({ storageState: '.auth/alice.json' });
const bobCtx = await browser.newContext({ storageState: '.auth/bob.json' });
try {
  const alicePage = await aliceCtx.newPage();
  const bobPage = await bobCtx.newPage();
  await Promise.all([alicePage.goto('/rooms/1'), bobPage.goto('/rooms/1')]);

  await alicePage.getByRole('textbox', { name: 'Message' }).fill('Hello Bob!');
  await alicePage.getByRole('button', { name: 'Send' }).click();
  await expect(bobPage.getByText('Hello Bob!')).toBeVisible();
} finally {
  await Promise.all([aliceCtx.close(), bobCtx.close()]);
}
```

## WebSockets and Real-Time Traffic

- Prefer asserting on visible UI state after round-trip sync rather than internal frames.
- Observe live frames with `page.on('websocket', ws => ws.on('framesent' | 'framereceived', ...))`, or inspect captured WebSocket traffic directly in traces via `npx playwright trace requests` (Playwright 1.61+).
- Register `await page.routeWebSocket('**/ws', ws => ...)` only when simulating server-pushed edge cases or third-party streams without a real backend.

## Canvas and WebGL

- Interact via DOM overlays whenever the canvas renders accessible overlays/tooltips; otherwise use relative coordinates (`canvas.click({ position: { x, y } })`, `canvas.hover` + `page.mouse.down/move(..., { steps: 10 })/up`, `page.mouse.wheel`).
- Wait for rendering readiness (e.g., loading indicator hidden or application state predicate) before comparing visual output:
  ```ts
  await expect(page.locator('canvas#board')).toHaveScreenshot('drawn.png', {
    mask: [page.locator('.live-timestamp')],
    maxDiffPixelRatio: 0.01,
  });
  ```
- Inspect canvas state directly via `page.evaluate()` (or exposed app test state) when asserting geometric/data invariants instead of brittle pixel diffs.
