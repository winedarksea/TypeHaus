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


def test_ea_drains_back_to_a_tee_by_the_machine(catlin_model_ro) -> None:
    """EA falls back from its riser foot (2026-11-21) to a tee 8 1/8" north of the kit lead's
    elbow. That vertex is a grade break, not a turn, so the tap stands on it (not one elbow
    take-off back, inside the lead's 90), bills the drain's own product, and its line starts
    there."""
    duct = next(d for d in catlin_model_ro.ducts if d.tag == "DU-ERV-EA")
    taps = [p for p in catlin_model_ro.duct_parts
            if p.kind == "drain_tee" and p.run_tag == "DU-ERV-EA"]
    assert [(t.product_ref, t.size, t.branch, t.other) for t in taps] == [
        ("PROD-DUCT-DRAIN-TAP-8", "8in", "0.75in", "PR-B-ERV-EA-DRAIN")]
    x, y, z = (c / _IN for c in taps[0].point)
    assert (x, y) == pytest.approx((96.625, 315.5), abs=1e-3)
    assert z == pytest.approx(duct.z_m[2] / _IN, abs=1e-3)
    assert max(duct.z_m[2:7]) == duct.z_m[6]  # the riser foot is the leg's high point

    findings = duct_drainage(check_context(model=catlin_model_ro))
    assert [f.result for f in findings] == [Result.PASS]
    assert "capped" not in findings[0].message
