# IKEA SEKTION order — rules and three hand counts

Revision 2026-10-30. Oracle for `library/placeables/sektion_parts.py` and for
`haus order houses/catlin --brand IKEA`. Article numbers and prices are in
`plan/products_ikea.py` and `prices.toml`. This note holds the counting rules.

## Rules

| Part | Rule | Source |
|---|---|---|
| Fronts across | One front up to 24 in. wide, a pair above that | IKEA sells no door wider than 24 in. |
| Door hinges | 2 for a door up to 40 in., 3 up to 60 in., 4 above | IKEA planner output. The Mar 2026 installation guide prints no chart; IKEA's VALLSTENA 50 in. door listing says "to be used with 3 hinges", which matches the 60 in. step. **Confirm the 4 above 60 in. with the planner at order.** |
| Lift-up front | One UTRUSTA horizontal hinge pair (804.654.15) | IKEA's 24x24x15 top configuration |
| Knobs | One per door or lift front | Owner, 2026-10-22 (BAGGANÄS 903.384.17) |
| Pulls | One per drawer front | Owner, 2026-10-22 (BAGGANÄS 803.384.13); the bed desk too, owner 2026-10-30 |
| Legs | 4 per floor-standing frame; 6 from 30 in. wide | **Assumed.** IKEA publishes no count. Legs may be shared at a joint, so this rule over-orders. |
| Toe kick | The frame's width, rounded to 84 in. sticks per touching run | FÖRBÄTTRA 602.668.17, 84 in. |
| Suspension rail | The frame's width, rounded to 84 in. sticks per touching run | 602.615.27. Not used under the peninsula, which stands on the floor anchoring frame. |
| Shelves | Enough that no bay is taller than 20 in.: ceil(h/20) − 1 over each unbroken stack of door courses (a door split is not a shelf; a drawer breaks the stack). A high frame's fixed shelf counts toward this. None behind a sink. | House rule. An authored count overrides it where an insert fills a bay. |
| Drawers | One MAXIMERA per drawer front: a 10 in. front takes a medium, a 15 in. front a high | MAXIMERA front ladder |

**Runs.** Frames on one storey whose footprints are within 1/2 in. of each other form one
run. The run's length is rounded up to whole sticks (`takeoff/placeables.py`). Splicing
a run is allowed; carrying an offcut from one run to another is not.

## Hand counts

**SEKT-SINK-B36 (`FURN-M-KIT-SINKBASE`)**
- **Frame:** 802.653.98 (the B36 frame).
- **Doors:** 36 in. is wider than 24 in., so two 18x30 AXSTAD doors (004.260.55).
- **Hinges:** 2 × 2 = 4 UTRUSTA 805.248.82, which is 2 packs.
- **Knobs:** 2, one pack.
- **Legs:** 6, because the frame is 36 in. wide. That is 3 packs.
- **Toe kick and rail:** 36 in. each, taken from the north run's sticks.
- **Shelves:** none, because the bowl takes the bay.

**SEKT-B24 drawer base (`FURN-M-KIT-PEN-B24-W`)**
- **Frame:** 902.653.88.
- **Drawers:** three 10 in. drawer fronts, so three AXSTAD 24x10 fronts (504.260.67) and three MAXIMERA medium 24x24 drawers (802.656.66).
- **Pulls:** 3.
- **Legs:** 4.
- **Toe kick:** 24 in.
- **Rail:** none, because the base is in the peninsula.
- **Not used:** no hinges and no shelves.

**SEKT-HIGH18-90, aligned (`FURN-M-KIT-PANTRYC`)**
- **Frame:** 002.654.39.
- **Doors:** 18x30 (004.260.55), 18x40 (804.260.56) and 18x20 (304.260.54).
- **Hinges:** 2 + 2 + 2 = 6, which is 3 packs.
- **Knobs:** 3.
- **Shelves:** the three doors are one 90 in. stack, so ceil(90/20) − 1 = 4 shelves (bays of 18 in.). Take away the frame's fixed shelf and 3 UTRUSTA 18x24 shelves (202.655.32) remain, which is 2 packs. (Counting per door course gave 1 + 1 + 0 = 2 and left 30 in. bays, because nothing stands at a door split.)
- **Legs:** 4.
- **Toe kick and rail:** 18 in. each.

**Cover panel nesting (`takeoff/sheet_nesting.py`).** Every FÖRBÄTTRA panel is 24 5/8 in.
wide. Each piece stands one side across that width and spends the other along the panel's
length; a 1/8 in. kerf goes before each piece after the first. Longest first, first panel
it fits.
- **25x30 (four pieces).** The bed desk cover is 24 5/8 x 30, which spends a whole panel.
  The study seat end (16 x 24 5/8) spends 16; the two pantry toe panels (24 x 6, cut per
  `kitchen_stock_cabinet_details.md`) spend 6 each. 16 + 1/8 + 6 + 1/8 + 6 = 28 1/4, under
  30. **2 panels**, not 4.
- **25x80 (five pieces).** The study nook cover (24 5/8 x 80) is a whole panel. The living
  end panel (24 x 34 9/16) and the peninsula end panel (24 x 34) share one:
  34 9/16 + 1/8 + 34 = 68 11/16, under 80. The peninsula seating face is authored as two
  whole panels. **4 panels**, not 5.
- **25x90.** The hall-bath closet cover, **1 panel**.
- **Total: 7 panels, not 10.**

**Rail run check (test).**
- Two wall frames, 48 in. and 54 in., set touching, make a 102 in. run. That needs ceil(102/84) = **2** rails.
- Set 2 in. apart they are two runs, which needs 1 + 1 = 2 rails. Set 30 in. and 36 in. touching, they make a 66 in. run, which needs 1 rail.

## Where the soft close is

| Line | Soft close |
|---|---|
| Doors | UTRUSTA 805.248.82 has a damper built in |
| MAXIMERA drawers | Soft close is built in |
| Lift-up fronts (pantry tops, hung stack, study seats) | UTRUSTA 804.654.15 is the version "with damper" |
| Carousel corner bifold | UTRUSTA 104.272.62 has a damper |
| Rev-A-Shelf 5374-24FL | The slides are soft close |

**Flagged: soft close not confirmed.**
- **Corner wall door (`SEKT-CORNER-W26-30`).** Its hinges come with frame 102.655.04, so check that they are damped.
- **Vanity combinations** (bath2 36 in. and 12 in., RM-S-VANITY 30 in., attic 24 in.). Each IKEA "s" combination includes its own hinges, so check that they are UTRUSTA with a damper.

## Known over-orders and open items

- **Scribes are shop stock.** The site-cut scribes (`FT-KIT-COLD-SCRIBE-20` at 3/4 in. thick, and `FT-S-SEKTION-SCRIBE-90` at 24 7/8 in. deep) do not fit any FÖRBÄTTRA size, so they carry no IKEA product.
- **The carousel corner** is ordered as frame 705.967.56 plus the UTRUSTA carousel and the bifold hinges. The AXSTAD bifold pair stands in for s79582533's VALLSTENA fronts. Its article number has not been read.
- **Articles not yet read** (they show as unresolved in `haus order`): the AXSTAD 24x50 door, the AXSTAD 24x15 lift front, the AXSTAD corner pair, and bath2's 36 in. combination (894.549.45 was read off a URL and not confirmed).
- **Not in this list.** Hardware for the vanity doors has not been selected, so no knob is counted for them. The hall bath and the study nook use VOXTORP fronts, which have no separate hardware.
