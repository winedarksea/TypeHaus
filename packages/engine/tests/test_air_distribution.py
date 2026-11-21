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


def test_a_ceiling_collar_takes_its_run_on_a_derived_drop(catlin_model_ro) -> None:
    """DU-M-ERV-R-LIVING is authored level over REG-M-SUP1; the resolver adds the drop onto
    the collar top, ``mep_fittings`` the 90 there. Moved under the collar top, it FAILs."""
    from typehaus.resolve.mep_fittings import fitting_records
    from typehaus.resolve.terminal_drops import collars_by_run

    model = catlin_model_ro
    duct = next(d for d in model.ducts if d.tag == "DU-M-ERV-R-LIVING")
    (_, collar), = collars_by_run(model)[duct.tag]
    x, y, top = collar.x, collar.y, collar.z_top
    assert duct.path[-1] == pytest.approx((x, y))
    assert duct.path[-2] == pytest.approx((x, y))
    assert duct.z_m[-1] == pytest.approx(top)
    assert duct.z_m[-2] - top > 2 * M_PER_IN
    drop = len(duct.path) - 2
    assert any(r.run_tag == duct.tag and r.index == drop and r.angle_deg == pytest.approx(90)
               for r in fitting_records(model))

    sunk = replace(model)
    z = [*duct.z_m[:-2], top - 6 * M_PER_IN]
    sunk.ducts = [replace(d, path=d.path[:-1], z_m=tuple(z)) if d is duct else d
                  for d in model.ducts]
    failed = [f for f in duct_connectivity(check_context(model=sunk))
              if f.result is Result.FAIL and duct.tag in f.element_tags]
    assert failed and "below REG-M-SUP1's collar top" in failed[0].message


def test_a_rectangular_return_neck_takes_a_drop_and_guards_its_section(
        catlin_model_ro) -> None:
    """REG-S-HP-SUITE-RET's 12x12 neck: a rectangular run drawn onto its top is graded
    connected (connectivity, end landing, and register_reach stands aside); another section
    is not. (REG-S-HP-RET was the subject until its box took a side inlet, 2026-11-21.)"""
    from typehaus.checks.mep.register_reach import register_reach
    from typehaus.resolve.duct_terminations import end_landings
    from typehaus.resolve.terminal_drops import collars_by_run, drop_onto_collars

    model = catlin_model_ro
    duct = next(d for d in model.ducts if d.tag == "DU-S-HP-SUITE-RET")
    (reg, neck), = collars_by_run(model)[duct.tag]
    assert (reg, neck.is_round) == ("REG-S-HP-SUITE-RET", False)

    def with_drop(**section):
        at = (neck.x, neck.y)
        run = replace(duct, path=[at, at, *duct.path[1:]],
                      z_m=(neck.z_top, *duct.z_m), **section)
        found = replace(model, ducts=[run if d is duct else d for d in model.ducts])
        ctx = check_context(model=found)
        mine = [f for f in duct_connectivity(ctx) if duct.tag in f.element_tags
                and "start" in f.message]
        reach = [f for f in register_reach(ctx) if reg in f.element_tags]
        lands = next(e for e in end_landings(found) if (e.run_tag, e.index) == (duct.tag, 0))
        return mine, reach, lands

    mine, reach, lands = with_drop(width_m=neck.width, depth_m=neck.depth)
    assert [f.result for f in mine] == [Result.PASS]
    assert "drops onto REG-S-HP-SUITE-RET" in mine[0].message
    assert not reach and (lands.landing, lands.other) == ("terminal", reg)
    flipped, *_ = with_drop(width_m=neck.depth, depth_m=neck.width)  # either orientation
    assert flipped[0].result is Result.PASS
    wrong, *_ = with_drop()  # DU-S-HP-SUITE-RET is 6x4 and the neck 12x12
    assert wrong[0].result is Result.FAIL and "arrives as 6x4 but" in wrong[0].message

    # A level end over the neck gets its drop appended, as a round collar's does.
    path, z = [(neck.x, neck.y), (neck.x + 1.0, neck.y)], [neck.z_top + 0.3] * 2
    drop_onto_collars(model, duct.tag, path, z)
    assert path[0] == (neck.x, neck.y) and z[0] == neck.z_top and len(path) == 3


def test_study_drops_on_the_adjustable_elbow_it_names(catlin_model_ro) -> None:
    """``adjustable_elbows=(6, 9)`` makes those two turns the 4.75" adjustable 90: the 4.76"
    drop onto REG-M-SUP4 fits it, and the radial is the note's hand figure (§10.16, re-worked
    at 10 cfm in §10.20)."""
    from typehaus.checks.mep.erv_static import _duct_drop
    from typehaus.resolve.mep_fittings import fitting_records

    model = catlin_model_ro
    duct = next(d for d in model.ducts if d.tag == "DU-M-ERV-R-STUDY")
    keys = {r.index: (r.order_key, r.adjustable) for r in fitting_records(model)
            if r.run_tag == duct.tag}
    assert keys[6] == keys[9] == ("elbow-adj-90-4in", True)
    assert keys[1] == ("elbow-90-4in", False)
    assert (duct.z_m[-2] - duct.z_m[-1]) / M_PER_IN == pytest.approx(4.7625, abs=0.01)
    leg = _duct_drop(check_context(model=model), duct, 0)
    assert leg.drop_in_wg == pytest.approx(0.004011, abs=2e-6)
