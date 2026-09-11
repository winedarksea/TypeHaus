# North entry canopy, piers and headers — hand-worked basis

**House:** catlin
**Structure:** `PT-BW-W`, `PT-BW-E`, `PT-BW-RE`, `PT-BW-GW`, `PT-BW-GE`, `PT-BW-RNE` (cast
piers) and their footings `FT-BW-*`; `PT-BW-CW`/`-CE`/`-CNW`/`-CNE` (6x6 KDAT roof columns);
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
**Oracle for:** `engineering/roof_beam.py` (§5) and `engineering/pier_basis.py` /
`engineering/deck_post.py` / `engineering/spread_footing.py` (§6); reproduced by
`tests/test_north_entry_piers.py`.
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
| footing thickness | authored | 10" |
| roof column length | 6'-4 3/4" − (−1'-3 1/2") | 7'-8 1/4" |
| header span, bearing to bearing | 43'-2 5/8" − 37'-6" | 5'-8 5/8" = 5.719 ft |
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

> ⚠ **The stainless tie is NOT the galvanized tie's 700 lbf, and this house records no
> number for it.** The figures in circulation for the H2.5ASS are materially lower (a
> 440/75/70 uplift-F1-F2 row and a 265 lbf stud-to-plate row both appear in secondary
> listings of the Simpson C-C catalog) and **none could be confirmed against a primary
> Simpson table or code report on 2026-09-10.** So `library/hardware.py` carries it with
> `allowable=None`, which is the house's standing way of saying "nobody read the report"
> rather than handing a capacity check a number nobody sourced. **256 lb is under even the
> lowest figure in circulation**, which is why one tie per bearing is specified and why this
> is stated rather than resolved. If a submittal wants it closed, read ESR-2613 or the
> current C-C catalog for the SS row and record it.

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
d/c 1.06 in bending and 0.76 in shear, and a 2-ply 2x10 fails outright at d/c 1.57. A
3-1/2" x 11-7/8" treated glulam is the alternative at roughly 4x the material rate; take it
only if the exposed 3-ply seam is objectionable.

**No repetitive-member factor.** NDS §4.3.9's C_r of 1.15 wants three or more members
**spaced** not more than 24" apart and joined by a load-distributing element. A built-up
beam's plies are in contact and share load through their nails alone. Claiming C_r would
buy 15% of capacity the section has not got.

**The span above is the whole beam, and since 2026-09-10 that is conservative by ~40%.**
`roof_beam.py` takes node to node, 5.719 ft, as a simple span. What is built is a 4.906 ft
back span between `PT-BW-CW` and `PT-BW-CNW` with an 8 7/8" tail carrying the roof plane out
to the garage wall. The real maximum is about 3,370 lb-ft (span moment less half the
cantilever moment w a²/2 = 321 lb-ft) against the 4,787 above, so **every ratio in this
section is on the safe side of what is built and none of them was re-pinned.** If the module
ever learns to resolve a beam's real bearings, expect d/c 0.71 to drop to about 0.50 and
re-work this table rather than assuming it drifted.

## 6. The piers (oracles `pier_basis` / `deck_post` / `spread_footing`)

Six piers on **two** bearing planes, and the split is the first thing to read.

> ⚠ **Two of the six are not piers, and the bearing numbers below are unchanged by that.**
> `PT-BW-RE` and `PT-BW-RNE` became full-height 12" cast columns on 2026-09-10, running
> unbroken from footing to header soffit and fixed at the base — the canopy's east lateral
> system (`notes/north_entry_structure.md` §1a). Same section, same cage, same pad, same
> footing: the shaft simply does not stop at −1'-3 1/2". **What is NOT re-worked here is the
> consequence of the fixed base**, and it is the engineer of record's: the base moment is a
> lateral demand this section was never asked to carry, `PT-BW-RNE` has 4'-2" of embedment
> below grade against roughly 5'-6" that IBC 1807.3.2.1's non-constrained formula wants for
> it in presumptive sand, and k·l_u/r on the exposed 9'-2 3/4" is about 74 as a SWAY column
> where §6's slenderness reading below was taken non-sway.

| pier | carries | pad | bottom | bearing d/c |
|---|---|---|---|---|
| `PT-BW-W` | `PT-BW-CW` + house-side west seat | 2'-0" | −9'-9 7/16" | 0.81 |
| `PT-BW-E` | house-side east seat | 2'-0" | −9'-9 7/16" | 0.42 |
| `PT-BW-RE` | the east header (full-height column) | 2'-0" | −9'-9 7/16" | 0.54 |
| `PT-BW-GW` | `PT-BW-CNW` + garage-side west seat | 2'-0" | −7'-0" | 0.74 |
| `PT-BW-GE` | garage-side east seat | 1'-6" | −7'-0" | 0.59 |
| `PT-BW-RNE` | the east header (full-height column) | 2'-0" | −7'-0" | 0.60 |

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
| roof live | 40.0 × 50 psf (`pier_basis` screens at ground snow) | 2,000 lb |
| deck live | 18.4 × 40 psf | 736 lb |
| dead | (40.0 + 18.4) × 10 psf + self weight + carried | 1,668 lb |
| service | | **4,404 lb** |
| factored | 1.2 D + 1.6 L | **6,380 lb** |

**`pier_basis` walks the beam chain and reads the tributaries wider than this line**: 17.0 ft²
of deck and 47.7 ft² of roof on `PT-BW-W` (it credits the seat, the screen sill and the
carriers each a share, and the west roof column's header), for 6,835 lb factored against the
6,380 here. Before the narrowing it read 23.3 / 51.8 and 7,687 lb against 7,765. Same
order, same conclusion, and the difference is bookkeeping in a load case that is nowhere
near governing.

**`pier_basis` screens the roof at ground snow (50 psf), not at the 73.7 psf of §3.** That is
a deliberate under-read in a screening tool, and it is why the pier's ratio is not the number
to argue about: at 73.7 psf the roof live becomes 2,948 lb, service 6,231 lb, and the axial
d/c moves from 0.027 to about 0.032 against a §22.4.2 cap of 2.859e5 lb. **Nothing near
governing either way** — the cage below is what sizes this shaft.

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
- **The canopy's lateral system as a separate plane.** It has none. East-west wind goes into
  the roof sheathing and spans north into the garage roof diaphragm; north-south wind runs
  axially along the headers into the garage's corner posts. **Both paths die if that joint
  ever becomes a real structural break.** If it does, a `KBS1Z` knee brace at each column is
  the cheap answer and is a live, rated, priced row in this house.
- **The soil bearing value itself.** 2,000 psf is presumptive, not measured; no boring log
  exists for this site. `PT-BW-W` at d/c 0.90 is what feels a lower number first.
- **The four cast terrace tiers, `SL-BW-TIER1..4`.** They are plain concrete on a compacted
  base, not frost-founded, and no calculation here covers them. Each is one riser thick and
  fully bedded on the tier below, so there is no span to grade; what is ungraded is
  **movement**, and the owner has accepted it knowingly. See
  `notes/north_entry_structure.md` §3 for what a winter costs and which joint pays.
- **The truss-to-header tie CAPACITY**, for the reason §4a gives: the stainless H2.5ASS's
  published allowables could not be sourced. The demand is computed; the capacity is not.

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
