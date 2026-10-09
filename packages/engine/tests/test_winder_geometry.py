"""Balanced fan geometry in every stair orientation and malformed-layout rejection."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from shapely.geometry import LineString, Polygon

from typehaus.checks.code.mn_residential.stair_winders import (
    dimension_problems,
    winder_measurements,
    winder_treads,
)
from typehaus.model import Stair, WinderFramingSpec, WinderTurnSpec, ft, inch, pt
from typehaus.resolve.model import ResolvedStair
from typehaus.resolve.stairs.winder import _winder_stair_members, resolved_winder_layout
from typehaus.resolve.stairs.winder_geometry import (
    balanced_winder_turn,
    layout_from_spec,
    measure_winders,
    physical_nosing_line,
    shifted_line,
)


@pytest.fixture
def authored():
    return Stair(
        uid="TESTWINDER",
        tag="ST-WINDER",
        from_storey="main",
        to_storey="second",
        width=inch(36),
        start=pt(ft(0), ft(0)),
        layout="right_angle_winder",
        turn_direction="left",
        winder_count=3,
        tread_thickness=inch(1),
        riser_thickness=inch(0.75),
        newel_profile="6x6",
    )


def resolved(authored):
    members = _winder_stair_members(
        authored, 0, 0, 0, 16, inch(7.5).meters, inch(10).meters, inch(11).meters, inch(1).meters
    )
    return ResolvedStair(
        uid=authored.uid,
        tag=authored.tag,
        storey="main",
        to_storey="second",
        outline=[],
        riser_count=16,
        riser_height_m=inch(7.5).meters,
        tread_depth_m=inch(11).meters,
        run_direction=authored.run_direction,
        run_reversed=authored.run_reversed,
        layout=authored.layout,
        turn_direction=authored.turn_direction,
        winder_count=3,
        members=members,
        winder_turn=resolved_winder_layout(authored, 0, 0, inch(1).meters),
    )


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("reversed_run", [False, True])
@pytest.mark.parametrize("turn", ["left", "right"])
def test_all_run_and_turn_orientations_preserve_the_complete_measurement(
    authored, direction, reversed_run, turn
):
    stair = resolved(
        authored.model_copy(
            update={
                "run_direction": direction,
                "run_reversed": reversed_run,
                "turn_direction": turn,
            }
        )
    )
    measured = winder_measurements(stair)
    assert len(measured.walkline_depths_m) == len(measured.narrow_depths_m) == 3
    assert measured.walkline_depths_m == pytest.approx([inch(12.83665708).meters] * 3)
    assert min(measured.narrow_depths_m) >= inch(6.25).meters
    assert not dimension_problems(measured)
    for member in stair.members:
        if member.plan_outline:
            polygon = Polygon(member.plan_outline)
            assert polygon.is_valid and polygon.area > 0
        if member.category == "winder":
            assert (
                Polygon(member.plan_outline)
                .boundary.buffer(1e-7)
                .covers(LineString(member.nosing_line))
            )


@pytest.mark.parametrize("plies", [1, 2, 3])
def test_departing_rim_attachment_uses_the_actual_parallel_plies(authored, plies):
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.stairs.winder_framing import departing_rim_members

    stair = resolved(
        authored.model_copy(update={"winder_framing": WinderFramingSpec(departing_rim_plies=plies)})
    )
    rims = departing_rim_members(
        stair.members, stair.winder_turn, 2, plies, cross_section("2x8").width_m
    )
    assert len(rims) == plies
    for stringer in (m for m in stair.members if m.category == "stringer"):
        rim = next(m for m in rims if stringer.start_connection == f"winder-box-rim:{m.child_key}")
        assert (
            Polygon(rim.plan_outline)
            .buffer(1e-7)
            .covers(LineString((stringer.p0, stringer.p0)).centroid)
        )


@pytest.mark.parametrize("which", ["first", "last"])
def test_the_entering_winder_and_straight_transition_cannot_escape_the_check(authored, which):
    stair = resolved(authored)
    if which == "first":
        target = next(m for m in stair.members if m.child_key == "winder-000")
        normal = stair.winder_turn.normals[0]
        distance = inch(4).meters
    else:
        target = next(m for m in stair.members if m.child_key == "tread-000")
        normal = stair.winder_turn.normals[-1]
        distance = -inch(4).meters

    def moved(point):
        return point[0] + normal[0] * distance, point[1] + normal[1] * distance

    replacement = replace(
        target,
        p0=moved(target.p0),
        p1=moved(target.p1),
        plan_outline=[moved(p) for p in target.plan_outline] if target.plan_outline else None,
    )
    broken = replace(stair, members=tuple(replacement if m is target else m for m in stair.members))
    ctx = SimpleNamespace(model=SimpleNamespace(stairs=[broken]))
    [finding] = winder_treads(ctx)
    assert finding.result.value == "fail"
    assert "walkline depth below 10" in finding.message
    assert "3 winder depths" in finding.message


@pytest.mark.parametrize(
    "field,threshold,delta,expected",
    [
        ("walkline_depths_m", 10, 0, False),
        ("walkline_depths_m", 10, -0.001, True),
        ("narrow_depths_m", 6, 0, False),
        ("narrow_depths_m", 6, -0.001, True),
        ("variation", 0.375, 0, False),
        ("variation", 0.375, 0.001, True),
    ],
)
def test_exact_code_thresholds(authored, field, threshold, delta, expected):
    measured = winder_measurements(resolved(authored))
    if field == "variation":
        measured = replace(
            measured,
            walkline_depths_m=(
                inch(11).meters,
                inch(11).meters,
                inch(11 + threshold + delta).meters,
            ),
        )
    else:
        measured = replace(measured, **{field: (inch(threshold + delta).meters,) * 3})
    assert bool(dimension_problems(measured)) is expected


@pytest.mark.parametrize(
    "malformation", ["bowtie", "empty", "missing_edge", "reversed", "off_boundary", "inner_chord"]
)
def test_malformed_layouts_are_rejected_explicitly(malformation):
    spec = balanced_winder_turn(inch(36).meters, 3, inch(1).meters)
    if malformation == "bowtie":
        spec = spec.model_copy(
            update={
                "footprint": tuple(
                    pt(inch(x), inch(y))
                    for x, y in [(0, 0), (49.25, 49.25), (0, 49.25), (49.25, 0)]
                )
            }
        )
    elif malformation == "empty":
        spec = spec.model_copy(update={"footprint": ()})
    elif malformation == "missing_edge":
        spec = spec.model_copy(update={"riser_lines": spec.riser_lines[:-1]})
    elif malformation == "reversed":
        spec = spec.model_copy(update={"riser_lines": tuple(reversed(spec.riser_lines))})
    elif malformation == "off_boundary":
        spec = spec.model_copy(
            update={
                "riser_lines": (
                    (pt(inch(10), inch(10)), spec.riser_lines[0][1]),
                    *spec.riser_lines[1:],
                )
            }
        )
    else:
        spec = spec.model_copy(
            update={"inner_boundary": (spec.inner_boundary[0], spec.inner_boundary[-1])}
        )
    with pytest.raises(ValueError):
        layout_from_spec(spec, 3, inch(36).meters)


def test_valid_but_undersized_layout_remains_measurable(authored):
    full = balanced_winder_turn(inch(36).meters, 3, inch(1).meters)
    factor = 0.75

    def scaled(p):
        return pt(inch(p.x.meters / 0.0254 * factor), inch(p.y.meters / 0.0254 * factor))

    undersized = WinderTurnSpec(
        footprint=tuple(map(scaled, full.footprint)),
        inner_boundary=tuple(map(scaled, full.inner_boundary)),
        riser_lines=tuple(tuple(map(scaled, edge)) for edge in full.riser_lines),
    )
    layout = layout_from_spec(undersized, 3, inch(27).meters)
    noses = tuple(
        physical_nosing_line(layout.panel(i, inch(1).meters, 0), layout.normals[i])
        for i in range(3)
    ) + (shifted_line(layout.riser_lines[-1], layout.normals[-1], -inch(1).meters),)
    measured = measure_winders(
        layout.inner_boundary,
        layout.riser_lines,
        noses,
        tuple(layout.panel(i, inch(1).meters, 0) for i in range(3)),
    )
    assert len(measured.walkline_depths_m) == 3
    assert "depth within clear width below 6 inches" in dimension_problems(measured)


def test_an_interior_pinched_point_cannot_hide_behind_passing_inner_endpoints(authored):
    stair = resolved(authored)
    middle = next(m for m in stair.members if m.child_key == "winder-001")
    inner = stair.winder_turn.inner_boundary
    extended = Polygon(middle.plan_outline).union(
        Polygon((inner[1], inner[2], stair.winder_turn.centre))
    )
    assert extended.is_valid and isinstance(extended, Polygon)
    changed = replace(middle, plan_outline=list(extended.exterior.coords)[:-1])
    broken = replace(stair, members=tuple(changed if m is middle else m for m in stair.members))
    measured = winder_measurements(broken)
    assert measured.walkline_depths_m == pytest.approx(winder_measurements(stair).walkline_depths_m)
    assert min(measured.narrow_depths_m) < inch(6).meters
    assert "depth within clear width below 6 inches" in dimension_problems(measured)


def test_all_winder_flight_measures_its_actual_arrival_nosing(authored):
    from typehaus.resolve.stairs.finish import nosing_lip

    short = _winder_stair_members(
        authored, 0, 0, 0, 4, inch(7.5).meters, inch(10).meters, inch(11).meters, inch(1).meters
    )
    head = next(m for m in short if m.child_key == "riser-winder-head")
    lip = nosing_lip(head, "stairhead:nosing", "oak", inch(30).meters, inch(1).meters)
    stair = replace(resolved(authored), members=short, riser_count=4, finish_parts=(lip,))
    measured = winder_measurements(stair)
    assert len(measured.walkline_depths_m) == 3
    assert measured.walkline_depths_m == pytest.approx([inch(12.83665708).meters] * 3)
    assert not dimension_problems(measured)
