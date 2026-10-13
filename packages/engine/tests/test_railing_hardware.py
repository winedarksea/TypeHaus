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
from typehaus.model.placeables import WallAttachment
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


def test_an_offset_return_preserves_the_rail_and_sets_the_flange_normal_to_the_wall():
    wall = wall_along_x("W-T", 0.0, x0_m=0.0)
    attachment = WallAttachment(wall_ref="W-T", face="left", distance_from_start=inch(116))
    rail = _handrail(end_termination="wall_return", end_return_attachment=attachment)
    model = resolve_railings([rail], walls=[wall])
    assert not model.railing_findings
    solids = {s.tag: s for s in solids_of(model, rail.tag)}
    endpoint = solids["RL-H-RAIL1"].sweep.path[-1]
    assert endpoint[:2] == pytest.approx(rail.path[-1].xy_m)
    assert endpoint[2] == pytest.approx(inch(36).meters)
    ret = solids["RL-H-RETURN2"].sweep.path
    assert ret[0] == endpoint
    assert ret[1] == pytest.approx((inch(116).meters, 0.0, endpoint[2]))
    a, b = solids["RL-H-ENDPLATE2"].sweep.path
    assert a == ret[1]
    assert b == pytest.approx((a[0], mm(6).meters, a[2]))


@pytest.mark.parametrize(("wall_tag", "station", "wall_end", "message"), [
    ("MISSING", 116, 120, "missing return wall"),
    ("W-T", 130, 120, "outside its wall"),
    ("W-T", 100, 120, "return reach"),
    ("W-T", 119.5, 120, "not completely supported"),
])
def test_an_invalid_explicit_return_reports_an_error(wall_tag, station, wall_end, message):
    wall = wall_along_x("W-T", 0.0, x0_m=0, x1_m=inch(wall_end).meters)
    rail = _handrail(end_termination="wall_return", end_return_attachment=WallAttachment(
        wall_ref=wall_tag, face="left", distance_from_start=inch(station)))
    model = resolve_railings([rail], walls=[wall])
    assert "RETURN2" not in _tags(model, rail.tag)
    (finding,) = model.railing_findings
    assert finding.check_id == "integrity.railing_return_attachment"
    assert finding.severity.value == "error"
    assert message in finding.message


def test_an_attachment_requires_a_wall_return_termination():
    with pytest.raises(ValueError, match="end_termination"):
        _handrail(end_return_attachment=WallAttachment(wall_ref="W-T", face="left",
                                                      distance_from_start=inch(116)))


@pytest.mark.parametrize("backend", ("libcst", "py"))
def test_return_attachment_round_trips_through_source_and_reference_remapping(tmp_path, backend):
    from _helpers import STARTER, copy_house

    from typehaus.model.remap import ReferenceRemap, remap_ops_for
    from typehaus.source import ProjectCoordinator, load_plan, writeback
    from typehaus.source.serialize import element_add_op

    house = copy_house(STARTER, tmp_path / "starter")
    source_path = house / "plan" / "placeables.py"
    before = source_path.read_text()
    coordinator = ProjectCoordinator(house)
    rail = _handrail(assembly=None, end_termination="wall_return",
                     end_return_attachment=WallAttachment(
                         wall_ref="W-101", face="left", distance_from_start=inch(96)))
    assert type(rail).model_validate(rail.model_dump()) == rail
    try:
        writeback.set_backend(backend)
        op = element_add_op(rail, tag=rail.tag, hint_list="MAIN_PLACEABLES")
        coordinator.apply_patch([op], coordinator.revision())
        loaded = load_plan(house)
        assert loaded.ok, loaded.findings
        added = loaded.plan.by_tag(rail.tag)
        assert added.end_return_attachment == rail.end_return_attachment
        remap = ReferenceRemap(renamed={"W-101": "W-102"},
                               shift={rail.tag: ft(12).meters}, reversed=frozenset({rail.tag}))
        coordinator.apply_patch(remap_ops_for(added, remap), coordinator.revision())
        loaded = load_plan(house)
        assert loaded.ok, loaded.findings
        attachment = loaded.plan.by_tag(rail.tag).end_return_attachment
        assert attachment.wall_ref == "W-102" and attachment.face == "right"
        assert attachment.distance_from_start.meters == pytest.approx(inch(48).meters, abs=1e-6)
        coordinator.undo()
        restored = load_plan(house).plan.by_tag(rail.tag)
        assert restored.end_return_attachment == rail.end_return_attachment
        coordinator.undo()
        assert source_path.read_text() == before
    finally:
        writeback.set_backend("libcst")


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
