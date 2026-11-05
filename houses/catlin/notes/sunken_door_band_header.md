# `D-B-SUNKEN` flush band header — hand check

**House:** catlin. **Element:** `D-B-SUNKEN` (63 5/16" RO French pair) in `W-B-S3-FR`, headed
in `FS-M-EAST`'s band (`Door.header_in_band`). **Written:** 2026-10-31, by hand from the maker's
document, before the record was compared against it.
**Oracle for:** `typehaus/engineering/band_header.py` (`band_header/D-B-SUNKEN`), reproduced by
`tests/test_band_header.py`.

## 1. Why the header is in the band

The RO is 82 7/8" with a -1 3/4" sill, so the rough head stands 4 5/8" under the plates. The
R602.7 2-2x10 grew 9 1/4" up from it, through both top plates and 1 5/8" past the wall top
(geometry review C3-E2). `W-B-S3-FR` is BEARING but runs PARALLEL to `FS-M-EAST`'s joists:
the member over the opening is the y=0 edge-joist line. So the beam goes there, flush:
two 1 3/4" x 11 7/8" Microllam LVL plies beside the edge I-joist, x 18'-2 11/32" to
24'-5 21/32" — the outer faces of the two 2-jack + 2-king packs, which run up to the plates.
It is NOT a bearing ref: `resolve/floors.py` would cut every joist at that line.

## 2. What it carries

| Term | Working | Value |
|---|---|---|
| Clear span | the RO | 63.3125" = 5.276 ft |
| Seats | 4 x 1 1/2" pack each end | 6" each |
| Design span L | 63.3125 + 6/2 + 6/2 = 69.3125" | **5.776 ft** |
| Floor strip | edge line at y=0 to half-way to the y=16" line; no deck outboard | **8" = 0.6667 ft** |
| Floor load | IRC R301.5, 40 live + 10 dead | 50 psf |
| Ply weight | TJ-9000 p.4, 1 3/4" x 11 7/8": 6.1 plf, x 2 | 12.2 plf |
| w total | 50 x 0.6667 + 12.2 | **45.53 plf** |
| w live | 40 x 0.6667 | **26.67 plf** |

**The jamb loads are not in the span.** `D-M-PORCH` above is the same 63 5/16" RO on the same
centre, so its 2-jack + 2-king packs stand on these seats exactly (x 18'-2 11/32"..18'-8 11/32"
and 23'-11 21/32"..24'-5 21/32"). The review's "west jamb at x≈19'-1"" was the stale
`CN-M-HD-PORCH-W` strap station, from before the 2026-10-29 re-centring; it is re-stationed onto
the pack. Nothing else of `W-M-S2` stands on its bottom plate inside the RO.

## 3. The check (Weyerhaeuser TJ-9000, July 2026)

p.5, Microllam LVL 2.0E beam, 100% duration: Fb 2,600 psi at 12" x (12/d)^0.136,
Fv 285 psi, E 2.0 x 10^6 psi. b = 2 x 1.75 = 3.5", d = 11.875".

| Limit state | Demand | Capacity | d/c |
|---|---|---|---|
| Bending | 45.53 x 5.776² / 8 = **189.9 lb-ft** | 2600 x 1.00142 x (3.5 x 11.875² / 6 = 82.26) / 12 = **17,849 lb-ft** (p.4: 2 x 8,925 = 17,850) | 0.011 |
| Shear | 45.53 x 5.776 / 2 = **131.5 lb** | 2/3 x 285 x 3.5 x 11.875 = **7,897 lb** (p.4: 2 x 3,950) | **0.017** |
| Deflection, live | 270 x 26.67 x 5.776⁴ / (2e6 x 3.5 x 11.875³) = 0.000684, + 28.8 x 26.67 x 5.776² / (2e6 x 3.5 x 11.875) = 0.000308: **0.00099"** | L/360 = 69.3125 / 360 = **0.1925"** | 0.005 |

Governs: shear, d/c 0.017. The 2-ply is sized by the bearing it must give the stacked jambs,
not by this span.

## 4. Not graded here

- **Bearing under the stacked jambs** (Fc⊥: LVL 750 psi, the SPF plates under it ~425 psi):
  the `D-S-BALCONY`/`D-M-PORCH` jamb loads reach the seats through the plies. No load takedown
  exists in this engine; the same stack bore on the old I-joist edge and plates.
- The two-ply nailing, the plies' connection to the edge I-joist, and dry-use service (the
  band is inside the envelope; TJ-9000 p.5: Microllam is for dry use).
- Lateral support: the subfloor sheathes the top edge.

## Sources

- Weyerhaeuser **TJ-9000** *Trus Joist Beam, Header and Column Specifier's Guide*, July 2026,
  pp.4-5 (Allowable Design Properties; Design Stresses).
- IRC 2018 R301.5 (floor loads), Table R301.7 (L/360).
