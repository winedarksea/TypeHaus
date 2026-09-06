# Main floor, wood-to-concrete boundary at y = 13'-0"

From the basement-ceiling overhaul (`plans/TODO.md § Basement Ceiling`, decisions #59/#60).

## What the boundary is

The main floor over the basement is two structures that meet on one line:

- **East of x = 18', north of y = 13'** — `SL-M-DECK`, 414 SF of 10" LiteDeck EPS
  stay-in-place beam (8" base panel + 2" top hat) under a 4 3/8" cast cover. Bears on the
  x=18' line and the east foundation wall.
- **Everywhere else** — `FS-M-WEST`, `FS-M-MECH`, `FS-M-STAIR` and `FS-M-EAST`, 11 7/8"
  I-joists at 16" o.c. with a 3/4" plywood subfloor. Same bearing lines; 18'-0" spans except
  over the mechanical room and the stair, where the x=10' line cuts them to 10'-0" and 8'-0".

**What the two share is the BEARING SEAT, not the depth.** The deck is 14 3/8" and both land
on one flat seat at **-13 7/16"**, the whole way round the basement, with no step in the
forms. The cost of that is at the top and it is
3/16": the cap tops at +15/16" where the plywood tops at +3/4", which is inside the thickness
of the 6 mm plank laid on the plywood — the two walking surfaces still meet flush, with the
LVP 1/64"-1/20" proud. `structural.mixed_deck_bearing_seat` holds all of it.

What is *not* continuous is stiffness.

## Why it needs a joint

The two systems deflect differently under the same load, and neither number is small enough
to ignore against a rigid floor finish:

- The concrete band is a one-way slab on an 18'-0" span. Its live-load deflection is small
  and it creeps slowly over years.
- The I-joist bays are designed to L/360 at worst and L/480 at best over the same 18'-0" —
  which is 0.45" to 0.60" of live-load deflection at midspan, and it moves *now*, under a
  person walking.

Along y = 13'-0" the two midspans are 18' apart in the span direction but adjacent across
the line, so the differential shows up as a hinge. Two consequences to draw:

1. **A continuous wood run across the line will telegraph.** The plank reads here, and a
   joint that opens and closes 1/2" per footfall works the edge loose: the seam nearest the
   line opens first. Break the run on the line with a **flush T** and let each field float
   within its own structure. The south bay was solid oak for part of 2026-09-05, which made
   this point sharper rather than softer — floating plank is at least forgiving in-plane and
   a nailed-down 3/4" strip floor is not — and it is plank again, so the softer case is the
   one that applies. Break it anyway: the differential is in the structure, not the finish.
2. **Tile must not cross it at all.** `FH-M-DINING` (x 22'-11" to 30'-11", y 13'-9" to
   21'-0") sits wholly inside the concrete band, 9" clear of the line, which is deliberate —
   a thinset bed over the cured cap has nothing to accommodate. If a tile field ever grows
   south past y = 13'-0", it needs a proper movement joint (TCNA EJ171) on the line, not a
   grout line.

## Detailing at the line

- **Framing.** `FS-M-EAST`'s north rim lands on the line; the concrete's south edge is
  formed against it. Do not tie the cap's reinforcing into the rim. The concrete bears on
  the x=18' wall and the east wall; the joists bear on x=18' and their own lines; nothing
  spans the boundary and nothing should.
- **Ceiling below.** Gypsum is continuous over both (5/8", IRC R316.4 over the EPS,
  `ceiling_below` on the joists). Break the board on the line with a control joint —
  otherwise the same differential cracks the taped seam, which is the visible half of this
  detail and the half a homeowner reports.
- **Finish above.** The joint lives in the finish, not in the structure — and since
  2026-08-21 the model can name what it is on each side. `SL-M-DECK` carries
  `floor_finish="polished-concrete"`: the cap's own top *is* the finished floor over the
  band, and `RM-M-LIVING`'s `floor_finish="lvp"` is the field finish over the wood bays
  only. The resolver intersects the slab with each room's clear face and emits the result as
  a finish zone, so the boundary is stated once — `_BAND_Y` in `params/main_deck.py` — and
  the finish moves when it does. As of 2026-09-05 that is the ONLY zone in the room: 410.2
  SF of polish, and 355.6 SF of plank field over everything else — south bay, stair lane and
  hall band alike. Both of the authored zones this room briefly carried (a `vinyl-sheet` hall
  band, then an `oak` south bay) are gone, which is worth keeping that way: a derived zone
  follows `_BAND_Y` when the boundary moves, and an authored one has to be chased.

## What the model still cannot hold

**The transition is an L, not a line.** Inside `RM-M-LIVING` the finish changes along
y = 13'-0" from x = 18' to 36' (17.9 lf) **and** along x = 18'-0" from y = 22.4' to 36'
(13.6 lf) — about 31.5 lf of edge in total. Only the **y = 13' leg is a movement joint**:
both systems are at mid-span there, which is the differential this whole note is about.
Along x = 18' both the slab and `FS-M-WEST`'s joists bear on the same wall line, so that leg
deflects nowhere. It is a material and height change and nothing more, and it does not want
a soft joint.

**The x = 18' leg is one material again, and it is flush.** It read sheet vinyl from
2026-08-25 to 2026-09-05 — the hall band was an authored `vinyl-sheet` `FinishZone`, ~2 mm
of goods with no rigid core, so the cap met a floor that sat **low** and this note carried a
warning that those 3.9 lf had to be trimmed for a real step. **That zone is deleted.** The
hall takes the room's own field `lvp`, so the whole 13.6 lf is 6 mm SPC against the cap:
+0.986" to +0.9375", **1/64" proud**. A plain flush T, specified for movement it does not
have. This leg got better, and there is nothing here to trim for height.

**The y = 13' leg is flush too, and that took a decision rather than a detail.** The south
bay (x 18'..36', y 0'..13') went to 3/4" solid oak on 2026-09-05 and came back to plank the
same day. Oak finishes at **+1.500"** against the polished cap's **+0.9375"**, and that
9/16" cannot be flushed from either side:

- *Not from the concrete.* `structural.mixed_deck_bearing_seat`
  (`checks/structural/bearing_seat.py`) FAILs when cap-top and subfloor-top differ by more
  than 1/4", so `DECK_TOP` has about **1/16"** of lift in it — not the 9/16" the oak wants.
  Raising it further needs the engine to give finishes a real thickness, which is that
  check's own stated fix and is not this change.
- *Not from the wood side.* Furring the whole south bay up 9/16" would move a subfloor plane
  that the bearing seat, the wall bases and the stair rise all read.

So oak here was a **reducer** or nothing, and the reducer was not wanted: 17.9 lf of ramped
moulding across the middle of the main living space, on the one line that also has to break
for movement. **The finish gave way instead of the detail.** The bay is 6 mm SPC like the
rest of the room, +0.986" against the cap — the same 1/64" as the x = 18' leg, the same
flush T, and the room reads as one floor across all 31.5 lf. It still needs the T: the
differential is in the structure and does not care what is laid over it. Oak stays the two
studies' floor, where nothing meets a concrete cap. Cost of the reversion, measured
line-to-line on `haus takeoff --csv`: **-$1,980 to -$2,751** delivered, against which the
`oak` row in `prices.toml` falls back under its sand-and-finish mobilisation minimum.

That 3/16" of cap over plywood is deliberate and it is derived, not dialled. The deck is
14 3/8" (10" beam + 4 3/8" cover) against the wood bay's 14 3/16" to the same seat
(1/16" gasket + 1 1/2" mudsill + 11 7/8" joist + 3/4" subfloor); the difference is spent
upward, because the seat below is the plane that must not move. Re-spec the cover and the
cap top moves with it — `structural.mixed_deck_bearing_seat` allows a quarter inch here,
which is roughly a floor finish, and FAILs past it. Check the resolved elevations before
ordering the moulding, not this paragraph.

**The one junction that is NOT flush, off this L entirely: the mudroom doorway.** `RM-M-MUDROOM` went to
porcelain over a 1/8" uncoupling membrane in the same change, so its walking surface is
~**+1.3125"** where the hall's plank is +0.986" — a ~5/16" **transition strip** at `D-M-MUD`,
and with the south bay back on plank it is the **only** threshold left on this storey. It is wanted: a dirt step at the door people
come in through in boots.

**That "only" is bought by tiling the two closets, and it was nearly missed.** `RM-M-MECH`
and `RM-M-MUD-CLOSET` are carved out of the mudroom's own footprint and **both of their
doors open into it** — `D-M-MECH` is hosted on `W-M-MECH-S` and `D-M-MUDC` on `W-M-MUDC-N`,
each facing the mudroom, and neither opens off the hall. So plank in either does not join
the LVP spine; it cuts this tile field into an island with **three** strips through it. Both
are tiled. The decisive one is `D-M-MUDC`, a `DT-INT-BYPASS48`: a bypass slider runs on a
**bottom guide**, and a 5/16" ramp under a sliding track is a detail nobody wants to build.
`RM-M-MECH` is the weaker case on its own — a hinged utility door opened twice a year, and
plank is marginally easier to open up around its riser penetration — and is tiled anyway,
because 15 SF is thin ground on which to break a dirt-containment field. Delivered cost of
the pair, measured line-to-line on `haus takeoff --csv`: **+$298 to +$627**.

The change also improves the *exterior* side, which no check can see — `FS-BW-FLOOR`'s
composite plank tops at +1.000", so the mudroom floor now stands 5/16" **above** the
breezeway deck instead of ~1/6" below it, and water runs out rather than in. R311.3.1's
1 1/2" is untouched.

**And a second step, in the ceiling below — 2 1/16".** The gypsum
is continuous across the boundary but the two faces are not coplanar: on the wood side the
board screws straight to the joists at -12 1/2", on the concrete side to the EPS form's
integral steel rib at -14 1/16". Two things make that number. The rib is 1/2" of it and
always was. The other 1 9/16" is the deck being deeper than the wood bay, which is what
buying one flat bearing seat costs — the two structures now agree at the BOTTOM of the
mudsill instead of at the bottom of the joists, and the concrete has no mudsill. Neither part
can be removed: furring the wood bays down to meet the band would cost the basement 2 1/16"
everywhere to fix a line, and the basement is at 8'-0 15/16" clear under the joists against
7'-10 7/8" under the band. This is now a real trim decision rather than a hairline, and the
control joint below is doing more work than it was. Detail it the way the finish above is
detailed: break the board on y = 13'-0" with a control joint (which this note already asks
for, since the joint has to be there anyway) and let the reveal absorb the offset, rather
than floating a feathered transition over a moving line.

**The polish spec.** A **cream polish** — grind the surface paste only, about 1/16" — not
aggregate exposure. The cap is 4 5/8" over EPS form and its reinforcement cover is not there
to survive a salt-and-pepper grind. That implies the pour itself: hard steel trowel finish,
and either a wet cure or a cure-and-seal the polisher's densifier will bond through — a
film-forming curing compound has to come off before the first pass and is a cost, not a
saving. Hairline flexural cracks over the one-way span are expected on a slab this thin and
are filled with semi-rigid joint filler as part of the polish, not treated as a defect.

### Fibre — this note said NO, and now says MICRO-MONOFILAMENT

**Superseded 2026-09-03.** This paragraph read *"no fibres in the mix (they fuzz the ground
surface)"*, and against **macro** fibre that is simply true: macro synthetic is explicitly
visible at a finished surface, which is why it is accepted on industrial floors and not on
one anybody looks at. Steel fibre is worse again — it rust-stains where it lies near the
surface, and this is an interior floor.

The owner asked for fibre here anyway, wanting a floor that is *pretty enough for everyday
use* rather than museum grade, and there is a middle path that gets both:

**Micro-synthetic MONOFILAMENT polypropylene at ~1.5 lb/cy** (`CATLIN_POLISHED_MIX`). It is
a different product answering a different question — it targets **plastic shrinkage**
cracking in the first hours, a 55-70% reduction, which is exactly the surface cracking a
thin 4 5/8" cap over EPS is prone to. Monofilament, not fibrillated. At the correct dosage
and finished properly it does not fuzz, and what little presents at the surface sits in the
paste layer a **cream polish removes** — the polish and the fibre are compatible precisely
because the polish is a cream one.

It is not structural and replaces no steel. The hard steel trowel finish and the cure
requirements above are unchanged and matter more with fibre in the mix, not less.

**Confirm the dose and the product against a supplier TDS before ordering.** The published
range is 0.75-1.5 lb/cy and the finisher's opinion on a *polished* floor should govern the
top end — 1.5 is where this house sits, and it is the end of the range, not the middle.
Sika Fibermesh-150 and Euclid's micro-synthetic line are the two obvious candidates.

## Model gap, recorded rather than solved

The engine has no element for a floor-finish movement joint. The *finish* half is derived
now — the band knows what it is, and bills and draws as its own material — but the **joint**
is not. A `Transition` binds to a *derived boundary condition* and there is no condition for
"two decks meet in plan"; a `ConstructionRule` bills a return along a wall or a ceiling, not
along a line between two floor elements. So the flush T, the soft joint and the ceiling
control joint are a note and a drawing instruction, and nothing in `haus check` will notice
if the finish is run straight through. If the mixed deck outlives this house — and the
depth-matching that makes it work is general — the condition worth deriving is
`deck_change:<assembly>|<assembly>`, on the shared edge of two floor elements at one storey,
which a `Transition` could then bind exactly the way `assembly_change:*` binds a wall line's.
Recorded in `plans/TODO.md`.
