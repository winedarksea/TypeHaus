# North entry canopy, piers and headers — hand-worked basis

**House:** catlin
**Structure:** `PT-BW-W`, `PT-BW-E`, `PT-BW-RE`, `PT-BW-GW`, `PT-BW-GE`, `PT-BW-RNE` (cast
piers, of which `PT-BW-RE` and `PT-BW-RNE` run on up as full-height cast **columns**) and
their footings `FT-BW-*`; `PT-BW-CW`/`-CNW` (the two surviving 6x6 KDAT roof columns — the
EAST pair went on 2026-09-10 when the east header moved onto concrete);
`BM-BW-RW`/`BM-BW-RE` (3-ply 2x12 KDAT roof headers); `RF-BW-CANOPY`.

> ⚠ **Revised 2026-09-10, after the first pass, on two owner calls.** (1) The canopy is
> **freestanding**: its headers bore north on `W-G-W` / `W-G-E` and now bear on two columns
> of their own, because a ~3,130 lb reaction on the END of a stud wall is not a detail and
> no bearing post was ever authored. (2) The garage-side piers stop at **-7'-0"**, the
> garage's own footing plane, not at the house-side -9'-9 7/16" — that depth is cheap only
> because the basement excavation is already open, and there is no such excavation out here.
> §6 carries both. The eight framed-terrace piers of the first pass are gone entirely (they
> stood east of a flight that runs west); the tiers are cast pours and are §7's business,
> not this note's.
**Written:** 2026-09-10, by hand, before the calculation it oracles was encoded.
**Oracle for:** `engineering/deck_tie.py` (§10, added 2026-09-21); `engineering/roof_beam.py` (§5); `engineering/pier_basis.py` /
`engineering/deck_post.py` / `engineering/spread_footing.py` (§6, axial and bearing); and
**`roof_moment.roof_base_moments` (§8, the canopy's east columns in BENDING)**, added
2026-09-11. Reproduced by `tests/test_north_entry_piers.py` and, for §8,
`tests/test_pier_calcs.py`. §3a (the drift trusses) oracles `structural.truss_reactions`'s
`drift_trusses`, reproduced by `tests/test_truss_reactions.py`.

> ⚠ **`deck_post`'s own `oracled_by` named the SUPERSEDED `breezeway_piers.md` until
> 2026-09-11 and did not name this note at all.** The lint only asserts that a named note
> exists on disk, so an oracle pointing at a calculation retired on 2026-09-10 read exactly
> like one pointing at a current one. It names this note and §8 now.
**Companions:** `notes/north_entry_structure.md` — the bearing map and what carries what,
without arithmetic. `notes/breezeway_piers.md` — the retired glazed breezeway's piers,
superseded. `notes/catlin_truss_engineering.md` — the wall the canopy dies against.
**What is asked of the reviewer:** check §3. Everything downstream is ordinary NDS and ACI
arithmetic against a load case that is **authored, not derived**, and §3 is where that load
comes from. If §3 is wrong, every ratio in §5 and §6 is wrong by the same factor.

> ⚠ **The drift case governs and the engine computes no part of it.** The only `p_f` in the
> whole codebase is a `0.7 * p_g` in a drawing emitter; drift, unbalanced and sliding
> magnitudes are computed nowhere. `preferences.toml [structural] roof_beam_snow_psf` is
> where the number below lands, and it is the only place the engine reads it from.

> ⚠ **The drift triangle is 9.8 ft long and the passage is 6 ft.** It runs another 3.8 ft
> into the garage roof, so **the garage's two southernmost trusses are drift trusses too**.
> Spec them to the fabricator as `p_g = 50 psf` **with the surcharge from the adjacent house
> wall named explicitly**. A quote against "50 psf ground snow" prices ordinary trusses, and
> the difference is roughly +15% to +30% per truss.

> ⚠ **These piers bottom at the same elevation as the house footing, about 10 inches away.**
> Cast in the open basement excavation — the owner's stated premise, and the only reason
> reaching this depth is cheap — that is a non-issue. Cast **after** the house footing is in
> and backfilled, a shaft 10 inches away bearing at the same depth is **undermining**. This
> is a sequencing note, not a detail note, and it belongs on the drawings as one.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| pier line | authored, `params/north_entry_frame.py::PIER_LINE_Y_FT` | y = 37'-6" |
| house cladding face | `W-B-N2` axis y=36'-0" + 4" concrete + 3 1/4" foam/skin | y = 36'-7 1/4" |
| clear, pier face to cladding | 37'-6" − 36'-7 1/4" − 6" (half a 12" round) | 6 3/4" |
| clear, pier face to concrete | 37'-6" − 36'-4" − 6" | 10 3/4" |
| garage plate top | `W-G-E`/`W-G-W` `z1` | +7'-4" |
| header top | = garage plate, so the two roof planes are one plane | +7'-4" |
| header soffit | +7'-4" − 11 1/4" | +6'-4 3/4" |
| bearing plane (seat soffits, pier tops) | −1" − 7 1/4" − 7 1/4" | −1'-3 1/2" |
| site grade | `params/foundations.py::SITE_GRADE` | −2'-10" |
| pier top above grade | 34" − 15.5" | 18 1/2" |
| footing underside | house footing underside | −9'-9 7/16" |
| footing thickness | authored | 10" (12" under the four moment piers, 2026-09-17) |
| roof column length | 6'-4 3/4" − (−1'-3 1/2") | 7'-8 1/4" |
| header span, node to node | 43'-2 5/8" − 37'-6" | 5'-8 5/8" = 5.719 ft |
| header back span, bearing to bearing | `GARAGE_SEAT_Y_FT` 42'-5 3/4" − 37'-6" | 4'-11 3/4" = 4.979 ft |
| header tail past the north bearing | 43'-2 5/8" − 42'-5 3/4" | 8 7/8" |
| canopy plan footprint | (31'-4" − 4'-8") x (43'-2 5/8" − 37'-2 5/8") | 26.667 x 6.0 = 160.0 ft² |

**Why the line sits at 37'-6" and not further south.** At 37'-2 5/8" a 12" round leaves
1 3/8" to the cladding and 4 5/8" to the concrete. That is not formable, and it means
excavating hard against the house foam. The 3 3/8" north costs 3 3/8" of canopy and buys a
buildable hole.

## 2. What each element carries

| element | carries |
|---|---|
| `BM-BW-RW` / `BM-BW-RE` | half the canopy roof each: 80.0 ft² |
| `PT-BW-CW` / `PT-BW-CNW` | half of the WEST header's reaction each — the only wood columns left |
| `PT-BW-W` | the west roof column **and** the landing's west seat |
| `PT-BW-E` | the landing's east seat |
| `PT-BW-RE` | the east header directly: it IS the east column, cast to the soffit |
| `PT-BW-GW` / `PT-BW-GE` | the garage-side seat beam, landing load only |

**No snow on the landing, the tiers or the paver landing.** The canopy runs x=6'-0" to
30'-0" with its south edge 7 3/8" off the house, so the whole entry path is under roof.
That is a benefit of this scheme, and it is why the landing is graded at IRC Table R301.5's
40 psf live and not against snow.

## 3. The design snow — ASCE 7-16 §7.7 roof-step drift **(READ THIS ONE)**

The house's north face is a gable end standing 6 1/2" south of the passage roof, rising
from +20'-2 1/4" at the corners to +29'-2 1/4" at the ridge — **12 to 21 feet above the
canopy**. That is a roof-step drift condition and it governs.

| term | working | value |
|---|---|---|
| ground snow | `Site.ground_snow_load_psf`, authored | p_g = 50 psf |
| snow density | γ = 0.13 p_g + 14 = 0.13(50) + 14 | 20.5 pcf |
| balanced flat-roof | p_f = 0.7 C_e C_t I_s p_g = 0.7(1.0)(1.2)(1.0)(50) | 42 psf |
| leeward drift height | h_d = 0.43 · l_u^(1/3) · (p_g+10)^(1/4) − 1.5, l_u = 36 ft | 2.45 ft |
| windward drift height | 0.75 · [0.43 · 25^(1/3) · 60^(1/4) − 1.5] | 1.50 ft — does not govern |
| drift surcharge at the wall | p_d = h_d γ = 2.45(20.5) | 50.3 psf |
| drift width | w = 4 h_d = 4(2.45) | 9.8 ft |
| peak total at the house wall | 42 + 50.3 | **92 psf** |

`C_t = 1.2` because this is an unheated open canopy, not a roof over conditioned space.

**Averaging the triangle across the canopy.** The surcharge is a triangle starting at the
house wall (y = 36'-7 1/4") and dying 9.8 ft north (y = 46'-5"). The canopy's own footprint
runs y = 37'-2 5/8" to 43'-2 5/8":

| term | working | value |
|---|---|---|
| surcharge at the canopy's south edge | 50.3 · (1 − (37.22 − 36.60)/9.8) | 47.1 psf |
| surcharge at the canopy's north edge | 50.3 · (1 − (43.22 − 36.60)/9.8) | 16.3 psf |
| average across the canopy | (47.1 + 16.3)/2 | 31.7 psf |
| **design snow** | 42 + 31.7 | **73.7 psf** |
| dead | roofing + deck + framing + self weight | 10 psf |
| **design total** | | **83.7 psf** |

This agrees with the 90–101 psf screen already recorded in `plans/north-gable-extension.md`
at the peak, so the number is not new to the house.

**Taking the full §7.7 surcharge on a GABLE lower roof is conservative and is not a
checked geometry.** §7.7 assumes a flat-ish lower roof; this one sheds east and west, so
some of the drift would in practice spill off the eaves. Nothing here credits that.

### 3a. How far into the garage — the drift trusses (oracles `structural.truss_reactions`, 2026-09-21)

The triangle is 9.8 ft wide and the canopy is 6.0 ft deep, so it spills onto `RF-GARAGE`.
Until 2026-09-21 the truss-reaction guard knew only roofs whose BEAMS the house grades at
the drift (`roof_beam` records) — the canopy — and the garage, whose trusses bear on walls,
was never held to it. The width is now authored (`roof_beam_drift_width_ft = 9.8`) and laid
from the canopy's **south** footprint edge rather than the house cladding face, which is
conservative by the 0.62 ft between them:

| term | working | value |
|---|---|---|
| canopy footprint, y | resolved `RF-BW-CANOPY` | 37.219 … 43.219 ft |
| drift limit | 37.219 + 9.8 | y = 47.019 ft |
| reach past the canopy | 47.019 − 43.219 | **3.80 ft** into the garage |
| (from the cladding face instead) | 36.604 + 9.8 | y = 46.404 ft — the same two trusses |
| `truss-000` (gable) | y = 43.281 | inside |
| `truss-001` | y = 45.219 | inside |
| `truss-002` | y = 47.219 | outside, by 0.20 ft |

So **two** drift trusses, `truss-000` and `truss-001` — the "two southernmost" of the banner.
The guard now refuses a reaction row with no drift surcharge when the row names one of those
two, or names no model truss at all (a fabricator's mark the model cannot place); a row for
`truss-002` … `truss-012` on ground snow alone is correct and passes. The canopy, drifted
whole, refuses any such row as before.

## 4. Uplift — stated, not left open

| term | working | value |
|---|---|---|
| velocity pressure | q_h at 115 mph (V_ult), Exposure B, RC II, h ≈ 12 ft | ≈ 16.4 psf |
| free-roof net pressure | C_N ≈ 1.3 | ≈ 21.3 psf |
| uplift per header | 21.3 psf × 80.0 ft² | 1,706 lb |
| dead resisting per header | 10 psf × 80.0 ft² | 800 lb |
| net, 0.6D + 0.6W, per column | (0.6(1,706) − 0.6(800)) / 2 | **272 lb** |

Well inside the `ABU66SS` standoff base on its cast-in `AB-058-10-SS`. **Uplift is not a
governing case here** and the detail needs no change for it. Four columns now rather than
two, so the per-column net above halves again to about 136 lb.

### 4a. The truss-to-header ties

| term | working | value |
|---|---|---|
| bearings per header | 4 truss stations | 4 |
| gross wind uplift per bearing | 1,706 / 4 | 427 lb |
| 0.6W, no dead relief | 0.6 (427) | **256 lb** |
| 0.6W − 0.6D | 0.6 (427 − 200) | 136 lb |

Eight authored `H2.5ASS`, one per bearing — stainless because these land on treated southern
pine at an entry salted every winter, and the house buys stainless at every KDAT joint.

> ⚠ **CLOSED 2026-09-11, and the number that looked wrong is what closed it.** This note
> said for a day that the stainless H2.5ASS was not the galvanized tie's 700 lbf, because the
> figures in circulation for it were materially lower — a 440/75/70 uplift-F1-F2 row in
> secondary listings of the Simpson C-C catalog — and none could be tied to a primary table.
>
> Simpson engineering letter **L-F-SSNAILS** explains both halves at once. A stainless
> connector carries the carbon connector's published allowables; the one thing that reduces
> them is that stainless SMOOTH-shank nails withdraw less than carbon ones, and the letter's
> Nail Substitution Chart recovers the full carbon values with Strong-Drive SCNR Type 316
> ring-shank nails. **The 440/75/70 row is real — it is the stainless smooth-shank table.**
> It was never a bad figure, it was the answer to a different installation.
>
> So the H2.5ASS is a **700 / 110 / 110** part here, and `library/hardware.py` records it,
> against 256 lb of demand.
>
> ⚠ **AND IT KEEPS THE 700 WHERE THE GALVANIZED TIE DROPPED TO 615 ON 2026-09-14.** That is
> not an inconsistency between two records of one stamping — it is the species column. Simpson's
> catalog (C-C-2024 p. 288) splits the H/TSP table into DF/SP and SPF/HF halves, which ESR-2613
> does not, and General Note e picks the column by the **lowest specific gravity in the
> connection**. These eight land on treated southern pine at SG 0.55 and stay in the DF/SP
> column; the ~270 galvanized ties elsewhere in the house land on SPF plates at SG 0.42 and
> take the catalog's 615. **Stainless parity is a claim about steel and nails and says nothing
> about species**, so it rides across unchanged in both directions.
>
> ⚠ **THE NAIL IS NOW A SPECIFICATION ITEM.** That 700 lbf is conditional on **SSA8D**
> stainless ring-shank nails, five to the rafter and five to the plates, substituting for the
> catalog's 8d common 0.131 x 2-1/2 in. Drive these eight ties with stainless SMOOTH-shank
> nails and each is worth 440 lbf instead, at 0 FAIL, with nothing in the model able to see
> it. The canopy survives either nail at 256 lb; the drawings must still say SSA8D.
>
> ⚠ **The letter states its own expiry: "valid until 12/31/2024".** No later revision could
> be retrieved on 2026-09-11. It is the manufacturer's own statement about its own part,
> which is exactly what this note previously asked for, but a submittal should re-pull the
> current letter rather than cite this one.

## 5. The headers — `BM-BW-RW` / `BM-BW-RE` (oracles `engineering/roof_beam.py`)

3-ply 2x12 KDAT, southern yellow pine No. 2.

| term | working | value |
|---|---|---|
| tributary | 160.0 ft² / 2 bearing lines | 80.0 ft² |
| span | node to node | 5.719 ft |
| uniform load | 80.0 × 83.7 / 5.719 | 1,170.9 plf |
| moment | w L² / 8 = 1,170.9 (5.719²) / 8 | 4,787 lb-ft |
| shear | w L / 2 = 1,170.9 (5.719) / 2 | 3,348 lb |
| section modulus | 3 (1.5) (11.25²) / 6 | 94.9 in³ |
| moment of inertia | 3 (1.5) (11.25³) / 12 | 533.9 in⁴ |
| F_b' | 875 × C_D 1.15 × C_M 0.85 | 855.3 psi |
| **moment capacity** | 855.3 (94.9) / 12 | **6,766 lb-ft → d/c 0.71** |
| f_v | 1.5 V / A = 1.5 (3,348) / (4.5 × 11.25) | 99.2 psi |
| F_v' | 175 × 1.15 × 0.97 | 195.2 psi → d/c 0.51 |
| live deflection | 5 w L⁴ / (384 E' I), E' = 1.4e6 × 0.90 | 0.0369 in |
| limit | L/240 = 68.63 / 240 | 0.286 in → d/c 0.13 |

**Bending governs at d/c 0.71.** **Ply count is the lever, not depth**: a 2-ply 2x12 reaches
d/c 1.06 in bending and 0.76 in shear, and a 2-ply 2x10 fails outright at d/c 1.57.

**The glulam alternative is REFUSED, and the engine is the reason (owner, 2026-09-12).** A
3-1/2" x 11-7/8" treated glulam would carry this easily; what it would not do is stay in the
register. `_SECTION` above matches a sawn `N-2xM` and nothing else, so a `"3.5x11.875"` makes
`_one()` return `_incomplete("published design values for the section as sold")` and both
records go INCOMPLETE. Nothing picks them up: `engineering/glulam_beam.py` left the
registered-kind tuple on 2026-09-11 and is deck-only besides — 40 psf live at `C_D` 1.0,
which cannot carry this 73.7 psf drift case. Retyping trades a d/c of 0.71 for a gap.
**And the ply seam, the one real durability argument, does not reach these two.** Both beams
ARE the canopy's eave bearing lines: the trusses land on their tops, so both seams sit inside
the roof assembly under the deck, 1'-4" inboard of the drip line. FPInnovations' mass-timber
durability guidance carves out exactly this case — avoid appressed parallel beams holding a
capillary **unless the beams are preservative treated**, and KDAT is. (→ DESIGN-LOG.md,
"Site and the four structures")

**No repetitive-member factor.** NDS §4.3.9's C_r of 1.15 wants three or more members
**spaced** not more than 24" apart and joined by a load-distributing element. A built-up
beam's plies are in contact and share load through their nails alone. Claiming C_r would
buy 15% of capacity the section has not got.

**The span above is the whole beam, and since 2026-09-10 that is conservative by ~38%.**
`roof_beam.py` takes node to node, 5.719 ft, as a simple span. What is built is a 4.979 ft
back span between `PT-BW-CW` and `PT-BW-CNW` with an 8 7/8" tail carrying the roof plane out
to the garage wall. The real maximum is about 3,470 lb-ft (back-span moment w L²/8 =
3,629 less half the cantilever moment w a²/2 = 320 lb-ft) against the 4,787 above, so
**every ratio in this section is on the safe side of what is built and none of them was
re-pinned.** If the module ever learns to resolve a beam's real bearings, expect d/c 0.71 to
drop to about 0.51 and re-work this table rather than assuming it drifted.

## 6. The piers (oracles `pier_basis` / `deck_post` / `spread_footing`)

Six piers on **two** bearing planes, and the split is the first thing to read.

> ⚠ **Two of the six are not piers, and the bearing numbers below are unchanged by that.**
> `PT-BW-RE` and `PT-BW-RNE` became full-height 12" cast columns on 2026-09-10, running
> unbroken from footing to header soffit and fixed at the base — the canopy's east lateral
> system (`notes/north_entry_structure.md` §1a). Same section, same cage, same pad, same
> footing: the shaft simply does not stop at −1'-3 1/2". **What is NOT re-worked here is the
> consequence of the fixed base**, and it is the engineer of record's: the base moment is a
> lateral demand this section was never asked to carry, `PT-BW-RNE` has 4'-6" of embedment
> below grade against roughly 5'-6" that IBC 1807.3.2.1's non-constrained formula wants for
> it in presumptive sand, and k·l_u/r on the exposed 9'-2 3/4" is about 74 as a SWAY column
> where §6's slenderness reading below was taken non-sway.

| pier | carries | pad | bottom | bearing d/c |
|---|---|---|---|---|
| `PT-BW-W` | `PT-BW-CW` + house-side west seat | 2'-0" | −9'-11 7/16" | 0.95 |
| `PT-BW-E` | house-side east seat | 2'-0" | −9'-9 7/16" | 0.34 |
| `PT-BW-RE` | the east header (full-height column) | 2'-0" | −9'-9 7/16" | **0.94** |
| `PT-BW-GW` | `PT-BW-CNW` + garage-side west seat | 2'-0" | −7'-4" | 0.84 |
| `PT-BW-GE` | garage-side east seat | 1'-6" | −7'-0" | 0.45 |
| `PT-BW-RNE` | the east header (full-height column) | 2'-0" | −7'-0" | 0.83 |

> **The west pair's rows moved again on 2026-09-20, and only their BOTTOMS moved.** Both
> joined `north_entry_frame._MOMENT_PIERS` — 12" pads where they had 10" and 8", tops held
> at `FOOTING_TOP_FT` and the garage strip's plane — so the shafts, the stations and
> `column_base`'s embedment are all untouched. The d/c rises because `W-BW-SCREEN`'s line
> load is in the demand now (§2's wall table above, 1.97 ft² of equivalent R507.3.1
> tributary), not because the pads changed: `PD-BW-W` is at **0.95** and is the tightest
> landing pad in the house, on presumptive soil with **no boring log**. Worth flagging.
>
> **Every ratio in that column moved on 2026-09-18** and the derivation is §6's 2026-09-17
> bearing table below, re-worked. Three things changed at once: the roof share is graded at
> the §3 **design** snow (73.7 psf) rather than the ground snow, which raises it; the pad's
> and the shaft's own weight are in the demand, which raises it further; and the soil the
> pad displaced is credited, which lowers it. The net is up on every pier that carries
> canopy and down on the two that carry only landing.

> ⚠ **Re-read 2026-09-11, when the landing narrowed.** `LANDING_EAST_FT` came in from 11'-6"
> to 9'-7" — `D-G-SERVICE`'s east jamb, once the door moved into the garage's SW corner — so
> both seat beams span 3'-7" instead of 5'-6", the four landing piers `PT-BW-W`/`-E`/`-GW`/
> `-GE` stand 3'-7" apart on each line, and the deck they share is 23.5 ft² plus the 13.2 ft²
> interior landing, down from 36.1 + 11.7. Every ratio in this table and every deck term
> below moved with it; the two east columns carry no landing and did not move. The pier
> STATIONS on the east line are x=9'-7" now, not 11'-6".

**The house-side three reach −9'-9 7/16" for a reason that is not bearing.** The basement
excavation is already open to that depth, so the extra 2'-9" of shaft costs shaft and
nothing else — and it must be cast **while that hole is open**, because a shaft bottoming at
the house footing's own elevation 10" away, cast after backfill, is undermining.

**There is no such excavation on the garage side, so those three stop at −7'-0".** That is
the garage strip footing's own underside, 50" of cover against Minn. R. 1303.1600 Zone II's
42", and they are cast with the garage foundation on one bearing plane. It also settles the
plan lap: `PT-BW-GW`'s and `PT-BW-RNE`'s pads reach about 8" under `FT-GF-S1`/`-S3`, which
at the house-side depth was undermining and a sequencing note, and at this depth is two
pours meeting edge to edge.

**And it is what keeps the hydrant simple.** `PR-G-HYDRANT-CW` runs north at x=11'-0" with
its invert at −8'-10". At −7'-0" it passes 1'-10" **under** `FT-BW-GE` rather than threading
between a shaft and a pad; `mep.footing_clearance` grades it and passes.

Worst case is `PT-BW-W`, which carries the west roof column **and** the landing's west seat.

| term | working | value |
|---|---|---|
| roof tributary | 160.0 / 2 headers / 2 supports per header | 40.0 ft² |
| deck tributary | (23.5 + 13.2) ft² of landing / 2 seat lines | 18.4 ft² |
| wall line load | `W-BW-SCREEN` + `SC-BW-WEST` on `BM-BW-SCSILL`, half | 98 lb |
| roof live | 40.0 × **73.7** psf (§3's design snow) | 2,948 lb |
| deck live | 18.4 × 40 psf | 736 lb |
| dead | (40.0 + 18.4) × 10 psf + self weight + carried + wall | 1,766 lb |
| service | | **5,450 lb** |
| factored | 1.2 D + 1.6 L | **8,014 lb** |

**The wall line load, worked (2026-09-20).** `BM-BW-SCSILL` is the sill under `W-BW-SCREEN`,
hung on `HU28-2Z` off the two 6x6 KDAT canopy columns `PT-BW-CW`/`-CNW`, which stand on
`PT-BW-W` / `PT-BW-GW` through `supported_by`. A **wall is neither a `FloorSystem` nor a
`Roof`**, so until 2026-09-20 `pier_basis._unmodelled_beams` reported that beam as unpriced
and `deck_post` declined to publish an axial ratio for either pier at all. A wall's dead load
never needed a tributary area: it is a plf times a run.

| term | working | value |
|---|---|---|
| `W-BW-SCREEN` | its own resolved layer stack over its 4.08' height | 30.54 plf |
| `SC-BW-WEST` | 26 slats, 1 1/2" × 3 1/2" × 2.40', kdat at 600 kg/m³, over 6.57' | 12.94 plf |
| line | | **43.48 plf** |
| run | the wall's axis inside `BM-BW-SCSILL`'s own footprint | 4.52' |
| total | | **196.6 lb** |
| each column | two bearings | **98.3 lb** |

The slat clerestory is a third of it, and leaving it out would understate the sill by 30% —
the same partial-stack failure `resolve/assembly_weight.dead_load_plf` refuses one layer
down. The plf is the one `checks/structural/guards.py` already printed ("guard wall
`W-BW-SCREEN` weighs 31 plf") in the same run that called this load unknown; it moved to
`resolve/assembly_weight.py` so a calc could read it, because `engineering` may not import
`checks`. `checks/structural/deck.py` divides the same pounds into R507.3.1's currency —
98.3 / 50 psf = 1.97 ft² — rather than holding a second answer about one load.

> ⚠ **WITHDRAWN 2026-09-21 as a DEMAND, kept as built.** With the landing tied to the garage (§10)
> the four landing piers lean: `deck_post` grades them "axial, tied column" (d/c 0.007-0.027)
> and the dowel-anchorage row below no longer exists for them. The 12" pads stay in
> `_MOMENT_PIERS` — they cost nothing now and are what a reversal would need.

**Closing it uncovered a real FAIL, and that was the point.** Both piers left
`deck_post._detailing_only`'s six load-independent states for `_moment_column`'s twelve, and
the twelfth is dowel ANCHORAGE into the base — ACI 318-19 §25.4.3.1's ℓ_dh, 7.115" for a #5.
`PT-BW-GW` had an 8" pad giving 5.375" and **no base dowels at all**: d/c 1.32. It was never
the wall load (98 lb is 1.5% of factored axial). `_MOMENT_PIERS` had covered the landing's
EAST column and not its west, while `pier_basis._base_moments` split the lateral case "over
4 fixed column(s)" and `structural.lateral_racking` named all four — so the west pair carried
its twins' base moment with nothing detailed to deliver it, and nobody saw it because their
records were detailing-only. The west pair joined `_MOMENT_PIERS` in the same commit: 12"
pads, **tops unchanged**, bottoms down 2" (`PT-BW-W`) and 4" (`PT-BW-GW`) — 0.073 cy and 8
more #5 dowels — and both land at **0.759**, `PT-BW-GE`'s own number. Because the pad TOPS
hold, `column_base`'s embedment (grade to pad top) does not move and
`entry_column_base_fixity.md` §6e's claim is undisturbed.

**`pier_basis` reads the tributaries close to this line now**: 17.0 ft² of deck and 40.0 ft²
of roof on `PT-BW-W` plus the 98 lb of wall above, for D 1,628 + L 3,629 = 5,257 lb service
and 7,760 lb factored against the 8,014 hand-worked here. The gap is the deck share — 17.0 against this line's 18.4 — and
it is bookkeeping in a load case nowhere near governing. It used to read 47.7 ft² of roof,
7.7 ft² of which was the garage landing counted a second time as a "rafter field"; that
duplicate went on 2026-09-18 (`pier_basis._rafter_fields` now skips a beam pair some
`FloorSystem` or `Roof` has already accounted for).

**`pier_basis` grades the roof at §3's 73.7 psf since 2026-09-18, not at the ground snow.**
It read 50 while `BM-BW-RE` eighteen inches overhead was designed at 73.7 — one roof, two
answers, the lighter underneath the heavier. The axial d/c moves from 0.027 to about 0.032
against a §22.4.2 cap of 2.859e5 lb, so **nothing near governing either way** on the shaft;
the cage below is what sizes it. Where the change does bite is bearing, §6's pad table
above, where `PD-BW-RE` goes from 0.85 to 0.94.

### Section and cage

| term | working | value |
|---|---|---|
| gross area | π (12/2)² | 113.10 in² |
| ACI 318-19 §10.6.1.1 floor | 0.01 A_g | 1.131 in² |
| provided | (4) #5 = 4 (0.31) | 1.24 in² → ρ = 1.096% |
| tie spacing | least of 16 d_b = 10.0", 48 d_t = 18.0", h = 12.0" | 10" |

**The 1% floor is why these bars are here, not the load.** It is a creep, shrinkage and
accidental-moment rule and is indifferent to a d/c of 0.03. Four bars is the Code's own
minimum for a circular tie (§10.7.3.1(b) — six is the spiral case). Do not thin it.

### Durability — why these are EXPOSED_MIX with galvanized bar

Recorded here 2026-09-11, because a reviewer reading this note could find the section, the
cage and the slenderness and nowhere find the exposure argument the cage costs money for.

**ACI 318-19 Table 19.3.1.1 class F3 + C2**, the same mix and the same coating as the
sunken-garden court. F3 is not in question: exterior concrete in Minnesota, in contact with
water, exposed to freeze-thaw, with deicing chemicals. **C2 is the class that was
questioned** — it wants "concrete exposed to moisture and an external source of chlorides"
— and the answer is that Table 19.3.1.1 names *spray* from deicing chemicals as such a
source. Five of these six shafts stand up to 18 1/2" out of the ground at the north entry,
which is shovelled and salted every winter and is the walk people arrive on. Occasional
splash at a column base is the condition the class describes; road-level exposure is not
the threshold.

**The galvanizing is an owner decision and is recorded as one, not as a code requirement.**
`plan/assemblies.py` is explicit about that, which is the right way round: C2 with a
5,000 psi / w/cm ≤ 0.40 / 6% air mix satisfies the Code without it, at the 2" cover these
cages carry. The coating is the margin on top, and since 2026-09-12 it is stated as a
**ladder** rather than as one product (BLD-02 finding 4; `notes/balcony_moment_columns.md`
§7 is the full statement):

- **Galvanized, either standard — preferred.** **ASTM A767**: galvanize AFTER fabrication
  (the class is a coating weight, not a bend order, so naming one never settled the
  sequence), A780 repair at any field cut or bend, and a welded cage leaves A767 for A123 —
  **AZZ Winsted** and **AZZ NE Minneapolis** are the two local plants. Or **ASTM A1094**:
  coated stock that bends after coating without repair, published by **CMC GalvaBar** as
  stocked. ACI 318-19 §20.2.1.7.2 lists both; ψ_e = 1.0 either way. **The fabricator names
  the route on the order.**
- **Black bar at this cover and mix — a written exception only**, when neither route can be
  supplied on schedule.
- **Epoxy and stainless — refused.** Epoxy's ψ_e of 1.2-1.5 would lengthen every lap here by
  half (galvanized bar reads ψ_e = 1.0, §25.4.2.5); stainless was considered for this house
  and rejected.

**These six cages are the same part as the court's six.** `ENTRY_PIER_CAGE` and the court's
`_CAST_COLUMN_CAGE` are one cross-section — 8.0" out-to-out of ties, (4) #5, #3 rings @ 10",
2" cover — so the house orders **one fabricated cage, twelve off**, lengths per pour, tied
not welded. Not the catalog stock 8" cage, which is (4) #4 at #3 @ 12": under §10.6.1.1's
1% floor and over §25.7.2.1's 16d_b.

The court's own chloride reasoning is worked in `params/sunken_garden.py` and is a
different argument reaching the same class: salt arrives there on boots and a shovel and
then **cannot leave**, because a sunken court with no outlet to daylight concentrates it
rather than shedding it. Neither argument depends on the other.

`prices.toml`'s two column rows point here, and the galvanized cage premium is priced on
both of them — it was missing from the pier row until 2026-09-11.

### Slenderness

| term | working | value |
|---|---|---|
| unbraced length | footing top −8'-11 7/16" to pier top −1'-3 1/2" | 92 in |
| radius of gyration | 0.25 d = 0.25 (12) | 3.00 in |
| k·l_u/r | 1.0 (92) / 3.00 | 30.7 |
| §6.2.5 non-sway floor | 34 − 12(M1/M2), ≥ 22 | 22 |

**30.7 exceeds 22, so it is computed rather than neglected.** P_c = π²EI/(k l_u)² ≈ 1,190 kip
against a factored 7.8 kip gives δ_ns ≈ 1.01, and e_min stays under §R22.4.2's 0.10h.

### Footing

> ### 2026-09-14 — three of these six left this note's scope, and the other three did not
>
> `PD-BW-W`, `PD-BW-E` and `PD-BW-RE` — the HOUSE-side three — are `Pad`s now, graded
> prescriptively by `structural.deck_footing_size` against IRC Table R507.3.1. Their
> `spread_footing/` items have left the engineering register, and **§6's bearing arithmetic
> no longer oracles anything for them**: what governs is a table lookup a reviewer can open.
> Their axial, slenderness, cage and durability sections above are untouched — `deck_post`
> still grades all six.
>
> What made the conversion possible is that the check learned the ROOF.
> `checks/structural/deck.py::_roof_borne_posts` converts a post's roof-footprint share into
> R507.3.1's own deck currency —
> `(DECK_DEAD_LOAD_PSF + Site.ground_snow_load_psf) / DECK_TOTAL_LOAD_PSF`, 1.2 on this site —
> so the canopy's snow arrives at the table as 48 ft² of equivalent area per column rather
> than being dropped. **That had to be built first because of `PT-BW-RE`**, which carries
> `BM-BW-RE` and no deck at all: it was in no deck's post list, so it was not graded at
> zero — it was not graded, and its only coverage was the `spread_footing/` item its Footing
> raised. Deleting that Footing without the roof pass would have removed an item and put
> nothing in its place.
>
> **`PT-BW-GW`, `-GE` and `-RNE` stay `Footing` and stay engineered**, and the reason is the
> garage strip footing, not the load. They bear at -7'-0", on `FT-GF-S1`/`-S3`'s own plane,
> and lap about 7 1/2" into it. A `Pad` is an ISOLATED pour by definition —
> `structural.concrete_interference` scopes every one of them and only a wall-less `Footing` —
> so calling these Pads asserts a pour that stands clear of something it is cast against.
> They cannot be pulled clear either: the pier line is 4 1/2" south of that footing's face
> and the shaft is a 12" round, so the COLUMN overhangs any pad stopping at the face. One
> pour is the truth, `Footing.under` is how the model says it, and three
> `spread_footing/` items are the price. **That is an open item, not an oversight.**
>
> The pads themselves are 2'-6" x 1'-6" x 1'-0" — a rectangle, not the 2'-0" square below.
> `FT-B-N1`..`-N4`, the basement's north strip footing, sits on the same -9'-9 7/16" plane
> and reaches y = 36'-8 1/8"; a 24" square centred on the pier line reached 2 1/8" into it.
> That lap was there while these were Footings and was invisible, because
> `concrete_interference` did not scope them. 18" north-south clears it by 1 1/16" and 30"
> east-west takes the area to **3.75 ft²**, against 2.48 ft² required for `PT-BW-W` on the
> mn-2020 profile's 1,500 psf. One size for all three: three pad sizes are three rows in
> S-100's FOUNDATION SCHEDULE, and that sheet is one row from its schedule governing its
> height again.

| term | working | value |
|---|---|---|
| service load | §6 above | 4,404 lb |
| presumptive bearing | IBC Table 1806.2, sand/silt/clay, taken at | 2,000 psf |
| required area | 4,404 / 2,000 | 2.20 ft² |
| provided | 2'-0" square | **4.00 ft²** |

The engine reads 0.81 here rather than the 0.55 this line arithmetic gives, because
`pier_basis` credits `PT-BW-W` a larger deck share than the round number above once it walks
the beam chain (0.90 against 0.51 before the 2026-09-11 narrowing). **0.81 is the tightest
bearing ratio in this structure** and it is the first number to revisit if a boring log comes
back under 2,000 psf. The retired `PR-BW-*` pads were 1.78 ft² against a 1,240 lb load; they
do not cover any of this, which is why 2'-0" is authored on five of the six.

### 2026-09-17 — the four moment-pier pads are 12" deep (owner)

`PD-BW-E`, `-RE` (were 10") and `PD-BW-GE`, `-RNE` (were 8") are **1'-0"**. `PD-BW-W` (10") and
`PD-BW-GW` (8") carry no dowels and are unchanged. Plan sizes are unchanged.

**Why.** Each moment pier's four #5 base dowels are laid as an L whose 90° foot rests at the
pad's 3" bottom cover, so embedment = thickness − 3". ACI 318-19 §25.4.3.1(a), f_y 60,000,
f'c 5,000 (√ = 70.71), λ 1.0, ψ_e 1.0 (galvanized), ψ_r 1.0 (bars ≥ 6 d_b apart), ψ_o 1.0,
ψ_c = 5,000/15,000 + 0.6 = 0.933:

| term | working | value |
|---|---|---|
| ℓ_dh | 60,000 × 0.933 / (55 × 1.0 × 70.71) × 0.625^1.5 = 14.40 × 0.4941 | **7.11"** |
| §25.4.3.1 floors | max(8 d_b = 5.00", 6") | 6.00" — ℓ_dh governs |
| embedment, 10" / 8" pad | 10 − 3 / 8 − 3 | 7.00" / 5.00" — **short** |
| embedment, 12" pad | 12 − 3 | **9.00"** (ℓ_dh / have = 0.79) |

**The tops stay; the bottoms go down.** House side: top −8'-11 7/16", bottom −9'-9 7/16" →
**−9'-11 7/16"**. Garage side: top −6'-4" (flush with the strip), bottom −7'-0" → **−7'-4"**.
Raising the tops instead was rejected on three counts: `PR-G-HYDRANT-CW` crosses over
`PD-BW-E` in plan (x = 11'-0" inside 9'-4" .. 11'-10") at −8'-10", 1 7/16" above today's top, so
a −8'-9 7/16" top would swallow it (why `FOOTING_DEPTH_FT` was 10" to begin with); a garage pad
would stand 4" proud of the strip it is cast monolithic with; and every shaft height — the §8
lever arms, the cage lengths — would move. Kept this way, column heights (91.9 / 184.2 / 60.5 / 152.8 in) and §8 are untouched.

Consequences, all benign: frost cover rises 2" (85.4" house side) and 4" (54" at −2'-10"
grade, garage side) against 42"; the house-side two now step 2" below `FT-B-N1..N4`'s plane
1 1/16" away in plan, which the existing open-excavation sequencing already covers (pour the
pads with or before that strip); the garage two are a 4" local deepening under their
monolithic lap; the hydrant passes 1'-6" under `PD-BW-GE` (was 1'-10") and still 1 7/16" over `PD-BW-E`. `PT-BW-RNE`'s
embedment below grade (§8d) is 4'-6", was 4'-2". Added concrete 0.123 cy
(2 × 3.75 × 2/12 + 2.25 × 4/12 + 4.00 × 4/12 = 3.33 ft³).

**Bearing** — re-worked 2026-09-18 on two changes that pull opposite ways, and the table
below is the second version. The first is the DESIGN SNOW: the canopy's roof share was
graded at `Site.ground_snow_load_psf` (50) while `BM-BW-RE` directly overhead was designed
at `preferences.toml [structural] roof_beam_snow_psf` (73.7, the §7.7 roof-step drift), so
40 ft² of canopy carried 2,000 lb of snow at the pier and 2,948 lb at the beam eighteen
inches above it. The pier reads 73.7 now. The second is NET bearing: a presumptive allowable
is a pressure over and above the overburden already there, so the soil the pad displaced is
credited at 110 pcf, the low end of the 110–130 band (`engineering/soil.displaced_soil_
credit_lb`). Against the mn-2020 profile's 1,500 psf:

| pad | area | D + L column | pad wt (12") | less displaced soil | net pressure | ratio |
|---|---|---|---|---|---|---|
| `PD-BW-E` | 3.75 ft² | 1,073 + 681 = 1,754 lb | 563 lb | −413 lb | 508 psf | 0.34 |
| `PD-BW-W` | 3.75 ft² | 1,529 + 3,629 = 5,158 lb | 563 lb | −413 lb | 1,394 psf | 0.93 |
| `PD-BW-GE` | 2.25 ft² | 764 + 681 = 1,445 lb | 338 lb | −248 lb | 682 psf | 0.45 |
| `PD-BW-GW` | 4.00 ft² | 1,221 + 3,629 = 4,850 lb | 600 lb | −440 lb | 1,225 psf | 0.82 |
| `PD-BW-RE` | 3.75 ft² | 2,208 + 2,948 = 5,156 lb | 563 lb | −413 lb | 1,415 psf | **0.94** |
| `PD-BW-RNE` | 4.00 ft² | 1,900 + 2,948 = 4,848 lb | 600 lb | −440 lb | 1,252 psf | 0.83 |

`D` includes each shaft's own 150 pcf over its full height (903 lb on the house-side pair,
594 garage-side, 1,808 on `PT-BW-RE`, 1,500 on `PT-BW-RNE`); `L` is 17.0 ft² of deck at 40
psf plus 40.0 ft² of canopy at 73.7 wherever the canopy reaches. The west canopy half
arrives at `PT-BW-W` / `PT-BW-GW` two posts down, through `PT-BW-CW` / `-CNW`.

**`PD-BW-RE` is the tightest pad in the house at 0.94, and the margin is real but thin.**
Gross and at the ground snow it read 0.85, which is what the 2026-09-17 version of this
table said; gross and at the design snow it is **1.02**, i.e. over. The 6% it passes by is
the displaced-soil credit and nothing else, so anything that adds load here — a heavier
canopy covering, a drift case worse than 73.7, a pad poured shallower than 12" — takes it
over. The S-100 FOUNDATION SCHEDULE holds all three house-side pads at one size
(30" × 18" × 12"), so the closure if it ever goes over is to widen all three together.

**Uplift and overturning improve** by the added pad weight: +94 lb under E/RE, +113 under GE,
+200 under RNE — at 0.6D, +56 lb on `PT-BW-RE` and +120 lb on `PT-BW-RNE` against the ~230 lb
net column uplift `params/north_entry_frame.py` states, and the same weight over half the pad
width as extra resisting moment. None of this is claimed as fixity (§8d stands). The
displaced-soil credit is deliberately NOT taken against uplift: it is a credit on a bearing
demand, and the soil is not there to be lifted.

**Engine agreement**, and it is checked rather than asserted. `structural.deck_footing_size`
now carries the pad's and the shaft's weight into the demand as equivalent R507.3.1 tributary
and nets the same displaced soil, so the ratios above are the check's own — `PD-BW-RE` reads
3.54 ft² required against 3.75 provided, which is this table's 0.94. `deck_post`'s records
move with the snow: `L` rose 2,000 → 2,948 lb on `PT-BW-RE` / `-RNE`, which stales any seal
pinned to them and correctly so. `integrity.reinforcement_layout`'s four anchorage FAILs
(7.00" / 5.00" against 7.11") are gone.

## 7. What is NOT graded here

- **Adfreeze jacking.** A 12" shaft through this parcel's 42" frost depth (Minn. R.
  1303.1600 Zone II — the 60" figure is northern Minnesota, a different zone) is gripped
  over about 11 ft². At even 10 psi of adfreeze that is well past the ~5,300 lb of service
  load holding it down. Resistance comes from the 2'-0" pad with nine feet of soil over it,
  which is almost certainly enough — but **it is a calculation nobody has done**, and
  `structural.frost_depth` does not do it: that rule grades cover, not uplift. The cheap
  mitigation is a polyethylene bond breaker or slip sleeve over the frost depth.
- **Negative skin friction** on nine feet of shaft in settling house backfill. `pier_basis`
  has no term for it, and on a 12" shaft it can exceed the roof load outright.
- **The leaning-column `k = 1.0` assumption**, which is weaker here than it was for the
  retired breezeway piers: this shaft has no reliable lateral restraint over most of its
  length.
- **Drift on a gable lower roof** — see §3. §7.7 assumes a flat-ish lower roof.
- **Bearing and connections at the header ends**, and lateral-torsional stability of the
  headers (C_L is taken as 1.0 on the strength of continuous deck sheathing).
- ~~**The canopy's lateral system as a separate plane.** It has none.~~ **Withdrawn
  2026-09-10 and re-worked below.** The canopy braces itself: two fixed cast columns east,
  a sheathed panel west, and the garage joint demoted to a tie
  (`notes/north_entry_structure.md` §1a). §8 is the hand pass for the east pair. What
  remains ungraded is not the system but four of its assumptions, and all four are in
  §8d. A `KBS1Z` knee brace at each column stays the cheap fallback and is a live,
  rated, priced row in this house — `pier_basis.knee_braced` is scoped per structure since
  2026-09-11, so authoring one here no longer silences the balcony's moment grading.
- **The soil bearing value itself.** 2,000 psf is presumptive, not measured; no boring log
  exists for this site. `PT-BW-W` at d/c 0.90 is what feels a lower number first.
- **The four cast terrace tiers, `SL-BW-TIER1..4`.** They are plain concrete on a compacted
  base, not frost-founded, and no calculation here covers them. Each is one riser thick and
  fully bedded on the tier below, so there is no span to grade; what is ungraded is
  **movement**, and the owner has accepted it knowingly. See
  `notes/north_entry_structure.md` §3 for what a winter costs and which joint pays.
- ~~**The truss-to-header tie CAPACITY**, for the reason §4a gives: the stainless H2.5ASS's
  published allowables could not be sourced.~~ **Closed 2026-09-11** — L-F-SSNAILS rates a
  stainless connector at its carbon twin's values, so the tie is 700/110/110 against 256 lb.
  What is ungraded now is narrower and is a SPECIFICATION risk rather than a capacity one:
  that parity is conditional on SSA8D ring-shank nails, and no check in this engine can see
  which nail was driven. See §4a.

## 8. The canopy's east columns in BENDING (oracles `roof_moment.roof_base_moments`)

**Written 2026-09-11, by hand from the authored geometry.** `PT-BW-RE` and `PT-BW-RNE` are
the canopy's east lateral system (`notes/north_entry_structure.md` §1a). Until this date
the engine graded them **axially only** — every path into its moment machinery was gated on
`FloorSystem.service == "deck"`, and a canopy column carries a roof header — so both records
read `SCREENING: axial only, no moment and no lateral case.` while the house's own guide
asserted they published a real d/c. §1a's sentence was wrong and is corrected there.

### 8a. Why the engine does not work §27.3.2

The provision that literally governs is ASCE 7-16 §27.3.2, a pitched free roof, and its
`C_N` comes out of **Fig. 27.3-4** — a copyrighted grid this repository does not hold, the
same problem `typehaus/wind_tables.py` records for Fig. 29.3-1. §1a works it by hand off
the standard. The engine will not transcribe, interpolate or curve-fit it.

So the engine takes a **bound** instead, the move `MAX_VERIFIED_CASE_AB` already exists for:
the roof's own vertical projection, the headers and the shafts are treated as a **solid
sign** at `C_f = 1.80`, the largest coefficient Fig. 29.3-1's Cases A and B are known to
reach. That bounds the real answer twice over — a thin inclined plate open on every side is
a far less obstructive body than a solid sign, and every published free-roof `C_N` is
smaller in magnitude than 1.80. §8c puts a number on how much.

### 8b. The engine's arithmetic, hand-worked

Geometry, off the resolved roof (`RF-BW-CANOPY`, gable, ridge north-south, 4:12):

| term | working | value |
|---|---|---|
| footprint | 26'-8" east-west x 6'-0" north-south, overhangs included | |
| eave / ridge | resolved | +7.951' / +12.396' |
| rise | 13.333' x 4/12 | 4.444' |
| q_h datum | `balcony_wind.ground_below_ft`, the site's LOWEST spot | -9.12' |
| z | 12.396 + 9.12 | 21.52' |
| q_h | ASCE 7-16 Sec 26.10, V_ult 115, Exp B, RC II | 18.335 psf |
| ASD pressure | 0.6 x 18.335 x 0.85 (G) x 1.80 (C_f) | **16.831 psf** |

> **The q_h datum is the sunken garden court, half a house away and nine feet down, and
> that is deliberate over-reading rather than a bug.** `ground_below_ft` takes the whole
> site's minimum spot elevation. Against the canopy's own grade at -2'-10" it makes `z`
> 21.5' instead of 10.8' and `q_h` 18.3 psf instead of about 16.4 — **12% conservative**, in
> the one direction a demand may err. Exposed SHAFT length does not use it: that reads
> `Site.grade`, because "how much column stands in the wind" has no safe direction.

Solid bands, per plan direction:

| direction | band | depth x length | area |
|---|---|---|---|
| E-W (across the ridge) | slope rise | 4.444' x 6.000' | 26.67 ft2 |
| | `BM-BW-RE` + `BM-BW-RW` | 11 1/4" x 5.719' x2 | 10.72 ft2 |
| | **top total** | | **37.39 ft2** |
| N-S (along the ridge) | gable-end triangle | (4.444'/2) x 26.667' | 59.26 ft2 |
| | headers | run along the wind, present their ends | 0 |
| | **top total** | | **59.26 ft2** |
| both | shaft drag, 2 x 12" round | 1.000' x 10.785' x2 | 21.57 ft2 |

The leeward slope is **not** counted: it stands in the windward slope's own shadow, and
projecting the same rise twice onto one plane would be double counting. The exposed shaft
length is the eave at +7.951' down to `Site.grade` at -2.833' = 10.785', an over-read of
the 9'-2 3/4" actually standing out of the ground.

Shears and moments:

```
N-S governs:  top    16.831 x 59.26  =   997 lb ASD
              drag   16.831 x 21.57  =   363 lb ASD
                                  frame = 1,360 lb ASD
(E-W for comparison: 16.831 x 37.39 = 629 + 363 = 992 lb ASD)
```

**All of it on the two cast columns, and nothing claimed for the west panel.** `W-BW-SCREEN`
is a sheathed 2x4 shear panel and is the west lateral system in fact. Splitting between it
and a 12" cast column is a relative-rigidity judgement this engine has no standing to make,
so it makes none and takes the whole frame shear east. Same reasoning as the guard load in
`notes/balcony_moment_columns.md` §2c, which is loaded wholly onto one column rather than
halved.

**Two shears, two lever arms.** The roof and the headers deliver at the roof plane; drag on
a shaft resolves at the mid-height of its exposed length. The lever is the **full shaft**,
footing top to header soffit — "fixed at the base" taken literally — not the exposed length
§1a measures against.

| | `PT-BW-RE` | `PT-BW-RNE` |
|---|---|---|
| shaft height | 15.349' | 12.729' |
| drag arm = h - 10.785/2 | 9.957' | 7.337' |
| roof: 498.7 lb x h | 7,654 lb-ft | 6,348 lb-ft |
| drag: 181.5 lb x arm | 1,807 lb-ft | 1,332 lb-ft |
| **M_w, ASD** | **9,461 lb-ft** | **7,680 lb-ft** |
| M_u = M_w / 0.6 (Sec 2.3.1's 1.0W) | 15,769 lb-ft | 12,799 lb-ft |
| phi*M_n at this column's Pu | 24,939 lb-ft | ~24,900 lb-ft |
| d/c before magnification | 0.63 | 0.51 |
| delta (k 2.1, k*lu/r 129 / 107) | 1.117 | 1.070 |
| **d/c magnified** | **0.71** | **0.55** |

`phi*M_n` is the same section arithmetic as `notes/balcony_moment_columns.md` §4 — 12" round,
(4) #5, 2" cover, 5,000 psi — at a slightly higher `P_u`, which is why it reads 24,939
rather than that note's 24,703. **No size change and no richer cage**: the ACI Sec 10.6.1.1
minimum these carry is still what sizes them.

### 8b-i. The §2.3.1 envelope — added 2026-09-18, and it moved the governing case

The table above takes ONE axial load, `1.2D + 1.6L` = 7,367 lb, finds the P-M point there,
and compares the wind moment against it. **A larger axial is not automatically conservative
on an interaction curve.** Below the balance point — where every column in this house sits,
at 2-3% of `P_n,max` — compression *raises* moment capacity, so grading the full wind moment
at the heaviest gravity case credits the column with compression the windstorm does not
bring. ASCE 7-16 §2.3.1's five combinations, each at its own `P_u` and its own P-M point,
for `PT-BW-RE`:

| §2.3.1 | P_u | M_u (magnified) | phi*M_n | d/c |
|---|---|---|---|---|
| 1.4D | 3,092 lb | 0 | 24,217 lb-ft | 0.00 |
| 1.2D + 1.6L + 0.5S | 4,124 lb | 0 | 24,487 lb-ft | 0.00 |
| 1.2D + 1.6S + 0.5W | 7,367 lb | 8,995 lb-ft | 25,335 lb-ft | 0.36 |
| **1.2D + 1.0W + L + 0.5S** | **4,124 lb** | **16,940 lb-ft** | **24,487 lb-ft** | **0.69** |
| 0.9D + 1.0W | 1,987 lb | 16,313 lb-ft | 23,927 lb-ft | **0.68** |

`D` is 2,208 lb (roof dead + the shaft's own 1,808 lb at 150 pcf), `L` is 0 — this column
carries no deck — and `S` is 40.0 ft² × 73.7 psf = 2,948 lb.

**The last two rows are the point.** Combination 4 governs at 0.69 and combination 5 is one
point behind it at 0.68, with barely half the axial load; the old single-axial reading gave
0.71 at 7,367 lb by crediting `1.2D + 1.6L`'s compression against the wind case's moment.
The numbers are close here because this column is so lightly loaded that the interaction
curve is nearly flat — which is the reason the correction costs nothing on catlin and the
reason it must be in the arithmetic anyway. On a column carrying real gravity load the two
readings diverge, and they diverge in the unconservative direction.

Wind and the guard load are taken CONCURRENTLY in combination 4, which is conservative and
free here (this column has no guard on it at all). The guard's 200 lb is an occupancy live
load and rides the `L` term.

### 8c. How much conservatism is in that 0.71

§1a's §27.3.2 hand pass, restated: `Gq_h` 13.94 psf, clear wind flow Case A at theta 18.44
(`C_NW` +1.10, `C_NL` -0.17), so `C_NW - C_NL` = 1.27 on the 24 ft2 projected area gives
**425 lb** of roof thrust at strength, plus column drag near 365 lb, for **790 lb strength
= 474 lb ASD** across the whole frame, east-west.

| | frame shear, ASD |
|---|---|
| Sec 27.3.2 hand pass, E-W (the governing case there) | 474 lb |
| engine surrogate, E-W (same direction) | 992 lb — **2.1x** |
| engine surrogate, N-S (the case it grades) | 1,360 lb — **2.9x** |

Three separate over-reads compose to it: `C_f` 1.80 against `C_NW - C_NL` 1.27 (1.42x),
`q_h` at the court datum (1.12x), and the gable-end triangle, which §27.3.2 barely loads at
all because wind along a free roof's ridge does not press on a projection that has no
windward face. **A column at d/c 0.71 on this basis is comfortably inside any legitimate
reading of Fig. 27.3-4**, which is the whole claim the bound is making.

It is also why the reviewer's wood alternate does not come back: the trigger written into
`plans/` was a canopy moment check returning OVER or wanting a cage richer than the ACI
minimum, and neither fires.

### 8d. Still the engineer of record's, and now named in the record

- **The fixed-base assumption itself.** `PT-BW-RNE` has 4'-6" of embedment below grade
  against roughly 5'-6" that IBC 1807.3.2.1's non-constrained formula wants for this moment
  in presumptive sand, and the 2'-0" pad's contribution is not in that formula at all.
  Nothing in the engine grades embedment; the record's `SCREENING:` note says so in those
  words since 2026-09-11.
- **Slenderness as a SWAY column.** `k*lu/r` is 129 on the full shaft at k 2.1 (107 on
  `PT-BW-RNE`), against Sec 6.2.5's sway limit of 22. It is computed rather than neglected
  and the magnifier is small because `P_u` is 2% of capacity — but §6's non-sway reading of
  30.7 was taken for a different question and does not cover this one.
- ~~**The joint at the top.**~~ ~~**Torsion and column shear.**~~ **Computed since
  2026-09-20 — §9** (`column_head_joint/*`, all ten lateral-system columns).

## 9. The column head joint (oracles `engineering/column_head_joint.py`)

**Written 2026-09-20, by hand, before the module.** Ten columns: the six `PT-BW-*` here and
the four balcony corners `PT-SG-B{R,F}{1,3}` (`notes/balcony_moment_columns.md`). Upstream
numbers are quoted from the notes that oracle them and are not re-derived: the canopy's
diaphragm split (`entry_column_base_fixity.md` §7), the deck storey shears (`pier_basis`,
this note §6 and the balcony note §2), q_h (§8b). Section: 12" round, 5,000 psi, (4) #5,
#3 ties @ 10", normalweight (λ = 1).

### 9a. Head moment — the adopted model asks for none

`deck_post` sways every one of these at `k = 2.1`: ACI 318-19 Table R6.2.5's fixed-base,
free-top cantilever (theory 2.0, 2.1 for real fixity). A free top is a head with no
rotational restraint, so the analysis the columns are graded on asks the joint for **no
moment**. Graded as a detailing row, `2.0 / 2.1 = 0.952`: it goes over the day somebody
adopts `k < 2.0`, which would be a claim that the head restrains rotation, and that claim
would have to be paid for here.

**One residue, named.** `deck_post` charges a guard column's base with 200 lb × (H + guard
height). The guard's own lever above the deck is a couple a pinned head cannot pass; it
comes back down through the deck's bearings as an axial pair. The base envelope stays the
conservative bound; that axial pair is not graded (a few hundred pounds against columns at
2-3% of axial capacity).

### 9b. Lateral through the connector

The joint's demand is the force the beam hands the head. Deck columns: the per-column storey
shear, or IRC R301.5's 200 lb guard. Canopy columns: each column's share of the diaphragm's
shear (`lateral_system.column_head_reactions`), **not netted** against the column's own drag
reaction pushing the other way.

Capacity (2026-09-21): a cast-in **HETA20Z pair**, FL11473 Table 3, double HETA in
concrete on a 2- or 3-ply member, SP: F1 1,350 / F2 1,430 lb for the PAIR — the lower,
**1,350 lb**, so no sign of the load needs knowing. It is the set's value, credited once
(`HeadConnector.set_rated`). Note 1: already +60% for wind. So a WIND demand is graded
against 1,350, and a GUARD demand (occupancy live, NDS Table 2.3.2 C_D = 1.0) against
**1,350 / 1.6 = 843.75 lb**. (The HGAM10 pair this replaced graded at 460 / 287.5, ratios
0.893 and 0.696 — `notes/column_head_connector_options.md` says why it left.)

| column | wind, ASD | vs 1,350 | guard | vs 843.75 |
|---|---|---|---|---|
| `PT-BW-RE` / `-RNE` | 0.5 × 821.31 = **410.66** (E-W) | **0.304** | — | — |
| `PT-BW-E` / `-GE` | 311 / 4 = 77.75 | 0.058 | 200 | **0.237** |
| `PT-SG-B*` | 615 / 4 = 153.75 | 0.114 | 200 | **0.237** |
| `PT-BW-W` / `-GW` | 77.75 | — | 200 | — |

The balcony glulam is Table 3's "2- or 3-ply" row by WIDTH (3-1/2"), not ply count. Read as
1-ply, Table 2's single 340 lb governs: guard 200 / (340 / 1.6) = **0.941**, still inside.

`PT-BW-W`/`-GW` have no HETA pair: their head is the `ABU66SS` under the 6x6 canopy column, and
the seat beam hangs off that 6x6 (`params/breezeway.py`). ESR-1622 Table 2 publishes uplift
and download only. **No lateral capacity is published for that joint, so those two records
are INCOMPLETE naming it** — an ACI 318 Ch. 17 anchor-shear design of the base's bolt, or a
different tie.

**Combined loading — graded since 2026-09-21.** FL11473-R4 §9 (Limitations) item 4 is the
report's own rule for every product in it, the embedded truss anchors of Tables 2 and 3
included: `(Design Uplift / Allowable Uplift) + (Lateral Parallel / Allowable) + (Lateral
Perpendicular / Allowable) < 1.0`. It was missed in the footnotes because it sits in the
Limitations. The canopy columns: `433.3 / 2,560 + 410.66 / 1,350 = 0.169 + 0.304 = 0.473`
— the pair's uplift is the set's, so it is not halved, and the lateral is taken at the lower
of F1/F2 so its direction need not be known. (The retired HGAM10 pair read 1.263 here.)
The report's alternate (each direction <= 0.75 x its allowable) also holds: 0.169, 0.304.

### 9c. Uplift — 0.6D + 0.6W, canopy columns only

The engine's §8 surrogate, spent on the plan area: `0.6 × 18.335 × 0.85 × 1.80 = 16.832 psf`.
Per column, 40.0 ft² of roof (half of 80.0): `16.832 × 40 = 673.3 lb` up, `0.6 × 10 × 40 =
240 lb` down, **net 433.3 lb**. Against the HETA20Z pair's 2,560 (the set's value, once):
**0.169**. `PT-BW-W`/`-GW` carry the same roof through their 6x6 and ABU66SS: 433.3 / 2,190
= **0.198**. (§4's 272 lb used C_N ≈ 1.3; the bound here is 1.80.)

The deck-only columns carry no roof (tributary 0, computed), and ASCE 7-16 assigns an
open-jointed walking surface no uplift coefficient: no uplift row, a note instead.

### 9d. Column shear — ACI 318-19 §22.5.5.1 with §22.5.2.2

Circular: `b_w = D = 12"`, `d = 0.8D = 9.6"`. Table 22.5.5.1(a), N_u taken as zero
(compression would only add): `V_c = 2 × 70.711 × 12 × 9.6 = 16,292 lb`, **φV_c = 12,219 lb**.
(a) needs `A_v ≥ A_v,min`: a circular tie counts twice (§22.5.10.5.3), `A_v = 0.22 in²`;
`A_v,min = max(0.75 × 70.711 × 12 × 10 / 60,000, 50 × 12 × 10 / 60,000) = 0.1061 in²` —
detailing row **0.482**.

Demand, strength level: canopy `496.17 / 0.6 = 827.0 lb` (**0.068**); guard columns
`max(wind/0.6, 1.6 × 200) = 320 lb` (**0.026**).

### 9e. Torsion — §22.7.4.1, and the headline that was wrong

`T_th = λ√f'c (A_cp² / p_cp)`: `A_cp = 113.097 in²`, `p_cp = 37.699 in`, `A²/p = 339.29 in³`,
`T_th = 23,992 lb-in = 1,999.3 lb-ft`, **φT_th = 0.75 × 1,999.3 = 1,499.5 lb-ft**.

> ⚠ **The 2026-09-20 plan put φT_th at 124 lb-ft.** That is 1,499.5 / 12 — lb-in read as
> lb-ft, a factor of twelve. It also took a VERTICAL reaction at a seat eccentricity as the
> torque, and that makes BENDING about a horizontal axis, not torsion about the column's.
> Torque needs a HORIZONTAL force off the axis in plan.

The lever: the force enters where the tie's parts are, never inside the beam — each face of
the beam (± half its width) and each authored tie position is an entry point, and the bound
is `|r × F| ≤ F × lever`. For a force of known direction, `lever = |r ⊥ F|`; a guard or deck
force is taken in any direction, `lever = |r|`.

| column | F_u | lever | T_u | / φT_th |
|---|---|---|---|---|
| `PT-BW-RE` / `-RNE` | N-S along the header, 142.27 / 0.6 = 237.1 lb (E-W has lever 0: every entry point is on y = 0) | 2.25" | **44.5 lb-ft** | **0.030** |
| `PT-SG-B*` | 320 lb | 1.75" | 46.7 lb-ft | 0.031 |
| `PT-BW-E` / `-GE` / `-W` / `-GW` | 320 lb | 1.50" | 40.0 lb-ft | 0.027 |

(`PT-BW-RE`'s y force: 0.11962 × 1,189.41 = 142.27 lb ASD.) Every column is **under 1/30 of
threshold**; §9.6.4's closed hoops are not owed and the #3 ties' geometry is not tested.

Seat eccentricity is still printed, as the bending it is: the pack (3.5" square, centred on
the column) ∩ the beam's footprint. Where the beam ENDS at the column centre (`PT-BW-E/-GE/
-W/-GW`, `PT-BW-RE`) the intersection's centroid sits **0.875"** off; where it runs through
(`PT-BW-RNE`, `PT-SG-B*`) it is 0. `PT-BW-RE`: `5,196.8 × 0.875 / 12 = 378.9 lb-ft`.

### 9f. Bearing at the seat — §22.8.3.2

`A_1` = the pack, 3.5 × 3.5 = 12.25 in². `A_2` must be concentric and similar: the largest
square about the pack's centre inside the 6" circle, half-side `6/√2 = 4.243"`, `A_2 = 72.0
in²` (not the circle's 113.1). `√(72.0 / 12.25) = 2.42`, capped at **2**.
`φB_n = 0.65 × 0.85 × 5,000 × 12.25 × 2 = 67,681 lb`.

`P_u = 1.2 (D − shaft self-weight) + 1.6 (L or S)`:

| column | D − self | L/S | P_u | / 67,681 |
|---|---|---|---|---|
| `PT-BW-RE` / `-RNE` | 2,351 − 1,951 = 400 | 2,948 | 5,196.8 | **0.077** |
| `PT-BW-W` / `-GW` | 725 | 3,629 | 6,676.4 | **0.099** |
| `PT-BW-E` / `-GE` | 170 | 681 | 1,293.6 | 0.019 |
| `PT-SG-B*` | 483 | 1,933 | 3,672.4 | 0.054 |

Wood crushing on the pack (NDS F_c⊥) is a different member's question and is not graded.

### 9g. Verdicts

Eight columns OK; the connector is no longer near governing (canopy lateral 0.304, the
rest 0.237 on the guard at C_D 1.0).
`PT-BW-W`/`-GW` INCOMPLETE on the unpublished lateral. Scope: SCREENING.

> ⚠ **WITHDRAWN 2026-09-21 for the four landing piers** (`PT-BW-W`/`-E`/`-GW`/`-GE`): the
> landing is tied to the garage stem (§10), its piers lean, and they are no longer lateral
> columns, so they have no head joint to grade. The rows above for them are history. The
> canopy columns and the balcony corners are unchanged — but read §10f first.

## 10. The landing's two tie lines (oracles `engineering/deck_tie.py`, `deck_tie_anchor.py`)

**Written 2026-09-21, by hand, before the module; reworked twice the same day.** The landing
is tied so its four piers stop being the lateral system. Two tie lines: over the garage stem
under each carrier, and on the screen's own line into `W-G-W`, wood to wood. Passes:
HGAM10 on the stem alone, OVER 1.82 (§10g); HL33HDG on both lines, all wet, OVER 1.177 (§10g);
**this one, the owner's decision of 2026-09-21: HL35HDG at the stem, still wet; HL33HDG at
`W-G-W` graded DRY, with a 4x filler.** The wood side closes (0.99). **The stem anchors do
not (1.13, §10e).**

### 10a. The parts

Simpson C-C-2024 p. 303, the HL table (read from the dealer excerpt, 2026-09-21):

| row | ga | W1/W2 | L | D1 | D2 | D3 | bolts | DF/SP uplift | F1 |
|---|---|---|---|---|---|---|---|---:|---:|
| HL33 | 7 | 3-1/4 | 2-1/2 | 1-1/4 | — | 2 | 2 x 1/2" | 740 | 1,040 |
| HL35 | 7 | 3-1/4 | 5 | 1-1/4 | 2-1/2 | 2 | 4 x 1/2" | 740 | 1,310 |

At C_D 1.6, HDG to order. Fn 3: centred on a member face at least as wide as the angle.
Fn 4: members >= 3-1/2" thick. Fn 6: loads are for one connector; uplift may be doubled for
two; **lateral may not be doubled**. Fn 7: a lag of equal diameter >= 5" may replace the bolt
in the carried member. Wood-to-wood only; nothing published on concrete.

**Reading the two directions** (unchanged). F1 is along the heel; uplift is perpendicular
to it in one leg's plane. The legs are equal and identically bolted, so perpendicular to the
heel in the OTHER leg's plane is the uplift case mirrored — read at 740, flagged a reading.

**Service, per joint** (NDS 2018 §11.3.3, Table 11.3.3: C_M 0.70 for dowel-type fasteners
only where in-service MC > 19%). Authored on the parts (`Connector.service`), not by tag.
- **Stem: WET, C_M 0.70.** Over a pour, under an open-jointed deck.
  HL35: F1 917, uplift 518 lb.
- **`W-G-W`: DRY, C_M 1.0 — a service-condition judgement the engineer of record
  confirms.** Vertical faces under `RF-BW-CANOPY`, behind the screen, reached only by
  windblown moisture. The NDS Commentary (C4.1.4) is quoted as calling members "protected
  from the weather by roofs … but occasionally subjected to windblown moisture, such as for
  covered porches … generally considered dry" — **secondhand**; the primary was not read.
  HL33: F1 1,040, uplift 740 lb.

**Line 1, the stem (x = 7.125 / 9.4583', y = 43.6771').** Each carrier's KDAT 4x tie block
grows to 3-1/2" x 3-1/2" x **5" N-S** (the HL35's length; fn 3), still 1/4" off the concrete.
A pair of HL35HDG, one each block face, heel N-S; two 1/2" bolts through the block. The
concrete leg's holes are D2 = 2-1/2" apart, **under ESR-2713's s_min of 3"**, so **one** 1/2"
x 4" Titen HD per leg and the other hole EMPTY — a detail **for the engineer of record**.
Per joint, E-W (across the heel) = mirrored uplift, one part, **518**; N-S (along the heel)
= F1, one part, **917**.

**Line 2, `W-G-W` (x = 6.1979', y = 43.1458').** Two HL33HDG stacked on the screen's north
end post, east face, heel vertical, into the garage corner pack through the existing KDAT
filler. The end stud pack is two 2x4 plies, a **3" face** against the 3-1/4" leg (fn 3): a
**4x KDAT filler** (3-1/2" face, 26-1/2" long, both angles) joins the pack. The east face
does not move, so neither does the joint. N-S: uplift doubled for the pair, **1,480**; E-W:
uplift, one part, **740**.

### 10b. What the ties carry

Unchanged by this pass. ASD pressure on a solid face, the deck's C_f ceiling:
`0.6 × 16.539 × 0.85 × 1.80 = 15.183 psf`. The deck's own wind reads the landing's edge band
(§10f): 0.6875' over 3.5833' (N-S wind) and 6.5729' (E-W wind), plus the seat beams' faces.

| load | axis | lb | acts at (x, y) ft |
|---|---|---:|---|
| deck wind, E-W: 0.6875 × 6.5729 × 15.183 | x | **68.61** | (7.7917, 39.9323) |
| `W-BW-SCREEN` face, 6.5729' × 4.0833' | x | 407.50 | (6.0, 39.9323) |
| `W-BW-SCREEN-SKIRT` face, 6.5729' × 1.125' | x | 112.27 | (5.7656, 39.9323) |
| **E-W total** | | **588.38** | |
| deck wind, N-S: (2.4635 + 4.3299) × 15.183 | y | **103.14** | (7.7917, 39.9323) |
| `W-BW-SCREEN` share of `RF-BW-CANOPY` N-S | y | 980.74 | (6.0, 39.9323) |
| **N-S total** | | **1,083.88** | |
| guard, IRC R301.5, either end of the screen | any | 200 | (6.0, 36.6458) / (6.0, 43.2188) |

### 10c. Distribution — three joints

Joints and forces do not move (equal stiffness; the parts changed, the stations did not).
W (6.1979, 43.1458), FC (7.125, 43.6771), FE (9.4583, 43.6771); centroid (7.5938, 43.5000);
`J = 5.8329 ft²`. `X_i = Fx/3 − M dy_i/J`, `Y_i = Fy/3 + M dx_i/J`.

**N-S wind**, `M = −1,542.6 lb-ft`:

| joint | X | Y | along / cap + across / cap |
|---|---:|---:|---|
| W (wall runs y) | −93.67 | 730.45 | 730.45/1,480 + 93.67/740 = 0.494 + 0.127 = **0.620** |
| FC (wall runs x) | 46.83 | 485.27 | 46.83/518 + 485.27/917 = 0.090 + 0.529 = **0.620** |
| FE | 46.83 | −131.84 | 0.090 + 0.144 = 0.234 |

**E-W wind**, `M = +2,099.2 lb-ft`:

| joint | X | Y | ratio |
|---|---:|---:|---|
| W | 323.58 | −502.34 | 502.34/1,480 + 323.58/740 = 0.339 + 0.437 = 0.777 |
| FC | 132.40 | −168.70 | 0.256 + 0.184 = 0.440 |
| FE | 132.40 | 671.03 | 132.40/518 + 671.03/917 = 0.256 + 0.732 = **0.987** |

**Guard at C_D 1.0** (caps over 1.6), 200 lb E-W at the screen's south end,
`M = 1,370.8 lb-ft`: FE `X 25.05, Y 438.21` → 25.05/323.75 + 438.21/573.13 = 0.077 + 0.765 =
**0.842**; W `149.90, −328.05` → 328.05/925 + 149.90/462.5 = 0.355 + 0.324 = **0.679**.

### 10d. Verdict — the angles close at 0.99; the stem anchors are OVER at 1.13

| reading | N-S | E-W | guard | stem anchors |
|---|---:|---:|---:|---:|
| HL35 stem wet + HL33 `W-G-W` dry (graded) | 0.620 | **0.987** (FE) | 0.842 (FE) | **1.132** (FE) |
| superseded: HL33 everywhere, wet | 0.886 | 1.177 | 1.040 | 0.761 |

The wood side closes, with 1.3% at FE — HL35's F1 is the whole of the gain there, and the
dry call at W is what takes W off 1.11. **The concrete side opens**: one anchor per leg in a
hole 1-1/4" off the core centreline is 1.75" from a face, not 3.0" (§10e). **Nothing is
picked here**; `deck_tie/FS-BW-FLOOR` is OVER and stays suppressed as a numbered debt.

### 10e. The stem anchors — ACI 318-19 Ch. 17 (`deck_tie_anchor.py`)

ESR-2713 Tables 1A/2A/3, Titen HD 1/2" at h_nom 4": h_ef = l_e = 2.99", k_cr 17, N_sa 20,130,
V_sa 7,455, k_cp 2.0, c_min 1-3/4", s_min 3"; cracked, condition B. f'c 5,000
(`GARAGE_ICF_6`). **The layout.** The HL35 is centred on the 6" core, its 5" length across
it; the anchored hole is D1 = 1-1/4" from an end, so **1-1/4" off the centreline: c = 1.75"
to the near face (exactly c_min), 4.25" to the far.** Both anchors of a pair on the same side
(the conservative reading; staggering leaves one anchor at 1.75" whichever way the shear
goes). Between the pair's anchors along the stem, `s = 3.5 + 2 × 2 = 7.5"` (D3 each side).
The arms: bolts at D3 = 2" over the concrete; the SHORTER arm from the anchor to a leg end is
1-1/4" (the same as HL33's L/2); the toe arm 3-1/4 − 2 = 1-1/4".

```
N_b = 17 √5,000 × 2.99^1.5                                   = 6,215.0 lb
A_Nc = (1.75 + 4.25) × (4.485 + 7.5 + 4.485) = 6 × 16.47      = 98.82 in²   (A_Nco 80.46)
ψ_ed,N = 0.7 + 0.3 × 1.75 / 4.485                             = 0.8171      (was 0.9007)
V_b = min(7 (5.98)^0.2 √0.5 √5,000 1.75^1.5, 9 √5,000 1.75^1.5) = min(1,158.7, 1,473.3)
φV_cbg, toward the near face = 0.70 × (10.5 × 2.625 / 13.781) × 1,158.7 = 0.70 × 2.0 × 1,158.7
                                                              = 1,622.2 lb  (was 3,337.5)
along the stem (§17.7.2.1(c)): 2 × 1,622.2                    = 3,244.3 lb
```

Worst case, FE under E-W wind, strength = ASD / 0.6: along the heel (N-S, toward a face)
`671.03 / 0.6 = 1,118.4 lb`, across it `132.40 / 0.6 = 220.7 lb`.

```
per anchor from the heel force: 1,118.4 / 2 × 2 / 1.25       = 894.7 lb
one anchor from the pry:         220.7 × 2 / 1.25            = 353.1 lb
group tension N = 2 × 894.7 + 353.1                          = 2,142.5 lb
e'_N = 353.1 / 2,142.5 × 3.75 = 0.618"  ψ_ec,N = 0.8789
φN_cbg = 0.65 × 1.2282 × 0.8789 × 0.8171 × 6,215.0          = 3,562.9 lb   → 0.6013
shear: 1,118.4 / 1,622.2 + 220.7 / 3,244.3 = 0.6894 + 0.0680 = 0.7575
§17.8.3: (0.6013 + 0.7575) / 1.2                             = 1.132   OVER
```

Steel (1,248 / 13,085 tension, 570 / 4,473 shear) and pryout (1,140 / 8,731) are far below;
the guard case at FE reads 0.31 / 0.44 / 0.63. Edge 1.75 = c_min and spacing 7.5 >= 3 pass
as detailing. **It is the near-face breakout in shear that opens the joint**: halving c
takes φV_cbg from 3,338 to 1,622. The anchor layout is the engineer of record's detail, and
the numbers above are the case against leaving it as drawn. Not graded: the block's screws
into the carrier, the fillers' fastening, and `W-G-W` receiving 730 lb in its own plane.
Stem out-of-plane: the governing N-S force is still 671 lb, so the first pass's 0.66 bound
(at 1,675 lb) scales to ~0.26.

### 10f. What this pass closed that was outside the tie

- **FL11473 §9 item 4 is graded now on the canopy heads** (`column_head_joint`, §9b): the
  HETA20Z pair reads `433.3 / 2,560 + 410.66 / 1,350 = 0.169 + 0.304 = 0.473`. The 1.263
  was the retired HGAM10 pair's. The HETA20Z passes; no new head part is needed.
- **The landing's deck wind reads its own edge band** (`deck_tie_basis.deck_wind`): a fascia
  counts only where its path lies on the deck's sheet; otherwise the deck's joist + board edge
  (`balcony_wind.deck_edge_band`). E-W 110.08 → 68.61, N-S 310.56 → 103.14. The balcony
  still reads `TR-SG-FASCIA` (its own) and its base moments do not move.
- Still open, not this pass's: the deck's q_h is taken at the lowest spot elevation on the
  site (the sunken garden), 40' away — conservative, and `balcony_wind`'s rule for every deck.

### 10g. History — the superseded passes

**HL33HDG everywhere, wet (superseded the same day):** N-S 0.886, E-W 1.177 at FE, guard
1.040, stem anchors 0.761 (one Titen HD on the core centreline, c = 3.0"). The 2.5"-long
HL33's single hole sat on the centreline; the HL35's two do not.

**The first pass (HGAM10 on the stem alone).** Two HGAM10 pairs (FL11473-R4 Table 1, SPF/HF: F1 630, F2 460 away, 920 for the pair) on the
carriers only, 2'-4" apart: the screen's 981 lb landed 1'-1 1/2" west of the line and the
couple put 1,675 lb on `BM-BW-FC` — **1.82** N-S, 1.60 E-W, 1.30 guard. Simpson also bars the
HGAM's Titen Turbo screws from exterior exposure (C-C-2021 p. 252). Retired 2026-09-21.

## Sources

- ASCE 7-16 §7.3 (flat-roof snow), §7.7 and Fig. 7.7-1 (drifts on lower roofs), §7.7.1
  (adjacent structures), §29.4 (open buildings and other structures).
- AWC NDS 2018 §3.3 (bending), §3.4.2 (shear in a rectangular section), §4.3.8 (wet
  service), §4.3.9 (repetitive member), Table 2.3.2 (load duration); NDS Supplement
  Table 4B (southern pine visually graded design values).
- ACI 318-19 §6.2.5 (slenderness), §10.6.1.1 (minimum longitudinal steel), §10.7.3.1
  (minimum bar count), §22.4.2 (axial strength cap), §25.7.2 (ties), §R22.4.2 (minimum
  eccentricity).
- IRC R301.5 and Table R301.5 (deck live load, guard loads), Table R301.7 (deflection),
  R507.5.1 (beam cantilever), R507.6.1 (joist cantilever).
- IBC Table 1806.2 — presumptive load-bearing values of foundation materials.
- Minn. R. 1303.1600 — frost depth by zone; Zone II is named to include Ramsey County, this
  parcel's own (it names Hennepin too — the depth is the same 42" for both).
- `plans/north-gable-extension.md` — the 90–101 psf drift screen this note agrees with.
- Simpson Strong-Tie C-C-2024 p. 303, HL heavy angle table and fns 2-8 (excerpt:
  https://cdn.shopify.com/s/files/1/0398/5188/4705/files/HL_Heavy_Angle_and_Gusset.pdf); C-C-2019 p. 287 for the superseded row.
- ICC-ES ESR-2713 (Titen HD), rev. 2026-03, Tables 1A, 2A, 3 and §5.20:
  https://icc-es.org/wp-content/uploads/report-directory/ESR-2713.pdf
- Simpson FL11473-R4 §9 Limitations item 4:
  https://www.floridabuilding.org/upload/PR_Tech_Docs/FL11473_R4_AE_SIM201701%20Sealed%202017-10-19.pdf
- ACI 318-19 §17.6.2, §17.7.2, §17.7.3, §17.8; AWC NDS 2018 §11.3.3 and Table 11.3.3 (C_M),
  §11.3.6 (γ); NDS Commentary C4.1.4 (covered porches "generally considered dry" —
  secondhand, via a search excerpt of the commentary; not read from the primary).
