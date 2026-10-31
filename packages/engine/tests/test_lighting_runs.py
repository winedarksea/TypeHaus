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


def test_the_surface_channel_is_a_channel_not_a_bar_inside_its_half_inch_square():
    """The channel/tape cross-section (→ resolve/trim_bands.surface_channel_parts) has to stay
    a fitting a person would recognize, inside the half-inch square ``LIGHT_STRIP_*`` names:
    soffit clearance and the cove-offset rule read that nominal, while every emitter and the
    diff adapter sweep these parts (→ resolve/geometry.light_run_section_shells).
    """
    from typehaus.resolve.geometry import LIGHT_STRIP_HEIGHT_M, LIGHT_STRIP_WIDTH_M
    from typehaus.resolve.trim_bands import surface_channel_parts

    parts = dict(surface_channel_parts(LIGHT_STRIP_WIDTH_M, LIGHT_STRIP_HEIGHT_M))
    assert set(parts) == {"back", "base", "lip", "tape"}
    half = LIGHT_STRIP_WIDTH_M / 2.0
    drops = {}
    for key, quad in parts.items():
        assert all(-half - 1e-9 <= across <= half + 1e-9 for across, _drop in quad), key
        top, bottom = min(d for _a, d in quad), max(d for _a, d in quad)
        assert 0.0 <= top < bottom <= LIGHT_STRIP_HEIGHT_M, key
        drops[key] = (bottom, top)

    # The lip only covers part of the opening — a shadow gap is read by what it hides, not
    # by a second full-height wall that would close the trough back up.
    assert drops["lip"][0] < drops["back"][0]
    assert drops["lip"][1] == drops["back"][1] == 0.0
    # The tape sits directly on the base's own top face, and rises above that.
    assert drops["tape"][0] == pytest.approx(drops["base"][1])
    assert drops["tape"][1] < drops["tape"][0]


def test_the_glb_emitter_draws_a_channel_and_tape_for_every_run(two_run_model):
    """``model.light_runs`` reached IFC and the 2D lighting plan but never the GLB — the
    3D model showed nothing where a cove run was authored. One node per run, colored as a
    channel plus its tape rather than one undifferentiated bar.
    """
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.gltf.palette import _color

    gltf, _blob = emit_gltf_dict(two_run_model)
    run_uids = {run.uid for run in two_run_model.light_runs}
    nodes = [node for node in gltf["nodes"] if node["extras"].get("uid") in run_uids]
    assert len(nodes) == len(run_uids), "one node per light run"
    assert all(node["extras"]["trade"] == "electrical" for node in nodes)

    material_colors = {tuple(material["pbrMetallicRoughness"]["baseColorFactor"])
                       for material in gltf["materials"]}
    assert _color("cove_channel") in material_colors
    assert _color("led_tape") in material_colors


def test_a_shadow_gap_bead_is_graded_against_the_framing_above_its_board(catlin_ctx):
    """A 5/8" bead in a 5/8" board stops on the joists and soffit rungs it is fastened to;
    the 1.44" plaster-in channel it replaced ran 0.81" into them (#103)."""
    from typehaus.checks.mep.plaster_in_depth import plaster_in_depth
    from typehaus.findings import Result

    by_run = {f.element_tags[0]: f for f in plaster_in_depth(catlin_ctx)}
    assert set(by_run) == {"LR-M-LIVING-W", "LR-M-LIVING-E", "LR-M-BATH2-TUB-CLG",
                           "LR-S-HALL-GAP"}
    assert all(f.result is Result.PASS for f in by_run.values()), by_run
