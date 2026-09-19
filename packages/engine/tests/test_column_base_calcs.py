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
_ORACLE = {
    "PT-BW-RE": (6.12, 8.08, 6.15, Status.OVER),
    "PT-BW-RNE": (3.50, 8.08, 6.15, Status.OVER),
    "PT-BW-W": (6.12, 4.45, 3.39, Status.OK),
    "PT-BW-E": (6.12, 4.45, 3.39, Status.OK),
    "PT-BW-GW": (3.50, 4.45, 3.39, Status.INCOMPLETE),
    "PT-BW-GE": (3.50, 4.45, 3.39, Status.INCOMPLETE),
}

#: §2's demand: the canopy pair and the landing four.
_DEMAND = {
    "canopy": (680.0, 7.79),
    "landing": (200.0, 4.54),
}

#: IBC Table 1806.2 class 4 (GM) — the site's own declared group.
_S1_PSF_PER_FT = 150.0


@pytest.mark.parametrize("case,expected", [("canopy", 8.08), ("landing", 4.45)])
def test_the_iteration_reproduces_the_note(case, expected) -> None:
    """§3, at the table's own lateral bearing.

    The pair ``(d, S1)`` is circular — §1807.3.2.1 reads S1 at one third the embedment — so
    the note iterates and so does the code. Both have to land on the same fixed point.
    """
    shear, height = _DEMAND[case]
    assert required_embedment_ft(shear, height, 1.0, _S1_PSF_PER_FT) == pytest.approx(
        expected, abs=0.01)


@pytest.mark.parametrize("case,expected", [("canopy", 6.15), ("landing", 3.39)])
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
    base = required_embedment_ft(680.0, 7.79, 1.0, _S1_PSF_PER_FT)
    assert required_embedment_ft(1360.0, 7.79, 1.0, _S1_PSF_PER_FT) > base
    assert required_embedment_ft(680.0, 15.0, 1.0, _S1_PSF_PER_FT) > base
    assert required_embedment_ft(680.0, 7.79, 2.0, _S1_PSF_PER_FT) < base
    assert required_embedment_ft(680.0, 7.79, 1.0, 2 * _S1_PSF_PER_FT) < base
    assert required_embedment_ft(0.0, 7.79, 1.0, _S1_PSF_PER_FT) == 0.0


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
    """§5, and the reason it is a NOTE and not a limit state.

    An embedded shaft and a spread pad are alternative paths for one moment. `PT-BW-RE`'s
    pad, taken alone, would have no contact at all — which is the arithmetic saying the
    shaft carries the moment, not a failure of the pad. Grading it would report a FAIL about
    a mechanism the structure does not use.
    """
    record = catlin_ctx.engineering[f"{KIND}/PT-BW-RE"]
    inputs = {q.name: q.value for q in record.inputs}
    least_ft = inputs["base_least_dimension"]
    assert inputs["eccentricity"] > least_ft / 2.0, "past the half-width: no contact"
    assert any("NOT WHAT MAKES THIS COLUMN FIXED" in note for note in record.notes)
    assert not [s for s in record.limit_states if "contact" in s.name]


def test_a_column_on_a_wall_raises_no_item(catlin_ctx) -> None:
    """One question, one item. The balcony's four pillars are doweled into `W-SG-W1`/`-E1`
    and `structural.foundation` already raises `column_support/<wall>` for that joint."""
    keys = {k for k in catlin_ctx.engineering if k.startswith(f"{KIND}/")}
    assert keys == {f"{KIND}/{tag}" for tag in _ORACLE}
    assert not [k for k in keys if "PT-SG-" in k]
