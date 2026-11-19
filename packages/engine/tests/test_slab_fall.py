"""A pour that falls to drain (decision #138): one plane, constant thickness, every emitter."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.model import Slab, SlabFall, ft, inch, pt
from typehaus.resolve.geometry_ir import signed_volume
from typehaus.resolve.geometry_slice import CutPlane, slice_part
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.slab_fall import fall_plane, slab_top_at, sloped_slab_mesh

_IN = inch(1).meters
_RING = ((0.0, 0.0), (ft(10).meters, 0.0), (ft(10).meters, ft(20).meters),
         (0.0, ft(20).meters))


def _slab(**overrides) -> Slab:
    fields = dict(uid="TSTSLB0001", tag="SL-T", kind="pour", thickness=inch(3.5),
                  outline=tuple(pt(ft(x / ft(1).meters), ft(y / ft(1).meters))
                                for x, y in _RING),
                  top_elevation=ft(-1),
                  fall=SlabFall(toward="north", rate_in_per_ft=0.125, low_edge=ft(20)))
    fields.update(overrides)
    return Slab(**fields)


def test_a_fall_needs_a_pour_at_an_elevation() -> None:
    with pytest.raises(ValueError, match="needs kind"):
        _slab(kind=None)
    with pytest.raises(ValueError, match="needs kind"):
        _slab(top_elevation=None)


def test_the_top_rises_an_eighth_a_foot_away_from_the_low_edge() -> None:
    slab = _slab()
    assert slab_top_at(slab, 0.0, ft(20).meters) == pytest.approx(ft(-1).meters)
    # 20' south of the door line: 2 1/2" up, whatever x.
    for x in (0.0, ft(7).meters):
        assert (slab_top_at(slab, x, 0.0) - ft(-1).meters) / _IN == pytest.approx(2.5)
    assert fall_plane(_slab(fall=None)) is None


def _solid() -> ResolvedSolid:
    top = ft(-1).meters
    return ResolvedSolid("TSTSLB0001", "SL-T", "garage", "slab", _RING, top - 3.5 * _IN, top,
                         top_plane=fall_plane(_slab()))


def test_the_mesh_lifts_top_and_bottom_together() -> None:
    solid = _solid()
    mesh = sloped_slab_mesh(solid)
    south = [z for x, y, z in mesh.positions if y == 0.0]
    assert (max(south) - ft(-1).meters) / _IN == pytest.approx(2.5)
    assert (max(south) - min(south)) / _IN == pytest.approx(3.5)
    assert solid.top_at(0.0, 0.0) == pytest.approx(max(south))
    volume = signed_volume(mesh.positions, mesh.triangles)
    assert volume == pytest.approx(Polygon(_RING).area * 3.5 * _IN)  # constant thickness


def test_a_section_cuts_the_falling_pour_as_a_parallelogram() -> None:
    from typehaus.model import Library
    from typehaus.resolve.geometry_build import _solid_geometry

    plan = type("P", (), {"library": Library()})()
    part = _solid_geometry(_solid(), plan).parts[0]
    profiles = slice_part(part, CutPlane(axis="y", station_m=ft(5).meters))
    zs = sorted(z for profile in profiles for _u, z in profile.outline)
    assert (zs[-1] - zs[0]) / _IN == pytest.approx(2.5 + 3.5, abs=1e-6)


def test_catlin_garage_slab_reaches_gltf_and_ifc_on_its_plane(catlin_model_ro,
                                                               catlin_ifc_path) -> None:
    import ifcopenshell

    from typehaus.emit.gltf import emit_gltf_dict

    slab = next(s for s in catlin_model_ro.solids if s.tag == "SL-G-FLOOR")
    assert slab.top_plane is not None
    high = max(slab.top_at(x, y) for x, y in slab.outline)
    gltf, _ = emit_gltf_dict(catlin_model_ro)
    node = next(n for n in gltf["nodes"] if n["extras"].get("uid") == slab.uid)
    accessor = gltf["accessors"][
        gltf["meshes"][node["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
    assert accessor["max"][1] == pytest.approx(high, abs=1e-4)  # glTF is y-up
    ifc = ifcopenshell.open(str(catlin_ifc_path))
    element = next(e for e in ifc.by_type("IfcSlab") if e.Name == "SL-G-FLOOR")
    face_set = element.Representation.Representations[0].Items[0]
    assert face_set.is_a("IfcTriangulatedFaceSet")
    assert max(p[2] for p in face_set.Coordinates.CoordList) == pytest.approx(high, abs=1e-6)


def test_the_stem_board_runs_down_to_the_falling_slab(catlin_model_ro) -> None:
    """GARAGE_ICF_6's gwb-stem goes up after the pour: its foot is the slab's plane."""
    from typehaus.resolve.geometry_ir import GBox

    slab = next(s for s in catlin_model_ro.solids if s.tag == "SL-G-FLOOR")
    wall = next(w for w in catlin_model_ro.walls if w.tag == "W-GF-E")
    element = catlin_model_ro.geometry.by_uid(wall.uid)
    (box,) = next(p for p in element.parts if p.key == "layer:gwb-stem").solids
    assert isinstance(box, GBox)
    for x, y, z in box.corners_bottom:
        assert z == pytest.approx(slab.top_at(x, y), abs=1e-9)
    rise = max(z for *_xy, z in box.corners_bottom) - min(z for *_xy, z in box.corners_bottom)
    assert rise / _IN == pytest.approx(2.77, abs=0.05)
