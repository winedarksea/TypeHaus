# Basement stair and theater carpet

Owner selection, 2026-11-01. `ST-B2M` takes `catlin-stair-carpet`; `RM-B-PLAY-N` takes
`catlin-theater-carpet` over the bedroom cushion (`catlin-bedroom-carpet-pad`). Both are
provisional: no sample, no quote. The generic library `carpet` is no longer used in this house.

## Products (Shaw spec data, `pdmsview.shawinc.com/api/specification`)

| | Stair: [Refine 54923 / Structural 00405](https://philadelphiacommercial.com/products/carpet/details/refine/54923/structural/00405) | Theater: [Emphatic II 30 54255 / Nightlife 56992](https://philadelphiacommercial.com/products/carpet/details/emphatic-ii-30/54255/nightlife/56992) |
|---|---|---|
| Construction | multi-level pattern loop, geometric, 3 x 1.5 ft repeat | cut pile, solid |
| Fiber | solution-dyed EcoSolution Q nylon | continuous-dyed BCF nylon |
| Face weight / pile / total | 16 oz/yd² / 0.082 in / 0.237 in | 30.3 oz/yd² / 0.201 in / 0.36 in |
| Gauge / stitches | 1/10 / 11 per in | 1/10 / 10 per in, twist 5.2 |
| Backing / width | ClassicBac, 12 ft | ClassicBac, 12 ft |
| Traffic (TARR) | Heavy | Moderate |
| Listed installation | Direct glue | Direct glue |
| Swatch median | #415058 (dark blue, light grey web) | #1F1A21 (near-black purple) |

## Why these, and why two carpets

- **Stair: a dense low loop, glued, no cushion.** It wraps the nosing without crushing, and
  glue-down is the commercial stair standard. The installed covering is **1/4 in** (0.237 in +
  adhesive), drawn over the 1 in substrate. Carbon Copy II TL (EcoWorx tile) was rejected
  because a 24 in tile can't wrap a nosing, so every step would need a separate nosing.
- **Theater: dark cut pile over the bedroom cushion**, so it is soft underfoot and dark for
  the screen. **0.735 in** installed (0.36 in + 3/8 in cushion), which is flush with the gym's
  3/4 in stall mats. `D-B-PLAY` is a Z-bar tuck against the mat edge, not a reducer
  (`plan/doorway_transitions.py`, `D_B_PLAY_MAT_ZBAR`).
- **Sharing one carpet was costed and rejected.** The stair is about 105 SF (12–15 SY
  ordered), so one product saves only a separate small cut, its freight and some offcut reuse:
  roughly $100–400. That is smaller than the price difference between the two styles. Putting
  Emphatic on the stair would mean a moderate-traffic cut pile on the nosings, and a
  near-black stair in a basement.

## Stretch-in basis for the theater

Shaw's [Stretch-In Installation](https://qmsview.shawinc.com/Specialty-Markets-PDMS/Installation/Stretch-In-Installation-%281%29)
guide (owner-supplied) covers "carpet with a synthetic secondary backing", and ClassicBac is
one. For commercial carpet it calls for a cushion of **at least 8 lb density, no more than
3/8 in thick**. The bedroom cushion (Future Foam 150553488-32, 8 lb, 3/8 in) meets that exactly.
The guide doesn't name ClassicBac, and the product's own spec lists direct glue only.

## Budget (`prices.toml`, allowances only)

- Theater: $2–3.25/SF material, $1–2.25/SF stretch-in labour, plus the cushion row.
- Stair: `finish-floor-stair-carpet-steps` at $33–60 per riser (15), and
  `finish-floor-stair-carpet-landings` at $3.5–6/SF (30 SF).
- Substrate: `deck 11x1` and `deck 43.375x1` in `[framing]`.

Before 2026-11-01 the stair carpet was billed nowhere: its substrate rows had no price, and
the comments that said the carpet was priced elsewhere were stale.

## Open before ordering

- The dealer confirms stretch-in over cushion is warranted for Emphatic II 30 / ClassicBac.
  If not, glue it down with no cushion. The theater then drops to 0.36 in, about 3/8 in below
  the mats, and `D-B-PLAY` needs a reducer again.
- The cushion and carpet sit on the sealed slab: confirm the slab moisture test and limits.
- Samples of both. Get a current quote, a seam layout for the theater and a stair-cut layout
  (waterfall vs. cap-and-band; the pattern's direction on the risers).
- Nosing visibility on the patterned stair: check the sample under the stair lighting.
