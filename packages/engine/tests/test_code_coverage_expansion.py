"""Two-sided tests for the code rules added by the coverage expansion.

Every rule here gets three tests, following the convention ``test_stair_code_checks``
established: one geometry that passes, the *same* geometry with exactly one number moved
that fails, and one with a datum missing that reports UNKNOWN.

The one-field-moved discipline is the point. A rule that always fails is as useless as one
that always passes, and both look identical from a single-sided test; changing one number
and watching the verdict flip is what proves the rule is reading that number.

The UNKNOWN half is not optional either. Every rule in this batch has a written "cannot
evaluate" clause, and a rule that quietly passes when its input is missing is worse than no
rule — it makes a claim about a house nobody measured.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.checks.code.mn_residential.attic import attic_access
from typehaus.checks.code.mn_residential.attic_ventilation import attic_ventilation
from typehaus.checks.code.mn_residential.glazing import safety_glazing
from typehaus.checks.code.mn_residential.stairs import stair_handrail
from typehaus.checks.code.mn_residential.circulation import hallway_width
from typehaus.checks.code.mn_residential.alarms import (
    alarm_on_every_storey,
    co_alarm_outside_sleeping_areas,
)
from typehaus.checks.code.mn_residential.egress import (
    basement_storey_egress,
    exterior_door_landing,
    window_well,
)
from typehaus.checks.code.mn_residential.fall_protection import (
    guard_opening_limit,
    raised_surface_guard_height,
    window_fall_protection,
)
from typehaus.checks.code.mn_residential.fire_separation import (
    floor_assembly_protection,
    garage_separation,
)
from typehaus.checks.code.mn_residential.ventilation import (
    bathroom_exhaust,
    habitable_light_and_ventilation,
    whole_house_ventilation,
)
from typehaus.checks.code.mn_energy import air_leakage
from typehaus.checks.mep.electrical_code import afci_branch_circuits, gfci_locations
from typehaus.checks.mep.exhaust import dryer_exhaust
from typehaus.checks.mep.water_heater import water_heater_relief
from typehaus.checks.registry import Preferences
from typehaus.findings import Result
from typehaus.model.enums import AlarmKind, Occupancy
from typehaus.quantities import ft, inch
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_ctx():
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    return ctx


def _results(findings) -> list[Result]:
    return [f.result for f in findings]


# --- R311.6 hallway width ----------------------------------------------------------------

def _hall(width_m: float, length_m: float = 4.0, occupancy: str = "hallway"):
    ring = ((0.0, 0.0), (length_m, 0.0), (length_m, width_m), (0.0, width_m))
    room = SimpleNamespace(tag="RM-HALL", storey="main", occupancy=occupancy,
                           clear_face=ring, area_m2=width_m * length_m, conditioned=True)
    return SimpleNamespace(model=SimpleNamespace(rooms=[room]))


def test_hallway_width_passes_at_thirty_six_inches():
    assert _results(hallway_width(_hall(ft(3).meters + 0.01))) == [Result.PASS]


def test_hallway_width_fails_when_the_corridor_pinches_below_thirty_six():
    """One number moved: 36" to 34". A 34" hall is the classic 2x4-partition-plus-drywall
    mistake, and it is measured on the *clear face*, which is where the tape goes."""
    findings = hallway_width(_hall(ft(2, 10).meters))
    assert _results(findings) == [Result.FAIL]
    assert "34" in findings[0].message and "RM-HALL" in findings[0].message


def test_hallway_width_is_unknown_when_no_hallway_resolves():
    findings = hallway_width(_hall(1.0, occupancy="living"))
    assert _results(findings) == [Result.UNKNOWN]


# --- R310.1 basement escape --------------------------------------------------------------

def _egress_ctx(*, grade_ft: float | None, opening_w: float, opening_h: float,
                sill_m: float = 0.9, is_door: bool = False):
    storeys = [SimpleNamespace(tag="basement", elevation=ft(-9)),
               SimpleNamespace(tag="main", elevation=ft(0))]
    room = SimpleNamespace(element_kind="Room", tag="RM-B-REC",
                           occupancy=Occupancy.LIVING)
    wall = SimpleNamespace(tag="W-B-S", storey="basement", is_foundation=True,
                           thickness_m=0.3, axis=((0.0, 0.0), (6.0, 0.0)),
                           assembly="A-FOUND")
    opening = SimpleNamespace(tag="WIN-B-REC", host_wall="W-B-S", is_door=is_door,
                              type_ref=None if is_door else "WT",
                              width_m=opening_w, height_m=opening_h, sill_m=sill_m,
                              center_along_m=3.0)
    site = SimpleNamespace(grade=None if grade_ft is None else ft(grade_ft))
    plan = SimpleNamespace(
        storeys=storeys,
        storey_elements=lambda tag: [room] if tag == "basement" else [],
        project=SimpleNamespace(site=site),
    )
    model = SimpleNamespace(rooms=[], openings=[opening], walls=[wall],
                            wall=lambda tag: wall if tag == "W-B-S" else None)
    return SimpleNamespace(plan=plan, model=model)


def test_basement_egress_passes_on_a_compliant_opening():
    # 36" x 30" = 7.5 sf, past R310.2.1's 5 sf grade-floor minimum.
    ctx = _egress_ctx(grade_ft=0.0, opening_w=0.914, opening_h=0.762)
    assert _results(basement_storey_egress(ctx)) == [Result.PASS]


def test_basement_egress_fails_when_the_opening_is_too_small():
    """One number moved: the 30" height drops to 18", taking the net clear area under
    R310.2.1 and the height under its own 24" minimum."""
    ctx = _egress_ctx(grade_ft=0.0, opening_w=0.914, opening_h=0.457)
    findings = basement_storey_egress(ctx)
    assert _results(findings) == [Result.FAIL]
    assert "RM-B-REC" in findings[0].message


def test_basement_egress_is_unknown_without_a_grade_datum():
    """No grade means no way to know the storey is a basement — and a rule that assumed it
    was not would silently exempt every below-grade room in the house."""
    ctx = _egress_ctx(grade_ft=None, opening_w=0.914, opening_h=0.762)
    assert _results(basement_storey_egress(ctx)) == [Result.UNKNOWN]


def test_basement_egress_accepts_an_exterior_door_and_an_untyped_opening():
    """A walkout basement complies through its door, and this house's sunken-garden
    archways are RoughOpenings with no window type at all. A rule that filtered on a
    resolved window type would report a false FAIL against 64 sf of open wall."""
    door = _egress_ctx(grade_ft=0.0, opening_w=0.9, opening_h=2.0, is_door=True)
    assert _results(basement_storey_egress(door)) == [Result.PASS]


# --- R314.3 / R315.3 alarms --------------------------------------------------------------

def _alarm_ctx(rooms, alarms):
    by_storey = {"main": list(rooms) + list(alarms)}
    return SimpleNamespace(
        plan=SimpleNamespace(storeys=[SimpleNamespace(tag="main", elevation=ft(0))],
                             storey_elements=lambda tag: by_storey.get(tag, [])),
        model=SimpleNamespace(rooms=[]),
    )


def _room(tag, occupancy):
    return SimpleNamespace(element_kind="Room", tag=tag, occupancy=Occupancy(occupancy))


def _alarm(tag, kind, room, circuit="CKT-A"):
    return SimpleNamespace(element_kind="Alarm", tag=tag, kind=AlarmKind(kind),
                           room=room, circuit=circuit)


def test_every_storey_alarm_passes_with_a_hardwired_smoke_alarm():
    ctx = _alarm_ctx([_room("RM-REC", "living")], [_alarm("AL-1", "smoke", "RM-REC")])
    assert _results(alarm_on_every_storey(ctx)) == [Result.PASS]


def test_every_storey_alarm_fails_on_a_storey_with_none():
    """The basement case: dwelling space, no bedroom, no alarm. The older rule only visits
    storeys that have a bedroom on them, so this storey was never looked at."""
    ctx = _alarm_ctx([_room("RM-REC", "living")], [])
    findings = alarm_on_every_storey(ctx)
    assert _results(findings) == [Result.FAIL]
    assert "basements" in findings[0].message


def test_every_storey_alarm_fails_on_an_alarm_with_no_circuit():
    """R314.4: primary power from the building wiring. One field moved — the circuit goes
    away — and an alarm that cannot be interconnected stops counting."""
    ctx = _alarm_ctx([_room("RM-REC", "living")],
                     [_alarm("AL-1", "smoke", "RM-REC", circuit=None)])
    findings = alarm_on_every_storey(ctx)
    assert _results(findings) == [Result.FAIL]
    assert "R314.4" in findings[0].message


def test_every_storey_alarm_scope_passes_a_garage_only_storey():
    ctx = _alarm_ctx([_room("RM-GARAGE", "garage")], [])
    findings = alarm_on_every_storey(ctx)
    assert _results(findings) == [Result.PASS]
    assert "does not reach it" in findings[0].message


def test_every_storey_alarm_is_unknown_on_a_storey_with_no_rooms():
    ctx = _alarm_ctx([], [])
    assert _results(alarm_on_every_storey(ctx)) == [Result.UNKNOWN]


def test_co_alarm_passes_outside_the_sleeping_area_and_fails_inside_it():
    outside = _alarm_ctx([_room("RM-BED", "bedroom"), _room("RM-HALL", "hallway")],
                         [_alarm("AL-CO", "co", "RM-HALL")])
    assert _results(co_alarm_outside_sleeping_areas(outside)) == [Result.PASS]
    # One field moved: the same alarm, in the bedroom instead of the hall.
    inside = _alarm_ctx([_room("RM-BED", "bedroom"), _room("RM-HALL", "hallway")],
                        [_alarm("AL-CO", "co", "RM-BED")])
    findings = co_alarm_outside_sleeping_areas(inside)
    assert _results(findings) == [Result.FAIL]
    assert "outside each separate sleeping area" in findings[0].message


# --- R303.1 light and ventilation ---------------------------------------------------------

def _light_ctx(glazed_w: float, glazed_h: float, *, operation: str = "casement",
               area_m2: float = 20.0):
    ring = ((0.0, 0.0), (5.0, 0.0), (5.0, area_m2 / 5.0), (0.0, area_m2 / 5.0))
    room = SimpleNamespace(tag="RM-BED", storey="main", occupancy="bedroom",
                           clear_face=ring, area_m2=area_m2, conditioned=True)
    wall = SimpleNamespace(tag="W-S", storey="main", axis=((0.0, 0.0), (5.0, 0.0)),
                           thickness_m=0.3)
    opening = SimpleNamespace(tag="WIN-1", host_wall="W-S", is_door=False, type_ref="WT",
                              width_m=glazed_w, height_m=glazed_h, sill_m=0.9,
                              center_along_m=2.5)
    window_type = SimpleNamespace(tag="WT",
                                  operation=SimpleNamespace(value=operation))
    return SimpleNamespace(
        plan=SimpleNamespace(library=SimpleNamespace(window_types=[window_type])),
        model=SimpleNamespace(rooms=[room], openings=[opening],
                              wall=lambda tag: wall if tag == "W-S" else None),
    )


def test_habitable_light_passes_with_eight_percent_glazing():
    # 20 m2 = 215 sf; 8% is 17.2 sf. A 1.5 x 1.5 m casement is 24 sf, and half of it
    # (12 sf openable) clears the 4% = 8.6 sf openable requirement.
    assert _results(habitable_light_and_ventilation(_light_ctx(1.5, 1.5))) == [Result.PASS]


def test_habitable_light_fails_when_the_glazing_drops_under_eight_percent():
    findings = habitable_light_and_ventilation(_light_ctx(0.6, 0.6))
    assert _results(findings) == [Result.FAIL]
    assert "8%" in findings[0].message


def test_habitable_light_fails_on_fixed_glass_that_passes_the_light_test():
    """The half that fails independently: a wall of fixed glass is all the daylight the code
    asks for and none of the ventilation, which is how a modern elevation gets written up."""
    findings = habitable_light_and_ventilation(_light_ctx(1.5, 1.5, operation="fixed"))
    assert _results(findings) == [Result.FAIL]
    assert "openable" in findings[0].message


def test_habitable_light_is_unknown_when_a_window_type_does_not_resolve():
    ctx = _light_ctx(1.5, 1.5)
    ctx.plan.library.window_types = []
    assert _results(habitable_light_and_ventilation(ctx)) == [Result.UNKNOWN]


# --- N1102.4.1.2 air leakage --------------------------------------------------------------

def _leakage_ctx(**prefs):
    return SimpleNamespace(preferences=Preferences(**prefs))


def test_air_leakage_passes_at_three_ach50_and_fails_above_it():
    assert _results(air_leakage(_leakage_ctx(ach50=3.0))) == [Result.PASS]
    findings = air_leakage(_leakage_ctx(ach50=3.1))
    assert _results(findings) == [Result.FAIL]
    assert "3" in findings[0].message


def test_air_leakage_is_unknown_with_no_blower_door_result():
    assert _results(air_leakage(_leakage_ctx())) == [Result.UNKNOWN]


def test_air_leakage_is_unknown_when_only_cfm50_is_authored():
    """Converting CFM50 to ACH50 needs a conditioned volume this engine does not resolve.
    Guessing one would turn a measured number into an estimated verdict."""
    findings = air_leakage(_leakage_ctx(cfm50=900.0))
    assert _results(findings) == [Result.UNKNOWN]
    assert "conditioned volume" in findings[0].message


# --- the reference house ------------------------------------------------------------------

NEW_CHECKS = (
    hallway_width, basement_storey_egress, exterior_door_landing,
    raised_surface_guard_height, window_fall_protection, alarm_on_every_storey,
    co_alarm_outside_sleeping_areas, garage_separation, floor_assembly_protection,
    habitable_light_and_ventilation, bathroom_exhaust, whole_house_ventilation,
    air_leakage, gfci_locations, attic_access, attic_ventilation, safety_glazing,
    stair_handrail, guard_opening_limit, afci_branch_circuits, window_well,
    dryer_exhaust, water_heater_relief,
)


@pytest.mark.parametrize("check_fn", NEW_CHECKS, ids=lambda fn: fn.__name__)
def test_every_new_rule_actually_evaluates_something_on_the_reference_house(
        check_fn, catlin_ctx):
    """``report.ran`` proves a check was called, not that it looked at anything.

    A rule whose applicability filter is one predicate too narrow runs, emits nothing, and
    reports as covered forever — which is the failure mode the checklist meta-tests cannot
    see. Every rule here must have an opinion about this house.
    """
    findings = check_fn(catlin_ctx)
    assert findings, f"{check_fn.__name__} emitted no finding on the reference house"


@pytest.mark.parametrize("check_fn", NEW_CHECKS, ids=lambda fn: fn.__name__)
def test_every_new_rule_cites_its_section(check_fn, catlin_ctx):
    for finding in check_fn(catlin_ctx):
        assert finding.code_ref, f"{check_fn.__name__} emitted an uncited finding"


# --- schema-dependent rules ---------------------------------------------------------------
#
# The rules below could not exist before the model grew a field to answer them. Each one had
# a placeholder that reported UNKNOWN forever, which is the right answer to "is this guard
# safe" when nothing in the model can describe a guard's infill — and the wrong answer to
# keep once something can.

def _railing(tag, **kw):
    from typehaus.model.structure import Railing
    from typehaus.quantities import pt

    defaults = dict(uid=f"RL{tag[-6:]:>08}"[:10], tag=tag,
                    path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
                    height=inch(36), base_elevation=ft(0), post_spacing=ft(4))
    defaults.update(kw)
    return Railing(**defaults)


def _railing_ctx(railings, stairs=()):
    return SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: list(railings)),
        model=SimpleNamespace(stairs=list(stairs)),
    )


def test_guard_opening_limit_passes_at_four_inches_and_fails_above_it():
    tight = _railing_ctx([_railing("RL-A", infill="balusters", baluster_spacing=inch(4))])
    assert _results(guard_opening_limit(tight)) == [Result.PASS]
    # One number moved: 4" to 4.5". This is the cable-rail failure, and it is the reason
    # a height-only guard check is not a guard check.
    loose = _railing_ctx([_railing("RL-A", infill="cable", baluster_spacing=inch(4.5))])
    findings = guard_opening_limit(loose)
    assert _results(findings) == [Result.FAIL]
    assert "4.5" in findings[0].message


def test_guard_opening_limit_is_unknown_when_the_infill_is_unstated():
    findings = guard_opening_limit(_railing_ctx([_railing("RL-A")]))
    assert _results(findings) == [Result.UNKNOWN]


def test_guard_opening_limit_passes_a_solid_panel_with_no_spacing_to_measure():
    """A panel admits nothing by construction, so demanding a baluster_spacing from one
    would be demanding a measurement of something that does not exist."""
    findings = guard_opening_limit(_railing_ctx([_railing("RL-A", infill="panel")]))
    assert _results(findings) == [Result.PASS]


def _stair(tag="ST-1", risers=14):
    return SimpleNamespace(tag=tag, riser_count=risers)


def test_handrail_passes_in_band_and_fails_outside_it():
    rail = _railing("RL-H", role="handrail", serves_stair="ST-1", top_height=inch(36),
                    graspable_profile="type-I")
    assert _results(stair_handrail(_railing_ctx([rail], [_stair()]))) == [Result.PASS]
    # One number moved: 36" to 32", under R311.7.8.1's 34" floor.
    low = _railing("RL-H", role="handrail", serves_stair="ST-1", top_height=inch(32),
                   graspable_profile="type-I")
    findings = stair_handrail(_railing_ctx([low], [_stair()]))
    assert _results(findings) == [Result.FAIL]
    assert "34" in findings[0].message


def test_handrail_distinguishes_a_missing_rail_from_an_unmodeled_one():
    """A house with handrails, one flight without: a deficiency. A house that has never
    authored a handrail role: a modeling gap. Collapsing them would fail every house that
    has not adopted the field."""
    elsewhere = _railing("RL-H", role="handrail", serves_stair="ST-OTHER",
                         top_height=inch(36), graspable_profile="type-I")
    missing = stair_handrail(_railing_ctx([elsewhere], [_stair()]))
    assert _results(missing) == [Result.FAIL]

    unmodeled = stair_handrail(_railing_ctx([_railing("RL-G")], [_stair()]))
    assert _results(unmodeled) == [Result.UNKNOWN]


def test_handrail_scope_passes_a_flight_under_four_risers():
    findings = stair_handrail(_railing_ctx([], [_stair(risers=3)]))
    assert _results(findings) == [Result.PASS]


def test_safety_glazing_fails_an_untempered_glazed_door_and_passes_a_tempered_one():
    from typehaus.model.types import DoorType

    def _ctx(tempered):
        door_type = DoorType(tag="DT-G", width=ft(3), height=ft(7), glazed=True,
                             tempered=tempered)
        opening = SimpleNamespace(tag="D-1", is_door=True, type_ref="DT-G",
                                  host_wall="W-1", width_m=0.9, height_m=2.0, sill_m=0.0,
                                  center_along_m=1.0)
        return SimpleNamespace(
            plan=SimpleNamespace(
                library=SimpleNamespace(window_types=[], door_types=[door_type]),
                storeys=[SimpleNamespace(tag="main", elevation=ft(0))]),
            model=SimpleNamespace(rooms=[], openings=[opening], stairs=[],
                                  wall=lambda tag: None),
        )

    findings = safety_glazing(_ctx(False))
    assert _results(findings) == [Result.FAIL]
    assert "R308.4.1" == findings[0].code_ref
    assert _results(safety_glazing(_ctx(True))) == [Result.PASS]


def test_afci_passes_a_protected_circuit_and_fails_an_unprotected_one():
    from typehaus.model.electrical import Circuit
    from typehaus.quantities import pt

    def _ctx(afci):
        circuit = Circuit(uid="CKTAAAAAAA", tag="CKT-BED", panel_ref="ED-PANEL",
                          breaker_amps=15, afci=afci)
        device = SimpleNamespace(element_kind="ElectricalDevice", tag="ED-BED-RC1",
                                 circuit="CKT-BED", position=pt(ft(2), ft(2)),
                                 room="RM-BED")
        room = SimpleNamespace(tag="RM-BED", storey="main", occupancy="bedroom",
                               clear_face=((0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)))
        return SimpleNamespace(
            plan=SimpleNamespace(
                library=SimpleNamespace(circuits=[circuit]),
                storeys=[SimpleNamespace(tag="main", elevation=ft(0))],
                storey_elements=lambda tag: [device] if tag == "main" else []),
            model=SimpleNamespace(rooms=[room]),
        )

    assert _results(afci_branch_circuits(_ctx(True))) == [Result.PASS]
    findings = afci_branch_circuits(_ctx(False))
    assert _results(findings) == [Result.FAIL]
    assert "CKT-BED" in findings[0].message


def test_dryer_exhaust_passes_a_short_run_and_fails_a_long_one():
    from typehaus.model.enums import DuctSystem
    from typehaus.quantities import pt

    def _ctx(length_ft, turns=0):
        path = [pt(ft(0), ft(0)), pt(ft(length_ft), ft(0))]
        if turns:
            path.append(pt(ft(length_ft), ft(10)))
        run = SimpleNamespace(element_kind="DuctRun", tag="DR-DRYER",
                              system=DuctSystem.DRYER, path=tuple(path), storey="main")
        dryer = SimpleNamespace(element_kind="Appliance", tag="AP-DRYER",
                                type_ref="AT-DRYER")
        return SimpleNamespace(
            plan=SimpleNamespace(all_elements=lambda: [run, dryer]),
            model=SimpleNamespace(rooms=[]),
        )

    passing = [f for f in dryer_exhaust(_ctx(20)) if f.code_ref == "M1502.4.5.1"]
    assert _results(passing) == [Result.PASS]
    # One number moved: 20' to 40', past the 35' budget.
    failing = [f for f in dryer_exhaust(_ctx(40)) if f.code_ref == "M1502.4.5.1"]
    assert _results(failing) == [Result.FAIL]
    assert "35'" in failing[0].message


def test_dryer_exhaust_charges_elbows_against_the_length_budget():
    """34' of duct passes; the same 34' with one 90-degree turn does not. That is the whole
    point of a *developed* length, and it is what makes a run measured off a tape lie."""
    from typehaus.model.enums import DuctSystem
    from typehaus.quantities import pt

    def _ctx(path):
        run = SimpleNamespace(element_kind="DuctRun", tag="DR-DRYER",
                              system=DuctSystem.DRYER, path=tuple(path), storey="main")
        return SimpleNamespace(plan=SimpleNamespace(all_elements=lambda: [run]),
                               model=SimpleNamespace(rooms=[]))

    straight = [f for f in dryer_exhaust(_ctx([pt(ft(0), ft(0)), pt(ft(34), ft(0))]))
                if f.code_ref == "M1502.4.5.1"]
    assert _results(straight) == [Result.PASS]
    bent = [f for f in dryer_exhaust(_ctx([pt(ft(0), ft(0)), pt(ft(29), ft(0)),
                                           pt(ft(29), ft(5))]))
            if f.code_ref == "M1502.4.5.1"]
    assert _results(bent) == [Result.FAIL]


def test_water_heater_relief_fails_a_discharge_that_rises():
    from typehaus.model.enums import EquipmentKind
    from typehaus.quantities import pt

    def _ctx(z_profile):
        heater = SimpleNamespace(element_kind="Equipment", tag="EQ-WH",
                                 kind=EquipmentKind.WATER_HEATER,
                                 position=pt(ft(1), ft(1)), storey="basement",
                                 relief_discharge_ref="PR-TPR", drain_pan=False)
        run = SimpleNamespace(tag="PR-TPR", z_m=tuple(z_profile),
                              z_start_m=z_profile[0], z_end_m=z_profile[-1])
        slab = SimpleNamespace(category="slab", tag="SL-B",
                               outline=((0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0)))
        return SimpleNamespace(
            plan=SimpleNamespace(all_elements=lambda: [heater],
                                 storeys=[SimpleNamespace(tag="basement", elevation=ft(0))]),
            model=SimpleNamespace(pipe_runs=[run], solids=[slab], rooms=[]),
        )

    # Drains downhill and terminates 12" above the floor.
    good = [f for f in water_heater_relief(_ctx([1.0, 0.6, 0.305]))
            if f.code_ref == "P2804.6.1"]
    assert _results(good) == [Result.PASS]
    # One profile point moved: the run now climbs on its way out, so it holds water.
    bad = [f for f in water_heater_relief(_ctx([1.0, 0.3, 0.9]))
           if f.code_ref == "P2804.6.1"]
    assert _results(bad) == [Result.FAIL]
    assert "rises" in bad[0].message


def test_water_heater_relief_is_unknown_when_no_discharge_is_named():
    from typehaus.model.enums import EquipmentKind
    from typehaus.quantities import pt

    heater = SimpleNamespace(element_kind="Equipment", tag="EQ-WH",
                             kind=EquipmentKind.WATER_HEATER, position=pt(ft(1), ft(1)),
                             storey="basement", relief_discharge_ref=None, drain_pan=False)
    ctx = SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [heater],
                             storeys=[SimpleNamespace(tag="basement", elevation=ft(0))]),
        model=SimpleNamespace(pipe_runs=[], solids=[], rooms=[]),
    )
    assert _results(water_heater_relief(ctx)) == [Result.UNKNOWN]


# --- the new schema survives a round trip -------------------------------------------------

def test_every_new_library_field_survives_json():
    """The library types added for these rules are only useful if they reach the check that
    reads them, and the library crosses JSON on the way to the viewer. A field that
    serializes to nothing turns a real verdict into a silent UNKNOWN."""
    from typehaus.model.electrical import Circuit
    from typehaus.model.materials import Material
    from typehaus.model.types import DoorType, WindowType

    cases = [
        Material(tag="gwb-x", name="Type X", gypsum_type="type-x"),
        DoorType(tag="DT", width=ft(3), height=ft(7), core="solid",
                 fire_rating_minutes=20, self_closing=True, tempered=True),
        WindowType(tag="WT", width=ft(3), height=ft(4), tempered=True,
                   fall_protection="limiter"),
        Circuit(uid="CKTAAAAAAA", tag="CKT-1", panel_ref="P", breaker_amps=15, afci=True),
    ]
    for original in cases:
        restored = type(original).model_validate_json(original.model_dump_json())
        assert restored == original, f"{type(original).__name__} lost data on round trip"


def test_the_new_geometric_elements_round_trip_through_a_model_dump():
    """``Railing`` and ``WindowWell`` carry ``Point2D``, whose JSON form is the authoring
    repr rather than a number pair — the plan's real persistence is Python source, not
    JSON. What has to hold is that the new fields survive a structural copy, which is the
    path writeback and every model_copy in the resolver take."""
    from typehaus.model.site import WindowWell
    from typehaus.model.structure import Railing
    from typehaus.quantities import pt

    railing = Railing(
        uid="RLAAAAAAAA", tag="RL-1", path=(pt(ft(0), ft(0)), pt(ft(4), ft(0))),
        height=inch(36), base_elevation=ft(0), post_spacing=ft(4),
        role="guard_and_handrail", serves_stair="ST-1", top_height=inch(36),
        graspable_profile="type-II", infill="balusters", baluster_spacing=inch(3.5))
    assert Railing.model_validate(railing.model_dump()) == railing

    well = WindowWell(
        uid="WWAAAAAAAA", tag="WW-1", serves_opening="WIN-1",
        outline=(pt(ft(0), ft(0)), pt(ft(4), ft(0)), pt(ft(4), ft(3)), pt(ft(0), ft(3))),
        floor_elevation=ft(-8), ladder=True, ladder_width=inch(14), drained=True)
    assert WindowWell.model_validate(well.model_dump()) == well


def test_the_new_railing_fields_default_so_existing_houses_load_unchanged():
    """Every field added to ``Railing`` is optional on purpose. A house authored before the
    handrail role existed must keep loading, and must report UNKNOWN rather than a verdict
    invented from a default."""
    from typehaus.model.structure import Railing
    from typehaus.quantities import pt

    plain = Railing(uid="RLBBBBBBBB", tag="RL-2",
                    path=(pt(ft(0), ft(0)), pt(ft(4), ft(0))), height=inch(36),
                    base_elevation=ft(0), post_spacing=ft(4))
    assert plain.role == "guard"
    assert plain.infill is None and plain.baluster_spacing is None
    assert plain.top_height is None and plain.graspable_profile is None


def test_window_well_is_registered_as_a_constructible_element():
    """A new element kind that skips ``register_constructor`` loads in Python and fails in
    every house file that names it."""
    from typehaus.model.registry import constructor_names, element_kinds

    assert "WindowWell" in constructor_names()
    assert "WindowWell" in element_kinds()
