# Network Mocking and Browser State

## CLI Route Mocking

```bash
# Mock status, JSON body, or headers
playwright-cli route "**/*.jpg" --status=404
playwright-cli route "**/api/users" --body='[{"id":1,"name":"Alice"}]' --content-type=application/json
playwright-cli route "**/api/data" --body='{"ok":true}' --header="X-Custom: value"
playwright-cli route "**/*" --remove-header=cookie,authorization

# Inspect or clear active routes
playwright-cli route-list
playwright-cli unroute "**/*.jpg"
playwright-cli unroute
```

For conditional responses, response mutation, delays, or simulated network failures (`connectionrefused`, `timedout`, `connectionreset`, `internetdisconnected`), use `run-code`:

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/user', async route => {
    const response = await route.fetch();
    const json = await response.json();
    json.isPremium = true;
    await route.fulfill({ response, json });
  });
}"
```

## Storage State, Cookies, and Web Storage

```bash
# Save and restore full auth state (cookies + localStorage)
playwright-cli state-save auth.json
playwright-cli state-load auth.json

# Cookies
playwright-cli cookie-list [--domain=example.com] [--path=/api]
playwright-cli cookie-get session_id
playwright-cli cookie-set session_id abc123 --domain=example.com --path=/ --httpOnly --secure --sameSite=Lax
playwright-cli cookie-delete session_id [--domain=example.com]
playwright-cli cookie-clear

# localStorage and sessionStorage (same subcommands with sessionstorage-*)
playwright-cli localstorage-list
playwright-cli localstorage-get token
playwright-cli localstorage-set theme dark
playwright-cli localstorage-delete token
playwright-cli localstorage-clear
```
