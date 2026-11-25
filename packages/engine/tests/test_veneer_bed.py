"""``structural.veneer_bed_bearing`` against notes/sunken_garden_veneer_beam.md §6l and
``scratch/L3/hand.py``: W-SG-BRKBM's 12" bed under a wythe 4.19" off its centre (F-04)."""

from __future__ import annotations

import pytest

from typehaus.checks.structural import veneer_bed
from typehaus.findings import Result


def test_the_resultant_sits_outside_the_kern_and_the_peak_is_graded(catlin_brick_ctx) -> None:
    (finding,) = veneer_bed.veneer_bed_bearing(catlin_brick_ctx)
    assert finding.result is Result.PASS
    msg = finding.message
    # 268.9 plf of brick + 221.6 plf of beam = 490.5 plf, 2.30" off the 12" centre (kern 2.00").
    assert "W-B-BRICK 268.9 + beam 221.6 = 490.5 plf" in msg
    assert "resultant 2.30\"" in msg and "kern 2.00\"" in msg
    # The veneer's wind base shear, 13.3 plf at the beam top 17.75" over the bed (236 lb-in/ft),
    # moves it 0.48" to 2.78": partial contact over 9.67", peak 1,217 psf of 2,000 (R401.4.1).
    assert "wind base shear 13.3 plf x 17.75\" = 236 lb-in/ft moves it 0.48\"" in msg
    assert "= 2.78\" off" in msg and "partial contact over 9.67\" of 12\"" in msg
    assert "peak 1,217 psf" in msg and "(0.61)" in msg


def test_widening_the_stone_does_not_widen_the_contact() -> None:
    """§6l: the beam's own bottom is the contact. Hand numbers for the rejected fixes."""
    brick, hb = 268.86, 17.75

    def peak(beam_w: float) -> float:
        own = beam_w * hb * 150 / 144
        centre = -6.0 - beam_w / 2
        res = (brick * -7.8125 + own * centre) / (brick + own)
        e, total = abs(res - centre), brick + own
        return 2 * total / (3 * (beam_w / 2 - e) / 12) if e > beam_w / 6 else total / (beam_w / 12)

    assert peak(12.0) == pytest.approx(1059, abs=2)
    # Stone south of the beam changes nothing; a beam 4" wider south is still outside its kern.
    assert peak(16.0) == pytest.approx(894, abs=2)
