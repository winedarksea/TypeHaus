"""``FurnitureType.wood_material_ref``: a built-in's wood takes its material in every reader."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from typehaus.checks import build_context
from typehaus.checks.integrity.catalog_tags import unknown_wood_material_ref
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _hex_rgba
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

OAK = Material(tag="oak-shelf", name="White oak shelving", color="#c9b08c", finish="oak-board")
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


def test_no_ref_keeps_the_generic_furniture_wood() -> None:
    plain = BOOKCASE.model_copy(update={"wood_material_ref": None})
    record = canvas_object_types(_plan(plain))[0]
    assert not any("material_ref" in part for part in record["model_parts"])
    assert part_hex("wood") in {part["color"] for part in record["model_parts"]}


def test_the_glb_colours_the_same_wood_the_viewer_does() -> None:
    item = SimpleNamespace(position=(0.0, 0.0), rotation_degrees=0.0, z_m=0.0)
    materials = {OAK.tag: OAK}
    for kind in (BOOKCASE, BUILT_IN):
        mb = _MeshBuilder()
        assert _add_canvas_parts(mb, item, kind, materials)
        assert _hex_rgba("#c9b08c") in mb._buckets
        assert PART_COLORS["wood"] not in mb._buckets


def test_a_dangling_wood_material_ref_is_an_error(starter_dir: Path) -> None:
    result = load_plan(starter_dir)
    assert result.plan is not None
    broken = BOOKCASE.model_copy(update={"wood_material_ref": "no-such-oak"})
    plan = result.plan.model_copy(update={"library": result.plan.library.model_copy(
        update={"furniture_types": (*result.plan.library.furniture_types, broken)})})
    ctx, _ = build_context(plan, starter_dir)
    findings = unknown_wood_material_ref(ctx)
    assert [f.element_tags for f in findings] == [("F-SHELF",)]
    assert findings[0].severity.value == "error" and "no-such-oak" in findings[0].message
