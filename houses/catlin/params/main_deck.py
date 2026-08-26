"""The basement's ceiling — the main floor's structure, mixed wood and concrete.

Until 2026-08-21 this was one element: ``SL-M-DECK``, a 1,233 SF x 9" cast suspended
concrete deck. It was the most expensive line in the model (34.26 cy on shored plywood
formwork, whose commercial shoring mobilisation floor alone is $25-40k — see
``plans/cost-options.md``), and it forced eight interior 12" concrete cross walls with
strip footings and drain tile under them, because it was designed to span between them.

Two facts change that. Wood I-joists already cross the same 18' bays on both storeys above
(``FS-SECOND``, ``FS-ATTIC``), and EPS stay-in-place deck forms — LiteDeck, BuildDeck,
Insul-Deck — span 18' one-way with far less concrete. Tune the EPS deck so it lands on the
same bearing plane as the wood floor's mudsill and the two become interchangeable bay by
bay: same seat, same soffit-to-datum arithmetic, same 18' span to the x=18' bearing line.
Concrete then goes only where it is actually wanted.

**One flat bearing seat, one shared mudsill (2026-08-23).** Until that date the joists and
their rim resolved z -11 7/8"..0'-0" against basement walls that topped out at 0'-0" — the
whole wood floor inside the top foot of the pour, with nothing between it and the concrete,
while the only sill return in the model sat *above* the joist tops under the framed wall.
The plate was never missing from the design (``plan/storeys/basement.py``'s WALLS header and
``plans/cost-options.md`` both say the I-joists share the framed wall's 2x6 mudsill, and
``pt-sill-plate`` bills the LF), only from the geometry. The fix is not more plate: it is
one flat seat all the way round at ``BEARING_SEAT``, reached by deepening the EPS deck until
its soffit lands on the same plane the mudsill sits on. No stepping in the forms, and the
basement wall comes out at exactly 8'-0".

::

                    WOOD BAY                          EPS DECK BAY
      +0.95"..0.99" 6 mm SPC LVP (5 mm + 1 mm IXPE)
      +15/16" ------------------------------------  cap top, polished  <- finished floor
      +3/4"   3/4" plywood subfloor
      0'-0"   ------------------------------------  STOREY DATUM (top of joists)
              11 7/8" I-joist @ 16" o.c.             4 3/8" cast cover
     -11 7/8" ----- joist soffit ------                 +
              1 1/2" PT mudsill                     10" LiteDeck (8" base + 2" top hat)
     -13 3/8"
              1/16" EPDM gasket, compressed
     -13 7/16" ==== BEARING SEAT - FLAT, NO STEP ====  deck soffit

The wood bay's stack to the seat is 1/16 + 1 1/2 + 11 7/8 + 3/4 = 14 3/16"; the deck's is
10" + 4 3/8" = 14 3/8". The 3/16" difference is the deck's, and it is spent upward: the cap
tops at +15/16" where the subfloor tops at +3/4", so the 6 mm plank laid on the plywood
finishes 1/64"-1/20" proud of the polished concrete — flush within any floor-covering
tolerance, and the joint detail is a movement joint anyway. ``structural.mixed_deck_bearing_seat``
is what holds all of that: nudge the joist depth, the subfloor, the mudsill, the gasket, the
form or the cover and the build FAILs instead of quietly stepping.

**The datum is the top of joists, not the walking surface.** Walls bear there and the
subfloor rides above it, so a wood bay's finished floor is +3/4" while the datum is 0'-0".
That is why ``DECK`` carries an explicit ``top_elevation``: a ``datum="structure"`` slab
pins its TOP to the datum whatever its thickness, so the arithmetic below — which is right
— never reached the elevation on its own.

The one plane that does NOT match is the basement ceiling, and it cannot: the board screws
to the form's integral steel rib on the concrete side and straight to the joists on the
wood side. With the deck 1 9/16" deeper than the wood bay's soffit and the rib's 1/2" on top
of that, the two gypsum faces sit **2 1/16"** apart at the boundary. That is a real step in
a real ceiling, and ``notes/mixed_deck_movement_joint.md`` carries how it is trimmed.

**And the model draws it.** ``RM-B-GYM`` is the only room the boundary runs through, so it
resolves TWO ceilings rather than one — 234 SF hung off ``FS-M-EAST``'s joist soffit at
-11 7/8", 90 SF off this deck's at -13 7/16" (``resolve/ceilings.py``, via
``ceiling_over.ceiling_regions``). The model states the **1 9/16"** it can derive, not the
2 1/16" that gets built: the rib is part of the EPS form, and EPS is never modelled here.
A room straddling two decks of the SAME depth — ``RM-M-LIVING`` over the second floor's
truss/I-joist split, ``RM-B-FURNACE`` over two of the west bays — is one flat ceiling and
must stay one; a deck seam is not a step.

The basement floor rose 2 9/16" with the seat (the house did not move — ``SITE_GRADE`` is
unchanged), so the basement slab and storey are at -9'-1 7/16" and the walls are exactly
8'-0" of pour: 8'-0 15/16" clear under the joists, 7'-10 7/8" under the concrete band, both
over R305.1's 7'-0". The 8" segments drop from ``#6 @ 48" o.c.`` to ``#5 @ 41" o.c.`` on
IRC Table R404.1.2(8)'s 8'-unsupported row.

**Why this is a params module and not ``plan/storeys/main.py``.** The depth wants to be one
constant, and now so does the seat: ``BEARING_SEAT`` is read by the basement walls (as
literals the ``integrity`` tier guards, since editable files cannot import), by
``structural.mixed_deck_bearing_seat`` and by the wall-base detail component.
Editable-dialect files may hold only literals and cannot import from ``params/``, so a file
that holds the arithmetic cannot be the file the UI writes back to. The elements here are
not UI-movable, so nothing is lost.

**Why three FloorSystems on the west half and not one.** ``FloorSystem.outline`` scopes only
the *perpendicular* extent; span boundaries come from the bearing refs' axis midpoints
(``resolve/floors.py``). One system naming all three bearing lines would frame joists across
the full 36' of the house, straight through the concrete band. So the west half's south
bay, its mechanical-room bay and its stair bay are separate systems, each naming only the
lines it actually bears on — see the split at ``_MECH_Y`` below.

**Bearing refs are a bearing statement, not an axis proxy.** They used to be the latter:
``FS-M-EAST`` named ``W-B-CS2`` (y 13'-10"..18') against a deck outlined y 0..13' that it
never touches. Every system below now names the walls its joists actually land on, all of
them, including the ones on the same grid line — a duplicate boundary is a degenerate span
and ``resolve/floors.py`` drops it, so listing the truth costs nothing.
``integrity.floor_bearing_grid`` is what catches the remaining trap: ``W-B-CS`` carries
``alignment=face("concrete-ext", offset=inch(-6))``, a hardcoded HALF of its thickness, and
an alignment offset that stopped matching would slide its axis off x=18' and inject a bay of
stub joists. It resolves to 18.000 exactly today; the check is what keeps it there.

Quantities, from the manufacturers' published tables:

* LiteDeck's form is modular — an 8" base panel plus a 2"/4"/6" top hat gives a 10"/12"/14"
  beam, and the cast cover over it is specified separately. This deck is the 10" beam (8" +
  2" hat) under a 4 3/8" cover. BuildDeck's 8" form spans 20' clear at a 4" cap (4,000 psi,
  60 ksi rebar, 15 psf dead + 40 psf live); this span is 18'-0" at a deeper section.
* The LiteDeck WRS manual's consumption table reads 58 SF/cy for the 10" beam at a 4" cover
  and 52 SF/cy at 4 1/2", so 4 3/8" interpolates to ~53.5 SF/cy = 0.01869 cy/SF. The 414 SF
  band is 7.74 cy — against 34.26 cy for the whole 9" slab it replaced.
* **It needs shoring.** The same manual requires continuous temporary shoring at 6' o.c. for
  any span over 5', held until 75% design strength / 21 days. This module claimed "no shored
  formwork at all" until 2026-08-23 and that was simply wrong. It does not flip the decision
  — adjustable posts at 6' o.c. under a 414 SF band are a rental line, not the 9" slab's
  commercial plywood-and-mobilisation package — but the line is in ``prices.toml`` now.

Sources: LiteDeck WRS installation manual, Sept 2020 (liteform.com), BuildDeck brochure
(buildblock.com), Insul-Deck technical summary, ICF Builder's foam-decking comparison.
"""

from typehaus import (
    DeckLayer,
    FloorSystem,
    JoistSpec,
    Layer,
    LayerFunction,
    Point2D,
    Slab,
    ft,
    inch,
    pt,
)

from params.second_deck import _DEPTH as _JOIST_DEPTH
from params.second_deck import _SUBFLOOR

# --- the wood bay this deck has to match, top and bottom --------------------------
#
# The second floor's build-up, repeated on this storey. The depth and subfloor thickness
# are imported from ``params/second_deck.py`` rather than restated: since 2026-08-21 that
# deck is split truss/I-joist at x=18', and both members share this one depth precisely so
# the concrete band below can keep matching a single number instead of two. Everything
# below derives from them rather than restating them.
_JOIST = "11.875 I-joist"
_JOIST_OC = inch(16)

# The basement's ceiling — 5/8" gypsum board, room side (and only layer). Migrated from a
# single ``DeckLayer`` to a one-``Layer`` tuple with the generalized ``ceiling_below`` field.
_CEILING_GWB = (Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),)

# The storey datum is the TOP OF JOISTS, not the walking surface — walls bear there and the
# subfloor rides above it (``Slab.datum``'s own docstring, and W-S-E2 starting at exactly
# 10'-0" on FS-SECOND's joist tops). So the finished floor of a wood bay is _SUBFLOOR
# *above* the datum, and anything claiming to share that plane has to be pinned there
# explicitly. ``plan/manifest.py`` takes the main storey's elevation from MAIN_DATUM, so
# the two cannot disagree.
MAIN_DATUM = ft(0)
MAIN_FINISHED_FLOOR = inch(MAIN_DATUM.inches + _SUBFLOOR.inches)

# The 6 mm SPC plank that goes down on that subfloor — 5 mm of rigid core plus a 1 mm IXPE
# pad that compresses under load, so the walking surface lands somewhere in 0.95"..0.99"
# above the datum. It has no home in the model: ``FloorSystem``/``Room`` ``floor_finish``
# is a bare material tag with no thickness (``model/floors.py``), so the only way to state
# the number the flush-joint argument rests on is here and in the ``lvp`` material's spec.
# Giving finishes a real thickness is its own change (plans/TODO.md).
_LVP = inch(0.2362)  # 6 mm nominal
MAIN_FINISHED_FLOOR_LVP = inch(MAIN_FINISHED_FLOOR.inches + _LVP.inches)

# --- the plane the whole exercise turns on ----------------------------------------
#
# **The bearing seat.** One flat plane, all the way round the basement, that both bays land
# on. On the wood side the stack under the datum is joist + mudsill + gasket; the deck's
# soffit is simply told to reach the same elevation. Every basement ``FoundationWall`` tops
# out here, ``SL-M-DECK``'s soffit sits here, and the flat-laid PT plate the joists and rim
# bear on is returned here (``resolve/construction_sills.py``).
#
# The mudsill is the framed wall's own 2x6 sill, shared: one board carries the studs above
# and the joists beside it, which is why the sill return is authored over the *union* of the
# two runs rather than as two rules that would double-bill the same plate.
# The same number ``FramingSpec.sill_gasket`` states on CATLIN_EXT_2X6 (and the same one
# ``BasementToFramedWallConfig.sill_gasket_in`` falls back to). It is stated twice on
# purpose: the seat is derived here, and the field is what the wall-base detail draws. It
# used to be stated twice *differently* — the field carried the uncompressed 1/4" roll until
# 2026-08-24, which is why this line existed at all.
_SILL_GASKET_COMPRESSED = inch(0.0625)   # EPDM sill seal, compressed thickness
_MUDSILL = inch(1.5)                     # the framed wall's 2x6 sill plate, laid flat
BEARING_SEAT = inch(-(_SILL_GASKET_COMPRESSED.inches + _MUDSILL.inches
                      + _JOIST_DEPTH.inches))

# **The deck's depth is what reaches that seat**, not a copy of the wood bay's depth. It was
# the latter until 2026-08-23 (11 7/8" + 3/4" = 12 5/8"), which matched the two *finished*
# planes and left the deck's soffit 1 9/16" above the plane the mudsill sits on — i.e. the
# joists bearing on bare concrete while the deck bore somewhere else entirely.
#
# The split into stay-in-place form and cast cover is the LiteDeck section, stated as the
# modularity it is rather than as a threshold rule: the form is an 8" base panel plus a
# 2"/4"/6" top hat, giving a 10", 12" or 14" beam, and the cover over it is specified
# separately. This is the 10" beam under a 4 3/8" cover. The old "at 13" or more take the
# 10" form" rule is satisfied by construction now and said nothing the section does not.
#
# Two constraints this arithmetic does NOT enforce, and a human must:
#   * The manufacturer's span table governs the cover, not the seat: a thinner cover to hit
#     some other seat needs the 18'-0" clear span re-checked, not just a thinner pour.
#   * ``plan/assemblies.py`` is editable-dialect — literals only, no imports from params —
#     so CATLIN_DECK_EPS_INT's two structural layers cannot read these and must be edited to
#     match. ``integrity.slab_thickness`` fails the build if they drift apart, and
#     ``structural.mixed_deck_bearing_seat`` fails it if the seat itself drifts.
EPS_FORM_DEPTH = inch(10.0)   # LiteDeck 8" base + 2" top hat
EPS_CAP = inch(4.375)         # cast cover over the form
DECK_DEPTH = inch(EPS_FORM_DEPTH.inches + EPS_CAP.inches)

# Where that puts the cap's own top: the seat plus the whole section. +15/16", 3/16" above
# the plywood beside it, which is what leaves the 6 mm plank 1/64"-1/20" proud of the polish
# rather than standing below it. Derived, never a literal — a thicker cover lifts it.
DECK_TOP = inch(BEARING_SEAT.inches + DECK_DEPTH.inches)

# The basement's own two planes, derived here because everything else in the house is
# derived from the seat and the basement should be too. The pour is exactly 8'-0" — which is
# what takes the 8" segments from ``#6 @ 48" o.c.`` to ``#5 @ 41" o.c.`` on IRC Table
# R404.1.2(8)'s 8'-unsupported / 7'-unbalanced cell. ``plan/storeys/basement.py`` is
# editable-dialect and repeats both as literals; ``integrity.basement_bearing_seat`` is what
# stops the two from drifting, exactly as ``integrity.slab_thickness`` guards DECK_DEPTH.
BASEMENT_WALL_HEIGHT = ft(8)
BASEMENT_DATUM = inch(BEARING_SEAT.inches - BASEMENT_WALL_HEIGHT.inches)

# The concrete/wood boundary. Concrete keeps the east half north of y=13' — the dining
# radiant zone (FH-M-DINING, x 22'-11"..30'-11", y 13'-9"..21'-0") sits wholly inside it,
# with its thinset bed over the cured cap exactly as before. Everything else is wood.
# Re-apportioning the ceiling later is a matter of moving this one line and the two
# outlines it cuts.
#
# It is also a movement joint, and the finish has to say so: the two systems match in depth
# but not in stiffness, and an I-joist bay's 1/2" of live-load deflection against a slab that
# barely moves is a hinge under whatever runs across it. The detail — break the LVP, break
# the ceiling board, keep tile off the line entirely — is
# ``houses/catlin/notes/mixed_deck_movement_joint.md``. Nothing in the engine can bind it to
# geometry (a Transition needs a derived boundary condition and there is none for "two decks
# meet in plan"), which is recorded there and in plans/TODO.md.
_BAND_Y = ft(13)
_CENTRE_X = ft(18)
_HOUSE = ft(36)
_ZERO = ft(0)


def _rect(x0: object, y0: object, x1: object, y1: object) -> tuple[Point2D, ...]:
    return (pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1))


# --- the west half, in three bays -------------------------------------------------
#
# One system spanning 18'-0" wall to centre line was the whole west half until 2026-08-23,
# and its bearing refs were an axis proxy: ``W-B-W2`` (y 0..18') standing in for a run that
# went to y=36'. Two things are true now instead. Each system names every wall its joists
# actually land on — duplicates on one grid line are a degenerate span and ``resolve/floors.py``
# drops them — and the x=10' line north of ``_MECH_Y`` is declared as bearing, which is what
# ``W-B-STR3`` was 12" of pour for until 2026-08-24. It is 2x6 bearing studs now (see its
# note in plan/storeys/basement.py): what these joists need from it is 1 1/2" of structure
# either side of the NODE axis, which the studs give at 2 7/8" / 2 5/8" — the pour was
# never the point, the bearing was.
#
# ``_MECH_Y`` is the N-B-BA-W / N-B-BA-E node line: the southernmost y at which x=10' is a
# bearing wall for its whole remaining run (W-B-STR3 to y=31', then W-B-STR to y=36' —
# one continuous wall, two tags). South of it x=10' is W-B-STR2, a non-bearing steel-stud stub, so the south bay
# keeps the full 18'-0" span.
#
# Joist depth does NOT follow the shorter spans. It is set by the deck match — the seat and
# the datum are one plane each, house-wide — so the 10' and 8' bays simply carry reserve.
_MECH_Y = ft(21, 9.375)
_STR_X = ft(10)

# The transition is a DOUBLE JOIST, and it has to be authored as one. Two abutting floor
# systems each lay a member on their own outline edge (``resolve/floors.py`` always emits at
# perp0 and perp1), so an edge shared to the inch puts two joists in the same place —
# ``structural.member_interference``, correctly. It is also not what anyone builds: a bay
# whose span changes from 18'-0" to 10'-0" gets a joist on each side of the line, nailed
# together. So the south system stops one joist WIDTH short and the pair sits face to face,
# which is exactly the 2 1/2" this subtracts. Do not "tidy" the two edges back onto one
# number.
_TRANSITION_DOUBLE = inch(2.5)   # one I-joist flange width
_MECH_Y_S = inch(_MECH_Y.inches - _TRANSITION_DOUBLE.inches)

# South bay: full 18'-0" span, wall to centre line, y 0'-0" to the bathroom node line.
WEST_FLOOR = FloorSystem(
    uid="CMFS01AAAA", tag="FS-M-WEST",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     # x=0': W-B-W2 carries y 0..18', W-B-W1 the rest. x=18': W-B-CS
                     # carries y 0..13'-10", W-B-CS2 to 18', W-B-CN2 to the node line.
                     # All five are true bearing; the three on x=18' resolve to one
                     # boundary (integrity.floor_bearing_grid holds them there).
                     bearing_refs=("W-B-W2", "W-B-W1", "W-B-CS", "W-B-CS2", "W-B-CN2")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    # The basement's ceiling. R316.4 wants gypsum over the EPS in the concrete band; the
    # owner's decision was to drywall the whole ceiling rather than stop the board at the
    # boundary, which is also what retires the old "visible copper in the basement"
    # preference (houses/catlin/preferences.toml).
    ceiling_below=_CEILING_GWB,
    outline=_rect(_ZERO, _ZERO, _CENTRE_X, _MECH_Y_S),
    source="catlin main floor, west half south of the bathroom node line — 11 7/8\" "
           "I-joists at 16\" o.c. spanning 18'-0\" east-west from the west wall to the "
           "x=18' bearing line",
)

# Mechanical-room bay: 10'-0" west wall to the x=10' line.
MECH_FLOOR = FloorSystem(
    uid="CMFS03AAAA", tag="FS-M-MECH",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     bearing_refs=("W-B-W1", "W-B-STR3", "W-B-STR")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    ceiling_below=_CEILING_GWB,
    outline=_rect(_ZERO, _MECH_Y, _STR_X, _HOUSE),
    source="catlin main floor, over the furnace room — same joists as FS-M-WEST, spanning "
           "10'-0\" east-west from the west wall to the x=10' bearing line",
)

# Stair bay: 8'-0" from the x=10' line to the centre line, carrying FO-M-STAIR. Its west
# edge is a bearing edge, which is why W-B-STR3 has to stay a declared bearing ref —
# ``structural.floor_opening_header`` reads FO-M-STAIR's own refs and would otherwise size
# that edge a 9'-0" engineered header. Since 2026-08-24 that edge sits on the framed wall's
# plywood face at x=10'-3 3/8" rather than the pour's at 10'-6"; the refs did not change,
# because ``_opening_edge_has_declared_bearing`` reads the named walls' full layer
# footprints and this one reaches exactly that face.
STAIR_FLOOR = FloorSystem(
    uid="CMFS04AAAA", tag="FS-M-STAIR",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     bearing_refs=("W-B-STR3", "W-B-STR", "W-B-CN")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    ceiling_below=_CEILING_GWB,
    outline=_rect(_STR_X, _MECH_Y, _CENTRE_X, _HOUSE),
    openings=("FO-M-STAIR",),
    source="catlin main floor, over the stair shaft — same joists as FS-M-WEST, spanning "
           "8'-0\" east-west from the x=10' bearing line to the x=18' bearing line",
)

# The east half's wood bay: the gym's ceiling, south of the concrete band.
EAST_FLOOR = FloorSystem(
    uid="CMFS02AAAA", tag="FS-M-EAST",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     # This bay is south of y=13'-10", so its west bearing is
                     # W-B-CS, not the W-B-CS2 it named until 2026-08-23 — that
                     # segment runs y 13'-10"..18' and this deck never touches it.
                     bearing_refs=("W-B-CS", "W-B-E1")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    ceiling_below=_CEILING_GWB,
    outline=_rect(_CENTRE_X, _ZERO, _HOUSE, _BAND_Y),
    source="catlin main floor, east half south of y=13' — same joists as FS-M-WEST, "
           "spanning 18'-0\" from the x=18' bearing line to W-B-E1",
)

# What is left of the concrete: 414 SF over the dining end. Same tag and same uid as the
# 1,233 SF slab it replaces, so the IFC GlobalId survives (decision #16).
DECK = Slab(
    uid="CMS501AAAA", tag="SL-M-DECK",
    outline=_rect(_CENTRE_X, _BAND_Y, _HOUSE, _HOUSE),
    thickness=DECK_DEPTH, assembly="CATLIN_DECK_EPS_INT",
    # The cap's own top is the finished floor: a cream polish, no covering, no subfloor.
    # Every room that sits on this outline resolves a derived finish zone from it
    # (``resolve/rooms.py``), so RM-M-LIVING keeps LVP as its FIELD finish over the wood
    # bays and the band bills as polished concrete. Move _BAND_Y and the finish moves too —
    # the boundary is stated once, here. Spec in notes/mixed_deck_movement_joint.md.
    floor_finish="polished-concrete",
    # Ceiling is 5/8" gypsum end to end (CLAUDE.md) — the media room below sees the same
    # board as the wood bays either side of it, no EPS layer (per the owner: EPS is always
    # hidden, never modelled).
    ceiling_below=_CEILING_GWB,
    # And the cap top has to BE a stated plane, not whatever a datum leaves it at.
    # ``top_elevation`` is absolute and wins over ``datum`` outright
    # (``resolve/envelope.py::_slab_elevations``), which is the only way to say it: a
    # ``datum="structure"`` slab hangs its thickness below the datum whatever its thickness
    # is, so the arithmetic above never reached the elevation. Pinning the top is also what
    # pins the SOFFIT — z0 = DECK_TOP - DECK_DEPTH = BEARING_SEAT, the plane the mudsill
    # sits on beside it. Derived, never a literal: a thicker cover lifts the polish and
    # leaves the seat alone, a deeper form lowers the seat and leaves the polish alone, and
    # ``structural.mixed_deck_bearing_seat`` FAILs on either if it stops meeting the wood.
    # SL-G-FLOOR pins itself the same way.
    top_elevation=DECK_TOP,
)

MAIN_ELEMENTS = [WEST_FLOOR, MECH_FLOOR, STAIR_FLOOR, EAST_FLOOR, DECK]
