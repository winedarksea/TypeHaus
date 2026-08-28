# `prices.toml` format

The section-by-section grammar for a house's optional `prices.toml`, loaded by
`typehaus.cli.price_file.load_prices`. See that module's docstring for why the file is
optional and how its estimate output behaves when sections are missing.

Every section is optional, and every value is either a single number (an exact unit
price) or an inline table `{ low = ..., high = ... }` (a $-range, e.g. quotes from two
yards):

```toml
[framing]        # $ per lineal foot of ORDERED stock, keyed by lumber profile
"2x4" = 0.72
"2x6" = { low = 0.95, high = 1.35 }

[sheet_goods]    # $ per 4x8 sheet, keyed by material tag
osb = 22.50
zip-r = { low = 42.0, high = 55.0 }

[hardware]       # $ per takeoff unit (usually each), keyed by part number
LUS210 = 1.85

[concrete]       # $ per cubic yard placed, keyed by solid category (slab, footing, ...)
slab = { low = 180, high = 240 }

[floor_heat]     # $ per lineal foot of element/wire, keyed by system name
electric = 12.0

[placeables]     # $ each, keyed by catalog type tag
wolf-range-36 = { low = 9500, high = 12500 }

[furnishings]    # $ each, keyed by catalog type tag — the same rows [placeables]
ikea-sofa-84 = { low = 700, high = 2400 }   # reads, but reported beside the total

[conductors]     # $ per CONDUCTOR-foot of branch wire, keyed by circuit pole count
"1" = { material = { low = 0.20, high = 0.35 }, labour = { low = 0.30, high = 0.75 } }

[solar_modules]  # $ per WATT DC, keyed by module product — modules, racking, rapid shutdown
"Aptos 440 W module" = { low = 3.00, high = 5.20 }

[data_raceways]  # $ per lineal foot of low-voltage raceway, keyed by service (data / spare)
data = { low = 2.80, high = 6.40 }
```

## Driven allowances

`[allowances]` is the one section with no BOM table behind it: a flat lump sum for scope the
model does not resolve, synthesised as a row at quantity 1 with unit `ls`. A row may instead
name a **driver** — a numeric field on a BOM table the model *does* resolve — and become
`rate x model quantity` without leaving the table:

```toml
[allowances]
# undriven: quantity 1, unit "ls", the number written is the line total
site-general-conditions = { low = 35000, high = 80000 }

# driven: the rate is $/SF and the SF comes from the model
roof-ventilated-underlayment-mat = { low = 1.00, high = 1.85, unit = "SF",
                                     driver = "envelope_layers.net_area_sqft[material=standing-seam]" }
finish-door-hardware = { low = 84, high = 306, unit = "ea",
                         driver = "openings.count[kind=door]" }
electrical-afci-gfci-breakers = { low = 39, high = 81, unit = "ea",
                                  driver = "panel_schedule.rows" }
envelope-air-sealing-and-blower-door = { low = 0.50, high = 1.20, unit = "SF",
                                         driver = "space_summary.gross_sf" }
```

Grammar: `"<bom_table>.<field>"`, summed over the table, with an optional
`[<field>=<value>,...]` filter whose clauses are ANDed. Two extras:

- the pseudo-field **`rows`** counts rows, for a table that carries no count column (a panel
  schedule is one row per circuit);
- **`space_summary.conditioned_sf`** and **`space_summary.gross_sf`** are the two addressable
  scalars, read from the `areas` mapping the caller supplies.

Four rules the loader and the estimate enforce:

1. Only `[allowances]` may carry a `driver`. Every other section already joins the BOM
   through `ESTIMATE_PLANS`, and a second per-row quantity source would shadow it silently.
2. A driver that cannot be resolved — unknown table, a field no row carries, a scalar with no
   `areas` behind it — is a hard error naming the key. It never becomes zero.
3. A driver that resolves *to* zero reports the row as **unpriced**, not as a $0 line.
4. `envelope_layers` reports a **layer, not a plane**, so `[scope=roof]` sums every stacked
   layer. Two filters (`[scope=roof,function=cladding]`) are usually what you want.

`haus takeoff` lists every driven allowance whose quantity was measured off BOM rows another
section also **priced**. It is a finding, not an error — measuring a roof vent mat off the
standing seam's area is right, billing the standing seam twice is wrong, and the two drivers
are the same shape — but it is the only automatic check `[allowances]`'s "must be scope no
other section prices" rule has ever had.

Unpriced rows are never silently dropped from a total: every estimate carries the list of
quantity rows it could not price, so a partial catalog reads as a partial estimate rather
than a low bid.

Nor are they silently *added*: what a sofa costs is not what the house costs. Sections in
`EXCLUDED_FROM_TOTAL` are priced and reported like any other and then summed into
`excluded_total` rather than `total`, which is why there is a `[furnishings]` table with
the same keys as `[placeables]` — where the line falls between built-in and loose is the
owner's call, made by which table a type is written into, and no type may sit in both.
