"""The backup-microgrid arithmetic — and the one invariant it rests on.

``takeoff/backup_calc.py`` exists to answer "does this system carry the house", and the
answer is only worth having if it cannot flatter itself. So the tests here are less about
the numbers being right today (they move whenever a duty cycle is revised) and more about
the shape of the answer: an unauthored duty cycle is an unknown contributor and never a
zero, a missing rating leaves the verdict UNKNOWN rather than optimistic, and a house with
no ESS gets ``modeled: False`` instead of a page of zeros.

The Catlin numbers are pinned against the hand-worked oracle in
``houses/catlin/notes/backup_power.md`` — battery-side draw with inverter idle and
efficiency, a summer and a December 48 h cycle, and the darkness bridge.
"""

from __future__ import annotations

import pytest

from typehaus.takeoff.backup_calc import DEPTH_OF_DISCHARGE, backup_runtime_summary


@pytest.fixture(scope="module")
def summary(catlin_model):
    return backup_runtime_summary(catlin_model)


def _with_circuits(model, circuits):
    library = model.plan.library.model_copy(update={"circuits": tuple(circuits)})
    return _rebind(model, model.plan.model_copy(update={"library": library}))


def _rebind(model, plan):
    """A shallow view of the resolved model with a different plan attached.

    ``ResolvedModel`` is a mutable dataclass built by the resolver, and re-resolving for
    each variant would triple this file's runtime for no extra coverage: every function
    under test reads ``model.plan.library`` and ``model.solar_panels``, neither of which
    the swap invalidates.
    """
    import copy

    clone = copy.copy(model)
    clone.plan = plan
    return clone


# --- the shape of the answer ----------------------------------------------------------

def test_a_house_with_no_ess_reports_not_modeled(catlin_model):
    library = catlin_model.plan.library.model_copy(update={"circuits": ()})
    plan = catlin_model.plan.model_copy(update={"library": library})
    for storey in plan.storeys:
        plan = plan.with_elements(storey.tag, [
            e for e in plan.storey_elements(storey.tag)
            if getattr(getattr(e, "kind", None), "value", None) not in {"battery", "inverter"}
        ])
    assert backup_runtime_summary(_rebind(catlin_model, plan)) == {"modeled": False}


def test_the_summary_says_it_is_an_estimate(summary):
    assert summary["modeled"] is True and summary["estimate"] is True


# --- the invariant: unknown, never zero -----------------------------------------------

def test_a_circuit_without_a_duty_cycle_is_an_unknown_contributor(catlin_model):
    """The failure this whole module exists to prevent: a silent zero would make the array
    look like it carries a house it does not carry."""
    circuits = tuple(
        c.model_copy(update={"duty_cycle": None}) if c.tag == "CKT-FRIDGE" else c
        for c in catlin_model.plan.library.circuits)
    result = backup_runtime_summary(_with_circuits(catlin_model, circuits))
    tier = result["tiers"]["always_on"]
    assert tier["unknown_duty_cycle"] == ["CKT-FRIDGE"]
    assert tier["complete"] is False and result["complete"] is False
    # The row is present and its average is None — not 0.0, which would sum silently.
    row = next(r for r in tier["circuits"] if r["circuit"] == "CKT-FRIDGE")
    assert row["average_w"] is None and row["connected_va"] == 800
    # And the tier average excludes it rather than counting it as nothing.
    assert tier["average_w"] < backup_runtime_summary(catlin_model)["tiers"][
        "always_on"]["average_w"]


def test_an_incomplete_model_gets_an_unknown_verdict(catlin_model):
    circuits = tuple(
        c.model_copy(update={"duty_cycle": None}) if c.tag == "CKT-HA" else c
        for c in catlin_model.plan.library.circuits)
    result = backup_runtime_summary(_with_circuits(catlin_model, circuits))
    assert result["verdict"].startswith("UNKNOWN")
    assert "floor, not a total" in result["verdict"]


def test_a_battery_with_no_declared_capacity_is_listed_not_assumed(catlin_model):
    types = tuple(t.model_copy(update={"storage_kwh": None}) if t.tag == "EQ-T-ESS-BATT" else t
                  for t in catlin_model.plan.library.equipment_types)
    library = catlin_model.plan.library.model_copy(update={"equipment_types": types})
    plan = catlin_model.plan.model_copy(update={"library": library})
    result = backup_runtime_summary(_rebind(catlin_model, plan))
    assert result["batteries_without_capacity"] == ["EQ-B-ESS-BATT"]
    assert result["autonomy"]["hours_all_tiers"] is None  # not 0.0, and not infinity
    assert result["complete"] is False


# --- the Catlin sizing decision -------------------------------------------------------

def test_usable_storage_is_nameplate_times_the_declared_dod(summary):
    autonomy = summary["autonomy"]
    assert autonomy["nameplate_kwh"] == 14.3
    assert autonomy["depth_of_discharge"] == DEPTH_OF_DISCHARGE
    assert autonomy["usable_kwh"] == pytest.approx(14.3 * DEPTH_OF_DISCHARGE, abs=0.01)


def test_the_always_on_tier_outlasts_the_shed_tier_by_a_wide_margin(summary):
    """Battery-only autonomy, battery-side: (330.9 W / 0.94 + 55 W idle) = 407.0 W on the
    always-on tier, so 12.87 kWh lasts 31.6 h (notes/backup_power.md, the hand oracle).

    Each PSU on CKT-LT-BACKUP sums at its nameplate, not its tape draw
    (plan/lighting_types.py's rule), so this is a floor: a backup calc errs heavy.
    """
    autonomy = summary["autonomy"]
    assert autonomy["inverter_idle_w"] == 55.0 and autonomy["inverter_efficiency"] == 0.94
    assert autonomy["battery_w_always_on"] == pytest.approx(330.9 / 0.94 + 55, abs=0.2)
    assert 29.0 < autonomy["hours_always_on_only"] < 34.0
    assert autonomy["hours_all_tiers"] < autonomy["hours_always_on_only"]


def test_an_inverter_without_idle_or_efficiency_is_unknown_not_free(catlin_model):
    """The inverter's own draw is a contributor like any circuit: unauthored is UNKNOWN."""
    types = tuple(t.model_copy(update={"inverter_idle_w": None}) if t.tag == "EQ-T-EG4-12KPV"
                  else t for t in catlin_model.plan.library.equipment_types)
    library = catlin_model.plan.library.model_copy(update={"equipment_types": types})
    result = backup_runtime_summary(_rebind(catlin_model, catlin_model.plan.model_copy(
        update={"library": library})))
    assert result["inverter_unknown"] == ["EQ-B-ESS-INV.idle_w"]
    assert result["verdict"].startswith("UNKNOWN")


def test_zero_storage_sustains_nothing(catlin_model):
    """A PV-only backup port has no dark day to buffer: however big the array, it must not
    report "sustains" (it used to, because the cycle never looked at the battery)."""
    types = tuple(t.model_copy(update={"storage_kwh": 0.0}) if t.tag == "EQ-T-ESS-BATT" else t
                  for t in catlin_model.plan.library.equipment_types)
    library = catlin_model.plan.library.model_copy(update={"equipment_types": types})
    plan = catlin_model.plan.model_copy(update={"library": library})
    result = backup_runtime_summary(_rebind(catlin_model, plan), strong_day_kwh_per_kw=50.0)
    assert result["cycle_48h"]["sustains_always_on"] is False
    assert result["darkness_bridge"]["bridges"] is False
    assert result["verdict"].startswith("no usable storage")


def test_shed_poe_ports_come_off_the_backup_average(catlin_model, summary):
    """CKT-HA's shed is structure, not a lowered duty: the three named ports' E-603 watts
    over the 88% supply (36.95 / 0.88 = 42 W). An unrated tag is listed and saves nothing."""
    row = next(r for r in summary["tiers"]["always_on"]["circuits"] if r["circuit"] == "CKT-HA")
    assert row["shed_w"] == pytest.approx(42.0, abs=0.1) and row["shed_unrated"] == []
    assert row["average_w"] == pytest.approx(300 * 0.44 - 42.0, abs=0.1)

    circuits = tuple(
        c.model_copy(update={"backup_shed_poe": ("ED-M-STUDY-DATA1",)}) if c.tag == "CKT-HA"
        else c for c in catlin_model.plan.library.circuits)
    unshed = backup_runtime_summary(_with_circuits(catlin_model, circuits))
    row = next(r for r in unshed["tiers"]["always_on"]["circuits"] if r["circuit"] == "CKT-HA")
    assert row["shed_unrated"] == ["ED-M-STUDY-DATA1"] and row["average_w"] == 132.0


def test_neither_season_carries_the_always_on_tier_and_the_bridge_falls_short(summary):
    """The hand oracle in notes/backup_power.md: 407.0 W x 48 h = 19.54 kWh against 15.84
    (summer, 3.0 kWh/kW) and 7.92 (December, 1.5 kWh/kW); the dark day plus St Paul's
    15.2 h longest night needs 16.0 kWh of the 12.87 usable."""
    summer, winter = summary["cycle_48h"], summary["cycle_48h_winter"]
    assert summer["array_kw"] == pytest.approx(5.28)
    assert summer["two_day_load_kwh_always_on"] == pytest.approx(19.54, abs=0.02)
    assert summer["net_kwh_always_on"] == pytest.approx(-3.70, abs=0.02)
    assert winter["net_kwh_always_on"] == pytest.approx(-11.62, abs=0.02)
    assert not summer["sustains_always_on"] and not winter["sustains_always_on"]
    bridge = summary["darkness_bridge"]
    assert bridge["longest_night_h"] == pytest.approx(15.23, abs=0.05)
    assert bridge["required_kwh"] == pytest.approx(15.97, abs=0.05)
    assert bridge["bridges"] is False
    assert "add array;" in summary["verdict"] and "does not bridge" in summary["verdict"]


def test_the_backup_load_fits_the_inverter(summary):
    """8 kW continuous, not the 12 kW the product name suggests — the 12k is PV input."""
    peak = summary["peak"]
    assert peak["inverter_kw_continuous"] == 8.0 and peak["inverter_kw_surge"] == 16.0
    assert peak["within_continuous"] is True and peak["within_surge"] is True
    assert peak["simultaneous_va"] > peak["always_on_va"]


def test_solar_input_scales_the_verdict(catlin_model, summary):
    """Solar yield is a parameter, not a rewrite: at 4.3 kWh/kW a summer day covers the
    always-on 48 h (22.7 > 19.54) and the December cycle becomes the binding complaint."""
    sunny = backup_runtime_summary(catlin_model, strong_day_kwh_per_kw=4.3)
    assert sunny["cycle_48h"]["sustains_always_on"] is True
    assert "December" in sunny["verdict"]
    assert summary["cycle_48h"]["sustains_always_on"] is False
