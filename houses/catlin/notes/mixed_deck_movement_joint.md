# Main floor, wood-to-concrete boundary at y = 13'-0"

Written 2026-08-21 with the basement-ceiling overhaul (`plans/TODO.md § Basement Ceiling`,
decisions #59/#60).

## What the boundary is

The main floor over the basement is two structures that meet on one line:

- **East of x = 18', north of y = 13'** — `SL-M-DECK`, 414 SF of 8" EPS stay-in-place form
  with a 4 5/8" cast concrete cap. Bears on the x=18' line and the east foundation wall.
- **Everywhere else** — `FS-M-WEST` and `FS-M-EAST`, 11 7/8" I-joists at 16" o.c. with a
  3/4" plywood subfloor. Same 18'-0" spans, same bearing lines.

Both are 12 5/8" deep, so the soffit plane and the finished-floor plane are continuous
across the line. That is the whole design and it is what makes the boundary movable later.
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

1. **A continuous LVP run across the line will telegraph.** Plank is floating and forgiving
   in-plane, but a joint that opens and closes 1/2" per footfall works the locking edge
   loose, and the seam nearest the line will open first. Break the run on the line with a
   T-moulding or a transition strip on the concrete side, and let each field float within
   its own structure.
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
- **Finish above.** The joint lives in the finish, not in the structure. Whatever the
  finished floor is, it stops and restarts on y = 13'-0".

## Model gap, recorded rather than solved

The engine has no element for a floor-finish movement joint. A `Transition` binds to a
*derived boundary condition* and there is no condition for "two decks meet in plan"; a
`ConstructionRule` bills a return along a wall or a ceiling, not along a line between two
floor elements. So this detail is a note and a drawing instruction, and nothing in
`haus check` will notice if the finish is run straight through. If the mixed deck outlives
this house — and the depth-matching that makes it work is general — the condition worth
deriving is `deck_change:<assembly>|<assembly>`, on the shared edge of two floor elements at
one storey, which a `Transition` could then bind exactly the way `assembly_change:*` binds a
wall line's. Recorded in `plans/TODO.md`.
