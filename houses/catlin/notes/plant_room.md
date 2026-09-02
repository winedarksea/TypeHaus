---
title: "Plant Room — permanent high-humidity design (RM-S-PLANT)"
applied_to:
  - room: RM-S-PLANT
  - assembly: PLANT_EXT_2X6_HUMID
  - assembly: PLANT_INT_2X6_BRG_HUMID
  - assembly: PLANT_INT_2X4_HUMID
  - transition: TR-CATLIN-PLANT-OPENING
  - transition: TR-CATLIN-PLANT-RIM
  - register: REG-S-ERV-PLANT-EXH
  - duct: DU-S-PLANT-EXH
tags:
  - building-science
  - vapour-control
  - humidity
  - ventilation
  - electrical
source:
  - plan/assemblies.py
  - plan/storeys/second.py
  - plan/storeys/main.py
  - plan/transitions.py
  - plan/mep_hvac.py
  - plan/mep_registers.py
  - plan/lighting_types.py
  - plan/mep_electrical.py
  - plan/electrical.py
---

# Notes

`RM-S-PLANT` is to be a tropical plant room held at **~75 °F / 70 % RH year-round**,
including Minnesota winters at the house's −15 °F heating design temperature. This closes
the "add the plant room wall types" item in `plans/TODO.md`.

The room is the second storey's SW corner, x 0'→18' × y 0'→9', 9'-0" ceiling. It is the
**worst location in the house** for this: two exterior walls, three windows, an exterior
French door, and a floor and ceiling that are wood I-joist systems shared with conditioned
space above and below.

A 70 %-RH room against −15 °F outdoor air is a natatorium-class vapour drive in a
residential shell. The failure mode is not visible — it is rot and mould inside the stud and
joist bays, discovered years later. Everything below serves one goal: **no moisture-
sensitive material ever sees moist room air.**

## The numbers that govern

At 75 °F / 70 % RH the room's **dew point is 64.4 °F**. Every surface colder than that is
wet.

| Surface | Winter temp at −15 °F out | vs 64.4 °F DP |
|---|---|---|
| Interior face of an R-44 wall | ≈ 73.6 °F | safe, +9 |
| Sheathing (condensing plane), as built | ≈ 25.5 °F | **−39 — catastrophic if vapour reaches it** |
| `WT-3048` glass, U-0.25 | ≈ 59.7 °F | **−4.7 — wet below about +13 °F outdoors** |
| `WT-3048-HP` glass, U-0.14 | ≈ 66.4 °F | +1.9 — dry to roughly −35 °F |
| Window frame / edge-of-glass | 5–8 °F below centre-of-glass | wet at any realistic setpoint |

Two conclusions fall straight out.

**You cannot insulate your way out of this.** Raising the sheathing to 64.4 °F would take
roughly **R-183** of exterior continuous insulation. The interior air + vapour barrier is not
belt-and-braces — it is the *only* thing preventing rot. It must therefore be continuous on
all six sides, sealed at every penetration, and **monitored**, because it has no redundancy.

**The glazing retype is necessary, not gold-plating.** As authored, the plant-room windows
condensed below about +13 °F outdoors — most of a Minnesota winter.
`building_science.glazing_dew_point` is the rule that says so, and it now prints the margin
for every one of the three units.

**Good news on the existing wall, and the truss wall does not change it.**
`CATLIN_EXT_2X6`'s exterior insulation was 2" polyiso (1.0 perm-in, 0.5 perm at 2") plus 2"
EPS (3.9 perm-in), which ran ≈ 0.4 perm — Class II, slow but real outward drying. It is now
4" of 2 lb closed-cell spray foam at 1.6 perm-in, which runs **≈ 0.4 perm: the same Class II**,
in one bonded seamless application instead of two boarded courses and a sheet WRB. The wall
did not need re-engineering then and does not now.

The warning the boarded stack carried is moot rather than wrong, and is kept here because it
is why the foam's permeance is a spec line and not an incidental: **glass-faced or unfaced
polyiso, never foil-faced.** Foil-faced polyiso (the house's own `polyiso-foil`, 0.03 perm)
would have sandwiched the stud bay between two vapour barriers with wet-prone wood at 25 °F
in between — the one genuinely unrecoverable mistake available here, and the model would not
have caught it, because it carries the permeable number. There is no board in this wall any
more, so there is nothing left to specify wrongly; the sprayed foam's 1.6 perm-in is authored
in `library/materials.py` and the condensation gate reads it directly.

**RH strategy.** Hold 70 % whenever outdoors is ≥ +10 °F; below that, reset the setpoint down
to ~55 % at −15 °F. With the HP glazing this is a comfort/safety margin on the frames rather
than a necessity, and it keeps a genuinely tropical room for ~95 % of the winter. 60 % is the
agreed fallback if any of this proves too costly; nothing in the design changes if you run it
at 60 %, it only gains margin. The model carries the *design* figure — 75 °F / 70 % — because
that is the condition the assemblies have to survive.

## The design — a six-sided sealed liner

The whole room is one continuous membrane envelope. Named surfaces, and the transitions
between them, matter more than any single material.

### Walls

Three new assemblies, following the **sauna precedent exactly**: the humid side is its own
wall *type*, not a `Room.wall_lining` override. That is deliberate three times over — the
liner changes the wall's thickness (a lining override may not), an asymmetric wall needs
`interior_room` to say which face it lands on, and only a type is a thing the condensation
walk and the humid-room checks can see.

The shared liner (`_HUMID_LINER` in `plan/assemblies.py`), interior → exterior:

| layer | thickness | function | control |
|---|---|---|---|
| `pvc-panel` | 1/2" | FINISH | — |
| `liner-furring` | 3/4" | FURRING | — (drainage + drying gap) |
| `humid-membrane` | ~0.04" | MEMBRANE | **VAPOR + AIR** |

and the three assemblies that carry it:

| tag | where | outboard of the liner |
|---|---|---|
| `PLANT_EXT_2X6_HUMID` | `W-S-S1`, `W-S-W4` | the whole `CATLIN_EXT_2X6` stack |
| `PLANT_INT_2X6_BRG_HUMID` | `W-S-C1` (x=18' bearing line) | 2x6 + gypsum on the study side |
| `PLANT_INT_2X4_HUMID` | `W-S-PS1`, `W-S-PS2` | 2x4 + gypsum on the study side |

Three things about this that will bite if missed:

- **`INT` is a whole `_`-delimited token** in the two interior tags. `mn_energy.py` splits on
  `_` to decide whether a wall is interior; without it, an interior partition is graded
  against R-21 as though it faced the weather.
- The exterior walls keep `alignment=face("sheathing-ext")`, so the sheathing datum does not
  move (decision #43). **The liner grows inward**, exactly as `W-B-CS` does for the sauna.
- The liner costs ~1 1/4" all round — about 7 sf of floor (159.2 → ~152 sf). Harmless here:
  the room has no egress duty and a smaller floor *improves* the R303.1 glazing ratio. The
  window and door jamb returns all deepen by that amount.
  **The model does not yet show that.** `resolve/rooms.py::_lining_inset` insets a room's
  claimed face by one uniform figure (0.635", the painted-gypsum stack) rather than by each
  bounding wall's own lining, so `RM-S-PLANT` still resolves at 159.15 sf — exactly as the
  sauna's 3 1/2" liner fails to move its own room polygon. Systemic and pre-existing;
  `plans/TODO.md` carries it.

### FRP is disqualified; PVC is the panel

Nudo's own product limitations state that FRP "should never be exposed to extremely high or
extremely low moisture conditions", must be installed at 60–75 °F and 35–55 % RH, and
"should never be directly installed over studs" — non-compliance **voids the warranty**.
Trusscore-class solid PVC is the opposite: 1/2" tongue-and-groove interlocking, concealed
screw flange, mounts direct to furring with no cellulose substrate, third-party mould-tested
to ISO 846, explicitly marketed for indoor grow rooms.

### The panel is *not* the vapour barrier

This is the single most important correction in the whole design, and it changes the
assembly from "panel = barrier" to "panel = liner, membrane = barrier".

No FRP or PVC manufacturer — Crane, Marlite, Nudo, Trusscore, Extrutech — publishes a perm
rating. Neither does any sheet-vinyl maker. So the vapour control layer is a **separate,
continuous, sealed membrane behind the panel**, chosen because it *has* a published ASTM E96
number.

The model says so in the only way that is honest: `pvc-panel` and `vinyl-sheet` carry **no**
`vapor_permeance_perms` at all (per the convention in `library/materials.py`), and
`humid-room-membrane` carries 0.05 perm with its basis in `source=`. That value is authored
as a **specification** — the loosest the submitted product may test at and still be Class I
with margin — not as a reading off one datasheet.

All three live in `library/materials.py`, not in this house. They were authored here first
and promoted the same day (CONTRIBUTING §Promotion flow): none of them carries a project
coordinate, an owner choice or a house-specific dimension, all three are ordinary catalog
products with stable tags — and `takeoff/finishes.py::_WASTE` is *engine* code that names
`vinyl-sheet`, which an engine table may not do for a material only one house defines.

The Glaser walk therefore starts at the membrane, not at the panel: `glaser_layers` now trims
a room-side ventilated cavity the same way it has always trimmed an exterior rainscreen. That
is both the honest scope (the gap behind the panel is at room conditions) and the conservative
one (the panel's own vapour resistance is credited at nothing).

### Ceiling — modelled

PVC panel on furring over the same membrane, continuous with the wall membrane at the
perimeter. **No suspended/tile ceiling** — natatorium guidance is explicit that the cavity
above one reaches at least the room's humidity ratio and cannot be protected.

`FS-ATTIC` still carries no `ceiling_below` (it never needed one: nothing else sits under
it with a ceiling of its own), so authoring the liner here needed a room-scoped override —
`Room.ceiling_lining`, the per-room ceiling construction added alongside the general
ceiling pipeline (`resolve/ceilings.py`). `RM-S-PLANT` authors the same three layers as the
wall liner (`pvc-panel`, `liner-furring`, `humid-membrane`), restated in
`plan/storeys/second.py` since the editable dialect cannot import `assemblies.py`'s
`_HUMID_LINER`. `building_science.humid_room_liner`/`_finish` now grade the ceiling exactly
as they grade the walls, closing the gap this section used to record.

### Floor

Heat-welded sheet vinyl (`vinyl-sheet`, new) with a **6" integral flash cove** that laps up
the wall and terminates *behind* the wall membrane, so floor and wall become one tray. This
is the single highest-value detail in the room: it eliminates the base joint, the most
failure-prone interface in any wet room. Slope to a floor drain — the room should be
hoseable.

**Do not put roofing membrane under the vinyl.** Sheet vinyl is already effectively Class I;
a second impermeable layer beneath it creates a classic moisture sandwich around the plywood
subfloor with no drying path in either direction, and no sheet-vinyl adhesive is qualified
over TPO/EPDM. **The cove *is* the waterproofing.**

### Openings

- `WIN-S-PLANT1/2/3` are retyped to `WT-3048-HP`, `WT-3048-HP-T` and `WT-2736-HP`: identical
  dimensions, better glass (U ≈ 0.14), warm-edge spacer, thermally broken frame. This follows
  the established `-T` tempered-twin precedent — *adding a better unit is a retype, never a
  move* — so no facade or framing rule is disturbed. `WIN-S-PLANT2` stays tempered (within
  24" of `D-S-DECK-W`), which is why there is a fourth type rather than a choice between the
  two properties.
- **Drained sill pan** under each unit: sloped, flashed into the wall membrane, draining to
  the room, never into framing. Drawn by `TR-CATLIN-PLANT-OPENING`.
- **Keep the glass-wash airflow.** `REG-S-HP-PLANT`'s throw washes the south glass, and that
  function survives the damper retype below.
- **`D-S-DECK-W`** is a 60" exterior French door in a 70 %-RH room. Spec an insulated,
  thermally broken, gasketed unit with a drained sill; **expect condensation on the
  threshold**. Whether balcony access should pass through this room at all is an open
  decision (below).
- Every opening returns the membrane into the jamb — `TR-CATLIN-PLANT-OPENING`, cloned from
  `TR-CATLIN-SAUNA-OPENING`. Butting the panel at the jamb is not sealing it.

### Penetrations and the rim joists

Every hole is a hole in the only barrier.

- **The rim joists are the hardest detail in the room.** `FS-SECOND` and `FS-ATTIC` joists
  run in `x`, so their **ends bear on `W-S-W4`** and a parallel rim bay sits against
  `W-S-S1`. Both are direct paths from a floor cavity into the coldest part of an exterior
  wall, and neither can take a sheet membrane. **Closed-cell spray foam at the rim** in both
  floor systems along both walls: bonded, monolithic, no seams, and its own vapour retarder.
  Its own sheet, `TR-CATLIN-PLANT-RIM` — everywhere else in this house the rim band is an air
  seal at 35 % RH, and here it is the continuity of a Class I barrier at 70 %.

  It is also its own **`ConstructionRule`**, `CR-PLANT-RIM-FOAM`, and that is not
  bookkeeping. A `Transition` documents and cannot bill (#45), so the detail sheet alone
  would have drawn foam that no takeoff ever ordered. The rule bills it: 54 LF (both walls'
  shared run × both floor bands) of 3" closed-cell foam, through the new
  `wall:rim_cavity_foam` finder in `resolve/construction_rim.py`. Adding it turned out to
  need `construction_returns` to become a *priced* section at all — until now every return
  in that table was a lap of material some other table already bought, and foam in a rim
  cavity is in no assembly and no other table.
- **`FX-S-BALC-HYD` pierces `W-S-S1`** — a wall hydrant whose escutcheon is outdoors, plus
  `PA-S-BALC-HYD-SEAT` behind it. A freeze-proof hydrant body passing through the liner into
  a −15 °F wall is both a vapour leak and a cold surface. Needs a sealed, insulated sleeve
  detail (`plans/TODO.md`).
- Electrical boxes, the `ED-S-PLANT-LT` fan-light, the grow-tube suspension points and the
  register boots are all vapour-tight or gasketed to the membrane.
- **Cavity "canary" RH sensors** in a south and a west stud bay. The liner has no redundancy;
  this is how a failure is caught in month three instead of year five. Cheap, and it is the
  difference between a maintainable design and a hopeful one. (`plans/TODO.md` — the model
  has no element kind for a sensor.)

## Ventilation, pressure and humidity control

**The arrangement was backwards.** `REG-S-HP-PLANT` was a supply-only terminal, so System 1
*pressurised* a 70 %-RH room, driving moist air into every crack in its envelope — and
`DU-S-HP-SOUTH` ties the room's air to the whole-house air handler and every other room on
that branch. `mep.humid_room_pressure` is the rule written for exactly this, and it FAILed the
house until the extract below existed.

What is built now:

1. **Neutral-to-slightly-negative pressure**, per natatorium practice (−0.05 to −0.15 in.
   w.g. relative to adjacent spaces). Slightly negative means house air leaks *in* —
   harmless — and plant-room air never leaks into a wall cavity.
2. **Matched extract**: `REG-S-ERV-PLANT-EXH` (25 cfm), at the far end of the room from the
   supply, **high**, because humid air stratifies and the wettest air in the room is the air
   overhead. Its radial has moved twice since this note was written and the terminal moved with
   it the second time — see the addendum at the end.
3. **Motorised isolation damper** on the System 1 terminal (`REG-T-HP-SUP-DAMPERED`), so
   System 1 can neither dry the room nor carry its moisture house-wide.
4. **RH-driven control** — none of this self-regulates humidity.
5. **A humidifier is required regardless.** Even an 84 %-latent ERV loses ~16 % of the
   moisture in every air change. At this flow against −15 °F outdoor air, unrecovered loss is
   on the order of **1.5–2 gal/day**. An ERV is damage limitation, not humidity control.

### Why a dampered branch and not a through-wall unit

A dedicated ERV was considered and rejected. The Pioneer ECOasis 50 (`ERV050AHRMCO2L`) is
**out of spec for this house**: minimum ambient −4 °F against a −15 °F design temperature; a
stated design limit of "relative humidity below 80 %", which puts the target at the edge;
6–15 CFM in actual recovery mode (the 29–35 CFM figures are one-way, no-recovery modes); no
published latent recovery, no humidity sensor, no condensate drain. Worst of all a single
unit is **unbalanced** — it alternates supply and exhaust on 75-second half-cycles,
pressurising and depressurising the room, which is precisely the thing that destroys the
envelope. Balanced operation needs two units, i.e. two more holes through the exterior wall.

The house already owns a proper ERV in a mechanical room with a condensate drain and real
frost control. "Separate from the house ERV" is best achieved with an independent *damper*,
not an independent *machine* — the pattern the sauna already establishes with
`REG-T-ERV-SAUNA-SUP`/`-EXH`.

*If true isolation is still wanted*, the right product is the **Panasonic WhisperComfort 60
(FV-06VE1)** — the only US-available unit in this class publishing latent performance (net
moisture transfer 0.7 @ 20 CFM, ASRE 73 %) — accepting that it closes its supply damper below
14 °F and reverts to exhaust-only.

## Electrical

Per NEC 2023, this is a **damp location** throughout and a **wet location** anywhere it is
misted or hosed.

- All luminaires **wet-location listed**, gasketed, corrosion-resistant housings. Standard
  "damp-rated" bath fixtures are inadequate in a room that condenses. `ED-S-PLANT-LT` is
  retyped to `ED-T-LT-FAN52-WET` (schedule mark N2).
- **Grow tubes must be UL 8800 listed** — NEC Article 410 Part XVI, added in the 2020 cycle,
  requires horticultural lighting equipment to be listed, and UL 8800 admits only damp- or
  wet-rated horticultural luminaires. `ED-T-LT-TUBE6` (mark F) now states both.
- `ED-S-PLANT-RC1..RC5`: **WR-listed, GFCI, in-use ("bubble") covers**, non-metallic gasketed
  boxes — `ED-T-RECEPTACLE-WR-GFCI`. In-use covers everywhere, because pumps, heat mats and
  the humidifier stay plugged in permanently and a flip lid is only weather-tight with
  nothing in it.
- **Lighting stays on a separate, non-GFCI circuit** (`CKT-LT-UPPER`) from the receptacles
  (`CKT-RC-SECOND`, GFCI at the device per the house convention). Both halves of that matter:
  grow-light drivers have leakage currents that nuisance-trip GFCIs, and a trip on the pumps
  must not take the photoperiod down with it.
- Bare steel and standard EMT will rust at 70 % RH.

## What the checks now say

`haus check houses/catlin --only all`:

- `building_science.condensation` reports `PLANT_EXT_2X6_HUMID @ RM-S-PLANT` **at 70 % RH**
  against the humid liner and passes the monthly gate — tightest plane 75 % RH, 577 Pa below
  saturation, warm-side retarder named as `humid-membrane`, Class I.
- `building_science.humid_room_liner` passes on all five bounding walls and the ceiling,
  naming `humid-membrane` at 0.050 perm on the room side of each core.
- `building_science.humid_room_finish` passes on all six surfaces — no paper-faced gypsum
  shows.
- `building_science.glazing_dew_point` passes all three windows by 1.9 °F **at the centre of
  glass**, and says in the finding that the frame and edge run 5–8 °F colder. That margin is
  the whole reason the frame spec, the sill pans and the glass wash are not optional.
- `mep.humid_room_pressure` passes now and FAILed before the extract existed.

## Open items

1. **`D-S-DECK-W`** — keep balcony access through the plant room, or relocate it? It is a
   60" exterior French door in the wettest room in the house, and its threshold will
   condense.
2. **Floor drain** — confirm. It implies a drain line, a trap primer (the trap *will* dry),
   and slope in `FS-SECOND`.
3. **KERDI-BOARD's 0.48 perm** and the **Pioneer/Blauberg latent recovery** figures are
   secondary-source or unpublished. Verify with the manufacturers if either becomes
   load-bearing for a decision.
4. The membrane's 0.05 perm is a **specification**, not a submittal. Replace it with the
   selected product's own ASTM E96 number and source when one is chosen.
5. `[construction_returns]` in `prices.toml` deliberately leaves `pt-sill-plate` and
   `resilient-channel` unpriced: whether either is a *separate purchase* or a second count
   of lumber another table already bought is a question for whoever authored those rules,
   and guessing in either direction would be worse than the blank. The reasons are written
   into the file beside the blanks.

## Addendum, 2026-08-29 — the extract moved, and the terminal with it

`DU-S-PLANT-EXH` is now **`DU-M-ERV-R-PLANT` on the LEVEL-2 manifold** (`EQ-M-ERV-MAN-EXH`,
which this fills to 10 of 10). Same uid throughout.

**The second move was not about air.** The attic route ran the x=1'-0" deck chase for 21'-8"
along the base of what had become a finished guest bedroom's knee wall — the last duct there,
and the whole reason that wall was carrying a joinery allowance. The run now goes south through
**`FS-S-WEST`'s open-web trusses** at x=2'-10", east along the y=4'-8" bay, and **up inside
`W-S-C1`** to a high sidewall grille at 8'-6".

**Why the trusses and not the attic joists.** Both floors span x, so a north-south run crosses
every joist in either. `FS-S-WEST` is 11 7/8" open-web truss, chosen in `params/second_deck.py`
precisely so crossings go through the webs; `FS-ATTIC` is I-joist, where the same crossing at
x=1'-0" means ~16 bored webs, every one of them within a foot of the joists' west bearing —
which is the one place the hole chart does not allow.

**Why `W-S-C1` and not `W-S-PS1`.** The riser needs a cavity that takes a 75 mm duct *and* a
vapour-tight boot through the Class I liner. `W-S-C1` is `PLANT_INT_2X6_BRG_HUMID`, 7.43" with a
5 1/2" cavity. The room's north wall `W-S-PS1` is `PLANT_INT_2X4_HUMID` at 5.42" — the duct
would fit and the boot would not, and a boot that cannot be sealed is exactly the penetration
this whole note exists to prevent.

**Ceiling → high sidewall does not give up the stratification argument**, which was about
*height*, not about which direction the boot arrives from. 8'-6" is six inches under the 9'-0"
ceiling. Separation from `REG-S-HP-PLANT` improves from 5'-9" to 6'-9".

**Length went 47'-5" → 55'-8"**, of which 9'-4" is the rise. That is affordable, and the reason
is a correction worth carrying: **the machine's rating point is 0.4" w.g., not the 0.2" that
several comments in `plan/mep_erv.py` still quote.** HVI certifies the Broan B210E75RT at 206
cfm net supply at 0.4" (HVI ID 2004940); 210 cfm at 0.2" is the model-name point off the
manufacturer's fan curve.

**Two corrections to "Why a dampered branch and not a through-wall unit" above,** from a
re-check against primary sources. Both *strengthen* that section's conclusion:

- Its fallback suggestion, the **Panasonic WhisperComfort 60**, should not be used. The
  FV-04VE1 is discontinued and no longer in the HVI directory; the current FV-06VE1 closes its
  supply damper below 20 °F and runs exhaust-only roughly 75% of the heating season here.
- The **Lunos e2** is not the escape hatch either. Its own installation manual gives −15 °C to
  +40 °C — **+5 °F**, 18 °F above this site's design temperature — and instructs that on
  exceeding the range you shut the unit off and close the indoor blind. The "−32 °F" figure is
  distributor marketing with no test report behind it. Lunos is also not in the HVI directory.

The general finding: **every single-room unit in this class either cannot run at −15 °F or
defends against frost by unbalancing itself** (Panasonic below 20 °F, Zehnder ComfoSpot 50 below
+8.6 °F, and every reversing ceramic regenerator by design, on a 70–75 second beat — both
Blauberg and VENTS specify pairwise reverse-phase installation as the fix). For a room whose
entire envelope strategy depends on never being pressurised, that is disqualifying, and none of
them carries an HVI 916 rating Minnesota would credit anyway.
