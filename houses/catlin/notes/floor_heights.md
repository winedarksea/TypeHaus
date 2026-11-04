# Catlin finished-floor heights and doorway details

Design schedule, 2026-09-28. Heights below are inches above each storey's top-of-joist
datum; the second-storey datum is 120 in above the main datum. A **flush** doorway has a
nominal difference no greater than **1/16 in**. The opening probes in
`tests/test_catlin_floor_height_schedule.py` sample on both sides of each hosted opening,
on the correct deck. Nominal heights are design targets; the installer must mock up and
measure compressed carpet edges and set tile elevations before fixing thresholds.

**Bedroom carpet, 2026-11-01 (owner; review C5-E5/E6):** no plywood. Sweet Spot I Romano
over a 3/8-in, 8 lb/ft³ Future Foam cushion is 1.000 in over the subfloor (0.56-in pile +
1/16-in backing allowance + 3/8-in cushion), so the carpet stands 1/4 in over the oak and
tile it meets. Each such doorway tucks the carpet into an aluminium Z-bar flush with the
hard floor, with no reducer. Every doorway product is named in `plan/doorway_transitions.py`
and graded by `integrity.doorway_assembly`. See [bedroom carpet](bedroom_carpet.md).

## Assemblies above the 3/4-in framed subfloor

**The subfloor is modelled at its 3/4-in nominal** (2026-11-01, review F3-009). The panel
bought is 23/32-in (0.71875-in) Performance Category plywood, 1/32 in thinner. Every
framed deck uses the same 0.75 (the whole main floor is wood since decision #112, 2026-11-01:
no cap), so no doorway spends the 1/32 in. The model keeps the nominal.

| Tag / location | Build-up above subfloor | Finished height |
| --- | --- | ---: |
| `oak-floor-custom`, second hall/linen/suite/study | 3/4-in site-milled oak | +1.5000 |
| `catlin-carpet-raised`, east bedrooms and main bedroom/closet | Sweet Spot I Romano (0.56-in pile + 1/16-in backing allowance) over 3/8-in rebond cushion; no plywood | +1.7500 |
| `catlin-tile-oak-height`, suite bath/vanity | 5/16-in nominal DITRA-XL + 5/16-in Marazzi Modern Formation MF01 24x24 matte porcelain + nominal 1/8-in combined mortar beds | +1.5000 |
| `catlin-tile-heated`, both heated baths | 1/4-in nominal DITRA-HEAT + same 5/16-in MF01 porcelain + nominal 3/16-in combined mortar beds, cable in studs | +1.5000 |
| `catlin-plant-vinyl-raised`, second plant | Nominal 1/4-in SurePly underlayment + 0.120-in fully adhered sheet; no floor drain or slope | +1.1200 at doorway |
| `lvp`, whole main floor | Karndean Cotton Oak AKP-RL38, 7.0 mm (0.27559 in) rigid core incl. backing, floating on the subfloor; no mat | +1.0255906 |

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

The 1/16-in carpet backing is an allowance: the published 0.56 in is pile only. Measure
the sample. The Z-bar answer below holds while the backing is 0.10 in or less.
Karndean Cotton Oak (7.0 mm incl. backing) replaces COREtec Quincy Oak 5 mm on 2026-11-01
(decision #112); no separate mat is specified or billed. Measure the installed plank; one
plank plane runs the whole main floor, with no concrete joint. Base cabinets with toe
kicks stand on the subfloor with the plank under the kick only; fridge, freezer, range and
dishwasher stand on the plank level (the dishwasher on a spacer).

See [Cotton Oak LVP](lvp_flooring.md) for the spec, install rules and alternatives.

## Opening schedule

All numbers are modeled finished planes, in inches above the relevant storey datum.
Carpet planes carry the 1/16-in backing allowance until the sample is measured. An edge
or movement joint may be required even where the modeled height difference is zero.

| Opening | Side A | Side B | Difference | Detail |
| --- | ---: | ---: | ---: | --- |
| `D-S-BED1`, `D-S-BED2`, `D-S-BED3` | carpet +1.7500 | hall oak +1.5000 | 0.2500 | Carpet tucked into a Z-bar flush with the oak; no reducer |
| `D-S-SUITE` | oak +1.5000 | oak +1.5000 | 0 | Continuous oak field |
| `D-S-SUITEBATH` | suite oak +1.5000 | porcelain +1.5000 | 0 | Schluter-SCHIENE tile edge, silicone joint to the oak |
| `O-S-VANITY` | hall oak +1.5000 | porcelain +1.5000 | 0 | Flush tile edge and movement joint |
| `D-S-BATH1` | hall oak +1.5000 | heated porcelain +1.5000 | 0 | Schluter-SCHIENE tile edge, silicone joint to the oak |
| `D-S-NCLOSET` | hall oak +1.5000 | oak +1.5000 | 0 | Continuous oak field |
| `D-S-STUDY2` | hall oak +1.5000 | oak +1.5000 | 0 | Continuous oak field |
| `D-S-PLANT` | study oak +1.5000 | raised sheet vinyl +1.1200 | 0.3800 | Solid-surface reducer over a sealed water stop; no drain |
| `D-M-MUD`, `D-M-MECH`, `D-M-MUDC` | LVP +1.0255906 | LVP +1.0255906 | 0 | One level field; keep expansion gaps; bottom guide at `D-M-MUDC` on flat substrate |
| `D-M-BED2` | hall LVP +1.0255906 | bedroom carpet +1.7500 | 0.7244094 | 5/4 oak saddle on the subfloor, top on the carpet plane under the leaf, 2-in bevel to the LVP; the automatic door bottom seals on it |
| `D-M-BED` | bedroom carpet +1.7500 | closet carpet +1.7500 | 0 | Continuous carpet stack |
| `D-M-BATH2` | bedroom carpet +1.7500 | heated porcelain +1.5000 | 0.2500 | Carpet tucked into a Z-bar flush with the tile |
| `ST-M2S` lower and upper head | main LVP +1.0255906 | second oak +1.5000 (+121.5000 absolute) | stair rise | 16 equal risers at 7.5296 in ((121.5 - 1.0255906)/16); level turn +61.2627953 absolute |
| `ST-S2A` lower head | second oak +1.5000 (+121.5000 absolute) | oak stair | 0 at head | Retain existing authored 121.5-in start |
| `D-M-ENTRY` exterior | mudroom LVP +1.0255906 | breezeway deck 0.0000 | 1.0255906 down | Flashed weather sill, **not** an interior reducer |

Use a restrained, shallow solid-surface reducer at the 0.3800-in plant change, sloping
down toward the vinyl over roughly 4 1/2 in of run. The wet-side sheet must turn up
and seal to a continuous water-stop riser beneath the reducer; seal its ends into the
jamb returns. A reducer without this sealed upturn provides no dependable spill
containment. Set the final profile from measured installed heights and check the
delivered glass door's swing and clearance. Use a securely retained tapered profile
at the 0.7244-in bedroom change, with no exposed sharp lip.

```text
study oak +1.5000  ─────────┐  solid-surface reducer ↘  plant vinyl +1.1200
                            │  ~4 1/2-in run for nominal 0.3800-in drop
sealed water-stop riser  ───┘  vinyl turns up beneath reducer and seals to riser
                                 seal both ends to jamb membrane returns
```

Anchor the reducer from the dry side or beneath its sealed cap; fasteners must not
puncture the wet-side vinyl upturn. This section is schematic until the delivered
door, subfloor and installed finish depths have been measured.
The resolved rooms on either side of `D-M-BED2` are `RM-M-LIVING` and `RM-M-BED`;
the earlier implementation plan described it as a closet-to-hall opening.

There is no living-room cap boundary and no movement joint (decision #112; the concrete
deck and `mixed_deck_movement_joint.md` are retired): the plank is one plane.
`ST-B2M` climbs 110.4630906 in over 15 risers (7.3642 in) to the plank top.

The scheduled interior openings contain **nine material changes** (three east carpet
doors, three upstairs bath openings, the plant door, the main bedroom entry and its bath
door). Six change height: the four carpet-to-hard doors by the carpet's 1/4 in, which the
Z-bar takes inside the carpet, and the two with a product, `D-S-PLANT` and `D-M-BED2`.

## Doorway transition products (2026-11-01)

`plan/doorway_transitions.py` names one per flooring change, each a design selection with a
schematic section, supplier PENDING. The rise in each section is the modelled step, so the
check fails if the floors move.

| Doorway | Change | Product |
| --- | --- | --- |
| `D-S-BED1/2/3`, `D-M-BATH2` | carpet 1/4 in over oak/tile | aluminium carpet Z-bar, no reducer |
| `D-M-BED2` | LVP up 0.7244 in to carpet | 5/4 site-milled oak saddle |
| `D-S-SUITEBATH`, `D-S-BATH1` | oak = tile | Schluter-SCHIENE |
| `D-S-PLANT` | oak down 0.38 in to vinyl | 12 mm solid-surface reducer over the water stop |
| `D-B-PLAY` | stall mat down 1/4 in to carpet | bevelled rubber reducer |
| `D-B-SAUNA` | stall mat down 3/4 in to the sealed slab | bevelled rubber reducer |
| `D-B-BATH` | sheet vinyl down 0.12 in to the slab | rubber reducer for 1/8-in sheet |
| `D-A-HALVES` | oak down 0.63 in to vinyl | site-milled 3/4-in oak reducer |

Still open: `D-A-STUDY` and `D-A-POCKET` open onto unfinished subfloor (no finish to pair
with), and `D-M-MECH`'s mechanical-room floor has no finish over part of the doorway. `D-M-STUDY` has plank on both sides
now: no reducer.

## Exterior entry section, schematic

```
       interior                          exterior / breezeway
  LVP top +1.0255906  ───┐  raised weather sill  ┌── composite deck 0.0000
  floating edge gap  →│  gasket / door sweep   │  open deck drainage ↓
  3/4-in plywood  ────┴─ sloped sill pan ──────┴── flashing drains outward
                      pan laps WRB at jambs and discharges past rim
```

Use a manufacturer-approved exterior door sill with an upstand above the LVP, a sloped
pan with end dams, and flashing that drains outward over the breezeway edge. Terminate
the floating plank with its required perimeter gap under a removable sill trim; do not
seal a drainage path shut. Set the sill height from the selected door system's instructions
and verify door sweep clearance after the plank is installed. The breezeway deck finishes at
0'-0" (`params/north_entry_frame.py` `DECK_FINISH_FT`; "bridge composite finish 0",
2026-09-11), 1.0255906 in below the LVP, so the step out is that drop plus the sill
upstand. The water path still relies on the sill and pan, not on floor-level fall. Use a removable boot mat or tray inside
the mudroom so standing snowmelt does not sit at floating plank seams.

`RM-S-PLANT` stays fully adhered sheet vinyl over one nominal 1/4-in SurePly layer.
The nominal remaining drop contains only incidental spills, and the room has no drain
and no automatic shutoff (owner, 2026-11-03). SurePly is an interior,
weather-protected underlayment, not a waterproof layer. Do not order the reducer until
the delivered underlayment and vinyl stack has been measured. The perimeter is a 4" rubber
cove base, not a flash cove, so the sheet stays inside Tarkett's guide; the 70%-RH
operating condition remains the owner's risk ([plant-room note](plant_room.md)).

## Estimate comparison

Historical comparison predating the 2026-10-23 bedroom selection. Its combined pad area
is now split between `carpet-pad` and `catlin-bedroom-carpet-pad`; the bedroom carpet
material allowance is now $3–4/SF. Totals below have not been repriced for that amendment.

`haus takeoff --json` against the previous room schedule and this schedule, using the
same engine, gave the following net/order areas in square feet:

| Finish or companion | Previous net / order | This schedule net / order |
| --- | ---: | ---: |
| LVP | 508.4 / 560 | 378.8 / 417 |
| Custom oak | 408.8 / 450 | 541.6 / 596 |
| Carpet, both stacks combined | 870.5 / 958 | 870.5 / 958 |
| Rigid carpet underlayment (dropped 2026-11-01) | — | 589.1 / 648 |
| Porcelain, all stacks combined | 205.4 / 237 | 202.2 / 233 |
| DITRA-HEAT | included at plain membrane rate | 137.9 / 159 |
| DITRA-XL | — | 64.3 / 74 |
| Plant-room SurePly | — | 137.5 / 155 |

The plant-room amendment adds **$217–$465** for 155 ordered SF of SurePly. Splitting
the same sheet vinyl into plant and shared rows adds one ordered square foot through
rounding, **$10–$20** at the existing rate. Together these add **$227–$485** to the
earlier floor-height optimization comparison. The current floor-finish subtotal is
**$25,580.35–$55,210.20**, versus **$22,718.90–$50,364.70** before that optimization.
The current whole-house takeoff is **$835,933.65–$1,725,035.25**; it also includes
other house changes since the original comparison and should not be attributed wholly
to this flooring amendment. These are estimate comparisons, not bids. Every new
companion row is priced; existing unrelated unpriced groups and unfinished room area
remain in the house estimate.

## Model review

The second-storey and main-storey plan renders show all scheduled rooms and openings.
The emitted glTF floor mesh bounds place the second hall, east bedrooms and heated hall
bath at +121.500 in absolute, and the main mudroom at +1.0255906 in. The living-room LVP
mesh tops at the same plane (the old cap is `FS-M-NE`, wood). The floor-height regression
probes sample both sides of each main opening;
stair arrival, riser uniformity, stair headroom and open-side guard checks remain in the gate.
