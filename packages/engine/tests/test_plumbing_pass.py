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


def _on_segment(point, start, end, tol=1e-6):
    """True when ``point`` lies on the segment ``start``-``end``.

    The branches no longer all land on the main's own last vertex — one ties in at the head of
    the under-slab leg and one part way down it — so the relationship to assert is
    "somewhere on that leg", not "at its end".
    """
    (px, py), (ax, ay), (bx, by) = point, start, end
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > tol:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    length_sq = (bx - ax) ** 2 + (by - ay) ** 2
    return -tol <= dot <= length_sq + tol


def _invert_at(run, point, tol=1e-6):
    """The run's authored invert where ``point`` sits on it, interpolated along the segment.

    Takes the *deepest* match, not the first. PR-B-MAIN-DRAIN passes through (3', 15'-6")
    twice — once at the ceiling, where the collector turns, and once 9'-8" lower, where the
    vertical drop through the slab lands — so one plan point carries two inverts. The under-slab
    one is the leg a buried branch actually ties into, and it is the lower of the two.
    """
    candidates = []
    for index in range(len(run.path) - 1):
        start, end = run.path[index], run.path[index + 1]
        if not _on_segment(point, start, end):
            continue
        length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        if length <= tol:
            continue
        travelled = ((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2) ** 0.5
        fraction = travelled / length
        candidates.append(run.z_m[index] + (run.z_m[index + 1] - run.z_m[index]) * fraction)
    assert candidates, f"{point} is not on {run.tag}"
    return min(candidates)


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
