"""Folded roof sheets retain their real envelope and closed section cuts."""

from collections import Counter
from types import SimpleNamespace

import pytest

from typehaus.model.enums import ConnectorKind
from typehaus.resolve.geometry_ir import GPart
from typehaus.resolve.geometry_roofs import roof_parts
from typehaus.resolve.geometry_slice import CutPlane, slice_part
from typehaus.resolve.metal_skin_profiles import IMAGE_II_16_PROFILE as PROFILE
from typehaus.resolve.model import ResolvedRoof
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_factor
from typehaus.resolve.roof_panel_skin import (
    resolve_profiled_roof_surfaces,
    roof_profile_mesh,
    seam_stations,
)


def gable(direction="y", form="gable"):
    return ResolvedRoof(
        "roof",
        "RF",
        "main",
        form,
        ((0, 0), (4, 0), (4, 6), (0, 6)),
        3.0,
        4.0,
        direction,
        "roof",
        24.0,
    )


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("form", ["gable", "shed"])
def test_roof_skin_envelope_and_closed_cuts(direction, form):
    roof = gable(direction, form)
    rect, base = (0.1, 3.9, 0.2, 5.8), 0.017
    mesh = roof_profile_mesh(roof, rect, base, PROFILE)
    assert mesh.triangles
    factor = roof_slope_factor(roof)
    for x, y, z in mesh.positions:
        along = x if direction == "x" else y
        assert (rect[0] if direction == "x" else rect[2]) - 1e-8 <= along
        assert along <= (rect[1] if direction == "x" else rect[3]) + 1e-8
        depth = (z - roof_plane_z(roof, y if direction == "x" else x)) / factor
        assert base - 1e-8 <= depth <= base + PROFILE.depth_m + 1e-8
    # Every geometric edge has two incident faces, including sheet end caps.
    edges = Counter()
    for triangle in mesh.triangles:
        points = [tuple(round(v, 8) for v in mesh.positions[i]) for i in triangle]
        for a, b in zip(points, points[1:] + points[:1], strict=True):
            edges[tuple(sorted((a, b)))] += 1
    across = 1 if direction == "x" else 0
    ridge = 3.0 if direction == "x" else 2.0
    assert all(
        count == 2
        or (
            form == "gable"
            and count == 4
            and all(abs(point[across] - ridge) < 1e-8 for point in edge)
        )
        for edge, count in edges.items()
    )
    part = GPart(key="layer:roofing", solids=(mesh,), material_key="metal")
    outlines = slice_part(part, CutPlane(axis=direction, station_m=1.13))
    assert outlines


def test_unprofiled_roof_has_no_mesh():
    roof = gable()
    model = SimpleNamespace(
        roofs=[roof],
        plan=SimpleNamespace(
            library=SimpleNamespace(materials=[], resolve_assembly=lambda _: None)
        ),
    )
    resolve_profiled_roof_surfaces(model)
    assert model.roofs[0].layer_surface_meshes == ()
    assert seam_stations(roof, model) == ()


def test_catlin_skin_and_clamps_follow_shared_seams(catlin_model_ro):
    model = catlin_model_ro
    roof = next(roof for roof in model.roofs if roof.tag == "RF-HOUSE")
    assert dict(roof.layer_surface_meshes)["roofing"].triangles
    assert not next(roof for roof in model.roofs if roof.tag == "RF-GARAGE").layer_surface_meshes
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    part = next(part for part in roof_parts(roof, assembly) if part.key == "layer:roofing")
    assert part.solids == (dict(roof.layer_surface_meshes)["roofing"],)
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    top = sum(layer.thickness.meters for layer in above_structure_layers(assembly))
    stations = seam_stations(roof, model)
    clamps = [
        element
        for storey in model.plan.storeys
        for element in model.plan.storey_elements(storey.tag)
        if getattr(element, "kind", None) is ConnectorKind.STANDING_SEAM_CLAMP
        and roof.tag in getattr(element, "connects", ())
    ]
    assert len(clamps) == 60
    for clamp in clamps:
        x, y = clamp.position.xy_m
        assert min(abs(y - station) for station in stations) < 0.25 * 0.0254
        expected = roof_plane_z(roof, x) + top * roof_slope_factor(roof)
        assert clamp.elevation.meters == pytest.approx(expected, abs=1e-6)


def test_catlin_param_stations_match_the_resolver(catlin_model_ro):
    import runpy
    import sys
    from unittest.mock import patch

    from _helpers import CATLIN

    model = catlin_model_ro
    roof = next(roof for roof in model.roofs if roof.tag == "RF-HOUSE")
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    board_batten = model.plan.library.resolve_assembly("EXT_2X6_BOARD_BATTEN")
    # Other house loads may purge params from sys.modules after the session fixture
    # resolves. Evaluate the actual helper against its assembly dependencies in isolation.
    dependencies = {
        "params.cladding": SimpleNamespace(
            HOUSE_EW_OUTBOARD_IN=-min(x for x,_ in roof.footprint)/.0254,
            HOUSE_NS_OUTBOARD_IN=-min(y for _,y in roof.footprint)/.0254),
        "plan.assemblies.envelope_roofs": SimpleNamespace(ROOF=assembly),
        "plan.assemblies.board_batten": SimpleNamespace(EXT_2X6_BOARD_BATTEN=board_batten),
    }
    with patch.dict(sys.modules, dependencies):
        params = runpy.run_path(str(CATLIN / "params" / "roof_panel.py"))
    assert seam_stations(roof, model) == pytest.approx(
        tuple(value * .0254 for value in params["SEAM_STATIONS_IN"]))


def test_catlin_rake_and_profile_closures_are_formed_sheets(catlin_model_ro):
    from typehaus.resolve.geometry_ir import GSweep
    from typehaus.resolve.geometry_members import member_solid
    from typehaus.takeoff.edge_trim import edge_trim_takeoff

    roof = next(roof for roof in catlin_model_ro.roofs if roof.tag == "RF-HOUSE")
    closures = [member for member in roof.members if member.category == "ridge_closure"]
    assert closures
    assert all(isinstance(member_solid(member), GSweep)
               for member in closures if not member.child_key.endswith("-top"))
    assert any(member.connection == "roof:panel-rake" for member in roof.members)
    assert any(row['category'] == 'ridge_closure' and row['length_ft'] > 60
               for row in edge_trim_takeoff(catlin_model_ro))


def test_catlin_roof_payload_keeps_the_resolved_skin(catlin_model_ro):
    from typehaus.server.model_json import model_to_dict

    payload = model_to_dict(catlin_model_ro)
    roof = next(roof for roof in payload['roofs'] if roof['tag'] == 'RF-HOUSE')
    assert roof['layer_surface_meshes'][0]['layer'] == 'roofing'
    assert roof['layer_surface_meshes'][0]['surface_mesh']['triangles']


def test_eave_closures_are_scribed_below_the_roof_pan(catlin_model_ro):
    from typehaus.resolve.geometry_ir import GSweep
    from typehaus.resolve.geometry_members import member_solid
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    roof = next(roof for roof in catlin_model_ro.roofs if roof.tag == 'RF-HOUSE')
    assembly = catlin_model_ro.plan.library.resolve_assembly(roof.assembly)
    base = sum(layer.thickness.meters for layer in above_structure_layers(assembly)
               if layer.name != 'roofing')
    closures = [member for member in roof.members if member.category == 'furring'
                and member.section_ring is not None]
    assert closures
    for member in closures:
        solid = member_solid(member)
        assert isinstance(solid, GSweep)
        for x,_y,z in solid.profile:
            assert z <= roof_plane_z(roof,x) + base*roof_slope_factor(roof) + 1e-8
    hems = [member for member in roof.members if member.category == 'roof_panel_hem']
    assert hems and all(member.surface_mesh.triangles for member in hems)
    # The viewer rejects a surface mesh without one normal per position.
    assert all(len(member.surface_mesh.normals) == len(member.surface_mesh.positions)
               for member in hems)
