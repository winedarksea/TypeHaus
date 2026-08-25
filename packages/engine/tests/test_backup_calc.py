"""The backup-microgrid arithmetic — and the one invariant it rests on.

``takeoff/backup_calc.py`` exists to answer "does this system carry the house", and the
answer is only worth having if it cannot flatter itself. So the tests here are less about
the numbers being right today (they move whenever a duty cycle is revised) and more about
the shape of the answer: an unauthored duty cycle is an unknown contributor and never a
zero, a missing rating leaves the verdict UNKNOWN rather than optimistic, and a house with
no ESS gets ``modeled: False`` instead of a page of zeros.

The Catlin numbers are pinned where they are structural — 14.3 kWh at 90% DoD, one strong
solar day against 48h of the always-on tier — because those are the sizing decision itself.
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
    """Battery-only autonomy, which fell from ~50 h to 46.3 h on 2026-08-02 and to 41.3 h
    on 2026-08-24.

    2026-08-02: nothing was added to the house's *design* — the three PoE access points
    became real elements, and the model had only ever carried one notional 15 W allowance
    for them (parked on CKT-FRIDGE, of all circuits). Counting all three, on the switch's
    circuit where they actually land, put ~30 W of genuine always-on load on the books for
    the first time.

    2026-08-24: the kitchen got under-cabinet task light, and its 24V supply
    (ED-M-KITCH-LT-PSU) sits on CKT-LT-BACKUP because electrical_notes.md line 24 puts
    kitchen lighting behind the backup relay. That circuit went 558 -> 782 VA and its
    average draw 83.7 -> 117.3 W at the authored 0.15 duty.

    ** MOST OF THAT 224 VA IS A RATING, NOT A LOAD, AND THE OVERSTATEMENT IS DELIBERATE. **
    Per plan/lighting_types.py's own rule, a PSU's ``load_va`` is the supply's rating and
    not the tape's draw: the driver is rated 200 VA and the four LR-M-KIT-* runs pull
    44.6 W (55.7 W at the 125% sizing factor). So the true added always-on average is nearer
    12 W than 33.6 W, and the honest 41.3 h is a floor rather than an estimate. A backup
    calculation that errs is supposed to err this way.

    The 48-hour question the design is built around is still answered yes — see
    ``test_the_48_hour_cycle_sustains_the_always_on_tier_but_not_both``, which is the one
    that includes solar — but on battery alone the tier is now well short of two full days.
    """
    autonomy = summary["autonomy"]
    assert 40.0 < autonomy["hours_always_on_only"] < 43.0

    assert autonomy["hours_all_tiers"] < autonomy["hours_always_on_only"]


def test_the_48_hour_cycle_sustains_the_always_on_tier_but_not_both(summary):
    """The TODO's actual question, and the answer that says one battery is enough: with
    strong sun every other day the always-on tier is net positive, and both tiers together
    are not — which is what the shed tier exists to answer."""
    cycle = summary["cycle_48h"]
    assert cycle["array_kw"] == pytest.approx(5.28)
    assert cycle["sustains_always_on"] is True and cycle["net_kwh_always_on"] > 0
    assert cycle["sustains_all_tiers"] is False
    assert "which is what the shed tier is for" in summary["verdict"]


def test_the_backup_load_fits_the_inverter(summary):
    """8 kW continuous, not the 12 kW the product name suggests — the 12k is PV input."""
    peak = summary["peak"]
    assert peak["inverter_kw_continuous"] == 8.0 and peak["inverter_kw_surge"] == 16.0
    assert peak["within_continuous"] is True and peak["within_surge"] is True
    assert peak["simultaneous_va"] > peak["always_on_va"]


def test_solar_input_scales_the_verdict(catlin_model, summary):
    """A worse solar year is a parameter, not a rewrite: halve the strong-day yield and the
    always-on tier stops riding, which is the recommendation flipping on its own evidence."""
    poor = backup_runtime_summary(catlin_model, strong_day_kwh_per_kw=1.0)
    assert poor["cycle_48h"]["sustains_always_on"] is False
    assert "add array, not battery" in poor["verdict"]
    assert summary["cycle_48h"]["sustains_always_on"] is True
