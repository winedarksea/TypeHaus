"""``DuctRun.drains`` -> a ``drain_tee`` part, and ``mep.duct_drainage`` (M1-114)."""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.mep.duct_drainage import _low_plateaus, duct_drainage
from typehaus.findings import Result

_IN = 0.0254


def test_low_plateaus_find_sags_and_low_ends_but_not_crowns() -> None:
    # port low end, crown, sag on a level pair, riser up to the hood, hood end falling
    z = [0.0, 1.0, 1.0, 0.5, 0.2, 0.2, 3.0, 2.9]
    assert _low_plateaus(z) == [(0, 0), (4, 5), (7, 7)]
    assert _low_plateaus([1.0, 1.0, 1.0]) == []


def test_ea_drains_at_its_riser_foot_through_a_capped_tee(catlin_model_ro) -> None:
    """The tap stands one stamped 8" elbow take-off (1.0 D) east of the foot, on the
    level leg's invert line, and bills the drain's own product."""
    duct = next(d for d in catlin_model_ro.ducts if d.tag == "DU-ERV-EA")
    taps = [p for p in catlin_model_ro.duct_parts
            if p.kind == "drain_tee" and p.run_tag == "DU-ERV-EA"]
    assert [(t.product_ref, t.size, t.branch, t.other) for t in taps] == [
        ("PROD-DUCT-DRAIN-TAP-8", "8in", "0.75in", None)]
    x, y, z = (c / _IN for c in taps[0].point)
    assert (x, y) == pytest.approx((24.625 + 8.0, 418.5), abs=1e-3)
    foot = duct.z_m[8] / _IN
    assert z == pytest.approx(foot + 8.0 * 0.125 / 12.0, abs=1e-3)

    findings = duct_drainage(check_context(model=catlin_model_ro))
    assert [f.result for f in findings] == [Result.PASS]
    assert "1 capped tee(s)" in findings[0].message
