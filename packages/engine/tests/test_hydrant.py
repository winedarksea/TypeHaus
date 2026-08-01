"""The garage frost-free hydrant — the project's first water-supply run.

`grep PipeSystem.WATER_COLD` across the repo returned nothing before this: every authored
run was DRAIN or VENT. So this file pins more than one fixture. It pins that a supply run
resolves at the elevation it was authored at, that a fixture needing no DRAIN does not trip
the drain-sleeve rule, and that the freeze-depth rule can actually fail.
"""

from __future__ import annotations

import pytest

from typehaus.findings import Result
from typehaus.model.enums import PipeSystem, Service

_M_TO_FT = 3.280839895


def _context(model):
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.registry import CheckContext, Preferences

    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2024)


def _hydrant(model):
    return model.plan.by_tag("FX-G-HYDRANT")


def _supply(model):
    return next(run for run in model.pipe_runs if run.tag == "PR-G-HYDRANT-CW")


# --- 1. the type -------------------------------------------------------------------------

def test_the_hydrant_type_needs_water_and_nothing_else(catlin_model):
    """The absence is the design. A hydrant drains through its own weep at the buried
    shutoff, not into the sanitary system — and because `needs` carries no Service.DRAIN,
    `_missing_sleeve_findings` will not fire a false "no sleeve" FAIL against it."""
    fixture_type = next(t for t in catlin_model.plan.library.fixture_types
                        if t.tag == "FX-HYDRANT-Y34SS")
    assert fixture_type.needs == frozenset({Service.WATER_COLD})
    assert Service.DRAIN not in fixture_type.needs
    assert fixture_type.plan_symbol == "hydrant"
    # The two things that are specified but unmodellable live in `source`, which is what
    # mep.hydrant_freeze_depth's UNKNOWN points the reader at.
    assert "vacuum breaker" in fixture_type.source
    assert "coating" in fixture_type.source


def test_the_hydrant_draws_its_own_symbol(catlin_model):
    """An unlisted plan_symbol raises at load; a *missing* one silently falls back to the
    anonymous rectangle every symbol-less type gets. Neither is what this wants."""
    from typehaus.model.placeable_symbols import SYMBOL_NAMES, plan_symbol_strokes

    assert "hydrant" in SYMBOL_NAMES
    strokes = plan_symbol_strokes("hydrant", 0.1524, 0.1524)  # the 6" escutcheon
    assert len(strokes) >= 3, "riser, handle and outlet at minimum"
    # Every stroke stays inside the type's own footprint, like every other symbol.
    for stroke in strokes:
        for x, y in stroke["points"]:
            assert abs(x) <= 0.1524, stroke
            assert abs(y) <= 0.1524, stroke


# --- 2. the instance, and where it lives --------------------------------------------------

def test_the_hydrant_is_authored_in_an_editable_module(catlin_model):
    """Fixtures are UI-movable, so authoring one in a non-editable module is a hard build
    error (loader.uneditable_movable_element). That is exactly why the type and the instance
    are split: fixture_types.py uses frozenset and cannot be editable."""
    from pathlib import Path

    from typehaus.source import load_plan

    provenance = load_plan(
        Path(__file__).resolve().parents[3] / "houses" / "catlin").provenance
    location = provenance.location("FX-G-HYDRANT")
    assert location is not None
    assert location.file.endswith("fixtures.py"), location.file
    assert provenance.is_editable("FX-G-HYDRANT")
    # Its *type* is the opposite, and deliberately so: fixture_types.py uses frozenset,
    # which the editable dialect forbids, which is exactly why the two are split.
    assert not provenance.is_editable("FX-HYDRANT-Y34SS")


def test_the_hydrant_is_on_the_garage_storey_at_the_authored_spot(catlin_model):
    hydrant = _hydrant(catlin_model)
    assert hydrant.room == "RM-GARAGE"
    x, y = hydrant.position.xy_m
    assert x * _M_TO_FT == pytest.approx(1.5, abs=1e-6)
    assert y * _M_TO_FT == pytest.approx(62.0, abs=1e-6)
    # Clear of everything else on that wall: EQ-G-HEATER at y=48', both EV receptacles at
    # y=41.5', and both north windows.
    heater = catlin_model.plan.by_tag("EQ-G-HEATER")
    assert abs(heater.position.xy_m[1] - hydrant.position.xy_m[1]) * _M_TO_FT > 10


# --- 3. the supply run --------------------------------------------------------------------

def test_the_supply_run_carries_the_hydrant(catlin_model):
    """No longer the project's *only* cold run — the 2026-07-29 plumbing pass authored the
    whole domestic distribution — but the hydrant's own feed must still exist and serve it."""
    runs = [r for r in catlin_model.pipe_runs if r.system == PipeSystem.WATER_COLD.value]
    hydrant = [r for r in runs if r.tag == "PR-G-HYDRANT-CW"]
    assert len(hydrant) == 1
    assert "FX-G-HYDRANT" in hydrant[0].serves


def test_the_supply_run_stays_six_feet_down_for_its_whole_length(catlin_model):
    """The number that matters, and the one that is easy to get wrong. PipeRun elevations
    resolve as `storey datum + authored`, so the same authored -6' on the basement's -9'
    datum would land at -15' absolute. This run is filed on `main` (datum 0' = grade)
    precisely so the authored number means what it says."""
    run = _supply(catlin_model)
    assert run.storey == "main"
    grade = catlin_model.plan.project.site.grade.meters
    # Every vertex holds the 6' bury except the terminal standpipe — the hydrant's own
    # self-draining barrel, a repeated final plan point rising through the slab.
    assert run.z_m is not None
    buried = run.z_m[:-1] if run.path[-1] == run.path[-2] else run.z_m
    for z in buried:
        assert (grade - z) * _M_TO_FT == pytest.approx(6.0, abs=1e-6)
    # ...and 72" is well below the 42" footing frost depth, not in conflict with it.
    assert (grade - run.z_start_m) > 42 / 12 / _M_TO_FT


def test_the_supply_sleeve_is_a_water_penetration_on_the_slabs_own_storey(catlin_model):
    """Two things go wrong here if nobody says them. The sleeve's purpose defaults to DRAIN,
    which this is not; and SL-G-FLOOR is filed on `main` while the garage walls are on
    `garage`, so a sleeve filed with the fixture would sit on a storey with no slab and
    `_missing_sleeve_findings` — which scopes its containment test to solid.storey ==
    storey.tag — would never see it."""
    sleeve = catlin_model.plan.by_tag("SP-G-HYDRANT")
    assert sleeve.purpose is Service.WATER_COLD
    assert sleeve.host_ref == "SL-G-FLOOR"
    resolved = next(s for s in catlin_model.sleeves if s.tag == "SP-G-HYDRANT")
    assert resolved.storey == "main"
    assert resolved.serves_fixture == "FX-G-HYDRANT"
    # The fixture itself is on the garage storey — the split is deliberate.
    assert next(o for o in catlin_model.canvas_objects
                if o.tag == "FX-G-HYDRANT").storey == "garage"


def test_the_pedestal_rides_on_the_slab_rather_than_bearing_on_soil(catlin_model):
    """A Pad at 0'-0" is a footing above the frost line and structural.frost_depth says so,
    correctly. This is a topping pour, so it is a walking-surface Slab."""
    pedestal = catlin_model.plan.by_tag("SL-G-HYDRANT-PED")
    assert pedestal.datum == "walking_surface"
    solid = next(s for s in catlin_model.solids if s.tag == "SL-G-HYDRANT-PED")
    grade = catlin_model.plan.project.site.grade.meters
    assert solid.z0_m == pytest.approx(grade, abs=1e-6)
    assert (solid.z1_m - solid.z0_m) * 12 * _M_TO_FT == pytest.approx(4.0, abs=1e-6)


def test_the_gravel_pit_is_the_only_drainage_path(catlin_model):
    """There is deliberately no floor drain — see notes/garage_hydrant.md. The pit is a
    Drywell; it was a deepened FootingBedding only while that was the closest thing the model
    had, and that stand-in billed the pit's perimeter as drain tile that is not there."""
    pit = catlin_model.plan.by_tag("DRW-G-HYDRANT")
    assert pit.depth.meters * _M_TO_FT == pytest.approx(3.0, abs=1e-6)
    assert pit.geotextile
    assert "FX-G-HYDRANT" in pit.inlet_refs
    # Outside the west wall line, clear of the 20"-wide footing it must not undermine.
    x_ft = pit.position.xy_m[0] * _M_TO_FT
    assert x_ft < 0 and abs(x_ft) - pit.diameter.meters * _M_TO_FT / 2 > 20 / 24
    solid = next(s for s in catlin_model.solids if s.tag == "DRW-G-HYDRANT")
    assert solid.category == "drywell"
    # No drain fixture, and no DRAIN run, anywhere in the garage.
    garage_fixtures = [e for e in catlin_model.plan.storey_elements("garage")
                       if e.element_kind == "Fixture"]
    types = {t.tag: t for t in catlin_model.plan.library.fixture_types}
    assert not [f for f in garage_fixtures
                if Service.DRAIN in types[f.type_ref].needs]


# --- 4. the check -------------------------------------------------------------------------

def test_the_freeze_depth_rule_passes_on_the_house_as_built(catlin_model):
    from typehaus.checks.mep.plumbing import hydrant_freeze_depth

    findings = hydrant_freeze_depth(_context(catlin_model))
    assert not [f for f in findings if f.result is Result.FAIL]
    passed = [f for f in findings if f.result is Result.PASS]
    assert len(passed) == 2, [f.message for f in passed]   # bury depth + the sleeve
    # The two things the model cannot express are UNKNOWN, not a silent PASS (#32).
    unknown = [f for f in findings if f.result is Result.UNKNOWN]
    assert len(unknown) == 1
    assert "vacuum breaker" in unknown[0].message
    assert "interior shutoff" in unknown[0].message


def test_a_shallow_supply_run_fails_the_freeze_depth_rule(catlin_model):
    """A rule that only ever passes proves nothing. Raise the run to 3' and it must fail."""
    from typehaus.checks.mep.plumbing import hydrant_freeze_depth
    from typehaus.model import ft

    ctx = _context(catlin_model)
    run = catlin_model.plan.by_tag("PR-G-HYDRANT-CW")
    shallow = run.model_copy(update={"elevations": tuple(
        ft(-3) if e.feet < 0 else e for e in run.elevations)})
    patched = catlin_model.plan.with_elements(
        "main", [shallow if e.tag == run.tag else e
                 for e in catlin_model.plan.storey_elements("main")])
    from typehaus.resolve import resolve
    model, _ = resolve(patched)
    failures = [f for f in hydrant_freeze_depth(
        type(ctx)(plan=patched, model=model, preferences=ctx.preferences,
                  profile=ctx.profile)) if f.result is Result.FAIL]
    assert len(failures) == 1
    assert "36\"" in failures[0].message and "72\"" in failures[0].message


def test_a_run_that_surfaces_mid_way_fails_even_with_deep_ends(catlin_model):
    """The failure people actually get: a supply routed up into the building and back down
    freezes at the high point, not at its ends. Authoring one end shallow is the closest the
    IR can express (a run carries only its two invert elevations), and the rule catches it."""
    from typehaus.checks.mep.plumbing import hydrant_freeze_depth
    from typehaus.model import ft
    from typehaus.resolve import resolve

    ctx = _context(catlin_model)
    run = catlin_model.plan.by_tag("PR-G-HYDRANT-CW")
    # Raise one mid-route vertex to -1' while both ends stay deep: the run now has a
    # genuine high point between deep ends, which is where a supply line freezes.
    rising = run.model_copy(update={"elevations": tuple(
        ft(-1) if i == 1 else e for i, e in enumerate(run.elevations))})
    patched = catlin_model.plan.with_elements(
        "main", [rising if e.tag == run.tag else e
                 for e in catlin_model.plan.storey_elements("main")])
    model, _ = resolve(patched)
    failures = [f for f in hydrant_freeze_depth(
        type(ctx)(plan=patched, model=model, preferences=ctx.preferences,
                  profile=ctx.profile)) if f.result is Result.FAIL]
    assert len(failures) == 1
    assert "high point" in failures[0].message


def test_the_hydrant_does_not_trip_the_drain_sleeve_rule(catlin_model):
    """The reason FX-HYDRANT-Y34SS declares no Service.DRAIN. If it did, the hydrant would
    be read as a drain fixture over a structural slab with no drain sleeve serving it."""
    from typehaus.checks.mep.plumbing import sleeve_alignment

    findings = sleeve_alignment(_context(catlin_model))
    assert not [f for f in findings
                if f.result is Result.FAIL and "FX-G-HYDRANT" in f.element_tags]


# --- 5. the export ------------------------------------------------------------------------

def test_the_hydrant_reaches_ifc_as_a_flow_terminal(catlin_model, tmp_path):
    """A fixture with no IFC class falls to IfcBuildingElementProxy, which no downstream
    plumbing schedule reads as a fixture."""
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    path = tmp_path / "model.ifc"
    emit_ifc(catlin_model, path)
    model = ifcopenshell.open(str(path))
    hydrant = next(e for e in model.by_type("IfcProduct") if e.Name == "FX-G-HYDRANT")
    # IfcSanitaryTerminal is an IfcFlowTerminal subtype — the family a plumbing schedule
    # collects, and specifically not IfcBuildingElementProxy.
    assert hydrant.is_a("IfcFlowTerminal"), hydrant.is_a()
