"""The backup-microgrid arithmetic — and the one invariant it rests on.

``takeoff/backup_calc.py`` exists to answer "does this system carry the house", and the
answer is only worth having if it cannot flatter itself. So the tests here are less about
the numbers being right today (they move whenever a duty cycle is revised) and more about
the shape of the answer: an unauthored duty cycle is an unknown contributor and never a
zero, a missing rating leaves the verdict UNKNOWN rather than optimistic, and a house with
no ESS gets ``modeled: False`` instead of a page of zeros.

The Catlin numbers are pinned against the hand-worked oracle in
``houses/catlin/notes/backup_power.md`` — battery-side draw with inverter idle and
efficiency, a summer and a December 48 h cycle, the darkness bridge and the surplus tier.
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
    assert result["autonomy"]["hours_always_on_only"] is None  # not 0.0, and not infinity
    assert result["complete"] is False


# --- the Catlin sizing decision -------------------------------------------------------

def test_usable_storage_is_nameplate_times_the_declared_dod(summary):
    autonomy = summary["autonomy"]
    assert autonomy["nameplate_kwh"] == 14.3
    assert autonomy["depth_of_discharge"] == DEPTH_OF_DISCHARGE
    assert autonomy["usable_kwh"] == pytest.approx(14.3 * DEPTH_OF_DISCHARGE, abs=0.01)


def test_autonomy_is_the_always_on_tier_alone(summary):
    """Battery-only autonomy, battery-side: 250.0 W / 0.94 + 55 W idle = 321.0 W, so 12.87 kWh
    lasts 40.1 h (notes/backup_power.md §6, the hand oracle). The surplus tier is never
    counted against it."""
    autonomy = summary["autonomy"]
    assert autonomy["inverter_idle_w"] == 55.0 and autonomy["inverter_efficiency"] == 0.94
    assert summary["tiers"]["always_on"]["average_w"] == pytest.approx(250.0, abs=0.1)
    assert autonomy["battery_w_always_on"] == pytest.approx(250.0 / 0.94 + 55, abs=0.1)
    assert autonomy["hours_always_on_only"] == pytest.approx(40.1, abs=0.1)
    assert "hours_all_tiers" not in autonomy


def test_the_surplus_tier_is_excluded_from_autonomy(catlin_model, summary):
    """Doubling every surplus circuit's duty moves the surplus figures and nothing the
    battery is graded on."""
    circuits = tuple(
        c.model_copy(update={"duty_cycle": c.duty_cycle * 2})
        if c.backup_tier is not None and c.backup_tier.value == "surplus" else c
        for c in catlin_model.plan.library.circuits)
    heavier = backup_runtime_summary(_with_circuits(catlin_model, circuits))
    for key in ("autonomy", "darkness_bridge"):
        for field in ("hours_always_on_only", "battery_w_always_on", "required_kwh"):
            if field in summary[key]:
                assert heavier[key][field] == summary[key][field]
    assert heavier["cycle_48h"]["surplus_hours"] < summary["cycle_48h"]["surplus_hours"]


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
    """CKT-HA's shed is structure, not a lowered duty: the five named ports' E-603 watts
    (doorbell, two cameras, two of the three APs) over the 88% supply: 66.95 / 0.88 = 76.1 W.
    An unrated tag is listed and saves nothing."""
    row = next(r for r in summary["tiers"]["always_on"]["circuits"] if r["circuit"] == "CKT-HA")
    assert row["shed_w"] == pytest.approx(76.1, abs=0.1) and row["shed_unrated"] == []
    assert row["average_w"] == pytest.approx(300 * 0.44 - 76.1, abs=0.1)

    circuits = tuple(
        c.model_copy(update={"backup_shed_poe": ("ED-M-STUDY-DATA1",)}) if c.tag == "CKT-HA"
        else c for c in catlin_model.plan.library.circuits)
    unshed = backup_runtime_summary(_with_circuits(catlin_model, circuits))
    row = next(r for r in unshed["tiers"]["always_on"]["circuits"] if r["circuit"] == "CKT-HA")
    assert row["shed_unrated"] == ["ED-M-STUDY-DATA1"] and row["average_w"] == 132.0


def test_summer_and_the_bridge_carry_the_always_on_tier_and_december_does_not(summary):
    """The hand oracle in notes/backup_power.md §6: 321.0 W x 48 h = 15.41 kWh against 15.84
    (summer, 3.0 kWh/kW) and 7.92 (December, 1.5 kWh/kW); the dark day plus St Paul's
    15.2 h longest night needs 12.59 kWh of the 12.87 usable."""
    summer, winter = summary["cycle_48h"], summary["cycle_48h_winter"]
    assert summer["array_kw"] == pytest.approx(5.28)
    assert summer["two_day_load_kwh_always_on"] == pytest.approx(15.41, abs=0.02)
    assert summer["net_kwh_always_on"] == pytest.approx(0.43, abs=0.02)
    assert winter["net_kwh_always_on"] == pytest.approx(-7.49, abs=0.02)
    assert summer["sustains_always_on"] and not winter["sustains_always_on"]
    bridge = summary["darkness_bridge"]
    assert bridge["longest_night_h"] == pytest.approx(15.23, abs=0.05)
    assert bridge["required_kwh"] == pytest.approx(12.59, abs=0.05)
    assert bridge["bridges"] is True
    assert summary["verdict"].startswith("a strong December day")


def test_a_strong_day_leaves_hours_for_the_surplus_tier(summary):
    """15.84 - 24 h x 321.0 W = 8.14 kWh over the surplus tier's 812 W / 0.94 = 863.8 W:
    9.4 h in summer; December leaves 0.22 kWh."""
    summer, winter = summary["cycle_48h"], summary["cycle_48h_winter"]
    assert summary["tiers"]["surplus"]["average_w"] == pytest.approx(812.0, abs=0.1)
    assert summer["surplus_kwh"] == pytest.approx(8.14, abs=0.02)
    assert summer["surplus_hours"] == pytest.approx(9.4, abs=0.1)
    assert winter["surplus_kwh"] == pytest.approx(0.22, abs=0.02)


def test_the_backup_load_fits_the_inverter(summary):
    """8 kW continuous, not the 12 kW the product name suggests — the 12k is PV input."""
    peak = summary["peak"]
    assert peak["inverter_kw_continuous"] == 8.0 and peak["inverter_kw_surge"] == 16.0
    assert peak["within_continuous"] is True and peak["within_surge"] is True
    assert peak["simultaneous_va"] > peak["always_on_va"]


def test_an_authored_start_governs_the_surge(catlin_model, summary):
    """Surge = the worst single start plus every other circuit running. CKT-WH has no
    authored start, so 3 x 1,440 + 6,783 - 1,440 = 9,663 VA; author a sump start of 12 kVA
    and the sump governs at 12,000 + 6,783 - 2,328."""
    assert summary["peak"]["surge_circuit"] == "CKT-WH"
    assert summary["peak"]["surge_va"] == pytest.approx(9663, abs=1)
    circuits = tuple(c.model_copy(update={"start_va": 12000.0}) if c.tag == "CKT-SUMP" else c
                     for c in catlin_model.plan.library.circuits)
    peak = backup_runtime_summary(_with_circuits(catlin_model, circuits))["peak"]
    assert peak["surge_circuit"] == "CKT-SUMP"
    assert peak["surge_va"] == pytest.approx(12000 + 6783 - 2328, abs=1)


def test_solar_input_scales_the_verdict(catlin_model, summary):
    """Solar yield is a parameter, not a rewrite: at 3.0 kWh/kW in December too, both seasons
    carry the always-on 48 h and the verdict is sufficient; at 2.9 summer fails."""
    sunny = backup_runtime_summary(catlin_model, winter_strong_day_kwh_per_kw=3.0)
    assert sunny["cycle_48h_winter"]["sustains_always_on"] is True
    assert sunny["verdict"].startswith("sufficient")
    dull = backup_runtime_summary(catlin_model, strong_day_kwh_per_kw=2.9)
    assert dull["cycle_48h"]["sustains_always_on"] is False
    assert "add array, not battery" in dull["verdict"]
