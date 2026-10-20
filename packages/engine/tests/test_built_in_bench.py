"""The fitted booth is one assembly in fabrication, viewer, GLB and IFC."""
from __future__ import annotations

import math

import pytest
from pydantic import ValidationError
from shapely.geometry import Point, Polygon

from typehaus.cli.cmd_millwork import _flat_rows, _markdown
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model import BuiltInBenchSpec, inch
from typehaus.model.bench_parts import bench_parts
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import place_local
from typehaus.takeoff.bench_millwork import bench_cut_rows
from typehaus.takeoff.hardwood import hardwood_takeoff
from typehaus.takeoff.millwork_pdf import write_millwork_pdf
from typehaus.takeoff.panel_stock import panel_order_rows

INCH = .0254
BENCH_TAG = "FURN-M-STUDY-BENCH"


@pytest.fixture
def bench_type(catlin_plan):
    return next(t for t in catlin_plan.library.furniture_types if t.tag == "FT-STUDY-BENCH")


def test_fit_uses_current_finishes_and_preserves_working_gap(catlin_model_ro, bench_type):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    room = next(r for r in model.rooms if r.tag == "RM-M-STUDY")
    west, south, east, north = Polygon(room.clear_face).bounds
    bench = objects[BENCH_TAG]
    bx0, by0, bx1, by1 = Polygon(bench.footprint).bounds
    assert (bx0 - west, east - bx1) == pytest.approx((.8125 * INCH,) * 2)
    assert north - by1 == pytest.approx(.0625 * INCH)
    assert bench.uid == "AZ3GY4JQFH"
    fixed = objects["FURN-M-STUDY-DESK"]
    leaf = objects["FURN-M-STUDY-DESK-LEAF"]
    fx0, fy0, fx1, fy1 = Polygon(fixed.footprint).bounds
    lx0, ly0, lx1, ly1 = Polygon(leaf.footprint).bounds
    assert fx1 == pytest.approx(lx0)
    assert (fy0, fy1) == pytest.approx((ly0, ly1))
    assert fy1 - fy0 == pytest.approx(16 * INCH)
    assert by0 - fy1 >= 7.125 * INCH
    assert fy0 - south == pytest.approx(.8125 * INCH)
    assert fx0 == pytest.approx(bx0) and lx1 == pytest.approx(bx1)
    spec = bench_type.built_in_bench
    assert spec.back_angle_degrees == 100
    assert spec.deck_height.inches == 17.5
    assert spec.effective_seat_depth.inches == 17
    assert spec.occupied_seat_height.inches == 19.5
    assert spec.lumbar_elevation / INCH == pytest.approx(26.5)
    footrest = objects["FURN-M-STUDY-FOOTREST"]
    assert Polygon(footrest.footprint).intersection(Polygon(bench.footprint)).is_empty
    register = objects["REG-M-RET-STUDY"]
    assert not Polygon(footrest.footprint).buffer(.5 * INCH).contains(
        Point(register.position))


def test_cuts_and_meshes_share_real_shapes_and_materials(catlin_model_ro, bench_type):
    parts = bench_parts(bench_type.built_in_bench)
    assert sum(p.name.startswith("support ") for p in parts) == 4
    assert sum(p.name.startswith("back gusset ") for p in parts) == 4
    panels = bench_cut_rows(catlin_model_ro, "panel")
    solids = [r for r in hardwood_takeoff(catlin_model_ro) if BENCH_TAG in r["tags"]]
    rows = {r["location"]: r for r in panels + solids}
    assert set(rows) == {p.name for p in parts if p.stock_kind != "upholstery"}
    for part in parts:
        if part.stock_kind == "upholstery":
            continue
        row = rows[part.name]
        assert row["pieces"] == 1 and row["material"] == part.material_ref
        assert (row["finished_thickness_in"], row["finished_width_in"],
                row["finished_length_in"]) == pytest.approx(
                    tuple(v / INCH for v in (part.thickness_m, part.width_m, part.length_m)),
                    abs=.001)
        if part.stock_kind == "panel":
            assert row["panel_grade"] == "A-1" and row["panel_core"] == "veneer core"
            assert "rough_board_feet" not in row
    assert not any(r["material"] == "walnut-shelf-8q"
                   for r in hardwood_takeoff(catlin_model_ro))
    gusset = next(p for p in parts if p.name == "back gusset 1")
    assert math.degrees(math.atan2(gusset.width_m, gusset.length_m)) == pytest.approx(10)
    back = next(p for p in parts if p.name == "back substrate")
    points = back.geometry["mesh"]["positions"]
    top, bottom = max(z for x, y, z in points), min(z for x, y, z in points)
    top_rear = max(y for x, y, z in points if abs(z - top) < 1e-8)
    bottom_rear = max(y for x, y, z in points if abs(z - bottom) < 1e-8)
    assert math.degrees(math.atan2(top_rear - bottom_rear, top - bottom)) == pytest.approx(10)


def test_panel_blanks_enclose_actual_geometry_in_each_boards_own_frame(bench_type):
    angle = bench_type.built_in_bench.recline_radians
    for part in bench_parts(bench_type.built_in_bench):
        if part.stock_kind != "panel":
            continue
        if part.name.startswith(("support ", "back gusset ")):
            axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        elif part.name == "seat deck":
            axes = ((0, 0, 1), (0, 1, 0), (1, 0, 0))
        elif part.name == "back substrate":
            axes = ((0, math.cos(angle), -math.sin(angle)),
                    (0, math.sin(angle), math.cos(angle)), (1, 0, 0))
        else:
            axes = ((0, 1, 0), (0, 0, 1), (1, 0, 0))
        extents = []
        for axis in axes:
            stations = [sum(a * v for a, v in zip(axis, vertex, strict=True))
                        for vertex in part.geometry["mesh"]["positions"]]
            extents.append(max(stations) - min(stations))
        assert extents == pytest.approx((part.thickness_m, part.width_m, part.length_m)), part.name


def test_viewer_and_glb_preserve_parts_and_linear_material_colors(catlin_model_ro, bench_type):
    materials = {m.tag: m for m in catlin_model_ro.plan.library.materials}
    parts = bench_parts(bench_type.built_in_bench)
    viewer = next(t for t in canvas_object_types(catlin_model_ro.plan)
                  if t["tag"] == bench_type.tag)
    assert len(viewer["model_parts"]) == len(parts)
    assert {p["color"] for p in viewer["model_parts"]} >= {"#80634f", "#a39a90"}
    for actual, part in zip(viewer["model_parts"], parts, strict=True):
        assert actual["mesh"] == part.geometry["mesh"]
        assert actual["material_ref"] == part.material_ref
    occurrence = next(o for o in catlin_model_ro.canvas_objects if o.tag == BENCH_TAG)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, occurrence, bench_type, materials)
    for material_ref in bench_type.built_in_bench.material_refs:
        rgb = tuple(int(materials[material_ref].color[i:i + 2], 16) / 255 for i in (1, 3, 5))
        linear = tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb)
        assert (*linear, 1) in mesh._buckets


def test_ifc_preserves_every_shared_mesh(catlin_ifc_path, catlin_model_ro, bench_type):
    import ifcopenshell

    file = ifcopenshell.open(str(catlin_ifc_path))
    entity = next(e for e in file.by_type("IfcFurniture") if e.Name == BENCH_TAG)
    items = entity.Representation.Representations[0].Items
    parts = bench_parts(bench_type.built_in_bench)
    assert len(items) == len(parts)
    occurrence = next(o for o in catlin_model_ro.canvas_objects if o.tag == BENCH_TAG)
    for item, part in zip(items, parts, strict=True):
        mesh = part.geometry["mesh"]
        xy = place_local([(x, y) for x, y, z in mesh["positions"]],
                         occurrence.position, occurrence.rotation_degrees)
        expected = [(x, y, vertex[2] + occurrence.z_m)
                    for (x, y), vertex in zip(xy, mesh["positions"], strict=True)]
        for actual, point in zip(item.Coordinates.CoordList, expected, strict=True):
            assert actual == pytest.approx(point)
        assert len(item.CoordIndex) == len(mesh["triangles"])


def test_panel_exports_preserve_purchasing_grade_and_do_not_add_board_feet(
        catlin_model_ro, tmp_path):
    hardwood = hardwood_takeoff(catlin_model_ro)
    panels = panel_order_rows(bench_cut_rows(catlin_model_ro, "panel"))
    assert {row["material"]: row["sheets_to_order"] for row in panels} == {
        "study-birch-ply": 2}
    assert all("pieces" not in row and "finished_width_in" not in row for row in panels)
    flattened = _flat_rows(panels)
    assert all(r["panel_grade"] == "A-1" and r["rough_board_feet"] == "" for r in flattened)
    markdown = _markdown(hardwood + panels)
    assert "Plywood sheets to order" in markdown and "sheets to order" in markdown
    assert "furniture panel" not in markdown
    pdf = tmp_path / "millwork.pdf"
    write_millwork_pdf(pdf, "catlin", _flat_rows(hardwood), flattened)
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert pdf.stat().st_size > 1000


def test_bench_orders_one_glued_front_and_two_single_board_trim_pieces(catlin_model_ro):
    rows = [row for row in hardwood_takeoff(catlin_model_ro) if BENCH_TAG in row["tags"]]
    assert len(rows) == 3
    front = next(row for row in rows if row["location"] == "walnut front")
    assert front["pieces"] == 1 and front["layup"] == "edge-glued panel"
    assert front["boards_per_piece"] == 2
    assert (front["finished_thickness_in"], front["finished_width_in"],
            front["finished_length_in"]) == pytest.approx((.75, 14.75, 48.625))
    assert "slotted fixings" in front["stock_note"]
    assert "do not glue to plywood supports" in front["stock_note"]
    trim = [row for row in rows if row is not front]
    assert {row["location"] for row in trim} == {"seat edge", "back cap"}
    assert all(row["pieces"] == 1 and row["layup"] == "one board" for row in trim)
    assert not any(row["material"] == front["material"]
                   for row in bench_cut_rows(catlin_model_ro, "panel"))


@pytest.mark.parametrize("update", [
    {"panel_thickness": inch(0)}, {"back_angle_degrees": 90},
    {"back_height": inch(18)}, {"occupied_seat_height": inch(30)},
    {"lumbar_height_above_seat": inch(10)}, {"internal_partition_count": -1},
    {"seat_foam_ifd_max_lbf": 20},
])
def test_impossible_bench_construction_is_rejected(bench_type, update):
    with pytest.raises(ValidationError):
        BuiltInBenchSpec(**{**bench_type.built_in_bench.model_dump(), **update})


def test_bench_spec_round_trips_without_losing_fit_inputs(bench_type):
    spec = bench_type.built_in_bench
    assert BuiltInBenchSpec.model_validate_json(spec.model_dump_json()) == spec
