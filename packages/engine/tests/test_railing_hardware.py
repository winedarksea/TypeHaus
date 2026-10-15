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
from typehaus.resolve.model import ResolvedOpening
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
    assert any(f.check_id == "geometry.railing_return_unanchored"
               for f in model.railing_findings)
    assert not any(t.startswith("BRACKET") for t in _tags(model, "RL-H"))


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
    assert not any(t.startswith("BRACKET") for t in _tags(model, "RL-H"))
    assert all(f.check_id == "geometry.railing_bracket_unanchored"
               for f in model.railing_findings)


def _window(**overrides):
    values = dict(uid="WINDOW0001", tag="WIN-T", host_wall="W-T", type_ref=None,
                  width_m=inch(24).meters, height_m=inch(48).meters,
                  sill_m=inch(24).meters, center_along_m=1.0 + inch(60).meters,
                  kind="window", is_door=False)
    values.update(overrides)
    return ResolvedOpening(**values)


@pytest.mark.parametrize("end_in", [60, 47])
def test_return_rejects_window_and_plate_overlapping_jamb(end_in):
    # A 70 mm plate centred 1" short of the jamb still overlaps the opening.
    rail = _handrail(path=(pt(inch(end_in), inch(2.375)), pt(inch(120), inch(2.375))),
                     start_termination="wall_return")
    wall = wall_along_x("W-T", 0.0, z0_m=0)
    model = resolve_railings([rail], walls=[wall], openings=[_window()])
    assert "RETURN1" not in _tags(model, "RL-H")
    assert "ENDPLATE1" not in _tags(model, "RL-H")
    assert any(f.check_id == "geometry.railing_return_unanchored"
               and f.element_tags == ("RL-H", "WIN-T") for f in model.railing_findings)


@pytest.mark.parametrize(("end_in", "height_in"), [(46, 36), (60, 76)])
def test_return_mounts_beside_or_above_window_across_storeys(end_in, height_in):
    rail = _handrail(path=(pt(inch(end_in), inch(2.375)), pt(inch(120), inch(2.375))),
                     height=inch(height_in), start_termination="wall_return")
    wall = wall_along_x("W-T", 0.0, storey="below", z0_m=0)
    model = resolve_railings([rail], walls=[wall], openings=[_window()])
    assert {"RETURN1", "ENDPLATE1"} <= set(_tags(model, "RL-H"))


def test_bracket_rejects_its_full_vertical_footprint_at_window_head():
    rail = _handrail(height=inch(73))
    model = resolve_railings([rail], walls=[wall_along_x("W-T", 0, z0_m=0)],
                             openings=[_window(center_along_m=1.0 + inch(40).meters)])
    # The rail is above the 72" head; the bracket arm is still inside the opening.
    assert "BRACKET2" not in _tags(model, "RL-H")
    assert any(f.check_id == "geometry.railing_bracket_unanchored"
               and f.element_tags == ("RL-H", "WIN-T") for f in model.railing_findings)


def test_opening_sill_uses_wall_reference_elevation():
    from dataclasses import replace

    wall = replace(wall_along_x("W-T", 0, z0_m=inch(108).meters,
                                z1_m=inch(240).meters), plate_base_z_m=inch(120).meters)
    rail = _handrail(base_elevation=inch(120), height=inch(20),
                     path=(pt(inch(60), inch(2.375)), pt(inch(120), inch(2.375))),
                     start_termination="wall_return")
    model = resolve_railings([rail], walls=[wall], openings=[_window()])
    # The wall extends down over a rim; the sill is still measured from its floor.
    assert "RETURN1" in _tags(model, "RL-H")


def test_authored_angled_return_reaches_solid_jamb_without_moving_grip():
    rail = _handrail(path=(pt(inch(47), inch(2.375)), pt(inch(120), inch(2.375))),
                     start_termination="wall_return", start_return_target=pt(inch(46), ft(0)))
    model = resolve_railings([rail], walls=[wall_along_x("W-T", 0, z0_m=0)],
                             openings=[_window()])
    ret = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-RETURN1")
    assert ret.sweep.path[0][:2] == pytest.approx(rail.path[0].xy_m)
    assert ret.sweep.path[-1][:2] == pytest.approx(rail.start_return_target.xy_m)
    plate = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-ENDPLATE1")
    assert plate.sweep.path[0][0] == pytest.approx(plate.sweep.path[-1][0])


@pytest.mark.parametrize("target_in", [60, 20])
def test_authored_return_target_cannot_land_in_opening_or_exceed_reach(target_in):
    rail = _handrail(path=(pt(inch(47), inch(2.375)), pt(inch(120), inch(2.375))),
                     start_termination="wall_return",
                     start_return_target=pt(inch(target_in), ft(0)))
    model = resolve_railings([rail], walls=[wall_along_x("W-T", 0, z0_m=0)],
                             openings=[_window()])
    assert "RETURN1" not in _tags(model, "RL-H")


def test_tall_bracket_anchors_below_the_rail_on_a_lower_wall():
    rail = _handrail(bracket_drop_overrides=((2, inch(14)),))
    wall = wall_along_x("W-T", 0, z0_m=0, z1_m=inch(24).meters)
    model = resolve_railings([rail], walls=[wall])
    bracket = next(s for s in solids_of(model, "RL-H") if s.tag == "RL-H-BRACKET2")
    assert bracket.sweep is not None
    anchor, elbow, rail_end = bracket.sweep.path
    assert anchor == pytest.approx((inch(40).meters, 0, inch(22).meters))
    assert elbow == pytest.approx((inch(40).meters, inch(2.375).meters, inch(22).meters))
    assert rail_end == pytest.approx((inch(40).meters, inch(2.375).meters, inch(36).meters))
    assert not any('bracket 2 ' in f.message for f in model.railing_findings)


@pytest.mark.parametrize(("drop_in", "supported"), [(14, True), (10, False)])
def test_tall_bracket_checks_the_wall_anchor_footprint_not_the_outboard_upright(drop_in, supported):
    rail = _handrail(bracket_drop_overrides=((2, inch(drop_in)),))
    wall = wall_along_x("W-T", 0, z0_m=0)
    model = resolve_railings([rail], walls=[wall],
                             openings=[_window(center_along_m=1 + inch(40).meters)])
    assert ("BRACKET2" in _tags(model, "RL-H")) is supported
    if not supported:
        assert any('bracket 2 ' in f.message and f.element_tags == ('RL-H', 'WIN-T')
                   for f in model.railing_findings)
