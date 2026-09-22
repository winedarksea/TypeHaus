"""``engineering/thermal_break.py`` against ``sunken_garden_court_free_body.md`` §11j-§11k.

The note was worked by hand before the module was rewritten; this file reproduces it. Basis 7
is basis 6's pure isolation joint — ASTM C578 Type X XPS, 15 psi, E ESTIMATED at 525, the
neutral-point demand with the stems' shrinkage credit — with two owner decisions in the model:
every board is set into a STRIPPED BLOCKOUT (no pour lock-in) and ``SL-B-FLOOR``'s 1" perimeter
break states its grade. Basis 8 makes that board FOAMULAR 1000 (Type V, 100 psi) and grades the
sheet's 1/3 sustained-load rule. Every item is OK, that rule governing at 0.885.
Two ablations below are the proof that each decision is the lever: take either away and the
numbers walk back to basis 6.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.thermal_break import KIND

_FOOT, _STEM, _BEAM = ("TB-SG-W1", "TB-SG-E1"), ("TB-SG-W1-STEM", "TB-SG-E1-STEM"), "W-SG-BRKBM"
_ALL = (*_FOOT, *_STEM, _BEAM)

# The lateral path is one set of links for the whole thrust (§11j-§11k), on every item.
_PATH = {
    "house slab-edge bearing": (44_582.1, 151_200.0, 0.2949),
    "house slab-edge sustained load": (44_582.1, 50_394.96, 0.8847),
    "house slab strut compression": (29.4855, 2_040.0, 0.014454),
    "house global sliding": (1.5, 2.6877, 0.5581),
    "house far-wall soil bearing": (52_213.6, 130_534.1, 0.4000),
    # Net thrust less the retained soil is NEGATIVE, so the row is a force, not an FS.
    "court sliding under break thrust": (0.0, 73_422.3, 0.0),
}
# (demand, capacity, ratio) per row, hand-worked in §11j. No fresh-concrete pressure row on
# any board: a blockout takes the pour and the board is set after it is stripped.
_NOTE = {
    "foot": {
        "board strain, pour + closing": (0.0309399, 0.071429, 0.4332),
        **_PATH,
    },
    "stem": {
        "board strain, pour + closing": (0.0051739, 0.071429, 0.0724),
        "house insulation bearing": (1.0860, 15.0, 0.0724),
        "house wall flexure": (15_012.9, 276_298.8, 0.0543),
        "house wall shear": (625.54, 72_376.8, 0.0086),
        "house floor-line reaction": (800.65, 3_285.0, 0.2437),
        **_PATH,
    },
    "beam": {
        "board strain, pour + closing": (0.0309399, 0.057143, 0.5414),
        **_PATH,
    },
}
_NOTE_X_IN = 187.51
_NOTE_SIGMA_PSI = {"TB-SG-W1": 6.497, "TB-SG-W1-STEM": 1.086, _BEAM: 8.122}
# Every board is formed and stripped, so nothing is locked in. The second column is what
# each board WOULD carry as a form face (§11i) — `test_a_formed_and_stripped_board_carries_
# no_pour` reads it back, because a flag with no measured effect is not a lever.
_NOTE_LOCK_LB = {"TB-SG-W1": 0.0, "TB-SG-W1-STEM": 0.0, _BEAM: 0.0}
_FORM_FACE_LOCK_LB = {"TB-SG-W1": 233.3, "TB-SG-W1-STEM": 6_238.0, _BEAM: 41_162.0}
_NOTE_TOTAL_LB = 46_183.4
_FORM_FACE_TOTAL_LB = 100_288.0
_NOTE_RUN_IN = 322.565


def _group(tag):
    return "beam" if tag == _BEAM else ("stem" if tag in _STEM else "foot")


@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    from typehaus.engineering import EngineeringContext

    return EngineeringContext(plan=catlin_plan, model=catlin_model_ro, soil_class="GM")


@pytest.fixture(scope="module")
def records(ctx):
    from typehaus.engineering import EngineeringResults

    results = EngineeringResults(ctx)
    return {tag: results[f"{KIND}/{tag}"] for tag in _ALL}


def _state(record, name):
    return next((s for s in record.limit_states if s.name == name), None)


def _input(record, name):
    return next(q.value for q in record.inputs if q.name == name)


def test_the_kind_is_computed_and_the_beam_board_is_an_item(ctx) -> None:
    from typehaus.engineering import DEFERRALS, keys_of

    assert KIND not in DEFERRALS
    assert keys_of(KIND, ctx) == sorted(_ALL)


@pytest.mark.parametrize("tag", _ALL)
def test_every_row_reproduces_section_11(records, tag) -> None:
    record = records[tag]
    expected = _NOTE[_group(tag)]
    assert [s.name for s in record.limit_states] == list(expected), tag
    for name, (demand, capacity, ratio) in expected.items():
        state = _state(record, name)
        assert state.demand == pytest.approx(demand, rel=5e-4), (tag, name)
        assert state.capacity == pytest.approx(capacity, rel=5e-4), (tag, name)
        assert state.ratio == pytest.approx(ratio, rel=1e-3, abs=6e-4), (tag, name)


@pytest.mark.parametrize("tag", _ALL)
def test_basis_7_is_ok_with_nothing_open(records, tag) -> None:
    record = records[tag]
    assert record.status is Status.OK
    assert record.missing == ()
    assert record.basis_version == "8"
    notes = " ".join(record.notes)
    for flag in ("RETIRED WITH THE BARS", "RETIRED WITH THE STRIP", "ESTIMATED MODULUS",
                 "NEUTRAL POINT", "FORMED AND STRIPPED", "SENSITIVITY ON E"):
        assert flag in notes, (tag, flag)
    # The lock-in flag is a statement about a form face and this joint has none.
    assert "POUR LOCK-IN" not in notes
    assert ("STEM SHRINKAGE" in notes) == (tag in _STEM)


def test_the_neutral_point_the_thrust_and_the_run(records) -> None:
    for tag, sigma in _NOTE_SIGMA_PSI.items():
        assert _input(records[tag], "board_stress") == pytest.approx(sigma, abs=1e-3)
        assert _input(records[tag], "board_lock_in") == _NOTE_LOCK_LB[tag]
    for tag in _ALL:
        assert _input(records[tag], "neutral_point") == pytest.approx(_NOTE_X_IN, abs=0.01)
        assert _input(records[tag], "house_thrust") == pytest.approx(_NOTE_TOTAL_LB, rel=1e-4)
    assert _input(records["TB-SG-W1"], "court_run") == pytest.approx(_NOTE_RUN_IN, abs=1e-3)
    assert _input(records["TB-SG-W1"], "delta_T") == 30.0


def test_the_stem_shrinkage_is_aci_209r() -> None:
    from typehaus.engineering.thermal_break_demand import stem_shrinkage

    assert stem_shrinkage() * 1e6 == pytest.approx(137.42, abs=0.01)


def test_the_sensitivity_note_reads_the_higher_modulus(records) -> None:
    note = next(n for n in records["TB-SG-W1-STEM"].notes if n.startswith("SENSITIVITY"))
        # §11j's table: the floor line moves with E and never approaches its capacity now.
    assert "house floor-line reaction 0.244 -> 0.179 / 0.320 / 0.380" in note
    assert "house slab-edge bearing 0.295 -> 0.217 / 0.387 / 0.459" in note
    # §11k: the graded 1/3 rule goes over inside the band (x1.5), unlike the bearing row.
    assert "house slab-edge sustained load 0.885 -> 0.651 / 1.162 / 1.378" in note


def _compute_with(ctx, monkeypatch, **values):
    from typehaus.engineering import thermal_break as tb
    from typehaus.engineering import thermal_break_geometry as geo

    real = geo.isolation_boards(ctx)
    monkeypatch.setattr(geo, "isolation_boards",
                        lambda _ctx: [b.model_copy(update=values) for b in real])
    return {r.key: r for r in tb.compute(ctx)}


def test_an_unnamed_product_holds_every_row_open(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, source=None)
    assert out["TB-SG-W1"].limit_states == ()
    assert "IsolationBoard.psi" in " ".join(out["TB-SG-W1"].missing)
    assert out[_BEAM].limit_states == (), "the beam's board names the closure boards' product"


def test_without_a_placement_sequence_a_form_face_pour_is_monolithic(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, placement_sequence_ref=None,
                        formed_and_stripped=False)
    state = _state(out["TB-SG-W1"], "fresh-concrete pressure")
    assert state.demand == pytest.approx(150 * 117.4375 / 1728.0, abs=1e-4)
    # And the locked-in pour follows it: a 117" head on the footing board, not 8".
    assert _input(out["TB-SG-W1"], "board_lock_in") > 10 * _FORM_FACE_LOCK_LB["TB-SG-W1"]


def _with_site(ctx, **site_values):
    project = ctx.plan.project
    site = project.site.model_copy(update=site_values)
    plan = ctx.plan.model_copy(update={"project": project.model_copy(update={"site": site})})
    return dataclasses.replace(ctx, plan=plan)


def test_no_service_temperature_holds_the_thermal_rows_open(ctx) -> None:
    from typehaus.engineering import thermal_break as tb
    from typehaus.engineering.thermal_break_board import TEMPERATURE_MISSING

    out = {r.key: r for r in tb.compute(_with_site(ctx, concrete_service_temperature=None))}
    record = out["TB-SG-W1"]
    assert TEMPERATURE_MISSING in record.missing
    # Not even a pressure row is left: a stripped board never meets fresh concrete.
    assert record.limit_states == ()
    assert record.status is Status.INCOMPLETE


def test_a_k_v_only_report_leaves_base_rotation_on_its_band(ctx) -> None:
    from typehaus.engineering.base_supports import measured

    report = ctx.plan.project.site.lateral_subgrade_modulus.model_copy(update={"n_h_pci": None})
    assert measured(_with_site(ctx, lateral_subgrade_modulus=report)) is None
    assert measured(ctx) is not None, "catlin authors a presumed n_h since 2026-09-21"


def test_a_formed_and_stripped_board_carries_no_pour(ctx, monkeypatch) -> None:
    """The flag is the lever, and this reads it BOTH ways: off, every board is a form face
    again and basis 6's lock-in, thrust and slab edge come straight back."""
    out = _compute_with(ctx, monkeypatch, formed_and_stripped=False)
    for tag, lock in _FORM_FACE_LOCK_LB.items():
        assert _input(out[tag], "board_lock_in") == pytest.approx(lock, rel=1e-3), tag
        assert _input(out[tag], "house_thrust") == pytest.approx(_FORM_FACE_TOTAL_LB, rel=1e-4)
        assert _state(out[tag], "fresh-concrete pressure") is not None, tag
    # FOAMULAR 1000 does not close the item on its own: the thrust more than doubles, the
    # sustained rule reads 1.864 and the beam's board is over again.
    assert _state(out["TB-SG-W1"], "house slab-edge sustained load").ratio == pytest.approx(
        93_955.0 / 50_395.0, rel=1e-3)
    assert _state(out[_BEAM], "board strain, pour + closing").ratio > 1.0
    assert out[_BEAM].status is Status.OVER


def test_the_beam_board_inherits_the_stripping_statement(ctx, monkeypatch) -> None:
    """A Layer names no sequence of its own, so the veneer beam's board reads the authored
    boards' statement — 41,162 lb of it, 76% of the lock-in that put basis 6 over."""
    assert _input(_compute_with(ctx, monkeypatch, formed_and_stripped=False)[_BEAM],
                  "board_lock_in") == pytest.approx(41_162.0, rel=1e-3)
    monkeypatch.undo()
    from typehaus.engineering import thermal_break as tb

    assert _input({r.key: r for r in tb.compute(ctx)}[_BEAM], "board_lock_in") == 0.0


def test_a_stripped_board_must_name_its_placement_annotation(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, placement_sequence_ref=None)
    assert any("placement_sequence_ref" in m for m in out["TB-SG-W1"].missing)
    assert out["TB-SG-W1"].status is Status.INCOMPLETE


def _with_slab_break(ctx, **values):
    from typehaus.engineering import thermal_break_path as path

    slab = ctx.plan.by_tag("SL-B-FLOOR")
    brk = slab.perimeter_thermal_break.model_copy(update=values)
    return slab.model_copy(update={"perimeter_thermal_break": brk}), path


def test_the_slab_edge_reads_the_authored_grade(ctx, monkeypatch) -> None:
    """Strip the product off SL-B-FLOOR's break and the edge falls back to the C578 floor —
    15 psi, an unstated grade, and 1.966 OVER. It never goes INCOMPLETE: an ungraded row can
    never read over, which is how 4.14 stayed visible through basis 6."""
    from typehaus.engineering import thermal_break as tb

    slab, path = _with_slab_break(ctx, psi=None, modulus_psi=None, source=None,
                                 sustained_load_fraction=None)
    real = path.house_slab
    monkeypatch.setattr(path, "house_slab",
                        lambda c, f: (slab, real(c, f)[1]) if real(c, f) else None)
    record = {r.key: r for r in tb.compute(ctx)}["TB-SG-W1"]
    state = _state(record, "house slab-edge bearing")
    assert state.capacity == pytest.approx(15.0 * 3.5 * 432.0)
    assert state.ratio == pytest.approx(1.966, rel=1e-3)
    assert "grade unstated" in state.citation
    assert record.status is Status.OVER and record.missing == ()
    assert _state(record, "house slab-edge sustained load") is None  # no sheet, no rule


def test_the_sheets_sustained_load_rule_is_graded_and_foamular_400_fails_it(
        ctx, monkeypatch) -> None:
    """§11k: the 1/3 rule is a limit state, and the product is the lever. On FOAMULAR 400
    (basis 7's board) the same 44,582 lb reads 2.212 OVER; FOAMULAR 1000 reads 0.885."""
    from typehaus.engineering import thermal_break as tb

    slab, path = _with_slab_break(ctx, psi=40.0, modulus_psi=1800.0)
    real = path.house_slab
    monkeypatch.setattr(path, "house_slab",
                        lambda c, f: (slab, real(c, f)[1]) if real(c, f) else None)
    record = {r.key: r for r in tb.compute(ctx)}["TB-SG-W1"]
    state = _state(record, "house slab-edge sustained load")
    assert state.ratio == pytest.approx(44_582.1 / (0.3333 * 40.0 * 1_512.0), rel=1e-3)
    assert state.ratio == pytest.approx(2.212, abs=1e-3)
    assert record.status is Status.OVER


def test_slab_thermal_break_round_trips_and_a_rating_names_its_sheet() -> None:
    import pytest as _pytest

    from typehaus.model.floors import SlabThermalBreak
    from typehaus.quantities import inch

    brk = SlabThermalBreak(material_ref="xps", thickness=inch(1), psi=40.0,
                           modulus_psi=1800.0, sustained_load_fraction=1 / 3,
                           source="Owens Corning FOAMULAR 400, ASTM C578 Type VI")
    assert SlabThermalBreak.model_validate(brk.model_dump()) == brk
    assert not brk.modulus_estimated
    with _pytest.raises(ValueError, match="source"):
        SlabThermalBreak(material_ref="xps", thickness=inch(1), psi=40.0)
    bare = SlabThermalBreak(material_ref="xps", thickness=inch(1))
    assert bare.psi is None and bare.sustained_load_fraction is None


def test_isolation_board_round_trips() -> None:
    from typehaus.model.structure import IsolationBoard
    from typehaus.quantities import ft, inch, pt

    board = IsolationBoard(uid="AAAAAAAAAA", tag="TB-RT", position=pt(ft(0), ft(0)),
                           thickness=inch(2.5), height=inch(8), length=inch(84),
                           elevation=inch(-100), modulus_psi=525.0, source="sheet",
                           modulus_estimated=True, placement_sequence_ref="AN-X")
    assert IsolationBoard.model_validate(board.model_dump()) == board
    assert board.psi == 40.0 and board.material == "xps" and board.modulus_estimated
    assert not board.formed_and_stripped, "a form face is the conservative default"


def test_site_inputs_carry_their_provenance() -> None:
    from typehaus.model import ConcreteServiceTemperature, SubgradeModulus

    presumed = SubgradeModulus(k_v_pci=88.4, provenance="presumed", source="Bowles T9-1",
                               basis="table row")
    assert SubgradeModulus.model_validate(presumed.model_dump()) == presumed
    temps = ConcreteServiceTemperature(max_f=80.0, min_f=0.0, source="AASHTO T3.12.2.1.1-1",
                                       basis="published row", placement_min_f=50.0)
    assert ConcreteServiceTemperature.model_validate(temps.model_dump()) == temps
    assert temps.provenance == "published"
