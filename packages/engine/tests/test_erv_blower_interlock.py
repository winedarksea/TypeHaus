"""``mep.erv_blower_interlock`` and the two verdicts that read it.

EQ-B-ERV feeds EQ-S-ERV-MIX, the return plenum of EQ-S-HP1-AH, so its fresh air reaches the
second storey only while that blower turns. The coupling is derived from the ducts; the
interlock is authored. Only the PLAN is edited below (the field touches no geometry), so
every case grades against the one resolved model.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.code.mn_residential.ventilation import whole_house_ventilation
from typehaus.checks.mep.erv_interlock import couplings, erv_blower_interlock
from typehaus.checks.mep.hvac import ventilation_distribution
from typehaus.findings import Result
from typehaus.model.enums import EquipmentKind


def _edit(plan, tag: str, **update):
    merged = {storey: tuple(el.model_copy(update=update) if el.tag == tag else el
                            for el in items)
              for storey, items in plan.elements.items()}
    return plan.model_copy(update={"elements": merged})


@pytest.fixture(scope="module")
def ctx(catlin_model_ro):
    return check_context(catlin_model_ro.plan, catlin_model_ro)


def _with(ctx, plan):
    return check_context(plan, ctx.model)


def _results(findings) -> set[Result]:
    return {f.result for f in findings}


def test_catlins_erv_is_coupled_to_system_1_by_its_ducts(ctx):
    (coupling,) = couplings(ctx)
    assert coupling.erv == "EQ-B-ERV"
    assert coupling.air_handlers == ("EQ-S-HP1-AH",)


def test_present_interlock_passes_all_three(ctx):
    assert _results(erv_blower_interlock(ctx)) == {Result.PASS}
    assert _results(whole_house_ventilation(ctx)) == {Result.PASS}
    assert Result.UNKNOWN not in _results(ventilation_distribution(ctx))


def test_absent_interlock_is_unknown_not_pass(ctx):
    loose = _with(ctx, _edit(ctx.plan, "EQ-B-ERV", blower_interlock_ref=None))
    (finding,) = erv_blower_interlock(loose)
    assert finding.result is Result.UNKNOWN
    assert "EQ-S-HP1-AH" in finding.message
    (rate,) = whole_house_ventilation(loose)
    assert rate.result is Result.UNKNOWN and "interlock" in rate.message
    # Rooms whose only supply is System 1's ducts lose their PASS; ERV-radial rooms keep it.
    unknown_rooms = {f.element_tags[0] for f in ventilation_distribution(loose)
                     if f.result is Result.UNKNOWN}
    assert "RM-S-BED1" in unknown_rooms


def test_interlock_authored_on_the_air_handler_counts(ctx):
    plan = _edit(ctx.plan, "EQ-B-ERV", blower_interlock_ref=None)
    plan = _edit(plan, "EQ-S-HP1-AH", blower_interlock_ref="EQ-B-ERV")
    assert _results(erv_blower_interlock(_with(ctx, plan))) == {Result.PASS}


def test_a_dangling_interlock_fails(ctx):
    plan = _edit(ctx.plan, "EQ-B-ERV", blower_interlock_ref="EQ-NOPE")
    results = _results(erv_blower_interlock(_with(ctx, plan)))
    assert Result.FAIL in results


def test_an_erv_reaching_no_air_handler_is_not_applicable(ctx):
    # The same ducts, but the machine at the end is a wall head: nothing to ride.
    plan = _edit(ctx.plan, "EQ-S-HP1-AH", kind=EquipmentKind.INDOOR_HEAD)
    plan = _edit(plan, "EQ-B-ERV", blower_interlock_ref=None)
    narrowed = _with(ctx, plan)
    assert _results(erv_blower_interlock(narrowed)) == {Result.NOT_APPLICABLE}
    assert _results(whole_house_ventilation(narrowed)) == {Result.PASS}


def test_no_ventilator_is_not_applicable(ctx):
    plan = _edit(ctx.plan, "EQ-B-ERV", kind=EquipmentKind.SPACE_HEATER,
                 blower_interlock_ref=None)
    assert _results(erv_blower_interlock(_with(ctx, plan))) == {Result.NOT_APPLICABLE}
