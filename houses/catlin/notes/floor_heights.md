# Catlin finished-floor heights and doorway details

Design schedule, 2026-09-28. Heights below are inches above each storey's top-of-joist
datum; the second-storey datum is 120 in above the main datum. A **flush** doorway has a
nominal difference no greater than **1/16 in**. The opening probes in
`tests/test_catlin_floor_height_schedule.py` sample on both sides of each hosted opening,
on the correct deck. Nominal heights are design targets; the installer must mock up and
measure compressed carpet edges and set tile elevations before fixing thresholds.

## Assemblies above the 3/4-in framed subfloor

| Tag / location | Build-up above subfloor | Finished height |
| --- | --- | ---: |
| `oak-floor-custom`, second hall/linen/suite/study | 3/4-in site-milled oak | +1.5000 |
| `catlin-carpet-raised`, east bedrooms and main bedroom/closet | 1/4-in rigid plywood underlayment + 1/4-in dense bonded cushion + 1/4-in nominal cut pile | +1.5000 |
| `catlin-tile-oak-height`, suite bath/vanity | 5/16-in nominal DITRA-XL + 5/16-in Marazzi Modern Formation MF01 24x24 matte porcelain + nominal 1/8-in combined mortar beds | +1.5000 |
| `catlin-tile-heated`, both heated baths | 1/4-in nominal DITRA-HEAT + same 5/16-in MF01 porcelain + nominal 3/16-in combined mortar beds, cable in studs | +1.5000 |
| `vinyl-sheet`, second plant | 0.120-in fully adhered sheet; local slope to drain is additional geometry | +0.8700 at doorway |
| `lvp`, main circulation/mudroom/closets | 0.2362-in SPC plank including attached pad; separately billed acoustic underlayment needs product approval and an installed height check | +0.9862 |
| `coated-concrete`, main living zone | cast cap top, coating adds no appreciable height | +0.9375 |

The Marazzi [product page](https://www.marazziusa.com/products/stone-look/modern-formation/peak-white)
specifies 5/16 in for the 24x24 matte tile. Schluter lists
[DITRA-XL at nominal 5/16 in](https://www.schluter.com/schluter-us/en_US/Membranes/Uncoupling-%28DITRA%29/Schluter-DITRA-%26-DITRA-XL/p/DITRA30M)
and [DITRA-HEAT at nominal 1/4 in](https://www.schluter.com/schluter-us/en_US/Membranes/Uncoupling-%28DITRA%29/Schluter-DITRA-HEAT/p/DITRA_HEAT).
The combined mortar depths above are project allowances, not manufacturer dimensions.
Check actual tile lot, trowel coverage, substrate flatness, second-storey truss deflection,
and the selected membrane's wood-subfloor detail. Waterproof DITRA seams and perimeters
where bath use calls for it. Do not replace the heated membrane with DITRA-XL. The
`floor_heat` estimate must be a **cable-only** quote; the DITRA-HEAT base is billed
once on the whole heated bathroom area by the floor-finish companion row.

The 1/4-in rigid layer under carpet is structural plywood, not a thicker cushion used as
a shim. The nominal 1/4-in pile is the existing catalog assumption. Compress the sample
at the actual door edge to confirm that its walking plane meets oak/tile within 1/16 in.
Confirm the LVP maker permits a separate mat below its attached pad. If it does not,
remove that takeoff companion before ordering. Measure the installed LVP/mat stack and
keep the mudroom and hall on the same stack; any height change at the concrete joint
must stay within this schedule's 1/16-in flush target.

## Opening schedule

All numbers are finished planes, in inches above the relevant storey datum. An edge or
movement joint may be required even where the height difference is zero.

| Opening | Side A | Side B | Difference | Detail |
| --- | ---: | ---: | ---: | --- |
| `D-S-BED1`, `D-S-BED2`, `D-S-BED3` | carpet +1.5000 | hall oak +1.5000 | 0 | Flush carpet edge/retainer, no ramp |
| `D-S-SUITE` | oak +1.5000 | oak +1.5000 | 0 | Continuous oak field |
| `D-S-SUITEBATH` | suite oak +1.5000 | porcelain +1.5000 | 0 | Flush tile edge and movement joint |
| `O-S-VANITY` | hall oak +1.5000 | porcelain +1.5000 | 0 | Flush tile edge and movement joint |
| `D-S-BATH1` | hall oak +1.5000 | heated porcelain +1.5000 | 0 | Flush tile edge and movement joint |
| `D-S-NCLOSET` | hall oak +1.5000 | oak +1.5000 | 0 | Continuous oak field |
| `D-S-STUDY2` | hall oak +1.5000 | oak +1.5000 | 0 | Continuous oak field |
| `D-S-PLANT` | study oak +1.5000 | sheet vinyl +0.8700 | 0.6300 | Drain-side wet-room doorway, reducer/raised water stop; coordinate cove and drain |
| `D-M-MUD`, `D-M-MECH`, `D-M-MUDC` | LVP +0.9862 | LVP +0.9862 | 0 | One level field; keep expansion gaps; bottom guide at `D-M-MUDC` on flat substrate |
| `D-M-BED2` | hall LVP +0.9862 | bedroom carpet +1.5000 | 0.5138 | One internal reducer, carpet edge securely retained |
| `D-M-BED` | bedroom carpet +1.5000 | closet carpet +1.5000 | 0 | Continuous carpet stack |
| `D-M-BATH2` | bedroom carpet +1.5000 | heated porcelain +1.5000 | 0 | Flush carpet/tile edge with suitable profile |
| `ST-M2S` lower and upper head | main LVP +0.9862 | second oak +1.5000 (+121.5000 absolute) | stair rise | 16 equal risers at 7.5321 in; level turn +61.2431 absolute |
| `ST-S2A` lower head | second oak +1.5000 (+121.5000 absolute) | oak stair | 0 at head | Retain existing authored 121.5-in start |
| `D-M-ENTRY` exterior | mudroom LVP +0.9862 | breezeway deck +1.0000 | 0.0138 | Weather sill, **not** an interior reducer |

Use a tapered, securely retained profile for the 0.6300-in plant and 0.5138-in bedroom
changes, with no exposed sharp lip. Confirm its run fits each door swing and the
plant-room water stop. Material-change edges at the level bath doors still need the
selected tile/carpet/oak manufacturer's termination and movement detail.
The resolved rooms on either side of `D-M-BED2` are `RM-M-LIVING` and `RM-M-BED`;
the earlier implementation plan described it as a closet-to-hall opening.

The coated-concrete/LVP living-room boundary is +0.9375 / +0.9862 in, a
0.0487-in difference within the same 1/16-in flush target. Keep the L-shaped edge and
the y=13-ft movement break described in `mixed_deck_movement_joint.md`.

The scheduled interior openings contain **nine material changes** (three east carpet
doors, three upstairs bath openings, the plant door, the main bedroom entry and its bath
door) but only **two height changes**: `D-S-PLANT` and `D-M-BED2`. The L-shaped
concrete/LVP boundary adds one material boundary with two legs and a movement joint;
it is a flush field joint rather than a doorway reducer.

## Exterior entry section, schematic

```
       interior                          exterior / breezeway
  LVP top +0.9862  ───┐  raised weather sill  ┌── composite deck +1.0000
  floating edge gap  →│  gasket / door sweep   │  open deck drainage ↓
  3/4-in plywood  ────┴─ sloped sill pan ──────┴── flashing drains outward
                      pan laps WRB at jambs and discharges past rim
```

Use a manufacturer-approved exterior door sill with an upstand above the LVP, a sloped
pan with end dams, and flashing that drains outward over the breezeway edge. Terminate
the floating plank with its required perimeter gap under a removable sill trim; do not
seal a drainage path shut. Set the sill height from the selected door system's instructions
and verify door sweep clearance after the plank is installed. The nearby exterior deck
being nominally 0.0138 in higher than the LVP is precisely why the water path must rely
on the sill and pan, not floor-level fall alone. Use a removable boot mat or tray inside
the mudroom so standing snowmelt does not sit at floating plank seams.

`RM-S-PLANT` stays fully adhered sheet vinyl. The [plant-room note](plant_room.md) and
`plans/TODO.md` still require written confirmation that the selected Tarkett First Class
sheet may be flash-coved. Do not raise its substrate or remove the doorway reducer until
drain, cove, adhesive and threshold compatibility have been detailed together.

## Estimate comparison

`haus takeoff --json` against the previous room schedule and this schedule, using the
same engine, gave the following net/order areas in square feet:

| Finish or companion | Previous net / order | This schedule net / order |
| --- | ---: | ---: |
| LVP | 508.4 / 560 | 378.8 / 417 |
| Custom oak | 408.8 / 450 | 541.6 / 596 |
| Carpet, both stacks combined | 870.5 / 958 | 870.5 / 958 |
| Rigid carpet underlayment | — | 589.1 / 648 |
| Porcelain, all stacks combined | 205.4 / 237 | 202.2 / 233 |
| DITRA-HEAT | included at plain membrane rate | 137.9 / 159 |
| DITRA-XL | — | 64.3 / 74 |

The floor-finish subtotal rises from **$22,718.90–$50,364.70** to
**$25,353.35–$54,725.20**, a change of **+$2,634.45–$4,360.50** at the authored unit
rates. The corresponding whole-house estimate moves from
**$831,599.98–$1,717,088.39** to **$834,480.65–$1,722,092.85**. The whole-house
change is **+$2,880.67–$5,004.46**, including the revised cable-only heating rate.
These are estimate
comparisons, not bids. Every new companion row is priced; existing unrelated unpriced
groups and unfinished room area remain in the house estimate.

## Model review

The second-storey and main-storey plan renders show all scheduled rooms and openings.
The emitted glTF floor mesh bounds place the second hall, east bedrooms and heated hall
bath at +121.500 in absolute, and the main mudroom at +0.9862 in. The main living-room
LVP mesh also tops at +0.9862 in on its wood deck despite the room centroid lying over
the coated cap. The Catlin check report has zero FAIL findings after the stair arrival
change; riser uniformity, stair headroom and open-side guard checks remain in that gate.
