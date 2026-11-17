"""The trap is made up of real fittings, clears support/deck geometry and collides."""

from collections import Counter
from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus import inch
from typehaus.checks.mep.air_handler_installation import air_handler_installation
from typehaus.checks.structural.placeable_interference import (
    equipment_support,
    placeable_interference,
)
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import signed_volume
from typehaus.resolve.mep_ports import placed_ports


def _handler(model):
    obj = next(o for o in model.canvas_objects if o.tag == "EQ-S-HP1-AH")
    product = next(p for p in model.plan.library.equipment_types if p.tag == obj.type_ref)
    return obj, product


def _findings(model):
    return air_handler_installation(check_context(model.plan, model))


def _with_spec(model, **changes):
    _, product = _handler(model)
    updated = product.model_copy(update={
        "air_handler_installation": product.air_handler_installation.model_copy(update=changes)})
    library = model.plan.library.model_copy(update={"equipment_types": tuple(
        updated if p.tag == product.tag else p for p in model.plan.library.equipment_types)})
    return replace(model, plan=model.plan.model_copy(update={"library": library}))


def test_catlin_installation_has_dimensional_clearance_and_retains_product_holds(catlin_model_ro):
    findings = _findings(catlin_model_ro)
    assert [f.result.value for f in findings] == ["pass", "unknown"]
    assert "2.34 inches above the deck" in findings[0].message
    assert "do not release fabrication" in findings[1].message
    assert all(f.result.value == "pass" for f in equipment_support(
        check_context(catlin_model_ro.plan, catlin_model_ro)))


def test_installed_parts_are_closed_positive_volume_and_shared_with_viewer(catlin_model_ro):
    obj, product = _handler(catlin_model_ro)
    parts = model_parts("gree-flexx-ultra-24-horizontal",
                        *(v.meters for v in (*product.footprint, product.height)),
                        air_handler_installation=product.air_handler_installation)
    roles = {p.get("role") for p in parts}
    assert {"flexx:emergency-pan-floor", "flexx:emergency-pan-rim", "flexx:support-rail",
            "flexx:pitch-shim", "flexx:primary-trap", "flexx:float-switch",
            "flexx:capped-cleanout", "flexx:downstream-vent", "flexx:drain-union",
            "flexx:secondary-plug"} <= roles
    for part in parts:
        mesh = part["mesh"]
        assert signed_volume(mesh["positions"], mesh["triangles"]) > 0, part.get("role")
        assert all(abs(sum(v * v for v in normal) - 1) < 1e-8 for normal in mesh["normals"])
        edges = Counter()
        for triangle in mesh["triangles"]:
            vertices = [tuple(round(v, 12) for v in mesh["positions"][i]) for i in triangle]
            edges.update(zip(vertices, (*vertices[1:], vertices[0]), strict=True))
        assert all(count == edges[(b, a)] for (a, b), count in edges.items()), part.get("role")
    viewer = next(t for t in canvas_object_types(catlin_model_ro.plan) if t["tag"] == product.tag)
    assert [p["mesh"] for p in parts] == [p["mesh"] for p in viewer["model_parts"]]
    assert len(viewer["plan_strokes"]) >= 4
    # The primary marker follows the pitched product port in all three axes.
    primary = next(p for p in product.ports if p.tag == "condensate_primary")
    marker = next(p for p in parts if p.get("role") == "flexx:condensate_primary")
    assert marker["center"] == pytest.approx(tuple(v.meters for v in primary.position), abs=0.0015)


def test_necks_and_plenum_openings_follow_the_raised_pitched_cabinet(catlin_model_ro):
    ports = {(p.equipment_tag, p.port_tag): p for p in placed_ports(catlin_model_ro)}
    for tag, interface, box_tag, box_interface, endpoint in (
        ("DU-A-HP1-SUP-NECK", "supply", "EQ-A-HP1-SUP-BOX", "inlet", 0),
        ("DU-A-HP1-RET-NECK", "return", "EQ-S-ERV-MIX", "return", -1),
    ):
        duct = next(d for d in catlin_model_ro.ducts if d.tag == tag)
        cabinet = ports[("EQ-S-HP1-AH", interface)]
        plenum = ports[(box_tag, box_interface)]
        assert (*duct.path[endpoint], duct.z_m[endpoint]) == pytest.approx(cabinet.point)
        assert plenum.y_m == pytest.approx(cabinet.y_m)
        assert plenum.z_m == pytest.approx(cabinet.z_m)
        assert any(s.tag == tag + "-CONNECTOR-1" for s in catlin_model_ro.solids)
    drain = next(p for p in catlin_model_ro.pipe_runs if p.tag == "PR-A-COND-HP1")
    assert (*drain.path[0], drain.z_m[0]) == pytest.approx(
        ports[("EQ-S-HP1-AH", "condensate_trap_outlet")].point)
    assert all(z1 >= z2 for z1, z2 in zip(drain.z_m, drain.z_m[1:], strict=False))


def test_the_old_cabinet_height_fails_against_platform_and_deck(catlin_model_ro):
    obj, _ = _handler(catlin_model_ro)
    lower = 3.0625 * M_PER_IN
    objects = [replace(o, z_m=o.z_m - lower, body_z0_m=o.body_z0_m - lower,
                       body_z1_m=o.body_z1_m - lower) if o.tag == obj.tag else o
               for o in catlin_model_ro.canvas_objects]
    findings = _findings(replace(catlin_model_ro, canvas_objects=objects))
    assert findings[0].result.value == "fail"
    assert "pan bottom is not seated" in findings[0].message
    assert "below the deck" in findings[0].message


@pytest.mark.parametrize("changes, message", [
    ({"trap_seal_depth": inch(2)}, "trap seal"),
    ({"trap_outlet_drop": inch(1)}, "inlet/outlet drop"),
    ({"vent_rise_above_inlet": inch(1)}, "vent rise"),
    ({"cabinet_slope_in_per_ft": 0}, "cabinet pitch"),
    ({"float_trip_depth": inch(2)}, "float trip level"),
    ({"float_switch_x": inch(30)}, "float travel envelope"),
    ({"pan_width": inch(44)}, "pan does not extend"),
    ({"rail_centers": (inch(0),)}, "support rails"),
    ({"trap_inlet_x": inch(28)}, "declared trap outlet disagrees"),
    ({"feeder_slope_in_per_ft": 0}, "feeder slope"),
    ({"primary_elbow_offset": inch(1.5)}, "adapter to first 90 is 1.5 in"),
])
def test_shortcuts_do_not_pass_installation_checks(catlin_model_ro, changes, message):
    findings = _findings(_with_spec(catlin_model_ro, **changes))
    assert findings[0].result.value == "fail"
    assert message in findings[0].message


def test_a_disconnected_primary_drain_fails(catlin_model_ro):
    pipes = [replace(p, z_m=tuple(z + M_PER_IN for z in p.z_m))
             if p.tag == "PR-A-COND-HP1" else p for p in catlin_model_ro.pipe_runs]
    findings = _findings(replace(catlin_model_ro, pipe_runs=pipes))
    assert findings[0].result.value == "fail"
    assert "does not start at the drawn trap outlet" in findings[0].message


def test_pan_support_must_exist_in_the_model(catlin_model_ro):
    model = replace(catlin_model_ro, solids=[s for s in catlin_model_ro.solids
                                           if s.tag != "SL-A-HP1-PLATFORM"])
    assert "pan bottom is not seated" in _findings(model)[0].message
    assert any(f.result.value == "fail" and "EQ-S-HP1-AH" in f.element_tags
               for f in equipment_support(check_context(model.plan, model)))


def test_moving_the_trap_under_the_platform_fails(catlin_model_ro):
    model = _with_spec(catlin_model_ro, trap_inlet_x=inch(20))
    findings = _findings(model)
    assert findings[0].result.value == "fail"
    assert "primary trap intersects SL-A-HP1-PLATFORM" in findings[0].message


def test_installed_drain_parts_join_the_collision_set(catlin_model_ro):
    # The mixing box pushed 4" south crosses the feeder and trap but not the cabinet body.
    shift = inch(4).meters
    objects = [replace(o, position=(o.position[0], o.position[1] - shift),
                       footprint=[(x, y - shift) for x, y in o.footprint])
               if o.tag == "EQ-S-ERV-MIX" else o for o in catlin_model_ro.canvas_objects]
    model = replace(catlin_model_ro, canvas_objects=objects)
    messages = [f.message for f in placeable_interference(check_context(model.plan, model))
                if f.result.value == "fail" and "EQ-S-HP1-AH" in f.element_tags]
    assert any("installed primary-trap" in m and "EQ-S-ERV-MIX" in m for m in messages)
    assert not any("EQ-S-HP1-AH's body" in m for m in messages)


def test_an_internal_heat_kit_needs_its_host_body(catlin_model_ro):
    objects = [replace(o, position=(o.position[0] + inch(60).meters, o.position[1]),
                       footprint=[(x + inch(60).meters, y) for x, y in o.footprint])
               if o.tag == "EQ-S-HP1-STRIP" else o for o in catlin_model_ro.canvas_objects]
    model = replace(catlin_model_ro, canvas_objects=objects)
    assert any(f.result.value == "fail" and "EQ-S-HP1-STRIP" in f.element_tags
               for f in equipment_support(check_context(model.plan, model)))
