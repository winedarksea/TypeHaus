"""Selected product silhouettes and finishes survive the viewer and both 3D exports."""

from types import SimpleNamespace

import ifcopenshell
import pytest

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.ifc.architectural import is_parts_fixture, is_parts_furniture
from typehaus.emit.ifc.placeable_parts import parts_representation
from typehaus.model import FixtureType, Material, ModelRepresentation, inch
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import model_parts
from typehaus.model.placeable_symbols._lav_faucets import lav_faucet

IN = .0254


@pytest.mark.parametrize("faucet,overall,reach,outlet", [
    ("genta", 8.4375, 4.5625, 4.0625), ("indy", 6.25, 5.125, 4.625),
])
def test_faucet_has_published_reach_and_a_spout_below_its_separate_handle(
    faucet, overall, reach, outlet,
):
    parts = lav_faucet(30*IN, 22*IN, 36*IN, (36+overall)*IN, 8*IN, faucet)
    vertices = []
    for part in parts:
        if "mesh" in part:
            vertices.extend(part["mesh"]["positions"])
        else:
            x, y, z = part["center"]
            w, d, h = part["size"]
            vertices.extend((x+sx*w/2, y+sy*d/2, z+sz*h/2)
                            for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1))
    assert max(p[2] for p in vertices) == pytest.approx((36+overall)*IN)
    tip_y = min(p[1] for p in vertices)
    assert tip_y == pytest.approx((8-reach)*IN)
    tip = [p for p in vertices if p[1] == pytest.approx(tip_y)]
    assert min(p[2] for p in tip) == pytest.approx((36+outlet)*IN)


def test_orrsjon_has_a_wider_bowl_thick_ceramic_top_and_gloss_slab_drawers():
    parts = model_parts("drawer-vanity", 37*IN, 21.75*IN, (27.625+8.4375)*IN)
    bowl = next(p for p in parts if p["color"] == "porcelain" and "mesh" in p)
    assert bowl["size"][0] == pytest.approx(22*IN)
    fronts = [p for p in parts if p["color"] == "high-gloss-white"]
    assert min(p["center"][2]-p["size"][2]/2 for p in fronts) == pytest.approx(0)
    assert max(p["center"][2]+p["size"][2]/2 for p in fronts) == pytest.approx(25.125*IN)
    assert not any("mesh" in p for p in fronts)  # flat fronts, unlike AXSTAD


def test_chulton_has_visible_pulls_feet_and_a_backsplash():
    parts = model_parts("door-drawer-vanity", 30.9375*IN, 22.4375*IN, 44.4375*IN)
    front_face = min(p["center"][1]-p["size"][1]/2 for p in parts
                     if p["color"] == "appliance-white")
    pulls = [p for p in parts if p["color"] == "chrome" and p["center"][1] < front_face]
    assert len(pulls) == 3
    backsplash = [p for p in parts if p["color"] == "porcelain"
                  and p["center"][2] > 36*IN]
    assert len(backsplash) == 1
    assert backsplash[0]["size"][2] == pytest.approx(3.3125*IN)
    feet = [p for p in parts if p["color"] == "appliance-white"
            and p["center"][2] - p["size"][2]/2 == pytest.approx(0)]
    assert len(feet) == 4


def test_sunnersta_is_stainless_with_a_separate_open_white_frame():
    sink = model_parts("sunnersta-sink", 18*IN, 14*IN, 26.25*IN)
    assert "porcelain" not in {p["color"] for p in sink}
    assert {"appliance-steel", "chrome", "faucet"} <= {p["color"] for p in sink}
    frame = model_parts("sunnersta-frame", 44.125*IN, 22*IN, 54.75*IN)
    assert max(p["size"][2] for p in frame if p["color"] == "appliance-steel") < IN
    assert is_parts_furniture(SimpleNamespace(
        model_representation=ModelRepresentation(symbol="sunnersta-frame")))


@pytest.mark.parametrize("finish,color", [("polished", "#cbd2d8"), ("brushed", "#aaa79e")])
def test_faucet_material_color_reaches_viewer_glb_and_ifc(finish, color):
    material = Material(tag="selected-faucet", name="Faucet finish", color=color, finish=finish)
    materials = {material.tag: material}
    product = FixtureType(tag="VANITY", name="Test vanity", footprint=(inch(30), inch(18)),
                          height=inch(44.4375), model_representation=ModelRepresentation(
                              symbol="sektion-vanity", material_refs={"faucet": material.tag}))
    viewer = _symbol_geometry(product, product.footprint, materials=materials)["model_parts"]
    faucets = [p for p in viewer if p.get("material_ref") == material.tag]
    assert faucets and all(p["color"] == color for p in faucets)
    assert all(p["metalness"] >= .85 for p in faucets)
    expected_rgb = tuple(int(color[i:i+2], 16)/255 for i in (1, 3, 5))
    exported_colors = []
    recorder = SimpleNamespace(
        add_mesh=lambda mesh, rgba: exported_colors.append(rgba),
        add_prism=lambda ring, z0, z1, rgba: exported_colors.append(rgba))
    _add_canvas_parts(recorder, SimpleNamespace(position=(0, 0), rotation_degrees=0, z_m=0),
                      product, materials)
    assert expected_rgb + (1.0,) in exported_colors
    f = ifcopenshell.file(schema="IFC4")
    parts = model_parts("sektion-vanity", 30*IN, 18*IN, 44.4375*IN,
                        material_refs={"faucet": material.tag})
    parts_representation(f, f.create_entity("IfcGeometricRepresentationContext"), parts,
                         (0, 0), 0, 0, materials=materials)
    assert expected_rgb in [(c.Red, c.Green, c.Blue) for c in f.by_type("IfcColourRgb")]


@pytest.mark.parametrize("symbol", ["sektion-vanity", "sektion-vanity-indy", "drawer-vanity",
                                     "drawer-vanity-indy", "door-drawer-vanity", "sunnersta-sink"])
def test_selected_vanities_export_their_geometry_in_ifc(symbol):
    assert is_parts_fixture(symbol)
