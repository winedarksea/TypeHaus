"""One countertop slab shape across the live payload and the GLB (→ geometry_countertops)."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.emit.gltf.emitter import emit_gltf_dict
from typehaus.emit.gltf.palette import _material_finish_color, authored_colors
from typehaus.model.placeable_symbols import PART_COLORS, part_hex
from typehaus.resolve.geometry_countertops import countertop_prisms, slab_hosts
from typehaus.server.model_json import model_to_dict

INCH = 0.0254


def test_tea_kettle_stands_on_north_counter_clear_of_sink_and_uppers(catlin_model_ro):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    kettle = objects["APPL-M-KETTLE"]
    top = next(item for item in model.countertops if item.tag == "CT-M-KIT-N")
    assert Polygon(top.outline).covers(Polygon(kettle.footprint))
    assert kettle.body_z0_m == pytest.approx(countertop_prisms(model, top)[0].z1_m)
    assert kettle.body_z1_m - kettle.body_z0_m == pytest.approx(0.275)
    assert not Polygon(kettle.footprint).intersects(
        Polygon(objects["FX-M-KITCH-SINK"].footprint))
    assert kettle.body_z1_m < objects["FURN-M-KIT-WE1"].body_z0_m
    # The intended outlet remains within a short countertop cord run.
    assert Polygon(kettle.footprint).distance(
        Polygon(objects["ED-M-LIVING-KET1"].footprint)) < 0.30


def test_rivelia_stands_beside_kettle_with_accepted_overhead_gap(catlin_model_ro):
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    coffee = objects["APPL-M-COFFEE"]
    footprint = Polygon(coffee.footprint)
    top = next(item for item in catlin_model_ro.countertops if item.tag == "CT-M-KIT-N")
    assert Polygon(top.outline).covers(footprint)
    assert coffee.position == pytest.approx((321.375 * INCH, 413.875 * INCH))
    assert coffee.rotation_degrees == pytest.approx(0)
    assert coffee.body_z0_m == pytest.approx(
        countertop_prisms(catlin_model_ro, top)[0].z1_m)
    assert coffee.body_z1_m - coffee.body_z0_m == pytest.approx(14.75 * INCH)
    assert footprint.distance(Polygon(objects["APPL-M-KETTLE"].footprint)) / INCH == (
        pytest.approx(8.401, abs=0.001))
    assert footprint.distance(Polygon(objects["FX-M-KITCH-SINK"].footprint)) == (
        pytest.approx(9.75 * INCH))
    upper = objects["FURN-M-KIT-WE1"]
    assert footprint.intersects(Polygon(upper.footprint))
    assert (upper.body_z0_m - coffee.body_z1_m) / INCH == pytest.approx(2.75)
    # Proximity proves a short route is possible, not that branch wiring is resolved.
    assert footprint.distance(Polygon(objects["ED-M-LIVING-KET1"].footprint)) < 0.30


def test_the_peninsula_draws_its_notched_slab_at_the_counter(catlin_model_ro):
    top = next(item for item in catlin_model_ro.countertops
               if item.tag == "CT-M-KIT-PENINSULA")
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    prisms = countertop_prisms(catlin_model_ro, top)
    assert len(prisms) == 1
    (prism,) = prisms
    from typehaus.resolve.fillet import filleted_ring

    # The viewer draws the fabricator's corners: R1" outside, R3/8" in the notch.
    assert Polygon(prism.ring).equals_exact(
        Polygon(filleted_ring(top.outline, top.corner_radii_m)), 1e-9)
    assert Polygon(top.outline).area == pytest.approx((84.5 * 25 + 73.5 * 15) * INCH * INCH)
    assert Polygon(prism.ring).area < Polygon(top.outline).area
    assert prism.z1_m == pytest.approx(max(objects[tag].body_z1_m for tag in top.hosts))
    assert prism.z1_m - prism.z0_m == pytest.approx(top.thickness_m)


def test_the_seating_brackets_are_steel_under_the_knee(catlin_model_ro):
    """Five bars, 12" in and 12" out, their tops 1/16" under the stone."""
    top = next(item for item in catlin_model_ro.countertops
               if item.tag == "CT-M-KIT-PENINSULA")
    z0 = countertop_prisms(catlin_model_ro, top)[0].z0_m
    bars = [obj for obj in catlin_model_ro.canvas_objects
            if obj.type_ref == "FT-KIT-CT-BRACKET-24"]
    assert len(bars) == 5
    slab = Polygon(top.outline)
    stations = sorted(obj.position[0] / INCH for obj in bars)
    assert [b - a for a, b in zip(stations, stations[1:], strict=False)] == pytest.approx(
        [16.375] * 4)
    for obj in bars:
        assert slab.contains(Polygon(obj.footprint))
        assert (z0 - obj.body_z1_m) / INCH == pytest.approx(0.0625, abs=1e-3)
        assert Polygon(obj.footprint).bounds[1] / INCH == pytest.approx(307.375)
    types = {item["tag"]: item for item in
             model_to_dict(catlin_model_ro)["catalog"]["canvas_object_types"]}
    assert {part["color"] for part in types["FT-KIT-CT-BRACKET-24"]["model_parts"]} == {
        part_hex("metal")}


def test_explicit_sink_opening_replaces_the_bases_centred_counter(catlin_model_ro):
    top = next(item for item in catlin_model_ro.countertops if item.tag == "CT-M-KIT-N")
    from shapely.geometry import Point

    from typehaus.resolve.fillet import filleted_ring

    sink = Polygon(top.cutouts[0])
    slab = Polygon(filleted_ring(top.outline, top.corner_radii_m))
    (faucet,) = top.holes
    drilled = Point(faucet.center).buffer(faucet.diameter_m / 2.0, quad_segs=4)
    drawn = sum(Polygon(prism.ring, holes=prism.voids).area
                for prism in countertop_prisms(catlin_model_ro, top))
    assert drawn == pytest.approx(slab.difference(sink).difference(drilled).area, rel=1e-6)
    hosted = slab_hosts(catlin_model_ro)
    assert hosted["FURN-M-KIT-SINKBASE"] == "CT-M-KIT-N"
    assert hosted["FURN-M-KIT-PEN-B24-W"] == "CT-M-KIT-PENINSULA"


def test_sink_without_explicit_cutout_keeps_its_schematic_counter(catlin_model_ro):
    from dataclasses import replace
    from types import SimpleNamespace

    tops = [replace(top, cutouts=()) for top in catlin_model_ro.countertops]
    model = SimpleNamespace(plan=catlin_model_ro.plan,
                            canvas_objects=catlin_model_ro.canvas_objects, countertops=tops)
    assert "FURN-M-KIT-SINKBASE" not in slab_hosts(model)
    top = next(item for item in tops if item.tag == "CT-M-KIT-N")
    objects = {obj.tag: obj for obj in model.canvas_objects}
    expected = Polygon(top.outline).difference(
        Polygon(objects["FURN-M-KIT-SINKBASE"].footprint))
    drawn = sum(Polygon(part.ring, holes=part.voids).area
                for part in countertop_prisms(model, top))
    assert drawn == pytest.approx(expected.area)


def test_cutout_tracks_fixture_translation_and_rotation(catlin_model_ro):
    from dataclasses import replace

    from shapely import affinity

    from typehaus.resolve.countertops import _fixture_cutouts

    model = catlin_model_ro
    top = next(item for item in model.countertops if item.tag == "CT-M-KIT-N")
    authored = model.plan.by_tag(top.tag)
    objects = {obj.tag: obj for obj in model.canvas_objects}
    sink = objects["FX-M-KITCH-SINK"]
    moved = replace(sink, position=(sink.position[0] + INCH, sink.position[1]),
                    rotation_degrees=180)
    objects[sink.tag] = moved
    rings, findings = _fixture_cutouts(authored, top, model.plan, objects)
    assert not findings
    expected = affinity.translate(
        affinity.rotate(Polygon(top.cutouts[0]), 180, origin=sink.position), xoff=INCH)
    assert Polygon(rings[0]).symmetric_difference(expected).area < 1e-9


@pytest.mark.parametrize("tag", ["MISSING-FIXTURE", "APPL-M-DW"])
def test_missing_or_undeclared_fixture_cutout_is_reported(catlin_model_ro, tag):
    from typehaus.resolve.countertops import _fixture_cutouts

    model = catlin_model_ro
    top = next(item for item in model.countertops if item.tag == "CT-M-KIT-N")
    authored = model.plan.by_tag(top.tag).model_copy(update={"cutouts": (tag,)})
    rings, findings = _fixture_cutouts(authored, top, model.plan,
                                     {obj.tag: obj for obj in model.canvas_objects})
    assert not rings
    assert len(findings) == 1 and findings[0].check_id == "integrity.countertop_ref"


def test_fixture_cutout_outside_slab_is_reported(catlin_model_ro):
    from dataclasses import replace

    from typehaus.resolve.countertops import _fixture_cutouts

    model = catlin_model_ro
    top = next(item for item in model.countertops if item.tag == "CT-M-KIT-N")
    objects = {obj.tag: obj for obj in model.canvas_objects}
    sink = objects["FX-M-KITCH-SINK"]
    objects[sink.tag] = replace(sink, position=(0.0, 0.0))
    rings, findings = _fixture_cutouts(model.plan.by_tag(top.tag), top, model.plan, objects)
    assert not rings
    assert len(findings) == 1 and findings[0].check_id == "integrity.countertop_cutout"


def test_hosted_cabinets_drop_their_symbol_counter_in_model_json(catlin_model_ro):
    payload = model_to_dict(catlin_model_ro)
    objects = {item["tag"]: item for item in payload["canvas_objects"]}
    assert objects["FURN-M-KIT-PEN-B24-W"]["countertop_ref"] == "CT-M-KIT-PENINSULA"
    assert objects["FURN-M-KIT-SINKBASE"]["countertop_ref"] == "CT-M-KIT-N"
    types = {item["tag"]: item for item in payload["catalog"]["canvas_object_types"]}
    for type_ref in ("SEKT-B24", "SEKT-SINK-B36"):
        roles = [part.get("role") for part in types[type_ref]["model_parts"]]
        assert "counter" in roles, type_ref

    rows = {row["tag"]: row for row in payload["countertops"]}
    peninsula = rows["CT-M-KIT-PENINSULA"]
    assert peninsula["material_ref"] == "quartz-counter"
    assert peninsula["host_uid"] == objects["FURN-M-KIT-PEN-END"]["uid"]
    assert peninsula["z1_m"] - peninsula["z0_m"] == pytest.approx(1.181 * INCH)
    # Filleted (four R1" corners, one R3/8" notch), so a little under the gross rectangle.
    assert Polygon(peninsula["parts"][0]["outline"]).area == pytest.approx(
        (84.5 * 25 + 73.5 * 15) * INCH * INCH, rel=1e-3)
    assert "CT-M-LIV-E-S" not in rows
    assert rows["CT-M-LIV-E-N"]["material_ref"] == "ash-counter-6q"


def test_countertops_reach_the_glb_in_their_own_material(catlin_model_ro):
    payload = model_to_dict(catlin_model_ro)
    rows = payload["countertops"]
    gltf, _blob = emit_gltf_dict(catlin_model_ro)
    slabs = [node for node in gltf["nodes"]
             if node["extras"].get("trade") == "millwork"
             and node["extras"].get("kind") == "canvas_object"]
    assert len(slabs) == len(rows)
    assert {node["extras"]["uid"] for node in slabs} == {row["host_uid"] for row in rows}
    colors = set()
    for node in slabs:
        mesh = gltf["meshes"][node["mesh"]]
        for primitive in mesh["primitives"]:
            material = gltf["materials"][primitive["material"]]
            colors.add(tuple(round(value, 4) for value in
                             material["pbrMetallicRoughness"]["baseColorFactor"]))
    authored = authored_colors(catlin_model_ro)
    for ref in ("ash-counter-6q", "quartz-counter"):
        expected = _material_finish_color(ref, "millwork", authored)
        assert tuple(round(value, 4) for value in expected) in colors, ref
    # None is the symbol counter's grey: the slab replaced it.
    assert tuple(round(value, 4) for value in PART_COLORS["counter"]) not in colors


def test_bath2_overhang_meets_the_bonded_bowl_deck(catlin_model_ro):
    top = next(item for item in catlin_model_ro.countertops if item.tag == "CT-M-BATH2-VANITY")
    vanity = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "FX-M-BATH2-SINK")
    prisms = countertop_prisms(catlin_model_ro, top)
    assert prisms
    assert all(prism.z1_m == pytest.approx(vanity.body_z0_m + 36 * INCH) for prism in prisms)
