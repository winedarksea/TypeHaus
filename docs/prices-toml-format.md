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
```

Unpriced rows are never silently dropped from a total: every estimate carries the list of
quantity rows it could not price, so a partial catalog reads as a partial estimate rather
than a low bid.

Nor are they silently *added*: what a sofa costs is not what the house costs. Sections in
`EXCLUDED_FROM_TOTAL` are priced and reported like any other and then summed into
`excluded_total` rather than `total`, which is why there is a `[furnishings]` table with
the same keys as `[placeables]` — where the line falls between built-in and loose is the
owner's call, made by which table a type is written into, and no type may sit in both.
