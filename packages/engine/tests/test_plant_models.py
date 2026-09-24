"""Procedural plant models: deterministic, bounded, budgeted, on the ground, instanced."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import pytest

from typehaus import PlantType, inch
from typehaus.resolve.plant_forms import TRIANGLE_BUDGET
from typehaus.resolve.plant_models import (
    ROLES,
    build_espalier,
    build_prototype,
    role_colors,
)
from typehaus.resolve.rain_garden import floor_z_m, surface_z_m

_FORMS = ("grass", "perennial", "groundcover", "shrub", "tree")


def _ptype(form: str, **extra) -> PlantType:
    return PlantType(tag=f"PT-{form.upper()}", botanical_name="Testus", form=form,
                     mature_height=inch(24), mature_spread=inch(18),
                     foliage_material="foliage", **extra)


def _digest(proto) -> str:
    return hashlib.sha256(repr(proto.parts).encode()).hexdigest()


def test_same_seed_same_prototype() -> None:
    for form in _FORMS:
        assert _digest(build_prototype(_ptype(form), 1)) == _digest(
            build_prototype(_ptype(form), 1))
    assert _digest(build_prototype(_ptype("grass"), 0)) != _digest(
        build_prototype(_ptype("grass"), 1))


def test_prototypes_ignore_the_hash_seed() -> None:
    """``hash()`` is salted per process; a prototype built off it would drift run to run."""
    code = ("import hashlib;from typehaus import PlantType, inch;"
            "from typehaus.resolve.plant_models import build_prototype;"
            "p=build_prototype(PlantType(tag='PT-GRASS',botanical_name='Testus',form='grass',"
            "mature_height=inch(24),mature_spread=inch(18),foliage_material='foliage'),2);"
            "print(hashlib.sha256(repr(p.parts).encode()).hexdigest())")
    digests = {
        subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                       env={**os.environ, "PYTHONHASHSEED": seed}).stdout.strip()
        for seed in ("1", "2")
    }
    assert digests == {_digest(build_prototype(_ptype("grass"), 2))}


@pytest.mark.parametrize("form", _FORMS)
@pytest.mark.parametrize("bloom", [False, True])
def test_unit_bounds_and_triangle_budget(form: str, bloom: bool) -> None:
    extra = {"bloom_material": "b", "fruit_material": "f"} if bloom else {}
    for k in range(3):
        proto = build_prototype(_ptype(form, **extra), k)
        points = [p for part in proto.parts for p in part.positions]
        assert points
        assert all(x * x + y * y <= 0.25 + 1e-3 for x, y, _ in points)
        assert all(-1e-9 <= z <= 1.0 + 1e-9 for _, _, z in points)
        assert max(z for _, _, z in points) == pytest.approx(1.0, abs=1e-3)
        assert 100 <= proto.triangle_count <= TRIANGLE_BUDGET[form], proto.triangle_count
        assert {part.role for part in proto.parts} <= set(ROLES)


def test_normals_are_unit() -> None:
    for part in build_prototype(_ptype("shrub"), 0).parts:
        for n in part.normals:
            assert sum(c * c for c in n) == pytest.approx(1.0, abs=1e-6)


def test_espalier_cordons_ride_the_wires() -> None:
    wires = (0.4572, 0.9144, 1.3716, 1.8288)
    spread, height, thickness = 1.8288, 2.1336, 6 * 0.0254
    proto = build_espalier("X", "PT-X", spread_m=spread, height_m=height,
                           wire_heights_m=wires, thickness_m=thickness, has_fruit=True)
    assert proto.triangle_count <= TRIANGLE_BUDGET["espalier"]
    points = [p for part in proto.parts for p in part.positions]
    assert all(abs(x) <= spread / 2 + 1e-9 and abs(y) <= thickness / 2 + 1e-9
               and 0.0 <= z <= height + 1e-9 for x, y, z in points)
    stems = [p for part in proto.parts if part.role == "stem" for p in part.positions]
    for wire in wires:
        # Both arms reach out along the wire, at the wire.
        for side in (-1, 1):
            arm = [z for x, _, z in stems if side * x > 0.8 * spread / 2]
            assert any(abs(z - wire) <= 0.02 for z in arm), wire
    assert any(part.role == "fruit" for part in proto.parts)


def test_catlin_prototypes_and_colours(catlin_model_ro) -> None:
    model = catlin_model_ro
    types = {t.tag: t for t in model.plan.library.plant_types}
    materials = {m.tag: m for m in model.plan.library.materials}
    for proto in model.plant_models.values():
        assert proto.triangle_count <= TRIANGLE_BUDGET[proto.form]
        colors = role_colors(types[proto.type_ref], materials)
        for part in proto.parts:
            assert colors[part.role].startswith("#") and len(colors[part.role]) == 7
    for ptype in types.values():
        for role in ROLES:
            ref = getattr(ptype, f"{role}_material")
            assert not ref or ref in materials
    assert {types["PT-MAL-HONEYCRISP"].fruit_material,
            types["PT-COR-MOONBEAM"].bloom_material} <= set(materials)
    solids = {s.uid for s in model.solids if s.category == "plant"}
    assert len(model.plants) == 563
    assert {p.uid for p in model.plants} == solids
    assert all(p.model_ref in model.plant_models for p in model.plants)
    espaliers = [p for p in model.plants if p.training == "espalier"]
    assert len(espaliers) == 3 and all(p.model_ref.startswith("espalier:") for p in espaliers)


def test_basin_plants_stand_on_the_basin(catlin_model_ro) -> None:
    model = catlin_model_ro
    basin = model.plan.by_tag("RG-W-BASIN")
    rim, floor = basin.rim_elevation.meters, floor_z_m(basin)
    slope = [p for p in model.plants if p.source_ref in ("PB-RG-SLOPE-W", "PB-RG-SLOPE-E")]
    assert slope
    for plant in slope:
        assert floor - 1e-9 <= plant.ground_z_m <= rim + 1e-9
        assert plant.ground_z_m == pytest.approx(surface_z_m(basin, *plant.position))
    # A slope is a slope: the slope beds are not one flat elevation any more.
    assert len({round(p.ground_z_m, 4) for p in slope}) > 1
    bed_floor = [p for p in model.plants if p.source_ref == "PB-RG-FLOOR"]
    assert all(p.ground_z_m == pytest.approx(floor) for p in bed_floor)
    solids = {s.uid: s for s in model.solids}
    assert all(solids[p.uid].z0_m == pytest.approx(p.ground_z_m) for p in slope)


def test_model_json_plants_block_budget(catlin_model_ro) -> None:
    from typehaus.server.model_json_plants import plants_json

    block = plants_json(catlin_model_ro)
    assert len(block["plants"]) == 563
    assert len(block["plant_models"]) == len(catlin_model_ro.plant_models)
    # Budget the parts: prototypes are fixed per type, instances scale with the beds
    # (~195 KB and ~247 B each at 564 plants).
    size = lambda o: len(json.dumps(o, separators=(",", ":")))  # noqa: E731
    assert size(block["plant_models"]) < 250_000
    assert size(block["plants"]) / len(block["plants"]) < 300


def test_glb_instances_share_meshes(catlin_model_ro) -> None:
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    gltf, _ = emit_gltf_dict(catlin_model_ro)
    plant_uids = {p.uid for p in catlin_model_ro.plants}
    instances = [n for n in gltf["nodes"] if "translation" in n]
    assert len(instances) == 563
    assert {n["extras"]["uid"] for n in instances} == plant_uids
    assert all(n["extras"]["kind"] == "solid" for n in instances)
    shared = {n["mesh"] for n in instances}
    assert len(shared) == len(catlin_model_ro.plant_models)
    for index in shared:
        for primitive in gltf["meshes"][index]["primitives"]:
            material = gltf["materials"][primitive["material"]]
            assert material["alphaMode"] == "OPAQUE" and material["doubleSided"] is False
            assert "indices" in primitive and "NORMAL" in primitive["attributes"]
    # No plant draws twice: its prism is not emitted alongside its instance.
    prisms = [n for n in gltf["nodes"] if "translation" not in n
              and n.get("extras", {}).get("uid") in plant_uids]
    assert prisms == []
