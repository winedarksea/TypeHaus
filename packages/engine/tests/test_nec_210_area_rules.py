"""NEC 210.52 and 210.70(A)(2)(3) readings (docs/code-notes/nec-2026-paraphrase-210-422-410.md)."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.mep.electrical_area_receptacles import _centreline_m
from typehaus.checks.mep.electrical_spacing import receptacle_spacing
from typehaus.checks.mep.electrical_stair_lighting import stair_lighting_control
from typehaus.checks.registry import CheckContext, Preferences

_FT = 0.3048


def _context(model, storey: str, edit) -> CheckContext:
    """A context whose plan has ``edit`` applied to one storey's elements (model untouched)."""
    plan = model.plan.with_elements(storey, edit(list(model.plan.storey_elements(storey))))
    return CheckContext(plan=plan, model=model, preferences=Preferences(), profile=MN_2020)


def test_hallway_centreline_is_the_equivalent_rectangle():
    assert _centreline_m(Polygon([(0, 0), (12, 0), (12, 3), (0, 3)])) == pytest.approx(12)
    ell = Polygon([(0, 0), (10, 0), (10, 3), (3, 3), (3, 10), (0, 10)])  # 3 ft wide L
    assert 15 < _centreline_m(ell) < 18  # centreline 15.5-17 ft


def test_stair_light_switched_at_one_level_only_fails(catlin_model_ro):
    """ST-M2S's chandelier on its old pair (both switches upstairs) leaves no light switched
    from the main floor: the foot can (ED-M-STAIR-CAN1) is a different light."""
    graded = {f.element_tags[0]: f.result.value for f in stair_lighting_control(
        _context(catlin_model_ro, "second", lambda es: es))}
    assert graded == {"ST-B2M": "pass", "ST-M2S": "pass", "ST-S2A": "pass"}

    def revert(elements):
        return [e.model_copy(update={"controlled_by": ("ED-S-STAIR-SW", "ED-S-LANDING-SW")})
                if e.tag == "ED-S-STAIR-CHAND" else e for e in elements]

    findings = {f.element_tags[0]: f for f in stair_lighting_control(
        _context(catlin_model_ro, "second", revert))}
    assert findings["ST-M2S"].result.value == "fail"
    assert "main no switch" in findings["ST-M2S"].message


def test_a_receptacle_on_the_walls_other_face_serves_no_wall_space(catlin_model_ro):
    """Without ED-B-PLAY-N-RC6/RC7, RM-B-PLAY-N's south wall has only the gym's receptacles
    on W-B-CE's other face, which no longer count for it."""
    findings = receptacle_spacing(_context(
        catlin_model_ro, "basement",
        lambda es: [e for e in es if e.tag not in ("ED-B-PLAY-N-RC6", "ED-B-PLAY-N-RC7")]))
    play = [f for f in findings if f.element_tags == ("RM-B-PLAY-N",)]
    assert [f.result.value for f in play] == ["fail"]
