# Debugging Playwright Tests with `playwright-cli`

## Run Tests Without Opening the HTML Report

Always set `PLAYWRIGHT_HTML_OPEN=never` so the runner exits cleanly in non-interactive shells:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/checkout.spec.ts
```

## Interactive CLI Debugging (`--debug=cli`)

1. Start the failing test in the background with `--debug=cli` (it pauses at the start and prints a session name such as `tw-abcdef` under "Debugging Instructions"):

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/checkout.spec.ts --debug=cli
```

2. Attach `playwright-cli` to the printed session name to inspect snapshots, test locators, and step through the flow:

```bash
playwright-cli attach tw-abcdef
playwright-cli snapshot
playwright-cli click e15
```

Every action executed through `playwright-cli` prints the corresponding Playwright TypeScript code, which can be applied directly to the test when the locator or expectation is at fault (verify first whether the failure is a test bug or a real application bug).

3. Stop the background test process after fixing the issue, then re-run the test normally (`PLAYWRIGHT_HTML_OPEN=never npx playwright test <spec>`) to verify it passes.
