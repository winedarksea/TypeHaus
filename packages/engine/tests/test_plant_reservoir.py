"""RM-S-PLANT's no-drain reservoir: the water stop out-holds the tank, the fill keeps its gap.

Oracle: ``houses/catlin/notes/plant_reservoir.md`` (arithmetic by hand, UPC 603.3.1 / 603.5.5).
Nothing in the engine grades the air gap or the tank, so these pin the authored numbers.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN

GAL_PER_M3 = 264.172
TANK_GAL = 10.0


def _stop_height_in(model) -> float:
    opening = next(o for o in model.openings if o.tag == "D-S-PLANT")
    spec = opening.doorway.components[0].specification
    riser = next(p for p in spec.parts if p.name == "water-stop riser")
    return max(z for _, z in riser.polygon_m) / M_PER_IN


def test_water_stop_holds_a_whole_tank_with_room_to_spare(catlin_model_ro):
    model = catlin_model_ro
    room = next(r for r in model.rooms if r.tag == "RM-S-PLANT")
    stop = _stop_height_in(model)
    assert stop >= 0.38 - 1e-9
    held_gal = lambda depth_in: room.area_m2 * depth_in * M_PER_IN * GAL_PER_M3  # noqa: E731
    assert held_gal(0.25) >= 21.0          # the note's 1/4" figure
    assert held_gal(stop) >= 2 * TANK_GAL  # stop height alone holds two tanks
    tank_depth_in = TANK_GAL / GAL_PER_M3 / room.area_m2 / M_PER_IN
    assert tank_depth_in < 0.25 < stop     # a full spill stands under the stop


def test_float_valve_spout_stands_over_the_rim(catlin_model_ro):
    plan = catlin_model_ro.plan
    appliance = next(a for a in plan.elements_of_kind("Appliance")
                     if a.tag == "APPL-S-PLANT-RESERVOIR")
    kind = next(t for t in plan.library.appliance_types if t.tag == appliance.type_ref)
    supply = next(p for p in kind.ports if p.tag == "supply")
    gap_in = (supply.position[2].meters - kind.height.meters) / M_PER_IN
    assert gap_in >= 1.5   # UPC Table 603.3.1, effective opening <= 1/2" near a wall
    stop = next(a for a in catlin_model_ro.pipe_accessories
                if a.tag == "PA-S-PLANT-RESERVOIR-STOP")
    assert stop.kind == "shutoff" and "APPL-S-PLANT-RESERVOIR" in stop.serves
