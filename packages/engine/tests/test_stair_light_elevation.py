"""A luminaire over a stair has to be over it in THREE dimensions.

``_lights_near`` was a 4 ft plan buffer with no z filter at all, and a plan ring has no
opinion about height: ED-S-STUDY2-STAIR-SC1 sat 2'-11 1/2" *below* the tread it was drawn
to light and ``code.R303_7_stairway_illumination`` counted it, the pantry light one storey
under ST-M2S counted, and the handrail tape that does not climb with its flight counted.
This module pins the window that fixes that, in both directions: the buried fixture is
discounted, and the step light set into the riser beside the flight is not.
"""

from __future__ import annotations

import dataclasses

import pytest

INCH = 0.0254

SC1 = "ED-S-STUDY2-STAIR-SC1"
STUDY_STAIR = "ST-S2A"
PORCH_STAIR = "ST-SG-PORCH"
PORCH_STEP_LIGHT = "ED-M-STAIR-LT"
BASEMENT_STAIR = "ST-B2M"
RAIL_TAPE = "LR-B-STAIR-RAIL"


@pytest.fixture(scope="module")
def ctx(catlin_plan):
    from typehaus.checks import build_context

    context, _findings = build_context(catlin_plan)
    return context


def _finding_for(findings, stair_tag: str):
    return next(f for f in findings if f"stair {stair_tag} " in f.message)


def _set_light_z(ctx, tag: str, z_m: float) -> None:
    """Move one resolved luminaire in z, leaving the authored plan untouched."""
    index = next(i for i, obj in enumerate(ctx.model.canvas_objects) if obj.tag == tag)
    moved = dataclasses.replace(ctx.model.canvas_objects[index], z_m=z_m)
    ctx.model.canvas_objects[index] = moved


def test_the_study_stair_sconce_is_counted_where_it_now_stands(ctx):
    """SC1 at 7'-6" and x=29' is over its tread, so it lights ST-S2A.

    The pin on the fix, not on the bug: the sconce moved east and up
    (``plan/lighting.py``) precisely so it would clear the flight it lights, and a check
    that discounted it here would be reporting a fixture that is fine.
    """
    from typehaus.checks.code.mn_residential.illumination import stairway_illumination

    message = _finding_for(stairway_illumination(ctx), STUDY_STAIR).message
    assert SC1 in message.split(" and switched")[0], message
    assert "below the nosing line" not in message, message


def test_a_sconce_dropped_under_its_own_tread_stops_counting(ctx):
    """The bug itself: a sconce under its own tread is discounted, and the finding says so.

    Driven off the RESOLVED elevation rather than by re-authoring the house, because that
    is the number the rule reads and the one that carries a storey datum with it. 66" down
    puts SC1 at its historical 5'-0" mount reading against the tread at x=25'-0" — the
    2'-11 1/2" burial the fix moved it out of, with the one-riser step-light band on top.
    """
    from typehaus.checks.code.mn_residential.illumination import stairway_illumination

    original = next(o for o in ctx.model.canvas_objects if o.tag == SC1).z_m
    try:
        _set_light_z(ctx, SC1, original - 66 * INCH)
        message = _finding_for(stairway_illumination(ctx), STUDY_STAIR).message
    finally:
        _set_light_z(ctx, SC1, original)
    assert f"{SC1} sits" in message and "below the nosing line" in message, message
    assert SC1 not in message.split(" and switched")[0], message


def test_the_porch_step_light_still_counts_from_inside_the_riser_band(ctx):
    """A step light is BELOW the tread it washes, and that is what a step light is.

    ED-M-STAIR-LT hangs 8" under the top of W-SG-E1 on purpose — there is no 7'-0" on that
    face to mount at. Measured against the flight's synthetic arrival station (the porch
    deck, one riser above the top nosing) it read 7.5" buried and failed R303.8. The rule
    drops that station and allows one riser, which is the riser FACE a step light lives in.
    """
    from typehaus.checks.code.mn_residential.illumination import (
        exterior_stairway_illumination,
    )

    findings = exterior_stairway_illumination(ctx)
    message = next(f for f in findings if PORCH_STAIR in f.message).message
    assert "is lit at" in message, message
    assert PORCH_STEP_LIGHT not in message, message


def test_a_step_light_below_the_whole_flight_is_still_discounted(ctx):
    """...and the band is one riser, not an amnesty: two feet down and it is buried."""
    from typehaus.checks.code.mn_residential.illumination import (
        exterior_stairway_illumination,
    )

    original = next(o for o in ctx.model.canvas_objects if o.tag == PORCH_STEP_LIGHT).z_m
    try:
        _set_light_z(ctx, PORCH_STEP_LIGHT, original - 24 * INCH)
        findings = exterior_stairway_illumination(ctx)
        message = next(f for f in findings if PORCH_STAIR in f.message).message
    finally:
        _set_light_z(ctx, PORCH_STEP_LIGHT, original)
    assert f"{PORCH_STEP_LIGHT} sits" in message, message


def test_the_handrail_tape_that_does_not_climb_is_reported(ctx):
    """LR-B-STAIR-RAIL's known limit, said by the engine instead of by a comment.

    ``LightRun`` carries one mount elevation for a whole path, so the tape under ST-B2M's
    handrail lies flat at 34" off the slab while the flight climbs away from it. The house
    documents that in prose (``plan/lighting.py``) and noted that nothing graded it. The
    stair is still lit by five other fixtures, so this is a parenthetical on a PASS rather
    than a FAIL — but it is no longer silent.
    """
    from typehaus.checks.code.mn_residential.illumination import stairway_illumination

    message = _finding_for(stairway_illumination(ctx), BASEMENT_STAIR).message
    assert f"{RAIL_TAPE} sits" in message and "below the nosing line" in message, message
    assert message.startswith("stair"), message  # still a PASS-shaped message
