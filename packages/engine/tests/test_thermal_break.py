"""``engineering/thermal_break.py`` against ``sunken_garden_court_free_body.md`` §11j-§11l.

The note was worked by hand before the module was rewritten; this file reproduces it. Basis 7
is basis 6's pure isolation joint — ASTM C578 Type X XPS, 15 psi, E ESTIMATED at 525, the
neutral-point demand with the stems' shrinkage credit — with two owner decisions in the model:
every board is set into a STRIPPED BLOCKOUT (no pour lock-in) and ``SL-B-FLOOR``'s 1" perimeter
break states its grade. Basis 8 makes that board FOAMULAR 1000 (Type V, 100 psi) and grades the
sheet's 1/3 sustained-load rule. Basis 9 (§11l) puts a stress-capped EPDM sponge in series
with every board and grades the thrust at its published 3.5 psi maximum: no verdict reads the
estimated modulus. Every item is OK, the stems' floor line governing at 0.786. §11m adds the
house's near footing line in plan and the court's winter contraction, both OK. The ablations
below are the proof that each decision is the lever: take one away and its numbers come back.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.thermal_break import KIND

_FOOT, _STEM, _BEAM = ("TB-SG-W1", "TB-SG-E1"), ("TB-SG-W1-STEM", "TB-SG-E1-STEM"), "W-SG-BRKBM"
_ALL = (*_FOOT, *_STEM, _BEAM)

# Basis 9 (§11l) at the 17'-0" court (§12, 2026-09-22) — RE-WORKED HERE by §11l's own lines;
# §11l itself still prints the 19'-0" figures. What moved, and why:
#   * the beam's board is 17.75" x 216" (the veneer beam, axis to axis), not x 240":
#     ΣA = 2 x 672 + 2 x 1,313.25 + 3,834 = 7,804.5 in², T = 3.5 x 7,804.5 = 27,315.75 lb;
#   * line = 27,315.75 − 2 x 2,580.375 = 22,155 lb; strut 22,155 / 1,512 = 14.65 psi;
#   * global (μ 0.25 x D 375,410 + at-rest 1,450.4 plf x (36.00' − 17.00' opening)) = 93,852.6
#     + 27,557.2 = 121,409.8 / 27,315.75 = 4.4447 (the court retains nothing over 17', not
#     19'). D was 375,794 until W-A-C1/C1B/C2/C2M/C2B stopped at the ridge beam's soffit
#     (123" -> 107", 432" of wall x 16" x 8 psf = −384 lb; §12, 2026-09-23), then gained
#     FT-B-CS/-CS2's 26" of 20" x 8" strip, +361.1 lb: D 375,771.1, FS 121,500.0 / 27,315.75
#     = 4.4480;
#   * court friction at 130 pcf, 0.35 x (5,974.8 x 32.667' + 6,174.8 x 18.0') / 1.5 = 71,474
#     (FT-SG-S's 4'-4" toe, free body §12a; 70,634 at one 7'-0" strip);
#   * W-B-S1/S4 are 118" panels (N-B-S1 at 9'-10", was 8'-10", 106"): φMn and φVc go with
#     the panel, x 118/106 — 307,578 and 80,570.
_PATH = {
    "house slab-edge bearing": (22_155.0, 151_200.0, 0.1465),
    "house slab-edge sustained load": (22_155.0, 50_394.96, 0.4396),
    "house slab strut compression": (14.6528, 2_040.0, 0.00718),
    "house global sliding": (1.5, 4.4480, 0.3372),
    "house far-wall soil bearing": (52_213.6, 130_534.1, 0.4000),
    "court sliding under break thrust": (0.0, 71_474.1, 0.0),
}
# §11m: the exact beam-on-bed solution (transfer matrices, not FE) and the winter bound.
_WINTER = {"court winter tension, side run": (37_015.11, 64_800.0, 0.5712),
           "court winter tension, unreinforced joint": (44.0656, 212.132, 0.2077)}
_LINE = {"house near-line plan flexure": (46_396.3, 84_852.81, 0.5468),
         "house near-line plan shear": (1_405.4, 6_788.23, 0.2070),
         "house slab-edge peak sustained load": (22.6527, 33.33, 0.6796), **_WINTER}
_CAP = {"compliant layer strain": (0.053223, 0.125, 0.4258),
        "board strain, pour + closing": (0.016667, 0.071429, 0.2333)}
_NOTE = {
    "foot": {**_CAP, **_PATH, **_LINE},
    "stem": {
        **_CAP,
        "house insulation bearing": (3.5, 15.0, 0.2333),
        "house wall flexure": (48_384.0, 307_578.0, 0.1573),
        "house wall shear": (2_016.0, 80_570.4, 0.0250),
        "house floor-line reaction": (2_580.375, 3_285.0, 0.7855),
        **_PATH, **_LINE,
    },
    "beam": {"compliant layer strain": (0.052635, 0.125, 0.4211),
             "board strain, pour + closing": (0.013333, 0.057143, 0.2333), **_PATH, **_LINE},
}
_CAPPED_TOTAL_LB = 27_315.75
# Basis 8 (§11j-§11k), the uncapped spring — what `compliant=None` must give back. At §12's
# court: S = Σ E A/t ε = 2 x 141,120 x 1.65e-4 + 2 x 275,782.5 x 2.758e-5 + 1,006,425 x
# 1.65e-4 = 227.84 lb/in; at 110 pcf H 56,210, μwL 97,508 over L 322.565" (μw 302.29; §12a,
# FT-SG-S's heavier strip), so x = 153,718 / (227.84 + 604.58) = 184.66" and
# T = 227.84 x 184.66 = 42,074.2 lb. Global: 121,500.0 / 42,074.2 = 2.8878 (D 375,771, above).
_PATH_8 = {
    "house slab-edge bearing": (40_497.2, 151_200.0, 0.2678),
    "house slab-edge sustained load": (40_497.2, 50_394.96, 0.8036),
    "house slab strut compression": (26.784, 2_040.0, 0.013129),
    "house global sliding": (1.5, 2.8878, 0.5194),
    "house far-wall soil bearing": (52_213.6, 130_534.1, 0.4000),
    # Net thrust less the retained soil is NEGATIVE, so the row is a force, not an FS.
    "court sliding under break thrust": (0.0, 71_474.1, 0.0),
    # §11m.1 uncapped: the peak stress is OVER the 1/3 rule — the cap carries this row too.
    "house near-line plan flexure": (58_241.1, 84_852.81, 0.6864),
    "house near-line plan shear": (1_560.4, 6_788.23, 0.2299),
    "house slab-edge peak sustained load": (46.137, 33.33, 1.3843),
    **_WINTER,
}
# (demand, capacity, ratio) per row, hand-worked in §11j. No fresh-concrete pressure row on
# any board: a blockout takes the pour and the board is set after it is stripped.
_NOTE_8 = {
    # Closure 5.5e-6 x 30 x 184.66 = 0.030470"; the stem's (1.65e-4 − 1.3742e-4) x 184.66 =
    # 0.005093", σ 525 x 0.005093 / 2.5 = 1.0695 psi, w 12.834 lb/in: M 14,785, R 616.1,
    # floor line 616.1 + 12.834 x 13.4375 = 788.5 lb; line 42,074.2 − 2 x 788.5 = 40,497.2.
    "foot": {
        "board strain, pour + closing": (0.0304696, 0.071429, 0.4266),
        **_PATH_8,
    },
    "stem": {
        "board strain, pour + closing": (0.0050930, 0.071429, 0.0713),
        "house insulation bearing": (1.06953, 15.0, 0.0713),
        "house wall flexure": (14_785.3, 307_578.0, 0.04807),
        "house wall shear": (616.05, 80_570.4, 0.00765),
        "house floor-line reaction": (788.52, 3_285.0, 0.2400),
        **_PATH_8,
    },
    "beam": {
        "board strain, pour + closing": (0.0304696, 0.057143, 0.5332),
        **_PATH_8,
    },
}
_NOTE_X_IN = 184.66
_NOTE_SIGMA_PSI = {"TB-SG-W1": 6.399, "TB-SG-W1-STEM": 1.0695, _BEAM: 7.998}
# Every board is formed and stripped, so nothing is locked in. The second column is what
# each board WOULD carry as a form face (§11i) — `test_a_formed_and_stripped_board_carries_
# no_pour` reads it back, because a flag with no measured effect is not a lever.
_NOTE_LOCK_LB = {"TB-SG-W1": 0.0, "TB-SG-W1-STEM": 0.0, _BEAM: 0.0}
# The beam's lock-in follows its board: 41,162 x 216/240 = 37,046 lb at the 17'-0" court.
_FORM_FACE_LOCK_LB = {"TB-SG-W1": 233.3, "TB-SG-W1-STEM": 6_238.0, _BEAM: 37_046.0}
_NOTE_TOTAL_LB = 42_074.2
_FORM_FACE_TOTAL_LB = 92_062.6             # 42,074.2 + 2 x 233.3 + 2 x 6,237.8 + 37,046.2
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


def _rows_match(record, expected, tag) -> None:
    assert [s.name for s in record.limit_states] == list(expected), tag
    for name, (demand, capacity, ratio) in expected.items():
        state = _state(record, name)
        assert state.demand == pytest.approx(demand, rel=5e-4), (tag, name)
        assert state.capacity == pytest.approx(capacity, rel=5e-4), (tag, name)
        assert state.ratio == pytest.approx(ratio, rel=1e-3, abs=6e-4), (tag, name)


@pytest.mark.parametrize("tag", _ALL)
def test_every_row_reproduces_section_11l(records, tag) -> None:
    _rows_match(records[tag], _NOTE[_group(tag)], tag)
    assert _input(records[tag], "board_stress") == 3.5
    assert _input(records[tag], "house_thrust") == pytest.approx(_CAPPED_TOTAL_LB, rel=1e-6)


def test_without_the_cap_basis_8_comes_back(ctx, monkeypatch) -> None:
    """§11j-§11k: the uncapped spring, E and the neutral point back in every row."""
    out = _compute_with(ctx, monkeypatch, compliant=None)
    for tag in _ALL:
        _rows_match(out[tag], _NOTE_8[_group(tag)], tag)
        assert "NEUTRAL POINT" in " ".join(out[tag].notes)
        assert ("STEM SHRINKAGE" in " ".join(out[tag].notes)) == (tag in _STEM)
    for tag, sigma in _NOTE_SIGMA_PSI.items():
        assert _input(out[tag], "board_stress") == pytest.approx(sigma, abs=1e-3)
        assert _input(out[tag], "board_lock_in") == _NOTE_LOCK_LB[tag]
    for tag in _ALL:
        assert _input(out[tag], "neutral_point") == pytest.approx(_NOTE_X_IN, abs=0.01)
        assert _input(out[tag], "house_thrust") == pytest.approx(_NOTE_TOTAL_LB, rel=1e-4)
    assert _input(out["TB-SG-W1"], "court_run") == pytest.approx(_NOTE_RUN_IN, abs=1e-3)
    assert _input(out["TB-SG-W1"], "delta_T") == 30.0
    note = next(n for n in out["TB-SG-W1-STEM"].notes if n.startswith("SENSITIVITY"))
    # x1.5 by hand: S 341.76, x = 153,718 / 946.34 = 162.43", T 55,514; the stem's floor
    # line 1.4111 psi x 12 x 61.4375" = 1,040.4 (0.317); line 53,433 (0.353, 1.060).
    assert "house floor-line reaction 0.240 -> 0.176 / 0.317 / 0.377" in note
    assert "house slab-edge bearing 0.268 -> 0.196 / 0.353 / 0.421" in note
    # §11k: the graded 1/3 rule goes over inside the band (x1.5) — why basis 9 exists.
    assert "house slab-edge sustained load 0.804 -> 0.590 / 1.060 / 1.262" in note


@pytest.mark.parametrize("tag", _ALL)
def test_basis_9_is_ok_with_nothing_open(records, tag) -> None:
    record = records[tag]
    assert record.status is Status.OK
    assert record.missing == ()
    assert record.basis_version == "10"
    notes = " ".join(record.notes)
    for flag in ("RETIRED WITH THE BARS", "RETIRED WITH THE STRIP", "ESTIMATED MODULUS",
                 "FORMED AND STRIPPED", "SENSITIVITY ON E", "STRESS-CAPPED"):
        assert flag in notes, (tag, flag)
    # Nothing graded reads the neutral point, the shrinkage credit or a form face.
    for flag in ("POUR LOCK-IN", "NEUTRAL POINT", "STEM SHRINKAGE"):
        assert flag not in notes, (tag, flag)


def test_the_stem_shrinkage_is_aci_209r() -> None:
    from typehaus.engineering.thermal_break_demand import stem_shrinkage

    assert stem_shrinkage() * 1e6 == pytest.approx(137.42, abs=0.01)


@pytest.mark.parametrize("tag", _ALL)
def test_no_row_moves_across_the_modulus_band(records, tag) -> None:
    """The owner's aim (§11l): the verdict does not hinge on the estimated modulus."""
    note = next(n for n in records[tag].notes if n.startswith("SENSITIVITY"))
    assert note.endswith("no row moves"), note


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
    out = _compute_with(ctx, monkeypatch, formed_and_stripped=False, compliant=None)
    for tag, lock in _FORM_FACE_LOCK_LB.items():
        assert _input(out[tag], "board_lock_in") == pytest.approx(lock, rel=1e-3), tag
        assert _input(out[tag], "house_thrust") == pytest.approx(_FORM_FACE_TOTAL_LB, rel=1e-4)
        assert _state(out[tag], "fresh-concrete pressure") is not None, tag
    # FOAMULAR 1000 does not close the item on its own: the thrust more than doubles, the
    # sustained rule reads 1.703 (1.864 at 19'-0") and the beam's board is over again.
    assert _state(out["TB-SG-W1"], "house slab-edge sustained load").ratio == pytest.approx(
        85_753.7 / 50_395.0, rel=1e-3)
    assert _state(out[_BEAM], "board strain, pour + closing").ratio > 1.0
    assert out[_BEAM].status is Status.OVER
    # The cap does not replace the stripping: a board cast against adds its pour in full.
    monkeypatch.undo()
    capped = _compute_with(ctx, monkeypatch, formed_and_stripped=False)
    locked = 2 * _FORM_FACE_LOCK_LB["TB-SG-W1"] + 2 * _FORM_FACE_LOCK_LB["TB-SG-W1-STEM"] \
        + _FORM_FACE_LOCK_LB[_BEAM]
    assert _input(capped["TB-SG-W1"], "house_thrust") == pytest.approx(
        _CAPPED_TOTAL_LB + locked, rel=1e-3)
    assert capped[_BEAM].status is Status.OVER


def test_the_beam_board_inherits_the_stripping_statement(ctx, monkeypatch) -> None:
    """A Layer names no sequence of its own, so the veneer beam's board reads the authored
    boards' statement — 37,046 lb of it at the 17'-0" court (41,162 on the 240" board), 74%
    of the lock-in that would put the record over."""
    assert _input(_compute_with(ctx, monkeypatch, formed_and_stripped=False)[_BEAM],
                  "board_lock_in") == pytest.approx(_FORM_FACE_LOCK_LB[_BEAM], rel=1e-3)
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
    15 psi, an unstated grade: 1.786 OVER uncapped, 0.977 at the cap since the 17'-0" court
    (1.966 / 1.043 at 19'-0") — but since §11m the near line reads it OVER even capped. It
    never goes INCOMPLETE: an ungraded row can never read over (how 4.14 stayed visible)."""
    from typehaus.engineering import thermal_break as tb

    slab, path = _with_slab_break(ctx, psi=None, modulus_psi=None, source=None,
                                 sustained_load_fraction=None)
    real = path.house_slab
    monkeypatch.setattr(path, "house_slab",
                        lambda c, f: (slab, real(c, f)[1]) if real(c, f) else None)
    record = {r.key: r for r in tb.compute(ctx)}["TB-SG-W1"]
    state = _state(record, "house slab-edge bearing")
    assert state.capacity == pytest.approx(15.0 * 3.5 * 432.0)
    assert state.ratio == pytest.approx(22_155.0 / 22_680.0, rel=1e-4)
    assert "grade unstated" in state.citation
    assert _state(record, "house slab-edge sustained load") is None  # no sheet, no rule
    # §11m.1: the unstated break's E is ESTIMATED 35 x 15 = 525, a bed 7x softer, and the near
    # line goes OVER even capped — both struts bear (147 / 176 lb) and still do not save it.
    for name, (demand, ratio) in {"house near-line plan flexure": (99_103.3, 1.1679),
                                  "house slab-edge peak bearing": (22.3759, 1.4917)}.items():
        assert _state(record, name).demand == pytest.approx(demand, rel=5e-4), name
        assert _state(record, name).ratio == pytest.approx(ratio, abs=6e-4), name
    assert "ESTIMATED" in _state(record, "house near-line plan flexure").citation
    assert record.status is Status.OVER and record.missing == ()
    # Uncapped, the same fallback reads OVER — the row is graded, not silently dropped.
    uncapped = _compute_with(ctx, monkeypatch, compliant=None)["TB-SG-W1"]
    edge = _state(uncapped, "house slab-edge bearing")
    assert edge.ratio == pytest.approx(40_497.2 / 22_680.0, rel=1e-3)
    assert uncapped.status is Status.OVER and uncapped.missing == ()


def test_the_sheets_sustained_load_rule_is_graded_and_foamular_400_fails_it(
        ctx, monkeypatch) -> None:
    """§11k-§11l: the 1/3 rule is a limit state. On FOAMULAR 400 (basis 7's board) even the
    capped 22,155 lb reads 1.099 OVER at the 17'-0" court (1.173 at 19'-0"); FOAMULAR 1000
    reads 0.440."""
    from typehaus.engineering import thermal_break as tb

    slab, path = _with_slab_break(ctx, psi=40.0, modulus_psi=1800.0)
    real = path.house_slab
    monkeypatch.setattr(path, "house_slab",
                        lambda c, f: (slab, real(c, f)[1]) if real(c, f) else None)
    record = {r.key: r for r in tb.compute(ctx)}["TB-SG-W1"]
    state = _state(record, "house slab-edge sustained load")
    assert state.ratio == pytest.approx(22_155.0 / (0.3333 * 40.0 * 1_512.0), rel=1e-4)
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
    assert board.compliant is None, "uncapped is the spring the foam's own E sets"
    from typehaus.model.structure import CompliantLayer

    capped = board.model_copy(update={"compliant": CompliantLayer(
        material="epdm_sponge", thickness=inch(0.5), max_psi=3.5, at_strain=0.25,
        source="sheet")})
    assert IsolationBoard.model_validate(capped.model_dump()) == capped


def test_site_inputs_carry_their_provenance() -> None:
    from typehaus.model import ConcreteServiceTemperature, SubgradeModulus

    presumed = SubgradeModulus(k_v_pci=88.4, provenance="presumed", source="Bowles T9-1",
                               basis="table row")
    assert SubgradeModulus.model_validate(presumed.model_dump()) == presumed
    temps = ConcreteServiceTemperature(max_f=80.0, min_f=0.0, source="AASHTO T3.12.2.1.1-1",
                                       basis="published row", placement_min_f=50.0)
    assert ConcreteServiceTemperature.model_validate(temps.model_dump()) == temps
    assert temps.provenance == "published"


def test_the_near_line_floats_on_the_slab_edge(records) -> None:
    """§11m.1: the end chains are struts, the x = 18' line (gapped at D-B-GYM) is not, and at
    the cap the line's ends lift off both struts — the slab edge carries it all."""
    cite = _state(records["TB-SG-W1"], "house near-line plan flexure").citation
    assert "FT-B-W2+FT-B-W1" in cite and "FT-B-E1+FT-B-E2" in cite
    assert "FT-B-CS" not in cite
    assert "none bear" in cite and "E 3,700 x 3.5\" / 1.5\"" in cite


def test_the_line_solver_is_hetenyi_far_from_its_ends() -> None:
    """An 800" beam, P at mid: M = P/(4λ), v = Pλ/(2k) (Hetényi's infinite beam)."""
    from typehaus.engineering.thermal_break_line import solve

    ei, k, p = 2.1496e10, 8_633.3, 2_000.0
    lam = (k / (4.0 * ei)) ** 0.25
    xs = sorted({i * 0.5 for i in range(1601)} - {400.0} | {399.999, 400.001})
    mid = xs.index(399.999)
    q = [p / 0.002 if e == mid else 0.0 for e in range(len(xs) - 1)]
    v, moment, shear = solve(xs, ei, [k] * (len(xs) - 1), {}, q)
    assert moment == pytest.approx(p / (4.0 * lam), rel=2e-3)
    assert v[mid] == pytest.approx(p * lam / (2.0 * k), rel=2e-3)
    # Never under; over by about the bed's load on half an element (4.5 lb here).
    assert p / 2.0 <= shear <= p / 2.0 * 1.01


def test_no_bar_crosses_the_court_side_joint(records) -> None:
    """§11m.2: 6 #4 in each braced run, and none across W1|W2 / E1|E2 — graded plain there."""
    record = records["TB-SG-W1"]
    assert _input(record, "winter_tension_steel") == pytest.approx(1.20)
    assert _input(record, "winter_joint_section") == pytest.approx(840.0)
    assert any(n.startswith("WINTER JOINT") and "-132.0" in n for n in record.notes)
