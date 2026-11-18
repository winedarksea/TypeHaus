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
two 1 3/4" x 11 7/8" Microllam LVL plies beside the edge line (an LSL rim board since 2026-11-18), x 18'-2 11/32" to
24'-5 21/32" — the outer faces of the two 2-jack + 2-king packs, which run up to the plates.
It is NOT a bearing ref: `resolve/floors.py` would cut every joist at that line.

## 2. What it carries

| Term | Working | Value |
|---|---|---|
| Clear span | the RO | 63.3125" = 5.276 ft |
| Seats | 4 x 1 1/2" pack each end | 6" each |
| Design span L | 63.3125 + 6/2 + 6/2 = 69.3125" | **5.776 ft** |
| Floor strip | the deck edge (y=0) to half-way from the edge rim's line (y=1.125", flush with the stud face at 0.5") to the y=16" line: 1.125 + 14.875/2 | **8.5625" = 0.71354 ft** |
| Floor load | IRC R301.5, 40 live + 10 dead | 50 psf |
| Ply weight | TJ-9000 p.4, 1 3/4" x 11 7/8": 6.1 plf, x 2 | 12.2 plf |
| w total | 50 x 0.71354 + 12.2 | **47.88 plf** |
| w live | 40 x 0.71354 | **28.54 plf** |

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
| Bending | 47.88 x 5.776² / 8 = **199.66 lb-ft** | 2600 x 1.00142 x (3.5 x 11.875² / 6 = 82.26) / 12 = **17,849 lb-ft** (p.4: 2 x 8,925 = 17,850) | 0.011 |
| Shear | 47.88 x 5.776 / 2 = **138.27 lb** | 2/3 x 285 x 3.5 x 11.875 = **7,897 lb** (p.4: 2 x 3,950) | **0.018** |
| Deflection, live | 270 x 28.54 x 5.776⁴ / (2e6 x 3.5 x 11.875³) = 0.000732, + 28.8 x 28.54 x 5.776² / (2e6 x 3.5 x 11.875) = 0.000330: **0.00106"** | L/360 = 69.3125 / 360 = **0.1925"** | 0.006 |

Governs: shear, d/c 0.018. The 2-ply is sized by the bearing it must give the stacked jambs,
not by this span.

## 4. Not graded here

- Dry-use service (the band is inside the envelope; TJ-9000 p.5: Microllam is for dry use).
- Lateral support: the subfloor sheathes the top edge.
- The plies' nails into the edge rim are not billed as a separate line.

## 5. The stacked jambs, by hand (2026-11-13; graded since BASIS_VERSION 2)

**Takedown, per seat.** One tributary length along the wall line, the same on every storey
the stack climbs: half the RO plus the seat (the seated pack is 4 x 1 1/2" = 6", and the
openings above share this RO and centre):

    L = 63.3125 / 2 + 6.0 = 37.65625" = 3.13802 ft

Wall dead load is a stated **15 psf** on the framed height at the pack's outer face (the
truss wall: 1/2" gypsum 2.2, 2x6 at 16" 1.6, 1/2" CDX 1.5, 4" ccSPF at 2 pcf 0.7, blocks and
girts 1.5, 24 ga panel 1.3, batts 0.4, trim/fasteners 0.8 = 10.0 psf, carried at 15). Glass
in the openings is lighter and is not deducted. Floors at 40 + 10 psf over half the way to
the next joist line plus the deck outboard of it (FS-S-EAST and FS-ATTIC both carry an extra
line at y = 9 1/2" and an edge rim at y = 1 1/8", so their edge strips are 1.125 + 8.375 / 2 =
**5.3125" = 0.44271 ft**). The gable carries half of RF-HOUSE's 24" rafter
spacing at 15 dead + 35 snow (`loads.ROOF_TOTAL_LOAD_PSF`, Pg 50 psf).

West seat (the gable is tallest there; W-A-S3 frames 362.355 - 240.75 = 121.605" at x =
218.34"):

| Term | Working | lb |
|---|---|---|
| W-A-S3 gable | 15 x (121.605 / 12) x 3.13802 | 477.00 |
| RF-HOUSE gable strip | 50 x 1.0 x 3.13802 | 156.90 |
| FS-ATTIC edge strip | 50 x 0.44271 x 3.13802 | 69.46 |
| W-S-S2 | 15 x (119.25 / 12) x 3.13802 | 467.76 |
| FS-S-EAST edge strip | 50 x 0.44271 x 3.13802 | 69.46 |
| W-M-S2 | 15 x (119.25 / 12) x 3.13802 | 467.76 |
| **On the seat** | | **1,708.35** |
| of which above FS-S-EAST | the first four | 1,171.13 |

The east seat's gable frames 83.95": 1,560.6 lb on that seat. The west governs.

**Bearing, NDS §3.10.2** (no C_D; C_b taken as 1.0). Sawn plates are SPF at Fc-perp
**425 psi**, dry (TJ-9000's own bearing tables use 425 for sawn plates); Microllam is 750 psi
(TJ-9000 p.5, not increased for duration). A plate on an LVL is governed by the plate.

| Interface | Demand | Area | Stress | Capacity | d/c |
|---|---|---|---|---|---|
| D-M-PORCH pack on W-M-S2's plate | 1,708.35 | 6.0 x 5.5 = 33.0 | 51.77 | 425 | 0.122 |
| W-M-S2's plate on the two plies | 1,708.35 | 6.0 x 3.5 = 21.0 | 81.35 | 425 | 0.191 |
| plies on W-B-S3-FR's plates | 1,708.35 + 138.27 = 1,846.62 | 21.0 | 87.93 | 425 | **0.207** |
| D-S-BALCONY pack on FS-S-EAST's edge rim | 1,171.13 | 6.0 x 1.25 = 7.5 | 156.15 | 425 | 0.367 |

138.27 lb is the band's own end reaction (§3).

**The load crosses FS-S-EAST on its LSL edge rim (2026-11-18).** The gable-end edge lines are
1 1/4" x 11 7/8" TimberStrand LSL rim boards now, not TJI 230s, so TJ-4000 detail CS's squash
plies (two 1 3/4" Microllam plies under each D-S-BALCONY pack, 2026-11-13) are gone: the rim is
rated for vertical load. Each rim lies flush with its wall's stud face (y 0.5"..1.75"), wholly
under the plates. Read off Weyerhaeuser TJ-8000 (March 2025; ESR-1387 Table 4), 1 1/4" 1.3E x
11 7/8":

| Read | Demand | Published | d/c |
|---|---|---|---|
| concentrated vertical load (p.5; needs 4 1/2" of bearing, the pack gives 6") | 1,171.13 lb | 3,760 lb | 0.311 |
| vertical load, the pack over its 6" seat (p.5) | 1,171.13 / 0.5 ft = 2,342.25 plf | 5,400 plf | **0.434** |
| the rim over the 63 5/16" RO as a 1-ply header, uniform only (p.6) | the whole strip, 47.88 plf (§2) | 792 plf (the 6'-0" row: p.6 reads the span c-c of bearing, 5.776 ft; 4 1/2" end bearing, 6" given) | 0.060 |

The header table assumes uniform load: D-M-PORCH's packs stand over the seats, not the span (§2),
and no joist hangs on this rim (it runs parallel to them), so its face-mount-hanger note is moot.

**Governs: the edge rim under the pack, d/c 0.434** (it was the plies on W-B-S3-FR's plates,
0.204). The rim over the opening is a companion to the plies, not counted in them; the plies
still carry the whole strip in §3.

**Published reads, not calculations:**

- Ply fastening, TJ-9000 (July 2026) p.30, *multiple-member connections for top-loaded
  beams*, 1 3/4" pieces, 2 plies: 10d (0.128-0.131 x 3") nails in **3 rows at 12" o.c.** from
  one face (an extra row only at depths of 14" or more), or 12d-16d in 2 rows at 12", or
  SDS/WS screws in 2 rows at 24". The load enters evenly across the plies' width through the
  subfloor and the wall plate, which is the table's condition. Authored: 10d, 3 rows at 12".
- No filler since 2026-11-18: TJ-4000 p.28's *Filler and Backer Block Sizes* (2x6 + 1/2"
  sheathing for a TJI 230) fills an I-joist's web recess; the LSL rim is solid, so the plies
  nail straight to its face.

## Sources

- Weyerhaeuser **TJ-9000** *Trus Joist Beam, Header and Column Specifier's Guide*, July 2026,
  pp.4-5 (Allowable Design Properties; Design Stresses), p.30 (multiple-member connections
  for top-loaded beams).
- Weyerhaeuser **TJ-4000** *TJI Joist Specifier's Guide*, July 2025, p.27 detail CS (squash
  blocks), p.28 (filler and backer block sizes) — history since the LSL rim.
- Weyerhaeuser **TJ-8000** *Trus Joist Rim Board Specifier's Guide*, March 2025, p.5 (vertical
  load transfer at bearing), p.6 (1-ply rim board headers, floor 100%); ICC-ES **ESR-1387**
  Table 4 (the same 5,400 plf / 3,760 lb for 1 1/4" 1.3E).
- AWC NDS 2018 §3.10.2 (compression perpendicular to grain).
- IRC 2018 R301.5 (floor loads), Table R301.7 (L/360).
