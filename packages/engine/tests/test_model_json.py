"""WP5 — model.json serialization contract: every member dict carries a pre-resolved
cross-section (the UI never parses ``profile`` strings itself)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.server.model_json import model_to_dict
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_payload():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model_to_dict(model)


def _all_members(payload):
    for wall in payload["walls"]:
        yield from wall["members"]
    for roof in payload["roofs"]:
        yield from roof["members"]
    for floor in payload["floors"]:
        yield from floor["members"]
    for stair in payload["stairs"]:
        yield from stair["members"]


def test_every_member_carries_shape_width_depth(catlin_payload):
    members = list(_all_members(catlin_payload))
    assert members
    for member in members:
        assert member["shape"] in ("rect", "i_joist")
        assert member["width_m"] > 0
        assert member["depth_m"] > 0


def test_skin_members_carry_a_material_and_lumber_does_not(catlin_payload):
    """The viewer colours a member by material when it has one, by category otherwise.

    Without the material the wall->roof closure and the roof-edge band fall through to the
    grey category fallback, which is what made the garage gable read as unwanted fill and
    left the house's standing seam stopping short of the roof's.
    """
    members = list(_all_members(catlin_payload))
    assert all("material" in member for member in members)
    house = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-HOUSE")
    band = [m for m in house["members"] if m["key"].endswith("-edge-cladding")]
    assert band and all(m["material"] == "standing-seam" for m in band)
    garage = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-GARAGE")
    gable = [m for m in garage["members"]
             if "W-G-E-closure-" in m["key"] and m["category"] == "cladding"]
    assert gable and all(m["material"] == "standing-seam" for m in gable)
    studs = [m for m in house["members"] if m["category"] == "rafter"]
    assert studs and all(m["material"] is None for m in studs)


def test_construction_returns_serialize_with_their_overlay_metadata(catlin_payload):
    """ConstructionRule returns reach the browser as their own records, not as solids.

    The solid mirror used to be the only path to model.json, and it carried none of the
    lap / sealant / flashing / returning-layer data the Inspector wants. Dropping it (the
    prisms were mis-placed gray fins in 3D) means these records have to be serialized.
    """
    returns = catlin_payload["construction_returns"]
    assert returns
    assert not [s for s in catlin_payload["solids"] if s["category"].startswith("return:")]
    uids = [r["uid"] for r in returns]
    assert uids == sorted(uids)
    for record in returns:
        assert record["material_ref"]
        assert record["tag"].startswith("CR-")
        assert len(record["outline"]) >= 3
        assert record["z1_m"] > record["z0_m"]
        assert record["length_m"] > 0.0
        assert record["element_tags"]


def test_second_floor_joists_are_i_joists(catlin_payload):
    floor = next(f for f in catlin_payload["floors"] if f["tag"] == "FS-SECOND")
    joists = [m for m in floor["members"] if m["category"] == "joist"]
    assert joists
    assert all(m["shape"] == "i_joist" for m in joists)
    assert all(m["flange_width_m"] is not None for m in joists)


def test_stud_carries_orient(catlin_payload):
    wall = next(w for w in catlin_payload["walls"] if w["tag"] == "W-M-S1")
    studs = [m for m in wall["members"] if m["category"] == "stud"]
    assert studs
    assert all(m["orient"] is not None and len(m["orient"]) == 2 for m in studs)


def test_roofs_carry_bearing_datum_and_layer_edge_setbacks(catlin_payload):
    """model.json contract: every roof serializes ``bearing_z_m`` and
    ``layer_edge_setbacks``; the rafter-framed house roof's deck plane rides ~0.2719 m
    above the plate and its setbacks step monotonically deck >= foam >= batten >= metal."""
    from typehaus.quantities import inch

    for roof in catlin_payload["roofs"]:
        assert "bearing_z_m" in roof
        assert "layer_edge_setbacks" in roof
    house = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-HOUSE")
    assert house["eave_z_m"] - house["bearing_z_m"] == pytest.approx(
        inch(11.875 - 3.5 / 3.0).meters)
    entries = {entry["layer"]: entry for entry in house["layer_edge_setbacks"]}
    assert entries
    for edge in ("west", "east", "south", "north"):
        assert (entries["deck"][edge] >= entries["polyiso"][edge]
                >= entries["batten-gap"][edge] >= entries["roofing"][edge])
    garage = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-GARAGE")
    assert garage["layer_edge_setbacks"] == []  # truss roof deferred


def test_ridge_beam_member_carries_multi_ply_width(catlin_payload):
    roof = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-HOUSE")
    beams = [m for m in roof["members"] if m["category"] == "ridge_beam"]
    assert len(beams) == 1
    assert beams[0]["plies"] == 3
    assert beams[0]["shape"] == "rect"


def test_opening_kind_serializes_all_interchange_categories(catlin_model):
    model = deepcopy(catlin_model)
    source = model.openings[0]
    model.openings[0] = replace(source, kind="rough_opening", is_door=False, type_ref=None)

    payload = model_to_dict(model)
    kinds = {opening["kind"] for opening in payload["openings"]}
    assert {"door", "window", "rough_opening"} <= kinds
    rough = next(opening for opening in payload["openings"] if opening["kind"] == "rough_opening")
    assert rough["is_door"] is False


def test_openings_serialize_swing_and_framing_overlays(catlin_payload):
    door = next(opening for opening in catlin_payload["openings"] if opening["is_door"])
    assert len(door["swing_clearance"]) == 10
    assert len(door["framing_bumper"]) == 4


def test_sunken_garden_arch_openings_serialize_their_rise(catlin_payload):
    arches = [opening for opening in catlin_payload["openings"]
              if opening["tag"].startswith("AO-ARCH-")]
    assert len(arches) == 2
    assert all(opening["arch_rise_m"] == pytest.approx(1.2192) for opening in arches)


def test_site_context_serializes_grade_parcel_and_spot_elevations(catlin_payload):
    site = catlin_payload["site"]
    assert {"grade_m", "parcel", "spot_elevations"} <= site.keys()
    assert site["grade_m"] is None or isinstance(site["grade_m"], float)
    assert isinstance(site["parcel"], list)
    assert all(set(spot) == {"position", "elevation_m"}
               for spot in site["spot_elevations"])


def test_model_json_serializes_finished_height_above_average_grade(catlin_payload):
    summary = catlin_payload["building_height_summary"]
    assert summary["average_ground_grade_m"] == pytest.approx(0.0)
    assert {row["roof_tag"] for row in summary["roofs"]} == {"RF-HOUSE", "RF-GARAGE"}
    assert all(row["peak_above_grade_m"] > row["midpoint_above_grade_m"] > 0
               for row in summary["roofs"])


def test_project_serializes_the_active_clearance_code_profile(catlin_payload):
    assert "active_code_profile" in catlin_payload["project"]


def test_stairs_payload_carries_landing_depth(catlin_payload):
    stairs = {stair["tag"]: stair for stair in catlin_payload["stairs"]}
    assert "landing_depth_m" in stairs["ST-B2M"]
    # ST-B2M authors landing_depth=ft(4); the winder stair authors none.
    assert stairs["ST-B2M"]["landing_depth_m"] == pytest.approx(1.2192)
    assert stairs["ST-S2A"]["landing_depth_m"] is None
