# Titanium basement handrail and range backsplash — hand-worked basis

**House:** catlin
**Structure:** `RL-M-HANDRAIL-E`, `RL-M-HANDRAIL-W` (ST-B2M); `WP-M-KIT-BACKSPLASH` (W-M-E1).
**Written:** 2026-10-09, by hand, from the authored geometry and the resolved rail sweeps.
**Oracle for:** the R301.5 support-spacing limit on `RAILING-INT-TI-HANDRAIL-42`
(`bracket_spacing_max = 1000 mm`), graded by `code.R301_5_handrail_support_spacing`;
reproduced by `tests/test_catlin_titanium_handrail.py`.
**Companions:** `notes/wall_backing.md` — the backing schedule this rail's blocks join.
**What is asked of the reviewer:** §4's arithmetic, and whether the fittings bought in §2
seat on a 42.0 x 37.0 mm tube.

> ⚠ **An end cap alone does not meet the code.** IRC R311.7.8.2: "Handrail ends shall be
> returned or shall terminate in newel posts or safety terminals." Every end of these rails
> RETURNS to the wall (`start_termination` / `end_termination = "wall_return"`), and the
> wall end plate is what closes the tube. `code.R311_7_8_2_handrail_ends` reads the drawn
> return.

> ⚠ **The tube is 42.0 mm, the fittings are 42.4 mm.** 42.4 is the European stainless
> handrail standard; nobody stocks 42.0. Measure every fitting against the tube before any
> epoxy is mixed (§2).

---

## 1. Stock on hand (owner-furnished, Waltly Titanium, 2026-10)

| item | bought | used | spare |
|---|---|---|---|
| Ti alloy tube 42 OD x 2.5 wall x ~1200 | 5 | 4 (2 per rail) | 1 full tube + 4 offcuts ~255-270 mm |
| Gr 2 sheet 500 x 1000 x 0.8, teardrop hem | 5 | 2 | 3 |

Tube grade is not on the order (a bike-frame supplier, so likely Gr 9 Ti-3Al-2.5V). Ask for
the mill cert. §4 grades on Gr 2's floor, so the answer does not change the verdict.

Cut plan per rail, developed (sloped) length off the resolved RAIL1 sweep:

| rail | developed | supports (developed station) | pieces |
|---|---|---|---|
| RL-M-HANDRAIL-E | 74.1" = 1882 mm | 0 / 37.3" / 74.1" | 2 x ~941 mm, spliced at the mid bracket |
| RL-M-HANDRAIL-W | 73.3" = 1862 mm | 0 / 36.6" / 73.3" | 2 x ~931 mm, spliced at the mid bracket |

The returns are stainless elbows, not tube: 70 mm wall-to-centre is all elbow and flange.
Cut each piece to the elbow's measured socket, not to these lengths.

Main to second (ST-M2S) needs ~4.2-4.5 m more and is NOT covered by this stock. It stays
dark steel unless more tube is ordered (same lot, so the brushed finish matches).

## 2. Fittings (stock 316 stainless, sized for 42.4 mm tube)

| part | count | fit on 42.0 / 37.0 tube |
|---|---|---|
| saddle wall bracket, 60-93 mm wall-to-centre, rated >= 0.9 kN | 2 | saddle R21.2 on R21.0: seats; bed in epoxy |
| 90-degree wall-return elbow | 4 | spigot for 42.4 x 2.6 tube (ID 37.2) is 0.2 mm loose: epoxy fills it. A 42.4 x 2.0 spigot (38.4) will NOT go in |
| wall end plate (flange), ~70 mm | 4 | closes the return; 3 screws |
| internal splice sleeve | 2 | catalogue sleeves are ~37.0-38.2 mm: likely too tight. Fallback: machine 316 bar to 36.85 x 100 mm |

The 0.2 mm step per side at each elbow (42.0 vs 42.4) is cosmetic. Blend it or accept it.
Bond with a structural two-part epoxy. Ti and 316 are both passive and sit close in the
galvanic series, so the pair is benign indoors. Anchors are A4/316.

## 3. Mounting and backing

- **E rail (W-B-CN, concrete):** two A4 6 mm screw anchors per plate, three per flange.
- **W rail mid bracket** (y = 28'-7 5/8") lands on W-M-STRW stud-005 at 28'-8".
- **W rail top return** (y = 26'-2 5/8", 37" up): one flange screw goes in W-M-STRW2's end
  stud; the rest land in the 4 1/8" bay to the N-M-STRJ tee, filled by `BK-M-STRW2-RAIL-TOP`
  (2x8 flat at 33").
- **W rail foot return** (y = 31'-1 5/8", ~6" below the main floor) lands in the floor
  band, behind the stair plywood. W-B-STR's studs stop 13 7/16" below the floor, and
  FS-M-MECH's joist end is 2 5/8" behind the face. **Field item:** block solid between the
  joist end and the plywood there before the plywood goes on. A `WallBacking` cannot sit
  above its wall's framing.
- The W rail stops at the upper flight's top nosing (26'-2 5/8"). Past that point the
  rake reads the lower flight.

## 4. R301.5 hand-calc — 200 lb concentrated, any direction

| term | working | value |
|---|---|---|
| D, d | 42.0, 42.0 - 2 x 2.5 | 42.0, 37.0 mm |
| I | pi (42^4 - 37^4) / 64 = pi x 1,237,535 / 64 | 60,746 mm^4 |
| S | I / 21 | 2,893 mm^3 |
| P | 200 lb x 4.448 | 890 N |
| M at L = 1000 mm, simple span, load at midspan | P L / 4 | 222,400 N mm |
| stress | M / S | **76.9 MPa** |
| ratio vs Gr 2 F_y,min 275 MPa | 76.9 / 275 | **0.28** |
| deflection | P L^3 / (48 E I), E = 105 GPa | 2.9 mm |
| at the widest drawn span, 947 mm | 890 x 947 / 4 / 2893 | 72.8 MPa |

Bending governs at 0.28 on a 1000 mm span. That span is the type's `bracket_spacing_max`,
and the drawn spans are 930-947 mm. Each support (bracket or flange) sees at most the full
890 N when the load lands on it, so buy fittings rated >= 0.9 kN. The splice sits over a
bracket, so the sleeve carries shear and a small continuity moment, not midspan moment.

## 5. Backsplash (WP-M-KIT-BACKSPLASH)

- **Layout:** two sheets, landscape, stacked, uncut: 1000 x 1000 mm centred on the range
  (y = 372 3/8"), spanning y 352 11/16"..392 1/16".
- **Height:** 36" AFF (counter top) to 75 3/8" AFF, hemmed seam at 55 11/16" AFF.
  `offset` is wall-local (from the wall base, which is the structural floor), so the
  authored 36 15/16" is the 36" counter.
- **Hood:** APPL-M-HOOD (66"-84" AFF, 30" wide) hides the top edge across its own width.
  The sheet shows 4 3/4" past each side of the hood above 66".
- **North upper:** the sheet laps 1 7/8" behind FURN-M-KIT-WN2 (bottom 73 1/2"). Shim or
  notch that upper's back by the sheet's edge thickness.
- **Clearances:** KGF3's plate edge is 2 1/16" clear of the south edge, and WIN-M-KIT-E is
  clear.
- **Hood power:** the hood needs a 120 V box that is not modelled. Put it at >= 77" AFF,
  behind the hood body and above the sheet.
- **Hem direction:** confirm which face the hems return to. Folded to the back, they stand
  the field ~5 mm off the wall, and the adhesive bed (MS-polymer, or a VHB stack) takes that.
- **Combustibility:** induction range, noncombustible sheet; no clearance question arises.

## 6. What is NOT graded here

- **Bracket and anchor capacity:** a product rating, read when the fittings are bought.
  `advisory.wall_backing_present` does not see railing supports.
- **The splice bond:** sleeve shear and bond are the epoxy maker's table.
- **Backsplash fixing:** no check reads `model.panelings`.

## Sources

- IRC 2018 (MN 1309) R301.5 Table, R311.7.1, R311.7.8.1-.3 — handrail load, projection,
  height, continuity, returns and the 1 1/2" wall space, grip size.
- ASTM B338 / B861 — titanium tube; Gr 2 F_y min 275 MPa (40 ksi); E ~105 GPa.
- EN 10217-7 / common 42.4 mm stainless handrail fittings catalogues — 42.4 x 2.0 and
  42.4 x 2.6 tube sizes.
