"""A floor-heat thermostat's two raceways, derived from ``FloorHeat.thermostat_ref`` (#93).

Schluter (DITRA-HEAT) and Warmup/WarmlyYours both require the floor sensor and the heating
cable's cold lead in separate raceways from the thermostat box, never shared:

* **sensor** (``fh_sensor``) — down the stud bay from the box and through the plate,
  capped so the sensor can be replaced. Under a mat (1/2" ENT, which bends through the
  plate) it ends at the plate's foot, where the mat's own sensor sleeve takes over: a 0.84"
  tube has no room in a 3/4" tile-and-mat build-up. Over a concrete pour it runs on to the
  zone's ``stat`` point cast into the band between cable passes (3/4", WarmlyYours' capped
  tube), so it is ``cast_in``: no sleeve, no straps.
* **cold lead** (``fh_cold_lead``) — from the box straight down to the top of the bottom
  plate, 1/2" ENT.

Both start in the box's own cavity, an inch either side of its centre, so the two never
coincide. A zone whose thermostat has no box (no standard, or not on a framed wall) derives
nothing.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.quantities import inch
from typehaus.resolve.device_drops import add_derived_run
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.solid_categories import is_pour_slab

_WALL_SIZE_M = inch(0.5).meters
_SLAB_SIZE_M = inch(0.75).meters
#: Sensor centreline below a pour's top (in the cap, under the cable) or above a subfloor
#: (in the mat's sensor sleeve).
_CAST_DEPTH_M = inch(1).meters
#: Tile, mat and thinset over the subfloor: the plate stands this far under the finish.
_MAT_STACK_M = inch(0.75).meters
_BOTTOM_PLATE_M = inch(1.5).meters
_SPLIT_M = inch(1).meters
_SLAB_TOP_TOLERANCE_M = inch(6).meters


def _pour_top(model: ResolvedModel, xy: tuple[float, float], near_z: float) -> float | None:
    """Top of a pour under ``xy`` within a few inches of the floor, else None."""
    point = Point(xy)
    tops = [solid.z1_m for solid in model.solids
            if is_pour_slab(solid.category) and len(solid.outline) >= 3
            and abs(solid.z1_m - near_z) <= _SLAB_TOP_TOLERANCE_M
            and Polygon(solid.outline).contains(point)]
    return max(tops) if tops else None


def _floor_planes(model: ResolvedModel, room_tag: str | None,
                  fallback: float) -> tuple[float, float]:
    """(structural, finished) floor for the zone's room."""
    from typehaus.resolve.room_floor import room_finished_floor_elevation, room_floor_elevation

    room = next((r for r in model.rooms if r.tag == room_tag), None)
    if room is None:
        return fallback, fallback
    return room_floor_elevation(model, room), room_finished_floor_elevation(model, room)


def _beside(box, sign: int) -> tuple[float, float]:
    """A point in the box's cavity, ``_SPLIT_M`` along the wall either side of its centre."""
    depth = box.depth_m / 2
    return (box.face_point[0] - box.normal[0] * depth - box.normal[1] * sign * _SPLIT_M,
            box.face_point[1] - box.normal[1] * depth + box.normal[0] * sign * _SPLIT_M)


def derive_floor_heat_leads(model: ResolvedModel) -> None:
    for element in model.plan.all_elements():
        if element.element_kind != "FloorHeat" or not element.thermostat_ref:
            continue
        box = next((b for b in model.device_boxes
                    if b.device_tag == element.thermostat_ref), None)
        wall = model.wall(box.wall_tag) if box is not None else None
        if box is None or wall is None or box.mounting == "surface" or element.stat is None:
            continue
        stat = element.stat.xy_m
        (sx, sy), (cx, cy) = _beside(box, -1), _beside(box, 1)
        structural, finished = _floor_planes(model, element.room_ref or box.room,
                                             wall.base_ref_z_m)
        # The plate's foot: on the subfloor under a mat, on the structure over a pour.
        plate_z = max(structural, finished - _MAT_STACK_M)
        pour = _pour_top(model, stat, structural)
        cast_in = pour is not None
        sensor = ([(sx, sy, box.z0_m), (sx, sy, pour - _CAST_DEPTH_M),
                   (stat[0], stat[1], pour - _CAST_DEPTH_M)] if cast_in
                  else [(sx, sy, box.z0_m), (sx, sy, plate_z)])
        circuit = next((c for c in model.plan.library.circuits if c.tag == box.circuit), None)
        power = "power_240" if circuit is not None and circuit.poles == 2 else "power_120"
        add_derived_run(
            model, uid=f"{element.uid}-sensor", tag=f"{element.tag}-SENSOR",
            storey=box.storey, points=sensor,
            trade_size_m=_SLAB_SIZE_M if cast_in else _WALL_SIZE_M, material="ent",
            service=None, derived="fh_sensor", to_ref=box.device_tag, cast_in=cast_in)
        add_derived_run(
            model, uid=f"{element.uid}-cold-lead", tag=f"{element.tag}-COLD-LEAD",
            storey=box.storey, points=[(cx, cy, box.z0_m), (cx, cy, plate_z + _BOTTOM_PLATE_M)],
            trade_size_m=_WALL_SIZE_M, material="ent", service=power,
            derived="fh_cold_lead", to_ref=box.device_tag)
