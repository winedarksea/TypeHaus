"""``integrity.header_under_plate`` — a wall header standing inside its own plates (C3-E1/E2)."""

from __future__ import annotations

from dataclasses import replace

from _helpers import check_context

from typehaus.checks.integrity.header_under_plate import header_under_plate
from typehaus.findings import Result

_IN = 0.0254


def test_a_header_grown_into_the_plates_fails_and_catlin_is_clean(catlin_model) -> None:
    assert header_under_plate(check_context(model=catlin_model)) == []
    # D-G-SERVICE as it was: a 5 1/2" header on the 93 1/2" head, 2" into the plates.
    index, wall = next((i, w) for i, w in enumerate(catlin_model.walls) if w.tag == "W-G-S")
    members = tuple(replace(m, z1_m=m.z0_m + 5.5 * _IN)
                    if m.category == "header" and m.opening_tag == "D-G-SERVICE" else m
                    for m in wall.members)
    catlin_model.walls[index] = replace(wall, members=members)
    [finding] = header_under_plate(check_context(model=catlin_model))
    assert finding.result is Result.FAIL
    assert finding.element_tags == ("W-G-S", "D-G-SERVICE")
    assert "2.00\" into its own plates" in finding.message
