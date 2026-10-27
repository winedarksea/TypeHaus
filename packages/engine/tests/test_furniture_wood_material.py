"""``FurnitureType.wood_material_ref``: a built-in's wood takes its material in every reader."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.checks.integrity.catalog_tags import unknown_wood_material_ref
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _authored_material_color
from typehaus.model import (
    Building,
    BuiltInBookcaseBay,
    BuiltInBookcaseSpec,
    FurnitureType,
    Material,
    Project,
    Site,
    ft,
    inch,
    m,
)
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import PART_COLORS, part_hex
from typehaus.model.plan import Library, PlanModel
from typehaus.source import load_plan

OAK = Material(tag="oak-shelf", name="White oak shelving", color="#c9b08c",
               finish="oak-board", species="oak")
BOOKCASE = FurnitureType(tag="F-SHELF", name="Shelf", footprint=(inch(30), inch(12)),
                         height=ft(7), plan_symbol="bookcase", wood_material_ref="oak-shelf")
BUILT_IN = FurnitureType(
    tag="F-BUILT-IN", name="Built-in", footprint=(inch(33.25), inch(10.625)), height=ft(5),
    wood_material_ref="oak-shelf",
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(31.25), height=ft(5),
                                 horizontal_board_count=5),),
        shelf_depth=inch(9.875), horizontal_board_thickness=inch(1.5),
        divider_thickness=inch(.75), back_thickness=inch(.75)))


def _plan(*types: FurnitureType) -> PlanModel:
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        library=Library(furniture_types=types, materials=(OAK,)))


def test_symbol_wood_parts_take_the_material_and_the_back_keeps_its_shadow() -> None:
    record = canvas_object_types(_plan(BOOKCASE))[0]
    wood = [part for part in record["model_parts"] if part.get("material_ref")]
    assert wood and all(part["color"] == "#c9b08c" for part in wood)
    # The bookcase back is drawn `wood-dark`: a shadowed back, not a second board of oak.
    assert any(part["color"] == part_hex("wood-dark") and "material_ref" not in part
               for part in record["model_parts"])


def test_every_built_in_board_is_the_named_wood() -> None:
    record = canvas_object_types(_plan(BUILT_IN))[0]
    assert {(p["color"], p["material_ref"]) for p in record["model_parts"]} == {
        ("#c9b08c", "oak-shelf")}


@pytest.mark.parametrize("symbol,wood_role", [
    ("bookcase", "wood"), ("sauna-bench", "sauna-wood"),
])
def test_no_ref_keeps_the_generic_furniture_wood(symbol, wood_role) -> None:
    plain = BOOKCASE.model_copy(update={"wood_material_ref": None, "plan_symbol": symbol})
    record = canvas_object_types(_plan(plain))[0]
    assert not any("material_ref" in part for part in record["model_parts"])
    assert part_hex(wood_role) in {part["color"] for part in record["model_parts"]}


def test_the_glb_colours_the_same_wood_the_viewer_does() -> None:
    item = SimpleNamespace(position=(0.0, 0.0), rotation_degrees=0.0, z_m=0.0, mount=None)
    materials = {OAK.tag: OAK}
    for kind in (BOOKCASE, BUILT_IN):
        mb = _MeshBuilder()
        assert _add_canvas_parts(mb, item, kind, materials)
        assert _authored_material_color(OAK) in mb._buckets
        assert PART_COLORS["wood"] not in mb._buckets


def test_mixed_bookcase_materials_agree_in_viewer_and_glb() -> None:
    plywood = Material(tag="plywood", name="Maple plywood", color="#e3d3b4")
    spec = BUILT_IN.built_in_bookcase.model_copy(update={
        "panel_material_ref": plywood.tag, "shelf_nosing_depth": inch(.75),
        "shelf_nosing_height": inch(1.5), "face_strip_width": inch(1.5),
    })
    furniture = BUILT_IN.model_copy(update={"built_in_bookcase": spec})
    plan = _plan(furniture)
    plan = plan.model_copy(update={"library": plan.library.model_copy(
        update={"materials": (OAK, plywood)})})
    parts = canvas_object_types(plan)[0]["model_parts"]
    assert {part["material_ref"] for part in parts} == {OAK.tag, plywood.tag}
    assert all(part["color"] == (OAK.color if part["material_ref"] == OAK.tag else plywood.color)
               for part in parts)
    mb = _MeshBuilder()
    item = SimpleNamespace(position=(0.0, 0.0), rotation_degrees=0.0, z_m=0.0, mount=None)
    assert _add_canvas_parts(mb, item, furniture, {OAK.tag: OAK, plywood.tag: plywood})
    assert set(mb._buckets) == {_authored_material_color(OAK), _authored_material_color(plywood)}


@pytest.mark.parametrize("panel_reference", [False, True])
def test_a_dangling_wood_material_ref_is_an_error(starter_dir: Path, panel_reference) -> None:
    result = load_plan(starter_dir)
    assert result.plan is not None
    broken = BOOKCASE.model_copy(update={"wood_material_ref": "no-such-oak"})
    if panel_reference:
        broken = BUILT_IN.model_copy(update={
            "tag": BOOKCASE.tag, "wood_material_ref": None,
            "built_in_bookcase": BUILT_IN.built_in_bookcase.model_copy(
                update={"panel_material_ref": "no-such-oak"}),
        })
    plan = result.plan.model_copy(update={"library": result.plan.library.model_copy(
        update={"furniture_types": (*result.plan.library.furniture_types, broken)})})
    ctx, _ = build_context(plan, starter_dir)
    findings = unknown_wood_material_ref(ctx)
    assert [f.element_tags for f in findings] == [("F-SHELF",)]
    assert findings[0].severity.value == "error" and "no-such-oak" in findings[0].message
