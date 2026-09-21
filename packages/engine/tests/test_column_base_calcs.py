"""``engineering/column_base.py`` against ``notes/entry_column_base_fixity.md``.

The note is hand-worked in a separate pass and this module reproduces its arithmetic — the
iteration in §3 term by term, and §4's table of verdicts. A calc that only agrees with
itself is not verified.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.column_base import ISOLATED_POLE_FACTOR, KIND
from typehaus.engineering.item import Status
from typehaus.engineering.pole_embedment import (
    PIVOT_RATIO_BAND,
    effective_width_ft,
    required_embedment_ft,
    required_embedment_stepped_ft,
)

#: §4's table, basis 4: ``(shaft ft, pole ft, B ft, needs at S1, needs at 2 S1, status)``.
#:
#: ** THE CAPACITY IS THE POLE SINCE 2026-09-20 — SHAFT PLUS PAD, GRADE TO PAD BOTTOM. ** The
#: pad is cast with the shaft and its dowels develop in it, so it turns with the shaft (§9).
#: Every verdict moved and almost none of it through the pad's WIDTH (b_eff 1.006-1.070);
#: it is the datum. Canopy 0.96 -> 0.85, landing W/E 0.73 -> 0.62, and the garage-side
#: landing pair stopped straddling §1806.3.4 — 0.96/0.98 on Table 1806.2's own S1 — so the
#: owner's isolated-pole claim was withdrawn (§6e).
#:
#: ** THE FOUR LANDING ROWS ARE WORKED ARITHMETIC ONLY SINCE 2026-09-21. ** The landing is
#: tied to the garage stem (`north_entry_piers.md` §10), its piers lean, and `column_base`
#: no longer enumerates them. `_WORKED` keeps §9e's rows for the pure-function tests;
#: `_ORACLE` is what the landed house must still publish.
_WORKED = {
    "PT-BW-RE": (7.33, 8.33, 1.5, 7.06, 5.36, Status.OK),
    "PT-BW-RNE": (7.33, 8.33, 2.0, 7.04, 5.33, Status.OK),
    "PT-BW-W": (6.12, 7.12, 1.5, 4.39, 3.30, Status.OK),
    "PT-BW-E": (6.12, 7.12, 1.5, 4.39, 3.30, Status.OK),
    "PT-BW-GW": (3.50, 4.50, 2.0, 4.33, 3.21, Status.OK),
    "PT-BW-GE": (3.50, 4.50, 1.5, 4.39, 3.30, Status.OK),
}
_ORACLE = {tag: _WORKED[tag] for tag in ("PT-BW-RE", "PT-BW-RNE")}

#: The columns that claim IBC §1806.3.4's doubling: NONE since basis 4. The mechanism and its
#: two refusals are still tested below; the house simply no longer needs it.
_CLAIMS_THE_DOUBLING: frozenset[str] = frozenset()

#: §2's demand table and §3's iteration: ``(P lb, h ft)``. One entry for the two canopy
#: columns, because §6a made them identical — see the note above.
_DEMAND = {
    "PT-BW-RE": (496.1, 7.489),
    "PT-BW-RNE": (496.1, 7.489),
    "landing": (200.0, 4.54),
}

#: IBC Table 1806.2 class 4 (GM) — the site's own declared group.
_S1_PSF_PER_FT = 150.0


@pytest.mark.parametrize("case,expected", [("PT-BW-RE", 7.07), ("PT-BW-RNE", 7.07),
                                           ("landing", 4.45)])
def test_the_iteration_reproduces_the_note(case, expected) -> None:
    """§3, at the table's own lateral bearing.

    The pair ``(d, S1)`` is circular — §1807.3.2.1 reads S1 at one third the embedment — so
    the note iterates and so does the code. Both have to land on the same fixed point.
    """
    shear, height = _DEMAND[case]
    assert required_embedment_ft(shear, height, 1.0, _S1_PSF_PER_FT) == pytest.approx(
        expected, abs=0.01)


@pytest.mark.parametrize("case,expected", [("PT-BW-RE", 5.40), ("PT-BW-RNE", 5.40),
                                           ("landing", 3.39)])
def test_the_isolated_pole_double_reproduces_the_note(case, expected) -> None:
    """§3's second block — IBC §1806.3.4, the upper end of the judgement band."""
    shear, height = _DEMAND[case]
    assert required_embedment_ft(
        shear, height, 1.0, _S1_PSF_PER_FT * ISOLATED_POLE_FACTOR) == pytest.approx(
            expected, abs=0.01)


def test_a_deeper_pole_needs_more_not_less() -> None:
    """The formula's monotonicity, which a fixed-point iteration can silently lose.

    More shear, or the same shear higher up, needs more embedment; a wider shaft or stiffer
    soil needs less. A solver that converged on the wrong root would still return a number.
    """
    base = required_embedment_ft(613.0, 7.70, 1.0, _S1_PSF_PER_FT)
    assert required_embedment_ft(1226.0, 7.70, 1.0, _S1_PSF_PER_FT) > base
    assert required_embedment_ft(613.0, 15.0, 1.0, _S1_PSF_PER_FT) > base
    assert required_embedment_ft(613.0, 7.70, 2.0, _S1_PSF_PER_FT) < base
    assert required_embedment_ft(613.0, 7.70, 1.0, 2 * _S1_PSF_PER_FT) < base
    assert required_embedment_ft(0.0, 7.70, 1.0, _S1_PSF_PER_FT) == 0.0


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_record_reproduces_the_notes_verdict(tag, catlin_ctx) -> None:
    """§4's table, on the landed house."""
    shaft, pole, width, needs, needs_doubled, status = _ORACLE[tag]
    record = catlin_ctx.engineering[f"{KIND}/{tag}"]
    assert record.status is status, record.summary
    assert not record.missing, record.missing
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["shaft_embedment"] == pytest.approx(shaft, abs=0.01)
    assert inputs["embedment"] == pytest.approx(pole, abs=0.01)
    assert inputs["pad_projected_width"] == pytest.approx(width, abs=0.01)
    assert inputs["pivot_ratio"] == pytest.approx(PIVOT_RATIO_BAND[0], abs=1e-4)

    state = next(s for s in record.limit_states if s.name.startswith("embedment"))
    assert state.capacity == pytest.approx(pole, abs=0.01)
    assert state.demand == pytest.approx(needs, abs=0.01)
    if tag in _CLAIMS_THE_DOUBLING:
        assert "CLAIMED BY THIS HOUSE" in state.citation
        return
    # Where nothing is claimed, the verdict is published only because both ends agreed.
    assert (needs <= pole) == (needs_doubled <= pole)
    assert "is not claimed" in state.citation
    assert "credited as part of the pole" in state.citation


def test_h_is_measured_off_the_shaft_and_the_capacity_is_the_pole(catlin_ctx) -> None:
    """§9d's trap. The arm runs from the pad TOP, so `h` takes the SHAFT's buried length off
    it; the capacity is the TOTAL. Collapse the two and `h` drops a foot on every column."""
    from typehaus.engineering.roof_moment import base_shear_of

    for tag in _ORACLE:
        inputs = {q.name: q.value for q in catlin_ctx.engineering[f"{KIND}/{tag}"].inputs}
        _shear, arm = base_shear_of(tag)
        assert inputs["shear_height_above_grade"] == pytest.approx(
            arm - inputs["shaft_embedment"], abs=1e-9), tag
        assert inputs["embedment"] - inputs["shaft_embedment"] == pytest.approx(1.0), tag


def test_the_pad_is_reported_as_not_being_the_mechanism(catlin_ctx) -> None:
    """§8, and the reason it is a NOTE on this house and not a limit state.

    An embedded shaft and a spread base are alternative paths for one moment. `PD-BW-RE`
    does not claim `resists_base_moment`, so the spread arithmetic is worked and PRINTED —
    the resultant 1.25' off the footprint centroid against a 0.42' kern, i.e. the base would
    lift at one edge before it did anything about the moment — and the embedment is what is
    graded. Grading both would count one moment twice.
    """
    record = catlin_ctx.engineering[f"{KIND}/PT-BW-RE"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["eccentricity"] == pytest.approx(1.25, abs=0.02)
    assert any("NOT WHAT MAKES THIS COLUMN FIXED" in note for note in record.notes)
    assert not [s for s in record.limit_states
                if s.name in ("eccentricity", "bearing", "overturning")]


def test_the_spread_mechanism_is_worked_and_refuses_a_pressure_outside_the_kern() -> None:
    """§8's arithmetic directly, on the same 30" x 18" footprint.

    Outside the kern the base lifts at one edge and the linear distribution stops describing
    the contact, so ``bearing_psf`` comes back ``None`` rather than as an extrapolated
    trapezoid. The factor of safety against tipping is still computable and still reported,
    and the pair passing/failing in opposite directions is exactly why eccentricity is a
    limit state of its own rather than a footnote to bearing.
    """
    from typehaus.engineering.spread_base import Pour, analyse, union_footprint

    pad = Pour(tag="PD-BW-RE", thickness_ft=1.0, outline_ft=(
        (28.75, 36.75), (31.25, 36.75), (31.25, 38.25), (28.75, 38.25)))
    footprint = union_footprint([pad], "x")
    assert footprint is not None
    assert footprint.area_ft2 == pytest.approx(3.75, abs=0.01)
    assert footprint.centroid_ft == pytest.approx(30.0, abs=0.01)
    # A 1.5' x 2.5' rectangle about its own E-W centroid: 1.5 x 2.5^3 / 12.
    assert footprint.inertia_ft4 == pytest.approx(1.953, abs=0.002)

    # 5,156 lb on the COLUMN, not 5,719: ``analyse`` weighs the footprint itself and adds
    # it at its own centroid, so handing it the padded figure counts the concrete twice and
    # puts the second copy on the column's lever rather than on its own.
    result = analyse(footprint, 5_156.0, 30.0, 4_940.0, "x")
    assert result is not None
    assert result.total_vertical_lb == pytest.approx(5_156.0 + 562.5, abs=1.0)
    assert result.kern_ft == pytest.approx(2.5 / 6.0, abs=0.005)
    assert result.eccentricity_ft > result.kern_ft
    assert result.bearing_psf is None, "outside the kern no linear pressure describes it"
    assert result.fs_overturning == pytest.approx(1.45, abs=0.02)


def test_a_pour_that_is_not_concrete_cannot_be_cast_with_anything() -> None:
    """§6f, as a guard rather than a paragraph.

    catlin retyped nine garage strip footings to IRC R403.5 crushed stone on 2026-09-15,
    five days after three pier pads declared they were cast monolithically with them. A
    union that silently dropped the stone would have credited a smaller footprint without
    saying so; one that included it would have credited concrete that is not there.
    """
    from typehaus.engineering.spread_base import Pour, union_footprint

    pad = Pour(tag="PD", thickness_ft=1.0, outline_ft=(
        (0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)))
    stone = Pour(tag="FT", thickness_ft=0.667, castable=False, outline_ft=(
        (1.0, 1.0), (10.0, 1.0), (10.0, 2.667), (1.0, 2.667)))
    assert union_footprint([pad, stone], "y") is None
    assert union_footprint([pad], "y") is not None


def test_two_pours_that_do_not_touch_are_not_one_footing() -> None:
    """A combined footing is one body. Two that share no edge share no section modulus."""
    from typehaus.engineering.spread_base import Pour, union_footprint

    near = Pour(tag="A", thickness_ft=1.0, outline_ft=(
        (0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)))
    far = Pour(tag="B", thickness_ft=1.0, outline_ft=(
        (9.0, 0.0), (11.0, 0.0), (11.0, 2.0), (9.0, 2.0)))
    assert union_footprint([near, far], "x") is None


def test_a_column_on_a_wall_raises_no_item(catlin_ctx) -> None:
    """One question, one item. The balcony's four pillars are doweled into `W-SG-W1`/`-E1`
    and `structural.foundation` already raises `column_support/<wall>` for that joint."""
    keys = {k for k in catlin_ctx.engineering if k.startswith(f"{KIND}/")}
    assert keys == {f"{KIND}/{tag}" for tag in _ORACLE}
    assert not [k for k in keys if "PT-SG-" in k]


# --- the §1806.3.4 claim is GRADED, which means it can be refused --------------------------
#
# A claim that makes a demand smaller has to be graded or it is not a claim, and these are
# the two refusals that make that sentence true. Both report INCOMPLETE naming the reason
# rather than being silently ignored: an authored claim this module cannot honour is a defect
# in the house, and "the doubling was quietly dropped" is the one outcome nobody could act on.


def _pier(**overrides):
    """A minimal ``_Pier`` for the claim reader. Only the fields ``_pole_claim`` reads matter."""
    from typehaus.engineering.pier_basis import _Pier

    base = dict(
        tag="PT-X", diameter_in=12.0, round_section=True, height_in=60.0,
        tributary_ft2=0.0, carried_dead_lb=0.0, footing_tag=None,
        shared_wall_footing=False, lateral_system=True,
        wind_base_moment_lb_ft=0.0, guard_base_moment_lb_ft=900.0, moment_basis="",
        footing_width_in=24.0, footing_depth_in=12.0,
    )
    base.update(overrides)
    return _Pier(**base)


class _StubPlan:
    def __init__(self, post):
        self._post = post

    def by_tag(self, tag):
        return self._post if tag == getattr(self._post, "tag", None) else None


class _StubCtx:
    def __init__(self, post):
        self.plan = _StubPlan(post)


def test_a_claim_with_no_basis_is_refused() -> None:
    """The stale-declaration failure a bare bool has, refused in as many words.

    ``isolated_pole_basis`` is prose precisely so a reader can tell whether it is still true
    of the structure it was written about. Authored empty it carries nothing to check, so it
    buys nothing — and it must say that out loud rather than halve a required depth.
    """
    from typehaus.engineering.column_base import _pole_claim
    from typehaus.model.structure import Post
    from typehaus.quantities import pt

    post = Post(uid="XXXXXXXXXX", tag="PT-X", position=pt(0, 0), isolated_pole_basis="   ")
    basis, refusal = _pole_claim(_StubCtx(post), _pier())
    assert basis is None
    assert refusal is not None and "isolated_pole_basis" in refusal
    assert "stale declaration" in refusal


def test_a_sustained_lateral_case_refuses_the_claim() -> None:
    """§1806.3.4's own words: the doubling is for motion "due to SHORT-TERM lateral loads".

    Wind is short-term by definition and an R301.5 guard push is a person leaning on a rail;
    a case that never goes away is neither, and half an inch of grade movement under it does
    not recover. No such case exists on a ``_Pier`` today, which is exactly why the guard is
    written as a SCAN over the base-moment fields rather than a list of the two that do: the
    day somebody adds a third, the claim is refused until they decide it belongs.
    """
    import dataclasses

    from typehaus.engineering.column_base import _pole_claim, _sustained_lateral_cases
    from typehaus.engineering.pier_basis import _Pier
    from typehaus.model.structure import Post
    from typehaus.quantities import pt

    @dataclasses.dataclass(frozen=True)
    class _SurchargedPier(_Pier):
        surcharge_base_moment_lb_ft: float = 0.0

    assert _sustained_lateral_cases(_pier()) == ()
    quiet = _SurchargedPier(**dataclasses.asdict(_pier()))
    assert _sustained_lateral_cases(quiet) == ()
    loaded = dataclasses.replace(quiet, surcharge_base_moment_lb_ft=300.0)
    assert _sustained_lateral_cases(loaded) == ("surcharge_base_moment_lb_ft",)

    post = Post(uid="XXXXXXXXXX", tag="PT-X", position=pt(0, 0),
                isolated_pole_basis="the owner says so")
    basis, refusal = _pole_claim(_StubCtx(post), loaded)
    assert basis is None
    assert refusal is not None and "SHORT-TERM" in refusal
    assert "surcharge_base_moment_lb_ft" in refusal
    # And the same pier without the sustained case honours it, so the refusal is about the
    # LOAD and not about the claim.
    assert _pole_claim(_StubCtx(post), quiet) == ("the owner says so", None)


def test_no_column_claims_the_doubling(catlin_ctx) -> None:
    """§6a's plane was chosen so the canopy would not need §1806.3.4, and §6e WITHDREW the
    landing pair's claim once basis 4 made it buy nothing. A claim left where it does no work
    is a stale declaration, so no column may carry one."""
    for tag in _ORACLE:
        record = catlin_ctx.engineering[f"{KIND}/{tag}"]
        assert any("is NOT claimed" in note for note in record.notes), tag
        state = next(s for s in record.limit_states if s.name.startswith("embedment"))
        assert "CLAIMED BY THIS HOUSE" not in state.citation, tag
        inputs = {q.name: q.value for q in record.inputs}
        assert inputs["isolated_pole_doubling"] == 0.0, tag
        assert getattr(catlin_ctx.plan.by_tag(tag), "isolated_pole_basis", None) is None, tag


# --- §9: the pad as part of the pole --------------------------------------------------------


def test_a_constant_width_profile_reproduces_the_code_formula_exactly() -> None:
    """§9c's oracle property. With ``B = b`` the pad's term is ZERO, not small, so the stepped
    solve IS Eq. 18-1 for any pivot ratio. Equality, not approx: the reduction is algebraic."""
    for shear, height, width, lateral in ((496.1, 7.489, 1.0, 150.0), (200.0, 4.54, 1.0, 300.0),
                                         (613.0, 7.70, 1.5, 150.0)):
        code = required_embedment_ft(shear, height, width, lateral)
        for pivot in (*PIVOT_RATIO_BAND, 0.5, 0.85, 1.0):
            assert effective_width_ft(code, width, width, 1.0, pivot) == width
            assert required_embedment_stepped_ft(
                shear, height, width, width, 1.0, lateral, pivot) == code


def test_the_pivot_band_is_what_eq_18_1_implies() -> None:
    """§9b: the 4.36 term implies 0.91743, the 2.34 term 0.92450."""
    assert PIVOT_RATIO_BAND[0] == pytest.approx(0.91743, abs=1e-5)
    assert PIVOT_RATIO_BAND[1] == pytest.approx(0.92450, abs=1e-5)


def test_one_effective_width_by_hand() -> None:
    """§9c: `PT-BW-GW` at d 4.33', γ 0.91743 — F 0.0700, b_eff 1.070'."""
    assert effective_width_ft(4.33, 1.0, 2.0, 1.0, PIVOT_RATIO_BAND[0]) == pytest.approx(
        1.0700, abs=0.0005)
    # A pivot above the pad top credits nothing: §9e's canopy at γ 0.85.
    assert effective_width_ft(7.072, 1.0, 1.5, 1.0, 0.85) == 1.0


@pytest.mark.parametrize("case,width,pivot,expected", [
    ("landing", 2.0, 0, 4.330), ("landing", 2.0, 1, 4.320), ("landing", 1.5, 0, 4.389),
    ("PT-BW-RE", 1.5, 0, 7.056), ("PT-BW-RNE", 2.0, 0, 7.039),
])
def test_the_stepped_iteration_reproduces_the_note(case, width, pivot, expected) -> None:
    """§9d-e, at S1: `PT-BW-GW` (2.0') at both ends, `-GE` (1.5'), and the canopy pair."""
    shear, height = _DEMAND[case]
    assert required_embedment_stepped_ft(
        shear, height, 1.0, width, 1.0, _S1_PSF_PER_FT, PIVOT_RATIO_BAND[pivot]
    ) == pytest.approx(expected, abs=0.002)


@pytest.mark.parametrize("tag", sorted(_WORKED))
def test_no_verdict_flips_across_the_wider_pivot_band(tag) -> None:
    """§9e: γ in [0.85, 1.00] moves no verdict — the pad's width never decides one here."""
    _shaft, pole, width, *_ = _WORKED[tag]
    shear, height = _DEMAND.get(tag, _DEMAND["landing"])
    for pivot in (0.85, *PIVOT_RATIO_BAND, 1.0):
        needs = required_embedment_stepped_ft(shear, height, 1.0, width, 1.0, _S1_PSF_PER_FT,
                                              pivot)
        assert needs <= pole, (tag, pivot, needs)


def test_the_pad_credit_is_refused_without_the_dowel_anchorage(catlin_ctx, monkeypatch) -> None:
    """§6g: the pad is part of the pole only because the dowels develop in it. Over or
    ungraded, the credit is refused and the shaft is graded alone — never silently kept."""
    from typehaus.engineering import deck_post
    from typehaus.engineering.column_base import _pad_of, _pole
    from typehaus.engineering.item import LimitState
    from typehaus.engineering.pier_basis import cast_piers

    pier = next(p for p in cast_piers(catlin_ctx) if p.tag == "PT-BW-GW")
    pad = _pad_of(catlin_ctx, pier)
    assert _pole(catlin_ctx, pier, pad, 1.0).credited

    monkeypatch.setattr(deck_post, "_dowel_anchorage", lambda *_a: LimitState(
        "dowel anchorage into the base", 10.0, 8.0, "in", "stub"))
    refused = _pole(catlin_ctx, pier, pad, 1.0)
    assert not refused.credited and "do not develop" in (refused.refusal or "")
    assert refused.needs(200.0, 4.54, _S1_PSF_PER_FT) == (
        required_embedment_ft(200.0, 4.54, 1.0, _S1_PSF_PER_FT),) * 2

    monkeypatch.setattr(deck_post, "_dowel_anchorage", lambda *_a: None)
    assert "no dowel anchorage" in (_pole(catlin_ctx, pier, pad, 1.0).refusal or "")
