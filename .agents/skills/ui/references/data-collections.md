# Record Collections, Data Tables, and Peer Grids

Apply the rules below when the interface displays a collection of structured records (lists, data tables, or grids of peer cards).

## Attribute Capacity Between Primary View and Secondary Detail

- **When** displaying a collection of records in a single view, include in the primary view only the attributes needed to identify a record, compare records, and trigger the primary action, so the minimum total width required to render horizontal attributes intact does not exceed the container width; for wide 2D data tables on narrow viewports (`320px`), scroll the table horizontally inside its own container so the page itself never scrolls horizontally.
- **When** a record carries more attributes than fit horizontally in the primary container, keep the identifying and comparison attributes in the primary view and move the remaining detail attributes into a secondary disclosure view (drawer, detail pane, or expanded row) opened on selection.

## Column Alignment and Repeated Row Action Weight

- **When** a data column displays quantitative magnitudes meant to be compared by place value across rows (or timers, counters, and prices), end-align the column (`text-align: end`) so digits of the same place value share a vertical axis and enable tabular numerals (`font-variant-numeric: tabular-nums`).
- **When** a data column displays strings read for character recognition rather than numeric magnitude comparison, start-align the column along the natural reading direction (`text-align: start`); if every value in the column shares a fixed character length (such as standardized identifiers or formatted timestamps), combine `font-variant-numeric: tabular-nums` (and `slashed-zero` on identifiers where `0` must be distinct from `O`) so corresponding characters align vertically.
- **When** each row in a list or table carries row-level actions, demote all per-row actions to outlined, ghost/text, or overflow-menu controls, and respond to row hover or action reveal within `150ms` or instantly. *Guardrail*: Never repeat a high-contrast solid-filled primary button on every row of a collection, and never animate hover-revealed row actions with staged or keyframe entrance effects.

## Peer Geometry Locking, Virtualization, and Reordering

- **When** peer cards or record blocks sit in the same row of a grid, clamp variable-length text fields to a fixed maximum line count and pin the action region to the bottom edge of the card so all peers in a row share an identical height and aligned bottom baseline.
- **When** a list or table can render more than `50` items, virtualize the collection (or apply `content-visibility: auto` / pagination) rather than mounting every DOM node at once. *Guardrail*: Never `.map()` unbounded arrays directly into the DOM without virtualization or pagination.
- **When** a list, table, or board supports drag-and-drop reordering or movement, provide a single-pointer alternative (such as move-up/move-down buttons or a move menu on each item) and a keyboard path that achieves the exact same result.
