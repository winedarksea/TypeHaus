"""LightRun → IFC, and the diff parity that one-fixture-per-run exists to protect.

``IfcLightFixture`` is in the diff adapter's *external* read list, unlike conduit's
``IfcCableCarrierSegment``. So a run's IFC shape and its baseline ``DiffElem`` are one
contract, not two: emit two solids per run without projecting them and every round trip
against our own export reports a phantom addition. Both halves are pinned here.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from typehaus.model import (Building, LightRun, Library, LuminaireForm, LuminaireType, Mount,
                            MountKind, PlanModel, Project, Site, Storey, degF, ft, inch, pt)
from typehaus.resolve import resolve

STRIP = LuminaireType(tag="ED-T-LT-STRIP24", name="24V LED strip, 3000K",
                      footprint=(inch(1), inch(1)), height=inch(1),
                      form=LuminaireForm.STRIP, type_mark="E", lamp="LED tape",
                      voltage=24, watts_per_ft=3.0, cct_k=3000, dimmable=True)


def _model(*runs):
    project = Project(
        name="lighting-runs",
        project_uuid=uuid.UUID("00000000-0000-4000-8000-000000001148"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15)),
        building=Building(name="L"))
    plan = PlanModel(
        project=project, library=Library(electrical_device_types=(STRIP,)),
        storeys=(Storey(uid="ST1", tag="main", elevation=ft(0),
                        default_ceiling_height=ft(9)),),
    ).with_elements("main", list(runs))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return model


def _run(tag: str, uid: str, *points, **overrides) -> LightRun:
    fields = dict(uid=uid, tag=tag, type_ref="ED-T-LT-STRIP24", path=tuple(points),
                  mount=Mount(kind=MountKind.CEILING, elevation=ft(9)))
    fields.update(overrides)
    return LightRun(**fields)


@pytest.fixture(scope="module")
def two_run_model():
    return _model(
        _run("LR-M-LIVING-N", "LRM00001AA", pt(ft(2), ft(20)), pt(ft(16), ft(20)),
             circuit="CKT-LT-MAIN", psu_ref="ED-M-LT-PSU",
             controlled_by=("ED-M-LIVING-SW1",)),
        _run("LR-M-LIVING-S", "LRM00002AA", pt(ft(2), ft(4)), pt(ft(16), ft(4)),
             pt(ft(16), ft(12)), psu_ref="ED-M-LT-PSU"),
    )


def test_one_light_fixture_per_run_with_a_lighting_pset(two_run_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    import ifcopenshell.util.element

    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(two_run_model, tmp_path / "runs.ifc")
    f = ifcopenshell.open(str(out))

    fixtures = f.by_type("IfcLightFixture")
    # Exactly one per run — the second run turns a corner and still yields one fixture.
    assert len(fixtures) == 2
    assert {fixture.Name for fixture in fixtures} == {"LR-M-LIVING-N", "LR-M-LIVING-S"}
    assert all(fixture.PredefinedType == "USERDEFINED" for fixture in fixtures)
    assert all(fixture.ObjectType == "LEDSTRIP" for fixture in fixtures)
    assert all(fixture.GlobalId for fixture in fixtures)

    north = next(x for x in fixtures if x.Name == "LR-M-LIVING-N")
    pset = ifcopenshell.util.element.get_psets(north, psets_only=True)["TypeHaus_Lighting"]
    assert pset["length_ft"] == pytest.approx(14.0, abs=1e-6)
    assert pset["watts"] == pytest.approx(42.0, abs=1e-6)  # 14 ft x 3 W/ft
    assert pset["voltage"] == 24
    assert pset["circuit"] == "CKT-LT-MAIN" and pset["psu_ref"] == "ED-M-LT-PSU"
    assert pset["controlled_by"] == "ED-M-LIVING-SW1"


def test_the_baseline_projection_offers_one_diff_elem_per_run(two_run_model):
    from typehaus.diff.ifc_adapter import baseline_elems

    runs = [elem for elem in baseline_elems(two_run_model)
            if elem.ifc_class == "IfcLightFixture"]
    assert len(runs) == len(two_run_model.light_runs) == 2
    assert {elem.tag for elem in runs} == {"LR-M-LIVING-N", "LR-M-LIVING-S"}
    assert all(elem.attrs["type"] == "ED-T-LT-STRIP24" for elem in runs)


def test_a_round_trip_against_our_own_ifc_reports_no_run_changes(two_run_model,
                                                                 tmp_path: Path):
    """The whole point of D3: local and external agree, so nothing phantom shows up."""
    pytest.importorskip("ifcopenshell")

    from typehaus.diff import build_report
    from typehaus.diff.ifc_adapter import baseline_elems, external_elems
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(two_run_model, tmp_path / "runs.ifc")
    report = build_report(baseline_elems(two_run_model), external_elems(out))
    run_tags = {run.tag for run in two_run_model.light_runs}
    assert not [change for change in report.substantive() if change.tag in run_tags]
