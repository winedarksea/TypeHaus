"""Authored track assemblies: product compatibility, electrical ownership, output parity."""

from __future__ import annotations

import math
import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from typehaus.checks.mep.lighting import light_run_psu, lighting_controls as check_controls
from typehaus.checks.mep.lighting_supplies import point_luminaire_psu
from typehaus.library.track_lighting import (
    PUREEDGE_SUPPLY, aim_head_at, magnetic_track_spec, radiant_medium, silo_x10,
    standard_track_spec, track_luminaire,
)
from typehaus.model import (
    Building, Circuit, DeviceKind, ElectricalDevice, ElectricalDeviceType, Library, LightRun,
    LuminaireForm, LuminaireType, Mount, MountKind, PlanModel, Project, Site, Storey,
    TrackHeadSpec, TrackLightingSpec, deg, degF, ft, inch, m, pt,
)
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._track_lighting import (
    head_direction, head_lens, track_dimensions, track_geometry,
)
from typehaus.resolve import resolve
from typehaus.takeoff.lighting import connected_lighting_va, light_run_takeoff, lighting_controls
from typehaus.takeoff.track_lighting import track_lighting_materials


def _head(product=None, **kwargs):
    fields = dict(product=product or radiant_medium(), offset=inch(0), azimuth_degrees=270,
                  tilt_degrees=15, beam_degrees=45)
    fields.update(kwargs)
    return TrackHeadSpec(**fields)


def _model(*, magnetic=True, lights=1, driver=PUREEDGE_SUPPLY, light_changes=None,
           supply_changes=None, tape_ft=0, rotation=0, switch_circuit="CKT"):
    spec = magnetic_track_spec() if magnetic else standard_track_spec()
    product = track_luminaire("TRACK", spec, type_mark="Y")
    switch_type = ElectricalDeviceType(tag="SW-T", name="Toggle",
                                       footprint=(inch(2), inch(2)), height=inch(2))
    elements = [ElectricalDevice(uid="SW1", tag="SW", kind=DeviceKind.SWITCH,
                                  position=pt(m(0), m(0)), type_ref="SW-T",
                                  circuit=switch_circuit)]
    for index in range(lights):
        fields = dict(uid=f"LIGHT{index}", tag=f"LIGHT-{index}", kind=DeviceKind.LIGHT,
                      position=pt(m(3 + index * 2), m(3)), type_ref="TRACK", rotation=deg(rotation),
                      controlled_by=("SW",), psu_ref="PSU" if magnetic else None,
                      circuit=None if magnetic else "CKT",
                      mount=Mount(kind=MountKind.CEILING, drop=product.height))
        fields.update(light_changes or {})
        elements.append(ElectricalDevice(**fields))
    if magnetic:
        fields = dict(uid="PSU1", tag="PSU", kind=DeviceKind.JUNCTION_BOX,
                      position=pt(m(1), m(1)), type_ref=driver.tag, circuit="CKT",
                      controlled_by=("SW",))
        fields.update(supply_changes or {})
        elements.append(ElectricalDevice(**fields))
    strip = LuminaireType(tag="STRIP", name="24V tape", form=LuminaireForm.STRIP,
                          footprint=(inch(1), inch(1)), height=inch(1), voltage=24,
                          watts_per_ft=3)
    if tape_ft:
        elements.append(LightRun(uid="TAPE1", tag="TAPE", type_ref="STRIP", psu_ref="PSU",
                                 path=(pt(ft(0), ft(0)), pt(ft(tape_ft), ft(0))),
                                 controlled_by=("SW",)))
    plan = PlanModel(
        project=Project(name="tracks", project_uuid=uuid.UUID(int=1149), building=Building(name="T"),
                        site=Site(lat=45, lon=-93, elevation=ft(800),
                                  design_temp_heating=degF(-15))),
        library=Library(electrical_device_types=(product, driver, switch_type, strip),
                        circuits=tuple(Circuit(tag=c, panel_ref="P", breaker_amps=15)
                                       for c in ("CKT", "OTHER"))),
        storeys=(Storey(uid="ST1", tag="main", elevation=ft(0), default_ceiling_height=ft(9)),),
    ).with_elements("main", elements)
    return resolve(plan)[0]


def _failures(model, check=point_luminaire_psu):
    return [f for f in check(SimpleNamespace(plan=model.plan, model=model))
            if f.result.value == "fail"]


@pytest.mark.parametrize("factory,watts,lumens,volts", [
    (magnetic_track_spec, 22, 1320, 24), (standard_track_spec, 20, 1580, 120),
])
def test_catalog_configuration_round_trips_without_losing_subclass_fields(factory, watts, lumens, volts):
    product = track_luminaire("TRACK", factory())
    library = Library(electrical_device_types=(product,))
    restored = Library.model_validate_json(library.model_dump_json()).electrical_device_types[0]
    assert isinstance(restored, LuminaireType)
    assert restored.track_lighting == product.track_lighting
    assert (restored.watts, restored.lumens, restored.voltage) == (watts, lumens, volts)
    assert restored.track_lighting.head_count == 2
    device = ElectricalDevice(uid="D", tag="D", kind=DeviceKind.LIGHT, position=pt(m(1), m(1)),
                              psu_ref="PSU", controlled_by=("SW",))
    assert ElectricalDevice.model_validate_json(device.model_dump_json()) == device


@pytest.mark.parametrize("changes", [
    {"rail_length": inch(49)}, {"rail_length": inch(-1)}, {"rail_width": m(float("nan"))},
    {"feed_height": m(float("inf"))}, {"feed_system": "h_track_120v"},
    {"heads": ()}, {"heads": (_head(offset=inch(17)),)},
    {"heads": (_head(offset=inch(0)), _head(offset=inch(1)))},
    {"heads": (_head(silo_x10(), beam_degrees=35),)},
])
def test_invalid_rail_or_component_configuration_is_rejected(changes):
    fields = magnetic_track_spec().model_dump()
    fields.update(changes)
    with pytest.raises(ValidationError):
        TrackLightingSpec.model_validate(fields)


@pytest.mark.parametrize("changes", [
    {"tilt_degrees": 91}, {"azimuth_degrees": float("nan")}, {"offset": m(float("inf"))},
    {"beam_degrees": 44}, {"product": silo_x10(), "azimuth_degrees": 355, "beam_degrees": 35},
])
def test_manufacturer_aiming_and_optic_limits_are_enforced(changes):
    with pytest.raises(ValidationError):
        _head(**changes)


def test_aiming_uses_the_modeled_lens_and_changes_actual_assembly_bounds():
    base = magnetic_track_spec(heads=(_head(offset=inch(-8), tilt_degrees=0),))
    target = (inch(-8).meters, inch(-36).meters, inch(-72).meters)
    aimed = aim_head_at(base, base.heads[0], target)
    spec = magnetic_track_spec(heads=(aimed,))
    lens, direction = head_lens(spec, aimed), head_direction(aimed)
    distance = math.dist(lens, target)
    assert tuple(lens[i] + direction[i] * distance for i in range(3)) == pytest.approx(target)
    assert track_dimensions(spec) != track_dimensions(base)
    with pytest.raises(ValueError, match="below"):
        aim_head_at(base, base.heads[0], (0, 0, 1))


def test_asymmetric_end_feed_bounds_keep_the_rail_midpoint_as_anchor():
    product = track_luminaire("TRACK", magnetic_track_spec())
    assert product.footprint[0].inches == pytest.approx(39)
    assert min(p.x.inches for p in product.footprint_shape.points) == pytest.approx(-21)
    assert max(p.x.inches for p in product.footprint_shape.points) == pytest.approx(18)
    for width in (m(float("nan")), inch(42)):
        fields = product.model_dump()
        fields["footprint"] = (width, product.footprint[1])
        with pytest.raises(ValidationError, match="dimensions"):
            LuminaireType.model_validate(fields)


@pytest.mark.parametrize("magnetic,expected", [(True, 40), (False, 20)])
def test_branch_counts_supply_or_integral_drivers_once(magnetic, expected):
    model = _model(magnetic=magnetic)
    assert not _failures(model)
    assert connected_lighting_va(model)["total_connected_va"] == expected
    row = lighting_controls(model)[0]
    assert row["circuit"] == "CKT" and row["controls"] == ["toggle"]


@pytest.mark.parametrize("kwargs", [
    {"light_changes": {"psu_ref": None}}, {"light_changes": {"psu_ref": "MISSING"}},
    {"driver": PUREEDGE_SUPPLY.model_copy(update={"output_voltage": 12})},
    {"supply_changes": {"circuit": None}}, {"supply_changes": {"controlled_by": ()}},
    {"light_changes": {"circuit": "CKT"}},
    {"supply_changes": {"kind": DeviceKind.RECEPTACLE}},
    {"magnetic": False, "light_changes": {"psu_ref": "PSU"}},
])
def test_missing_incompatible_and_ambiguous_supplies_fail(kwargs):
    assert _failures(_model(**kwargs))


def test_supply_demand_combines_points_and_tape_before_sizing():
    model = _model(tape_ft=2)
    assert not _failures(model) and not _failures(model, light_run_psu)
    supply = light_run_takeoff(model)["supplies"][0]
    assert supply["connected_watts"] == 28 and supply["required_watts"] == 35
    assert supply["fixtures"] == ["LIGHT-0"] and supply["runs"] == ["TAPE"]
    assert connected_lighting_va(model)["total_connected_va"] == 40
    assert _failures(_model(lights=2))
    assert _failures(_model(tape_ft=8), light_run_psu)


def test_switch_reporting_and_validation_use_the_supply_branch():
    model = _model(switch_circuit="OTHER")
    assert _failures(model, check_controls)
    assert lighting_controls(model)[0]["cross_circuit"] == ["SW"]


def test_component_order_sheet_distinguishes_stock_from_installed_rail():
    rows = track_lighting_materials(_model())
    assert {r["item"]: r["quantity"] for r in rows} == {
        "rail_stock": 1, "end_feed": 1, "head": 2, "supply": 1}
    rail = rows[0]
    assert rail["stock_length_in"] == 48 and rail["installed_length_in"] == 36
    assert all(r["pricing"] == "quote_required" for r in rows)


def test_field_optics_preserve_known_photometry_and_order_required_replacement_lenses():
    h_track = standard_track_spec(heads=(_head(silo_x10(), beam_degrees=25),))
    assert track_luminaire("H25", h_track).lumens == 790
    magnetic = magnetic_track_spec(heads=(_head(beam_degrees=20),))
    product = track_luminaire("TRACK", magnetic)
    assert product.lumens is None
    model = _model()
    library = model.plan.library.model_copy(update={"electrical_device_types": (
        product, *model.plan.library.electrical_device_types[1:])})
    model.plan = model.plan.model_copy(update={"library": library})
    optic = next(r for r in track_lighting_materials(model) if r["item"] == "optic")
    assert optic["product"] == "PROD-PUREEDGE-LEN-RADM-SP-SW" and optic["quantity"] == 1


@pytest.mark.parametrize("rotation", [0, 90, 37])
def test_configured_plan_canvas_glb_and_ifc_share_rotated_geometry(rotation, tmp_path):
    from typehaus.diff.ifc_adapter import baseline_elems, external_elems
    from typehaus.emit.draw.lightingplan import build_lighting_plan
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.ifc.emitter import emit_ifc

    model = _model(rotation=rotation)
    product = model.plan.library.electrical_device_types[0]
    strokes, parts = track_geometry(product.track_lighting)
    canvas = next(t for t in canvas_object_types(model.plan) if t["tag"] == "TRACK")
    assert len(canvas["model_parts"]) == len(parts) == 12
    item = next(c for c in model.canvas_objects if c.tag == "LIGHT-0")
    plan = [n for n in build_lighting_plan(model, "main").nodes
            if getattr(n, "tag", None) == item.tag]
    assert plan[0].points == pytest.approx([
        (x / 0.0254, y / 0.0254) for x, y in place_local(strokes[0]["points"], item.position, rotation)])
    gltf, _ = emit_gltf_dict(model)
    assert any(n.get("extras", {}).get("uid") == item.uid for n in gltf["nodes"])
    path = emit_ifc(model, tmp_path / "track.ifc")
    local = next(e for e in baseline_elems(model) if e.tag == item.tag)
    exported = next(e for e in external_elems(path) if e.global_id == local.global_id)
    assert exported.centroid == pytest.approx(local.centroid, abs=1e-6)
    assert exported.bbox == pytest.approx(local.bbox, abs=1e-6)
    node = next(n for n in gltf["nodes"] if n.get("extras", {}).get("uid") == item.uid)
    accessors = [gltf["accessors"][p["attributes"]["POSITION"]]
                 for p in gltf["meshes"][node["mesh"]]["primitives"]]
    low = [min(a["min"][i] for a in accessors) for i in range(3)]
    high = [max(a["max"][i] for a in accessors) for i in range(3)]
    assert tuple(high[i] - low[i] for i in (0, 2, 1)) == pytest.approx(local.bbox, abs=1e-6)
