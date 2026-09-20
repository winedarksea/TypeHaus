"""``engineering/column_base.py`` against ``notes/entry_column_base_fixity.md``.

The note is hand-worked in a separate pass and this module reproduces its arithmetic — the
iteration in §3 term by term, and §4's table of verdicts. A calc that only agrees with
itself is not verified.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.column_base import (
    ISOLATED_POLE_FACTOR,
    KIND,
    required_embedment_ft,
)
from typehaus.engineering.item import Status

#: §4's table. ``(embedment ft, needs at S1, needs at 2 S1, status)``.
#:
#: ** THE TWO CANOPY ROWS MOVED TWICE, AND THE SECOND TIME THEY MOVED BACK TOGETHER. **
#: §7's shear split (2026-09-19) took `PT-BW-RE` from 8.08' of required embedment to 6.25' and
#: `PT-BW-RNE` from 8.08' to 7.74' — they stopped sharing a demand, because a relative-rigidity
#: split gives the SHORT column the larger share. §6a (2026-09-20) put both bases on one plane
#: at -10'-2", which makes them the same column again: equal shaft, equal `3EI/h³`, 50% each of
#: the governing E-W case, 7.07' needed against 7.33'. Both publish at the table's own S1 with
#: §1806.3.4's doubling unclaimed. The four landing columns carry a guard load delivered at a
#: rail rather than at a diaphragm, so neither revision reaches them.
_ORACLE = {
    "PT-BW-RE": (7.33, 7.07, 5.40, Status.OK),
    "PT-BW-RNE": (7.33, 7.07, 5.40, Status.OK),
    "PT-BW-W": (6.12, 4.45, 3.39, Status.OK),
    "PT-BW-E": (6.12, 4.45, 3.39, Status.OK),
    "PT-BW-GW": (3.50, 4.45, 3.39, Status.INCOMPLETE),
    "PT-BW-GE": (3.50, 4.45, 3.39, Status.INCOMPLETE),
}

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
    embedment, needs, needs_doubled, status = _ORACLE[tag]
    record = catlin_ctx.engineering[f"{KIND}/{tag}"]
    assert record.status is status, record.summary
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["embedment"] == pytest.approx(embedment, abs=0.01)

    if status is Status.INCOMPLETE:
        # The band convention: the two ends straddle the embedment this column has, so the
        # verdict turns on a judgement about the STRUCTURE — whether 1/2" of motion at grade
        # matters — and the record names it instead of picking a side.
        assert needs_doubled < embedment < needs
        assert any("1806.3.4" in text for text in record.missing), record.missing
        assert not [s for s in record.limit_states if s.name.startswith("embedment")]
        return

    state = next(s for s in record.limit_states if s.name.startswith("embedment"))
    assert state.demand == pytest.approx(needs, abs=0.01)
    assert state.capacity == pytest.approx(embedment, abs=0.01)
    # Where the verdict IS published, both ends agreed — which is what makes it publishable.
    assert (needs <= embedment) == (needs_doubled <= embedment)


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
