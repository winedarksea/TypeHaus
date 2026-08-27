"""Structured cabling: the raceway service split, the reachability graph, and the export.

The house under test is catlin, whose data system is one patch enclosure feeding three PoE
access points up the shared radon/plumbing chase, plus a capped 2" spare.
"""

from __future__ import annotations

import pathlib

import pytest

from typehaus.model.enums import Service
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



def _findings(model, check_id: str):
    import typehaus.checks.mep  # noqa: F401 - registers the mep checks
    from typehaus.checks.registry import (CheckContext, JurisdictionProfile, Preferences,
                                          registered)

    fn = next(fn for cid, fn in registered() if cid == check_id)
    return fn(CheckContext(
        plan=model.plan, model=model, preferences=Preferences(),
        profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                    irc_base="t", coverage_statement="t")))


def test_data_raceways_carry_their_service_and_the_spare_carries_none(catlin_model):
    by_tag = {run.tag: run for run in catlin_model.conduits}
    assert by_tag["CD-B-DATA-CHASE"].service == "data"
    assert by_tag["CD-A-DATA-NE"].service == "data"
    # A capped spare is neither power nor data. Giving it either would pre-decide what gets
    # pulled through it, and it would then be billed as wire that does not exist.
    assert by_tag["CD-B-SPARE-CHASE"].service is None
    assert by_tag["CD-B-ATTIC-RISER"].service == "power_120"


def test_power_and_data_raceways_are_billed_apart(catlin_model):
    """One 3/4" power run and one 3/4" data run must not merge into a single 80-foot row —
    comms and power are separate orders pulled by separate trades on separate days."""
    from typehaus.takeoff import conduit_takeoff, data_raceway_takeoff

    power_tags = {tag for row in conduit_takeoff(catlin_model) for tag in row["tags"]}
    data_tags = {tag for row in data_raceway_takeoff(catlin_model) for tag in row["tags"]}
    assert not power_tags & data_tags
    assert "CD-M-DATA-KITCH" in data_tags and "CD-B-KITCHEN" in power_tags
    # The spare rides the low-voltage schedule — the reader who wants to know what can still
    # be pulled is that one — and is labelled rather than silently counted as data.
    spare = next(row for row in data_raceway_takeoff(catlin_model)
                 if row["service"] == "spare")
    assert spare["trade_size_in"] == 2.0 and spare["tags"] == ["CD-B-SPARE-CHASE"]


def test_poe_load_is_not_on_the_panel_schedule(catlin_model):
    """A PoE access point names no circuit, so its watts can only be read on E-603."""
    from typehaus.takeoff import poe_budget

    budget = poe_budget(catlin_model)
    assert budget["powered_devices"] == 3
    assert budget["connected_watts"] == pytest.approx(45.0)
    aps = [element for storey in catlin_model.plan.storeys
           for element in catlin_model.plan.storey_elements(storey.tag)
           if element.element_kind == "ElectricalDevice"
           and element.kind.value == "data_outlet"
           and element.tag != "ED-B-NET-PATCH"]
    assert aps and all(ap.circuit is None for ap in aps)


def test_data_reachability_passes_and_catches_an_orphaned_access_point(catlin_model):
    results = {f.result.value for f in _findings(catlin_model, "electrical.data_reachability")}
    assert results == {"pass"}

    # Drop the raceway that serves the attic AP; the AP must be reported, not ignored.
    plan = catlin_model.plan
    storey = "attic"
    kept = [e for e in plan.storey_elements(storey)
            if getattr(e, "tag", None) != "CD-A-DATA-NE"]
    pruned = plan.with_elements(storey, kept)
    model, _ = resolve(pruned)
    failures = [f for f in _findings(model, "electrical.data_reachability")
                if f.result.value == "fail"]
    assert any("ED-A-EAST-AP" in f.message for f in failures)


def test_conduit_crossings_of_concrete_are_sleeved(catlin_model):
    """The pour-day walk covers raceways, not only pipe: a raceway crossing a deck that
    cured without a sleeve gets cored exactly like a drain does."""
    from typehaus.resolve.mep import concrete_crossings

    conduit = [c for c in concrete_crossings(catlin_model)
               if str(c["run"]).startswith("CD-")]
    assert conduit, "conduit must be walked against concrete at all"
    assert not [c for c in conduit if c["sleeve"] is None]


def test_a_raceway_cannot_claim_a_plumbing_sleeve(catlin_model):
    """Proximity alone let a 1" power raceway match a 3" drain sleeve 2" away — reported as
    a PASS, and it stole the sleeve from the drain that really threads it."""
    from typehaus.resolve.mep import concrete_crossings

    purposes = {s.tag: s.purpose for s in catlin_model.sleeves}
    plumbing = {"drain", "vent", "water_cold", "water_hot", "gas"}
    for crossing in concrete_crossings(catlin_model):
        if crossing["sleeve"] is None or not str(crossing["run"]).startswith("CD-"):
            continue
        assert purposes[crossing["sleeve"]] not in plumbing, crossing


def test_low_voltage_devices_export_as_communications_appliances(catlin_ifc_path):
    """DeviceKind is the symbol axis; the IFC class rides the product type, which is what
    keeps a PoE camera a catalog entry instead of a patch to five engine maps."""
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))
    appliances = {p.Name: p.PredefinedType for p in f.by_type("IfcCommunicationsAppliance")}
    assert appliances == {
        "ED-B-NET-PATCH": "NETWORKHUB",
        "ED-M-KITCH-AP": "NETWORKAPPLIANCE",
        "ED-M-PORCH-AP": "NETWORKAPPLIANCE",
        "ED-A-EAST-AP": "NETWORKAPPLIANCE",
        # The three hardwired drops, 2026-08-22. They are the first instances of
        # ED-T-DATA-JACK: the catalog had an enclosure and two access points and no way to
        # say "a cable ends here at a plate", so a wall jack could not be modelled at all.
        "ED-B-WORKSHOP-DATA1": "NETWORKAPPLIANCE",
        "ED-M-STUDY-DATA1": "NETWORKAPPLIANCE",
        "ED-B-PLAY-N-DATA1": "NETWORKAPPLIANCE",
    }
    systems = {s.Name: s.PredefinedType for s in f.by_type("IfcDistributionSystem")}
    assert systems["Data"] == "COMMUNICATION"
    data = next(s for s in f.by_type("IfcDistributionSystem") if s.Name == "Data")
    members = {o.Name for o in data.IsGroupedBy[0].RelatedObjects}
    assert "ED-A-EAST-AP" in members
    # The capped spare joins no system: an empty pipe distributes nothing, and a reader
    # should see it that way.
    assert not any(str(name).startswith("CD-B-SPARE") for name in members)


def test_the_starter_house_still_builds_without_any_data_system():
    """`ConduitRun.service` and the type-level IFC fields must default to the old behaviour."""
    from typehaus.takeoff import poe_budget

    starter = CATLIN_DIR.parent / "starter"
    model, findings = resolve(load_plan(starter).plan)
    assert not [f for f in findings if f.severity.value == "error"]
    assert poe_budget(model) == {}
    assert all(run.service == Service.POWER_120.value for run in model.conduits)
