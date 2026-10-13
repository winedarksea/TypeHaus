"""Local headers seat on support without displacing framing along the supported edge."""

from __future__ import annotations

import pytest
from _floor_opening_fixtures import _deck, _deck_plan
from shapely.geometry import Point, Polygon

from typehaus.hardware.config import HangerDetectionRules
from typehaus.joints.hung import hung_connections
from typehaus.model import FloorOpening, FloorSystem, Node
from typehaus.quantities import inch, pt
from typehaus.resolve import resolve
from typehaus.resolve.framing.footprint import member_footprint


@pytest.mark.parametrize(("support", "expected"), [
    (((54, 144),), ((48, 55.5),)),              # Low terminal gap: one wall seat.
    (((0, 82),), ((80.5, 88),)),               # High terminal gap: one wall seat.
    (((0, 60), (72, 144)), ((58.5, 73.5),)),    # Internal gap: a seat at each end.
    (((0, 144),), ()),                        # Complete support: no header.
    ((), ((48, 88),)),                        # No support: historical full edge.
    (((0, 54), (64, 70), (82, 144)), ((52.5, 65.5), (68.5, 83.5))),
    (((0, 54), (64, 66), (76, 144)), ((52.5, 77.5),)),  # Seats overlap the small island.
])
@pytest.mark.parametrize("along_x", (True, False))
def test_headers_cover_only_gaps_and_their_seats(support, expected, along_x):
    plan = _deck_plan(support_spans=support)
    if not along_x:
        def rotated(element):
            if isinstance(element, Node):
                return element.model_copy(update={
                    "position": pt(element.position.y, element.position.x)})
            if isinstance(element, FloorOpening):
                return element.model_copy(update={
                    "outline": tuple(pt(p.y, p.x) for p in element.outline)})
            if isinstance(element, FloorSystem):
                return element.model_copy(update={
                    "joists": element.joists.model_copy(update={"direction": "y"})})
            return element
        plan = plan.model_copy(update={"elements": {
            storey: tuple(rotated(el) for el in elements)
            for storey, elements in plan.elements.items()}})
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    headers = [m for m in model.floors[0].members
               if m.child_key.startswith("header-FO-1-0")]
    along = 1 if along_x else 0
    assert len(headers) == len(expected)
    for header, interval in zip(headers, expected, strict=True):
        assert (header.p0[along] / inch(1).meters,
                header.p1[along] / inch(1).meters) == pytest.approx(interval)
    for index, header in enumerate(headers):
        assert header.profile == "2-1.75x11.875 LVL"
        suffix = f"-{index}" if len(headers) > 1 else ""
        assert header.child_key == f"header-FO-1-0{suffix}"


def test_lining_extends_a_terminal_gap_to_its_framed_edge():
    _model, members = _deck(support_spans=((54, 144),), lining=True)
    header = members["header-FO-1-0"]
    assert header.p0[1] == pytest.approx(inch(47.375).meters)
    assert header.p1[1] == pytest.approx(inch(55.5).meters)
    assert header.length_m == pytest.approx(inch(8.125).meters)


@pytest.mark.parametrize("gap_end", (72, 62))
def test_joists_clip_at_local_headers_including_their_bearing_seats(gap_end):
    # y=64 cuts the header; when its seat ends at 63.5, the joist's width still meets it.
    _model, members = _deck(support_spans=((0, 60), (gap_end, 144)))
    for station, cut_end in ((64, 164.5), (80, 168)):
        (tail,) = [m for m in members.values() if m.category == "joist"
                   and abs(m.p0[1] - inch(station).meters) < 1e-9
                   and abs(m.p0[0] - inch(144).meters) < 1e-9]
        assert tail.p1[0] == pytest.approx(inch(cut_end).meters)


def test_each_trimmer_uses_support_at_its_own_end_of_the_edge():
    _model, members = _deck(support_spans=((0, 82),))
    assert members["trimmer-FO-1-0-0"].p0[0] == pytest.approx(inch(165.25).meters)
    assert members["trimmer-FO-1-1-0"].p0[0] == pytest.approx(inch(144).meters)


def test_each_header_is_sized_for_its_seated_span():
    plan = _deck_plan(support_spans=((22, 144),), member="2x10")
    opening = plan.by_tag("FO-1")
    extended = opening.model_copy(update={"outline": tuple(
        pt(p.x, inch(16 if p.y == inch(48) else 132)) for p in opening.outline)})
    plan = plan.model_copy(update={"elements": {
        **plan.elements, "second": tuple(extended if e.tag == opening.tag else e
                                        for e in plan.storey_elements("second"))}})
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    members = {m.child_key: m for m in model.floors[0].members}
    local, unsupported = members["header-FO-1-0"], members["header-FO-1-1"]
    assert local.profile == "2x10"
    assert local.length_m == pytest.approx(inch(7.5).meters)
    assert unsupported.child_key == "header-FO-1-1"
    assert unsupported.length_m == pytest.approx(inch(116).meters)
    assert unsupported.profile == "3-1.75x9.25 LVL"


def test_an_insufficient_wall_seat_is_reported_without_a_full_edge_fallback():
    _model, findings = resolve(_deck_plan(support_spans=((48, 49),)))
    assert any(f.check_id == "integrity.floor_opening_header_bearing"
               and f.severity.value == "error" for f in findings)


def test_catlin_local_header_seats_on_the_plate_and_hangs_from_the_south_trimmer(catlin_model_ro):
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-S-WEST")
    (header,) = [m for m in floor.members if m.child_key == "header-FO-S-STAIR-0"]
    wall = catlin_model_ro.wall("W-M-STRW")
    (plate,) = [m for m in wall.members
               if m.child_key == "plate-top-0"]
    seat = Polygon(member_footprint(header)[0]).intersection(Polygon(member_footprint(plate)[0]))
    assert seat.area == pytest.approx(inch(3.5).meters * inch(1.5).meters)
    assert header.z0_m >= wall.plate_top_z_m
    (trimmer,) = [m for m in floor.members if m.child_key == "trimmer-FO-S-STAIR-0-0"]
    assert (header.z0_m, header.z1_m) == (trimmer.z0_m, trimmer.z1_m)
    joints = [c for c in hung_connections(catlin_model_ro, HangerDetectionRules())
              if c.member_key.endswith(":header-FO-S-STAIR-0")]
    assert [c.carrier_tag for c in joints] == [f"{floor.uid}:trimmer-FO-S-STAIR-0-0"]
    # The header replaces the terminal ceiling nailer over the storage wall.
    assert not any(m.child_key == "partition-block-W-M-STOS2-003" for m in floor.members)
    assert header.p0[1] < inch(318).meters < header.p1[1]
    ring, _z0, _z1 = member_footprint(header)
    assert Polygon(ring).covers(Point(inch(120).meters, inch(318).meters))
