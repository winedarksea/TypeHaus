"""EQ-B-WH's position is repeated as a path literal in eight places. Pin them together.

``houses/catlin`` authors the water heater's coordinate once as ``Equipment.position``
(``plan/mep_hvac.py``) and then again, verbatim, as a path endpoint in every supply run that
leaves the tank (``plan/mep_supply.py``) — seven of them — plus as the datum for the T&P
relief discharge (``plan/mep_drainage.py``). Those files are ``# haus: editable``, whose
dialect allows only literals: no shared constant can reach across them, and nothing in the
resolver pulls a pipe onto its equipment. So moving the tank without moving all eight
silently disconnects the hot trunk, the cold feed and five branches, and the model still
resolves, still builds, and still passes every MEP check — it just describes plumbing that
does not connect.

That is exactly what happened on 2026-08-23, when the tank moved from (6'-2 1/4", 32'-9 7/8")
to (5'-6", 24'-0") to clear ``EQ-B-ESS-BATT``'s REQUIRED separation zone. The move was fine;
the trap is real, and this file is the guard. It reads the RESOLVED model, not the source, so
it holds however the coordinate is spelled.
"""

from __future__ import annotations

import pytest

_TOLERANCE_M = 1e-9
# The tap is deliberately NOT on the tank: it hangs 2" off the west face and drops a foot
# south. This is how far off-centre that puts it, and it is checked as a range rather than a
# point so the detail can be re-drawn without editing a test.
_TPR_MAX_OFFSET_M = 0.6096  # 2'-0" — anything further is not "beside the tank" any more


def _centre(canvas_object) -> tuple[float, float]:
    xs = [p[0] for p in canvas_object.footprint]
    ys = [p[1] for p in canvas_object.footprint]
    return sum(xs) / len(xs), sum(ys) / len(ys)


@pytest.fixture(scope="module")
def water_heater(catlin_model):
    obj = next((o for o in catlin_model.canvas_objects if o.tag == "EQ-B-WH"), None)
    assert obj is not None, "EQ-B-WH did not resolve to a placed object"
    return obj


def test_every_supply_run_that_names_the_tank_actually_touches_it(catlin_model,
                                                                  water_heater) -> None:
    """Each run below leaves or arrives at the tank; a vertex must sit ON its position."""
    expected = {
        "PR-B-HW-TRUNK",   # the hot trunk out of the tank
        "PR-B-CW-WH",      # the cold feed into it
        "PR-B-HW-BATH1",
        "PR-B-HW-WASH",
        "PR-B-HW-SBATH",
        "PR-B-CW-BATH",
        "PR-B-HW-BATH",
    }
    tx, ty = _centre(water_heater)
    touching = set()
    for run in catlin_model.pipe_runs:
        if any(abs(x - tx) <= _TOLERANCE_M and abs(y - ty) <= _TOLERANCE_M
               for x, y in run.path):
            touching.add(run.tag)
    assert expected <= touching, (
        "these runs no longer start or end on EQ-B-WH — the tank moved and they did not: "
        + ", ".join(sorted(expected - touching))
    )


def test_the_relief_discharge_followed_the_tank(catlin_model, water_heater) -> None:
    """P2804.6.1's discharge is offset from the tank, so it is checked by proximity."""
    tpr = next((r for r in catlin_model.pipe_runs if r.tag == "PR-B-WH-TPR"), None)
    assert tpr is not None, "EQ-B-WH names relief_discharge_ref=PR-B-WH-TPR; it is missing"
    tx, ty = _centre(water_heater)
    start = tpr.path[0]
    offset = ((start[0] - tx) ** 2 + (start[1] - ty) ** 2) ** 0.5
    assert offset <= _TPR_MAX_OFFSET_M, (
        f"PR-B-WH-TPR starts {offset:.3f} m from EQ-B-WH — the relief line did not follow "
        "the tank"
    )


def test_the_tank_stands_inside_the_room_it_claims(catlin_model, water_heater) -> None:
    """A placeable that drifts out of its room takes its clearances and loads with it."""
    from shapely.geometry import Polygon

    room = next((r for r in catlin_model.rooms if r.tag == "RM-B-FURNACE"), None)
    assert room is not None
    assert Polygon(room.clear_face).contains(Polygon(water_heater.footprint))
