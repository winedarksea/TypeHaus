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
from typehaus.checks.code.mn_residential.rules import ceiling_height
from typehaus.checks.code.mn_residential.alarms import (
    alarm_on_every_storey,
    co_alarm_outside_sleeping_areas,
)
from typehaus.checks.code.mn_residential.egress import (
    basement_storey_egress,
    egress_door_height,
    egress_windows,
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
from typehaus.model.refs import FollowRoof
from typehaus.quantities import ft, inch
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



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
               area_m2: float = 20.0, lumens: float | None = None, supply: bool = False,
               erv_cfm: float | None = None, window_type_resolves: bool = True):
    """A room with one window, and optionally the three things R303.1 Exception 1 needs.

    The exception's inputs default to absent, which is the state that matters most: a room
    short of glazing and with no artificial light stated has no lawful path and must FAIL.
    Pass ``lumens``/``supply``/``erv_cfm`` to build the room that does.

    The room's glazing totals are computed here with ``resolve.room_openings``, the same
    call ``resolve_rooms`` makes, rather than being hand-set: the check reads the totals off
    the room now, so a fixture that made them up would stop exercising the geometry that
    produces them. ``window_type_resolves=False`` is the unresolvable-type case, and it has
    to be set BEFORE the totals are taken, exactly as it would be in a real model — emptying
    the library afterwards would leave a room that had already been given its numbers.
    """
    from typehaus.model.enums import DeviceKind, DuctSystem, EquipmentKind
    from typehaus.resolve.room_openings import room_glazing_areas

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
    elements = []
    device_types = []
    equipment_types = []
    if lumens is not None:
        device_types.append(SimpleNamespace(tag="LT-T", lumens=lumens))
        elements.append(SimpleNamespace(element_kind="ElectricalDevice", tag="ED-LT",
                                        kind=DeviceKind.LIGHT, room="RM-BED",
                                        type_ref="LT-T"))
    if supply:
        elements.append(SimpleNamespace(element_kind="Register", tag="REG-SUP",
                                        kind=DuctSystem.SUPPLY, room="RM-BED"))
    if erv_cfm is not None:
        equipment_types.append(SimpleNamespace(tag="ERV-T", ventilation_cfm=erv_cfm))
        elements.append(SimpleNamespace(element_kind="Equipment", tag="EQ-ERV",
                                        kind=EquipmentKind.ERV, type_ref="ERV-T"))
    plan = SimpleNamespace(
        library=SimpleNamespace(window_types=[window_type] if window_type_resolves else [],
                                electrical_device_types=device_types,
                                equipment_types=equipment_types),
        all_elements=lambda: elements)
    model = SimpleNamespace(rooms=[room], openings=[opening],
                            wall=lambda tag: wall if tag == "W-S" else None)
    glazing = room_glazing_areas(plan, model, room)
    room.glazed_area_m2 = glazing[0] if glazing else None
    room.operable_glazed_area_m2 = glazing[1] if glazing else None
    return SimpleNamespace(plan=plan, model=model)


def test_habitable_light_passes_with_eight_percent_glazing():
    # 20 m2 = 215 sf; 8% is 17.2 sf. A 1.5 x 1.5 m casement is 24 sf, and half of it
    # (12 sf openable) clears the 4% = 8.6 sf openable requirement.
    assert _results(habitable_light_and_ventilation(_light_ctx(1.5, 1.5))) == [Result.PASS]


def test_habitable_light_fails_when_the_glazing_drops_under_eight_percent():
    findings = habitable_light_and_ventilation(_light_ctx(0.6, 0.6))
    assert _results(findings) == [Result.FAIL]
    assert "8%" in findings[0].message
    # ...and says why the lawful alternative is not open to it, rather than only the shortfall.
    assert "Exception 1 is not available" in findings[0].message


def test_habitable_light_fails_on_fixed_glass_that_passes_the_light_test():
    """The half that fails independently: a wall of fixed glass is all the daylight the code
    asks for and none of the ventilation, which is how a modern elevation gets written up."""
    findings = habitable_light_and_ventilation(_light_ctx(1.5, 1.5, operation="fixed"))
    assert _results(findings) == [Result.FAIL]
    assert "openable" in findings[0].message


def test_r303_exception_1_carries_a_windowless_room_that_is_lit_and_ventilated():
    """R303.1 Exception 1 — 6 fc of artificial light plus mechanical outdoor air.

    A 215 sf room at CU 0.60 x LLF 0.80 needs 6 x 215 / 0.48 = 2,688 lm to reach 6 fc, and
    the whole-house rate for one 215 sf conditioned room with one bedroom is 6.5 + 15 = 22
    cfm. This room clears both, so the glazing is not required and the finding is a PASS
    that names the exception.
    """
    findings = habitable_light_and_ventilation(
        _light_ctx(0.6, 0.6, lumens=3000.0, supply=True, erv_cfm=60.0))
    assert _results(findings) == [Result.PASS]
    assert "Exception 1" in findings[0].message


def test_r303_exception_1_fails_a_room_the_lighting_cannot_carry():
    """Lit, ventilated, and still short: the exception is adjudicated, not granted on
    presence. 1,000 lm over 215 sf is 2.2 fc against the 6 fc required."""
    findings = habitable_light_and_ventilation(
        _light_ctx(0.6, 0.6, lumens=1000.0, supply=True, erv_cfm=60.0))
    assert _results(findings) == [Result.FAIL]
    assert "short of the 6 fc" in findings[0].message


def test_r303_exception_1_is_unknown_when_a_fixture_states_no_lumens():
    """A fixture with no photometrics is a gap in the model, not a dark room — UNKNOWN,
    never a PASS and never a FAIL."""
    findings = habitable_light_and_ventilation(
        _light_ctx(0.6, 0.6, lumens=None, supply=True, erv_cfm=60.0))
    assert _results(findings) == [Result.FAIL]  # no luminaire at all: exception unavailable
    ctx = _light_ctx(0.6, 0.6, lumens=900.0, supply=True, erv_cfm=60.0)
    ctx.plan.library.electrical_device_types[0].lumens = None
    findings = habitable_light_and_ventilation(ctx)
    assert _results(findings) == [Result.UNKNOWN]
    assert "no lumens" in findings[0].message


def test_habitable_light_is_unknown_when_a_window_type_does_not_resolve():
    """A room whose glazing cannot be totalled is not a room with no glazing.

    The flag is passed to the fixture rather than the library being emptied afterwards,
    because the totals are taken at resolve now: a room built with a resolvable type and
    then robbed of it would carry the numbers it was already given, which is not a state a
    real model can be in."""
    ctx = _light_ctx(1.5, 1.5, window_type_resolves=False)
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
    from _railing_fixtures import railing

    return railing(tag, height=inch(36), post_spacing=ft(4), **kw)


def _railing_ctx(railings, stairs=()):
    """A ctx whose model carries the railings' *resolved* geometry, not just the elements.

    ``guard_opening_limit`` cross-checks its verdict against the drawn infill, so a ctx with
    no solids in it would exercise only half the rule — and the half that was already there
    when the balcony guard passed on an authored field while drawing nothing.
    """
    from _railing_fixtures import resolve_railings

    model = resolve_railings(railings, stairs=stairs)
    return SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: list(railings)),
        model=model,
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
    # ``members=()`` because the railing resolver now rakes a ``serves_stair`` rail along
    # this stair's nosing line: an empty flight has no walkline, so every post falls back to
    # the authored base elevation — which is exactly the flat geometry these handrail-band
    # assertions were written against.
    return SimpleNamespace(tag=tag, riser_count=risers, members=())


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


def test_afci_does_not_reach_a_240v_or_oversized_circuit():
    """E3902.16 / NEC 210.12 covers 120V single-phase 15- and 20-ampere branch circuits.

    A range, a dryer, a heat pump and an EV charger all land in rooms on the section's list,
    and none of them is what the section is about — there is no AFCI breaker made for most
    of them. Screening on the room alone wrote up eight of these in the catlin panel.
    """
    from typehaus.model.electrical import Circuit
    from typehaus.quantities import pt

    def _ctx(**circuit_kwargs):
        circuit = Circuit(uid="CKTAAAAAAA", tag="CKT-RANGE", panel_ref="ED-PANEL",
                          afci=False, **circuit_kwargs)
        device = SimpleNamespace(element_kind="ElectricalDevice", tag="ED-RANGE",
                                 circuit="CKT-RANGE", position=pt(ft(2), ft(2)),
                                 room="RM-LIVING")
        room = SimpleNamespace(tag="RM-LIVING", storey="main", occupancy="living",
                               clear_face=((0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)))
        return SimpleNamespace(
            plan=SimpleNamespace(
                library=SimpleNamespace(circuits=[circuit]),
                storeys=[SimpleNamespace(tag="main", elevation=ft(0))],
                storey_elements=lambda tag: [device] if tag == "main" else []),
            model=SimpleNamespace(rooms=[room]),
        )

    # 240V, and a 120V circuit over 20A: both out of scope, so neither is reported at all.
    assert afci_branch_circuits(_ctx(breaker_amps=50, poles=2))[0].result is Result.PASS
    assert afci_branch_circuits(_ctx(breaker_amps=30, poles=1))[0].result is Result.PASS
    # ...while the 120V 20A circuit beside them still fails.
    assert _results(afci_branch_circuits(_ctx(breaker_amps=20, poles=1))) == [Result.FAIL]


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
            plan=SimpleNamespace(all_elements=lambda: [run, dryer],
                                 library=SimpleNamespace(appliance_types=[])),
            model=SimpleNamespace(rooms=[]),
        )

    passing = [f for f in dryer_exhaust(_ctx(20)) if f.code_ref == "M1502.4.5.1"]
    assert _results(passing) == [Result.PASS]
    # One number moved: 20' to 40', past the 35' budget.
    failing = [f for f in dryer_exhaust(_ctx(40)) if f.code_ref == "M1502.4.5.1"]
    assert _results(failing) == [Result.FAIL]
    assert "35'" in failing[0].message


def test_dryer_exhaust_exempts_a_listed_condensing_dryer():
    """M1502.1 — the section does not reach a ventless heat-pump dryer.

    Without ``ApplianceType.ductless`` there is nothing to tell one from a vented dryer:
    both are boxes named "dryer" with a 240V connection, so the check demanded a duct, and
    the only way to satisfy it would have been to author a hole in the envelope for an
    appliance whose moisture leaves down a drain.
    """
    vented = SimpleNamespace(element_kind="Appliance", tag="AP-DRYER", type_ref="AT-VENTED")
    ductless = SimpleNamespace(element_kind="Appliance", tag="AP-HP-DRYER",
                               type_ref="AT-DUCTLESS")

    def _ctx(dryer, ductless_flag):
        appliance_type = SimpleNamespace(tag=dryer.type_ref, ductless=ductless_flag)
        return SimpleNamespace(
            plan=SimpleNamespace(all_elements=lambda: [dryer],
                                 library=SimpleNamespace(appliance_types=[appliance_type])),
            model=SimpleNamespace(rooms=[]))

    assert _results(dryer_exhaust(_ctx(vented, False))) == [Result.FAIL]
    findings = dryer_exhaust(_ctx(ductless, True))
    assert _results(findings) == [Result.PASS]
    assert findings[0].code_ref == "M1502.1"


def test_dryer_exhaust_charges_elbows_against_the_length_budget():
    """34' of duct passes; the same 34' with one 90-degree turn does not. That is the whole
    point of a *developed* length, and it is what makes a run measured off a tape lie."""
    from typehaus.model.enums import DuctSystem
    from typehaus.quantities import pt

    def _ctx(path):
        run = SimpleNamespace(element_kind="DuctRun", tag="DR-DRYER",
                              system=DuctSystem.DRYER, path=tuple(path), storey="main")
        return SimpleNamespace(
            plan=SimpleNamespace(all_elements=lambda: [run],
                                 library=SimpleNamespace(appliance_types=[])),
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


# --- R311.2 egress door clear height -----------------------------------------------------

def _door_height_ctx(height_in: float, *, exterior: bool = True, type_known: bool = True):
    door_type = SimpleNamespace(tag="DT-TEST", exterior=exterior, width=inch(36),
                                height=inch(height_in))
    door = SimpleNamespace(element_kind="Door", tag="D-TEST",
                           type_ref="DT-TEST" if type_known else "DT-MISSING")
    plan = SimpleNamespace(all_elements=lambda: [door],
                           library=SimpleNamespace(door_types=[door_type]))
    return SimpleNamespace(plan=plan)


def test_door_height_passes_a_standard_six_eight_leaf():
    findings = egress_door_height(_door_height_ctx(80.0))
    assert _results(findings) == [Result.PASS]


def test_door_height_fails_below_78_inches():
    findings = egress_door_height(_door_height_ctx(76.0))
    assert _results(findings) == [Result.FAIL]
    assert findings[0].code_ref == "R311.2"


def test_door_height_reports_unknown_for_an_unknown_door_type():
    findings = egress_door_height(_door_height_ctx(80.0, type_known=False))
    assert _results(findings) == [Result.UNKNOWN]


def test_interior_doors_are_not_held_to_the_egress_height_bar():
    findings = egress_door_height(_door_height_ctx(76.0, exterior=False))
    assert _results(findings) == [Result.PASS]


def test_catlin_exterior_doors_clear_the_height_bar(catlin_ctx):
    """Both breezeway-adjacent doors carry 6'-8" (80") leaves — everything passes."""
    findings = egress_door_height(catlin_ctx)
    assert findings and all(f.result is Result.PASS for f in findings)


# --- R305.1 sloped ceilings, graded against the REQUIRED floor area -----------------------
#
# Minn. R. 1309.0305 Exception 1 measures BOTH clauses against "the required floor area" —
# R304.1's 70 sf — and R304.3 says floor under 5'-0" "shall not be considered as contributing
# to the minimum required habitable area for that room". The check used to read both clauses
# against the whole room, which fails any room whose ceiling reaches the floor at the eave.
# That is a story-and-a-half, and it is legal; the misreading is what put 5'-0" knee walls in
# catlin. These pin the corrected predicate so it cannot quietly regress.

def _sloped_ctx(*, room_wide_ft: float, room_deep_ft: float, eave_ft: float, ridge_ft: float,
                span_ft: float = 36.0, occupancy=Occupancy.BEDROOM):
    """A gable ridged in y, so headroom varies with x. Storey datum is 0."""
    half, deep = span_ft / 2.0, room_deep_ft
    ring = tuple((ft(x).meters, ft(y).meters)
                 for x, y in ((0.0, 0.0), (room_wide_ft, 0.0),
                              (room_wide_ft, deep), (0.0, deep)))
    footprint = tuple((ft(x).meters, ft(y).meters)
                      for x, y in ((0.0, 0.0), (span_ft, 0.0), (span_ft, deep), (0.0, deep)))
    roof = SimpleNamespace(tag="RF", form="gable", footprint=footprint,
                           eave_z_m=ft(eave_ft).meters, ridge_z_m=ft(ridge_ft).meters,
                           ridge_direction="y")
    resolved = SimpleNamespace(tag="RM-A", storey="attic", clear_face=ring,
                               area_m2=ft(room_wide_ft).meters * ft(deep).meters)
    authored = SimpleNamespace(element_kind="Room", tag="RM-A", occupancy=occupancy,
                               ceiling=FollowRoof(roof_ref="RF"))
    storey = SimpleNamespace(tag="attic", elevation=ft(0))
    plan = SimpleNamespace(storeys=[storey], storey_elements=lambda _t: [authored],
                           all_elements=lambda: [authored],
                           project=SimpleNamespace(site=SimpleNamespace(grade=ft(-9))))
    ctx = SimpleNamespace(plan=plan, model=SimpleNamespace(rooms=[resolved], roofs=[roof]))
    assert half > 0
    return ctx, authored


def test_r305_sloped_ceiling_passes_when_the_room_reaches_the_floor_at_the_eave():
    """The story-and-a-half case. Eave at the deck, 6:12 to a 9'-0" ridge over an 18' half
    span: the west 10' of this room is under 5'-0" and contributes nothing, and the room is
    still compliant because the 70 sf it owes sits in the tall half."""
    ctx, room = _sloped_ctx(room_wide_ft=18.0, room_deep_ft=20.0, eave_ft=0.0, ridge_ft=9.0)
    finding = ceiling_height(ctx)[0]
    assert finding.result is Result.PASS
    assert "required floor area" in finding.message


def test_r305_sloped_ceiling_fails_when_seventy_good_feet_cannot_be_assembled():
    """A shallow room in the same roof: only 3'-6" of depth, so even the whole tall half is
    under 70 sf at 5'-0". This is the clause that should fail, and the only one."""
    ctx, room = _sloped_ctx(room_wide_ft=18.0, room_deep_ft=3.5, eave_ft=0.0, ridge_ft=9.0)
    finding = ceiling_height(ctx)[0]
    assert finding.result is Result.FAIL
    assert "cannot assemble" in finding.message


def test_r305_sloped_ceiling_fails_when_half_the_required_area_misses_seven_feet():
    """A roof that clears 5'-0" everywhere but 7'-0" almost nowhere: 70 sf assembles, but
    less than 35 sf of it is tall enough."""
    ctx, room = _sloped_ctx(room_wide_ft=18.0, room_deep_ft=20.0, eave_ft=5.0, ridge_ft=7.1)
    finding = ceiling_height(ctx)[0]
    assert finding.result is Result.FAIL
    assert "50%" in finding.message


def test_r305_does_not_reach_a_storage_room():
    """R305.1's subject is habitable space, hallways, bathrooms, toilet rooms and laundry
    rooms. An eave storage pocket is none of them, and grading one is a category error — the
    same argument that already excused the garage."""
    ctx, room = _sloped_ctx(room_wide_ft=18.0, room_deep_ft=20.0, eave_ft=0.0, ridge_ft=9.0,
                            occupancy=Occupancy.STORAGE)
    assert ceiling_height(ctx) == []


def test_r305_is_unknown_for_a_non_subject_room_when_the_site_states_no_grade():
    """R305.1.1's 6'-8" tier is a *basement* rule, so a storage room's applicable minimum
    depends on where grade is. With no grade datum that is undecidable, and undecidable is
    UNKNOWN — not a silent pass out of scope."""
    ctx, _room = _sloped_ctx(room_wide_ft=18.0, room_deep_ft=20.0, eave_ft=0.0, ridge_ft=9.0,
                             occupancy=Occupancy.STORAGE)
    ctx.plan.project.site.grade = None
    findings = ceiling_height(ctx)
    assert _results(findings) == [Result.UNKNOWN]
    assert "no grade datum" in findings[0].message


# --- R310.1: an escape opening has to be on an EXTERIOR wall -------------------------------
#
# The bug this pair guards was live until 2026-08-29. `_room_windows` selected windows by
# proximity to the room's clear-face boundary and nothing else, so a borrowed-light sash of
# adequate size in a bedroom's *interior* partition was credited as that bedroom's emergency
# escape opening. R310.1's subject is an opening "opening directly into a public way, yard or
# court"; a window into the hallway reaches none of them. One field moves between these two
# tests — whether the second room sits on the far side of the window's host wall — and the
# verdict flips, which is what proves the rule reads it.

def _sleeping_room_egress_ctx(*, room_on_the_far_side: bool):
    """A 4m x 3m bedroom with one 36" x 30" casement in its north wall.

    7.5 sf net clear, 36" wide, 30" tall, sill 0.9 m — comfortably past R310.2.1 on every
    dimension, so the ONLY thing that can decide this rule is whether that wall is the
    envelope or a partition.
    """
    bedroom_ring = [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]
    # Directly north of the bedroom, sharing the y = 3.0 wall. Present only in the
    # partition case; in the exterior case the far side of that wall is outdoors.
    neighbour_ring = [(0.0, 3.0), (4.0, 3.0), (4.0, 6.0), (0.0, 6.0)]

    plan_room = SimpleNamespace(element_kind="Room", tag="RM-BED",
                                occupancy=Occupancy.BEDROOM)
    bedroom = SimpleNamespace(tag="RM-BED", storey="main", occupancy="bedroom",
                              clear_face=bedroom_ring)
    rooms = [bedroom]
    if room_on_the_far_side:
        rooms.append(SimpleNamespace(tag="RM-HALL", storey="main", occupancy="hallway",
                                     clear_face=neighbour_ring))
    wall = SimpleNamespace(tag="W-N", storey="main", is_foundation=False,
                           thickness_m=0.14, axis=((0.0, 3.0), (4.0, 3.0)),
                           assembly="A-WALL")
    opening = SimpleNamespace(tag="WIN-BED", host_wall="W-N", is_door=False, type_ref="WT",
                              width_m=0.914, height_m=0.762, sill_m=0.9,
                              center_along_m=2.0)
    plan = SimpleNamespace(all_elements=lambda: [plan_room])
    model = SimpleNamespace(rooms=rooms, openings=[opening], walls=[wall],
                            wall=lambda tag: wall if tag == "W-N" else None)
    return SimpleNamespace(plan=plan, model=model)


def test_sleeping_room_egress_passes_on_a_window_in_an_exterior_wall():
    findings = egress_windows(_sleeping_room_egress_ctx(room_on_the_far_side=False))
    assert _results(findings) == [Result.PASS]
    assert "WIN-BED" in findings[0].message


def test_sleeping_room_egress_does_not_credit_a_window_in_an_interior_partition():
    """The same 7.5 sf opening, with a room put on the far side of its host wall."""
    findings = egress_windows(_sleeping_room_egress_ctx(room_on_the_far_side=True))
    assert _results(findings) == [Result.FAIL]
    assert "exterior wall" in findings[0].message
