"""Lighting schema contracts: LuminaireType survives the library, LightRun resolves.

The subclass round trip is the load-bearing one. ``LuminaireType`` rides in
``Library.electrical_device_types``, a tuple typed as its *parent* — if pydantic ever
down-cast on validation, every photometric silently vanishes and the E-602 schedule
would print blanks with nothing failing. Pinned here rather than discovered on a sheet.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.model import (Building, ElectricalDevice, ElectricalDeviceType, DeviceKind,
                            LightRun, Library, LuminaireForm, LuminaireType, Mount,
                            MountKind, PlanModel, Project, Site, Storey, degF, ft, inch, pt)
from typehaus.resolve import resolve


def _luminaire(**overrides) -> LuminaireType:
    fields = dict(tag="ED-T-LT-CAN4", name='4" recessed can', footprint=(inch(4), inch(4)),
                  height=inch(6), form=LuminaireForm.RECESSED_CAN, type_mark="A",
                  lamp="LED integrated", watts=10.5, lumens=800.0, cct_k=3000, cri=90,
                  dimmable=True, load_va=10.5, plan_symbol="recessed-can")
    fields.update(overrides)
    return LuminaireType(**fields)


def test_luminaire_type_keeps_its_subclass_fields_inside_the_library():
    product = _luminaire()
    library = Library(electrical_device_types=(product,))

    stored = library.electrical_device_types[0]
    assert isinstance(stored, LuminaireType)
    assert stored.form is LuminaireForm.RECESSED_CAN
    assert (stored.type_mark, stored.watts, stored.lumens, stored.cct_k) == ("A", 10.5, 800.0, 3000)
    assert stored.dimmable and not stored.wet_rated


def test_luminaire_defaults_are_the_conservative_ones():
    bare = LuminaireType(tag="ED-T-LT-X", name="unrated fixture", footprint=(inch(4), inch(4)),
                         height=inch(4), form=LuminaireForm.PENDANT)
    assert bare.voltage == 120
    assert not (bare.dimmable or bare.damp_rated or bare.wet_rated or bare.integral_switch)
    assert bare.watts is None and bare.watts_per_ft is None and bare.type_mark is None


def test_electrical_device_type_carries_a_control_attribute():
    plain = ElectricalDeviceType(tag="ED-T-SWITCH", name="Wall switch",
                                 footprint=(inch(4), inch(2)), height=inch(2))
    dimmer = ElectricalDeviceType(tag="ED-T-SWITCH-DIM", name="Dimmer",
                                  footprint=(inch(4), inch(2)), height=inch(2),
                                  control="dimmer")
    assert plain.control is None and dimmer.control == "dimmer"


def test_controlled_by_round_trips_on_a_device():
    light = ElectricalDevice(uid="D1", tag="ED-M-LIVING-LT1", kind=DeviceKind.LIGHT,
                             position=pt(ft(4), ft(4)), type_ref="ED-T-LT-CAN4",
                             controlled_by=("ED-M-LIVING-SW1", "ED-M-LIVING-SW2"))
    assert light.controlled_by == ("ED-M-LIVING-SW1", "ED-M-LIVING-SW2")
    assert ElectricalDevice(uid="D2", tag="ED-X", kind=DeviceKind.LIGHT,
                            position=pt(ft(0), ft(0))).controlled_by == ()


def _plan(*elements) -> PlanModel:
    strip = _luminaire(tag="ED-T-LT-STRIP24", name="24V LED strip", form=LuminaireForm.STRIP,
                       type_mark="E", voltage=24, watts=None, watts_per_ft=3.0,
                       plan_symbol=None)
    project = Project(
        name="lighting", project_uuid=uuid.UUID("00000000-0000-4000-8000-000000001147"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15)),
        building=Building(name="L"))
    return PlanModel(
        project=project,
        library=Library(electrical_device_types=(strip, _luminaire())),
        storeys=(Storey(uid="ST1", tag="main", elevation=ft(0), default_ceiling_height=ft(9)),),
    ).with_elements("main", list(elements))


def _run(**overrides) -> LightRun:
    fields = dict(uid="LR000000AA", tag="LR-M-LIVING-N", type_ref="ED-T-LT-STRIP24",
                  path=(pt(ft(0), ft(0)), pt(ft(12), ft(0)), pt(ft(12), ft(9))),
                  mount=Mount(kind=MountKind.CEILING, elevation=ft(9)))
    fields.update(overrides)
    return LightRun(**fields)


def test_light_run_resolves_to_its_plan_length_at_its_mounted_height():
    model, findings = resolve(_plan(_run(circuit="CKT-LT-MAIN", psu_ref="ED-M-LT-PSU",
                                         controlled_by=("ED-M-LIVING-SW1",))))
    assert not [f for f in findings if f.severity.value == "error"]

    assert len(model.light_runs) == 1
    run = model.light_runs[0]
    assert run.tag == "LR-M-LIVING-N" and run.storey == "main"
    assert run.length_m == pytest.approx(ft(21).meters)  # 12' + 9'
    assert run.z_m == pytest.approx(ft(9).meters)
    assert run.psu_ref == "ED-M-LT-PSU" and run.controlled_by == ("ED-M-LIVING-SW1",)


def test_light_run_with_one_point_is_an_integrity_error():
    _model, findings = resolve(_plan(_run(path=(pt(ft(0), ft(0)),))))
    assert any(f.check_id == "integrity.light_run_path" and f.severity.value == "error"
               for f in findings)


def test_light_run_naming_a_point_fixture_type_is_an_integrity_error():
    """A run priced per foot must not point at a per-fixture wattage."""
    _model, findings = resolve(_plan(_run(type_ref="ED-T-LT-CAN4")))
    assert any(f.check_id == "integrity.light_run_type" and f.severity.value == "error"
               for f in findings)


def test_light_run_naming_an_unknown_type_is_an_integrity_error():
    _model, findings = resolve(_plan(_run(type_ref="ED-T-NOPE")))
    assert any(f.check_id == "integrity.light_run_type" and f.severity.value == "error"
               for f in findings)


def test_light_run_is_not_a_placeable():
    """It has no footprint to place, rotate or keep clear — like ConduitRun."""
    from typehaus.model.canvas import canvas_objects

    model = _plan(_run())
    assert not [item for item in canvas_objects(model) if item["kind"] == "LightRun"]
