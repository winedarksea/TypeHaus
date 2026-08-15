"""The garage frost-free hydrant — the project's first water-supply run.

`grep PipeSystem.WATER_COLD` across the repo returned nothing before this: every authored
run was DRAIN or VENT. So this file pins more than one fixture. It pins that a supply run
resolves at the elevation it was authored at, that a fixture needing no DRAIN does not trip
the drain-sleeve rule, and that the freeze-depth rule can actually fail.
"""

from __future__ import annotations

import pytest

from _helpers import check_context

from typehaus.findings import Result
from typehaus.model.enums import PipeSystem, Service

_M_TO_FT = 3.280839895


def _context(model):
    return check_context(model=model)


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
    assert x * _M_TO_FT == pytest.approx(5.0, abs=1e-6)
    assert y * _M_TO_FT == pytest.approx(60.0, abs=1e-6)
    # It stands free, and that is the design rather than a missing reference: a 6'-0" bury
    # cannot sit against a wall whose footing bears at -4'-2" without putting its shutoff
    # and weep stone inside the 45° influence line. → test_the_hydrant_assembly_clears_...
    assert hydrant.wall_ref is None
    # Clear of everything else in the room: EQ-G-HEATER and the workbench at y≈48', both EV
    # receptacles at y=41.5'/56', and both north windows.
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


def test_the_hydrant_stands_on_the_garage_slab_not_on_the_storey_datum(catlin_model):
    """The bug this test exists for: the hydrant floated 22" in the air.

    RM-GARAGE's floor is SL-G-FLOOR, poured at grade and filed on `main`, while the `garage`
    storey datum is the ICF stem top 1'-10" above it. A mount elevation measured off the
    storey datum therefore lands a floor-standing fixture 22" over its own floor, which is
    exactly where this one stood until `resolve_placeables` was taught to measure off
    `room_floor_elevation` instead. No source file states the offset — the resolver derives
    it — so nothing but this assertion would catch the regression.
    """
    hydrant = next(o for o in catlin_model.canvas_objects if o.tag == "FX-G-HYDRANT")
    slab = next(s for s in catlin_model.solids if s.tag == "SL-G-FLOOR")
    assert hydrant.z_m == pytest.approx(slab.z1_m, abs=1e-6)
    grade = catlin_model.plan.project.site.grade.meters
    assert hydrant.z_m == pytest.approx(grade, abs=1e-6)
    # ...and that is a full GARAGE_STEM_REVEAL below the storey it is filed on.
    storey = next(s for s in catlin_model.plan.storeys if s.tag == "garage")
    assert (storey.elevation.meters - hydrant.z_m) * _M_TO_FT == pytest.approx(
        1 + 10 / 12, abs=1e-6)


def test_the_whole_garage_stands_on_its_floor_not_on_the_stem_top(catlin_model):
    """The fix is not hydrant-specific and must not become so. Everything in RM-GARAGE was
    22" high — the workbench off the floor, every device off its authored height — because
    one shared resolver measured them all from the same wrong plane."""
    by_tag = {o.tag: o for o in catlin_model.canvas_objects}
    grade = catlin_model.plan.project.site.grade.meters
    assert by_tag["FURN-G-WORKBENCH"].z_m == pytest.approx(grade, abs=1e-6)
    for tag, above_floor_ft in (("ED-G-EV-620", 4.0), ("ED-G-EV-1450", 4.0),
                                ("EQ-G-HEATER", 6.0), ("ED-G-SW", 46 / 12),
                                ("ED-G-LT1", 8.0)):
        assert (by_tag[tag].z_m - grade) * _M_TO_FT == pytest.approx(
            above_floor_ft, abs=1e-6), tag
    # The one deliberate exception: ED-G-EXT-LT is authored with no `room` (it stands outside
    # RM-GARAGE, and `electrical.wet_location` decides "exterior" from that), so it keeps the
    # storey datum its comment in plan/lighting.py already accounts for.
    assert (by_tag["ED-G-EXT-LT"].z_m - grade) * _M_TO_FT == pytest.approx(
        8 + 10 / 12, abs=1e-6)


def test_the_pedestal_and_its_block_out_are_gone(catlin_model):
    """Retired 2026-08-03 (notes/garage_hydrant.md): the hydrant uses the garage's own slab.
    Both pieces went together — a block-out sleeve whose host no longer exists is an orphan
    reference, not a leftover detail."""
    assert catlin_model.plan.by_tag("SL-G-HYDRANT-PED") is None
    assert catlin_model.plan.by_tag("SP-G-HYDRANT-PED") is None
    assert not [s for s in catlin_model.solids if s.tag == "SL-G-HYDRANT-PED"]
    # What stayed is what actually does the work: the slab penetration and the drywell.
    assert catlin_model.plan.by_tag("SP-G-HYDRANT") is not None
    assert catlin_model.plan.by_tag("DRW-G-HYDRANT") is not None


def test_the_gravel_pit_is_the_only_drainage_path(catlin_model):
    """There is deliberately no floor drain — see notes/garage_hydrant.md. The Y34's head
    self-drains through a weep at its buried shutoff, into stone packed around the valve —
    not into a separate exterior catch basin, so the pit sits on the hydrant's own stack."""
    pit = catlin_model.plan.by_tag("DRW-G-HYDRANT")
    assert pit.depth.meters * _M_TO_FT == pytest.approx(1.5, abs=1e-6)
    assert pit.geotextile
    assert "FX-G-HYDRANT" in pit.inlet_refs
    # Collocated with the hydrant's own supply stack (SP-G-HYDRANT), not offset to some
    # exterior spot — the weep has to reach stone at the valve, not stone a pipe carries it to.
    x_ft, y_ft = pit.position.xy_m[0] * _M_TO_FT, pit.position.xy_m[1] * _M_TO_FT
    assert x_ft == pytest.approx(5.0, abs=1e-6)
    assert y_ft == pytest.approx(60.0, abs=1e-6)
    # Stone from -5'-6" to -7'-0": the 6' shutoff sits 6" below the top of it with a foot of
    # stone under the weep. It was 2' across x 4' deep to -9'-0" until 2026-08-15 — 12.6 cu
    # ft for a weep that discharges quarts, and deep enough that no position in the garage
    # could stand it off the footings. → test_the_hydrant_assembly_clears_the_footings.
    solid = next(s for s in catlin_model.solids if s.tag == "DRW-G-HYDRANT")
    assert solid.category == "drywell"
    assert solid.z1_m * _M_TO_FT == pytest.approx(-5.5, abs=1e-6)
    assert solid.z0_m * _M_TO_FT == pytest.approx(-7.0, abs=1e-6)
    # No drain fixture, and no DRAIN run, anywhere in the garage.
    garage_fixtures = [e for e in catlin_model.plan.storey_elements("garage")
                       if e.element_kind == "Fixture"]
    types = {t.tag: t for t in catlin_model.plan.library.fixture_types}
    assert not [f for f in garage_fixtures
                if Service.DRAIN in types[f.type_ref].needs]


def test_the_hydrant_assembly_clears_the_footings(catlin_model):
    """The thing that put this fixture where it is, checked as geometry rather than as a
    position it happens to have.

    Everything at the shutoff is 22" below the garage footings' -4'-2" bearing plane, and
    the weep stone reaches 34" below it. IRC P2604.3's 45° influence line asks for that much
    lateral clearance from the footing edge before an excavation stops loading the footing.
    At the old (1'-6", 62') the riser had 8" and the stone pocket overlapped FT-GF-W's
    footprint outright; `mep.footing_clearance` walks pipe runs only, so nothing graded the
    pocket at all and the riser was passing on a sleeve that protected nothing.

    Being *under* a footing is not clearance from it — the cone opens downward — so the one
    crossing that stays, PR-G-HYDRANT-CW passing beneath FT-GF-S-DR, is sleeved rather than
    spaced.
    """
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    footings = [s for s in catlin_model.solids
                if s.category == "footing" and s.tag.startswith("FT-GF-")]
    pour = unary_union([Polygon(s.outline) for s in footings])
    bearing = min(s.z0_m for s in footings)

    pit = next(s for s in catlin_model.solids if s.tag == "DRW-G-HYDRANT")
    stone = Polygon(pit.outline)
    assert not stone.intersects(pour), "the weep excavation is under the footing"
    assert stone.distance(pour.boundary) + 1e-9 >= bearing - pit.z0_m, \
        "the weep excavation is inside the footings' 45° influence line"

    # The riser, at the deep end where the shutoff is.
    run = _supply(catlin_model)
    riser = Point(run.path[-1])
    assert riser.distance(pour.boundary) + 1e-9 >= bearing - min(run.z_m), \
        "the hydrant riser is inside the footings' 45° influence line"

    # And the run reaches it without a jog: entry, hydrant, rise. Two legs, one of them
    # vertical — the west dog-leg out to the old position is what carried the encroachment.
    assert len(run.path) == 3
    assert run.path[0][0] == pytest.approx(run.path[1][0], abs=1e-9), "not one straight leg"


# --- 4. the check -------------------------------------------------------------------------

def test_the_freeze_depth_rule_passes_on_the_house_as_built(catlin_model):
    """Three findings for this hydrant now, and none of them UNKNOWN.

    It used to be two PASSes and one UNKNOWN, the UNKNOWN reading "the model has no valve
    or backflow-preventer element, so neither can be evaluated here". ``PipeAccessory``
    (2026-08-01) is that element, and `PA-G-HYD-SEAT`/`PA-G-HYD-VB` are what the third
    finding now grades — the shutoff and the vacuum breaker this file's §5 used to record
    only as a sentence on the fixture type's ``source``.
    """
    from typehaus.checks.mep.plumbing import hydrant_freeze_depth

    findings = [f for f in hydrant_freeze_depth(_context(catlin_model))
                if "FX-G-HYDRANT" in f.element_tags]
    assert not [f for f in findings if f.result is not Result.PASS], \
        [f.message for f in findings if f.result is not Result.PASS]
    messages = " | ".join(f.message for f in findings)
    assert "below grade over its whole length" in messages   # bury depth
    assert "SP-G-HYDRANT" in messages                        # the sleeve
    assert "PA-G-HYD-SEAT" in messages and "PA-G-HYD-VB" in messages


def test_a_sleeve_the_run_misses_does_not_protect_it(catlin_model):
    """The defect this fixture's move came out of, pinned as a rule rather than as geometry.

    SP-GF-W-HYD was authored at (0'-9.6", 61'-6") on FT-GF-W, boring the footing's full 20"
    width east-west at the 6' bury while the pipe it claimed to protect ran *parallel* to
    that footing 8" away and never crossed it. `mep.footing_clearance` graded three PASSes
    on it, because the test was only "some sleeve on this pour within 0.3 m" and 8.4" is
    0.213 m. A sleeve is the hole a pipe goes through; proximity is not the question.

    Re-author that sleeve here — offset from the run by more than its own bore, exactly as
    the deleted one was — and the crossing it sits on must go back to FAIL, naming the
    sleeve as present-but-useless so the reader knows to move it rather than add one.
    """
    from typehaus.checks.mep.plumbing_concrete import footing_clearance
    from typehaus.model import ft, pt
    from typehaus.resolve import resolve

    ctx = _context(catlin_model)
    sleeve = catlin_model.plan.by_tag("SP-GF-S-HYD")
    # Slide it 8" off the run's x=5' line, still inside its host footing so it resolves.
    strayed = sleeve.model_copy(update={"position": pt(ft(5, 8), ft(41))})
    patched = catlin_model.plan.with_elements(
        "main", [strayed if e.tag == sleeve.tag else e
                 for e in catlin_model.plan.storey_elements("main")])
    model, _ = resolve(patched)
    findings = [f for f in footing_clearance(
        type(ctx)(plan=patched, model=model, preferences=ctx.preferences,
                  profile=ctx.profile))
        if "PR-G-HYDRANT-CW" in f.element_tags]
    assert [f.result for f in findings] == [Result.FAIL], \
        [f.message for f in findings]
    message = findings[0].message
    assert "SP-GF-S-HYD" in message and "protects nothing" in message

    # And the unmoved house is the control: same crossing, same sleeve, PASS by name.
    passing = [f for f in footing_clearance(ctx) if "PR-G-HYDRANT-CW" in f.element_tags]
    assert [f.result for f in passing] == [Result.PASS]
    assert "SP-GF-S-HYD" in passing[0].message


def test_the_yard_hydrant_and_the_wall_hydrants_are_graded_differently(catlin_model):
    """The house has both families now, and the boundary between them is the thing most
    likely to break quietly: a wall hydrant has no bury depth, so holding it to 72" would
    fail it forever. See ``notes/balcony_irrigation.md``."""
    from typehaus.checks.mep.plumbing import hydrant_freeze_depth

    findings = hydrant_freeze_depth(_context(catlin_model))
    assert not [f for f in findings if f.result is Result.FAIL]
    graded = {tag for f in findings for tag in f.element_tags if tag.startswith("FX-")}
    assert {"FX-G-HYDRANT", "FX-M-PORCH-HYD", "FX-S-BALC-HYD"} <= graded
    for tag in ("FX-M-PORCH-HYD", "FX-S-BALC-HYD"):
        message = " | ".join(f.message for f in findings if tag in f.element_tags)
        assert "no bury depth to grade" in message
        assert "below grade" not in message


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
    # Raise the last *buried* vertex to -1' while the entry stays deep: the run now surfaces
    # before it reaches the hydrant, which is where a supply line freezes.
    #
    # This is the run's second-to-last vertex, and it is the case the standpipe exemption
    # used to swallow — it popped every rising vertex off the tail rather than the one
    # terminal barrel, so a run climbing to -1'-0" graded PASS. The run is only three
    # vertices long now, so there is nothing left to hide that behind.
    rising = run.model_copy(update={"elevations": tuple(
        ft(-1) if i == len(run.elevations) - 2 else e
        for i, e in enumerate(run.elevations))})
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
