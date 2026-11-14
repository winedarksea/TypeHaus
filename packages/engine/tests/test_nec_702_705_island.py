"""Articles 702, 705 Parts I-III and 625.46-625.52 as printed 2026 (see
docs/code-notes/nec-2026-paraphrase-702-705-island.md): numbering pins and the standby-capacity advisory."""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.mep.standby_capacity import standby_capacity
from typehaus.findings import Result
from typehaus.model.nec import NEC

_PRINTED = {
    "STANDBY_FULL_LOAD": "702.4(A)(2)(a)", "STANDBY_MULTIMODE": "702.4(A)(3)",
    "STANDBY_TRANSFER": "702.5(A)", "STANDBY_PARALLEL": "702.5(D)", "STANDBY_SIGNALS": "702.6",
    "STANDBY_SIGN": "702.7(A)(1)", "STANDBY_GROUNDING_SIGN": "702.7(B)",
    "INTERACTIVE_LISTING": "705.2", "GFPE_SOURCES": "705.32", "LOSS_OF_PRIMARY": "705.40",
    "UNBALANCED": "705.45", "MICROGRID_CONNECTIONS": "705.60", "MICROGRID_INTERCONNECT": "705.70",
    "MICROGRID_CONTROL": "705.76", "ISLAND_CAPACITY": "705.80", "ISLAND_VOLTAGE": "705.81",
    "EVSE_LOSS_OF_PRIMARY": "625.46", "EVSE_INTERACTIVE": "625.48", "EVSE_ISLAND": "625.49",
    "EVSE_COUPLING_HEIGHT": "625.50", "EVSE_VENTILATION": "625.52",
}


@pytest.mark.parametrize(("name", "section"), sorted(_PRINTED.items()))
def test_section_numbers_match_the_printed_code(name, section):
    assert getattr(NEC, name) == section


def _with_inverter(plan, **update):
    types = tuple(t.model_copy(update=update) if getattr(t, "inverter_kw_continuous", None) else t
                  for t in plan.library.equipment_types)
    return plan.model_copy(update={
        "library": plan.library.model_copy(update={"equipment_types": types})})


def test_the_inverter_covers_the_backup_panel_but_pcs_status_is_unknown(catlin_plan, catlin_model):
    findings = standby_capacity(check_context(catlin_plan, catlin_model))
    assert [f.result for f in findings] == [Result.PASS, Result.UNKNOWN]
    assert "5,649 VA" in findings[0].message and "CKT-HP3" in findings[0].message


def _run(plan, model):
    """The calc reads the model's own plan, so the spliced plan goes onto it for the call."""
    original = model.plan
    model.plan = plan
    try:
        return standby_capacity(check_context(plan, model))
    finally:
        model.plan = original


def test_a_small_inverter_is_unknown_then_fails(catlin_plan, catlin_model):
    # 3 kW: under the 5,649 VA all circuits draw, over the 1,850 VA largest -> only a PCS can.
    mid = _run(_with_inverter(catlin_plan, inverter_kw_continuous=3.0), catlin_model)
    assert mid[0].result is Result.UNKNOWN and "702.4(A)(3)" in mid[0].message
    low = _run(_with_inverter(catlin_plan, inverter_kw_continuous=1.5), catlin_model)
    assert low[0].result is Result.FAIL
    # Declared not PCS-listed: (A)(3) falls away, the capacity finding stands alone.
    off = _run(_with_inverter(catlin_plan, pcs_listed=False), catlin_model)
    assert [f.result for f in off] == [Result.PASS]
