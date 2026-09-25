"""Placeables join the collision set: the shared body, the IR element, and the two checks."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.checks.structural.placeable_interference import (
    equipment_support,
    placeable_interference,
)
from typehaus.findings import Result, Severity
from typehaus.quantities import inch
from typehaus.resolve.placeable_bodies import body_prism
from typehaus.resolve.solid_categories import solid_category


@pytest.fixture(scope="module")
def model(catlin_model):
    return catlin_model  # module-scoped and mutable: the tests below restore what they move


def _ctx(model):
    return SimpleNamespace(model=model, plan=model.plan)


def _index(model, tag: str) -> int:
    return next(i for i, o in enumerate(model.canvas_objects) if o.tag == tag)


def test_the_equipment_row_is_registered() -> None:
    row = solid_category("equipment")
    assert (row.trade, row.elevation_family, row.collision) == ("mechanical", "body", "hard")


def test_a_body_with_no_height_has_no_prism(model) -> None:
    obj = model.canvas_objects[_index(model, "EQ-M-HP3-OD")]
    prism = body_prism(obj)
    assert prism is not None and prism.z1_m > prism.z0_m
    assert body_prism(replace(obj, body_z1_m=None)) is None


def test_every_bodied_equipment_is_one_ir_element(model) -> None:
    bodied = {o.uid for o in model.canvas_objects
              if o.kind == "Equipment" and body_prism(o) is not None}
    ir = [e.uid for e in model.geometry.of_kind("equipment")]
    assert set(ir) == bodied and len(ir) == len(set(ir))


def test_the_glb_draws_each_equipment_once(model) -> None:
    """The IR carries the body for the drawings; the glTF draws canvas_objects. Not both."""
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    gltf, _blob = emit_gltf_dict(model, "core")
    uids = [n.get("extras", {}).get("uid") for n in gltf["nodes"]]
    for element in model.geometry.of_kind("equipment"):
        assert uids.count(element.uid) <= 1, element.uid


def test_catlin_is_clear_and_carried(model) -> None:
    ctx = _ctx(model)
    for check in (placeable_interference, equipment_support):
        assert [f.result for f in check(ctx)] == [Result.PASS]


def test_a_unit_pushed_into_a_wall_is_an_advisory_fail(model) -> None:
    index = _index(model, "EQ-B-ESS-INV")
    obj = model.canvas_objects[index]
    wall = model.wall(obj.attachment_wall)
    # Detached from its host and dropped onto the wall's own layers.
    ring = [(x, y) for x, y in wall.layers[0].polygon]
    model.canvas_objects[index] = replace(obj, attachment_wall=None, footprint=ring)
    try:
        hits = [f for f in placeable_interference(_ctx(model)) if f.result is Result.FAIL]
    finally:
        model.canvas_objects[index] = obj
    assert any(wall.tag in f.element_tags for f in hits)
    assert all(f.severity is Severity.WARN for f in hits)


def test_a_floating_condenser_fails_and_a_perched_one_is_unknown(model) -> None:
    index = _index(model, "EQ-M-HP3-OD")
    obj = model.canvas_objects[index]
    lift = inch(18).meters
    model.canvas_objects[index] = replace(obj, body_z0_m=obj.body_z0_m + lift,
                                          body_z1_m=obj.body_z1_m + lift)
    try:
        findings = equipment_support(_ctx(model))
    finally:
        model.canvas_objects[index] = obj
    assert [f.result for f in findings if "EQ-M-HP3-OD" in f.element_tags] == [Result.FAIL]
    # Half the footprint slid off the west rail: two quadrants carried is not a verdict.
    x0 = min(x for x, _ in obj.footprint)
    shift = (max(x for x, _ in obj.footprint) - x0) * 0.6
    model.canvas_objects[index] = replace(
        obj, footprint=[(x - shift, y) for x, y in obj.footprint])
    try:
        findings = equipment_support(_ctx(model))
    finally:
        model.canvas_objects[index] = obj
    assert [f.result for f in findings if "EQ-M-HP3-OD" in f.element_tags] == [Result.UNKNOWN]


def test_no_equipment_is_not_applicable(model) -> None:
    empty = SimpleNamespace(model=SimpleNamespace(canvas_objects=[]), plan=model.plan)
    assert [f.result for f in placeable_interference(empty)] == [Result.NOT_APPLICABLE]
    assert [f.result for f in equipment_support(empty)] == [Result.NOT_APPLICABLE]
