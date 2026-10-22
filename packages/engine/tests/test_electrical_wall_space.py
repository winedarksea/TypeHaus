"""Roof-edge uncertainty must neither invent compliance nor hide known wall gaps."""

from dataclasses import replace

import pytest
from _electrical_helpers import room_plan

from typehaus.checks import build_context_from_model
from typehaus.checks.mep.electrical import receptacle_spacing
from typehaus.checks.mep.electrical_wall_space import (
    definite_coverage_gaps,
    uncertain_wall_space,
)
from typehaus.model import (
    Assembly,
    DeviceKind,
    ElectricalDevice,
    FloorOpening,
    FollowRoof,
    FramingSpec,
    Layer,
    LayerFunction,
    Roof,
    RoofForm,
    ft,
    inch,
    pt,
)
from typehaus.quantities import Pitch
from typehaus.resolve import resolve


def _outlet(tag, x, y):
    return ElectricalDevice(uid=f"{tag:0>10}", tag=tag, kind=DeviceKind.RECEPTACLE,
                            position=pt(ft(x), ft(y)))


def _sloped_room(project, *, plate=False, devices=()):
    plan = room_plan(project, devices)
    assembly = Assembly(tag="PLATE", layers=(Layer(
        name="plate", material_ref="spf", thickness=inch(5.5),
        function=LayerFunction.STRUCTURE,
        framing=FramingSpec(member="2x6", wall_frame="plate")),))
    library = plan.library.model_copy(update={"assemblies": (*plan.library.assemblies, assembly)})
    elements = []
    for element in plan.storey_elements("s1"):
        if element.tag in {"W-1", "W-3"}:
            element = element.model_copy(update={
                "top": inch(1.5),
                "assembly": "PLATE" if plate and element.tag == "W-1" else "EXT"})
        elif element.tag == "RM-1":
            element = element.model_copy(update={"ceiling": FollowRoof(roof_ref="RF")})
        elements.append(element)
    elements.append(Roof(uid="RFTEST0001", tag="RF", form=RoofForm.GABLE, pitch=Pitch(6, 12),
                         bearing_refs=("W-1", "W-3"), assembly="EXT", ridge_direction="x"))
    plan = plan.model_copy(update={"library": library, "elements": {"s1": tuple(elements)}})
    model, findings = resolve(plan)
    assert not [f.message for f in findings if f.severity.value == "error"]
    return model


def _room_findings(model):
    return [f for f in receptacle_spacing(build_context_from_model(model, []))
            if "RM-1" in f.element_tags]


def _intervals_in_feet(intervals):
    return [(round(a / 0.3048, 7), round(b / 0.3048, 7)) for a, b in intervals]


def _gaps(perimeter, positions=(), breaks=(), uncertain=()):
    return _intervals_in_feet(definite_coverage_gaps(
        ft(perimeter).meters, [ft(p).meters for p in positions],
        [(ft(a).meters, ft(b).meters) for a, b in breaks],
        tuple((ft(a).meters, ft(b).meters) for a, b in uncertain)))


def test_low_knee_wall_and_tapered_gable_remain_required(project):
    model = _sloped_room(project, devices=(_outlet("RC", 10, 7),))
    walls = [replace(w, top_z0_m=inch(2).meters, top_z1_m=ft(8).meters)
             if w.tag == "W-2" else w for w in model.walls]
    model = replace(model, walls=walls)
    uncertainty = uncertain_wall_space(model, model.rooms[0], list(model.rooms[0].clear_face))
    assert not uncertainty.intervals  # Even the 1.5-inch stud wall stays required.
    assert [f.result.value for f in _room_findings(model)] == ["fail"]


def test_ceiling_height_alone_cannot_create_an_exemption(project):
    plan = room_plan(project, (_outlet("RC", 10, 7),))
    for height in (ft(9), ft(3)):
        elements = tuple(e.model_copy(update={"ceiling": height})
                         if e.tag == "RM-1" else e for e in plan.storey_elements("s1"))
        model, _ = resolve(plan.model_copy(update={"elements": {"s1": elements}}))
        assert [f.result.value for f in _room_findings(model)] == ["fail"]


def test_plate_only_edge_is_unknown_even_with_full_coverage(project):
    devices = tuple(_outlet(f"RC-{i}", x, y) for i, (x, y) in enumerate(
        [(5, 0), (15, 0), (20, 4), (20, 10), (15, 14), (5, 14), (0, 10), (0, 4)]))
    findings = _room_findings(_sloped_room(project, plate=True, devices=devices))
    assert [f.result.value for f in findings] == ["unknown"]
    assert findings[0].element_tags == ("RM-1", "W-1")
    assert "rafter plate" in findings[0].message


def test_definite_failure_and_plate_uncertainty_are_both_reported(project):
    model = _sloped_room(project, plate=True, devices=(_outlet("RC", 10, 7),))
    findings = _room_findings(model)
    assert {f.result.value for f in findings} == {"fail", "unknown"}
    assert next(f for f in findings if f.result.value == "fail").severity.value == "warn"


def test_unresolved_roof_does_not_pass_or_invent_definite_failures(project):
    model = _sloped_room(project, plate=True, devices=(_outlet("RC", 10, 7),))
    findings = _room_findings(replace(model, roofs=[]))
    assert [f.result.value for f in findings] == ["unknown"]
    assert "RF" in findings[0].element_tags
    assert "geometry is unresolved" in findings[0].message


def test_missing_boundary_host_stays_visible(project):
    model = _sloped_room(project, devices=(_outlet("RC", 10, 7),))
    findings = _room_findings(replace(model, walls=[]))
    assert [f.result.value for f in findings] == ["unknown"]
    assert "no resolved wall host" in findings[0].message


def test_gap_midpoint_on_plate_cannot_hide_known_wall_failures():
    assert _gaps(40, [4], uncertain=[(18, 30)]) == [(10, 18), (30, 38)]


def test_alternative_interpretations_must_fail_at_the_same_known_position():
    # Including the uncertain edge lets its outlet serve the adjacent actual wall;
    # excluding it removes that outlet. Only the uncovered portions common to both fail.
    assert _gaps(40, [20], uncertain=[(18, 22)]) == [(0, 14), (26, 40)]


@pytest.mark.parametrize("perimeter,positions,expected", [
    (24, [6, 18], []),
    (24.01, [6, 18], [(24, 24.01)]),
    (40, [20], [(0, 14), (26, 40)]),
])
def test_exact_reach_and_cyclic_seam(perimeter, positions, expected):
    assert _gaps(perimeter, positions) == expected


def test_overlapping_breaks_do_not_create_spurious_wall_spaces():
    assert _gaps(40, [4, 16, 36], [(20, 25), (23, 30)]) == []
    assert _gaps(40, [4, 16, 36], [(20, 30)]) == []


@pytest.mark.parametrize("length,expected", [(1.99, []), (2, [(10, 12)])])
def test_two_foot_minimum_applies_to_a_whole_unbroken_space(length, expected):
    assert _gaps(40, [], [(0, 10), (10 + length, 40)]) == expected


def test_all_uncertain_boundary_cannot_become_a_vacuous_pass():
    assert _gaps(40, [], uncertain=[(0, 40)]) == []
    # Classification still carries all uncertainty even though no known wall can fail.


def test_floor_opening_breaks_coverage_without_a_catlin_device_dependency(project):
    devices = (_outlet("SOUTH1", 5, 0), _outlet("SOUTH2", 15, 0),
               _outlet("WEST", 0, 5), _outlet("EAST", 20, 5))
    plan = room_plan(project, devices)
    opening = FloorOpening(uid="WELLTEST01", tag="WELL", outline=(
        pt(ft(0), ft(10.5)), pt(ft(20), ft(10.5)),
        pt(ft(20), ft(14)), pt(ft(0), ft(14))))
    elements = (*plan.storey_elements("s1"), opening)
    plan = plan.model_copy(update={"elements": {"s1": elements}})
    model, _ = resolve(plan)
    assert [f.result.value for f in _room_findings(model)] == ["pass"]
    stranded = tuple(e.model_copy(update={"position": pt(ft(20), ft(12))})
                     if e.tag == "EAST" else e for e in elements)
    model, _ = resolve(plan.model_copy(update={"elements": {"s1": stranded}}))
    assert [f.result.value for f in _room_findings(model)] == ["fail"]


def test_uncertain_interval_crossing_the_seam_preserves_known_failures():
    assert _gaps(40, [24], uncertain=[(0, 10), (38, 40)]) == [(10, 18), (30, 38)]
