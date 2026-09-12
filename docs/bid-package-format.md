# Bid package format

`haus bids houses/<name>` — one request for quote per trade, from the same bill of materials
the estimate prices, **unpriced by default** (decision #71). A bid package is a *view*: every
BOM row lands in exactly one package (`takeoff/bom_walk.walk_bom` walks each table once,
`takeoff/cost_codes.cost_code` files it by fact), and nothing here adds to the estimate.

```
haus bids houses/catlin                         # one line per trade
haus bids houses/catlin --trade framing         # the package, printed
haus bids houses/catlin --trade framing --md out/bids/framing.md --csv out/bids/framing.csv
haus bids houses/catlin --all [--out out/bids]  # <trade>.md + <trade>.csv + README.md + MANIFEST.json
haus bids houses/catlin --priced ...            # carries the estimate's prices; exit 2 without prices.toml
```

## The Markdown package

Rendered through `emit/md_writer`, byte-deterministic (no date; sorted throughout; rounding
happens in the builder), so two runs over one model produce identical bytes and the
`MANIFEST.json` sha256s mean something.

1. **Header** — `House`, `Trade`, `Engine`, `Model hash` (the plan's `_content_hash`), `Lines`.
2. **Intro** — the trade's recipe text (`takeoff/bid_recipes.RECIPES`), then a callout:
   quantities are net of waste; this is a request for quote.
3. **One table per section** in the recipe's `section_order`, remaining sections in estimate
   order. Columns: `item` (a readable label with the id kept, → `takeoff/labels.describe`),
   `quantity`, `unit` (the shape's spelling: `LF ordered`, `sheets 4x8`, `cy`), `detail`
   (piece counts, cut lengths, run counts — the shape's per-row builder), `storeys`.
   `--priced` appends `unit low/high` and `total low/high`.
4. **Appendix A** — element tags per line (omitted for recipes that say `tags_appendix=False`).
5. **Appendix B** — the drawing sheets the recipe points at, filtered against
   `emit/draw/sheets.build_sheet_index` so a sheet the house does not draw is not cited.
6. **Appendix C** — owner allowances filed under this trade, listed without dollars unless
   `--priced`. Present only when the house has a `prices.toml` (allowances live there).

## The CSV

`BID_COLUMNS = (trade, group, section, key, description, quantity, unit, storeys,
element_tags)`; `--priced` appends `unit_price_low, unit_price_high, total_low, total_high`.
`key` is the qualified estimate key (`slab:DECK_EPS_INT`), which is what `prices.toml`
prices and `costs.toml` files against.

## Invariants (pinned by `tests/test_bid_packages.py`)

- Every recipe and shape names a section in `ESTIMATE_PLANS` and a trade in `TRADES`.
- Every walked BOM row is in exactly one package; catlin never raises.
- Unpriced by default; `priced=True` without an estimate raises.
- `tests/fixtures/bid_goldens/framing.md` is the framing golden (`--bless` rewrites it; the
  model-hash line is excluded from the comparison); two `--all` runs are byte-identical.
