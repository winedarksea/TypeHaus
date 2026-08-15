"""Catlin's stated house facts, turned into assertions.

``houses/catlin/CLAUDE.md`` §"House facts that must stay true" is a list of invariants the
plan is *supposed* to hold, and one of them says so out loud: "The breezeway follows the
doors, and **nothing enforces that but this line**." That is exactly the failure mode this
house has already had — the 2026-07-28 mudroom conversion pushed ``D-M-ENTRY`` 4'-0" east
and the shelter stood 3'-6" off its own door for four days, until an unrelated landing check
happened to notice. A prose invariant that only a code check can catch by accident is not
enforced; this module is where those lines stop being prose.
"""

from __future__ import annotations

import pytest

FT = 0.3048
INCH = 0.0254

# The two doors the breezeway exists to connect, and the enclosure that must stay centred
# between them. `params/breezeway.py` derives its glazing from _GLAZING_CENTER_X = 7.25 ft;
# this test never reads that constant — it re-derives the answer from the doors, which is
# the whole point.
ENTRY_DOOR = "D-M-ENTRY"
SERVICE_DOOR = "D-G-SERVICE"
BREEZEWAY_GLAZING = ("GL-BW-WALL-W", "GL-BW-WALL-E")


def _opening_world_center(model, tag: str) -> tuple[float, float]:
    """A door's centre in the project frame, from its host wall's axis."""
    opening = next(o for o in model.openings if o.tag == tag)
    wall = next(w for w in model.walls if w.tag == opening.host_wall)
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    t = opening.center_along_m / length
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t


def _solid_x_span(model, tag: str) -> tuple[float, float]:
    solid = next(s for s in model.solids if s.tag == tag)
    xs = [p[0] for p in solid.outline]
    return min(xs), max(xs)


def test_breezeway_stays_centred_between_the_two_doors_it_shelters(catlin_model):
    """The invariant `houses/catlin/CLAUDE.md` says nothing enforces.

    Tolerance is 1/2", not zero: the enclosure is a literal 4'-0" of polycarbonate and the
    doors are 1'-6" apart in x, so the centre is a derived midpoint, not a snapped one.
    Half an inch is far tighter than the 3'-6" miss this is here to catch and still leaves
    room for a deliberate inch of re-centring.
    """
    entry_x, _ = _opening_world_center(catlin_model, ENTRY_DOOR)
    service_x, _ = _opening_world_center(catlin_model, SERVICE_DOOR)
    doors_midpoint = (entry_x + service_x) / 2.0

    spans = [_solid_x_span(catlin_model, tag) for tag in BREEZEWAY_GLAZING]
    glazing_center = (min(s[0] for s in spans) + max(s[1] for s in spans)) / 2.0

    assert glazing_center == pytest.approx(doors_midpoint, abs=0.5 * INCH), (
        f"the breezeway is centred at x={glazing_center / FT:.3f}' but "
        f"{ENTRY_DOOR}/{SERVICE_DOOR} are centred at x={doors_midpoint / FT:.3f}' — "
        f"move _GLAZING_CENTER_X in params/breezeway.py to follow the doors"
    )


def test_breezeway_is_the_briefs_literal_four_feet(catlin_model):
    """Three sheets, one cut: the 4'-0" glazed dimension is the brief, not a preference.

    Measured panel-centre to panel-centre, which is the glazing line the module authors
    (`_GLAZING_X0`/`_GLAZING_X1`); outer face to outer face is that plus one sheet
    thickness, and picking the wrong one of the two is its own small trap.

    Paired with the test above on purpose — "centred" and "4 feet wide" are one invariant
    in two halves, and satisfying either alone is how the enclosure drifted last time.
    """
    centers = []
    for tag in BREEZEWAY_GLAZING:
        lo, hi = _solid_x_span(catlin_model, tag)
        centers.append((lo + hi) / 2.0)
    assert max(centers) - min(centers) == pytest.approx(4.0 * FT, abs=0.5 * INCH)


def test_both_breezeway_doors_open_onto_the_deck_at_the_same_level(catlin_model):
    """`D-G-SERVICE` carries the same negative sill as `D-G-OVERHEAD` so both doors land
    at 0'-0" on the shared deck — the 22" step at the garage was resolved on 2026-08-01 by
    gapping the ICF stem to a grade beam, and a future stem edit must not silently undo it."""
    storey_z = {s.tag: s.elevation.meters for s in catlin_model.plan.storeys}
    levels = {}
    for tag in (ENTRY_DOOR, SERVICE_DOOR):
        opening = next(o for o in catlin_model.openings if o.tag == tag)
        wall = next(w for w in catlin_model.walls if w.tag == opening.host_wall)
        levels[tag] = storey_z[wall.storey] + opening.sill_m
    assert levels[ENTRY_DOOR] == pytest.approx(levels[SERVICE_DOOR], abs=0.5 * INCH), levels
