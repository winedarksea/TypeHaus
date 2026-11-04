"""``structural.veneer_cavity_width`` and the ``veneer_anchor`` keys against
notes/sunken_garden_veneer_beam.md §6k: W-B-BRICK's back at -6.0", the studs at +0.5",
the foam at -4.06" — 6.500" to the backing, 1.940" of airspace.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus import veneer_ties
from typehaus.findings import Authority, Result

#: §6k, by hand.
_TO_STUDS_IN = 6.500
_AIRSPACE_IN = 1.940


def _grade(ctx, irc_base):
    from typehaus.checks.structural.veneer_cavity import veneer_cavity_width

    return veneer_cavity_width(replace(ctx, profile=replace(ctx.profile, irc_base=irc_base)))


def test_the_brick_reads_six_and_a_half_inches_to_the_studs(catlin_model_ro) -> None:
    reach = veneer_ties.measure(catlin_model_ro, catlin_model_ro.wall("W-B-BRICK"))
    assert reach.to_structure_in == pytest.approx(_TO_STUDS_IN, abs=1e-3)
    assert reach.airspace_in == pytest.approx(_AIRSPACE_IN, abs=1e-3)
    assert reach.backing in ("W-B-S2-FR", "W-B-S3-FR") and reach.unbacked_in == 0


def test_the_2024_w2_8_row_covers_it_and_prints_the_spacing(catlin_ctx) -> None:
    (finding,) = _grade(catlin_ctx, "2024 IRC")
    assert finding.result is Result.PASS
    assert "W2.8" in finding.message and "6.625\" to the backing" in finding.message
    # ASD Zone 5 suction 18.2 psf (§6k) is under R703.8.4.1's 30 psf: 2.67 sf per tie.
    assert "one tie per 2.67 sf" in finding.message and "32\" o.c." in finding.message


def test_the_adopted_2018_table_hands_it_to_veneer_anchor(catlin_ctx) -> None:
    (finding,) = _grade(catlin_ctx, "2018 IRC + MN amendments")
    assert finding.result is Result.UNKNOWN and finding.authority is Authority.ENGINEERED
    assert finding.engineering_item == "veneer_anchor/W-B-BRICK"
    assert "4.5\"" in finding.message


def test_the_veneer_anchor_item_retires_on_the_2024_irc(catlin_model_ro) -> None:
    from typehaus.engineering.deferred import _veneer_anchor_keys
    from typehaus.engineering.registry import EngineeringContext

    def keyed(irc_base):
        return _veneer_anchor_keys(EngineeringContext(
            plan=catlin_model_ro.plan, model=catlin_model_ro, irc_base=irc_base))

    assert keyed("2018 IRC + MN amendments") == ["W-B-BRICK"]
    assert keyed("2024 IRC") == []
    # An edition the table is not transcribed for is never read as covered.
    assert keyed(None) == ["W-B-BRICK"]
