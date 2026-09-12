"""The two MEP holes that a rule iterating over *runs* is structurally unable to see.

``mep.duct_connectivity`` walks duct ends, so it cannot notice a machine nobody drew a duct
to (``mep.equipment_port_service``), and ``mep.duct_joist_bay`` grades one run at a time
against the framing, so it cannot notice two runs in one bay
(``mep.duct_joist_bay_occupancy``). Plus the two small predicates the pair shares:
``Register.duct_ref`` validation, and the duct<->duct joint that stops a real tee inside a
soffit from reading as a hanger-gap conflict.
"""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model.enums import AIR_SERVICE_DUCT_SYSTEM, DuctSystem, Service


def _findings(model, check_id, tier=Tier.INTEGRITY):
    return [f for f in run_from_model(model, [], tier=tier).findings
            if f.check_id == check_id]


# --- the Service -> DuctSystem map ------------------------------------------------------


def test_every_air_service_maps_to_its_own_duct_system():
    """The four air services and no others. A POWER or DRAIN entry would be a claim that a
    duct connects them, which is the one thing this table must never say."""
    assert AIR_SERVICE_DUCT_SYSTEM == {
        Service.SUPPLY_AIR: DuctSystem.SUPPLY,
        Service.RETURN_AIR: DuctSystem.RETURN,
        Service.EXHAUST_AIR: DuctSystem.EXHAUST,
        Service.OUTDOOR_AIR: DuctSystem.OUTDOOR_AIR,
    }


# --- mep.equipment_port_service ---------------------------------------------------------


def test_every_air_port_in_catlin_is_reached_or_explained(catlin_model):
    findings = _findings(catlin_model, "mep.equipment_port_service")
    assert findings, "the check must speak for a house with an ERV in it"
    orphans = [f.message for f in findings if f.result.value == "fail"]
    assert not orphans, orphans


def test_the_erv_is_reached_on_all_four_of_its_sides(catlin_model):
    """EQ-B-ERV is the regression this check exists for: it stood for a fortnight with four
    declared ports and no duct to either manifold, and every check in the engine passed."""
    served = [f for f in _findings(catlin_model, "mep.equipment_port_service")
              if f.element_tags == ("EQ-B-ERV",)]
    assert len(served) == 1
    assert served[0].result.value == "pass"
    for system in ("supply", "return", "exhaust", "outdoor_air"):
        assert system in served[0].message


def test_deleting_the_supply_trunk_orphans_the_manifold(catlin_model):
    """The point of the rule. Nothing lands on a manifold nobody drew a duct to, so no rule
    that walks duct *ends* can report it — remove the two runs that reach EQ-B-ERV-MAN-SUP
    and the manifold has to be the thing that speaks up."""
    keep = tuple(d for d in catlin_model.ducts
                 if not d.tag.startswith(("DU-B-ERV-SUP-TRUNK", "DU-B-ERV-R-",
                                          "DU-ERV-RISER-SUP")))
    stripped = catlin_model.__class__(**{**catlin_model.__dict__, "ducts": keep})
    orphaned = [f.message for f in _findings(stripped, "mep.equipment_port_service")
                if f.result.value == "fail"]
    assert any("EQ-B-ERV-MAN-SUP" in m for m in orphaned), orphaned


def test_the_discharge_hood_declares_the_direction_it_is_placed_in(catlin_model):
    """The house side of the same question, since 2026-09-11. EQ-S-ERV-HOOD-EA used to
    borrow EQ-T-ERV-HOOD-6 — one casting, one row, OUTDOOR_AIR stated once — and could only
    read UNKNOWN. It is EQ-T-ERV-HOOD-6-EXH now: the same casting on a second catalog row at
    the same rate, declaring EXHAUST_AIR, which is the direction its damper is hung in."""
    hood = [f for f in _findings(catlin_model, "mep.equipment_port_service")
            if f.element_tags == ("EQ-S-ERV-HOOD-EA",)]
    assert len(hood) == 1
    assert hood[0].result.value == "pass"
    assert "DU-ERV-EA" in hood[0].message


def test_a_reversible_casting_is_unknown_and_not_a_failure(catlin_model):
    """The UNKNOWN arm, now that no placement in catlin exercises it — so it is forced on a
    synthetic model rather than deleted with the house edit that closed it.

    Retype the discharge hood back to EQ-T-ERV-HOOD-6, the intake's row, and the check is
    looking at a reversible casting stated once: the type declares OUTDOOR_AIR and the run
    that reaches the case carries EXHAUST. Nothing is wrong with that building either — what
    is missing is a model that can say a type is directional and a placement reverses it, and
    a FAIL would report the catalog rather than the house. Splitting the row is what this
    house did about it; a house that has not may still hit this arm."""
    hood = next(el for el in catlin_model.plan.all_elements()
                if el.tag == "EQ-S-ERV-HOOD-EA")
    assert hood.type_ref == "EQ-T-ERV-HOOD-6-EXH"
    reversed_casting = hood.model_copy(update={"type_ref": "EQ-T-ERV-HOOD-6"})
    plan = _plan_with(catlin_model.plan, hood.tag, reversed_casting)
    model = catlin_model.__class__(**{**catlin_model.__dict__, "plan": plan})
    finding = [f for f in _findings(model, "mep.equipment_port_service")
               if f.element_tags == ("EQ-S-ERV-HOOD-EA",)]
    assert len(finding) == 1
    assert finding[0].result.value == "unknown"
    assert "DU-ERV-EA" in finding[0].message
    assert "reversible casting" in finding[0].message


# --- integrity.register_duct_ref --------------------------------------------------------


def test_catlin_registers_all_name_a_real_run(catlin_model):
    findings = _findings(catlin_model, "integrity.register_duct_ref")
    assert [f.result.value for f in findings] == ["pass"]


def test_a_typo_in_duct_ref_is_an_error_not_an_unserved_run(catlin_model):
    """Every consumer reads the field defensively, so before this arm a typo read exactly
    like a run with no take-off — the grille lost its duct and nothing anywhere said so."""
    register = next(el for el in catlin_model.plan.all_elements()
                    if el.element_kind == "Register" and el.duct_ref is not None)
    broken = register.model_copy(update={"duct_ref": register.duct_ref + "-TYPO"})
    plan = _plan_with(catlin_model.plan, register.tag, broken)
    model = catlin_model.__class__(**{**catlin_model.__dict__, "plan": plan})
    bad = [f for f in _findings(model, "integrity.register_duct_ref")
           if f.result.value == "fail"]
    assert len(bad) == 1
    assert broken.duct_ref in bad[0].message


def test_a_transfer_louver_needs_no_duct_ref(catlin_model):
    """REG-M-XFER-MUD carries none by design — a passive opening belongs to no ducted
    system — so it is skipped rather than excused, and the house still reports clean."""
    louver = next(el for el in catlin_model.plan.all_elements()
                  if el.element_kind == "Register" and el.duct_ref is None)
    assert louver.kind is DuctSystem.TRANSFER


def _plan_with(plan, tag, replacement):
    """A copy of ``plan`` with the one element of ``tag`` swapped out."""
    swapped = {key: tuple(replacement if el.tag == tag else el for el in group)
               for key, group in plan.elements.items()}
    return plan.model_copy(update={"elements": swapped})


# --- the duct<->duct joint predicate ----------------------------------------------------


def test_a_tee_is_a_joint_and_a_crossing_is_not(catlin_model):
    """``ducts_are_joined`` is the same predicate ``mep.duct_connectivity`` uses to decide
    an end has landed on something, asked with the sign flipped. Only an END counts: two
    runs crossing mid-span are two runs crossing, which is the case the occupancy checks
    exist to report."""
    from typehaus.resolve.mep_soffit import ducts_are_joined

    assert ducts_are_joined(catlin_model, "DU-S-HP-SUITE", "DU-S-HP-SUP")
    assert ducts_are_joined(catlin_model, "DU-S-HP-SUP", "DU-S-HP-SUITE")  # symmetric
    assert not ducts_are_joined(catlin_model, "DU-S-HP-SUP", "DU-ERV-OA")


def test_the_soffit_check_no_longer_calls_a_tee_a_hanger_gap(catlin_model):
    """``_pair_is_plumbed`` returned False unconditionally for a duct<->duct pair, so a
    branch teeing off a trunk *inside a soffit* — which is where a branch tees off a trunk —
    read as two things crowding one box with 0" between them."""
    from typehaus.resolve.mep_soffit import SoffitOccupant, _pair_is_plumbed

    def leg(tag):
        duct = next(d for d in catlin_model.ducts if d.tag == tag)
        return SoffitOccupant(tag=tag, kind="duct", along=(0.0, 1.0), across=(0.0, 1.0),
                              z=(0.0, 1.0)) if duct else None

    assert _pair_is_plumbed(catlin_model, leg("DU-S-HP-SUITE"), leg("DU-S-HP-SUP"))
    assert not _pair_is_plumbed(catlin_model, leg("DU-S-HP-SUP"), leg("DU-ERV-OA"))


# --- mep.duct_joist_bay_occupancy -------------------------------------------------------


def test_no_pair_of_bay_runs_in_catlin_exceeds_its_bay(catlin_model):
    findings = _findings(catlin_model, "mep.duct_joist_bay_occupancy", Tier.STRUCTURAL)
    assert findings
    over = [f.message for f in findings if f.result.value == "fail"]
    assert not over, over


def test_two_lanes_on_one_bay_centre_are_reported_as_unknown(catlin_model):
    """FS-S-WEST is the floor the TODO named. ``plan/mep_erv.py`` records in prose that
    STUDY and LAUNDRY both ride the 20'-8" bay and that "nothing in the engine grades
    duct-against-duct outside a modeled Soffit"; this is the check that does. It is UNKNOWN
    rather than FAIL because the model gives a run one centreline per bay — two lanes in one
    bay are necessarily drawn on top of each other — and the bay is wide enough for both."""
    west = [f for f in _findings(catlin_model, "mep.duct_joist_bay_occupancy",
                                 Tier.STRUCTURAL)
            if f.element_tags == ("FS-S-WEST",)]
    assert len(west) == 1
    assert west[0].result.value == "unknown"
    assert "DU-M-ERV-R-STUDY" in west[0].message
    assert "DU-M-ERV-R-LAUNDRY" in west[0].message


def test_crossing_runs_are_not_paired(catlin_model):
    """Between two runs that cross, a hanger-gap subtraction returns a number with no
    meaning — the first draft reported "-112 inches of gap" for the FS-S-WEST radials.
    Whether a run may cross a joist line at all is ``mep.duct_joist_bay``'s question."""
    west = next(f for f in _findings(catlin_model, "mep.duct_joist_bay_occupancy",
                                     Tier.STRUCTURAL)
                if f.element_tags == ("FS-S-WEST",))
    assert "-" not in west.message.split("overlapping by")[1].split('"')[0]


def test_a_bay_the_pair_cannot_fit_fails(catlin_model):
    """The FAIL half, forced: fatten two runs that already share a bay past its clear width
    and the verdict must move off UNKNOWN, because then it is no longer the drawing's
    limitation — the bay genuinely does not hold them."""
    fat = tuple(d.__class__(**{**d.__dict__, "width_m": 0.30})
                if d.tag in {"DU-M-ERV-R-STUDY", "DU-M-ERV-R-LAUNDRY"} else d
                for d in catlin_model.ducts)
    model = catlin_model.__class__(**{**catlin_model.__dict__, "ducts": fat})
    west = next(f for f in _findings(model, "mep.duct_joist_bay_occupancy", Tier.STRUCTURAL)
                if f.element_tags == ("FS-S-WEST",))
    assert west.result.value == "fail", west.message


# --- schema additions (step 5) ----------------------------------------------------------


def test_the_only_serviceable_face_on_system_1_states_its_filter(catlin_plan):
    """EQ-S-HP1-AH hangs in SF-S-HP1 with no filter cabinet, so REG-T-HP-RET's hinged face
    is the only filter in the system — and until now that lived only in a prose ``source``."""
    grille = next(t for t in catlin_plan.library.register_types
                  if t.tag == "REG-T-HP-RET")
    assert grille.filter_nominal_size == "28x12x1"
    assert grille.filter_merv == 13
    assert grille.service_face == "bottom"


def test_the_new_installation_fields_are_additive_and_default_off(catlin_plan):
    """No catlin equipment declares any of them yet; the point of the batch is that they
    have somewhere to live, not that anything changed."""
    equipment = [el for el in catlin_plan.all_elements() if el.element_kind == "Equipment"]
    assert equipment
    for unit in equipment:
        assert unit.behind_access_panel is False
        assert unit.access_panel_ref is None
        assert unit.blower_interlock_ref is None


def test_a_trap_primer_is_a_pipe_accessory_kind():
    """The enum member only. The RM-S-PLANT floor drain it unblocks is deliberately not
    authored here, and no rule reads it: "a dry room needs a primer" needs a notion of which
    rooms are wetted that this model does not have."""
    from typehaus.model.enums import PipeAccessoryKind

    assert PipeAccessoryKind.TRAP_PRIMER.value == "trap_primer"


@pytest.mark.parametrize("field", ["filter_nominal_size", "filter_merv", "service_face"])
def test_both_air_side_type_families_carry_the_product_facts(field):
    """The filter in this house is not in the machine — it is behind a *register* — so the
    facts have to be sayable of both families or they have nowhere to live."""
    from typehaus.model.types import EquipmentType, RegisterType

    assert field in EquipmentType.model_fields
    assert field in RegisterType.model_fields
