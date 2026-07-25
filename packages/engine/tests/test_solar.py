"""Rooftop PV array (WS5): fit, plane geometry, IFC/glTF emission, hardware, wattage."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.resolve.roof_geometry import roof_height_at
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_array_fit_and_wattage(catlin_model):
    """Landscape max fit: 6 modules per side of the 36' ridge, 12 x 440 W = 5,280 W."""
    panels = catlin_model.solar_panels
    assert len(panels) == 12
    west = [p for p in panels if p.tag.startswith("SP-A-PV-W")]
    east = [p for p in panels if p.tag.startswith("SP-A-PV-E")]
    assert len(west) == 6 and len(east) == 6
    assert sum(p.watts for p in panels) == 5280.0

    from typehaus.takeoff import solar_takeoff
    takeoff = solar_takeoff(catlin_model)
    assert takeoff["panels"] == 12
    assert takeoff["total_watts"] == 5280
    assert takeoff["by_product"][0]["panels"] == 12


def test_panels_ride_the_roof_plane(catlin_model):
    """Every corner sits a clamp-standoff off the 4:12 plane, and the module's slope
    edge measures its true 44.6" while its plan projection is foreshortened."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    for panel in catlin_model.solar_panels:
        for (x, y, z) in panel.corners_bottom:
            standoff = z - roof_height_at(roof, (x, y))
            # roof_height_at is the deck plane; the module sits above the same
            # above-structure layer stack the roof shell draws, plus the 3" clamp
            # standoff (perpendicular, so the vertical figure is slightly larger).
            assert 0.20 < standoff < 0.32, (panel.tag, standoff)
        # Slope-edge length in 3D vs plan (corners 0->3 span the down-slope edge).
        a, b = panel.corners_bottom[0], panel.corners_bottom[3]
        edge_3d = math.dist(a, b)
        edge_plan = math.dist(a[:2], b[:2])
        expected = 44.6 * 0.0254
        # One of the two edges adjacent to corner 0 is the slope edge; accept either ring
        # orientation by checking against corner 1 too.
        c = panel.corners_bottom[1]
        alt_3d = math.dist(a, c)
        assert (abs(edge_3d - expected) < 0.002 or abs(alt_3d - expected) < 0.002)
        assert edge_plan <= edge_3d + 1e-9


def test_panels_stay_clear_of_ridge_and_eaves(catlin_model):
    for panel in catlin_model.solar_panels:
        for (x, y, _z) in panel.corners_bottom:
            assert 0.0 <= y <= 36 * 0.3048 + 1e-6
            # Authored 1' plan clearance, minus the small ridge-ward shift the
            # perpendicular lift introduces (the modules stay clear on their own side).
            assert abs(x - 18 * 0.3048) >= 0.55 * 0.3048


def test_ifc_solar_devices(catlin_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model.ids import derive_guid

    out = emit_ifc(catlin_model, tmp_path / "solar.ifc")
    f = ifcopenshell.open(str(out))
    devices = f.by_type("IfcSolarDevice")
    assert len(devices) == 12
    assert all(d.PredefinedType == "SOLARPANEL" for d in devices)
    by_name = {d.Name: d for d in devices}
    panel = next(p for p in catlin_model.solar_panels if p.tag == "SP-A-PV-W1")
    # Guids derive from the uid, so a Revit reload updates in place.
    project_uuid = catlin_model.plan.project.project_uuid
    assert by_name["SP-A-PV-W1"].GlobalId == derive_guid(project_uuid, panel.uid)
    # The watts ride along as a pset for downstream consumers.
    pset = next(rel.RelatingPropertyDefinition for rel in by_name["SP-A-PV-W1"].IsDefinedBy
                if rel.RelatingPropertyDefinition.Name == "TypeHaus_Solar")
    props = {prop.Name: prop.NominalValue.wrappedValue for prop in pset.HasProperties}
    assert props["watts"] == 440.0 and props["roof_ref"] == "RF-HOUSE"


def test_gltf_carries_the_array(catlin_model):
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    doc, _blob = emit_gltf_dict(catlin_model)
    solar_nodes = [node for node in doc["nodes"]
                   if node.get("extras", {}).get("trade") == "electrical"
                   and node["name"].split("|")[-1].startswith("SPV")]
    assert len(solar_nodes) == 12


def test_pv_mounting_kits_are_billed(catlin_model):
    from typehaus.takeoff import hardware_takeoff

    rows = hardware_takeoff(catlin_model)
    pv = [row for row in rows if row["part_number"] == "S-5-PVKIT"]
    assert len(pv) == 1
    assert pv[0]["count"] == 48  # 4 kits x 12 modules
    # The plain S-5! clamps (vent riser + boxes) keep their own line.
    plain = [row for row in rows if row["part_number"] == "S-5!"]
    assert plain and plain[0]["count"] >= 5


def test_model_json_serializes_solar(catlin_model):
    from typehaus.server.model_json import model_to_dict

    payload = model_to_dict(catlin_model)
    panels = payload["solar_panels"]
    assert len(panels) == 12
    assert all(len(p["corners_bottom"]) == 4 and len(p["corners_top"]) == 4 for p in panels)
    assert sum(p["watts"] for p in panels) == 5280.0
