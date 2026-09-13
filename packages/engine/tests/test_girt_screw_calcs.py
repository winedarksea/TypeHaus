"""``engineering/girt_screw.py`` against a hand-worked note.

The oracle is ``houses/catlin/notes/catlin_truss_engineering.md`` §3, re-worked by hand on
2026-09-12 from ASCE 7-16, ICC-ES ESR-1078 and NDS 2018 — the discipline every calc module
in this package is held to.

Three of these assertions are doing unusual work and are worth reading before changing:

* :func:`test_the_engagement_rule_rejects_the_screw_this_wall_used_to_specify` pins the
  reason this item exists. A lag-type screw clamps only on plain SHANK, every SDWS22 threads
  3" whatever its length (IAPMO UES ER-192 Table 7), and the 8" SDWS22800DB this wall
  specified until 2026-09-12 therefore stood 1" of thread inside the 6.0" stack it was meant
  to pull together. Nothing in the house had ever written that thread length down.
* :func:`test_the_clamped_stack_is_six_inches_not_six_and_a_half` pins the correction the
  audit got wrong. The sheathing is nailed to the stud, so it is on the stud's side of the
  joint and is not a member being drawn together.
* :func:`test_the_east_and_west_walls_are_in_the_same_item` pins the grouping. Every
  ``standoff="block"`` wall on this house resolves to one stack, one block module and one
  course module, so ``EXT_2X6`` and ``PLANT_EXT_2X6_HUMID`` are one design and one seal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.engineering.item import Status

#: §3 of the note, hand-worked before the module existed. The wind half is shared term for
#: term with ``board_batten_girt_span.md`` and ``test_wall_panel_calcs.py``: the panel and
#: the screw carry ONE suction, and two numbers for it would mean one of them was wrong.
_ORACLE = {
    "mean_roof_height_ft": 25.5990,
    "q_h_psf": 19.2679,
    "gcp_zone5": -1.4,
    "gcpi": 0.18,
    "asd_zone5_psf": 18.2659,
    # 32" block module x 24" course module.
    "tributary_ft2": 5.3333,
    "demand_lb": 97.4184,
    # The screw: FastenMaster TimberLOK 8" TLOK08, ESR-1078 Table 1A (2" thread).
    "length_in": 8.0,
    "thread_in": 2.0,
    "diameter_in": 0.189,
    "clamped_stack_in": 6.0,
    "through_in": 6.5,
    "plain_shank_in": 6.0,
    "thread_in_stud_in": 1.5,
    # ESR-1078 Table 2, SPF G 0.42: 170 lb/in x 1.5", C_D 1.0 (the report's clause unread).
    "withdrawal_lb": 255.0,
    "withdrawal_ratio": 0.3820,
    # ESR-1078 Table 3, 1-1/2" side member at SG 0.55 — the girt IS that side member.
    "pull_through_lb": 200.0,
    "pull_through_ratio": 0.4871,
    # NDS 2018 §12.2.1 cross-check, printed and never graded against.
    "nds_w_per_in": 95.01,
    # NDS 2018 §12.1.4.6, 6D.
    "min_penetration_in": 1.134,
    # The superseded screw: 8" long, 3" thread (IAPMO UES ER-192 Table 7).
    "sdws_thread_in_stack_in": 1.0,
}

#: The group's key: the lowest member tag, which is what a person types.
_ITEM = "girt_screw/W-A-N1"

#: Every wall whose outer band is a block-standoff girt — 34 ``EXT_2X6`` plus the plant
#: room's two ``PLANT_EXT_2X6_HUMID``, which share the stack exactly.
_GIRT_WALL_COUNT = 36

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def results(catlin_plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    return EngineeringResults(EngineeringContext(plan=catlin_plan, model=model))


@pytest.fixture(scope="module")
def record(results):
    return results[_ITEM]


def _variant(tmp_path, edit):
    """catlin with one edit to ``plan/assemblies.py``, resolved — the ablation harness."""
    from _helpers import copy_house

    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    house = copy_house(_CATLIN, tmp_path / "house")
    source = house / "plan" / "assemblies.py"
    source.write_text(edit(source.read_text()))
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    model, _ = resolve(loaded.plan)
    return EngineeringResults(EngineeringContext(plan=loaded.plan, model=model))


def _replace(old: str, new: str, count: int = 0):
    def edit(text: str) -> str:
        assert old in text, old
        return text.replace(old, new) if count == 0 else text.replace(old, new, count)
    return edit


def _state(record, fragment):
    return next(s for s in record.limit_states if fragment in s.name)


def _inputs(record):
    return {q.name: q.value for q in record.inputs}


# --- scope and grouping ------------------------------------------------------------------

def test_the_east_and_west_walls_are_in_the_same_item(results, record):
    """One stack, one block module, one course module and one screw are ONE design.

    Both cladding overrides are in it: the north/south walls carry board & batten and the
    east/west walls PBR, and the screw under them does not know the difference — a
    ``layer_materials`` override swaps a material and never a ``FramingSpec``.
    """
    ids = {key for key in results if key.startswith("girt_screw/")}
    assert ids == {_ITEM}
    tags = set(record.element_tags)
    assert len(record.element_tags) == _GIRT_WALL_COUNT
    for north_south in ("W-A-N1", "W-M-S1", "W-S-N3B"):
        assert north_south in tags
    for east_west in ("W-M-E1", "W-M-W1B", "W-S-E1", "W-S-W4"):
        assert east_west in tags


def test_any_member_resolves_to_the_group(results):
    # `haus engineering --item girt_screw/W-M-E1` has to reach the design that grades it.
    assert results["girt_screw/W-M-E1"].item_id == _ITEM
    assert "girt_screw/W-M-E1" not in results


def test_membership_is_in_the_fingerprint(record):
    # `element_tags` is not hashed, so without this input a wall could join or leave the
    # group and a stamp pinned to the old set would still read FRESH.
    assert _inputs(record)["crossing_count"] == float(_GIRT_WALL_COUNT)


# --- the demand --------------------------------------------------------------------------

def test_the_wind_demand_is_the_panels_own(record):
    """Same q_h, same coefficients, same 0.6W as ``wall_panel`` — one suction, one number."""
    inputs = _inputs(record)
    assert inputs["design_wind_speed"] == 115.0
    assert inputs["mean_roof_height"] == pytest.approx(_ORACLE["mean_roof_height_ft"], abs=1e-3)
    assert inputs["velocity_pressure"] == pytest.approx(_ORACLE["q_h_psf"], abs=1e-3)
    assert inputs["GCp_zone5"] == pytest.approx(_ORACLE["gcp_zone5"])
    assert inputs["GCpi"] == pytest.approx(_ORACLE["gcpi"])
    assert inputs["suction_asd"] == pytest.approx(_ORACLE["asd_zone5_psf"], abs=1e-3)


def test_the_crossing_tributary_is_the_block_module_by_the_course_module(record):
    inputs = _inputs(record)
    assert inputs["block_spacing"] == pytest.approx(32.0)
    assert inputs["course_spacing"] == pytest.approx(24.0)
    assert inputs["tributary_area"] == pytest.approx(_ORACLE["tributary_ft2"], abs=1e-3)
    assert inputs["crossing_demand"] == pytest.approx(_ORACLE["demand_lb"], abs=0.01)


# --- the thread bookkeeping --------------------------------------------------------------

def test_the_clamped_stack_is_six_inches_not_six_and_a_half(record):
    """The 1/2" ply is nailed to the stud, so it is not a member being drawn together."""
    inputs = _inputs(record)
    assert inputs["clamped_stack"] == pytest.approx(_ORACLE["clamped_stack_in"])
    assert inputs["through_thickness"] == pytest.approx(_ORACLE["through_in"])
    assert inputs["thread_in_stud"] == pytest.approx(_ORACLE["thread_in_stud_in"])


def test_thread_bookkeeping_matches_the_note(record):
    from typehaus.engineering.girt_screw_withdrawal import (
        plain_shank_in,
        thread_in_main_member,
        thread_in_side_member,
    )

    length, thread = _ORACLE["length_in"], _ORACLE["thread_in"]
    assert plain_shank_in(length, thread) == pytest.approx(_ORACLE["plain_shank_in"])
    assert thread_in_side_member(
        length, thread, _ORACLE["clamped_stack_in"]) == pytest.approx(0.0)
    assert thread_in_main_member(
        length, thread, _ORACLE["through_in"]) == pytest.approx(_ORACLE["thread_in_stud_in"])


def test_the_engagement_rule_rejects_the_screw_this_wall_used_to_specify(record):
    """SDWS22800DB: 8" long, 3" thread (ER-192 Table 7) — 1" of it inside the stack."""
    from typehaus.engineering.girt_screw_withdrawal import plain_shank_in, thread_in_side_member

    assert thread_in_side_member(8.0, 3.0, _ORACLE["clamped_stack_in"]) == pytest.approx(
        _ORACLE["sdws_thread_in_stack_in"])
    assert plain_shank_in(8.0, 3.0) < _ORACLE["clamped_stack_in"]

    state = _state(record, "thread engagement")
    assert state.demand == pytest.approx(_ORACLE["clamped_stack_in"])
    assert state.capacity == pytest.approx(_ORACLE["plain_shank_in"])
    assert state.ratio == pytest.approx(1.0)
    assert state.ok
    # It sits on its own minimum when the screw fits, so it must never win `governing`.
    assert state.is_detailing


def test_the_sdws_is_printed_as_the_alternate_that_fails(record):
    joined = "\n".join(record.notes)
    assert "SDWS22800DB" in joined and "ER-192" in joined
    assert "SDWS221000DB" in joined


# --- the graded capacities ---------------------------------------------------------------

def test_withdrawal_is_the_reports_value_times_the_embedded_thread(record):
    from typehaus.engineering.girt_screw_withdrawal import withdrawal_lb

    hand = withdrawal_lb(170.0, _ORACLE["thread_in_stud_in"])
    assert hand == pytest.approx(_ORACLE["withdrawal_lb"], abs=0.01)

    state = _state(record, "withdrawal")
    assert state.capacity == pytest.approx(_ORACLE["withdrawal_lb"], abs=0.01)
    assert state.demand == pytest.approx(_ORACLE["demand_lb"], abs=0.01)
    assert state.ratio == pytest.approx(_ORACLE["withdrawal_ratio"], abs=1e-3)
    assert state.ok


def test_the_nds_equation_is_a_cross_check_and_not_the_grade(record):
    """W = 2850 G^2 D is printed beside the tested value, never instead of it."""
    from typehaus.engineering.girt_screw_withdrawal import nds_withdrawal_per_in

    assert nds_withdrawal_per_in(0.42, _ORACLE["diameter_in"]) == pytest.approx(
        _ORACLE["nds_w_per_in"], abs=0.05)
    assert any("2850 G^2 D" in note and "CROSS-CHECK" in note for note in record.notes)
    # The graded capacity is the report's 170 lb/in, not the equation's 95.
    assert _state(record, "withdrawal").capacity > 200.0


def test_head_pull_through_governs(record):
    """The lowest of the three capacities, and the girt IS the table's 1-1/2" side member."""
    state = _state(record, "pull-through")
    assert state.capacity == pytest.approx(_ORACLE["pull_through_lb"])
    assert state.ratio == pytest.approx(_ORACLE["pull_through_ratio"], abs=1e-3)
    assert state.ok
    assert record.governing is not None
    assert "pull-through" in record.governing.name


def test_the_six_diameter_minimum_penetration_is_checked(record):
    state = _state(record, "minimum thread penetration")
    assert state.demand == pytest.approx(_ORACLE["min_penetration_in"], abs=1e-3)
    assert state.capacity == pytest.approx(_ORACLE["thread_in_stud_in"])
    assert state.ok and state.is_detailing


def test_the_item_is_finished_and_stampable(record):
    assert record.status is Status.OK
    assert record.missing == ()
    assert len(record.limit_states) == 4


def test_the_lsl_scope_note_is_stated_for_the_reviewer(record):
    assert any("LSL" in note and "REVIEWER ITEM" in note for note in record.notes)


def test_the_c_d_of_one_is_stated_rather_than_assumed(record):
    assert any("C_D is taken as 1.0" in note for note in record.notes)


# --- the refusals ------------------------------------------------------------------------

def test_a_girt_band_with_no_screw_authored_is_incomplete_and_names_every_field(tmp_path):
    """A house that authors no screw gets five named fields, never a defaulted capacity.

    The whole block has to come out together: ``FramingSpec`` refuses a half-authored screw
    at load time (all-or-none), because three numbers out of five would report as "nobody
    has got to it yet" rather than "somebody transcribed half a table row".
    """
    results = _variant(tmp_path, _strip_fastener_fields)
    record = results[_ITEM]
    assert record.status is Status.INCOMPLETE
    named = "\n".join(record.missing)
    for field in ("standoff_fastener_length_in", "standoff_fastener_thread_in",
                  "standoff_fastener_diameter_in",
                  "standoff_fastener_withdrawal_lb_per_in",
                  "standoff_fastener_pull_through_lb"):
        assert field in named
    assert record.limit_states == ()


def _strip_fastener_fields(text: str) -> str:
    # The block runs to the end of the FramingSpec call, so the closing parens come off with
    # it and `standoff="block"` has to become the last argument again.
    assert 'standoff="block",' in text, "the fields moved; fix this test"
    text = text.replace('standoff="block",', 'standoff="block")),')
    lines = [line for line in text.splitlines(keepends=True)
             if "standoff_fastener" not in line]
    return "".join(lines)


def test_half_an_authored_screw_is_refused_at_load(tmp_path):
    """The all-or-none validator, from the house's own source."""
    from _helpers import copy_house

    from typehaus.source import load_plan

    house = copy_house(_CATLIN, tmp_path / "house")
    source = house / "plan" / "assemblies.py"
    source.write_text(source.read_text().replace(
        "standoff_fastener_pull_through_lb=200.0,\n", "", 1))
    loaded = load_plan(house)
    messages = "\n".join(f.message for f in loaded.findings)
    assert loaded.plan is None or "all-or-none" in messages, messages


def test_a_screw_whose_thread_stands_in_the_stack_is_over(tmp_path):
    """Author the SDWS's own 3" thread and the item must report OVER, not quietly pass."""
    results = _variant(tmp_path, _replace(
        "standoff_fastener_thread_in=2.0,", "standoff_fastener_thread_in=3.0,"))
    record = results[_ITEM]
    assert record.status is Status.OVER
    state = _state(record, "thread engagement")
    assert not state.ok
    assert state.capacity == pytest.approx(5.0)


def test_the_cross_check_names_the_studs_own_specific_gravity(record):
    """G feeds the NDS note only; the graded capacity is the report's tested value."""
    assert any("G 0.42" in note for note in record.notes)
    assert _state(record, "withdrawal").capacity == pytest.approx(
        _ORACLE["withdrawal_lb"], abs=0.01)
