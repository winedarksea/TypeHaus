"""The second floor's deck, split at the centre bearing line: trusses west, joists east.

Every second-floor service that has to cross the joist run — the plumbing stacks and
supply risers serving ``RM-S-PLANT``/the suite bath cluster, the radon/plumbing chase, the
hydrant distribution, the data conduits — is west of x=18', so that half is where open-web
trimmable floor trusses pay for themselves: services cross *through* the webs (8 7/8" clear
chord-to-chord) instead of being bored, soffited or chased. The east half is bedrooms and a
study with only incidental crossings, so it keeps the cheaper I-joist.

Both members are the same 11 7/8" depth, deliberately — the deck plane, the finished floor
and the ceiling below all stay flat across the split, exactly as the wood/wood halves of
``params/main_deck.py`` do. Unlike that module's concrete/wood boundary, this one needs
**no movement joint and no finish break**: same depth, same stiffness class, one
continuous ceiling plane. ``notes/mixed_deck_movement_joint.md`` does not apply here.

**Why two FloorSystems and not one.** Same reasoning as ``main_deck.py``:
``FloorSystem.outline`` scopes only the perpendicular extent, and span boundaries come
from the bearing refs' axis midpoints — one system naming all three bearing lines would
frame joists straight through the material change at x=18'. ``BM-M-HALL``'s axis midpoint
in x is 18', the same as ``W-M-C2``, so including it in both halves' bearing_refs injects
no third span boundary.

**Why a params module and not the editable storey file.** Same reason as
``main_deck.py`` (its own docstring, lines 43-47): the shared depth wants to be one
constant, and an editable file may hold only literals and cannot import from ``params/``.
FloorSystems are not UI-movable, so nothing is lost by keeping this out of
``plan/storeys/second.py`` — and it lets ``main_deck.py`` import the depth from here
instead of restating it, since the concrete band's depth derivation matches whatever this
module's members share.

**Known cost of the west/trusses choice.** ``FO-S-STAIR`` (x 10'-3⅜"..17'-8⅝",
y 26'-0⅜"..35'-5⅜") lands in the west half. Eight joist lines clip to 10'-1⅝" there and
become short fabricated trusses rather than trimmed 18' stock — outside the trimmable
range, so they are fabricated to length instead. The opening's parallel edges (running
with the joist direction) resolve to doubled truss members — the correct real detail, a
girder-truss pair; its perpendicular edges already resolve to multi-ply LVL headers via
``opening_header_profile``.

**Stock, and what the truss is built to.** Trimmable stock is 18' and 20', trimmable up to
6" from each end. The west field's *bearing grid* is 18'-0"; the truss is **17'-11"** —
``resolve/floor_ends.py`` cuts it to where it stops, behind the 1 1/4" rim at the west
framing face and 3 1/2" onto the x=18' plate. Clear span 17'-3 1/4". An 18' blank trimmed
1" still covers it (``takeoff/framing.py::_order_length_ft``), but 17'-11" is the number on
the fabricator's order, which ``haus takeoff``'s fabrication schedule states.
"""

from typehaus import DeckLayer, FloorSystem, JoistSpec, Layer, LayerFunction, Point2D, ft, inch, pt

# Both members share one depth, deliberately — see the module docstring. ``main_deck.py``
# imports ``_DEPTH``/``_SUBFLOOR`` from here rather than restating them, so the concrete
# band's depth derivation can never drift from what this deck actually frames.
_TRUSS = "11.875 floor truss"
_JOIST = "11.875 I-joist"
_DEPTH = inch(11.875)
_OC = inch(16)
_SUBFLOOR = inch(0.75)

# How the x=18' plate is split. ``W-M-C2`` is a 2x6: 5 1/2" of seat, both decks landing on
# it from opposite sides. A centreline split gives each 2 3/4", which shorts the truss — an
# open-web truss wants 3" minimum, an I-joist 1 3/4". So the meeting line moves 3/4" east:
# 3 1/2" truss, 2" I-joist, both clear of their minimum with the plate exactly spent. The
# two must sum to 5 1/2" or the halves do not meet, which is why they are stated together;
# ``integrity.floor_end_bearing`` grades the result.
_TRUSS_BEARING = inch(3.5)
_JOIST_BEARING = inch(2.0)

# The main floor's ceiling below both halves — 5/8" gypsum board, room side (and only
# layer). The living room's resilient channel (``CR-LIVING-CEIL-RC`` in
# ``plan/assemblies.py``) still bills separately as a ``ConstructionRule`` return.
_CEILING_GWB = (Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),)
_CENTRE_X = ft(18)
_HOUSE = ft(36)
_ZERO = ft(0)


def _rect(x0: object, y0: object, x1: object, y1: object) -> tuple[Point2D, ...]:
    return (pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1))


# ** THE WEB PANEL LAYOUT IS PROVISIONAL AND SAYS SO. **
#
# Until 2026-09-19 nothing in the engine narrowed an open-web member along its span, so
# `profiles.open_web_opening_m`'s 8 7/8" chord-to-chord window read as a CONTINUOUS SLOT:
# thirteen 4" ducts crossing every truss inside a 41" band all passed
# `mep.run_member_crossing` without a word. A real truss has webs at panel points and a
# duct lands in an opening or it lands on a web.
#
# These three numbers are a PLACEHOLDER for a fabricator's drawing nobody has yet asked
# for. They are not read off a submittal, and the way they are derived is the whole of
# their authority:
#
#   * 24" PANEL PITCH — an ordinary Warren layout for a parallel-chord wood floor truss at
#     16" o.c. Panel points every 24" is the commonest spacing in the 11 7/8"–16" depth
#     range, and it is a round number on purpose so nobody mistakes it for a reading.
#   * 15" CLEAR OPENING — derived, not asserted. A diagonal crossing an 8 7/8" clear depth
#     at 45 degrees advances 8 7/8" along the chord, so between two consecutive diagonals
#     of a 24" panel there is 24 − 8 7/8 ≈ 15 1/8" of clear run. Rounded DOWN to 15".
#   * 12" OFFSET — half a panel, so the first opening straddles the bearing rather than
#     starting on it. A fabricator sets this off the actual span and nobody else can.
#
# ** THE OWNER REPLACES ALL THREE WHEN THE TRUSS SUBMITTAL ARRIVES, ** and plans/TODO.md
# carries it. A marked placeholder beats an UNKNOWN here for one reason: without a datum
# the level-2 duct design cannot be graded at all, and an ungraded design is how thirteen
# ducts came to be drawn through one another in the first place. Delete these three fields
# and `mep.open_web_panel` goes straight back to saying so, by name.
_WEB_PANEL_PITCH = inch(24)
_WEB_OPENING = inch(15)
_WEB_PANEL_OFFSET = inch(12)

# ** TWO TRUSS LINES MOVED OFF THE 16" MODULE, AND THEY ARE AS PROVISIONAL AS THE WEBS. **
# (laid station, new station) in y (owner, 2026-09-23). The fabricator's layout replaces
# the whole field; these say only where a line must NOT stand.
#   * 26'-8" -> 26'-10": clears PR-B-HW-SBATH and PR-M-S-BATH1-DRAIN's risers.
#   * 34'-8" -> 34'-5 3/4": clears the radon/plumbing chase (VR-M-RADON-VENT, now at
#     y=35'-1.3") and the ERV exhaust risers in FO-M-ERV-EA.
_LINE_MOVES = ((inch(320), inch(322)), (inch(416), inch(413.75)))

# West half: open-web trusses, so every second-floor plumbing stack, supply riser and the
# radon/plumbing chase can cross the deck through the webs instead of a soffit or chase.
WEST_FLOOR = FloorSystem(
    uid="1JXQ975X9E", tag="FS-S-WEST",
    joists=JoistSpec(member=_TRUSS, spacing=_OC, direction="x",
                     bearing_refs=("W-M-W2", "W-M-C2", "BM-M-HALL"),
                     web_panel_pitch=_WEB_PANEL_PITCH,
                     web_opening_width=_WEB_OPENING,
                     web_panel_offset=_WEB_PANEL_OFFSET,
                     line_overrides=_LINE_MOVES,
                     end_bearing=(("W-M-C2", _TRUSS_BEARING),)),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    ceiling_below=_CEILING_GWB,
    outline=_rect(_ZERO, _ZERO, _CENTRE_X, _HOUSE),
    openings=("FO-S-STAIR", "FO-S-ERV-CHASE"),
    source="catlin second floor, west half — 11 7/8\" open-web floor trusses at 16\" o.c. "
           "spanning 18'-0\" from W-M-W2 to the x=18' bearing line south of FO-S-STAIR, "
           "and 10'-3 3/8\" to that opening's west header north of it, chosen for the "
           "plumbing/HVAC crossings this half carries",
)

# East half: keeps FS-SECOND's original specification and uid — the half whose IFC
# GlobalId should survive (decision #16).
EAST_FLOOR = FloorSystem(
    uid="CSF603AAAA", tag="FS-S-EAST",
    joists=JoistSpec(member=_JOIST, spacing=_OC, direction="x",
                     bearing_refs=("W-M-C2", "W-M-E1", "BM-M-HALL"),
                     end_bearing=(("W-M-C2", _JOIST_BEARING),)),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    # The main floor's ceiling: this deck's underside *is* that ceiling (unchanged from
    # the old FS-SECOND). Plain board, not type X: R302.13 doesn't reach this floor.
    ceiling_below=_CEILING_GWB,
    outline=_rect(_CENTRE_X, _ZERO, _HOUSE, _HOUSE),
    source="catlin second floor, east half — 11 7/8\" I-joists at 16\" o.c. spanning "
           "18'-0\" from the x=18' bearing line to W-M-E1, unchanged from the old "
           "whole-floor FS-SECOND",
)

SECOND_ELEMENTS = [WEST_FLOOR, EAST_FLOOR]
