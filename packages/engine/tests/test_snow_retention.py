"""Roof-mounted rail geometry, installation boundaries and procurement agreement."""

import math
from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus import (
    Assembly,
    Connector,
    ConnectorKind,
    Layer,
    LayerFunction,
    Library,
    Material,
    SnowRetentionSpec,
    inch,
    pt,
)
from typehaus.cli.prices import estimate_costs, load_prices
from typehaus.hardware.snow_retention import INCH_M, STOCK_LENGTH_IN
from typehaus.resolve.geometry_ir import signed_volume
from typehaus.resolve.model import ResolvedRoof
from typehaus.resolve.snow_retention import resolve_snow_retention
from typehaus.resolve.snow_retention_layout import rail_segments, snow_retention_layout
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.snow_retention import snow_retention_rows


def roof_run(*, direction="y", form="gable", length=64, profile="standing-seam", base=1):
    """A small actual roof assembly; no mocks of panel or placement calculations."""
    material = Material(tag="metal", name="roof", finish=profile, color="#202124")
    assembly = Assembly(tag="roof", layers=(
        Layer(name="deck", material_ref="ply", thickness=inch(base),
              function=LayerFunction.SHEATHING),
        Layer(name="roofing", material_ref="metal", thickness=inch(1),
              function=LayerFunction.CLADDING),
    ))
    library = Library(materials=(material,), assemblies=(assembly,))
    footprint = tuple((x * INCH_M, y * INCH_M)
                      for x, y in ((0, 0), (96, 0), (96, 128), (0, 128)))
    if direction == "x":
        footprint = tuple((y, x) for x, y in footprint)
    roof = ResolvedRoof("roof", "RF", "main", form, footprint, 3, 4, direction,
                        "roof", 0)
    position = (64, 64)
    connector = Connector(
        uid="SNOW000001", tag="SNOW", kind=ConnectorKind.SNOW_GUARD,
        position=pt(inch(position[0]), inch(position[1])), axis=direction,
        connects=("RF",), size="S-5! ColorGard",
        snow_retention=SnowRetentionSpec(length=inch(length)))
    plan = SimpleNamespace(library=library, by_tag=lambda _: None,
                           storeys=(SimpleNamespace(tag="main"),),
                           storey_elements=lambda _: (connector,))
    return SimpleNamespace(roofs=[roof], plan=plan, solids=[]), connector


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("form", ["gable", "shed"])
def test_layout_tracks_pitch_layers_and_panel_seams(direction, form):
    model, connector = roof_run(direction=direction, form=form)
    layout, findings = snow_retention_layout(model, connector)
    assert layout is not None
    assert not findings
    along_index = 0 if direction == "x" else 1
    absolute = tuple(connector.position.xy_m[along_index] + s for s in layout.supports)
    from typehaus.resolve.roof_panel_skin import seam_stations
    assert set(absolute).issubset(set(seam_stations(model.roofs[0], model)))
    assert math.dist((0, 0, 0), layout.normal) == pytest.approx(1)
    dot_product = sum(a * b for a, b in zip(layout.normal, layout.downhill, strict=True))
    assert dot_product == pytest.approx(0)
    assert layout.downhill[2] < 0
    thicker, _ = roof_run(direction=direction, form=form, base=3)
    higher, _ = snow_retention_layout(thicker, connector)
    assert higher.origin[2] - layout.origin[2] == pytest.approx(2 * INCH_M / layout.normal[2])


@pytest.mark.parametrize("length,expected", [(92, 1), (92.001, 2), (184, 2), (185, 3)])
def test_stock_length_boundaries_and_balanced_cuts(length, expected):
    segments = rail_segments(0, length * INCH_M)
    assert len(segments) == expected
    assert segments[0][0] == 0
    assert segments[-1][1] == pytest.approx(length * INCH_M)
    assert all(b - a <= STOCK_LENGTH_IN * INCH_M + 1e-8 for a, b in segments)


@pytest.mark.parametrize("change,reason", [
    ({"connects": ("MISSING",)}, "exactly one resolved"),
    ({"axis": "x"}, "parallel"),
    ({"elevation": inch(120)}, "roof-derived"),
    ({"kind": ConnectorKind.STANDING_SEAM_CLAMP}, "SNOW_GUARD"),
    ({"snow_retention": SnowRetentionSpec(length=inch(4))}, "two seam-clamp"),
    ({"snow_retention": SnowRetentionSpec(length=inch(200))}, "inside"),
])
def test_invalid_runs_produce_findings_without_marker_fallback(change, reason):
    model, connector = roof_run()
    invalid = connector.model_copy(update=change)
    findings = resolve_snow_retention(model, invalid, "main")
    assert reason in findings[0].message
    assert not model.solids


def test_unsupported_roof_profile_is_actionable():
    model, connector = roof_run(profile="ribbed-panel")
    layout, findings = snow_retention_layout(model, connector)
    assert layout is None
    assert "standing-seam" in findings[0].message


def test_end_cantilever_is_checked_and_each_cut_needs_two_clamps(monkeypatch):
    model, connector = roof_run(length=90)
    _, findings = snow_retention_layout(model, connector)
    assert any("8-inch" in f.message for f in findings)
    model, connector = roof_run(length=100)
    model.roofs[0] = replace(model.roofs[0], footprint=tuple(
        (x, y * 2) for x, y in model.roofs[0].footprint))
    import typehaus.resolve.roof_panel_skin as panels

    monkeypatch.setattr(panels, "seam_stations", lambda roof, model:
                        tuple(value * INCH_M for value in (48, 80, 112)))
    _, findings = snow_retention_layout(model, connector)
    assert any("two clamps" in f.message for f in findings)


@pytest.mark.parametrize("length,over_limit", [(80, False), (80.001, True)])
def test_exact_eight_inch_cantilever_boundary(length, over_limit):
    model, connector = roof_run(length=length)
    _, findings = snow_retention_layout(model, connector)
    assert any("8-inch" in f.message for f in findings) is over_limit


def test_components_are_closed_dimensioned_and_follow_roof_local_axes():
    model, connector = roof_run()
    assert not resolve_snow_retention(model, connector, "main")
    layout, _ = snow_retention_layout(model, connector)
    for solid in model.solids:
        assert solid.host_ref == connector.tag
        assert solid.derived and solid.body_mesh
        assert signed_volume(solid.body_mesh.positions, solid.body_mesh.triangles) > 0
        assert solid.z0_m == min(p[2] for p in solid.body_mesh.positions)
    rail = next(s for s in model.solids if s.tag.endswith("RAIL-1"))
    assert max(p[1] for p in rail.body_mesh.positions) - min(
        p[1] for p in rail.body_mesh.positions) == pytest.approx(64 * INCH_M)
    # Every foot spans a flat pan between the 4/8/12-inch striations.
    for station, support in zip(layout.snow_clips, layout.supports[:-1], strict=True):
        assert (station - support) / INCH_M == pytest.approx(6)
    assert len([s for s in model.solids if "CLAMP-" in s.tag]) == len(layout.supports)
    rows = snow_retention_rows(model)
    assert next(r for r in rows if r["part_number"] == "S-5-N")["count"] == len(layout.supports)
    assert not [r for r in rows if "included" in r["part_number"]]


def test_longer_run_draws_included_splice_without_buying_it_twice():
    model, connector = roof_run(length=100)
    assert not resolve_snow_retention(model, connector, "main")
    layout, _ = snow_retention_layout(model, connector)
    assert len(layout.segments) == 2
    splices = [s for s in model.solids if "SPLICE-" in s.tag]
    assert len(splices) == 1
    from typehaus.solids3d.convert import to_manifold

    for solid in model.solids:
        manifold = to_manifold(solid.body_mesh)
        assert manifold.volume() > 0
        assert str(manifold.status()) == "Error.NoError"
    rows = snow_retention_rows(model)
    stock = next(r for r in rows if r["part_number"] == "ColorGard 2.0 Unpunched")
    assert stock["count"] == 2 and "1 splices used" in stock["basis"]
    assert not [r for r in rows if "Splice" in r["part_number"]]


def test_catlin_run_and_quantities_agree(catlin_model_ro):
    model = catlin_model_ro
    connector = model.plan.by_tag("CN-BW-SNOW-E-1")
    layout, findings = snow_retention_layout(model, connector)
    assert not findings
    assert layout.roof_ref == "RF-BW-CANOPY"
    assert len(layout.supports) == 4 and len(layout.snow_clips) == 3
    assert len(layout.segments) == 1
    roof = next(r for r in model.roofs if r.tag == layout.roof_ref)
    centre_y = connector.position.xy_m[1]
    assert centre_y + layout.start - min(y for _, y in roof.footprint) == pytest.approx(
        7.625 * INCH_M)
    assert max(y for _, y in roof.footprint) - centre_y - layout.end == pytest.approx(2 * INCH_M)
    guards = [e for e in model.plan.all_elements()
              if isinstance(e, Connector) and e.kind is ConnectorKind.SNOW_GUARD]
    assert guards == [connector]
    rows = hardware_takeoff(model)
    run_rows = [r for r in rows if r["scope"] == "snow-retention run"]
    assert {r["part_number"]: r["count"] for r in run_rows} == {
        "ColorGard 2.0 Unpunched": 1, "S-5-N": 4, "VersaClip 2.0": 4,
        "SnoClip 2.0 II": 3, "ColorGard ColorStrip": 1}
    assert not [r for r in rows if r["part_number"] == "S-5! ColorGard"]
    assert not [r for r in rows if r["scope"] == "carried-mount" and "ColorGard" in r["basis"]]
    assert len([s for s in model.solids if s.host_ref == connector.tag]) == 20
    materials = {material.tag for material in model.plan.library.materials}
    assert all(solid.material in materials for solid in model.solids
               if solid.host_ref == connector.tag)


def test_snow_clamps_are_priced_separately_from_pv_allowance():
    from pathlib import Path

    prices = load_prices(Path("houses/catlin"))
    bom = {"hardware": [
        {"part_number": "S-5-N", "scope": "snow-retention run", "count": 4},
        {"part_number": "S-5-N", "scope": "carried-mount", "count": 72},
    ]}
    estimate = estimate_costs(bom, replace(prices, allowances={}))
    assert estimate["total"]["low"] == pytest.approx(28.2)
    assert estimate["total"]["high"] == 60


def test_catlin_components_export_in_glb(catlin_model_ro):
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    model = catlin_model_ro
    parts = [s for s in model.solids if s.host_ref == "CN-BW-SNOW-E-1"]
    gltf, blob = emit_gltf_dict(model)
    nodes = {n["extras"].get("uid"): n for n in gltf["nodes"] if "extras" in n}
    assert blob
    for part in parts:
        node = nodes[part.uid]
        assert node["extras"]["host_ref"] == part.host_ref
        assert node["extras"]["trade"] == "roofing"
        assert gltf["meshes"][node["mesh"]]["primitives"]
    foot = next(p for p in parts if p.material == "epdm")
    primitive = gltf["meshes"][nodes[foot.uid]["mesh"]]["primitives"][0]
    material = gltf["materials"][primitive["material"]]["pbrMetallicRoughness"]
    assert material["metallicFactor"] == 0
    assert material["baseColorFactor"][0] < 0.2


def test_catlin_components_export_in_ifc(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell

    document = ifcopenshell.open(str(catlin_ifc_path))
    parts = [s for s in catlin_model_ro.solids if s.host_ref == "CN-BW-SNOW-E-1"]
    for part in parts:
        matches = [e for e in document.by_type("IfcDiscreteAccessory") if e.Name == part.tag]
        assert len(matches) == 1, part.tag
        assert matches[0].Representation


def test_catlin_components_clear_roof_and_gutters(catlin_model_ro):
    from typehaus.resolve.geometry_ir import GPrism
    from typehaus.solids3d.convert import to_manifold, union

    model = catlin_model_ro
    parts = [s for s in model.solids if s.host_ref == "CN-BW-SNOW-E-1"]
    roof = next(r for r in model.roofs if r.tag == "RF-BW-CANOPY")
    roof_body = union(to_manifold(mesh) for _, mesh in roof.layer_surface_meshes)
    gutters = [s for s in model.solids if s.category == "gutter"]
    gutter_body = union(to_manifold(s.body_mesh if s.body_mesh is not None else
                                   GPrism(s.outline, s.z0_m, s.z1_m)) for s in gutters)
    for part in parts:
        body = to_manifold(part.body_mesh)
        assert (body ^ roof_body).volume() < 1e-9, part.tag
        assert (body ^ gutter_body).volume() < 1e-9, part.tag


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("form", ["gable", "shed"])
@pytest.mark.parametrize("size,length", [("S-5-N", 2.0), ("S-5-N Mini", 1.18)])
def test_roof_clamp_uses_normal_dimensions(direction, form, size, length):
    from typehaus.resolve.seam_clamp import roof_seam_clamp_mesh
    from typehaus.solids3d.convert import to_manifold

    model, run = roof_run(direction=direction, form=form)
    layout, _ = snow_retention_layout(model, run)
    along_index = 0 if direction == "x" else 1
    position = list(run.position.xy_m)
    position[along_index] += layout.supports[0]
    clamp = run.model_copy(update={
        "kind": ConnectorKind.STANDING_SEAM_CLAMP, "snow_retention": None, "size": size,
        "position": pt(inch(position[0] / INCH_M), inch(position[1] / INCH_M)),
    })
    mesh = roof_seam_clamp_mesh(model, clamp)
    projected = [sum(p[i] * layout.downhill[i] for i in range(3)) for p in mesh.positions]
    assert max(projected) - min(projected) == pytest.approx(length * INCH_M)
    assert to_manifold(mesh).volume() > 0


def test_catlin_wind_clamps_follow_seams_clear_roof_and_omit_snow_corner(catlin_model_ro):
    from typehaus.resolve.roof_panel_skin import profiled_roof_layers, seam_stations
    from typehaus.solids3d.convert import to_manifold, union

    model = catlin_model_ro
    clamps = [s for s in model.solids if s.tag.startswith(("CN-G-WIND-", "CN-A-WIND-"))]
    assert len(clamps) == 21
    assert not any(s.tag.startswith("CN-G-WIND-RFSE-") for s in clamps)
    for solid in clamps:
        connector = model.plan.by_tag(solid.tag)
        roof = next(r for r in model.roofs if r.tag in connector.connects)
        assert connector.elevation is None
        assert connector.position.y.meters == pytest.approx(min(
            seam_stations(roof, model), key=lambda y: abs(y - connector.position.y.meters)))
        body = to_manifold(solid.body_mesh)
        roof_body = union(to_manifold(mesh) for _, mesh in roof.layer_surface_meshes)
        assert (body ^ roof_body).volume() < 1e-9, solid.tag
        if solid.tag.startswith("CN-G-"):
            _, _, rect, _ = next(profiled_roof_layers(roof, model))
            x = connector.position.x.meters
            assert min(x - rect[0], rect[1] - x) / INCH_M == pytest.approx(3.79959, abs=1e-4)


@pytest.mark.parametrize("change,reason", [
    ({"position": pt(inch(64), inch(65))}, "align"),
    ({"position": pt(inch(120), inch(64))}, "inside"),
    ({"position": pt(inch(48), inch(64))}, "ridge"),
    ({"connects": ("missing",)}, "exactly one"),
])
def test_invalid_roof_clamp_reports_finding_without_marker(change, reason):
    from typehaus.resolve.seam_clamp import resolve_roof_seam_clamp

    model, run = roof_run()
    clamp = run.model_copy(update={
        "kind": ConnectorKind.STANDING_SEAM_CLAMP, "snow_retention": None,
        "size": "S-5-N Mini", **change,
    })
    findings = resolve_roof_seam_clamp(model, clamp, "main")
    assert reason in findings[0].message
    assert not model.solids
