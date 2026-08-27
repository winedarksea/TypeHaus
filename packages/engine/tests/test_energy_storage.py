"""The ESS rules — R327, NEC 705.12/690.12, and the two advisories — each proved twice.

Same pattern as ``test_supply_protection.py``: a check that passes on a house which already
complies proves almost nothing, since it would pass just as well if it returned ``[]``. So
every rule here runs against the Catlin house as authored *and* against the same house with
the one thing it looks for spliced out — an unlisted battery, a missing alarm, a cleared
``rsd`` flag, an oversized backfeed.

The splice is always the smallest edit that makes the model wrong, because that is what
proves the check is reading the field it claims to read rather than something correlated
with it.
"""

from __future__ import annotations


import pytest

from _helpers import check_context

from typehaus.checks.advisory.energy_storage import ess_clearance, ess_enclosure
from typehaus.checks.code.mn_residential.energy_storage import (
    ess_capacity,
    ess_detection,
    ess_listing,
)
from typehaus.checks.mep.power_sources import interconnection_busbar, rapid_shutdown
from typehaus.checks.registry import CheckContext
from typehaus.findings import Result
from typehaus.model.enums import AlarmKind




def _context(plan, model=None) -> CheckContext:
    return check_context(plan, model)


def _fails(findings) -> list:
    return [f for f in findings if f.result is Result.FAIL]


def _passes(findings) -> list:
    return [f for f in findings if f.result is Result.PASS]


def _retype_battery(plan, **updates):
    """The Catlin plan with EQ-T-ESS-BATT's product type edited in place."""
    types = tuple(
        item.model_copy(update=updates) if item.tag == "EQ-T-ESS-BATT" else item
        for item in plan.library.equipment_types)
    assert any(t.tag == "EQ-T-ESS-BATT" for t in types), "fixture regression: no battery type"
    library = plan.library.model_copy(update={"equipment_types": types})
    return plan.model_copy(update={"library": library})


def _recircuit(plan, tag: str, circuit):
    """The Catlin plan with one placed element's ``circuit`` edited in place."""
    found = False
    for storey in plan.storeys:
        elements = plan.storey_elements(storey.tag)
        edited = [e.model_copy(update={"circuit": circuit}) if e.tag == tag else e
                  for e in elements]
        if any(e.tag == tag for e in elements):
            plan = plan.with_elements(storey.tag, edited)
            found = True
    assert found, f"fixture regression: the Catlin house has no {tag}"
    return plan


def _without_alarm(plan, tag: str):
    found = False
    for storey in plan.storeys:
        elements = plan.storey_elements(storey.tag)
        kept = [e for e in elements
                if not (e.element_kind == "Alarm" and e.tag == tag)]
        if len(kept) != len(elements):
            plan = plan.with_elements(storey.tag, kept)
            found = True
    assert found, f"fixture regression: the Catlin house has no alarm {tag}"
    return plan


# --- R327.2 listing -------------------------------------------------------------------

def test_battery_declares_its_ul_9540_listing(catlin_plan, catlin_model):
    findings = ess_listing(_context(catlin_plan, catlin_model))
    assert findings and not _fails(findings)
    assert any("EQ-B-ESS-BATT" in f.message and "UL 9540" in f.message for f in findings)
    assert all(f.code_ref == "R327.2" for f in findings)


def test_an_undeclared_listing_fails(catlin_plan):
    """False means "this model does not state that the unit is listed" — which is exactly
    the finding a plan reviewer needs, not a gap the check papers over."""
    plan = _retype_battery(catlin_plan, ul_9540_listed=False)
    fails = _fails(ess_listing(_context(plan)))
    assert len(fails) == 1 and "EQ-B-ESS-BATT" in fails[0].message


# --- R327.5 energy ratings ------------------------------------------------------------

def test_capacity_is_within_both_the_unit_and_the_aggregate_limit(catlin_plan, catlin_model):
    findings = ess_capacity(_context(catlin_plan, catlin_model))
    assert not _fails(findings)
    assert any("14.3 kWh aggregate inside the dwelling" in f.message for f in findings)


def test_an_oversized_unit_fails_the_per_unit_limit(catlin_plan):
    plan = _retype_battery(catlin_plan, storage_kwh=25.0)
    fails = _fails(ess_capacity(_context(plan)))
    assert any("R327.5 limits one unit to 20 kWh" in f.message for f in fails)


def test_an_undeclared_capacity_is_unknown_not_zero(catlin_plan):
    """A battery with no ``storage_kwh`` must not silently contribute 0 to the aggregate:
    that would make an unmodeled bank look like compliance."""
    plan = _retype_battery(catlin_plan, storage_kwh=None)
    findings = ess_capacity(_context(plan))
    assert [f.result for f in findings] == [Result.UNKNOWN]


# --- R327.7 fire detection ------------------------------------------------------------

def test_the_ess_room_has_both_smoke_and_heat_coverage(catlin_plan, catlin_model):
    findings = ess_detection(_context(catlin_plan, catlin_model))
    assert not _fails(findings)
    assert {"smoke", "heat"} <= {word for f in findings for word in f.message.split()}


@pytest.mark.parametrize("tag,missing", [("AL-B-ESS-SMOKE", "smoke"),
                                         ("AL-B-ESS-HEAT", "heat")])
def test_removing_either_alarm_fails(catlin_plan, tag, missing):
    """Both, not either. R327.7 sends you to R314 for smoke and adds a heat detector for
    the locations a smoke alarm cannot serve; a battery closet is such a location."""
    plan = _without_alarm(catlin_plan, tag)
    fails = _fails(ess_detection(_context(plan)))
    assert len(fails) == 1 and f"no {missing} alarm" in fails[0].message


# --- NEC 705.12 interconnection -------------------------------------------------------

def test_the_backfeed_fits_the_120_percent_allowance(catlin_plan, catlin_model):
    """225A bus x 1.2 = 270A allowed; 200A main + 50A source = 250A, 20A spare."""
    findings = interconnection_busbar(_context(catlin_plan, catlin_model))
    assert len(findings) == 1 and findings[0].result is Result.PASS
    assert "20A spare" in findings[0].message


def test_an_oversized_source_breaker_fails(catlin_plan):
    """The ceiling on this bus is 70A of source. 90A is over it, and the check says by how
    much rather than only that it is."""
    circuits = tuple(
        c.model_copy(update={"breaker_amps": 90}) if c.source else c
        for c in catlin_plan.library.circuits)
    library = catlin_plan.library.model_copy(update={"circuits": circuits})
    plan = catlin_plan.model_copy(update={"library": library})
    fails = _fails(interconnection_busbar(_context(plan)))
    assert len(fails) == 1 and "290A exceeds" in fails[0].message


def test_a_panel_without_a_bus_rating_is_unknown(catlin_plan):
    """Not a pass. "We do not know the bus" and "the bus is big enough" are different
    answers, and only one of them is safe to print under a code citation."""
    types = tuple(t.model_copy(update={"bus_amps": None}) if t.tag == "ED-T-PANEL" else t
                  for t in catlin_plan.library.electrical_device_types)
    library = catlin_plan.library.model_copy(update={"electrical_device_types": types})
    plan = catlin_plan.model_copy(update={"library": library})
    findings = interconnection_busbar(_context(plan))
    assert [f.result for f in findings] == [Result.UNKNOWN]


# --- NEC 690.12 rapid shutdown --------------------------------------------------------

def test_every_module_carries_a_shutdown_device(catlin_plan, catlin_model):
    findings = rapid_shutdown(_context(catlin_plan, catlin_model))
    assert len(findings) == 2  # one per string
    assert all(f.result is Result.PASS for f in findings)
    assert all("all 6 modules" in f.message for f in findings)


def test_dropping_rsd_from_alternate_modules_fails_on_cold_voc(catlin_model):
    """The "every other module" option plans/TODO.md hoped for, tested rather than assumed:
    two Aptos modules sum to 88.8V at the -30 degC design low, over the 80V limit."""
    from dataclasses import replace

    panels = [replace(p, rsd=(index % 2 == 0))
              for index, p in enumerate(sorted(catlin_model.solar_panels,
                                               key=lambda p: p.tag))]
    model = catlin_model
    original = list(model.solar_panels)
    model.solar_panels[:] = panels
    try:
        fails = _fails(rapid_shutdown(_context(model.plan, model)))
        assert fails and all("over the 80V limit" in f.message for f in fails)
        assert any("88.8V" in f.message for f in fails)
    finally:
        model.solar_panels[:] = original


def test_a_module_without_cold_voc_is_unknown_not_a_pass(catlin_model):
    """``voc_cold`` is the only voltage this rule may read. Rated Voc would put a pair at
    78.1V and pass it — legal in July, not in January."""
    from dataclasses import replace

    original = list(catlin_model.solar_panels)
    catlin_model.solar_panels[:] = [replace(p, rsd=False, voc_cold=None) for p in original]
    try:
        findings = rapid_shutdown(_context(catlin_model.plan, catlin_model))
        assert findings and all(f.result is Result.UNKNOWN for f in findings)
    finally:
        catlin_model.solar_panels[:] = original


# --- the advisories -------------------------------------------------------------------

def test_the_closet_meets_the_owners_type_x_standard(catlin_plan, catlin_model):
    findings = ess_enclosure(_context(catlin_plan, catlin_model))
    assert len(findings) == 1 and findings[0].result is Result.PASS


def test_a_plain_gypsum_partition_fails_the_enclosure_standard(catlin_plan):
    """Re-material the closet assembly's two membranes from Type X to regular board and
    change nothing else — same tag, same thickness, same steel studs. The advisory has to
    notice, because it reads the material's declared gypsum grade and not the layer's
    thickness or the assembly's name."""
    target = next(a for a in catlin_plan.library.assemblies
                  if a.tag == "INT_ESS_CLOSET_STEEL")
    layers = tuple(layer.model_copy(update={"material_ref": "gwb"})
                   if layer.material_ref == "gwb-x" else layer
                   for layer in target.layers)
    assert any(layer.material_ref == "gwb" for layer in layers), "fixture: no Type X to swap"
    swapped = target.model_copy(update={"layers": layers})
    assemblies = tuple(swapped if a.tag == target.tag else a
                       for a in catlin_plan.library.assemblies)
    library = catlin_plan.library.model_copy(update={"assemblies": assemblies})
    plan = catlin_plan.model_copy(update={"library": library})
    fails = _fails(ess_enclosure(_context(plan)))
    assert len(fails) == 1 and "0.00\" Type X" in fails[0].message


def test_nothing_stands_in_the_batterys_separation_zone(catlin_plan, catlin_model):
    findings = ess_clearance(_context(catlin_plan, catlin_model))
    assert len(findings) == 1 and findings[0].result is Result.PASS


def test_the_batterys_own_inverter_is_not_an_other_device(catlin_plan, catlin_model):
    """EQ-B-ESS-INV stands 18 1/4" from EQ-B-ESS-BATT — half the separation the owner's rule
    asks of an *other* device, and deliberately so: a 12kPV and the pack it charges are one
    listed ESS, and the DC run between them is the highest-amperage circuit in the house.
    The exemption is named in the PASS message rather than applied silently."""
    findings = ess_clearance(_context(catlin_plan, catlin_model))
    assert len(findings) == 1 and findings[0].result is Result.PASS
    assert "EQ-B-ESS-INV is its own power-conversion equipment" in findings[0].message
    assert "EQ-B-ESS-INV" in findings[0].element_tags


def test_an_inverter_on_a_foreign_circuit_is_an_other_device(catlin_plan):
    """The smallest edit that makes the model wrong: move EQ-B-ESS-INV onto some other
    circuit and it stops being the battery's own power-conversion equipment. Nothing about
    the geometry changes, so this proves the exemption reads the authored link and not the
    inverter's kind, its tag or its distance."""
    plan = _recircuit(catlin_plan, "EQ-B-ESS-INV", "CKT-RC-BASEMENT")
    fails = _fails(ess_clearance(_context(plan)))
    assert len(fails) == 1 and "EQ-B-ESS-INV" in fails[0].message


def test_a_battery_with_no_circuit_exempts_nothing(catlin_plan):
    """A battery that names no circuit has no declared pairing, so the exemption cannot
    fire — an unauthored link must never be inferred from the inverter alone."""
    plan = _recircuit(catlin_plan, "EQ-B-ESS-BATT", None)
    fails = _fails(ess_clearance(_context(plan)))
    assert len(fails) == 1 and "EQ-B-ESS-INV" in fails[0].message


def test_a_battery_with_no_required_zone_is_reported(catlin_plan):
    plan = _retype_battery(catlin_plan, clearances=())
    fails = _fails(ess_clearance(_context(plan)))
    assert len(fails) == 1 and "declares no REQUIRED clearance zone" in fails[0].message


# --- the guard ------------------------------------------------------------------------

def test_every_ess_rule_no_ops_on_a_house_with_no_battery(catlin_plan):
    """A house with no ESS is not a house failing the ESS rules. The starter house has no
    battery, and all five battery-driven rules must return nothing at all rather than a
    row of UNKNOWNs nobody can clear."""
    plan = catlin_plan
    for storey in plan.storeys:
        kept = [e for e in plan.storey_elements(storey.tag)
                if not (e.element_kind == "Equipment"
                        and getattr(getattr(e, "kind", None), "value", None) == "battery")]
        plan = plan.with_elements(storey.tag, kept)
    ctx = _context(plan)
    for rule in (ess_listing, ess_capacity, ess_detection, ess_enclosure, ess_clearance):
        assert rule(ctx) == [], rule.__name__


def test_the_alarm_kinds_the_detection_rule_looks_for_exist():
    """A guard on the enum this rule reads: renaming either member would turn the R327.7
    check into one that can never pass, silently."""
    assert AlarmKind.SMOKE and AlarmKind.HEAT and AlarmKind.COMBO
