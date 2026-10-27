"""The hoods shed sideways, ventilate the wood and preserve the independent house slot."""

from dataclasses import replace

import pytest

from typehaus import FormedFlashingSection, inch
from typehaus.resolve.beam_hoods import resolve_beam_hood
from typehaus.resolve.roof_geometry import roof_height_at
from typehaus.takeoff.edge_trim import edge_trim_takeoff
from typehaus.takeoff.framing import structural_solids_takeoff


def test_matching_tails_keep_the_roof_and_trusses_at_their_original_stations(catlin_model_ro):
    model = catlin_model_ro
    beams = [model.plan.by_tag(f"BM-BW-R{side}") for side in ("W", "E")]
    solids = [next(s for s in model.solids if s.tag == b.tag) for b in beams]
    assert [min(y for _, y in s.outline) for s in solids] == pytest.approx([441.125 * 0.0254] * 2)
    assert [max(y for _, y in s.outline) for s in solids] == pytest.approx([518.625 * 0.0254] * 2)
    assert [b.roof_bearing_insets[0].inches for b in beams] == pytest.approx([6.125] * 2)
    roof = next(r for r in model.roofs if r.tag == "RF-BW-CANOPY")
    assert sorted(
        {round(t.p0[1] / 0.0254, 3) for t in roof.members if t.category == "roof_truss"}
    ) == [447.25, 471.25, 495.25]
    assert min(y for _, y in roof.footprint) / 0.0254 == pytest.approx(446.625)
    cap = model.plan.by_tag("CN-BW-CAP-E")
    assert (cap.uid, cap.size) == ("X0QPPRBG1X", "AC6Z")


@pytest.mark.parametrize("side", ["W", "E"])
def test_hood_ventilation_shedding_and_house_separation(catlin_model_ro, side):
    model = catlin_model_ro
    hood = next(s for s in model.solids if s.tag == f"TR-BW-HOOD-{side}")
    beam = next(s for s in model.solids if s.tag == f"BM-BW-R{side}")
    spec = model.plan.by_tag(hood.tag)
    half = spec.thickness.meters / 2
    centre = spec.path[0].x.meters
    crown = spec.top_elevation.meters
    edge = crown - half * spec.section.slope
    assert edge - beam.z1_m == pytest.approx(inch(0.5).meters)
    assert half - (max(x for x, _ in beam.outline) - centre) == pytest.approx(inch(0.5).meters)
    assert min(y for _, y in beam.outline) - spec.path[0].y.meters == pytest.approx(
        inch(0.5).meters
    )
    # Finished north house cladding is 36'-7 1/4". All folds, including the end hem,
    # must preserve this slot; the fabrication movement allowance is a separate release.
    assert min(y for _, y, _ in hood.body_mesh.positions) - inch(439.25).meters == pytest.approx(
        inch(1.25).meters
    )
    roof = next(r for r in model.roofs if r.tag == "RF-BW-CANOPY")
    truss_face = (
        min(t.p0[1] for t in roof.members if t.category == "roof_truss") - inch(0.75).meters
    )
    assert truss_face - max(y for _, y, _ in hood.body_mesh.positions) >= inch(1).meters - 1e-8
    top_points = [
        p
        for p in hood.body_mesh.positions
        if abs(p[2] - (crown - abs(p[0] - centre) * spec.section.slope)) < 1e-9
    ]
    assert any(abs(x - centre) < 1e-9 for x, _, _ in top_points)
    assert any(abs(abs(x - centre) - half) < 1e-9 for x, _, _ in top_points)
    # Each panel can leave the wood below it to drain; no sheet closes the underside.
    assert all(
        not all(
            p[2] < beam.z1_m
            and min(x for x, _ in beam.outline) < p[0] < max(x for x, _ in beam.outline)
            and min(y for _, y in beam.outline) < p[1] < max(y for _, y in beam.outline)
            for p in (hood.body_mesh.positions[i] for i in triangle)
        )
        for triangle in hood.body_mesh.triangles
    )
    apron = next(s for s in model.solids if s.tag == hood.tag + "-APRON")
    assert apron.host_ref == roof.tag
    assert apron.z0_m - edge == pytest.approx(inch(0.125).meters)
    assert min(y for _, y in apron.outline) < spec.path[-1].y.meters
    assert max(y for _, y in apron.outline) > min(y for _, y in roof.footprint)
    # Only the roof lap enters the truss's plan projection, above its deck plane.
    assert all(
        y < truss_face or z > roof_height_at(roof, (x, y)) for x, y, z in apron.body_mesh.positions
    )


def test_hoods_bill_once_with_their_roof_aprons(catlin_model_ro):
    model = catlin_model_ro
    sheets = [s for s in model.solids if s.tag.startswith("TR-BW-HOOD-")]
    assert len(sheets) == 4
    assert all(s.derived and s.category == "beam_cap" and s.body_mesh for s in sheets)
    rows = [r for r in edge_trim_takeoff(model) if r["category"] == "beam_tail_hood"]
    assert len(rows) == 1
    assert rows[0]["count"] == 2
    assert rows[0]["length_ft"] == pytest.approx(0.8)
    assert not rows[0]["also_in_structural_solids"]
    without = replace(model, solids=[s for s in model.solids if s not in sheets])
    assert structural_solids_takeoff(model) == structural_solids_takeoff(without)


def test_hood_configuration_and_bad_hosts_fail_explicitly(catlin_model_ro):
    with pytest.raises(ValueError, match="roof_ref"):
        FormedFlashingSection(profile="ventilated_hood", slope=0.02)
    with pytest.raises(ValueError, match="air space"):
        FormedFlashingSection(
            profile="ventilated_hood", slope=0.02, roof_ref="roof", air_gap=inch(0.25)
        )
    hood = catlin_model_ro.plan.by_tag("TR-BW-HOOD-W")
    bad = hood.model_copy(update={"host_ref": "missing"})
    with pytest.raises(ValueError, match="host is missing"):
        resolve_beam_hood(replace(catlin_model_ro, solids=[]), bad, "entry")


def test_hood_sheets_reach_json_glb_and_ifc(catlin_model_ro, tmp_path):
    import ifcopenshell

    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.ifc import emit_ifc
    from typehaus.resolve.geometry_build import build_geometry
    from typehaus.resolve.model import ResolvedModel
    from typehaus.server.model_json_fabric import shell_json

    sheets = [s for s in catlin_model_ro.solids if s.tag.startswith("TR-BW-HOOD-")]
    plan = catlin_model_ro.plan.model_copy(update={
        "elements": {storey.tag: () for storey in catlin_model_ro.plan.storeys}})
    model = ResolvedModel(plan, solids=sheets)
    model.geometry = build_geometry(model)
    payload = shell_json(model, None)
    for solid in sheets:
        record = next(s for s in payload["solids"] if s["uid"] == solid.uid)
        assert record["body_mesh"]["positions"] == [list(p) for p in solid.body_mesh.positions]
    gltf, _ = emit_gltf_dict(model)
    assert {node.get("extras", {}).get("uid") for node in gltf["nodes"]} >= {
        solid.uid for solid in sheets
    }
    file = ifcopenshell.open(str(emit_ifc(model, tmp_path / "hoods.ifc")))
    covers = file.by_type("IfcCovering")
    assert len(covers) == 4
    assert all(c.Representation.Representations[0].RepresentationType == "Tessellation"
               for c in covers)
