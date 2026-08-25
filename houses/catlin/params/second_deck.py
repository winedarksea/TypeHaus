"""The second floor's deck, split at the centre bearing line: trusses west, joists east.

Until 2026-08-21 ``FS-SECOND`` was one FloorSystem of 11 7/8" I-joists spanning the full
36' east-west. Every second-floor service that had to cross the joist run — the plumbing
stacks and supply risers serving ``RM-S-PLANT``/the suite bath cluster, the radon/plumbing
chase, the hydrant distribution, the data conduits — is west of x=18', so that half is
where open-web trimmable floor trusses pay for themselves: services cross *through* the
webs (8 7/8" clear chord-to-chord) instead of being bored, soffited or chased. The east
half is bedrooms and a study with only incidental crossings, so it keeps the cheaper
I-joist.

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
y 26'-0⅜"..35'-5⅜") lands in the west half. Seven joist lines clip to ~10'-3⅜" there and
become short fabricated trusses rather than trimmed 18' stock — outside the trimmable
range, so they are fabricated to length instead. The opening's parallel edges (running
with the joist direction) resolve to doubled truss members — the correct real detail, a
girder-truss pair; its perpendicular edges already resolve to multi-ply LVL headers via
``opening_header_profile``.

**Stock.** Trimmable stock is 18' and 20', trimmable up to 6" from each end. The west
field's spans are exactly 18'-0" — the 18' truss untrimmed, with 6" of range each end for
any later adjustment (``takeoff/framing.py::_order_length_ft``).
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

# The main floor's ceiling below both halves — 5/8" gypsum board, room side (and only
# layer). Migrated from a single ``DeckLayer`` to a one-``Layer`` tuple with the
# generalized ``ceiling_below`` field; the living room's resilient channel
# (``CR-LIVING-CEIL-RC`` in ``plan/assemblies.py``) still bills separately as a
# ``ConstructionRule`` return, unaffected by this shape change.
_CEILING_GWB = (Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),)
_CENTRE_X = ft(18)
_HOUSE = ft(36)
_ZERO = ft(0)


def _rect(x0: object, y0: object, x1: object, y1: object) -> tuple[Point2D, ...]:
    return (pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1))


# West half: open-web trusses, so every second-floor plumbing stack, supply riser and the
# radon/plumbing chase can cross the deck through the webs instead of a soffit or chase.
WEST_FLOOR = FloorSystem(
    uid="1JXQ975X9E", tag="FS-S-WEST",
    joists=JoistSpec(member=_TRUSS, spacing=_OC, direction="x",
                     bearing_refs=("W-M-W2", "W-M-C2", "BM-M-HALL")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    ceiling_below=_CEILING_GWB,
    outline=_rect(_ZERO, _ZERO, _CENTRE_X, _HOUSE),
    openings=("FO-S-STAIR",),
    source="catlin second floor, west half — 11 7/8\" open-web floor trusses at 16\" o.c. "
           "spanning 18'-0\" from W-M-W2 to the x=18' bearing line, chosen for the "
           "plumbing/HVAC crossings this half carries",
)

# East half: unchanged specification from the old whole-floor FS-SECOND, so it keeps that
# element's uid — the half whose IFC GlobalId should survive (decision #16).
EAST_FLOOR = FloorSystem(
    uid="CSF603AAAA", tag="FS-S-EAST",
    joists=JoistSpec(member=_JOIST, spacing=_OC, direction="x",
                     bearing_refs=("W-M-C2", "W-M-E1", "BM-M-HALL")),
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
