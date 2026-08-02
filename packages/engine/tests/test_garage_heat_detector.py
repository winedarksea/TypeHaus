"""The garage heat detector: ``AlarmKind.HEAT``, its label, its circuit, and its rule.

Half the original TODO item was already satisfied — every bedroom carries a COMBO alarm and
``code.R314_R315_alarms`` enforces it. What was missing is the garage, and it was missing on
three axes at once: ``AlarmKind`` had no rate-of-rise member, ``storeys/garage.py`` authored
no ``Alarm`` at all, and no rule looked at a garage storey (R314's filter is (SMOKE, COMBO)
and it only walks storeys with bedrooms on them, so the garage was invisible to it).

A heat detector is a kind of ``Alarm``, not a ``DeviceKind``: ``DeviceKind``'s own docstring
argues for keeping that enum flat and differentiating by ``type_ref``, and a detector is
life-safety equipment keyed to a room.
"""

from __future__ import annotations

import pytest

from typehaus.findings import Result
from typehaus.model.enums import AlarmKind, Occupancy


def _alarms(model):
    return [element for element in model.plan.all_elements()
            if element.element_kind == "Alarm"]


def _context(model):
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.registry import CheckContext, Preferences

    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2024)


# --- 1. the enum member and its one hard crash site ---------------------------------------

def test_every_alarm_kind_has_a_plan_label():
    """``_emit_alarms`` indexes a dict by ``kind.value``, so a new member without a label
    KeyErrors the whole plan sheet rather than drawing an unlabelled symbol. This is the
    test that makes that coupling visible instead of leaving it to be discovered."""
    from typehaus.emit.draw.floorplan import _emit_alarms  # noqa: F401  (import guard)
    import inspect

    from typehaus.emit.draw import floorplan

    source = inspect.getsource(floorplan._emit_alarms)
    for kind in AlarmKind:
        assert f'"{kind.value}"' in source, f"{kind} has no label in _emit_alarms"


def test_heat_is_its_own_kind():
    assert AlarmKind.HEAT.value == "heat"
    assert AlarmKind.HEAT not in (AlarmKind.SMOKE, AlarmKind.COMBO)


# --- 2. the authored detector -------------------------------------------------------------

def test_the_garage_carries_a_heat_detector(catlin_model):
    detector = next(item for item in _alarms(catlin_model) if item.tag == "AL-G-HEAT")
    assert detector.kind is AlarmKind.HEAT
    assert detector.room == "RM-GARAGE"
    garage = next(room for room in catlin_model.rooms if room.tag == "RM-GARAGE")
    assert garage.occupancy == Occupancy.GARAGE.value


def test_every_alarm_names_an_unswitched_circuit(catlin_model):
    """R314.4 wants alarms on an unswitched circuit. CKT-LT-BACKUP is the only thing here
    that survives an outage — CKT-RC-GARAGE is GFCI, which is wrong for a life-safety
    device, and there is no spare 1-pole."""
    circuits = {circuit.tag: circuit for circuit in catlin_model.plan.library.circuits}
    for alarm in _alarms(catlin_model):
        assert alarm.circuit == "CKT-LT-BACKUP", alarm.tag
    backup = circuits["CKT-LT-BACKUP"]
    assert backup.backup is True and backup.poles == 1


def test_the_alarms_reconcile_against_the_panel_schedule(catlin_model):
    """``electrical.circuit_refs`` used to walk devices, equipment and registers only, so an
    alarm naming a circuit that does not exist was not a finding. It is now."""
    from typehaus.checks.mep.electrical import circuit_refs

    findings = circuit_refs(_context(catlin_model))
    assert not [f for f in findings if f.result is Result.FAIL]

    broken = catlin_model.plan.by_tag("AL-G-HEAT").model_copy(
        update={"circuit": "CKT-NOT-A-CIRCUIT"})
    patched = catlin_model.plan.with_elements(
        "garage", [broken if element.tag == "AL-G-HEAT" else element
                   for element in catlin_model.plan.storey_elements("garage")])
    ctx = _context(catlin_model)
    failures = [f for f in circuit_refs(
        type(ctx)(plan=patched, model=catlin_model, preferences=ctx.preferences,
                  profile=ctx.profile)) if f.result is Result.FAIL]
    assert [f.element_tags for f in failures] == [("AL-G-HEAT",)]


# --- 3. the rule --------------------------------------------------------------------------

def test_the_garage_rule_passes_on_the_house_as_built(catlin_model):
    from typehaus.checks.code.mn_residential.alarms import garage_heat_and_co_alarms

    findings = garage_heat_and_co_alarms(_context(catlin_model))
    assert findings and all(f.result is Result.PASS for f in findings), [
        (f.result, f.message) for f in findings]
    # Both halves: the detector in the garage, and CO coverage on the dwelling side.
    assert any("heat detector" in f.message for f in findings)
    assert any("CO alarm" in f.message for f in findings)


def test_the_garage_rule_fails_when_the_detector_is_missing(catlin_model):
    """A rule that only ever passes proves nothing — remove the detector and it must fail."""
    from typehaus.checks.code.mn_residential.alarms import garage_heat_and_co_alarms

    ctx = _context(catlin_model)
    stripped = catlin_model.plan.with_elements(
        "garage", [element for element in catlin_model.plan.storey_elements("garage")
                   if element.tag != "AL-G-HEAT"])
    findings = garage_heat_and_co_alarms(
        type(ctx)(plan=stripped, model=catlin_model, preferences=ctx.preferences,
                  profile=ctx.profile))
    failures = [f for f in findings if f.result is Result.FAIL]
    assert [f.element_tags for f in failures] == [("RM-GARAGE",)]
    assert "no heat detector" in failures[0].message


def test_a_heat_detector_does_not_satisfy_the_bedroom_smoke_rule(catlin_model):
    """R314's filter is (SMOKE, COMBO), so a HEAT alarm is correctly invisible to it — a
    garage detector must never be mistaken for a bedroom's smoke alarm."""
    from typehaus.checks.code.mn_residential.alarms import smoke_and_co_alarm_placement

    ctx = _context(catlin_model)
    # Re-kind every bedroom alarm on the second storey to HEAT: the rule must go red.
    retyped = [element.model_copy(update={"kind": AlarmKind.HEAT})
               if element.element_kind == "Alarm" else element
               for element in catlin_model.plan.storey_elements("second")]
    patched = catlin_model.plan.with_elements("second", retyped)
    findings = smoke_and_co_alarm_placement(
        type(ctx)(plan=patched, model=catlin_model, preferences=ctx.preferences,
                  profile=ctx.profile))
    failed = {tag for f in findings if f.result is Result.FAIL for tag in f.element_tags}
    assert {"RM-S-BED1", "RM-S-BED2", "RM-S-BED3", "RM-S-SUITE"} <= failed


# --- 4. the drawing -----------------------------------------------------------------------

def test_the_detector_draws_as_HD_at_the_room_seed(catlin_model):
    from typehaus.emit.draw.floorplan import build_floorplan

    from typehaus.emit.draw.floorplan import _in

    scene = build_floorplan(catlin_model, "garage")
    labels = [node for node in scene.nodes if getattr(node, "content", None) == "HD"]
    assert len(labels) == 1
    garage = catlin_model.plan.by_tag("RM-GARAGE")
    seed_x, seed_y = garage.seed.xy_m
    # Drawn just off the seed, the same offset every alarm label uses.
    expected = _in((seed_x + 0.08, seed_y + 0.08))
    assert labels[0].anchor[0] == pytest.approx(expected[0], abs=1e-6)
    assert labels[0].anchor[1] == pytest.approx(expected[1], abs=1e-6)
    # ...and no smoke label snuck into the garage alongside it.
    assert not [node for node in scene.nodes
                if getattr(node, "content", None) in ("SD", "SD/CO")]
