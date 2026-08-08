"""``PipeAccessory`` — the in-line supply devices, and how they find their host run.

Until this element existed the model had no way to say "there is a valve here". The
hydrant check said so out loud: ``mep.hydrant_freeze_depth`` reported the shutoff and the
vacuum breaker as UNKNOWN because "the model has no valve or backflow-preventer element"
(``notes/garage_hydrant.md``). Everything a supply system is actually judged on — a main
shutoff you can reach, backflow protection at a hose bib, an arrestor at a quick-closing
valve — was prose.

The resolver's one interesting behaviour is the elevation fallback: an accessory *is on* a
pipe, so its default z is the host run's invert at the nearest vertex rather than a number
the author has to copy and keep in step by hand.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.model.enums import PipeAccessoryKind, PipeSystem
from typehaus.model.mep import PipeAccessory, PipeRun
from typehaus.quantities import ft, inch, pt
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_M_TO_FT = 3.280839895


@pytest.fixture(scope="module")
def catlin_plan():
    return load_plan(CATLIN_DIR).plan


def _plan_with(catlin_plan, *elements, storey: str = "basement"):
    """The Catlin plan with extra elements spliced onto a storey.

    Same trick ``test_drainage_elements.py`` uses, and for the same reason: an accessory
    resolves against a real ``PipeRun`` on a real storey datum, and a synthetic two-wall
    fixture would have neither.
    """
    return catlin_plan.with_elements(
        storey, (*catlin_plan.storey_elements(storey), *elements))


def _errors(findings):
    return [f for f in findings if f.severity.value == "error"]


def test_an_accessory_takes_its_elevation_from_the_run_it_sits_on(catlin_plan):
    """The whole point of the fallback: a shutoff on the cold trunk is at the trunk's
    invert, and nobody should have to re-type ``ft(8, 1.2)`` to say so."""
    valve = PipeAccessory(
        uid="TSTPA00001", tag="PA-TEST-SHUTOFF", kind=PipeAccessoryKind.SHUTOFF,
        position=pt(ft(8), ft(16)), pipe_ref="PR-B-CW-TRUNK")
    model, findings = resolve(_plan_with(catlin_plan, valve))
    assert not _errors(findings)

    resolved = next(a for a in model.pipe_accessories if a.tag == "PA-TEST-SHUTOFF")
    trunk = next(r for r in model.pipe_runs if r.tag == "PR-B-CW-TRUNK")
    vertex = trunk.path.index((ft(8).meters, ft(16).meters))
    assert resolved.z_m == pytest.approx(trunk.z_m[vertex])
    # And it inherits the run's identity, so a schedule row never has to re-find the pipe.
    assert resolved.system == "water_cold"
    assert resolved.diameter_m == pytest.approx(trunk.diameter_m)


def test_an_authored_elevation_is_storey_relative_like_every_other_authored_z(catlin_plan):
    valve = PipeAccessory(
        uid="TSTPA00002", tag="PA-TEST-HIGH", kind=PipeAccessoryKind.SHUTOFF,
        position=pt(ft(8), ft(16)), pipe_ref="PR-B-CW-TRUNK", elevation=ft(6))
    model, findings = resolve(_plan_with(catlin_plan, valve))
    assert not _errors(findings)
    resolved = next(a for a in model.pipe_accessories if a.tag == "PA-TEST-HIGH")
    basement = next(s for s in catlin_plan.storeys if s.tag == "basement")
    assert resolved.z_m == pytest.approx(basement.elevation.meters + ft(6).meters)


def test_an_accessory_with_no_host_run_is_a_hard_error(catlin_plan):
    """A valve floating in space bills, schedules and exports as real while protecting
    nothing — which is worse than a missing one, because it reads as done."""
    valve = PipeAccessory(
        uid="TSTPA00003", tag="PA-TEST-ORPHAN", kind=PipeAccessoryKind.BACKFLOW_PREVENTER,
        position=pt(ft(8), ft(16)), pipe_ref="PR-NO-SUCH-RUN")
    _, findings = resolve(_plan_with(catlin_plan, valve))
    errors = _errors(findings)
    assert [f.check_id for f in errors] == ["integrity.pipe_accessory_host"]


def test_an_accessory_draws_a_solid_named_for_the_device_not_the_family(catlin_plan):
    """A solid's category is what every consumer *labels* it with — the 3D inspector's
    heading, the ``structural_solids`` rollup, the palette. One "pipe_accessory" for the lot
    told a reader nothing: it is equally true of a shutoff, a backflow preventer and a can of
    foam. So the category is the kind."""
    from typehaus.emit.trades import PIPE_ACCESSORY_CATEGORIES, solid_trade

    valve = PipeAccessory(
        uid="TSTPA00004", tag="PA-TEST-SOLID", kind=PipeAccessoryKind.MAIN_SHUTOFF,
        position=pt(ft(8), ft(16)), pipe_ref="PR-B-CW-TRUNK", accessible=True)
    model, _ = resolve(_plan_with(catlin_plan, valve))
    solid = next(s for s in model.solids if s.tag == "PA-TEST-SOLID")
    assert solid.category == "main_shutoff"
    assert solid.category in PIPE_ACCESSORY_CATEGORIES
    assert solid_trade(solid.category) == "plumbing"
    # Centred on the pipe, not sitting on top of it: half the box is above the invert.
    resolved = next(a for a in model.pipe_accessories if a.tag == "PA-TEST-SOLID")
    assert solid.z0_m < resolved.z_m < solid.z1_m
    assert (solid.z1_m - solid.z0_m) == pytest.approx(inch(6).meters)


def test_the_install_kit_rides_the_accessory_not_the_catalog(catlin_plan):
    """A gasket, a bracket and a can of foam are properties of *this* penetration, not of
    the hydrant type — the same hydrant through a different wall takes a different kit."""
    seal = PipeAccessory(
        uid="TSTPA00005", tag="PA-TEST-SEAL", kind=PipeAccessoryKind.PENETRATION_SEAL,
        position=pt(ft(8), ft(16)), pipe_ref="PR-B-CW-TRUNK",
        install_parts=("silicone gasket", "plastic mounting bracket",
                       "closed-cell spray foam"))
    model, _ = resolve(_plan_with(catlin_plan, seal))
    resolved = next(a for a in model.pipe_accessories if a.tag == "PA-TEST-SEAL")
    assert len(resolved.install_parts) == 3
    solid = next(s for s in model.solids if s.tag == "PA-TEST-SEAL")
    assert solid.category == "penetration_seal", \
        "a seal is not a valve and must not be labelled as one"


def test_an_appliances_install_kit_bills_in_the_same_section(catlin_plan):
    """``install_parts`` is a shape of order, not a property of pipework.

    The disposer's 24V control loop — transformer, contactor, enclosure, buttons, cable —
    is seven part numbers with no route anyone has designed. Drawing conduit for it would
    invent geometry; counting it is the true statement, and the section that already exists
    for exactly this (the hydrant kits) is where it belongs. One takeoff, two carriers.
    """
    from typehaus.takeoff.plumbing_specialties import install_parts_takeoff

    model, _ = resolve(catlin_plan)
    rows = {row["part"]: row for row in install_parts_takeoff(model)}

    disposer = next(element for element in model.plan.storey_elements("main")
                    if getattr(element, "tag", None) == "APPL-M-DISP")
    assert len(disposer.install_parts) == 7
    for part in disposer.install_parts:
        assert rows[part]["count"] == 1
        assert rows[part]["tags"] == ["APPL-M-DISP"]

    # The pipe-accessory kits are untouched and still carry their own tags: the two
    # carriers share a section, not a count.
    hydrant_kit = rows["silicone gasket, hydrant escutcheon"]
    assert hydrant_kit["count"] == 2
    assert "APPL-M-DISP" not in hydrant_kit["tags"]


def test_pipe_runs_carry_a_finish_and_an_insulation_spec(catlin_plan):
    """Two fields, not one: copper is the pipe and lacquer is a coating on it, and a run
    can have either without the other."""
    run = PipeRun(
        uid="TSTPR00001", tag="PR-TEST-CU", system=PipeSystem.WATER_HOT,
        path=(pt(ft(20), ft(4)), pt(ft(24), ft(4))), diameter=inch(0.75),
        elevations=(ft(8), ft(8)), material="copper", finish="lacquered",
        insulation='1" fiberglass, ASJ')
    model, findings = resolve(_plan_with(catlin_plan, run))
    assert not _errors(findings)
    resolved = next(r for r in model.pipe_runs if r.tag == "PR-TEST-CU")
    assert (resolved.material, resolved.finish) == ("copper", "lacquered")
    assert resolved.insulation == '1" fiberglass, ASJ'


def test_a_bare_run_still_resolves_with_both_fields_unset(catlin_plan):
    """Both fields are optional: the drain and vent runs authored before they existed
    resolve unchanged, carrying None for each rather than a default that would put every
    waste line into the insulation take-off."""
    model, _ = resolve(catlin_plan)
    drains = [r for r in model.pipe_runs if r.system == "drain"]
    assert drains, "fixture regression: the Catlin house lost its drains"
    assert all(r.finish is None and r.insulation is None for r in drains)
