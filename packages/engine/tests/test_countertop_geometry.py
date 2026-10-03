"""One countertop slab shape across the live payload and the GLB (→ geometry_countertops)."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.emit.gltf.emitter import emit_gltf_dict
from typehaus.emit.gltf.palette import _material_finish_color, authored_colors
from typehaus.model.placeable_symbols import PART_COLORS
from typehaus.resolve.geometry_countertops import countertop_prisms, slab_hosts
from typehaus.server.model_json import model_to_dict

INCH = 0.0254


def test_the_bar_top_draws_its_whole_cantilever_at_the_counter(catlin_model_ro):
    top = next(item for item in catlin_model_ro.countertops
               if item.tag == "CT-M-KIT-PENINSULA-BAR")
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    prisms = countertop_prisms(catlin_model_ro, top)
    assert len(prisms) == 1
    (prism,) = prisms
    assert Polygon(prism.ring).equals_exact(Polygon(top.outline), 1e-9)
    assert Polygon(prism.ring).area == pytest.approx(122.5 * 11.625 * INCH * INCH)
    assert prism.z1_m == pytest.approx(max(objects[tag].body_z1_m for tag in top.hosts))
    assert prism.z1_m - prism.z0_m == pytest.approx(top.thickness_m)


def test_a_sink_base_keeps_its_own_counter(catlin_model_ro):
    top = next(item for item in catlin_model_ro.countertops if item.tag == "CT-M-KIT-N")
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    sink = Polygon(objects["FURN-M-KIT-SINKBASE"].footprint)
    slab = Polygon(top.outline)
    drawn = sum(Polygon(prism.ring).area for prism in countertop_prisms(catlin_model_ro, top))
    assert drawn == pytest.approx(slab.difference(sink).area, rel=1e-6)
    hosted = slab_hosts(catlin_model_ro)
    assert "FURN-M-KIT-SINKBASE" not in hosted
    assert hosted["FURN-M-KIT-PEN-B24-W"] == "CT-M-KIT-PENINSULA"


def test_hosted_cabinets_drop_their_symbol_counter_in_model_json(catlin_model_ro):
    payload = model_to_dict(catlin_model_ro)
    objects = {item["tag"]: item for item in payload["canvas_objects"]}
    assert objects["FURN-M-KIT-PEN-B24-W"]["countertop_ref"] == "CT-M-KIT-PENINSULA"
    assert objects["FURN-M-KIT-SINKBASE"]["countertop_ref"] is None
    types = {item["tag"]: item for item in payload["catalog"]["canvas_object_types"]}
    for type_ref in ("SEKT-B24", "SEKT-SINK-B36"):
        roles = [part.get("role") for part in types[type_ref]["model_parts"]]
        assert "counter" in roles, type_ref

    rows = {row["tag"]: row for row in payload["countertops"]}
    bar = rows["CT-M-KIT-PENINSULA-BAR"]
    assert bar["material_ref"] == "oak-counter"
    assert bar["host_uid"] == objects["FURN-M-KIT-PEN-END"]["uid"]
    assert bar["z1_m"] - bar["z0_m"] == pytest.approx(1.1875 * INCH)
    assert Polygon(bar["parts"][0]["outline"]).area == pytest.approx(
        122.5 * 11.625 * INCH * INCH)
    assert {rows[tag]["material_ref"] for tag in ("CT-M-LIV-E-S", "CT-M-LIV-E-N")} == {
        "live-edge-white-oak"}


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
    for ref in ("oak-counter", "live-edge-white-oak", "quartz-counter"):
        expected = _material_finish_color(ref, "millwork", authored)
        assert tuple(round(value, 4) for value in expected) in colors, ref
    # None is the symbol counter's grey: the slab replaced it.
    assert tuple(round(value, 4) for value in PART_COLORS["counter"]) not in colors
