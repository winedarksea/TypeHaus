# Truss criteria — what the truss orders are written against (decision 20), hand-worked

**House:** catlin. **Written 2026-11-23** (review C-8, C-9, D §2.4; decisions 19, 20, 24), plain arithmetic, no
engine import. **Oracle for:** `emit/draw/schedules/truss_criteria.py` (S-001's TRUSS CRITERIA block),
`checks/structural/truss_reactions.py` (specified reactions), `checks/structural/uplift_path.py` (the garage's R802.11
read) and the `rafter` deferral. Reproduced by `tests/test_truss_criteria.py`.

**Two statuses, never merged.** *Supporting structure closed*: the chain below the heel is graded now, against the
reactions the order SPECIFIES (`Roof.specified_reactions`; a floor reaction against the maker's published maximum).
*Component confirmed*: the supplier's sealed design is checked against the same criteria. It stays OPEN until a
reaction schedule is quoted into `Roof.published_reactions` — one of the two things the house leaves open.

## 1. The roof trusses (RF-BW-CANOPY, RF-GARAGE: one truss, 4:12, 2x4 fink, 24" o.c., 23'-11 1/8" out to out)

Loads: TCDL 10 psf; BCDL canopy 0, garage 6 psf (5/8" gypsum 2.2 + 14.5" loose-fill R-38 ~1.8 + 2.0 for lights and
services, stated on the order); ground snow 50, flat 0.7 C_e C_t I_s p_g = 0.7(1.0)(1.2)(1.0)(50) = 42 psf; the
ASCE 7-16 §7.7 step drift of `north_entry_piers.md` §3 (surcharge 31.7 + 5.133 (40.219 - y) psf on both roofs, 0 past the
9.8' width: canopy 46.5 / 36.2 / 26.0 on trusses 000..002; garage truss-000 (y 43.281) 16.0, truss-001 (45.219) 6.0,
truss-002 (47.219) none). Unbalanced snow (§7.6.1) is NOT computed here and is the supplier's. Wind V_ult 115 mph,
Exposure B, RC II; the canopy is an open free roof, the garage enclosed.

Gravity reaction at each bearing, (snow + TCDL + BCDL) x tributary x 13.333' (half the 26.667' footprint reach):

```
canopy  T1 (88.5+10) x 1.1146 x 13.333 = 1,464 lb    T2 (78.25+10) x 2.0 x 13.333 = 2,353 lb    T3 (68.0+10) x 1.974 x 13.333 = 2,052 lb
garage  truss-000  (58.0 + 16.0 + 6.0 + 10 ... ) 1,916 lb (joint-bay half 0.974' + 1.0')   truss-001 1,681   002..010 1,547   011 1,523   012 1,829
```

**Uplift: 450 lb net per heel, every truss, both roofs (specified).** The widest truss is 2.0' x 13.333' = 26.67 sf. The engine's
uplift surrogate is 16.832 psf (`north_entry_piers.md` §8): **449 lb gross, no dead relief**, which is the 450; **289 lb net** of
0.6D (6 psf) is the design uplift. (The free-roof C_N 1.3 route of `north_entry_piers.md` §4 gives 0.6W 341 lb gross, 181 lb net:
lower, so the surrogate governs.) `north_entry_piers.md` §4a's "4 truss stations" was stale: there are three.

**The heel tie stands on its nailing (review verifier, 2026-11-23).** Simpson C-C-2021 p.277: H2.5A 700 lb DF/SP, **615 lb SPF/HF**, five
0.131x2-1/2 nails each side; fn. 12: H2.5ASS matches the carbon values only with SCNR/SSA8D ring-shank nails (smooth-shank stainless is
440 lb); **fn. 14: three nails into a 2x4 bottom chord is 260 lb**. The truss is the supplier's, SPF in Minnesota, so the weaker
member's column is SPF (615), not the SP header's 700. Canopy: 450 / 615 = 0.73 with all five nails landing; but design 289 / 260 =
**1.11** at the three-nail row, so the canopy heel is NOT closed until the supplier's drawing shows five truss nails in the heel
(`structural.truss_reactions` is UNKNOWN, not PASS). Garage: design 178 / 260 = 0.68, closed either way; its specified 450 rests on
the five-nail row (0.73). Options if the five nails cannot land: a raised or energy heel, a second tie per heel, or an engineered tie.

**The garage is an IRC R802.11 read (decision 24).** 2018 IRC Table R802.11 (Minnesota 2020), UpCodes, read 2026-11-23:
Exposure B, 115 mph, 24' span, 24" o.c., pitch < 5:12: **178 lb per connection** (>= 5:12: 158); the engine's `wind_tables` grid
gives the same two cells. The 23.93' span reads the 24' column (rounded up, never interpolated). Footnotes: 33 ft mean roof height
(~12 ft here), overhang <= 24" (16"), a 15 psf roof + ceiling dead allowance (10 + 6), corner-zone value kept. 178 / 615 = 0.29 (0.68 at the 260 lb three-nail row).
The canopy is an open structure and keeps its engineered `wood_roof_post` uplift.

**N-S diaphragm chord:** 752 lb on every canopy truss (`canopy_garage_diaphragm.md` §12b). **Deflection:** IRC Table R301.7
L/240 snow (no ceiling on the canopy, ceiling on the garage per the order), L/180 total.

## 2. The floor trusses (statics: P a b / L, patch at its centroid)

**FS-M-NE** (TRIFORCE OJ418S, 16" o.c., bearing centres 217" / 425", L = 208", 40 + 15 psf): uniform (55)(16/12)(17.333)/2 = 635.6 lb.
Peninsula patch x 303.4..387.4, centroid 345.4":

```
line 316 (2 plies)  616 lb : per ply West 616(425-345.4)/208/2 = 117.9   East 616(345.4-217)/208/2 = 190.1   max 753 / 826
line 332 pair       443 lb : 84.8 / 136.7 per ply, plus the fridge's 175 lb at x 232.5: 81.0 / 6.5 per ply (2 plies)
line 348            114 lb + 175 : 206 W / 83 E      lines 364, 380: 175 lb each at x 219..246
```

Total of the peninsula 616 + 443 + 114 = 1,173 lb = 872 dead + 300 stool users. The OJ418S row is uniform only and publishes no
maximum reaction at this seat, so the supporting structure is not closed here by a table: the order states the loads and asks the
supplier to confirm both doubled pairs.

**FS-S-WEST** (TrimJoist J12, 16" o.c., bearing centres 3.5" / 215", L = 211.5"): uniform 646 lb. `W-S-SN3` (bearing since
2026-11-22, ~240 plf with the attic opening trimmer) reaches the y = 272 truss through the 1 1/4" LSL strip, x 131..216: 240 x 85/12
= 1,700 lb at centroid 173.5" (W 334, E 1,366), plus the squash block's 570 lb at x = 120" (W 256, E 314): east max
646 + 1,366 + 314 = **2,327 lb** against J12's published 3,500 lb at 3 1/2" of bearing (3,000 / 3,500 / 4,000 at 1 3/4 / 3 1/2 / 5 1/2"):
0.66, supporting structure closed; the component stays open until TrimJoist's drawing carries the line-272 loads.

## 3. Not graded here, said aloud

The truss's own bottom chord bearing on `BM-BW-RW`/`-RE` (SPF Fc-perp) is the fabricator's. The schedule prints the maximum
reaction and the bearing it must accept: T2 2,353 lb on 1.5" x 5.5" = 285 psi (the glulam's side of it is `roof_beam`, 0.662). On the
garage plates the same check is the supplier's at 1,916 lb. The end-strap couple row (0.774) is a conservative bound: an elastic
distribution over the six straps puts 351 lb on an end strap (0.53 with the chord force).
