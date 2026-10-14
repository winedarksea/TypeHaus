"""R311.7.6's exception: a flight that rises to a door with no top landing.

ST-G-SERVICE rises straight to D-G-SERVICE's threshold since 2026-10-13, legal because the
door swings OUT (houses/catlin/notes/garage_service_door_outswing.md). The inswing case is
the same door with its sweep mirrored across the wall onto the flight.
"""

from dataclasses import replace

from _helpers import check_context

from typehaus.checks.code.mn_residential.stair_arrival import door_at_stair_head
from typehaus.findings import Result


def _finding(model, tag="ST-G-SERVICE"):
    [finding] = [f for f in door_at_stair_head(check_context(model=model))
                 if tag in f.element_tags]
    return finding


def _with_swing(model, swing):
    return replace(model, openings=[
        replace(o, swing_clearance=swing) if o.tag == "D-G-SERVICE" else o
        for o in model.openings])


def test_the_outswing_service_door_passes(catlin_model_ro):
    finding = _finding(catlin_model_ro)
    assert finding.result is Result.PASS, finding.message
    assert "D-G-SERVICE" in finding.message and "RM-GARAGE" in finding.message


def test_an_inswing_leaf_over_the_flight_fails(catlin_model_ro):
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    hinge_y = door.swing_clearance[0][1]
    inswing = tuple((x, 2 * hinge_y - y) for x, y in door.swing_clearance)
    finding = _finding(_with_swing(catlin_model_ro, inswing))
    assert finding.result is Result.FAIL and "swings over ST-G-SERVICE" in finding.message


def test_a_door_with_no_resolved_swing_is_unknown(catlin_model_ro):
    finding = _finding(_with_swing(catlin_model_ro, ()))
    assert finding.result is Result.UNKNOWN


def test_flights_without_a_door_at_the_head_are_not_applicable(catlin_model_ro):
    """ST-BW-ENTRY arrives beside D-G-SERVICE, but walks parallel to its wall."""
    for tag in ("ST-BW-ENTRY", "ST-SG-PORCH", "ST-S2A"):
        assert _finding(catlin_model_ro, tag).result is Result.NOT_APPLICABLE
