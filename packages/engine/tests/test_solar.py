"""Rooftop PV array (WS5): fit, plane geometry, IFC/glTF emission, hardware, wattage."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.quantities import inch
from typehaus.resolve import resolve
from typehaus.resolve.roof_geometry import roof_height_at


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
    """Every corner sits a clamp-standoff off the 6:12 plane, and the module's slope
    edge measures its true 44.6" while its plan projection is foreshortened.

    **The bounds are DERIVED from the roof's own stack, not transcribed.** They were a
    literal 0.18..0.32 m band until 2026-08-31, and the day CATLIN_ROOF's six inches of
    outsulation were deleted the modules came down with the roof and the band failed —
    correctly reporting a change that was not a defect. What is actually invariant is the
    sandwich: ``roof_height_at`` is the DECK plane, the module rides the above-structure
    stack plus a clamp above it, and the figure compared here is the VERTICAL projection of
    a perpendicular offset, so it lands strictly between the stack's own vertical thickness
    (the module is above the metal, not in it) and the full perpendicular stack-plus-clamp.
    """
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    skin_m = sum(layer.thickness.meters for layer in above_structure_layers(assembly))
    cos_slope = 1.0 / math.hypot(1.0, 6.0 / 12.0)
    clamp_m = inch(3).meters  # SolarPanel.standoff's default: clamp + rail off the plane
    seen: set[float] = set()
    for panel in catlin_model.solar_panels:
        for (x, y, z) in panel.corners_bottom:
            standoff = z - roof_height_at(roof, (x, y))
            seen.add(round(standoff, 9))
            assert skin_m * cos_slope < standoff < skin_m + clamp_m, \
                (panel.tag, standoff, skin_m)
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
    # One plane, one clamp height: every corner of every module reads the same standoff.
    assert len(seen) == 1, sorted(seen)


def test_panels_stay_clear_of_ridge_and_eaves(catlin_model):
    for panel in catlin_model.solar_panels:
        for (x, y, _z) in panel.corners_bottom:
            assert 0.0 <= y <= 36 * 0.3048 + 1e-6
            # Authored 1' plan clearance, minus the small ridge-ward shift the
            # perpendicular lift introduces (the modules stay clear on their own side).
            assert abs(x - 18 * 0.3048) >= 0.55 * 0.3048


def test_x_ridge_roof_branch(catlin_model):
    """The resolver's ridge_direction="x" arm, exercised on the garage roof (the house
    array only covers the "y" arm): width runs along x, the slope runs in y, and the
    corners ride the garage plane with the same standoff contract."""
    from typehaus.model import SolarPanel, ft, inch, pt

    plan = catlin_model.plan.with_elements("garage", (
        *catlin_model.plan.storey_elements("garage"),
        SolarPanel(uid="TESTSPX001", tag="SP-G-TEST", roof_ref="RF-GARAGE",
                   origin=pt(ft(4), ft(52)), width=inch(69.4), length=inch(44.6),
                   thickness=inch(1.2), watts=440.0),
    ))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    panel = next(p for p in model.solar_panels if p.tag == "SP-G-TEST")
    roof = next(r for r in model.roofs if r.tag == "RF-GARAGE")
    xs = [c[0] for c in panel.corners_bottom]
    ys = [c[1] for c in panel.corners_bottom]
    # Landscape edge along the x ridge; the slope edge foreshortens in plan y.
    assert abs((max(xs) - min(xs)) - 69.4 * 0.0254) < 1e-6
    assert (max(ys) - min(ys)) < 44.6 * 0.0254
    for (x, y, z) in panel.corners_bottom:
        standoff = z - roof_height_at(roof, (x, y))
        assert 0.05 < standoff < 0.36, standoff


def test_missing_roof_ref_is_an_error(catlin_model):
    from typehaus.model import SolarPanel, ft, inch, pt

    plan = catlin_model.plan.with_elements("garage", (
        *catlin_model.plan.storey_elements("garage"),
        SolarPanel(uid="TESTSPX002", tag="SP-G-BAD", roof_ref="RF-NOPE",
                   origin=pt(ft(4), ft(52)), width=inch(69.4), length=inch(44.6),
                   thickness=inch(1.2)),
    ))
    _model, findings = resolve(plan)
    errors = [f for f in findings if f.check_id == "integrity.solar_roof_ref"]
    assert errors and errors[0].severity.value == "error"


def test_ifc_solar_devices(catlin_model_ro, catlin_ifc_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.model.ids import derive_guid

    f = ifcopenshell.open(str(catlin_ifc_path))
    devices = f.by_type("IfcSolarDevice")
    assert len(devices) == 12
    assert all(d.PredefinedType == "SOLARPANEL" for d in devices)
    by_name = {d.Name: d for d in devices}
    panel = next(p for p in catlin_model_ro.solar_panels if p.tag == "SP-A-PV-W1")
    # Guids derive from the uid, so a Revit reload updates in place.
    project_uuid = catlin_model_ro.plan.project.project_uuid
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
    # The plain S-5! clamps (vent riser + boxes) split across scopes: directly modeled
    # connectors get their own row, and the clamps carried under a part that declares
    # ``requires_role`` (which reaches the roof but is not itself a separately modeled
    # Connector) get another — see authored_connector_rows in takeoff/anchors.py. Gather
    # every S-5! row regardless of scope and use `>=` throughout, so this pins the SPLIT
    # and never an exact count or a single row's index.
    #
    # Both halves fell on 2026-08-26 and the rule did not. The carried count was >= 11, all
    # of it CanDuit rings on the house walls; the exposed-fastener cladding swap took those
    # onto through-panel straps, which reach the wall themselves and carry nothing. ColorGard
    # is the remaining ``requires_role`` part, and it pins the rule the same way.
    #
    # The MODELED half went to zero in the same pass, and that is the point rather than an
    # erosion of the test. An S-5! closes on a seam; the house has no seam left to close on,
    # so the two wall-mounted enclosure clamps (CN-A-NEMA-CLAMP, CN-A-PV-CLAMP) and the vent
    # riser's were removed as uninstallable. Every S-5! the model still bills is implied by
    # the ColorGard rail on the ROOF, which kept its standing seam — so this now pins the
    # split as "carried only", which is a stronger statement than ">= 2 modeled" was.
    s5_rows = [row for row in rows if row["part_number"] == "S-5!"]
    assert s5_rows
    modeled = sum(row["count"] for row in s5_rows if row["scope"] == "modeled connector")
    carried = sum(row["count"] for row in s5_rows if row["scope"] == "carried-mount")
    assert modeled == 0, "an S-5! needs a seam; the walls are exposed-fastener panel now"
    assert carried >= 6
    assert sum(row["count"] for row in s5_rows) == carried


def test_model_json_serializes_solar(catlin_model):
    from typehaus.server.model_json import model_to_dict

    payload = model_to_dict(catlin_model)
    panels = payload["solar_panels"]
    assert len(panels) == 12
    assert all(len(p["corners_bottom"]) == 4 and len(p["corners_top"]) == 4 for p in panels)
    assert sum(p["watts"] for p in panels) == 5280.0
