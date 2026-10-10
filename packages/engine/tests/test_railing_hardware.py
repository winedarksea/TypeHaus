"""A handrail's hardware as drawn: its section, its wall returns and where its brackets land.

``resolve/railings/parts.py`` (diameter), ``terminations.py`` (returns, end plates) and
``wall_contact.py`` (the finish face a bracket or a return reaches).
"""

from __future__ import annotations

import pytest
from _railing_fixtures import (
    inches,
    railing,
    railing_type,
    resolve_railings,
    solids_of,
    wall_along_x,
)

from typehaus.model.enums import RailingKind
from typehaus.quantities import ft, inch, mm, pt
from typehaus.resolve.sweep import profile_radius_m


def _handrail(tag="RL-H", y_in=2.375, **kw):
    defaults = dict(path=(pt(ft(0), inch(y_in)), pt(ft(10), inch(y_in))), mount="wall",
                    kind=RailingKind.METAL_SURFACE_MOUNT, rail_count=1, height=inch(36),
                    post_spacing=inch(48), role="handrail")
    defaults.update(kw)
    return railing(tag, **defaults)


def _tags(model, tag):
    return sorted(s.tag[len(tag) + 1:] for s in solids_of(model, tag))


def test_a_type_diameter_draws_the_rail_at_that_diameter():
    product = railing_type("RT-TI", rail_diameter=mm(42))
    rail = _handrail(type_ref="RT-TI", graspable_profile="1.5in round — Type I")
    model = resolve_railings([rail], types=[product])
    (bar,) = solids_of(model, "RL-H", "railing")[-1:]
    assert bar.tag == "RL-H-RAIL1"
    assert profile_radius_m(bar.sweep.profile) == pytest.approx(0.021, abs=1e-9)


@pytest.mark.parametrize(("profile", "radius_m"), [
    ("42mm round — Type I", 0.021),          # read as millimetres, not 42 inches
    ("1.5in round — Type I", 0.75 * 0.0254),
    ('1.25" round', 0.625 * 0.0254),
])
def test_a_profile_string_states_its_unit(profile, radius_m):
    model = resolve_railings([_handrail(graspable_profile=profile)])
    bar = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-RAIL1")
    assert profile_radius_m(bar.sweep.profile) == pytest.approx(radius_m, abs=1e-9)


def test_a_wall_return_draws_return_and_end_plate_and_drops_that_end_bracket():
    rail = _handrail(start_termination="wall_return", end_termination="wall_return",
                     graspable_profile="42mm round")
    model = resolve_railings([rail], walls=[wall_along_x("W-T", 0.0)])
    tags = _tags(model, "RL-H")
    assert {"RETURN1", "RETURN2", "ENDPLATE1", "ENDPLATE2"} <= set(tags)
    # 10' at 48" is three 40" bays: stations 0, 40, 80, 120 — the two ends return instead.
    assert sorted(t for t in tags if t.startswith("BRACKET")) == ["BRACKET2", "BRACKET3"]
    ret = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-RETURN1")
    (_x0, y0, _z0), (_x1, y1, _z1) = ret.sweep.path
    assert inches(y0) == pytest.approx(2.375) and inches(y1) == pytest.approx(0.0, abs=1e-6)


def test_a_wall_return_with_no_wall_warns_and_draws_nothing():
    rail = _handrail(start_termination="wall_return")
    model = resolve_railings([rail])
    assert "RETURN1" not in _tags(model, "RL-H")
    assert [f.check_id for f in model.railing_findings] == ["geometry.railing_return_unanchored"]


def test_brackets_reach_a_wall_on_another_storey():
    """A stair's rail is filed on the arrival storey; its wall belongs to the one below."""
    model = resolve_railings([_handrail()], walls=[wall_along_x("W-B", 0.0,
                                                                 storey="basement")])
    arm = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-BRACKET2")
    ys = [y for _x, y in arm.outline]
    assert inches(min(ys)) == pytest.approx(0.0, abs=1e-6)
    assert inches(max(ys)) == pytest.approx(2.375)


def test_brackets_land_on_the_finish_face_not_the_axis_offset():
    """A face-aligned wall: the axis is 1" off the body's centreline."""
    wall = wall_along_x("W-F", 0.0, depth_m=0.14, axis_y_m=-0.0954)
    model = resolve_railings([_handrail()], walls=[wall])
    arm = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-BRACKET2")
    assert inches(min(y for _x, y in arm.outline)) == pytest.approx(0.0, abs=1e-6)


def test_a_wall_the_rail_dies_into_end_on_is_not_its_wall():
    """Only a wall alongside the rail counts; one square across its end does not."""
    rail = _handrail(path=(pt(inch(2.375), ft(0)), pt(inch(2.375), ft(10))))
    model = resolve_railings([rail], walls=[wall_along_x("W-X", -0.05, x0_m=-1.0,
                                                         x1_m=1.0)])
    arm = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-BRACKET1")
    xs = [x for x, _y in arm.outline]
    assert inches(max(xs) - min(xs)) == pytest.approx(1.0, abs=1e-6), "a stub, not an arm"
