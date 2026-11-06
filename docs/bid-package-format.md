# Bid package format

`haus bids houses/<name>` — one request for quote per **crew**, from the same bill of
materials the estimate prices, **unpriced by default** (decision #71). A crew is the trades one
sub takes together, authored in `tasks.toml` `[crews]`; a trade no crew names is its own crew,
and a `self_performed` crew's file is the owner's materials list (decision #115,
`docs/site-state-format.md`). A bid package is a *view*: every
BOM row lands in exactly one package (`takeoff/bom_walk.walk_bom` walks each table once,
`takeoff/cost_codes.cost_code` files it by fact), and nothing here adds to the estimate.

```
haus bids houses/catlin                         # one line per trade, grouped by crew
haus bids houses/catlin --crew envelope         # one crew's package: a part per trade
haus bids houses/catlin --trade framing         # one trade's package, printed
haus bids houses/catlin --trade framing --md out/bids/framing.md --csv out/bids/framing.csv
haus bids houses/catlin --all [--out out/bids]  # <crew>.md + <crew>.csv + README.md + MANIFEST.json
haus bids houses/catlin --priced ...            # carries the estimate's prices; exit 2 without prices.toml
haus bids houses/catlin --trade openings --summary   # the trade's summary schedule, printed
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
   `quantity`, `unit` (the shape's spelling: `pc`, `sheets 4x9` (per row: the layer's sheet size), `cy`), `detail`
   (piece counts, cut lengths, run counts — the shape's per-row builder), `storeys`. A group
   whose lines carry an `application` gets that column after `unit`.
   **Lumber is one line per stock length, by the piece** (`takeoff/lumber_order`): what a yard
   prices, pulls and tickets. `2x6 SPF No. 2 & Btr framing lumber, 104 5/8" PET (2x6)`, 204 pc,
   application `corner stud, king stud, stud`. A full-height stud that fits a precision-end-
   trimmed length (92 5/8", 104 5/8", 116 5/8") is bought as one; a built-up member is bought
   as its plies (`2-2x8` header → 2x8 sticks, application `header (2-ply)`); a bare sawn size
   names the engine's default species (`spf`) and every EWP its depth, thickness and the E
   grade its design values were read at (LVL 2.0E, 1 3/4" LSL 1.55E — never guessed).
   Trusses stay `ea`, one line per made length.
   `--priced` appends `unit low/high` and `total low/high`.
4. **Appendix A** — element tags per line (omitted for recipes that say `tags_appendix=False`).
5. **Appendix B** — the drawing sheets the recipe points at, filtered against
   `emit/draw/sheets.build_sheet_index` so a sheet the house does not draw is not cited.
6. **Appendix C** — owner allowances filed under this trade, listed without dollars unless
   `--priced`. Present only when the house has a `prices.toml` (allowances live there).

## The CSV

`BID_COLUMNS = (trade, group, section, key, description, quantity, unit, application,
storeys, element_tags)`; `--priced` appends `unit_price_low, unit_price_high, total_low,
total_high`. `key` is the qualified estimate key (`slab:DECK_EPS_INT`), which is what
`prices.toml` prices and `costs.toml` files against; the stock-length lines of one lumber size
repeat it, and a priced total splits across them by ordered LF (unit price is per piece).
`application` is what the line frames, for the delivery ticket; blank outside lumber.

## Summaries

Many subs price from a schedule, not a material list. For those trades `--all` also writes
`<trade>-summary.md` and one `<trade>-<table>.csv` per table, each with its own columns
(`takeoff/bid_summaries.SUMMARIES`; builders in `takeoff/summary_*.py`). The package stays
the detail behind it. Every number is a takeoff the model already makes, regrouped:

| trade | tables |
|---|---|
| openings | windows & exterior doors (mark, location, unit and RO, hand, wall, jamb, R308.4 safety glazing, R310 egress, U/SHGC, product, spec URL); hardware sets |
| carpentry | interior doors; trim pack (LF, sticks at the `TrimStandard` stock length, corners); hardware sets |
| roofing | per roof: pitch, sloped SF, squares, eave/rake/ridge LF (3D, seams between roofs left out); hip/valley 0 by vocabulary |
| siding | cladding SF and squares per material and elevation (plan north); the package's trim lines |
| drywall | board SF and sheets by storey, surface, type and thickness; ceiling-height bands; `DrywallStandard.finish_level` or "not stated" |
| flooring, resilient, tile | room finish schedule (net SF, the model's waste, underlayment, base); tile adds wall tile |
| plumbing | fixtures by class (`plumbing_tables.FIXTURE_CLASS_BY_SYMBOL`) and equipment; every fixture with room, product, spec URL |
| electrical | devices by kind and storey; luminaires by form; dedicated and 240 V circuits; panels |

Safety glazing and egress come from the checks' own derivation
(`glazing.safety_glazing_clauses`, `egress.egress_window_rooms`), passed in by the CLI so
`takeoff` never imports `checks`. Wall splits read `envelope.wall_layer_areas`, the yields
`envelope_layer_takeoff` sums, so they add back to the package (`tests/test_bid_summaries.py`).

## Invariants (pinned by `tests/test_bid_packages.py`)

- Every recipe and shape names a section in `ESTIMATE_PLANS` and a trade in `TRADES`.
- Every walked BOM row is in exactly one package (a lumber size as one or more stick lines), except `MIRRORED_SOLID_CATEGORIES` — the
  `structural_solids` volume of a product billed by the foot or the piece in its own section
  (pipe, ducts, raceways, trim, clamps, guards, connectors) — and the unresolved floor-finish
  row, which are left out on purpose (`plans/trade-audit-decisions.md`); catlin never raises.
- Quantities are restated in the unit a sub buys in (`bid_package._shaped_quantity`): wood
  solids in board feet, brick and block by wall face, PV by the module, trusses each,
  aggregate by the yard. The takeoff's own figure stays in the `detail` column.
- Unpriced by default; `priced=True` without an estimate raises.
- `tests/fixtures/bid_goldens/framing.md` is the framing golden (`--bless` rewrites it; the
  model-hash line is excluded from the comparison); two `--all` runs are byte-identical.
