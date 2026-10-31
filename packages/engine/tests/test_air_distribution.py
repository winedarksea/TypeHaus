"""The 2026-10-31 air-distribution additions, one focused assertion each, on catlin.

Hood losses in the static budget are pinned by ``test_erv_static_oracle.py``; this covers
the rest: the rectangular gauge band, the duct wall seal and its billing, the duct-vs-own-RO
fit, the one-collar port check, the wrap solid stopping at the sheathing, and the terminal
neck boxes.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus import DuctProductType, inch
from typehaus.checks.mep.duct_connectivity import duct_connectivity
from typehaus.checks.mep.duct_penetrations import duct_penetration_fit
from typehaus.checks.mep.terminal_necks import terminal_neck_fit
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_sizing import rectangular_row
from typehaus.takeoff.mep import duct_fitting_takeoff, duct_takeoff, sleeve_takeoff


def test_a_rectangular_row_is_a_gauge_band_and_must_say_so(catlin_plan) -> None:
    with pytest.raises(ValueError, match="gauge band"):
        DuctProductType(tag="X", name="x", material="galvanized", section="rectangular")
    # IRC M1601.1.1: an 18x8 trunk takes the band to 18", a 10x6 the one to 10".
    library = catlin_plan.library
    assert rectangular_row(library, "galvanized", inch(18).meters, inch(8).meters).gauge == 26
    assert rectangular_row(library, "galvanized", inch(10).meters, inch(6).meters).gauge == 30
    assert rectangular_row(library, None, inch(10).meters, inch(6).meters) is None


def test_the_duct_schedule_prints_the_trunks_gauge(catlin_model_ro) -> None:
    rows = [r for r in duct_takeoff(catlin_model_ro) if "DU-S-HP-SUP" in r["tags"]]
    assert rows and rows[0]["gauge"] == 26


def test_the_hood_legs_wall_seals_fit_and_bill_as_kits(catlin_model_ro) -> None:
    findings = duct_penetration_fit(check_context(model=catlin_model_ro))
    assert findings and all(f.result is Result.PASS for f in findings)
    tags = {f.element_tags for f in findings}
    assert ("DU-ERV-OA", "AO-M-ERV-OA") in tags  # the RO, graded instead of exempted
    assert ("SP-S-ERV-EA-SEAL", "DU-ERV-EA") in tags
    kits = [r for r in duct_fitting_takeoff(catlin_model_ro) if r["fitting"] == "wall-seal-8in"]
    assert sum(r["count"] for r in kits) == 2
    assert not any("SP-S-ERV-EA-SEAL" in r["tags"] for r in sleeve_takeoff(catlin_model_ro))


def test_a_run_on_a_one_collar_hood_of_another_size_fails(catlin_model) -> None:
    hood = next(e for e in catlin_model.plan.all_elements() if e.tag == "EQ-M-ERV-HOOD-OA")
    library = catlin_model.plan.library
    six = next(t for t in library.equipment_types if t.tag == "EQ-T-ERV-HOOD-6")
    assert hood.type_ref == "EQ-T-ERV-HOOD-8"
    # The 2026-09-15..10-31 state: an 8" leg on a 6" hood.
    catlin_model.canvas_objects = [replace(o, type_ref=six.tag) if o.tag == hood.tag else o
                                   for o in catlin_model.canvas_objects]
    failed = [f for f in duct_connectivity(check_context(model=catlin_model))
              if f.result is Result.FAIL]
    assert any('8" run on its 6" collar' in f.message for f in failed)


def test_the_wrap_is_drawn_and_stops_at_the_sheathing(catlin_model_ro) -> None:
    wrap = next(s for s in catlin_model_ro.solids if s.tag == "DU-ERV-OA-WRAP")
    assert wrap.category == "insulation_wrap"
    # W-M-N3B's sheathing room face is y=35'-11 1/2"; the bare duct runs on to the hood.
    assert max(y for _, y in wrap.outline) / M_PER_IN <= 431.5 + 0.01
    duct = next(s for s in catlin_model_ro.solids if s.tag == "DU-ERV-OA-RUN")
    assert max(y for _, y in duct.outline) / M_PER_IN > 436.0


def test_every_typed_neck_is_placed_and_clear(catlin_model_ro) -> None:
    findings = terminal_neck_fit(check_context(model=catlin_model_ro))
    assert len(findings) >= 30
    assert all(f.result is Result.PASS for f in findings), [
        f.message for f in findings if f.result is not Result.PASS]
