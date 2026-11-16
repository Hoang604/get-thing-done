# Existing Codebase Recon, Change Review, and Report Format

## Existing Codebase Convention and Palette Inventory

- **When** modifying or reviewing an existing project, inventory the project's framework, styling mechanism, component/macro library, design tokens, interface docs, and locale catalogs before proposing or writing changes, and express every fix in the project's established token notation, component primitives, and domain vocabulary. *Guardrail*: Never introduce an isolated color notation (such as raw `oklch()` inside a hex/RGB token codebase), an unrequested UI dependency, or a competing domain term unless a system migration is explicitly in scope.
- **When** asked to consolidate or restructure an existing codebase's color palette, collect all color literals across the codebase, group by hue family sorted by perceived lightness, merge near-duplicates within `0.02` OKLab $\Delta E$ into the most-used token, map each survivor to a semantic role, and present the mapping before mutating screens outside the immediate task scope.

## Read-Only Change Review and Blast-Radius Expansion

- **When** reviewing a code change (diff, commit range, branch, or pull request), keep the workspace strictly read-only unless asked to apply fixes, read the full diff before forming findings, inspect every removed (`-`) line that drops an accessibility, contrast, layout, lifecycle-state, or localization guarantee required by `SKILL.md` or `references/*.md` (recording each in Step 2 as `Cleared` with the exact replacement `file:line` that preserves or upgrades that guarantee, or flagging it as a `Regression`), expand inspection from changed files to consuming surfaces (one hop to direct importers for components, two hops for design tokens and shared primitives, ordered by route entry points $\rightarrow$ importer count $\rightarrow$ directory proximity), and verify new components or variants across hover, focus, active, disabled, loading, empty, error, `320px` width, `200%` text zoom, and localization states.

## Review Report Severity, Structure, and Anchor

- **When** formatting an interface review report, emit Step 2's individual rulings first, then consolidate confirmed findings that share a single root cause into one table row listing every affected `path/to/file:line`; in change reviews classify each row as `Introduced` (new defect added by the change), `Regression` (weakened or removed a previously compliant guarantee), or `Pre-existing` (present before the change and unchanged in severity, placed in a separate section); assign severity from observable impact (`HIGH`: blocks task completion, loses user input, omits accessible name/keyboard path/focus visibility, clips or overflows horizontally at `320px` width or `200%` zoom, fails WCAG `4.5:1`/`3:1` contrast, or conveys state by color/motion alone; `MEDIUM`: degrades comprehension, scan speed, layout stability, URL state restoration, or semantic token/component consistency without blocking the task; `LOW`: spacing/radius step alignment or motion polish where hierarchy, accessibility, and tokens hold); separate `Executed` verification checks from `Not verified` checks (stating why and the risk left); and end with `Block` if any `HIGH` finding (or `HIGH` `Introduced`/`Regression` finding in a change review) remains, or `Approve` otherwise, naming any uninspected consumers or domains on the verdict line.

```markdown
### Causal Rulings (Step 2)
- `src/orders/OrderRow.tsx:42` (`-` hunk removed `aria-label="Delete order"`): Regression — icon-only `<button>` at `OrderRow.tsx:44` now has no accessible name.
- `src/orders/OrderHeader.tsx:18–29` (decision scope actions): Violation — both `Export CSV` (`:21`) and `Create order` (`:26`) render solid accent primary fills.
- `src/orders/OrderCard.tsx:12` (`Order ID:` static label): Redundant — `#ORD-8492` format uniquely identifies the attribute among `[#ORD-8492, $140.00, Shipped]`.

### Findings (`Introduced` & `Regression`)
| Severity | Class | Rule & Cause | Locations | Concrete Fix |
|---|---|---|---|---|
| HIGH | Regression | Icon-only `<button>` lacks accessible name after `aria-label` removal | `src/orders/OrderRow.tsx:44` | Restore `aria-label={`Delete order ${order.code}`}` |
| MEDIUM | Introduced | Two solid primary buttons compete in one header scope | `src/orders/OrderHeader.tsx:21`, `src/orders/OrderHeader.tsx:26` | Demote `Export CSV` to `variant="secondary"` |
| MEDIUM | Introduced | Redundant `Order ID:` label competes with self-identifying `#ORD-*` code | `src/orders/OrderCard.tsx:12` | Omit static label; render `order.code` directly |

### Pre-existing Findings
- `LOW` | `src/orders/OrderCard.tsx:31` — Row hover transition uses `280ms` instead of `<= 150ms`.

### Verification
- **Executed**: Diff hunk `-` audit (`OrderRow.tsx`, `OrderHeader.tsx`, `OrderCard.tsx`); 1-hop consumer check (`OrdersPage.tsx:1–118`).
- **Not verified**: Live `320px` / `200%` zoom reflow and computed contrast in headless browser (no dev server running; leaves risk of flex wrap collision in `OrderHeader.tsx` below `360px`).

**Verdict**: Block — 1 HIGH Regression (`src/orders/OrderRow.tsx:44`); uninspected consumers: none.
```
