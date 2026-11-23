> Current white MDO screen: 35.65 plf, 156.74 lb to each west chord (§2a, 7/16" ZIP west face since 2026-11-18).

# North entry canopy, piers and headers — hand-worked basis

> **Current east pair, 2026-09-29:** `PT-BW-RE`/`-RNE` are 6x6 KDAT posts on 3'-0"
> piers with stainless standoff bases and drained PVC wraps. Their current wood check and
> the switchable steel/cast alternatives are in `canopy_garage_diaphragm.md` §5a. The
> full-height east-column passages below record the earlier cast design.
>
> **Headers, 2026-10-28:** `BM-BW-RW`/`-RE` are 5-1/2" x 11-7/8" glulam ending flush on
> their posts (no 8 7/8" tail); the header rows below are history. Current geometry and
> calcs: `canopy_west_band.md` 2026-10-28 amendment.

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
| house foundation face (2026-11-01, §13) | `W-B-N*` concrete face y=36'-0" + 0.06" membrane + 4" XPS | y = 36'-4 1/16" (436.06") |
| clear, 14" pier face to it (`PT-BW-W`, kdat `PT-BW-PE`) | 450" − 7" − 436.06" | **6.94"** |
| clear, 12" pier face to it (`PT-BW-E`) | 450" − 6" − 436.06" | 7.94" |
| clear, pier face to concrete, 14" / 12" | 450" − 7" (6") − 432" | 11" / 12" |
| garage plate top | `W-G-E`/`W-G-W` `z1` | +7'-4" |
| header top | = garage plate, so the two roof planes are one plane | +7'-4" |
| header soffit | +7'-4" − 11 1/4" | +6'-4 3/4" |
| bearing plane (seat soffits) | −0.94" − 7 1/4" − 7 1/4" (2026-10-15 stock) | −15.44" |
| pier tops, one 3/4" SS316 pack lower (2026-10-31, §12) | −15.44" − 0.75" | −16.19" |
| site grade | `params/foundations.py::SITE_GRADE` | −2'-10" |
| pier top above grade | 34" − 16.19" (2026-10-31) | 17.81" |
| footing underside | house footing underside | −9'-9 7/16" |
| footing thickness | authored | 10" (12" under the four moment piers, 2026-09-17) |
| roof column length | 76.125" + 16.19" (2026-10-31, 5 1/2" glulam soffit) | 92.315" |
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

### 2a. `W-BW-SCREEN`'s line load (oracles `resolve/assembly_weight.py`, `pier_basis.wall_line_loads`)

`BM-BW-SCSILL` is the sill under `W-BW-SCREEN`, hung (`LUS28Z`) off the two 6x6 KDAT canopy columns
`PT-BW-CW`/`-CNW`, which stand on `PT-BW-W` / `PT-BW-GW` through `supported_by`. A wall is neither a `FloorSystem`
nor a `Roof`, so its dead load is a plf times a run, never a tributary area. The screen is the guard, the closure
over the deck framing and a declared shear panel: WEST face 7/16" taped ZIP under `corrugated-panel-24` (the shear,
alone), 2x4 KDAT studs on axis 74.1875" (flush with the chords' west faces), EAST face white painted 3/4" MDO (finish only).
The MDO is three panels and stops at the north chord post (owner, 2026-11-14). The lower centre timber is one solid
KDAT 6x6, 5.5" x 5.5" x 44.44", with five 2x4 MDO nailers, 3.5" x 1.5" x 44.44" (`entry_screen_mdo.md`). The weight is derived from the assembly, never a constant; `checks/structural/guards.py`
reads the same plf (`engineering` may not import `checks`).

600 kg/m³ = 37.457 pcf; wall height 48.94" = 4.0783'; a framed layer at the engine's 0.23 field factor; 1 kg/m² =
0.20482 psf.

| layer | working | psf | plf (x 4.0783') |
|---|---|---:|---:|
| 2x4 KDAT studs | 3.5/12 x 37.457 x 0.23 | 2.513 | 10.25 |
| 7/16" ZIP (west), 650 kg/m³ = 40.578 pcf | 0.4375/12 x 40.578 | 1.479 | 6.03 |
| corrugated 24 ga | 5.2 kg/m² x 0.20482 | 1.065 | 4.34 |
| white 3/4" MDO, with timber, nailers, reserve | 2.341 + 3.227, over 55.5" of the 78.0" run, 45.5" high | 5.568 | 15.02 |
| **wall** | | | **35.65** |

```
MDO sheet     0.75/12 x 37.457 = 2.341 psf
accessories   timber 5.5 x 5.5 x 44.44 = 1,344.3 in³ + five nailers 5 x 1.5 x 3.5 x 44.44 = 1,166.6 in³
              = 2,510.9 in³ x 37.457/1,728 = 54.43 lb;  reserve 2 + 8 x 0.02 (end nails) = 2.16 lb;  56.59 lb
              over the net panel (7.25 + 24.125 + 24.125) x 45.5 = 55.5 x 45.5 = 17.536 sf -> 3.227 psf
MDO row       5.568 x 45.5/12 x 55.5/78.0 = 5.568 x 3.7917 x 0.7115 = 15.02 plf
```

`SB-BW-BAND` stands on the screen's top plate: two 2x6 plates, the centre 6x6 post and two corner-to-corner 6x6
diagonals cut 35.0058", 2 x 54.25 x 1.5 x 5.5 + 25.125 x 5.5² + 2 x 35.0058 x 5.5² = 3,773.0 in³ = 2.1835 ft³ x
37.457 = 81.79 lb over its own 4.5208': **18.09 plf**. The line is 35.65 + 18.09 = **53.74 plf**. The sill is
54.25" = 4.5208' between the chords; the panel runs 78.0" (6.5', its south end 1" off the house cladding since
2026-11-18, clear of D-M-ENTRY's casing), 23.75" = 1.9792' past it, where only the panel runs (the band stops on
the sill):

```
on the sill   53.74 x 4.5208 = 242.9 lb          past the sill   35.65 x 1.9792 = 70.6 lb
total 313.5 lb  ->  156.74 lb to each west chord, `PT-BW-CW` / `-CNW`, and down to `PT-BW-W` / `-GW`
```

`checks/structural/deck.py` divides the same pounds by R507.3.1's 50 psf: 156.74 / 50 = 3.13 ft² per pier. The screen
has no roof-support role; its local member, connection and plate checks are `entry_screen_mdo.md`'s.

## 3. The design snow — ASCE 7-16 §7.7 roof-step drift **(READ THIS ONE)**

The house's north face is a gable end standing 6 1/2" south of the passage roof, rising
from +20'-2 1/4" at the corners to +29'-2 1/4" at the ridge — **13 to 22 feet above
the canopy's eave** at +7.200' (half a foot more since the standard-heel trusses, 2026-10-08,
and 3.27" more since the heel is read at the outside face of bearing, 2026-10-31:
20.1875 − 7.200 = 12.99', 29.1875 − 7.200 = 21.99').
That is a roof-step drift condition and it governs. The clear height h_c is many times the
2.45' drift, so h_d is set by l_u alone and the drop moved none of the numbers below.

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

**Corrected 2026-11-23 (review C-9, decision 20).** The canopy has **three** truss stations per header, not four, and
they are not equal: the widest (T2, 2.0') has 2.0 x 13.333 = 26.67 sf. The order SPECIFIES **450 lb of net uplift per
heel** (`Roof.specified_reactions`); the table is `canopy_truss_criteria.md` §1.

| term | working | value |
|---|---|---|
| bearings per header | 3 truss stations (T1 1.115', T2 2.0', T3 1.974' tributary) | 3 |
| gross wind uplift, widest truss | 21.3 psf x 26.67 sf | 568 lb |
| 0.6W, no dead relief | 0.6 (568) | **341 lb** |
| 0.6W - 0.6D | 0.6 (568 - 10 x 26.67) | 181 lb |
| specified | covers the gross 0.6W + 32% | **450 lb** |

Six authored `H2.5ASS`, one per bearing (three on each header) — stainless because these land on treated southern
pine at an entry salted every winter, and the house buys stainless at every KDAT joint. 450 / 700 = 0.64.

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
> So the H2.5ASS is a **700 / 110 / 110** part here, and `library/hardware/` records it,
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
> ⚠ **THE NAIL IS A SPECIFICATION ITEM, ON THE ORDER AND S-001 (2026-11-23).** That 700 lbf is conditional on **SSA8D**
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

> **Superseded for these two headers on 2026-09-30.** They are 5-1/2" x 11-7/8" glulam now,
> for the AC/ACE caps and the band brace, and `canopy_west_band.md` §7 is their hand pass
> (bearing on the post governs, 0.355). This section stays as the oracle for a SAWN built-up
> roof beam, which is still the rule `roof_beam` applies to an `N-2xM` section.

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
> load is in the demand now (§2's wall table above, 1.95 ft² of equivalent R507.3.1
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
| deck tributary | 23.5 ft² of landing / 2 seat lines | 11.8 ft² |
| wall line load | `W-BW-SCREEN` + `SB-BW-BAND` on `BM-BW-SCSILL`, half | 281 lb |
| roof live | 40.0 × **73.7** psf (§3's design snow) | 2,948 lb |
| deck live | 11.8 × 40 psf | 470 lb |
| dead | (40.0 + 11.8) × 10 psf + 1,188 lb self weight + carried + wall | 1,884 lb |
| service | | **5,302 lb** |
| factored | 1.2 D + 1.6 L | **7,729 lb** |

(2026-10-13: the garage's interior landing, 13.2 ft², retired with the inswing door, and the
two carriers that brought it to the seats with it: 18.4 → 11.8 ft², service 5,456 → 5,124,
factored 8,021 → 7,515.)

**The wall line load** (the screen and its band on `BM-BW-SCSILL`, half to each west chord and its pier) is
worked in §2a.

> ⚠ **WITHDRAWN 2026-09-21 as a DEMAND, kept as built.** With the landing tied to the garage (§10)
> the four landing piers lean: `deck_post` grades them "axial, tied column" (d/c 0.007-0.027)
> and the dowel-anchorage row below no longer exists for them. The 12" pads stay in
> `_MOMENT_PIERS` — they cost nothing now and are what a reversal would need.

**Closing it uncovered a real FAIL, and that was the point.** Both piers left
`deck_post._detailing_only`'s six load-independent states for `_moment_column`'s twelve, and
the twelfth is dowel ANCHORAGE into the base — ACI 318-19 §25.4.3.1's ℓ_dh, 7.115" for a #5.
`PT-BW-GW` had an 8" pad giving 5.375" and **no base dowels at all**: d/c 1.32. It was never
the wall load (105 lb then, 1.3% of factored axial; 283 lb with the veneer and the panel's
ends, 3.7%). `_MOMENT_PIERS` had covered the landing's
EAST column and not its west, while `pier_basis._base_moments` split the lateral case "over
4 fixed column(s)" and `structural.lateral_racking` named all four — so the west pair carried
its twins' base moment with nothing detailed to deliver it, and nobody saw it because their
records were detailing-only. The west pair joined `_MOMENT_PIERS` in the same commit: 12"
pads, **tops unchanged**, bottoms down 2" (`PT-BW-W`) and 4" (`PT-BW-GW`) — 0.073 cy and 8
more #5 dowels — and both land at **0.759**, `PT-BW-GE`'s own number. Because the pad TOPS
hold, `column_base`'s embedment (grade to pad top) does not move and
`entry_column_base_fixity.md` §6e's claim is undisturbed.

**`pier_basis` reads the same roof and wall as this line, and half its deck** (re-read
2026-10-13): 5.50 ft² of deck and 40.0 ft² of roof on `PT-BW-W` plus the 283 lb of wall above,
for D 2,023 + L 3,168 = 5,191 lb service and 7,497 lb factored, against the 7,729 hand-worked
here. The 5.50 is the house seat's strip, `0.792' cantilever + 4.979' / 2 = 3.281'`, over the
seat's 3.3542' and split between its two piers; `PT-BW-GW`/`-GE` read the garage seat's
`4.979' / 2 + 0.604' = 3.094'` the same way, 5.19 ft². Each pier carried 3.91 ft² more (9.41 /
9.10) until 2026-10-13, the interior landing arriving on the seats through `BM-BW-FC`/`-FE`:
`3.91 × (1.2 × 10 + 1.6 × 40) = 297 lb` factored off all four. The gap is the deck share. `deck_post_tributaries` splits each seat beam's strip between
the TWO piers under it, and the table above puts a whole seat line (18.4 ft²) on one, so the
hand row is the conservative end by about that half. It is bookkeeping in a load case nowhere
near governing (axial d/c 0.02). It used to read 47.7 ft² of roof,
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

The 12" rounds (`PT-BW-E`, `-GE`) below; the 14" rounds are §13.

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

**These six cages are the same part as the court's four.** `ENTRY_PIER_CAGE` and the court's
`_CAST_COLUMN_CAGE` are one cross-section — 8.0" out-to-out of ties, (4) #5, #3 rings @ 10",
2" cover — so the house orders **one fabricated cage, ten off**, lengths per pour, tied
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

**The engine reads 8.375" (d/c 0.850) since 2026-09-23**: 12 − 3 − 0.625, one bar diameter
more conservative than this table. Until then `deck_post` took the COLUMN cage's 2" cover for
the pad's bottom cover and read 9.375" (0.759) — 3/8" of concrete under the foot that the
pad's 3" does not leave. `test_north_entry_piers.py` pins the pad's own cover.

**ψ_r = 1.0 is earned by SPACING, and that is why these cages stay at 2" cover** (owner asked
for 3", 2026-09-23). The four dowels lap one bar inside the verticals, 3.80" apart at 2" cover
against Table 25.4.3.2's 6 d_b = 3.75". At 2 1/2" they are 3.09" apart and at 3" 2.39", so
ψ_r = 1.6 and ℓ_dh = 11.38" against the 9.00" above — `integrity.reinforcement_layout` FAILs
all six pads. Back to 3" needs 15" pads or hook ties through the pad
(`balcony_moment_columns.md` §14c).

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

### 6c. 2026-11-22 — footing piers, graded prescriptively (decision 16; review C-11, D4)

All six piers are PINNED. The four landing piers are propped at the head by the tied landing
(§10); `PT-BW-PE`/`-PNE` stand free under the pinned east posts. Tops at −1'-4 3/16"
(landing) and +0'-2" (PE/PNE) against grade −2'-10": exposed 1.48' (h/d 1.27 on 14", 1.48 on
12") and 3.00' (2.57 on 14"), all <= 3. IRC R507.3 / Figure R507.3 draw a concrete pier from
the footing to the bearing and state NO height; the <= 3 cap is the ACI 318-19 plain-concrete
pedestal definition (§2.3, §14.3.3.1) used as a conservative proxy, not an IRC rule. Below
grade the shaft is soil-embedded. Each is the deck's R507.3 footing, not an R507.4 post: pad by `structural.deck_footing_size`, depth by
`structural.frost_depth` (`engineering/footing_pier.py`). The eight items `deck_post/PT-BW-*`
(6) and `column_base/PT-BW-PE`/`-PNE` leave the register.

**PE/PNE as short poles — IBC 2018 §1807.3.2.1, Eq. 18-1** (non-constrained: no rigid floor
at grade, no diaphragm above). Load canopy_garage_diaphragm.md §2/§6, the post's drag on its
7 1/2" PVC jacket (2026-11-23, verifier): post half-drag 16.661 x 7.5/12 x 6.1771 / 2 = 32.16 +
pier drag 58.31 = **P 90.47 lb ASD**; M at grade 32.16 x 3.0 + 58.31 x 1.5 = 183.95 lb-ft,
**h 2.033'** above grade. b = 14" = 1.1667'; S1 = 150 psf/ft
x d/3 (Table 1806.2 class 4, GM, presumptive); no §1806.3.4 doubling; the pad is NOT credited
— embedment is the shaft only, grade to pad top.

    d = 2.59': S1 = 150 x 2.59/3 = 129.5 psf; A = 2.34 x 90.47 / (129.5 x 1.1667) = 1.401
    d = 0.5 x 1.401 x (1 + sqrt(1 + 4.36 x 2.033 / 1.401)) = 0.7006 x 3.707 = 2.597 -> 2.59'
    PE : shaft grade -2.833' to pad top -8.953' = 6.12'   d/c 2.59/6.12 = 0.42
    PNE: shaft grade -2.833' to pad top -6.333' = 3.50'   d/c 2.59/3.50 = 0.74

Graded in `structural.column_base` (`checks/structural/deck_piers.py`), PRESCRIPTIVE.
**Bond breaker:** the top 42" of all six shafts are wrapped (two layers 6-mil poly, or a slip
sleeve), closing §7's adfreeze and skin-friction items by detail (AN-BW-STRUCTURE).

### 6d. 2026-11-22 — pull-out of the screen's chord piers (decision 15; review C-1)

`PD-BW-GW` and `PD-BW-RNE` are 2'-6" x 2'-6" x 12". The tension chord's pier must hold the
full-height overturning: T = 1,034.6 x 8.6825 / 4.979 + 426.5 (net roof uplift, 0.6D + 0.6W)
= **2,230.6 lb**, the hold-down row's own number. Held down at 0.6D by shaft + doweled pad +
soil on the pad's projection (110 pcf, the low end of the band) + post 57 + screen wall 157;
no deck or roof dead (the roof's 0.6D is already in T).

    GW: shaft 1.069 ft2 x 4.984' x 150 = 799; pad 6.25 x 1.0 x 150 = 937.5;
        soil (6.25 - 1.069) x 3.50' x 110 = 1,995;  sum 3,945.5 x 0.6 = 2,367  d/c 0.942
    W : shaft 1.069 x 7.604' x 150 = 1,219; pad 3.75 x 1.0 x 150 = 562.5;
        soil (3.75 - 1.069) x 6.12' x 110 = 1,805;  sum 3,800.5 x 0.6 = 2,280  d/c 0.978

Both pass and both sit past the 0.85 owner cost-review trigger (decision 30; limit 1.0).
Conservative on two counts not taken: the overturning arm runs to the chord bases, not the
landing that props them (to the sill, T = 1,540 + 426.5 = 1,966.5, W 0.86), and the landing
dead hung on the chord through the LUS26-2Z is not credited. Rows in `lateral_system/
RF-BW-CANOPY` (`engineering/lateral_band._pullout_rows`).

> **Superseded for N-S 2026-11-23 (§10p).** The MSTA49Z collector takes the screen's shear
> out at its top plate, so the chords' overturning never reaches their bases: the pull-out,
> pad-bearing, hold-down and base-shear rows are no longer graded (`_strapped_out`). The
> arithmetic above stays as the case the rows would grade without the strap; the pads stay
> as drawn (decision 15).

**The compression chord's pad (review C-6)**, ASCE 7-16 §2.4.1 D + 0.75(L+S) + 0.75(0.6W),
gross on the pad, no displaced-soil credit, against 2,000 psf (Table 1806.2 class 4):
overturning compression 1,034.6 x 8.6825 / 4.979 = 1,804.1 lb, x 0.75 = 1,353 lb. PD-BW-W
(3.75 ft2): D + pad + 0.75(L+S) = 4,804 lb (the pier's own record), total 6,157.5 lb =
**1,642 psf, d/c 0.82** (`_pad_bearing_rows`). The reviewer's independent 6,312 lb (1,683 psf,
0.84) differs by 0.75 x 205 = 154 lb, the drift gradient below.

**The drift gradient on the house-side supports (review C-5) — recorded, not modelled.**
`pier_basis` splits each 6-ft header by halves on the average surcharge. By statics the south
support takes L(2p_s + p_n)/6 = 110.5 psf-ft of surcharge against 95.1: **+205 lb (+6%)** on
PT-BW-RE/-CW, piers PE/W and pads PD-BW-RE/W; the north ones are 205 lb lighter. No verdict
moves: post axial 0.213 → 0.226, PD-BW-W D+S+L 1,546 psf, the C-6 row 0.84. A known, bounded
approximation; `pier_basis.landed_roof_tributaries` is the place to split it if a row ever
gets close.

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

> **§8 and §9 are the 2026-09-11 / -20 passes, before the canopy delivered to the garage and
> before the standard-heel trusses (2026-10-08) dropped the eave to +7.472' and the ridge to
> +11.917' (`q_h` 18.217 psf, 16.723 psf ASD), and before the heel moved to the outside face
> of bearing (2026-10-31: eave +7.200', ridge +11.644', `q_h` 18.149, 16.661 psf ASD, east
> columns at x 29.719').** The cast variant's current split, base moments and head forces are
> `canopy_garage_diaphragm.md`'s 2026-10-31 block.

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
shear (`lateral_system.column_head_reactions`) **with its torsional increment**
(`north_entry_canopy_lateral.md` §8h, a relief never credited), **not netted** against the
column's own drag reaction pushing the other way.

Capacity (2026-09-21): a cast-in **HETA20Z pair**, FL11473 Table 3, double HETA in
concrete on a 2- or 3-ply member, SP: F1 1,350 / F2 1,430 lb for the PAIR — the lower,
**1,350 lb**, so no sign of the load needs knowing. It is the set's value, credited once
(`HeadConnector.set_rated`). Note 1: already +60% for wind. So a WIND demand is graded
against 1,350, and a GUARD demand (occupancy live, NDS Table 2.3.2 C_D = 1.0) against
**1,350 / 1.6 = 843.75 lb**. (The HGAM10 pair this replaced graded at 460 / 287.5, ratios
0.893 and 0.696 — `notes/column_head_connector_options.md` says why it left.)

| column | wind, ASD | vs 1,350 | guard | vs 843.75 |
|---|---|---|---|---|
| `PT-BW-RE` / `-RNE` | 0.5 × 821.31 = **410.66** / +0.40 torsion = 411.06 (E-W) | **0.304** | — | — |
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
(`-RNE` 411.06: 0.4737)
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

Demand, strength level: canopy `496.17 / 0.6 = 827.0 lb` (`-RNE` 496.58 / 0.6 = 827.6, both **0.068**); guard columns
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
| `PT-BW-RE` / `-RNE` | N-S along the header, 342.52 / 0.6 = 570.9 lb (E-W has lever 0: every entry point is on y = 0) | 2.25" | **107.0 lb-ft** | **0.071** |
| `PT-SG-B*` | 320 lb | 1.75" | 46.7 lb-ft | 0.031 |
| `PT-BW-E` / `-GE` / `-W` / `-GW` | 320 lb | 1.50" | 40.0 lb-ft | 0.027 |

(`PT-BW-RE`'s y force: 0.11962 × 1,189.41 = 142.27 lb direct + 200.31 lb torsion =
342.52 lb ASD, `north_entry_canopy_lateral.md` §8g; the k/Σk-only 142.27 read 44.5 lb-ft.)
Every column is **under 1/14 of threshold**; §9.6.4's closed hoops are not owed and the #3 ties' geometry is not tested.

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

The landing is tied to the garage so its four piers stop being the lateral system. There are two joints, both
wood to wood, both on y = 43.1458' (the garage cladding face): **W** on the screen's end stud pack into `W-G-W`, and
**FE** on `BM-BW-FE` into `W-G-S`. No joint lands on concrete (§10e is the anchor module's oracle only). Every row
passes: **E-W wind at W governs at 0.786**.

### 10a. The parts

Simpson C-C-2024 p. 303, the HL table, at C_D 1.6, HDG to order:

| row | ga | W1/W2 | L | D1 | D2 | D3 | bolts | DF/SP uplift | F1 |
|---|---|---|---|---|---|---|---|---:|---:|
| HL33 | 7 | 3-1/4 | 2-1/2 | 1-1/4 | — | 2 | 2 x 1/2" | 740 | 1,040 |
| HL35 | 7 | 3-1/4 | 5 | 1-1/4 | 2-1/2 | 2 | 4 x 1/2" | 740 | 1,310 |
| HL43 | 3 | 4-1/4 | 3 | 1-1/2 | — | 2-3/4 | 2 x 3/4" | 1,275 | 1,445 |

Fn 3: centred on a member face at least as wide as the angle. Fn 4: members >= 3-1/2" thick. Fn 5 (HL43): wood
members of the "4" series >= 5-1/8" thick. Fn 6: loads are for one connector; uplift may be doubled for two;
**lateral may not be doubled**. Fn 7: a lag of equal diameter >= 5" may replace the bolt in the carried member.
Wood to wood only; nothing is published on concrete.

**Reading the two directions.** F1 is along the heel; uplift is perpendicular to it in one leg's plane. The legs are
equal and identically bolted, so perpendicular to the heel in the OTHER leg's plane is the uplift case mirrored,
read at the uplift value and flagged a reading. **The angle's plane runs with the member**: a vertical heel's wood
leg lies on the tied member's side face. For the screen (runs y, ties into `W-G-W`, which runs y) that plane is
ALONG the wall; for FE (runs y, ties into `W-G-S`, which runs x) it is ACROSS the wall.

**Service, per joint** (NDS 2018 §11.3.3, Table 11.3.3: C_M 0.70 for dowel-type fasteners where in-service MC >
19%), authored on the parts (`Connector.service`), not by tag:

- **FE: WET, C_M 0.70.** HL43: uplift 1,275 x 0.70 = 892.5 lb; the pair in the member's leg plane 1,785 lb.
- **`W-G-W`: DRY, C_M 1.0, a service-condition judgement the engineer of record confirms.** Vertical faces under
  `RF-BW-CANOPY`, behind the screen, reached only by windblown moisture. The NDS Commentary (C4.1.4) is quoted as
  calling members "protected from the weather by roofs ... but occasionally subjected to windblown moisture, such as
  for covered porches ... generally considered dry" (**secondhand**; the primary was not read). HL33: uplift 740 lb,
  the pair in plane 1,480 lb.

### 10b. What the ties carry

ASD pressure on a solid face, the deck's C_f ceiling. **The wall faces take q at the screen's own height**: its top
is +4'-0", 13.1' over the site's lowest ground (-9.12'), under the Exposure B table floor of 15', so
K_z = 2.01 (15/1200)^(2/7) = 0.5747 and

```
q = 0.00256 x 0.5747 x 0.85 x 115² = 16.54 psf        p = 0.6 x 16.54 x 0.85 x 1.80 = 15.183 psf
```

This is deliberately not the canopy roof's 16.661 psf (q_h 18.149 at the ridge, `canopy_garage_diaphragm.md` §2):
the two stand at different heights, and nobody should unify them. The deck's own wind reads the landing's edge band
(a fascia counts only where its path lies on the deck's sheet; otherwise the joist and board edge,
`balcony_wind.deck_edge_band`), with the deck's q taken at the lowest spot elevation on the site, 40' away:
conservative, and the rule for every deck. Geometry: §10i (edge band), §10k (landing, seat beams), §10n (joint x).
The deck's south edge stands at y 36'-7 7/8" since 2026-11-17 (3/8" off D-M-ENTRY's sill beam,
`exterior_door_sill_beam.md` §4): the E-W band is 6.4479' long, its centre 39.8802'.

| load | axis | lb | acts at (x, y) ft |
|---|---|---:|---|
| deck wind E-W: 0.6825' x 6.4479' x 15.183 | x | **66.82** | (7.9323, 39.8802) |
| `W-BW-SCREEN` face, 6.5' x 4.0783' x 15.183 | x | 402.49 | (6.19792, 39.8958) |
| `W-BW-SCREEN-SKIRT` face, 6.5' x 1.125' x 15.183 | x | 111.03 | (6.19792, 39.8958) |
| **E-W total** | | **580.33** | |
| deck wind N-S: (0.6825 x 3.3021 + 2 x 0.6042 x 3.0355) x 15.183 = (2.2537 + 3.6681) x 15.183 | y | **89.91** | (7.9323, -) |
| `W-BW-SCREEN` share of `RF-BW-CANOPY` N-S (canopy note §4, the whole delivered shear) | y | 1,034.49 | (6.19792, -) |
| **N-S total** | | **1,124.40** | |
| guard, IRC R301.5, 200 lb at the screen's south end (y 36.6458, 2026-11-18) | x | 200 | |

### 10c. Distribution — two joints

W (6.34375, 43.1458), FE (9.5833, 43.1458); centroid x 7.96354, dx = -/+1.61979, dy = 0,
`J = Σ(dx² + dy²) = 2 x 1.61979² = 5.24745 ft²`. `X_i = Fx/2` (E-W), `Y_i = Fy/2 + M dx_i/J` (N-S), M the couple of
the loads about the centroid.

```
N-S   ΣFy 1,124.40
      M = 1,034.49 (6.19792 - 7.96354) + 89.91 (7.9323 - 7.96354) = -1,829.3 lb-ft
      W:  562.20 + 1,829.3 x 1.61979/5.24745 = 562.20 + 564.68 = 1,126.9 lb  / 1,480 = 0.761
      FE: 562.20 - 564.68 = -2.5 lb,  2.5 / 1,785 = 0.001
E-W   ΣFx 580.33, X = 290.17 each
      M = 66.82 x (43.1458 - 39.8802) + 513.51 x (43.1458 - 39.8958) = 218.19 + 1,668.91 = 1,887.1 lb-ft
      Y = 1,887.1 x 1.61979/5.24745 = 582.5 lb
      W:  582.5/1,480 + 290.2/740     = 0.3936 + 0.3921 = 0.786
      FE: 290.17/892.5 + 582.5/1,785  = 0.3251 + 0.3263 = 0.651
guard at C_D 1.0 (caps / 1.6), 200 lb E-W at the south end: M = 200 x 6.5 = 1,300.0 lb-ft, X = 100,
      Y = 1,300.0 x 1.61979/5.24745 = 401.3 lb
      W:  401.3/925 + 100/462.5 = 0.4338 + 0.2162 = 0.650
      FE: 100/557.8 + 401.3/1,115.6 = 0.1793 + 0.3597 = 0.539
```

At W, Y acts along the wall (1,480) and X across it (740); at FE X acts along `W-G-S` (892.5) and Y across it (1,785).

### 10d. Verdict — every row passes; E-W wind at W governs at 0.786

| reading | N-S | E-W | guard |
|---|---:|---:|---:|
| W (2 x HL33HDG, dry) | 0.761 | **0.786** | 0.650 |
| FE (2 x HL43HDG, wet) | 0.001 | 0.651 | 0.539 |

Two things stay the engineer of record's to confirm: **W's dry service** (§10a), and FE's 3/4" bolt, which stands
2-3/4" (3.7D) off FE's end grain, under NDS Table 12.5.1A's 7D for full design value, with the wall leg's lag landing
in a two-ply jack/king pack.

### 10e. The stem anchors — ACI 318-19 Ch. 17 (`deck_tie_anchor.py`; no house joint uses it)

`deck_tie_anchor` stays oracled by this worked case, an HL35HDG pair on a 6" ICF stem core, one Titen HD per leg.
ESR-2713 Tables 1A/2A/3, Titen HD 1/2" at h_nom 4": h_ef = l_e = 2.99", k_cr 17, N_sa 20,130, V_sa 7,455, k_cp 2.0,
c_min 1-3/4", s_min 3"; cracked, condition B; f'c 5,000 (`GARAGE_ICF_6`). The angle sits 1-1/4" off the core
centre so the anchored hole (D1 = 1-1/4" from the leg end) lands ON the centreline, c = 3.0" to each face; between
the pair's anchors along the stem `s = 3.5 + 2 x 2 = 7.5"`.

```
N_b = 17 sqrt(5,000) x 2.99^1.5                                  = 6,215.0 lb
A_Nc = (3 + 3) x (4.485 + 7.5 + 4.485) = 6 x 16.47               = 98.82 in²   (A_Nco 80.46)
ψ_ed,N = 0.7 + 0.3 x 3 / 4.485                                   = 0.9007
V_b = min(7 (5.98)^0.2 sqrt(0.5) sqrt(5,000) 3^1.5, 9 sqrt(5,000) 3^1.5) = min(2,600.7, 3,306.8)
φV_cbg, toward a face = 0.70 x (16.5 x 4.5 / 40.5) x 2,600.7     = 3,337.6 lb
along the stem (§17.7.2.1(c)): 2 x 3,337.6                       = 6,675.1 lb
```

Demand 1,124.5 lb along the heel (toward a face) and 199.1 lb across it (strength level, ASD / 0.6):

```
per anchor from the heel force: 1,124.5 / 2 x 2 / 1.25          = 899.6 lb
one anchor from the pry:         199.1 x 2 / 1.25                = 318.6 lb
group tension N = 2 x 899.6 + 318.6                              = 2,117.9 lb
e'_N = 318.6 / 2,117.9 x 3.75 = 0.564"   ψ_ec,N = 1/(1 + 0.564/4.485) = 0.8883
φN_cbg = 0.65 x 1.2282 x 0.8883 x 0.9007 x 6,215.0               = 3,969.4 lb   -> 0.5336
shear: 1,124.5 / 3,337.6 + 199.1 / 6,675.1 = 0.3369 + 0.0298     = 0.3668
§17.8.3: (0.5336 + 0.3668) / 1.2                                 = 0.7503
```

Steel (1,218 / 13,085 tension, 571 / 4,473 shear) and pryout (1,142 / 9,625) are far below; edge 3.0" >= 1.75" and
spacing 7.5" >= 3" pass as detailing. An angle centred on the core instead leaves the anchor 1.75" off a face and
reads 1.132 (near-face breakout φV_cbg 1,622 lb), which is why the angle is set 1-1/4" over.

### 10f. What the tie takes out of the lateral system

The four landing piers `PT-BW-W`/`-E`/`-GW`/`-GE` lean on the garage through the two joints and are not a lateral
system. The deck's wind reads its own edge band: see §10b.

### 10h. The two joints as built

**FE.** `BM-BW-FE` (3-ply 2x8, 4-1/2") runs N-S and stops at the garage cladding; its tip ties into `W-G-S` over
`D-G-SERVICE`'s east jamb pack by a pair of **HL43HDG** on FE's east face, heel vertical, lagged through a KDAT filler
cut flush with the corrugated. The 3/4" bolt passes FE and the rim beside it, 6" of wood (fn 5). Joint at x 9.5833'.

**W.** Two **HL33HDG** stacked on the screen's north end post, east face, heel vertical, into the garage corner
pack through the existing KDAT filler. The end stud pack is two 2x4 plies, a 3" face against the 3-1/4" leg (fn 3),
so a **4x KDAT filler** (3-1/2" face, 26-1/2" long, both angles) joins the pack. Joint at x 6.34375' (§10n).

Loads are §10b's; the capacities §10a's. There are no anchor rows: nothing ties to concrete.

### 10i. The deck edge — actual Trex stock

Trex Enhance Basics is 0.94" actual: the deck edge is 7.25 + 0.94 = 8.19" = 0.6825', and the seat-beam faces are
7.25" = 0.6042'. The framing and the landing pier tops hold the 0'-0" walking surface; the screen sill follows. The
deck sheet stops 1/2" south of the garage cladding: y 36.604' -> 43.104', 6.500' long, centroid y 39.8542'.

### 10j. The screen's weight at the sill

See §2a: 156.74 lb to each west chord.

### 10k. The landing and its seat beams

The landing's west edge is the screen's column line (x 6.28125'): the deck is 39.625" = **3.3021'** wide. The seat
beams `BM-BW-HOUSE-SEAT`/`-GARAGE-SEAT` start 0.4495" east of the west columns' face (1/8" past the CBSTQ66Z-SDS2
strap's SDS heads), so each is 115 - 78.5745 = 36.4255" = **3.0355'** long. The screen's run is 78.0" = 6.5',
y 36.6458' -> 43.1458' (it ends on the garage cladding face; its south end moved 1/2" north on 2026-11-18).

### 10m. The screen's stud line; the cast variant's head joint

`W-BW-SCREEN`'s 2x4s stand flush with the 6x6 chords' west faces, axis 74.375" = **6.19792'**, so the CDX laps the
chords and both west planes are the garage's. `BM-BW-SCSILL` sits under it; posts, seats and deck do not move.

**The cast variant's head joint (§12e).** The N-S head force is the canopy note's §7 value, 333.76 lb (screen panel
at x 6.19792', x_r 11.9145'); connector 333.76/1,350 = 0.247. The engine reads 334.28 (0.16% over).

### 10n. Line 2's joint is on the stud face

Joint W seats on the end stud pack's east face, a half stud off the axis: 6.19792 + 1.75/12 = **6.34375'**. The
distribution and verdict are §10c-§10d.

### 10o. 2026-11-18 — the garage's 7/16" ZIP moves the column line 3/16" west

The column line is now x 6.265625' (`canopy_west_band.md` §10), so the screen axis is 74.1875" = **6.182292'** and
joint W is at 6.182292 + 1.75/12 = **6.328125'**. The landing is 115 - 75.1875 = 39.8125" = **3.317708'** wide, the
seat beams 115 - (75.1875 + 2.75 + 0.4495) = 36.6130" = **3.051083'** long, the deck centroid x 7.924479'. The
canopy's N-S delivered shear is 1,034.57 lb. Every E-W load and every y station are unchanged.

```
deck wind N-S  (0.6825 x 3.317708 + 2 x 0.604167 x 3.051083) x 15.183 = 5.951061 x 15.183 = 90.35 lb
joints         W 6.328125, FE 9.583333: centroid 7.955729, dx -/+1.627604, 2 dx = 3.255208'
N-S   ΣFy 1,124.92;  M = 1,034.57 (6.182292 - 7.955729) + 90.35 (7.924479 - 7.955729) = -1,837.6 lb-ft
      W:  562.46 + 1,837.6/3.255208 = 562.46 + 564.50 = 1,127.0 lb / 1,480        0.761
      FE: 562.46 - 564.50 = -2.0 lb                                              0.001
E-W   Y = 1,887.1 / 3.255208 = 579.7 lb
      W:  579.7/1,480 + 290.2/740 = 0.3917 + 0.3921                              0.784  (governs)
      FE: 290.17/892.5 + 579.7/1,785                                             0.650
guard Y = 1,300.0 / 3.255208 = 399.4 lb
      W:  399.4/925 + 100/462.5                                                  0.648
      FE: 100/557.8 + 399.4/1,115.6                                              0.537
```

§10b-§10n above are the 11-17 working; these rows supersede theirs.

### 10p. 2026-11-23 — G5: a strap, a DTT pair and an accepted HL43 reading (supersedes §10o's parts)

Owner (2026-11-23): the HL43 catalog values may be read for the as-installed direction; the
MSTA/DTT swap where it is better. Every part graded WET, C_M 0.70 (decision 17). Each part
carries only the direction it is published for, and each plan direction is shared among the
joints that carry it (`deck_tie.distribute`, basis 6).

| Joint | Part (C-C-2026) | Carries | Published (160) | Wet |
|---|---|---|---|---|
| W, `CN-BW-SCREEN-STRAP` | MSTA49Z, p. 290, 26 nails, half per member (note d), over ZIP (note b) | N-S tension | 2,020 | 1,414.0 |
| FE, `CN-BW-GSDTT-S/-N` | DTT2Z pair + 1/2" HDG rod, deck-to-house detail, holdown note h | N-S tension | 1,825 (1 1/2" row, ESR-2330) | 1,277.5 |
| FE, `CN-BW-GSTIE-LO/-HI` | HL43HDG, one per face, heel vertical, p. 315 F1 (fn 6: one per sense) | E-W only | 1,445 | 1,011.5 |

The opposite sense of each tension tie bears (the filler at the strap line; FE's tip).

```
joints  strap x 6.036458 (W face of the screen, over the ZIP), DTT rod x 9.718750, y 43.3125
        N-S joints: xr 7.877604, dx -/+1.841146, J = 2 x 1.841146^2 = 6.779637
        The screen share enters AT THE STRAP (x 6.036458), not mid-screen (verifier, 11-23);
        it is 1,051.72 lb with the east posts' drag on their 7 1/2" jackets.
N-S   ΣFy 1,142.07; M = 1,051.72 (6.036458 - 7.877604) + 90.35 (7.924479 - 7.877604) = -1,932.16 lb-ft
      strap: 571.04 + 1,932.16 x 1.841146 / 6.779637 = 1,095.8 lb / 1,414.0      0.775 (governs)
      DTT:   571.04 - 524.7 = 46.3 lb / 1,277.5                                 0.036
E-W   ΣFx 580.3 lb, all to the HL43: 580.3 / 1,011.5                    0.574 (owner reading)
      M 1,887.1 lb-ft: ±1,887.1 x 1.841146 / 6.779637 = ±512.5 lb N-S (strap 0.36, DTT 0.40)
guard 200 lb at the screen's south end: DTT 353.0 / (1,277.5 / 1.6)               0.442
```

`deck_tie/FS-BW-FLOOR` 0.784 → **0.775**, N-S at the strap. It stays in the register: the
demand is an elastic distribution with plan torsion, not a table read. Named on the record:
the HL43's E-W 0.574 is an OWNER-ACCEPTED reading OUTSIDE the published condition — the
figure's F1 bears along the grain, here the garage leg's lags bear across a vertical stud's
grain, and that bearing may be materially lower than the row. ESR-2330 §4.1 scopes the
DTT2 to dry interior service; the catalog sells it for deck lateral ties and it is graded wet.

**The screen's chords carry no N-S.** The canopy's screen share runs SB-BW-BAND → top plate →
MSTA49Z → W-G-W; `lateral_band._strapped_out` drops the chord overturning, base shear,
pull-out and pad rows (§6d) from `lateral_system/RF-BW-CANOPY`. Line 2's HL33HDG pair and tie block are retired. **Open detail:** the DTT's rod line
1 5/8" off FE's east face meets the D-G-SERVICE east jamb pack; the garage-side tie needs a
nailer or filler on the drawing, set before drywall.

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

## 12. 2026-10-31 — the pack is a solid; the four hangers re-picked (C3-E11..E14)

**12a. Pier tops (E13).** The SS316-SHIM-35 pack between a seat soffit and its pier had no
height: both were −15.44". The four landing piers are cast one pack low, **3/4"**, the one
house-wide `column_heads.STANDOFF_PACK_IN`:

| item | before | after |
|---|---:|---:|
| `PT-BW-W`/`-E` top | −15.44" | **−16.19"** (17.81" over grade) |
| `PT-BW-W`/`-E` shaft, from the −107.4375" pad top | 91.9975" | 91.2475" |
| `PT-BW-GW`/`-GE` shaft, from the −76.0" pad top | 60.56" | 59.81" |
| `PT-BW-CW`/`-CNW` post, pier top to the +76.125" soffit | 91.565" | 92.315" |
| pack at `-E`/`-GE` | 0" | 0.75" |
| pack at `-W`/`-GW`, under the LUS26-2Z's 18 ga seat (0.048") | 0" | 0.75 − 0.048 = 0.702" |
| CBSTQ66Z-SDS2 seat, `PT-BW-CW` bottom (+1.1046" standoff) | −14.335" | −15.085" |

Pads, bottoms and every pad top hold, so `column_base` embedment and the hydrant clearances
do not move. The shafts lose 3/4" of self weight: 14" round, π x 7² x 0.75 / 1,728 x 150 =
10.02 lb, less the 3/4" the 6x6 gains (7.87 x 0.0625 = 0.49 lb), x 1.2 = **11.44 lb**
factored off `PT-BW-W`/`-GW` (the engine: 7,468.6 → 7,457.1, −11.47); 12" round, 113.10 x 0.75
/ 1,728 x 150 x 1.2 = **8.84 lb** off `-E`/`-GE` (1,467.0 → 1,458.1). Axial d/c stays 0.02.
The west chord rows that read the longer post are `canopy_west_band.md`'s 10-31 amendment (2).
`W-BW-SCREEN-SKIRT` keeps its −14.44" bottom: 1 3/4" over the pier tops now, and the deck tie's
skirt band is unchanged.

**12b. Seat-beam hangers (E12): LUS26-2Z.** The seat beam's west end, service, at 50 psf (10 D +
40 L) over its 3.281' (house) / 3.094' (garage) strip, plus 5.658 plf of 2-2x8 (21.75 in² at
37.46 pcf), over the 3.0729' beam (§10k), plus `BM-BW-FE`'s share — its ~168 lb seat reaction
(0.875' of deck x 6.44' x 50 / 2 + 8.49 plf x 6.44 / 2) stands 0.1875' off the east pier:

```
house   (50 x 3.281 + 5.658) x 3.0729 / 2 = 169.71 x 1.53645 = 260.75 + 168.2 x 0.1875/3.0729
        = 260.75 + 10.26 = 271.0 lb
garage  (50 x 3.094 + 5.658) x 1.53645 = 246.38 + 10.26 = 256.6 lb
LUS26-2 (C-C-2026 p. 114, DBL 2x8 row, DF/SP): floor (100) 1,030 x C_M 0.70 (wet) = 721 lb
        271.0 / 721 = 0.376        uplift (160) 1,060 x 0.70 = 742 lb against no net uplift
```

The beam actually bears on the pack through the hanger's seat, so 0.376 is the hung reading.
**Backing.** The post's end grain is 1.1046" over the pier top, −15.085", which is **0.355"** over
the soffit. The LUS26-2's flange runs soffit to soffit + (4.875 − 0.048) = 4.827": 4.472" of it,
92.6%, is backed (the HU28-2Z before E13: 6.2375 − 1.1046 = 5.133", 82%). Hold point: all four
header nails above the post's end. The catalog does not dimension hole heights, and only the
bottom 3/8" is unbacked.

**12c. Sill hangers (E11): LUS28Z.** `BM-BW-SCSILL` is a single 2x8, 1.5"; the HU28-2Z seat was
3.125" (`structural.hanger_seat_fit` FAILs it by 1.625"). Each end carries §10j's wall line
**276.45 lb**, the deck boards between the sill and the first joist (half of 3.75" = 0.156' x 50
psf = 7.8 plf x 4.5208'/2 = 17.63 lb) and the sill (2.83 plf x 2.2604' = 6.40 lb): **300.5 lb**.

```
LUS28 (C-C-2026 p. 114, 2x8 row, DF/SP): floor (100) 1,100 x C_D 0.9 (dead-dominated) x C_M 0.70
      = 693 lb      300.5 / 693 = 0.434
```

Backing: the sill's soffit is −8.19", 6.90" over the post's end, and the CBSTQ's two straps are
on the post's east and west faces, so the north and south faces it hangs on are clear.

**12d. Straps (E14).** No HETA12 or HETA16 is listed in ZMAX or stainless (strongtie.com/heta
lists both G90; FL11473-R5 §4.6 evaluates every HETA as G90), so `CN-BW-TIE-E*/-GE*` stay
HETA20Z. Its 16" exposed strap stood 16 − 0.75 − 7.25 = 8.0" past the seat beam's top, into
the joists. It is field-trimmed at the beam top, 8.0" over the pour (`AN-BW-HETA-TRIM`); the
model draws it so. FL11473 Table 3 needs 12 nails for the pair, 6 per strap (note 4). Table 2
note 2 says which holes: the **lowest four**. Table 2 note 6's floor of **7** fasteners is the
SINGLE anchor's lateral rule, and Table 3 note 6 replaces it for a pair. Uplift 2,560 / F1
1,350 lb are unchanged.

**12e. The `cast` variant's head joint (§9).** Cast one pack short, the canopy columns' N-S
head force is `canopy_garage_diaphragm.md` §7's **332.81 lb** (was 333.06); the engine reads
333.40 (0.18% over, as before). Connector lateral 332.81/1,350 = 0.247 (unchanged to three
figures); column shear (332.81 + 167.16 − 93.06)/0.6 = 678.2 lb (engine 679.2); torsion
332.81/0.6 x 2.75/12 = 127.1 lb-ft (engine 127.3) against 1,499.5, 0.085.

## 13. 2026-11-01 — the 14" rounds are their own section (C3-E21)

`PT-BW-W`/`-GW` (and, under the `kdat` east posts, `PT-BW-PE`/`-PNE`) are **14"** rounds for the
CBSTQ66Z-SDS2's 3" strap cover (`canopy_west_band.md` §5e), and carried `PIER_CONCRETE_12`, whose
12" this note's §6 cage and slenderness rows assumed. They take `PIER_CONCRETE_14` now
(`east_posts.pier_assembly`); `PT-BW-E`/`-GE` stay 12". Worked here from the section alone.

**13a. §1 clearances, re-measured.** The rows above used a cladding face at 36'-7 1/4" and
arithmetic that did not close (37'-6" − 36'-7 1/4" − 6" is 4 3/4", not 6 3/4"). From grade to
the pier tops (−34" to −16.19") the pier faces the foundation's XPS and coating, 36'-4 1/16";
the main wall's cladding (36'-6 3/4") starts above the pier tops, at −13 7/16". 14": 6.94" clear
to the foam, 11" to concrete. 12": 7.94" / 12".

**13b. Section and cage, 14" round — (6) #5 since 2026-11-05**

| term | working | value |
|---|---|---|
| gross area | π (14/2)² | 153.94 in² |
| §10.6.1.1 floor on A_g | 0.01 x 153.94 | 1.539 in² |
| provided | (6) #5 = 6 (0.31) | 1.86 in² → ρ = 1.208% |
| bar circle | 7 − 2 cover − 0.375 tie − 0.3125 | r = 4.3125" |
| vertical c-c / clear | 2 r sin 30° | 4.31" / 3.69" ≥ 1.5" (§25.2.3) |
| dowel c-c, lapped beside each vertical | same circle | 4.31" ≥ 6 d_b = 3.75" → ψ_r 1.0 (§25.4.3.2) |
| tie spacing | least of 16 d_b = 10.0", 48 d_t = 18.0", h = 14" | 10" |

The (4) #5 cage this carried was 1.24 / 153.94 = 0.806%, under the gross floor, and met it only
on §10.3.1.2's half area (0.770 in² on 76.97 in²) — an engineer hold (C3-E21, F5-106). Six bars
take the gross floor outright, so `deck_post` no longer claims §10.3.1.2 on these four. The cage
is 10" at the 12" rounds' 2" cover, not the 8" cage at 3": six dowels lapped inside six
verticals at 2" stand 3.69" apart, and at 3" cover 2.69", both under 6 d_b, which would take
ψ_r to 1.6 and ℓ_dh to 11.38" against the pad's 9". **Lap each dowel beside its vertical, on the
bar circle.** The CBSTQ strap corners are 3.252" off the axis (`canopy_west_band.md` §5e), so a
bar on the 4.3125" circle clears them by 4.3125 − 3.252 − 0.3125 = 0.75" at any rotation. The
12" rounds keep (4) #5 (§6, 1.096%).

**13c. Slenderness, 14".** r = 0.25 x 14 = 3.50", I_g = π 14⁴ / 64 = 1,885.7 in⁴, E_c = 57,000
√5,000 = 4.031e6 psi, EI = 0.4 E_c I_g / 1.6 = 1.900e9 lb-in²:

| pier (k = 1, leaning) | l_u (pad top to pier top) | k l_u / r | P_c = π² EI / l_u² | P_u | δ_ns |
|---|---|---|---|---|---|
| `PT-BW-W` | −107.4375" to −16.19" = 91.25" | 26.1 | 2,252 kip | 7,457 lb | 1.004 |
| `PT-BW-GW` | −76.0" to −16.19" = 59.81" | 17.1 | 5,242 kip | 6,931 lb | 1.002 |

The 12" `PT-BW-E` at the same 91.25" reads 30.4 (§6's 92" row predates §12a's 3/4"). `PT-BW-PE`
/ `-PNE` are fixed-base sway columns (k 2.1), graded in bending with `canopy_garage_diaphragm.md`
§5a; only their cage (13b) is this note's. `deck_post` agrees on all four: 1.539 in² on the
gross area against (6) #5's 1.86, `PT-BW-W`/`-GW` k l_u/r 26.1 / 17.1.


## Addendum 2026-11-06 — the seat beams stop off the base strap (C2 E9)

`BM-BW-HOUSE-SEAT`/`-GARAGE-SEAT` start 0.4495" east of the west columns' face, 1/8" past the
CBSTQ66Z-SDS2 strap's SDS heads (`canopy_west_band.md` 2026-11-06 amendment). Each beam is
115 − 78.5745 = 36.4255" = **3.0355'** long (was 3.0729'); the hanger stays on the post face.

**§10b/§10c.** The landing tie reads the shorter beams; worked in §10.

**§6 piers.** Each seat beam gives half its length to each pier: W and E lose 3.281/2 x 0.03746 =
0.0615 ft², GW and GE 3.094/2 x 0.03746 = 0.0580 ft², at 1.2 x 10 + 1.6 x 40 = 76 psf factored:
W 7,311.0 → **7,306.3**, E 1,458.1 → 1,453.5, GW 6,785.0 → **6,780.6**, GE 1,065.9 → 1,061.5 lb.
Axial d/c stays 0.019 / 0.005 / 0.017 / 0.004. The retired GW spring example's 1/δ rises by
4.40/(0.75 x 9,270) = 0.000633 to **0.029205**, δ about **34.24**: still OVER, arithmetic only.

**§12b hangers.** Over the 3.0355' beam:

```
house   (50 x 3.281 + 5.658) x 3.0355 / 2 + 168.2 x 0.1875/3.0355 = 257.57 + 10.39 = 268.0 lb
        268.0 / 721 = 0.372 (was 0.376)
garage  160.358 x 1.51773 + 10.39 = 253.8 lb
```

The beam sits 1.55" on the LUS26-2Z's 2" seat. Its flange and backing are on the post face, as before.
Its end stands 0.4495" off that face, past C-C-2026 p. 22 note m's 1/8" maximum and the 3/8"
Simpson's gap tables reach, so 0.372 is arithmetic, not a rated reading; the beam bears on
the pack (`canopy_west_band.md` 2026-11-06 amendment, an EOR/Simpson item).

**Filler (owner, 2026-11-06; `canopy_west_band.md` amendment (b)).** The hanger is now nailed over
11/32" treated plywood strips, one each side of the strap. The end gap to the hanger is
0.4495 − 0.344 = **0.1055"**, within note m, and the beam sits **1.8945"** on the seat. The 16d
header nails keep 3.108" in the post. The demand is unchanged, 268.0 / 721 = **0.372**, and it is
now read inside the gap the row was tested at. The row does not publish a filler installation:
Simpson's confirmation is the remaining line, and gravity bears on the pack either way. Backing
is unchanged, because the flange moves out, not up.
