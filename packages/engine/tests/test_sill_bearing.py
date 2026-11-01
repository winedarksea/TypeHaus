"""structural.sill_bearing_on_core: the garage 2x6 sill fails, the flush 2x8 passes."""

from __future__ import annotations

from typehaus.checks.structural.sill_bearing import problems
from typehaus.resolve.sill_bearing import SillBearing, grade

# Inches inward from the sill's outside edge: the ICF core spans 1 7/8" to 7 7/8".
_CORE = (1.875, 7.875)


def _bearing(sill_w: float) -> SillBearing:
    width, on_core, third, band = grade((0.0, sill_w), _CORE)
    return SillBearing(sill_in=width, stud_in=5.5, on_core_in=on_core, core=_CORE,
                       third=third, band=band, sign=1.0)


def test_2x6_sill_fails_and_flush_2x8_passes():
    old, new = _bearing(5.5), _bearing(7.25)
    assert old.on_core_in == 3.625 and problems(old, bolted=False)
    assert new.on_core_in == 5.375 and not problems(new, bolted=True)
    assert new.band == (3.375, 7.25 * 2 / 3)


def test_no_anchor_band_fails_a_bolted_sill():
    # A core too thin for the edge distance leaves no band inside the middle third.
    width, on_core, third, band = grade((0.0, 7.25), (3.0, 5.0))
    sb = SillBearing(width, 5.5, on_core, (3.0, 5.0), third, band, 1.0)
    assert band is None and any("anchor band" in p for p in problems(sb, bolted=True))


def test_garage_sill_in_catlin(catlin_model_report):
    found = [f for f in catlin_model_report.findings
             if f.check_id == "structural.sill_bearing_on_core" and f.element_tags[0] == "W-G-W"]
    assert found and found[0].result.name == "PASS"
