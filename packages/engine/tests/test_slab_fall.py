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


# --- a dish to a floor drain inside a level rim (decision #148) -----------------------------

_DRAIN = (ft(4).meters, ft(15).meters)  # 4' off the west edge, 5' off the north


def test_a_dish_falls_at_its_rate_to_the_drain_and_holds_its_rim() -> None:
    from typehaus.resolve.slab_dish import build_dish

    dish = build_dish("U", "SL-T", _DRAIN, list(_RING), 0.125)
    # The farthest edge (south, 15') sets the rise: 15 x 1/8" = 1 7/8".
    assert dish.rise_m == pytest.approx(1.875 * _IN)
    assert dish.lift(*_DRAIN) == pytest.approx(-dish.rise_m)
    for x, y in (*_RING, (ft(5).meters, 0.0), (0.0, ft(9).meters)):
        assert dish.lift(x, y) == pytest.approx(0.0, abs=1e-12)
    assert dish.lift(-1.0, 3.0) == 0.0 and dish.lift(ft(12).meters, 1.0) == 0.0  # clamped
    # The shallowest facet (south) falls at exactly the rate; the others are steeper.
    step = ft(1).meters
    south = dish.lift(_DRAIN[0], _DRAIN[1] - step) - dish.lift(*_DRAIN)
    west = dish.lift(_DRAIN[0] - step, _DRAIN[1]) - dish.lift(*_DRAIN)
    assert south == pytest.approx(0.125 * _IN) and west > south


def test_a_dish_refuses_a_rim_not_star_shaped_from_its_drain() -> None:
    from typehaus.resolve.slab_dish import build_dish

    # An L whose inside corner hides the north-east arm from a drain in the south-west.
    ell = [(0.0, 0.0), (4.0, 0.0), (4.0, 1.0), (1.0, 1.0), (1.0, 4.0), (0.0, 4.0)]
    with pytest.raises(ValueError, match="star-shaped"):
        build_dish("U", "SL-T", (3.5, 0.5), ell, 0.125)


def test_the_dish_mesh_top_follows_the_surface() -> None:
    from typehaus.resolve.slab_dish import build_dish, dish_mesh

    dish = build_dish("U", "SL-T", _DRAIN, list(_RING), 0.125)
    solid = ResolvedSolid("U-dish-0", "SL-T:dish-0", "s", "slab", list(_RING),
                          -0.0889, 0.0, dish=dish)
    mesh = dish_mesh(solid)
    top = mesh.positions[: len(_RING) + 1]
    for x, y, z in top:
        assert z == pytest.approx(solid.top_at(x, y))
    assert signed_volume(mesh.positions, mesh.triangles) == pytest.approx(
        Polygon(_RING).area * 0.0889, rel=1e-9)


def test_catlin_sauna_floor_dishes_to_its_drain(catlin_model_ro) -> None:
    """Hand number: 1/8"/ft x 63" (drain y=84" to the south rim at y=21", FT-B-S2's edge) = 0.656"."""
    model = catlin_model_ro
    slab = next(s for s in model.solids if s.uid == "CBS501AAAA")
    piece = next(s for s in model.solids if s.uid == "CBS501AAAA-dish-0")
    drain = next(o for o in model.canvas_objects if o.tag == "FX-B-SAUNA-FD")
    assert (slab.z1_m - piece.top_at(*drain.position)) / _IN == pytest.approx(0.656, abs=1e-3)
    assert (slab.z1_m - drain.z_m) / _IN == pytest.approx(0.656, abs=1e-3)
    # The rim, D-B-SAUNA's side included, stays flush with the gym.
    ring = piece.dish.ring
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1], strict=True):
        assert piece.top_at((ax + bx) / 2, (ay + by) / 2) == pytest.approx(slab.z1_m)
    assert not any(layer.bottom_plane is not None for wall in model.walls
                   if wall.tag.startswith("W-B-SA") or wall.tag == "W-B-CS"
                   for layer in wall.layers)


def test_the_deepest_lift_along_a_segment_is_found_on_its_hips() -> None:
    from types import SimpleNamespace

    from typehaus.resolve.slab_dish import build_dish, lowest_lift_along

    dish = build_dish("U", "SL-T", _DRAIN, list(_RING), 0.125)
    slab = ResolvedSolid("U", "SL-T", "s", "slab", list(_RING), -0.0889, 0.0)
    piece = ResolvedSolid("U-dish-0", "SL-T:dish-0", "s", "slab", list(_RING),
                          -0.0889, 0.0, dish=dish)
    model = SimpleNamespace(solids=[slab, piece])
    across = ((-1.0, _DRAIN[1]), (ft(13).meters, _DRAIN[1]))  # through the drain
    assert lowest_lift_along(model, slab, *across) == pytest.approx(-dish.rise_m)
    assert lowest_lift_along(model, slab, (-2.0, -1.0), (-1.0, -2.0)) == 0.0  # outside
