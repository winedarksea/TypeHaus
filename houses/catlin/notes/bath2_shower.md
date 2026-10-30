# RM-M-BATH2's shower — thermostatic, one outlet, glass short of the ceiling

**House:** catlin
**Structure:** `FX-M-BATH2-SH` (`FX-SHOWER-36-THERMO-COMBO`), `WP-M-BATH2-SURR`, `REG-M-EXH2`,
`DU-M-ERV-R-BATH2`, `EQ-B-WH`; since the follow-up the same day, `EQ-M-BATH2-STALL-FAN`,
`DU-M-BATH2-DRY`, `REG-M-BATH2-DRY-IN`/`-OUT` (§7).
**Written:** 2026-10-12, by hand, against `out/model.json` after the change.
**Oracle for:** nothing. This is a **decision record**. No engine module computes hot-water
duration or steam, and none is proposed. It follows `notes/TEMPLATE.md`'s shape so the
arithmetic can be redone line by line.
**Companions:** `notes/dwhr_decision.md` (§10 re-reads the DWHR "no" at 1.75 gpm);
`notes/bath2_lighting.md` (the room's two light layers);
`notes/interior_selections.md` (the ASSE 1016 argument every shower valve here rests on).
**What is asked of the reviewer:** §2's three assumptions (setpoint, usable fraction, mains
temperature). Disagree with one and redo the table.

> ⚠ **The grille is outside the enclosure on purpose, and the front glass's open top is the
> steam path.** Do not glass the front to the ceiling, add a transom, or move `REG-M-EXH2`
> back by the tub without re-reading §4. The ERV has no headroom to boost, so position is
> the only lever. The stall-drying fan (§7) does not change this: its air enters at the
> ceiling inside the glass and leaves the stall the same way, over the open top.

---

## 1. What changed, and why thermostatic

| Item | Before (2026-09-06) | After (2026-10-12) |
|---|---|---|
| Valve | R10000-UNBX rough, pressure-balance trim | **same rough**, Delta TempAssure 17T thermostatic trim |
| Outlets | fixed head + slide-bar handshower: diverter rough, second riser | **one**: Moen Attract Magnetix 26008 rain/handheld combo |
| Head flow | Speakman S-2005-H, 2.5 gpm | 1.75 gpm |
| Walls | marble-look panel to 7'-0" | solid-surface panel floor to ceiling (106"), 53.0 SF net |
| Base | kit pan | matching 36x36 solid-surface base |
| Glass | unspecified | tub (north) side floor to ceiling; front (west) stock Flex door, 72" above threshold (2026-10-22) |
| Exhaust | `REG-M-EXH2` at (4'-0", 18'-0"), by the tub | (4'-2", 15'-4"), ~8" west of the front glass |

**The thermostatic argument is about the tank, not about the outlet count.** A
pressure-balance valve holds the hot-to-cold *ratio*. When the 80-gal heat-pump tank's outlet
starts to fall late in a long shower, the mixed water falls with it, at about 0.8 °F per °F
(the hot fraction in §2). A thermostatic valve re-mixes: it opens the hot side to hold the set
temperature until the outlet itself reaches the set point. It also gives a separate volume
control. The 2026-09-06 argument against thermostatic, that the element drifts and a PB spool
is nearly inert, still holds for the other four showers. It is outweighed here, in the one
shower used daily and long. The R10000 rough was chosen so this choice could be made from
outside the tile, and this is that choice.

## 2. How long one tank lasts at 1.75 gpm

Assumptions:

| # | term | value | why |
|---|---|---|---|
| B1 | tank setpoint | **120 °F** | the usual heat-pump setpoint; none is authored on `EQ-T-WATER-HEATER` |
| B2 | usable fraction before the outlet falls off | **0.70** × 80 gal = **56 gal** | the common stratified-tank figure; first-hour ratings imply about this |
| B3 | mixed temperature at the head | **105 °F** | |
| B4 | cold main | **50 °F** annual, **40 °F** February | as `dwhr_decision.md` A3 |

No credit is taken for recovery during the draw. Heat-pump-only recovery is about 7 gph at a
70 °F rise (~4,000 Btu/h), worth roughly 3 more minutes.

| term | working | 50 °F main | 40 °F main |
|---|---|---|---|
| hot fraction | (105 − Tc) / (120 − Tc) | 55/70 = **0.786** | 65/80 = **0.813** |
| hot draw | 1.75 × fraction | 1.375 gpm | 1.422 gpm |
| **minutes at 105 °F** | 56 / hot draw | **40.7 min** | **39.4 min** |

**About 40 minutes of one shower, summer or winter.** No tank, setpoint or mixing-valve change
is needed. Two back-to-back 15-minute showers draw 2 × 15 × 1.42 = 43 gal, inside the 56.

Past that point, the two valves behave differently. At an outlet of 110 °F with a 40 °F main,
a PB valve still set for 120 °F delivers 40 + 0.813 × 70 = **96.9 °F**. The 17T holds 105 °F
until the outlet itself is at about 105. That tail is the whole reason for the swap.

## 3. Glass heights

`RM-M-BATH2.clear_height_m` = 2.6924 m = **106"**.

| side | what | height | open above |
|---|---|---|---|
| north (tub) | custom fixed pane on Corian, independently supported at the east wall, ceiling and west post | deck 22¾" to ceiling 106" (83¼" high) | none |
| west (front) | DreamLine Flex SHDR-22327200-01, chrome, stock pivot front | 72" above threshold; top at datum 77¼" | 28¾" |
| east, south | Swanstone Carrara panels (`WP-M-BATH2-SURR`) | 106" | none |

**Selected 2026-10-22:** a stock framed pivot front and a custom north pane replace the
90" custom front. The supplied top/bottom rails supersede the earlier trackless preference.
Corrected 2026-10-29: the pan bears on the ¾" subfloor, without tile or DITRA beneath
it. Its 4½" threshold puts the front's head at 77¼" above storey datum. The custom
north glass remains anchored at deck datum 22¾" and modeled ceiling datum 106".
There is no transom, and the gap to the ceiling remains the steam path.

`ModelRepresentation.symbol="swanstone-flex-3636"` generates the pan, door, post and return
for the viewer, GLB and IFC. `WP-M-BATH2-SURR` supplies the two wall panels separately.
The return is inset ¾" north onto the deck; the 1½" post sits wholly on Corian, with its
inside face on the pan's north edge. Its front-to-back centre is 1⅜" in from the pan's west
edge, so its base clears the deck's west edge. The resolved south panel's finished face is already flush with the pan edge (its ½"
thickness is on the wall side), so there is **36"** between it and the post: the upper
limit of the Flex's 32–36" adjustment range. Do not subtract the wall panel twice.
**Owner confirmed 2026-10-23:** move `W-M-TUBDK-S` and the unchanged 36" pan ⅛" south
to close the south jamb gap introduced by the thinner wall board. The pan now runs
y=158.25"–194.25", flush with the south surround. The deck edge, west apron and east-wall
surround/splash spans follow; the tub and its service connections stay put. Its internal
foot-bay clearance grows from 4.740" to 4.865".
Field-measure the finished opening and confirm tolerances before ordering.
Post and channel dimensions are preliminary visualization allowances, not a shop drawing.

**Procurement confirms:** DreamLine requires finished solid jambs and at least **1⅜" of
flat threshold**. The pan's modeled 2¾" threshold footprint is not certification of its flat
bearing width: verify the top land and corner radii on the Carrara dealer's submittal.
Have DreamLine/glazier approve the supported-post jamb connection; size the post, its
connections into deck/ceiling backing, channels and tempered north pane. Do not transfer
the door's load to the unsupported edge of the return. No glass drilling after tempering.
The front pivots at the south wall and swings out toward the vanity; the integration test
checks its conservative sweep, including the handle, against the vanity and bathroom door.

**Appearance:** the live viewer applies the existing illustrative veined-marble texture
to the Carrara panels and base; it is not a photograph of Swan's colour chip. GLB/IFC retain
shared geometry and glass transparency but export flat Carrara colour rather than the
procedural texture. IFC surface styles identify the solid-surface material. Physical chip
and supplier shop drawings govern fabrication.

Sources, read 2026-10-22:
- [Flex front product](https://dreamline.com/product/dreamline-flex-32-36-inch-w-x-72-inch-h-semi-frameless-pivot-shower-door/shdr-22327200/shdr-22327200-01)
- [Flex installation requirements](https://dreamline.com/media/manuals/FLEX_28x72_32x72_and_Single_Threshold_Base_Manual_Ver_2_082022.pdf)
- [Swan SS-3636 specification](https://assets.unilogcorp.com/267/ITEM/DOC/Swan_SF03636MD_130_Specification_Sheet.pdf)

## 4. Steam path and the grille

The Broan B210E75RT delivers ~206.6 cfm against the 205 cfm the code requires
(`mep.erv_static_budget`; `notes/erv_static_budget.md`). There is no headroom to boost
BATH2's 20 cfm, so the grille's position is the only lever.

- Warm, wet air rises and leaves the enclosure through the front's 28" open top.
- `REG-M-EXH2` now sits at **(4'-2", 15'-4")**. The front glass is at x = 4'-10 5/8", so the
  grille is **8 5/8" outside it**, right where the plume comes over. Before, it was ~4' away by
  the tub.
- It stays **outside** the enclosure and **always on**. A grille inside a glassed stall needs
  a wet-rated, listed-for-shower terminal, and the stall would still need make-up air.
- It is clear of `ED-M-BATH2-CAN1` at (2'-6", 16'-0"), 1'-8" west of it.
- `DU-M-ERV-R-BATH2` leaves the x = 3'-10 1/2" extract trunk in the **15'-4" bay**. FS-S-WEST's
  bay centres are 8" + n × 16", and this is the next bay north of BED2's 14'-0". It is a pure
  bay leg at `_BAY_Z`, crossing no truss. `haus route --run DU-M-ERV-R-BATH2 --evaluate`
  proposed the same lane, stopping 1 1/2" short of the grille's centre.
- After the move, `haus check` is unchanged: 0 FAIL and the same 69 UNKNOWN.
  `mep.ventilation_distribution` still passes for RM-M-BATH2.

## 5. What is NOT decided here

- **Drain-water heat recovery**: still no. See `dwhr_decision.md` §10.
- **A transom, a boost of the ERV extract, or steam features**: not done. The ERV cannot
  boost (§4). The stall-drying fan of §7 is a TRANSFER loop of bedroom air, not a boost:
  it takes nothing out of the house and earns no ventilation credit.
- **The studio bath and sauna showers, and the two tub-showers' valves**: unchanged. The
  tub-showers get only the 52535-SS head. Their WALLS are §6.
- **A flow-rate field**: none. Nothing in the engine would read it. 1.75 gpm lives on the
  product records in `plan/products_showering.py`.

### Closed confirms (owner, 2026-10-22)

1. **Finish: all chrome.** The 26008 head (no stainless exists), the 17T trim and the tub
   filler, now Moen Align `T393` on a `4794` rough (2026-10-22). The Align accessories,
   Arvo lavatory faucet, and Clearflo drain are chrome too.
2. **17T trim: Delta T17T059**, the Trinsic valve-only 17T trim on the R10000 rough. No
   Ashlyn 17T exists (T17264 is Monitor 17 pressure-balance), and Trinsic remains the
   selected thermostatic shower trim alongside the Align tub filler.
   T17T259 is the shower-only version with its own head; this shower uses the 26008.
3. **Base and panels: Swanstone, in Carrara (221)** (colour closed by the owner 2026-10-22;
   confirm against a physical chip, `notes/bath2_tub_deck_finish.md` §4). SS-3636:
   36x36x5 1/2", 4 1/2" threshold, centre Fit-Flo drain, 3" drain hole. Still to confirm on
   the dealer's submittal: that the flanges suit a W threshold with E/S/N walls, and a panel
   height that reaches the 106" ceiling above the base (or a top cap). A Corian
   floor-to-ceiling stall (about $1.5-3k more, one piece) was considered and declined.

**Drain coordination, updated 2026-10-23.** The SS-3636's centre drain, (6'-4 5/8",
14'-8 1/4"), sits over FS-M-WEST joist 11, whose top flange runs y 174 3/4"..177 1/4". A riser
there cuts the flange: `mep.run_in_joist_flange` FAILs it and `mep.riser_through_deck` finds no
opening to head it. `drain_position` is now (6'-4 5/8", 14'-11"), the nearest bay point that
clears the flange for a 2" pipe, 2 3/4" north of centre. `PR-B-SH2-DRAIN` drops from the drain
into that bay, runs below the joists (underside 97 9/16" basement) west along y=14'-11" from
87 1/16" to 85 15/16", and enters PR-B-MAIN-DRAIN's corner at (3', 16'-6") at the old 85 3/8"
invert. Flattest slope 0.33"/ft, against the 1/4" minimum. `haus route --run` was no use here:
it routes to the main's sewer exit at 37', 35 ft long, with footing, sleeve and cleanout
FAILs, so the run is hand-authored. Checks: `haus check` 0 FAIL, no new UNKNOWN. Under
`--no-suppress` the only SH2 line is the riser through the deck (2.38" against the 2" undrawn
allowance), the same class the old run carried. **OPEN, owner:** a 2 3/4" offset from a moulded
centre drain sits off the pan's low point. Confirm with Swanstone that the SS-3636 takes it, or
frame a centre floor opening with joist 11 cut and headed (a structural call).

## 6. Wet walls (follow-up, 2026-10-12)

Every shower here is now specified so water cannot get behind its walls. Nothing in the
engine grades a substrate, so this lives on the type `source`, the price rows and the
comment on `WP-M-BATH2-SURR` (the "glass has no element" precedent; `Wall.layer_materials`
would retype the whole wall face).

| shower | behind the finish | rule |
|---|---|---|
| BATH2 (`FX-M-BATH2-SH`) | glass-mat gypsum or cement backer, floor to ceiling, on both closed walls; bonded liquid membrane (RedGard / Hydro Ban class) lapped OVER the base flange; panel bonded over that | neither wall is exterior, so no double vapour barrier |
| BATH2 knee wall `W-M-TUBDK-S` | the Corian stall face (`WP-M-BATH2-TUBDK-APRON`, since 2026-10-22), bonded to the deck top and run 3/4"-22 3/4" with no horizontal joint under the glass; its E end meets the Swanstone E panel in a silicone corner, the base flange tucked behind it | the top slopes >= 1/4" into the stall on the stall side of the glass; glass in a routed channel or clamps, bedded in silicone (`notes/bath2_tub_deck_finish.md` §3) |
| STUBATH neo-angle | the same backer and membrane under `WP-A-STUBATH-SURR` | priced on `FX-SHOWER-36-NEO-COMBO` |
| BATH1, SUITEBATH tub-showers | the one-piece insert IS the wall | **nothing penetrates the insert** but the valve and spout knockouts; use the moulded shelves. Both lit niches are dropped (`notes/superseded/shower_niche.md`) |
| BATH1's back, exterior `W-S-N3` | insert inside, ccSPF outside: ~0 perm both faces | never penetrate it |
| sauna rinse | model: tile on shiplap; note: foam backer | OPEN — `notes/sauna_shower_basement_detail.md` |

**Backer: the spec above stands** (owner, 2026-10-22, after a reviewer suggested GoBoard).
Swanstone's shower-wall-kit guide prepares sheetrock/greenboard/cementboard/wood, plaster,
cement/concrete, old tile, wallpaper and Masonite. It lists no foam board, and it wants
every one sealed with a water- or oil-based primer/sealer. So **trial-bond Swanstone's tape
and adhesive to the cured membrane, or prime over the membrane with a water-based primer**
first. GoBoard (JM polyiso tile backer, ICC-ES ESR-4812) was considered and declined: it is
a tile backer, Swanstone does not list foam board, and the liquid membrane already provides
the waterproofing GoBoard would add.

BATH2's base: integral flanges E, S and N, threshold W, fully bedded with no voids, and no
radiant cable under it. Joints: mould-inhibiting 100% silicone at panel-to-base, the corner
and the cap; escutcheons sealed to the panel; the R10000's plaster guard set to the panel
face. No niche. Stock Flex front with its supplied bottom rail and seals (2026-10-22).

The knee-wall span needed one engine addition: `W-M-TUBDK-S` stands inside the room's face,
so both its faces are the room's and no side can be derived. `PanelingSpan.face` names it
(`"right"` of C->E is the stall), and a span on an inside wall without one is an ERROR.

## 7. Stall drying fan (Option A, owner 2026-10-12)

**What it is.** `EQ-M-BATH2-STALL-FAN`, a moisture-rated 4" inline fan in RM-M-BED's ceiling,
draws filtered bedroom air through `REG-M-BATH2-DRY-IN` and blows it down into the stall
through `REG-M-BATH2-DRY-OUT`, a damped round nozzle at (6'-4", 15'-4"), on a 30-60 min
countdown (`ED-M-BATH2-SW-DRY`). The air leaves over the front glass's 28" open top, past
`REG-M-EXH2`, and returns to the bedroom under `D-M-BATH2`.

### 7.1 The three options

| | what | why not / why |
|---|---|---|
| **A** | breeze dryer: inline fan, ~95 cfm at 0.3-0.4 in. w.g. | **chosen**: ~1 sone, one duct, a passive terminal in the stall |
| B | spa-blower jet system (Airmada class) | Airmada's blowers move 70-115 cfm at **40-130 in. w.g.**, two orders of magnitude over the inline fan's 0.2-0.4". That pressure buys jets, at 62-70 dB, custom nozzles, and a blower that would need a mechanical room |
| C | skip it | a squeegeed stall in still, humid air takes ~2 h to dry (§7.2) |

Airmada itself claims 5-7 h for an untreated shower; that is the still-air row below.

### 7.2 How long the stall takes to dry

Wetted area: two closed walls and the glass to ~7' (4 x 3' x 7' = 84 SF) plus the base
(9 SF): **93 SF = 8.6 m²**. Evaporation is h_m x (vapour density at the film - in the air).

| term | still stall, after a shower | with the breeze |
|---|---|---|
| air | ~23 °C, ~80% RH: 0.80 x 20.6 = 16.5 g/m³ | bedroom air ~21 °C, 40% RH: 0.40 x 18.3 = 7.3 g/m³ |
| film | ~21 °C: 18.3 g/m³ | ~17 °C (evaporatively cooled, still warm from the shower): 14.5 g/m³ |
| drive | 18.3 - 16.5 = **1.8 g/m³** | 14.5 - 7.3 = **7.2 g/m³** |
| h_m | natural convection, h ~ 3 W/m²K: 3 / (1.2 x 1006 x 0.89) = **2.8e-3 m/s** | forced, 0.5-1 m/s on the near faces, h ~ 7-11: **6e-3 to 1e-2 m/s** |
| rate | 2.8e-3 x 1.8 = 5.0e-3 g/m²s = **18 g/m²h** | 7.2 x (6e-3..1e-2) = **150-260 g/m²h** |
| squeegeed film, ~50 g/m² | 50 / 18 = **~2.8 h** | 50 / (150..260) = 12-20 min; **~20-30 min** with the faces the jet does not reach |
| unsqueegeed, ~150-300 g/m² | **~8-16 h**, in practice 4-8 h as the room dries out | **~1-2 h** |

The air can carry it: 95 cfm = 0.045 m³/s; picking up 7.7 g/m³ (7.3 -> 15) that is 0.35 g/s,
**1.2 kg/h**, against 50 g/m² x 8.6 m² = **0.43 kg** to remove.

### 7.3 Route and static

`DU-M-BATH2-DRY`: 4" galvanized, 13.0 ft developed, 4 x 90° plus the two tier offsets.
West along the 11'-4" FS-S-WEST bay (lower tier) to x=8'-0"; south on the upper tier
through web opening 3 (x 7'-4 1/2"..8'-7 1/2") across the 12', 13'-4" and 14'-8" trusses,
passing over `DU-M-ERV-R-LIVING` and `-BED2`; west along the 15'-4" bay to the nozzle. It
moves no existing run. **The accepted route is the router's proposal A**
(`haus route --run DU-M-BATH2-DRY --alternatives 6 --evaluate --via "8,11.3333" --via
"8,15.3333"`: 13.07 ft, 4 bends), with two corrections. Its crossing tier was -2", which
puts the crown 1 1/2" into the top chord, so the crossing rides the house's -3 1/2" upper
tier instead. Its lane at x=7'-10 13/16" moved to 8'-0", the centre of web opening 3. As
authored, the run checks clean. Proposals B-F were longer, and each added FAILs. The router's sizing line
says 95 cfm wants 6" at the house's 0.08 in./100 ft design rate. 5" and 6" do not fit the
crossing, so the fan carries the friction instead:

| term | working | in. w.g. |
|---|---|---|
| duct friction | 95 cfm in 4" (1,090 fpm): 0.55 / 100 ft x 13 ft | 0.07 |
| four elbows | ~5-10 ft equivalent each at 0.55 / 100 ft | 0.11-0.22 |
| filter grille + filter | 12x12 face; AAF PerfectPleat HC M8, nominal 10x10x1 (actual 9.5x9.5x0.75) | 0.05-0.10 |
| nozzle + damper | velocity pressure 0.074 x K 1-1.5 | 0.07-0.11 |
| **total** | | **~0.3-0.4** |

At 0.3-0.4" a WhisperLine-class 4" fan (120 cfm at 0.2", 108 at 0.3") gives **~90-105 cfm**.

The recommended filter's actual media area is 0.626 ft²; 95 cfm gives about 152 fpm. AAF rates
the 1-inch filter at 0.23 in. w.g. initial resistance at 300 fpm, which gives an estimated
0.06 in. w.g. at the operating point by square-law interpolation. That is a filter-only
estimate; the grille allowance is included in the table's 0.05-0.10 in. w.g. range. The
manufacturer's 10x10x1 size is nominal: verify the final grille holder accepts the stated
9.5x9.5x0.75 actual dimensions.

### 7.4 Open confirms

1. **Fan model.** The FV-10NLF1E was discontinued 2024-04-02; confirm a current 4" equal
   (Fantech, Broan, Panasonic) with a published curve >= 95 cfm at 0.3-0.4" and a
   moisture-rated, insulated housing.
2. **Nozzle**: a round adjustable diffuser with a gravity backdraft damper, suitable for a
   wet location.
3. **GFCI**: the fan is in the bedroom ceiling, not a shower zone, so the code does not
   require it; confirm the fan's own listing does not. ~30 VA on `CKT-LT-MAIN`, stated on
   the circuit (an Equipment adds 0 VA to the derived panel schedule).

## Sources

- Moen 26008 product page and spec sheet: 1.75 gpm at 80 psi for units made after 3/1/2018
  (2.0 before); finishes 26008 (chrome), 26008SRN. Read 2026-10-12.
  https://www.moen.com/products/Attract/Attract-Chrome-Magnetix-Rainshower-Combo/26008
- Moen 26010SRN product page: 1.75 gpm max. Read 2026-10-12.
- [AAF PerfectPleat HC M8 product data sheet](https://aafterms.aafintl.com/-/media/files/aaf/commercial-and-industrial/us-products/pleated-filters/perfectpleat-hc-m8/perfectpleat-hc-m8_prod_mark_sht_afp-1-210.pdf), read 2026-10-22: MERV 8, 10x10x1 nominal / 9.5x9.5x0.75 actual, rated airflow and initial resistance.
- Delta 52535-SS spec sheet (DSP-B-52535): 1.75 gpm at 80 psi, WaterSense, 1/2"-14 NPT.
- Delta TempAssure 17T Series listings: thermostatic trim for the MultiChoice R10000 body,
  separate volume and temperature controls.
- Panasonic FV-10NLF1E distributor listings (supplyhouse.com, platt.com): 120 cfm, 1.0 sone,
  4" duct, insulated housing; discontinued 2024-04-02. Read 2026-10-12.
- Airmada product literature: 70-115 cfm at 40-130 in. w.g. blowers; 5-7 h to dry an
  untreated shower (the plan of 2026-10-12).
- ASHRAE Fundamentals Ch. 6 (mass transfer, Lewis relation) and Ch. 21 (duct friction,
  fitting losses), for §7.2-7.3's coefficients.
- Swanstone Shower Wall Kits and Panels installation guide, "Surface Preparation". Read
  2026-10-22. https://res.cloudinary.com/american-bath-group/image/upload/websites-product-info-and-content/swan/product-info/walls/installation-guides/swan-wall-install-guide-shower-wall-kits.pdf
- Johns Manville GoBoard tile backer board (polyiso, waterproof core; ICC-ES ESR-4812). Read
  2026-10-22. https://www.jm.com/en/building-insulation/commercial/tile-backer-board
- `houses/catlin/out/model.json`: `rooms` (RM-M-BATH2 clear height), and
  `plan/mep_registers.py`, `plan/mep_erv_l2.py`, `plan/fixture_types_wc.py`.
