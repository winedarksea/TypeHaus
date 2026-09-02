# RM-M-BATH2 — the over-toilet cabinet, and why the engine had to be corrected first

`FURN-M-BATH2-CAB` / `FT-BATH2-CAB-4506`. This note exists because the
cabinet's two hard dimensions — 6" deep, bottom at 4'-0" AFF — are not styling, and because
adding it required changing a code check that was reporting a violation this house does not
have. Both facts are the kind that get lost and then re-litigated.

## The room had one wall left

RM-M-BATH2 is 72.8 sf with no storage above the vanity drawers. Three of its four walls are
spent: the 54" `FX-M-BATH2-SINK` runs the south half of the west wall and its north end stops
3 1/4" short of `FX-M-BATH2-WC`'s front clearance, and the 36" shower plus the drop-in tub
deck take the whole east wall. What is left is **W-M-HS1's bathroom (south) face, y = 264.615",
x from 6.635" to 52.0"** — over the toilet.

| | |
|---|---|
| West stop | W-M-W3's finish face, **x = 6.635"** (the plane `FX-M-BATH2-SINK` is struck off) |
| East stop | W-M-TUBDK-W's west face, **x = 52.0"** — 54.25" axis less half of a 2x4 wall |
| Free run | **45 3/8"** |
| Carcass | **45" W x 6" D x 60" H**, 3/16" of scribe each end |
| Elevation | bottom **4'-0" AFF**, top **9'-0"** — the ceiling |
| Doors | **3 x 15" x 60"** flush overlay MDF, push-to-open latches, painted out |
| Shelves | 4 adjustable — ~22 linear feet, 7.8 cu ft |

45" is not a rounding: it is exactly three 15" doors, and stopping on the tub deck's west face
puts the east end plane on an edge already in the room.

## Why 4'-0" — this is the compliance line, not a comfort choice

`FX-TOILET-STD` is 30" tall. A cabinet coming down to tank level would push the wall face 6"
south, the bowl would move with it, and its front clearance would land at y = 209.6" — **2.8"
inside the vanity**, which clears by 3 1/4" today. Keeping the box above 30" means the toilet
does not move and nothing else in the room is redrawn. At 4'-0" there is 18" of clear air over
the tank lid: enough to lift the lid out, and not behind your head seated.

## Why not recessed

W-M-HS1 is `INT_2X6_STAGGERED_PLUMBING` — 6 3/4" overall, 5 1/2" cavity, 2x4s staggered on 2x6
plates, bath-face studs at x = 7 3/8, 16, 24, 32, 40, 48.

1. Every bay is 6 1/2" clear, and each bath-face bay has a **hall-face stud 2" back at its
   midpoint**. A continuous recess means cutting the bath-face studs and heading them.
2. The WC's vent rises in that wall **directly above the bowl**, the bay around x = 28"–31"
   (the fixture left `PR-M-WC-VENT` on 2026-08-29 and vents in-wall through W-S-SN1).
3. 5" net depth after gypsum, for all of that, when the ask was 6".

W-M-W3 (west) is the thermal envelope and is not a candidate at any depth.

## The check that was wrong, and the clause that was missing

As authored the cabinet trips `integrity.placeable_required_clearance_conflict`
(Severity.ERROR / Result.FAIL) against `FX-M-BATH2-WC`. The zone is live because
`plan/manifest.py` sets `active_code_profile="MN/IRC"`; `_clearance_conflicts` subtracts the
bowl's own 20"-wide footprint from its 30"-wide zone, leaving flanks at x 15"–20" and
x 40"–45", and the cabinet puts 60 sq in into them.

**The citation is faithful and the finding is still wrong.** UPC 402.5 governs here (Minn. R.
1309.0010 subp. 3.D deletes IRC ch. 25–33; ch. 4714 adopts the UPC) and really does say "to a
side wall or obstruction". But UPC 402.5's 15" is elbow room for someone **seated** on the
fixture and its 24" is standing room in **front** of it. Both are measured through a person,
not up to the ceiling. Every escape hatch the engine offered instead cites **ICC A117.1**, an
accessibility standard Minn. R. 1341 does not apply to detached one- and two-family dwellings
— and the one clause that settles this case was missing: *an object mounted above the fixture
whose zone it overlaps takes none of that fixture's use space.*

Two independent confirmations that this is the ordinary reading and not a convenience:

- stock over-toilet cabinets are 24–30" wide and **8"–12" deep** and are built and inspected
  routinely. A 6" box is shallower than the standard article.
- A117.1 **§604.3.2** says it positively: the clearance around a water closet is permitted to
  be overlapped by grab bars, paper dispensers, coat hooks and **shelves**. The standard the
  engine already cites names shelving over a bowl as something that does not take the space.

So the fix was to teach the check the missing clause, not to shrink the cabinet:
`resolve/placeables.py::_mounted_over_the_fixture`, a per-(zone, peer) exemption in
`_clearance_conflicts` alongside the two that function already documents — a zone is not the
space its owner stands in, and a zone does not reach through a partition. This is the third:
**a zone is not a column of air.** (→ `plans/01-decisions.md` #67 for the rule, its three
conditions, and the `kind == "Fixture"` proxy it rests on.)

Checked against this case: the bowl's local y runs -14"..+14"; the cabinet's overlap lands at
local y 8"..14", base 48" against the bowl's 30" top. Exempt. A cabinet 24" in *front* of the
bowl would sit at local y -38"..-32" and still reports, which is the condition that keeps the
exemption honest.

**The before/after, measured.** `haus check houses/catlin --only all` reports 848 pass / 0 fail
with the cabinet in, and exactly one clearance finding of either kind in the whole house —
`FURN-A-STUDY-DESK` vs `FURN-A-STUDY-CHAIR1`, recommended, furniture-owned, floor-standing.
Forcing the exemption off reproduces the FAIL on `FX-M-BATH2-WC` / `FURN-M-BATH2-CAB`, so the
exemption is what clears it and not a geometry accident.

## Cost, and what is deliberately not modelled

One `[placeables]` row: `FT-BATH2-CAB-4506` at $175–450 material / $275–800 labour.
`[placeables]`, not `[furnishings]` — it is screwed to W-M-HS1's studs (a staggered wall gives
a fastening point every 8") and cannot be carried out of the room. Basis: ~2 sheets (3/4"
paint-grade ply carcass + 5/8" MDF doors), 6 concealed hinges, 3 push latches, 4 adjustable
shelves, paint-grade finish in a wet room, plus shop time and the set. It lands just under the
$175–350/LF custom built-in band the study casework implies (3.75 LF -> $656–1,313) because
this is a flat box: no scribe beyond 3/8", no face frame, no stepped top, no counter.

**An unpriced type is silently dropped from the BOM and the total FALLS**, which reads as a
saving — so that row is not optional.

**No millwork entry and no `ShelfBank`.** `haus millwork` is the hardwood milling schedule and
every `material_ref` in it is a species board; a painted MDF/ply box has no board feet, and a
`ShelfBank` would ask the mill to saw a painted shelf. The money is in the `[placeables]` row.

**Known cosmetic gap:** `plan_symbol="wall-cabinet"` draws two doors with pulls. The real unit
is three flush slabs with none. Nothing downstream reads the symbol for quantity or clearance;
fixing it means a new no-pull, three-cell symbol in `model/placeable_symbols/furniture.py`.
