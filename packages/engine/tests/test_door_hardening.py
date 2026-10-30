"""Authored hardware, doubled packs and net cavity replacements share one door type."""
from types import SimpleNamespace as NS

import pytest
from pydantic import ValidationError
from shapely.geometry import Polygon

from typehaus import DoorHardwareItem, DoorType, JambFraming, inch, m
from typehaus.checks.integrity.door_hardware import door_hardware
from typehaus.resolve.framing.openings import WallOpening, frame_opening
from typehaus.resolve.framing.tables import jamb_pack_counts, opening_framing_pattern
from typehaus.resolve.jamb_fill import resolve_jamb_fills
from typehaus.resolve.model import FramedMember, ResolvedLayer, ResolvedModel, ResolvedOpening, ResolvedWall
from typehaus.takeoff.door_hardening import authored_hardware_rows, door_field_paint_rows
from typehaus.takeoff.envelope import envelope_layer_takeoff
from typehaus.takeoff.openings import opening_takeoff


@pytest.fixture
def hardware():
    return (DoorHardwareItem(role="hinge", product_ref="hinge", height=inch(20),
                             installation="Anchor hinge with 3 inch screws."),
            DoorHardwareItem(role="passage", product_ref="lever", height=inch(36),
                             installation="Solid composite shims behind latch strike."),
            DoorHardwareItem(role="deadbolt", product_ref="deadbolt", height=inch(41.5),
                             installation="Solid composite shims behind deadbolt strike."))


def test_hardware_model_constraints(hardware):
    with pytest.raises(ValidationError):
        DoorHardwareItem.model_validate({**hardware[0].model_dump(), "quantity": 0})
    with pytest.raises(ValidationError):
        DoorHardwareItem(role="viewer", product_ref="viewer", height=inch(-1), installation="Seal.")
    with pytest.raises(ValidationError):
        JambFraming(kings=0, jacks=2)


def test_integrity_reports_missing_references_bad_heights_and_incomplete_sets(hardware):
    spec = DoorType(tag="DT", width=inch(36), height=inch(40), hardware=hardware)
    ctx = NS(plan=NS(library=NS(door_types=[spec], products=[], materials=[])),
             model=NS(openings=[]))
    messages = [finding.message for finding in door_hardware(ctx)]
    assert sum("unknown hardware" in message for message in messages) == 3
    assert any("inside the leaf" in message for message in messages)
    spec = spec.model_copy(update={"hardware": (), "jamb_framing": JambFraming(
        kings=2, jacks=2, blocking=True)})
    ctx.plan.library.door_types = [spec]
    assert any("anchor heights" in finding.message for finding in door_hardware(ctx))
    item = DoorHardwareItem(role="strike_reinforcement", product_ref="plate", installation="Shim.")
    ctx.plan.library.door_types = [spec.model_copy(update={"hardware": (item,)})]
    assert any("requires a passage" in finding.message for finding in door_hardware(ctx))


def test_jamb_override_reaches_pack_and_header():
    framing = JambFraming(kings=2, jacks=2)
    opening = WallOpening(1.5, .9, 2.1, 0, True, tag="D", jamb_framing=framing)
    pattern = opening_framing_pattern(None)
    assert jamb_pack_counts(m(.9), pattern, framing) == (2, 2)
    wall = NS(uid="w", base_ref_z_m=0)
    members = frame_opening(wall, (1, 0), (0, 0), opening, "2x6", .0381,
                           lambda station: 2.9, 0, .4064)
    assert sum(member.category == "king" for member in members) == 4
    assert sum(member.category == "jack" for member in members) == 4
    header = next(member for member in members if member.category == "header")
    assert header.length_m == pytest.approx(.9 + 4*.0381)


@pytest.mark.parametrize("batt", ["fiberglass", "mineral-wool"])
def test_jamb_foam_replaces_exact_clear_bay_area_and_blocks_at_anchors(hardware, batt):
    ring = ((0, -.06985), (3, -.06985), (3, .06985), (0, .06985))
    layers = (ResolvedLayer("stud", "wood", "structure", .1397, ring),
              ResolvedLayer("batt", batt, "insulation", .1397, ring, is_cavity=True))
    members = tuple(FramedMember("w", str(station), "king" if .8 < station < 2.2 else "stud",
        "2x6", (station, 0), (station, 0), .0381, 3, 2.9619, orient=(1, 0))
        for station in (.4, .91665, 2.08335, 2.6))
    members += (FramedMember("w", "plate", "plate", "2x6", (0, 0), (3, 0), 0, .0381, 3),)
    wall = ResolvedWall("w", "W", "main", "A", ((0, 0), (3, 0)), layers, 0, 3,
                        members=members)
    spec = DoorType(tag="DT", width=m(.9), height=m(2.1), hardware=hardware,
                    jamb_framing=JambFraming(kings=2, jacks=2, blocking=True,
                                            bay_fill_ref="foam"))
    # Empty non-wall collections make this a hand-worked two-bay takeoff.
    plan = NS(library=NS(door_types=[spec], material=lambda ref: None, materials=()),
              all_elements=lambda: (), storeys=())
    opening = ResolvedOpening("d", "D", "W", "DT", .9, 2.1, 0, 1.5, "door", True)
    model = ResolvedModel(plan, walls=[wall], openings=[opening])
    before = envelope_layer_takeoff(model)
    resolve_jamb_fills(model)
    clear_width = .8976 - .41905
    expected_area = 2 * clear_width * (3 - .0381 - 3*.0381)
    assert sum(fill.area_m2 for fill in model.jamb_fills) == pytest.approx(expected_area)
    blocks = [member for member in model.wall("W").members if member.category == "door_blocking"]
    assert len(blocks) == 6
    assert sorted({(member.z0_m+member.z1_m)/2 for member in blocks}) == pytest.approx(
        sorted(item.height.meters for item in hardware))
    assert all(Polygon(fill.bay_polygon).is_valid for fill in model.jamb_fills)
    after = envelope_layer_takeoff(model)
    get = lambda rows, material: sum(row["net_area_sqft"] for row in rows
                                     if row["material"] == material)
    assert get(before, batt) - get(after, batt) == pytest.approx(expected_area/.09290304, abs=.11)
    assert get(after, "foam") == pytest.approx(expected_area/.09290304, abs=.06)
    resolve_jamb_fills(model)
    assert sum(fill.area_m2 for fill in model.jamb_fills) == pytest.approx(expected_area)
    assert len([member for member in model.wall("W").members
                if member.category == "door_blocking"]) == 6


def test_catlin_hardware_scope_takeoff_and_finish(catlin_model_ro):
    model = catlin_model_ro
    expected = {"D-M-ENTRY", "D-M-BALC", "D-B-PATIO", "D-S-DECK-E"}
    rows = opening_takeoff(model)
    authored = {tag for row in rows if row["hardware_authored"] for tag in row["tags"]}
    assert authored == expected
    assert {fill.opening_tag for fill in model.jamb_fills} == expected
    assert {fill.replaced_material_ref for fill in model.jamb_fills} == {"fiberglass", "mineral-wool"}
    hardware_rows = authored_hardware_rows(model)
    from typehaus.takeoff.cost_codes import cost_code

    assert all(cost_code("hardware", row["part_number"], row=row).trade == "openings"
               for row in hardware_rows)
    count = lambda ref: sum(row["count"] for row in hardware_rows if row["hardware_tag"] == ref)
    assert count("PROD-SCHLAGE-BE889WB") == 1
    assert count("PROD-ENDURA-PANOLOCK-PLUS") == 3
    assert count("PROD-THERMATRU-HINGE") == 21
    paint = door_field_paint_rows(model)
    assert {row["material"] for row in paint} == {"door-paint-black", "door-paint-white"}
    assert paint[0]["net_area_sqft"] == paint[1]["net_area_sqft"]
    entry = next(opening for opening in model.openings if opening.tag == "D-M-ENTRY")
    parts = model.geometry.by_uid(entry.uid).parts
    assert {part.catalog.material_ref for part in parts if part.key.startswith("leaf:")} == {
        "door-paint-black", "door-paint-white"}
    for tag in expected:
        opening = next(opening for opening in model.openings if opening.tag == tag)
        wall = model.wall(opening.host_wall)
        assert any(member.opening_tag == tag and member.category == "door_blocking"
                   for member in model.all_members())
    assert sum(member.category == "king" for member in model.wall(entry.host_wall).members) == 4


def test_hardware_schedule_includes_installation_and_heights(catlin_model_ro):
    from typehaus.emit.draw.schedules.door_hardware import hardware_schedule_rows

    rows = hardware_schedule_rows(catlin_model_ro)
    text = " ".join(str(cell) for row in rows for cell in row)
    assert "BE889WB" in text and "DS2000" in text
    assert '60"' in text and '41.5"' in text
    assert "Solid composite shims" in text and "low-expansion foam" in text
