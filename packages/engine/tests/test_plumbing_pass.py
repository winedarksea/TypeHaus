"""The 2026-07-29 plumbing pass: routed 3D runs, wet-wall occupancy, concrete coverage,
staggered-stud framing, fixture-unit tables, and the plumbing takeoff block."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return model


@pytest.fixture(scope="module")
def code_report(catlin_model):
    return run_from_model(catlin_model, [], tier=Tier.CODE)


# --- routed 3D runs -------------------------------------------------------------------

def test_legacy_two_invert_runs_still_resolve(catlin_model):
    """A run authored with only start/end inverts (the old schema) interpolates linearly
    and keeps its endpoint elevations — no source edit was needed for existing vents."""
    run = next(r for r in catlin_model.pipe_runs if r.tag == "PR-M-WC-VENT")
    assert run.z_m is not None and len(run.z_m) == len(run.path)
    assert run.z_start_m == pytest.approx(run.z_m[0])
    assert run.z_end_m == pytest.approx(run.z_m[-1])
    # Monotonic between the two authored inverts.
    assert min(run.z_m) >= min(run.z_start_m, run.z_end_m) - 1e-9
    assert max(run.z_m) <= max(run.z_start_m, run.z_end_m) + 1e-9


def test_vertical_drops_count_in_developed_length(catlin_model):
    """The main collector drops a foot at the WC1 sleeve (repeated plan point); its
    resolved length is the 3D developed length, longer than the plan polyline."""
    run = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-MAIN-DRAIN")
    plan_len = sum(
        ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        for a, b in zip(run.path[:-1], run.path[1:]))
    assert run.length_m > plan_len + 0.2  # the ~1' drop at the sleeve


def test_pipe_runs_emit_viewer_solids_by_system(catlin_model):
    categories = {s.category for s in catlin_model.solids
                  if s.category.startswith("pipe_")}
    assert {"pipe_drain", "pipe_water_cold", "pipe_water_hot", "pipe_vent"} <= categories


# --- wet-wall occupancy ---------------------------------------------------------------

def test_wet_wall_occupancy_passes_for_the_bath1_risers(code_report):
    rows = [f for f in code_report.findings if f.check_id == "mep.wet_wall_occupancy"]
    assert rows and all(f.result.value == "pass" for f in rows)
    assert any("W-M-BAE" in f.message for f in rows)


def test_wet_wall_occupancy_flags_a_pipe_too_fat_for_its_wall(catlin_model):
    from typehaus.resolve.mep import wet_wall_occupancy

    run = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-CW-BATH1")
    assert not wet_wall_occupancy(run, catlin_model)
    import dataclasses
    fat = dataclasses.replace(run, diameter_m=0.2)  # an 8" pipe in a 5.5" wall
    problems = wet_wall_occupancy(fat, catlin_model)
    assert any(p["kind"] == "too_shallow" for p in problems)


# --- concrete coverage ----------------------------------------------------------------

def test_every_concrete_crossing_is_sleeved(catlin_model):
    from typehaus.resolve.mep import concrete_crossings

    unsleeved = [c for c in concrete_crossings(catlin_model) if c["sleeve"] is None]
    assert not unsleeved, unsleeved


def test_sleeve_coverage_and_alignment_are_clean(code_report):
    for check_id in ("mep.sleeve_coverage", "mep.sleeve_alignment",
                     "mep.drain_slope", "mep.footing_clearance",
                     "mep.sewer_exit_invert", "mep.pipe_sizing",
                     "mep.under_slab_burial"):
        rows = [f for f in code_report.findings if f.check_id == check_id]
        assert rows, check_id
    for check_id in ("mep.sleeve_coverage", "mep.sleeve_alignment",
                     "mep.drain_slope", "mep.under_slab_burial",
                     "mep.footing_clearance", "mep.sewer_exit_invert",
                     "mep.pipe_sizing"):
        fails = [f.message for f in code_report.findings
                 if f.check_id == check_id and f.result.value == "fail"]
        assert not fails, (check_id, fails)


def test_sewer_exit_matches_its_cast_sleeve(code_report):
    rows = [f for f in code_report.findings
            if f.check_id == "mep.sewer_exit_invert" and "SP-B-SEWER-EXIT" in f.message]
    assert rows and all(f.result.value == "pass" for f in rows)


def test_building_drain_leaves_under_the_footing_not_through_the_wall(catlin_model):
    """The sewer connection is below the slab, and the foundation's geometry then leaves the
    building drain exactly one way out.

    The walls stop at -9'-0", which is the slab *top*, so there is no wall to pass through at
    an under-slab invert; the footings run -9'-8" to -9'-0", so the drain leaves beneath one
    inside a protection sleeve (IRC P2604). This pins that arrangement — a future edit that
    quietly re-hosts the exit onto a wall would be authoring a hole through concrete that
    does not extend that far down.
    """
    exit_sleeve = next(s for s in catlin_model.sleeves if s.tag == "SP-B-SEWER-EXIT")
    assert exit_sleeve.host_category == "footing"
    assert exit_sleeve.axis == "horizontal"
    # Below the footing's own underside: it passes under the bearing plane, not through it.
    assert exit_sleeve.center_z_m < exit_sleeve.z0_m

    slab = next(s for s in catlin_model.solids if s.tag == "SL-B-FLOOR")
    main = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-MAIN-DRAIN")
    # The run starts at the basement ceiling and ends under the slab: the collector is still
    # hung where the upper-floor stacks arrive, and only its last leg is buried.
    assert main.z_m[0] > slab.z1_m
    assert main.z_m[-1] < slab.z0_m
    # Monotonic fall the whole way — a building drain that ever rises is a blockage.
    assert all(b <= a + 1e-9 for a, b in zip(main.z_m, main.z_m[1:]))


def test_the_basement_slab_fixtures_drain_by_gravity(catlin_model):
    """The basement's slab fixtures are what the under-slab main exists to make possible:
    they stand *on* the slab, so they can only drain if the main is below them. Before the
    re-route the main hung 6'-6" overhead and none of these runs could be authored at all.

    Written for FX-1, the mechanical room's utility sink and the only such fixture until
    2026-07-30; it now covers the two branches that replaced it — the stair-foot bathroom's
    and the sauna shower end's.
    """
    slab = next(s for s in catlin_model.solids if s.tag == "SL-B-FLOOR")
    main = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-MAIN-DRAIN")
    branches = {
        # branch tag: (fixtures it carries, the vent branch that serves them)
        "PR-B-BATH-DRAIN": (("FX-B-BATH-WC", "FX-B-BATH-LAV"), "PR-B-BATH-VENT"),
        "PR-B-SAUNA-DRAIN": (("FX-B-SAUNA-SH", "FX-B-SAUNA-FD"), "PR-B-SAUNA-VENT"),
    }
    for arm_tag, (fixtures, vent_tag) in branches.items():
        arm = next(r for r in catlin_model.pipe_runs if r.tag == arm_tag)
        assert set(fixtures) <= set(arm.serves), arm_tag
        # Each ties onto the main's under-slab leg, and arrives no lower than the main's
        # invert where it lands — a branch below the main it joins would not flow.
        assert _on_segment(arm.path[-1], main.path[-2], main.path[-1]), arm_tag
        assert arm.z_m[-1] >= _invert_at(main, arm.path[-1]) - 1e-9, arm_tag
        # Buried, not cast into the slab.
        assert max(arm.z_m[1:]) + arm.diameter_m / 2.0 <= slab.z0_m, arm_tag
        # And each is vented, which needed the drain to exist first.
        vent = next(r for r in catlin_model.pipe_runs if r.tag == vent_tag)
        assert set(fixtures) <= set(vent.serves), vent_tag


# These started life as private copies here; the 2026-07-31 DFU rollup promoted them into
# the engine (they are what `drain_tie_ins`/`accumulated_serves` derive the topology
# with), so the tests import the one source of truth rather than cross-checking a fork.
from typehaus.resolve.mep import on_pipe_segment as _on_segment  # noqa: E402


def _invert_at(run, point):
    from typehaus.resolve.mep import pipe_invert_at

    z = pipe_invert_at(run, point)
    assert z is not None, f"{point} is not on {run.tag}"
    return z


# --- drain-load topology (2026-07-31 rollup) -------------------------------------------

def test_drain_loads_roll_up_through_the_routed_geometry(catlin_model):
    """The building drain grades on the union of every run that discharges into it —
    the FX-1 serves convention (slab branches not re-listed on the main) can no longer
    hide load. 34 authored + 8 slab-branch DFU = 42, which is what forced the 4" main."""
    from typehaus.resolve.mep import accumulated_serves, drain_tie_ins
    from typehaus.takeoff.plumbing_calc import branch_load, fixture_units

    drains = [r for r in catlin_model.pipe_runs if r.system == "drain"]
    acc = accumulated_serves(drains)
    units = {row.tag: row for row in fixture_units(catlin_model.plan)}
    main = acc["PR-B-MAIN-DRAIN"]
    # Union by fixture tag — a fixture listed on both its branch and the main counts once.
    assert len(main) == len(set(main))
    for fx in ("FX-B-BATH-WC", "FX-B-SAUNA-SH", "FX-B-SAUNA-FD", "FX-B-BATH-LAV"):
        assert fx in main, fx
    load, unresolved = branch_load(main, units, "drain")
    assert not unresolved
    assert load == 42.0
    # Every drain run discharges somewhere except the building drain itself and the
    # dryer condensate's air-gap termination — a new run silently missing its tie-in
    # would show up here as an extra terminal, understating every load downstream of it.
    ties = drain_tie_ins(drains)
    terminals = {r.tag for r in drains} - set(ties)
    assert terminals == {"PR-B-MAIN-DRAIN", "PR-M-DRYER-COND"}


def test_rollup_is_a_union_never_a_sum_and_unknown_never_partial():
    """Synthetic three-run tree: branch B (fixture also re-listed on main M) and orphan O.
    The rollup must count the shared fixture once, leave the orphan alone, and go UNKNOWN
    downstream when any upstream tag has no table row."""
    from types import SimpleNamespace

    from typehaus.resolve.mep import accumulated_serves
    from typehaus.takeoff.plumbing_calc import FixtureUnits, branch_load

    def run(tag, path, z, serves):
        return SimpleNamespace(tag=tag, system="drain", path=path, z_m=z, serves=serves)

    main = run("M", ((0.0, 0.0), (10.0, 0.0)), (-0.5, -0.6), ("FX-A",))
    branch = run("B", ((5.0, 3.0), (5.0, 0.0)), (-0.3, -0.55), ("FX-A", "FX-B"))
    orphan = run("O", ((20.0, 20.0), (25.0, 20.0)), (-0.3, -0.4), ("FX-C",))
    acc = accumulated_serves([main, branch, orphan])
    assert acc["M"] == ("FX-A", "FX-B")
    assert acc["O"] == ("FX-C",)
    units = {"FX-A": FixtureUnits("FX-A", "toilet", None, 3.0, 2.5, 0.0, 2.5),
             "FX-B": FixtureUnits("FX-B", "lavatory", None, 1.0, 1.0, 1.0, 1.5)}
    load, unresolved = branch_load(acc["M"], units, "drain")
    assert load == 4.0 and not unresolved
    # FX-B loses its table row: the main's load is unknowable, never 3.0-and-shrug.
    load, unresolved = branch_load(acc["M"], {"FX-A": units["FX-A"]}, "drain")
    assert load is None and unresolved == ("FX-B",)


def test_a_sibling_terminating_on_the_same_junction_is_not_a_parent():
    """Several branches all ending on one wye point are siblings discharging into
    whatever continues downstream — deriving parent links between them would both
    inflate their loads and put a cycle in the graph (catlin's WC2/BATH1 junction)."""
    from types import SimpleNamespace

    from typehaus.resolve.mep import drain_tie_ins

    def run(tag, path, z, serves=()):
        return SimpleNamespace(tag=tag, system="drain", path=path, z_m=z, serves=serves)

    junction = (3.0, 0.0)
    a = run("A", ((3.0, 5.0), junction), (-0.5, -0.61))
    b = run("B", ((3.0, -5.0), junction), (-0.5, -0.61))
    main = run("M", ((0.0, 0.0), (10.0, 0.0)), (-0.6, -0.7))
    ties = drain_tie_ins([a, b, main])
    assert ties == {"A": "M", "B": "M"}


# --- staggered-stud framing -----------------------------------------------------------

def test_staggered_wet_wall_frames_2x4_on_2x6_plates(catlin_model):
    wall = next(w for w in catlin_model.walls if w.tag == "W-S-BD-N")
    studs = [m for m in wall.members if m.category == "stud"]
    plates = [m for m in wall.members if "plate" in m.category]
    assert {p.profile for p in plates} == {"2x6"}
    module = [s for s in studs if s.profile == "2x4"]
    assert module, "staggered module studs missing"
    # Alternating faces: module studs sit off the centerline on both sides.
    axis_y = wall.axis[0][1]
    offsets = {round(s.p0[1] - axis_y, 3) for s in module}
    assert len(offsets) == 2 and all(abs(abs(o) - 0.0254) < 1e-3 for o in offsets)


def test_bearing_walls_stay_continuous_2x6(code_report):
    rows = [f for f in code_report.findings
            if f.check_id == "structural.wet_wall_bearing"]
    assert rows and all(f.result.value == "pass" for f in rows)


# --- fixture units + takeoff ----------------------------------------------------------

def test_dfu_table_sizing():
    from typehaus.takeoff.plumbing_calc import (
        required_drain_diameter_in, required_supply_size_in, trap_arm_limit_in)

    assert required_drain_diameter_in(3) == 1.5
    assert required_drain_diameter_in(18) == 3.0
    assert required_drain_diameter_in(500) is None
    assert required_supply_size_in(8) == 0.75
    assert trap_arm_limit_in(0.0508) == 60.0  # 2"
    assert trap_arm_limit_in(1.0) is None


def test_branch_load_reports_unresolved_rather_than_partial_sums():
    from typehaus.takeoff.plumbing_calc import FixtureUnits, branch_load

    units = {"A": FixtureUnits("A", "toilet", None, 3.0, 2.5, 0.0, 2.5)}
    load, unresolved = branch_load(("A", "B"), units, "drain")
    assert load is None and unresolved == ("B",)
    load, unresolved = branch_load(("A",), units, "drain")
    assert load == 3.0 and not unresolved


def test_laundry_pair_keeps_its_fixture_units_under_the_stacked_type(catlin_model):
    """The fixture-unit tables are keyed on ``plan_symbol``, so retyping the washer to the
    stacked pair silently zeroes its 3 DFU unless ``washer-dryer-stacked`` has its own rows.
    A stack is still one washer for code: the heat-pump dryer above it drains condensate to
    an indirect waste, which is not a drainage fixture and takes no water at all."""
    from typehaus.takeoff.plumbing_calc import fixture_units

    units = {u.tag: u for u in fixture_units(catlin_model.plan)}
    washer = units["FX-M-LAUNDRY"]
    assert washer.symbol == "washer-dryer-stacked"
    assert (washer.dfu, washer.wsfu_total) == (3.0, 4.0)
    tub = units["FX-M-LAUNDRY-SINK"]
    assert tub.symbol == "laundry-sink"
    assert (tub.dfu, tub.wsfu_total) == (2.0, 1.5)


def test_plumbing_takeoff_block_shape(catlin_model):
    import json

    from typehaus.takeoff.plumbing import plumbing_takeoff

    block = plumbing_takeoff(catlin_model)
    assert set(block) == {"riser", "fixture_units", "takeoff"}
    assert block["riser"] and all(
        len(v) == 3 for row in block["riser"] for v in row["vertices"])
    assert block["fixture_units"]["total_dfu"] > 0
    assert block["takeoff"]["cast_in"], "the pour-day list must not be empty"
    assert any(r["material"] == "pex" for r in block["takeoff"]["pipe"])
    json.dumps(block)  # the whole block must be JSON-serializable


def test_reader_and_check_share_the_fixture_unit_derivation():
    """The invariant that keeps the public page and the permit finding in agreement."""
    import typehaus.checks.mep.plumbing as checks
    import typehaus.takeoff.plumbing as takeoff

    import inspect

    assert "takeoff.plumbing_calc" in inspect.getsource(checks)
    assert "plumbing_calc" in inspect.getsource(takeoff)
