"""The supply-protection checks, each proved by removing the thing it looks for.

A check that passes on a house which already complies proves almost nothing — it would pass
just as well if it returned ``[]``. So every check here is exercised twice: once against the
Catlin house as authored, and once against the same house with the one accessory spliced
out, which is the state the check exists to catch. That is the pattern
``test_hydrant.py`` uses for the freeze-depth rules.

Also covered here: the two hydrant families. The house now has both — a buried yard hydrant
in the garage and two envelope-protected wall hydrants on the south face — and the thing
most likely to break quietly is the boundary between them, because grading a wall hydrant
against a 72" bury it does not have would fail it forever.
"""

from __future__ import annotations


import pytest

from typehaus.checks.mep.plumbing import (exterior_hydrant_protection, hot_water_insulation,
                                          hydrant_freeze_depth, pipe_material_preference)
from typehaus.checks.mep.supply_protection import (backflow_prevention, main_shutoff,
                                                   water_hammer_arrestor)
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.run import load_preferences
from typehaus.findings import Result
from typehaus.model.enums import PipeAccessoryKind
from typehaus.model.mep import PipeAccessory
from typehaus.resolve import resolve
from _helpers import CATLIN as CATLIN_DIR, check_context




@pytest.fixture(scope="module")
def catlin_prefs():
    return load_preferences(CATLIN_DIR)


def _context(plan, model, preferences: Preferences | None = None) -> CheckContext:
    return check_context(plan, model, preferences=preferences)


def _fails(findings) -> list:
    return [f for f in findings if f.result is Result.FAIL]


def _without(plan, tag: str):
    """The Catlin plan with one accessory removed from whichever storey holds it."""
    found = False
    for storey in plan.storeys:
        elements = plan.storey_elements(storey.tag)
        kept = [e for e in elements
                if not (isinstance(e, PipeAccessory) and e.tag == tag)]
        if len(kept) != len(elements):
            plan = plan.with_elements(storey.tag, kept)
            found = True
    assert found, f"fixture regression: the Catlin house has no accessory {tag}"
    return plan


def _resolved(plan):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return model


# --- the house as authored -----------------------------------------------------------

def test_the_house_passes_all_three_supply_protection_checks(catlin_plan, catlin_model):
    ctx = _context(catlin_plan, catlin_model)
    for check in (main_shutoff, backflow_prevention, water_hammer_arrestor):
        findings = check(ctx)
        assert findings, f"{check.__name__} evaluated nothing at all"
        assert not _fails(findings), [f.message for f in _fails(findings)]


def test_no_finding_claims_a_review_it_did_not_do(catlin_plan, catlin_model):
    """No UNKNOWNs left in this family. The whole point of ``PipeAccessory`` was to retire
    ``mep.hydrant_freeze_depth``'s "the model has no valve or backflow-preventer element"."""
    ctx = _context(catlin_plan, catlin_model)
    for check in (main_shutoff, backflow_prevention, water_hammer_arrestor,
                  hydrant_freeze_depth):
        unknown = [f for f in check(ctx) if f.result is Result.UNKNOWN]
        assert not unknown, [f.message for f in unknown]


# --- each check fails when its accessory is gone -------------------------------------

def test_a_missing_main_shutoff_fails(catlin_plan):
    plan = _without(catlin_plan, "PA-B-MAIN-SHUTOFF")
    findings = main_shutoff(_context(plan, _resolved(plan)))
    assert len(_fails(findings)) == 1
    assert "P2903.9.1" in _fails(findings)[0].message


def test_an_inaccessible_main_shutoff_fails_separately(catlin_plan, catlin_model):
    """A missing valve is caught at rough-in; a valve behind the water heater passes
    rough-in and is discovered the night something bursts."""
    plan = _without(catlin_plan, "PA-B-MAIN-SHUTOFF")
    original = catlin_plan.by_tag("PA-B-MAIN-SHUTOFF")
    buried = original.model_copy(update={"accessible": False})
    plan = plan.with_elements(
        "basement", (*plan.storey_elements("basement"), buried))
    findings = main_shutoff(_context(plan, _resolved(plan)))
    assert len(_fails(findings)) == 1
    assert "accessible" in _fails(findings)[0].message


def test_two_main_shutoffs_fail_because_the_main_is_singular(catlin_plan):
    extra = PipeAccessory(
        uid="TSTMS00001", tag="PA-TEST-SECOND-MAIN",
        kind=PipeAccessoryKind.MAIN_SHUTOFF, pipe_ref="PR-B-CW-TRUNK",
        position=(catlin_plan.by_tag("PA-B-MAIN-SHUTOFF").position), accessible=True)
    plan = catlin_plan.with_elements(
        "basement", (*catlin_plan.storey_elements("basement"), extra))
    findings = main_shutoff(_context(plan, _resolved(plan)))
    assert len(_fails(findings)) == 1
    assert "singular" in _fails(findings)[0].message


def test_a_hydrant_without_its_vacuum_breaker_fails(catlin_plan):
    """Per hydrant, not per house: three hydrants and one breaker protects one hydrant."""
    plan = _without(catlin_plan, "PA-S-BALC-HYD-VB")
    findings = backflow_prevention(_context(plan, _resolved(plan)))
    failed = _fails(findings)
    assert [f.element_tags[0] for f in failed] == ["FX-S-BALC-HYD"]
    # And the other two hydrants still pass, which is what makes it per-hydrant.
    passed = {f.element_tags[0] for f in findings if f.result is Result.PASS}
    assert {"FX-M-PORCH-HYD", "FX-G-HYDRANT"} <= passed


def test_an_arrestor_is_required_per_supply_not_per_appliance(catlin_plan):
    """The washer slams both solenoids shut; arresting only the cold leaves the hot to
    hammer, and a check that counted devices against appliances would call that done."""
    plan = _without(catlin_plan, "PA-M-WASH-WHA-HW")
    findings = water_hammer_arrestor(_context(plan, _resolved(plan)))
    failed = _fails(findings)
    assert len(failed) == 1
    assert "hot supply" in failed[0].message
    assert "FX-M-LAUNDRY" in failed[0].element_tags


def test_the_dishwasher_is_a_quick_closing_valve_too(catlin_plan):
    plan = _without(catlin_plan, "PA-M-DW-WHA-HW")
    failed = _fails(water_hammer_arrestor(_context(plan, _resolved(plan))))
    assert [f.element_tags[0] for f in failed] == ["APPL-M-DW"]


def test_the_checks_no_op_on_a_plan_with_no_supply_runs(catlin_plan, catlin_model):
    """A house whose plumbing has not been drawn yet is not a house missing a shutoff, and
    three FAILs against it would train the reader to ignore them."""
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import PipeRun

    plan = catlin_plan
    for storey in plan.storeys:
        kept = [e for e in plan.storey_elements(storey.tag)
                if not (isinstance(e, PipeRun)
                        and e.system in (PipeSystem.WATER_COLD, PipeSystem.WATER_HOT))]
        plan = plan.with_elements(storey.tag, kept)
    model, _ = resolve(plan)
    ctx = _context(plan, model)
    for check in (main_shutoff, backflow_prevention, water_hammer_arrestor):
        assert check(ctx) == []


# --- the two hydrant families ---------------------------------------------------------

def test_a_wall_hydrant_is_exempt_from_bury_depth_and_a_yard_hydrant_is_not(
        catlin_plan, catlin_model):
    findings = hydrant_freeze_depth(_context(catlin_plan, catlin_model))
    assert not _fails(findings), [f.message for f in _fails(findings)]
    by_hydrant: dict[str, list[str]] = {}
    for finding in findings:
        by_hydrant.setdefault(finding.element_tags[0], []).append(finding.message)
    # The yard hydrant is graded on its 72" bury and on the sleeve it rises through.
    garage = " | ".join(by_hydrant["FX-G-HYDRANT"])
    assert "below grade over its whole length" in garage
    assert "SP-G-HYDRANT" in garage
    # The wall hydrants are graded on neither, and say why.
    for tag in ("FX-M-PORCH-HYD", "FX-S-BALC-HYD"):
        message = " | ".join(by_hydrant[tag])
        assert "no bury depth to grade" in message
        assert "below grade" not in message


def test_removing_the_seal_drops_a_wall_hydrant_back_onto_the_bury_rule(catlin_plan):
    """The PENETRATION_SEAL is the *declaration* that a hydrant is envelope-protected.
    Without it the check has no way to know, and correctly falls back to asking for 72"."""
    plan = _without(catlin_plan, "PA-M-PORCH-HYD-SEAL")
    model = _resolved(plan)
    failed = _fails(hydrant_freeze_depth(_context(plan, model)))
    assert failed, "a wall hydrant with no seal must not silently keep its exemption"
    assert all("FX-M-PORCH-HYD" in f.element_tags for f in failed)


def test_an_uninsulated_barrel_is_an_advisory_failure(catlin_plan):
    """An advisory, not an ERROR: a bare barrel is a bad detail, not an illegal one."""
    from typehaus.findings import Severity

    plan = catlin_plan
    run = plan.by_tag("PR-S-CW-BALC-HYD-CU")
    bare = run.model_copy(update={"insulation": None})
    kept = [e for e in plan.storey_elements("second") if e.tag != run.tag]
    plan = plan.with_elements("second", (*kept, bare))
    findings = exterior_hydrant_protection(_context(plan, _resolved(plan)))
    failed = _fails(findings)
    assert [f.element_tags[0] for f in failed] == ["FX-S-BALC-HYD"]
    assert failed[0].severity is Severity.WARN
    assert "thermal bridge" in failed[0].message


# --- the finish rule and the insulation rule ------------------------------------------

def test_hot_runs_at_or_over_three_quarter_inch_are_insulated(catlin_plan, catlin_model):
    findings = hot_water_insulation(_context(catlin_plan, catlin_model))
    assert findings
    assert not _fails(findings), [f.message for f in _fails(findings)]
    # The 1/2" branches are below N1103.4.2's threshold and are not asked at all.
    graded = {f.element_tags[0] for f in findings}
    assert "PR-B-HW-TRUNK" in graded
    assert "PR-B-HW-SAUNA" not in graded


def test_supply_on_concrete_is_lacquered_copper(catlin_plan, catlin_model, catlin_prefs):
    findings = pipe_material_preference(_context(catlin_plan, catlin_model, catlin_prefs))
    assert findings, "the house states a rule; the check must grade something"
    assert not _fails(findings), [f.message for f in _fails(findings)]
    graded = {f.element_tags[0] for f in findings}
    # The trunks hung under the cast deck are exactly what the rule is about.
    assert {"PR-B-CW-TRUNK", "PR-B-HW-TRUNK", "PR-B-CW-WH"} <= graded
    # A run that never leaves a wall or a joist bay is not visible pipe and is not asked.
    assert "PR-M-CW-HYD-DIST" not in graded
    assert "PR-B-CW-HYD-RISER" not in graded


def test_the_rule_re_derives_from_what_is_overhead_not_from_a_tag_list(
        catlin_plan, catlin_model, catlin_prefs):
    """The claim preferences.toml makes: swap the cast deck for wood joists and the rule
    stops applying by itself. Proved the cheap way round — a new PEX trunk on the same
    ceiling inherits the rule with nothing authored to say so."""
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import PipeRun
    from typehaus.quantities import ft, inch, pt

    intruder = PipeRun(
        uid="TSTPM00001", tag="PR-B-CW-NEW", system=PipeSystem.WATER_COLD,
        path=(pt(ft(12), ft(6)), pt(ft(16), ft(6))), diameter=inch(0.75),
        elevations=(ft(8), ft(8)), material="pex")
    plan = catlin_plan.with_elements(
        "basement", (*catlin_plan.storey_elements("basement"), intruder))
    findings = pipe_material_preference(_context(plan, _resolved(plan), catlin_prefs))
    failed = _fails(findings)
    assert [f.element_tags[0] for f in failed] == ["PR-B-CW-NEW"]


def test_no_rule_no_findings(catlin_plan, catlin_model):
    """A house that states no preference is not a house getting it wrong."""
    assert pipe_material_preference(_context(catlin_plan, catlin_model)) == []
