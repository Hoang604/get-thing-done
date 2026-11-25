# Tracing, Video, Custom Code, and UI Annotation

## Tracing

Start tracing before reproducing the flow so `.playwright-cli/traces/` captures actions, DOM snapshots, screenshots, network traffic, and console logs:

```bash
playwright-cli open
playwright-cli tracing-start
playwright-cli goto https://example.com
playwright-cli click e1
playwright-cli tracing-stop
```

## Video Recording and Interactive UI Review

```bash
# Record WebM video with animated cursor and chapter markers
playwright-cli video-start demo.webm --cursor --fps=60
playwright-cli video-chapter "Checkout" --description="Submitting order" --duration=2000
playwright-cli video-show-actions --duration=800 --position=top-right
playwright-cli video-hide-actions
playwright-cli video-stop

# Launch annotation dashboard for user UI feedback (returns annotated screenshot, snapshot, and notes)
playwright-cli show --annotate

# Generate a Playwright locator or highlight an element
playwright-cli generate-locator e5 --raw
playwright-cli highlight e5 [--style="outline: 3px dashed red"]
playwright-cli highlight --hide
```

## Custom Playwright Code (`run-code`)

Pass a single async function expression taking `page` (inline or via `--filename=./script.js`). Code runs in an isolated sandbox without `require`, `process`, or Node modules (timers, `fetch`, `URL`, `Buffer`, `crypto`, `AbortController`, `TextEncoder`, and `TextDecoder` are available):

```bash
# Grant permissions and geolocation
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 37.7749, longitude: -122.4194 });
}"

# Wait for an element state or application readiness predicate
playwright-cli run-code "async page => {
  await page.locator('.loading').waitFor({ state: 'hidden' });
  await page.waitForFunction(() => window.appReady === true);
}"

# Interact inside an iframe
playwright-cli run-code "async page => {
  const frame = page.locator('iframe#embed').contentFrame();
  await frame.getByRole('button', { name: 'Save' }).click();
}"
```
