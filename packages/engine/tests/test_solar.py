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
    literal 0.18..0.32 m band until 2026-08-31, and the day ROOF's six inches of
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
    """The resolver's ridge_direction="x" arm: width runs along x, the slope runs in y, and
    the corners ride the plane with the same standoff contract.

    ** THE PREMISE CHANGED ON 2026-09-07 AND THE COVERAGE DID NOT. ** This used to lean on
    the garage roof being the one "x" ridge in catlin. The garage's overhead door turned
    north, its ridge turned with it, and BOTH of this house's gables now run "y" — so the
    "x" arm has no witness in the reference house at all. Rather than hunt for another roof
    or let the branch go dark, the test now states its own premise: it takes RF-GARAGE and
    turns its ridge back to "x" in a throwaway plan. That is honest about what is being
    exercised (the resolver, not the house) and it cannot rot when the house moves again.
    """
    from typehaus.model import Roof, SolarPanel, ft, inch, pt

    # `model_copy`, not `dataclasses.replace`: every model element is a pydantic model here,
    # not a dataclass, and `replace()` raises TypeError on one.
    garage = catlin_model.plan.storey_elements("garage")
    turned = tuple(
        e.model_copy(update={"ridge_direction": "x"})
        if isinstance(e, Roof) and e.tag == "RF-GARAGE" else e
        for e in garage
    )
    assert any(isinstance(e, Roof) and e.ridge_direction == "x" for e in turned), \
        "the fixture this branch needs is built here, not borrowed from the house"
    plan = catlin_model.plan.with_elements("garage", (
        *turned,
        SolarPanel(uid="TESTSPX001", tag="SP-G-TEST", roof_ref="RF-GARAGE",
                   origin=pt(ft(10), ft(52)), width=inch(69.4), length=inch(44.6),
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
    # ** NO PLAIN S-5! IS AUTHORED IN THIS HOUSE, AND THE ONLY ONES BILLED ARE CARRIED. **
    # The MODELED half went to zero on 2026-09-07: an S-5! closes on a seam, and the
    # exposed-fastener cladding swap moved the wall clamps onto through-panel straps.
    #
    # The CARRIED half came back on 2026-09-10 with the extruded garage. It is NOT the old
    # rail returning: those guards stood on RF-GARAGE's south slope over the polycarbonate
    # canopy, and that slope is a rake now. These four are on the EAST AND WEST EAVES over
    # the screen, the tier approach and the equipment circulation, which
    # `notes/north_entry_structure.md` §5 requires snow retention along — a walking surface,
    # not a roof, so `sliding_snow` never sees it and the note is the only authority.
    #
    # `S-5-PVKIT` above is a different part and is unaffected: it clamps the PV array to
    # RF-HOUSE's standing seam, which is untouched.
    s5_rows = [row for row in rows if row["part_number"] == "S-5!"]
    modeled = sum(row["count"] for row in s5_rows if row["scope"] == "modeled connector")
    carried = sum(row["count"] for row in s5_rows if row["scope"] == "carried-mount")
    assert modeled == 0, "an S-5! needs a seam; the walls are exposed-fastener panel now"
    assert carried == 4, "four CN-BW-SNOW rails, each carried on its own clamp"


def test_model_json_serializes_solar(catlin_model):
    from typehaus.server.model_json import model_to_dict

    payload = model_to_dict(catlin_model)
    panels = payload["solar_panels"]
    assert len(panels) == 12
    assert all(len(p["corners_bottom"]) == 4 and len(p["corners_top"]) == 4 for p in panels)
    assert sum(p["watts"] for p in panels) == 5280.0
