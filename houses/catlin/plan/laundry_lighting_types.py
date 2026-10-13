"""Laundry task lighting: stock rail cut to fit, two heads on channel one."""

from params.main_deck import MAIN_FINISHED_FLOOR_LVP
from typehaus.library.track_lighting import (
    PUREEDGE_SUPPLY, aim_head_at, magnetic_track_spec, radiant_medium, track_luminaire,
)
from typehaus.model import TrackHeadSpec
from typehaus.quantities import inch

RAIL_CENTER_IN = (130.7, 258.0)
CEILING_IN = 108.0
MACHINE_ADAPTER_X_IN = 115.83
SINK_ADAPTER_X_IN = 145.55
# The appliance's north/front face and the basin's front interior. Fixture bodies are
# floor-relative, so their task elevations follow the same finished walking surface.
TASK_TARGETS_IN = (
    (MACHINE_ADAPTER_X_IN, 253.012, MAIN_FINISHED_FLOOR_LVP.inches + 74.375 / 2),
    (SINK_ADAPTER_X_IN, 240.0, MAIN_FINISHED_FLOOR_LVP.inches + 34.0),
)
_HEADS = tuple(TrackHeadSpec(product=radiant_medium(),
                            offset=inch(x - RAIL_CENTER_IN[0]), azimuth_degrees=270,
                            tilt_degrees=0, beam_degrees=45)
               for x in (MACHINE_ADAPTER_X_IN, SINK_ADAPTER_X_IN))
_UNAIMED = magnetic_track_spec(heads=_HEADS)
LAUNDRY_TRACK_SPEC = magnetic_track_spec(heads=tuple(
    aim_head_at(_UNAIMED, head, (inch(target[0] - RAIL_CENTER_IN[0]).meters,
                                inch(target[1] - RAIL_CENTER_IN[1]).meters,
                                inch(target[2] - CEILING_IN).meters))
    for head, target in zip(_HEADS, TASK_TARGETS_IN, strict=True)))
LAUNDRY_TRACK = track_luminaire(
    "ED-T-LT-TRACK-LAUNDRY", LAUNDRY_TRACK_SPEC, type_mark="Y",
    name='Laundry: 36" white magnetic rail, two adjustable 45° Radiant Medium heads')
LAUNDRY_TRACK_DROP = LAUNDRY_TRACK.height
# Mount.elevation is measured from finished floor; the requested 84" is from datum.
LAUNDRY_SUPPLY_MOUNT = inch(84 - MAIN_FINISHED_FLOOR_LVP.inches)
LAUNDRY_LIGHTING_TYPES = (LAUNDRY_TRACK, PUREEDGE_SUPPLY)
