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
    "INTERCONNECTION_CENTER_FED": "705.12(B)(4)", "INTERCONNECTION_FEED_THROUGH": "705.12(B)(5)",
    "INTERCONNECTION_ENGINEERED": "705.12(B)(6)",
}


@pytest.mark.parametrize(("name", "section"), sorted(_PRINTED.items()))
def test_section_numbers_match_the_printed_code(name, section):
    assert getattr(NEC, name) == section


def _with_inverter(plan, **update):
    types = tuple(t.model_copy(update=update) if getattr(t, "inverter_kw_continuous", None) else t
                  for t in plan.library.equipment_types)
    return plan.model_copy(update={
        "library": plan.library.model_copy(update={"equipment_types": types})})


def test_the_inverter_covers_the_backup_panel_and_pcs_is_export_only(catlin_plan, catlin_model):
    findings = standby_capacity(check_context(catlin_plan, catlin_model))
    assert [f.result for f in findings] == [Result.PASS, Result.NOT_APPLICABLE, Result.UNKNOWN]
    assert "include no overload control" in findings[1].message  # EG4's published PCS list
    assert "5,629 VA" in findings[0].message and "CKT-HP3" in findings[0].message
    # 702.6: EG4 publishes a fault LED only.
    assert "carrying load visual" in findings[2].message


def test_702_6_passes_with_every_signal_published(catlin_plan, catlin_model):
    signals = ("malfunction_visual", "malfunction_audible", "carrying_load_visual",
               "carrying_load_audible")
    plan = _with_inverter(catlin_plan, standby_signals=signals)
    assert standby_capacity(check_context(plan, catlin_model))[-1].result is Result.PASS


def _run(plan, model):
    """The calc reads the model's own plan, so the spliced plan goes onto it for the call."""
    original = model.plan
    model.plan = plan
    try:
        return standby_capacity(check_context(plan, model))
    finally:
        model.plan = original


def test_a_small_inverter_is_unknown_then_fails(catlin_plan, catlin_model):
    # 3 kW: under the 5,629 VA all circuits draw, over the 1,850 VA largest -> only a PCS can.
    mid = _run(_with_inverter(catlin_plan, inverter_kw_continuous=3.0), catlin_model)
    assert mid[0].result is Result.UNKNOWN and "702.4(A)(3)" in mid[0].message
    low = _run(_with_inverter(catlin_plan, inverter_kw_continuous=1.5), catlin_model)
    assert low[0].result is Result.FAIL
    # Declared not PCS-listed: (A)(3) falls away, the capacity finding stands alone.
    off = _run(_with_inverter(catlin_plan, pcs_listed=False), catlin_model)
    assert [f.result for f in off][:2] == [Result.PASS, Result.NOT_APPLICABLE]
    on = _run(_with_inverter(catlin_plan, pcs_functions=("overload_control",)), catlin_model)
    assert [f.result for f in on][:2] == [Result.PASS, Result.UNKNOWN]  # setting, reconnection


# --- lane F: EG4's published facts (ESS User Manual v1.0, 12kPV QSG v1.3.2) ---------------

def test_ess_shutdown_reads_the_inverters_rsd_scope(catlin_plan, catlin_model):
    from typehaus.checks.mep.ess_shutdown import ess_emergency_shutdown

    results = [f.result for f in ess_emergency_shutdown(check_context(catlin_plan, catlin_model))]
    # 706.15(B), 480.7(A)/(B), and 706.15(D): the WallMount's breaker is not stated to open
    # both conductors and no disconnect is drawn beside it.
    assert results == [Result.PASS, Result.NOT_APPLICABLE, Result.PASS, Result.UNKNOWN]
    stated = _with_inverter(catlin_plan)  # helper only edits inverters; patch the battery
    types = tuple(t.model_copy(update={"battery_disconnect_all_ungrounded": True})
                  if getattr(t, "storage_kwh", None) else t
                  for t in stated.library.equipment_types)
    stated = stated.model_copy(update={"library": stated.library.model_copy(
        update={"equipment_types": types})})
    assert ess_emergency_shutdown(check_context(stated, catlin_model))[-1].result is Result.PASS
    pv_only = _with_inverter(catlin_plan, rsd_shutdown_scope=("pv_array",))
    assert ess_emergency_shutdown(check_context(pv_only, catlin_model))[0].result is Result.FAIL


def test_source_breaker_over_the_inverters_maximum_fails(catlin_plan, catlin_model):
    from typehaus.checks.mep.power_sources import source_ocpd

    small = _with_inverter(catlin_plan, max_overcurrent_a=45)  # under CKT-ESS-GRID's 50 A
    ceiling = source_ocpd(check_context(small, catlin_model))[1]
    assert ceiling.result is Result.FAIL and "45A maximum OCPD" in ceiling.message


def test_evse_connector_under_18_in_indoors_fails(catlin_plan, catlin_model):
    from typehaus.checks.mep.electrical_evse import evse_circuit
    from typehaus.quantities import inch

    types = tuple(t.model_copy(update={"connector_holster_height": inch(12)})
                  if t.connector_holster_height is not None else t
                  for t in catlin_plan.library.appliance_types)
    low = catlin_plan.model_copy(update={
        "library": catlin_plan.library.model_copy(update={"appliance_types": types})})
    [found] = [f for f in evse_circuit(check_context(low, catlin_model)) if "625.50" in f.code_ref]
    assert found.result is Result.FAIL and "12 in." in found.message
