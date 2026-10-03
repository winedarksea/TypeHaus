# The IKEA SEKTION ladder, and how this kitchen closes on it

Written 2026-09-11, when the kitchen was retyped from the generic `CASE-*` catalog onto
`library/placeables/sektion.py`. Later edits must check the exact width, depth and height
against the manufacturer; a dimension off the stock ladder needs an explicit custom type.

## What the house had decided, and what the model said

`plan/products_interior.py` has registered `PROD-IKEA-SEKTION` and `PROD-IKEA-VOXTORP-WH`
since 2026-09-06. Stock frames still use SEKTION, while seven deep uppers now have custom
carcasses with a coordinated finish. The original Section 232 argument made SEKTION the
choice: 25% on wooden cabinets from 2025-10-14, the scheduled 50% delayed to 2027-01-01, the
EU cap at 15%, and SEKTION's carcasses manufactured in the US and therefore insulated from
it.

The geometry did not agree. Every kitchen box was a `CASE-*` type on the generic US 3"
module, whose four governing constants were a **13" upper depth, a 42" upper height, a 96"
tall frame and a 12" stacker course**. None of those four is a SEKTION size. The widths
mostly were; the heights and the upper depth were not. So the estimate was priced against
boxes that could not be ordered, and the run arithmetic was defended to the sixteenth of an
inch on the wrong ladder.

## Finished-ceiling correction (2026-09-29)

The earlier 3" toe is below the [current SEKTION leg's 3 1/2" minimum](https://www.ikea.com/us/en/p/sektion-leg-for-cabinet-90556071/).
The [IKEA installation guide](https://www.ikea.com/us/en/files/pdf/49/6f/496ff2f6/kitchen_installation_guide_mar_2026.pdf)
also requires 1/2" above the wall-cabinet suspension rail to lift cabinets into place.
The former 108" tops entered the actual finished ceiling by 1 7/16". The owner approved
adjusting the stack and using standard legs where sensible; the low living-room cabinets
behind the kitchen retain their planned custom bases. The kitchen now uses a continuous
3 1/2" support. The high run is an 80" stock frame plus a custom 20"-high, 24"-deep
top box. The shallow counter uppers are stock 30" plus 20" frames above a 53 1/2" mount.
Both finish at 103 1/2", leaving just over 3"
below the finished ceiling and enough room to hang the rail. The over-fridge/freezer boxes
are custom 30"-high deep frames starting at 73 1/2"; the window upper is a shallow
30" stock frame at the same height. The first pair has exactly 1" above
the Frigidaire hinge; verify that fit on the appliance and cabinet shop drawings.

## The ladder

Verified 2026-09-11 against ikea.com/us and the IKEA US size guides:

| | values |
|---|---|
| Base frame | 30" high, 24" deep (23 5/8" without the suspension rail), 3/4" sides |
| Base widths | 12 / 15 / 18 / 21 / 24 / 30 / 36 / 38 / 47 |
| Wall heights | 15 / 20 / 30 / 40 |
| Wall depths | 15" shallow wall frames; limited 24" deep top frames |
| High frames | 80 / 90, in 15" and 24" depths |
| Legs | nominally 4 1/2", adjustable; FÖRBÄTTRA toe kick is a board cut on site |
| Drawer fronts | 5 / 10 / 15; MAXIMERA is the drawer box, low / medium / high |

Sources: [SEKTION base cabinet 36x24x30](https://www.ikea.com/us/en/p/sektion-base-cabinet-white-80265398/),
[SEKTION base cabinets](https://www.ikea.com/us/en/cat/base-cabinets-frame-height-23607/),
[legs, toekicks and plinths](https://www.ikea.com/us/en/cat/frames-rail-legs-toekicks-23615/),
[FÖRBÄTTRA toekick](https://www.ikea.com/us/en/p/foerbaettra-toekick-white-60266817/).

**Every stock frame height is a multiple of five, but depth and width availability differ.**
IKEA's [wall frame size list](https://www.ikea.com/us/en/p/sektion-wall-cabinet-frame-white-30265452/)
shows the 15"-deep widths; its [top cabinet range](https://www.ikea.com/us/en/cat/cabinets-for-built-in-appliances-23610/)
is narrower. No stock 18x24x20, 24x24x20, 30x24x30, 24x24x40 or 24x24x30 frame was found
in the US catalog on 2026-09-29. These are explicit custom millwork in
`plan/kitchen_deep_cabinets.py`, not SEKTION order items.

## The current stack-up: a 3 1/2" toe kick

The drawn 108" storey datum is not the finished ceiling underside: the latter is lower.
One leg height serves both runs so the toe kick does not step where the east tall bank meets
base `N3`:

```
tall    3.5 toe + 80 frame + 20 custom top box                 = 103.5
upper           30 wall  + 20 top, hung at 53.5               = 103.5
base    3.5 toe + 30 frame + ~1.319 build-up + 1.181 quartz  =  36
```

The substrate allowance is the difference to a 36" work surface, approximately 1 5/16";
dimension it with the selected quartz thickness and support detail. The 80" pantry frame
still has enough clear height for the 75" pullout rack.

Uppers hang at **53 1/2"**, leaving a 17 1/2" backsplash. The 83 1/2" top course clears
`WIN-M-KITCH`'s 78" head by 5 1/2".

## The two places the ladder does not close

Both are recorded here rather than quietly absorbed, because a later reader will otherwise
try to "fix" them.

**1. The mixer garage: confirm the narrow ceiling reveal.** It stands on the peninsula
carousel's 36" counter, wholly on the corner square since 2026-10-03. `FT-KIT-DEEP24-40` at 36" under `FT-KIT-DEEP24-30` at 76" tops at 106", about 9/16"
below the finished ceiling. The IKEA rail guide calls for 1/2" installation space, so
verify the actual ceiling and mounting detail in the field before ordering this box.

**2. The cold bay: 5 3/4" of filler, deliberately split.** The bay between the tall
cabinets is 65 3/4", exactly two Frigidaire column widths (32 7/8" each), which is why the
appliances divide it with no remainder. Two 30" custom frames over them are 60". The pair
is **ganged**, its joint landing on the appliance joint at 30'-1 3/4", so each end of the
bay takes a 2 7/8" scribe against a tall cabinet — rather than one 2 7/8" gap floating
between the two boxes where every eye in the room lands.

## What the retype deleted

* **`FURN-M-KIT-WE3`**, a 12" box hung over `WIN-M-KITCH-N`. Uppers went from 13" deep to
  15", so `FURN-M-KIT-WN1`'s return in the inside corner reaches 2" further west and that
  slot fell from 12 3/8" to 10 3/8". IKEA's narrowest wall cabinet is 12". The 10 3/8" is a
  scribed filler panel built in the plane of the upper fronts, and `LR-M-KIT-N-WE3` still
  lights the corner counter from under it. This restores the kitchen's own stated corner
  rule — the east run claims the inside corner and the north run yields at 33'-4", which is
  what the base run already does.
* **The cold run's stacker course.** Four boxes became two: a 30" frame at 73 1/2" lands on
  103 1/2" by itself, so `FURN-M-KIT-OVER-FRIDGE-ST` and `-FREEZER-ST` are gone and there is no
  joint at 8'-0" on that wall at all.
* **Two house-local types**, `FT-KIT-OVER-COLD-3278` and `FT-KIT-MIXER-GARAGE-24`. Both
  existed only because a number was unreachable on the generic catalog.

## Drawers

The TODO that started this asked about MAXIMERA. It is registered as `PROD-IKEA-MAXIMERA`
and it is a **product, not a geometry**: the model has one solid carcass per cabinet and no
drawer vocabulary at all, so which boxes are drawer stacks is prose, recorded in
`prices.toml`'s SEKTION block and beside the instances in `plan/placeables.py`.

MAXIMERA is the full-extension soft-close box; FÖRVARA is the basic one a SEKTION base ships
with if nobody chooses. Fronts sit on the 5/10/15" ladder, so a 30" base is 5+10+15 or
10+10+10 and the fronts line up across a run either way. It fits every base and pantry width
in this kitchen; the two it does not fit are a 12" base and a corner base, and this house
has neither.

## What did NOT change (2026-09-11)

The north sink run's composition. `5/8" scribe + B15 + DW + SINK-36 + B30 = 105 5/8"`, pantry
wall to corner, with the 36" sink base dead-centred under `WIN-M-KITCH`. Every one of those
widths was already on the SEKTION ladder, so the retype vindicated the arithmetic rather
than moving it. (The B30 became a B15 + filler on 2026-10-02, and the 5/8" scribe went into
the pantry on 2026-10-03; both below.) The peninsula's knee is graded by
`advisory.countertop_overhang`; it is 11 5/8" today.

## The east wall, carousel corners and the SEKTION peninsula (2026-10-02)

**15"-deep bases.** IKEA US lists SEKTION base frames at a 15" system depth (15 3/8" actual)
in 15/18/24/30/36 widths, read 2026-10-02 (e.g. 24x15x30, 18x15x30 configured listings).
The library carries them as `SEKT-B{15,18,24,30,36}-D15`, 15 1/2" with fronts, 36" nominal
like every base. On the living-room run: 3 1/2" leg + 30" frame + 1/2" sub-top + 2" oak = 36".

**The composition**, south to north on W-M-E1 (y in inches):

    6 5/8   2 1/8 scribe | B24 8 3/4-32 3/4 | B30 -62 3/4 (E1 +1/4) | B18 -80 3/4 | 1/2 panel | brick 81 1/4
    126 3/4 1/2 panel | B18 -145 1/4 | B30 -175 1/4 (E2 +1/4) | B30 -205 1/4 | B36 -241 1/4 (MID -3/4) | B18 -259 1/4 | 1/2 scribe

The B18s sit at 104 -/+ 32 1/4 and the window B30s at 104 -/+ 56 1/4: mirrored about the brick.
A B30 under EAST-MID too would leave 34" between it and E2's, which no stock width fills.

**Corner base.** `SEKT-CORNER-B38`: 38x38, 24"-deep legs, a 14" notch, sold with a carousel and
a 13"+13" bifold (IKEA s79582533 / s89506379). The type carries an L `footprint_shape` off the
glyph's own ring (`sektion_corner_points`), and `carcass_depth` is a leg's 24".

**Kitchen arithmetic after the corners.** North: 5/8 + B15 + DW + SINK-36 + B15 + 2 3/8 filler +
38 leg. East: peninsula corner (outer corner y=317 3/8) + 1 + range 30 + 1 + NE corner 38 = to
425 3/8. Landings 14" south / 38" north. Peninsula: 1/2 panel + B36 + B24 + B24 = 84 1/2, on the
82 5/8" floor anchoring frame. Uppers: W24 between the garage (5/8 scribe) and the hood; WN1
W30 -> `SEKT-W36-30`, 3" to the hood.

## Take two: fillers, a symmetric fireplace and a 2" peninsula move (2026-10-03)

**Filler policy.** A width the ladder cannot reach takes a FILLER, and a filler is an
element: a FÖRBÄTTRA strip site-cut from a 25x80 panel and faced to match the fronts, 34"
tall like the end panels (`FT-KIT-FILLER-2375`, `FT-LIV-E-FILLER-2125`, `FT-LIV-E-FILLER-050`
in `plan/living_east_run_types.py`, each priced). IKEA ships a filler piece with its corner
bases for exactly the NE-carousel spot. A filler is a countertop host, so the slab is cut
straight over it. A scribe is used only where something else cannot move, and this pass
removed the one the north run had: the pantry partition moved 5/8" east instead.

**Living room**, mirrored about the brick (y=104"). E1 moved to 64", so E1 and E2 stand at
104 -/+ 40 and each window's unit centres 1 1/4" off its window, away from the brick:

    6 5/8   2 1/8 filler | B36 8 3/4-44 3/4 | B36 -80 3/4 (E1) | 1/2 panel | brick 81 1/4
    126 3/4 1/2 panel | B36 -163 1/4 (E2) | B15 -178 1/4 | B30 -208 1/4 (E3) | B15 -223 1/4 | B36 -259 1/4 | 1/2 filler

The north bank is symmetric about E3 (193 1/4 = 192 + 1 1/4).

**North run.** `B15 + DW + SINK-36 + B15 + 2 3/8 filler + 38 leg`, from W-M-PAN-E's face at
295" (moved 5/8" east, so the pantry is 70 7/8" clear) to the east wall. The sink did not move.

**East run.** The peninsula moved 2" north (carcass y 319 3/8..343 3/8), so the range is
FLUSH between the two carousels (357 3/8..387 3/8): no fillers at the range. The mixer garage
stands wholly on the peninsula carousel's corner square (y 319 3/8..343 3/8), the support box
is deleted, and so is `FURN-M-KIT-WN3`: between the garage and the hood only 14" is left, and
no 30" upper is that narrow. The 14" landing is lit by `ED-M-KITCH-CAN4`.

**Peninsula.** The knee is 11 5/8" (34% of 34"), so the oak bar top is the design, not one
alternative; it runs 122 1/2" to the east wall and dies into the tall bank's north side. The
stools stay on the west 98 1/2": along the east 24" the tall bank stands where a stool would.

**The two places the ladder does not close** are still the two above: the mixer garage's
ceiling reveal and the cold bay's split filler.

