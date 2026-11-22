"""Laundry task lighting: IKEA NYMÅNE 4-spot bar, two spots on each task (2026-11-21).

Replaced the PureEdge 24 V magnetic rail, its two Radiant Medium heads and its accessible
40 W supply (`typehaus.library.track_lighting.magnetic_track_spec`, the revert). The bar is
line voltage on a ceiling box, so the supply, its wall box and its Class 2 feed are gone.
"""

from params.main_deck import MAIN_FINISHED_FLOOR_LVP
from plan.ikea_lighting_types import GU10_90_30K, NYMANE_4SPOT
from typehaus.library.track_lighting import aim_head_at, track_luminaire
from typehaus.model import ProductPart, TrackHeadProduct, TrackHeadSpec, TrackLightingSpec
from typehaus.quantities import inch

RAIL_CENTER_IN = (128.4, 260.0)  # its centre box clear of the y=256" truss
# The bar sits on the laundry's resolved board face: 5/8" gypsum under the 108 1/8" soffit.
CEILING_IN = 107.5
# Machine east, sink west since the door moved 11 1/2" east (2026-11-07).
MACHINE_ADAPTER_X_IN = 143.25
SINK_ADAPTER_X_IN = 113.55
# The appliance's north/front face and the basin's front interior. Fixture bodies are
# floor-relative, so their task elevations follow the same finished walking surface.
TASK_TARGETS_IN = (
    (MACHINE_ADAPTER_X_IN, 253.012, MAIN_FINISHED_FLOOR_LVP.inches + 74.375 / 2),
    (SINK_ADAPTER_X_IN, 240.0, MAIN_FINISHED_FLOOR_LVP.inches + 34.0),
)
# Even pitch, end spots at the bar ends (assembly sheet drawing; IKEA dimensions only the
# 29 x 5 in. envelope). Shade and joint sizes are schematic, to that envelope.
SPOT_OFFSETS_IN = (-13.0, -13.0 / 3, 13.0 / 3, 13.0)
_SPOT = TrackHeadProduct(
    product_ref=GU10_90_30K.tag, system="fixed_bar_120v",
    body_length=inch(4), body_diameter=inch(2.5), adapter_length=inch(1.5),
    adapter_width=inch(1.5), adapter_height=inch(0.5), pivot_drop=inch(2.25),
    watts=6, lumens=500, cct_k=3000, cri=90, beam_options=(36,),
    max_tilt_degrees=90, max_azimuth_degrees=360, source=NYMANE_4SPOT.source)


def _spec(heads):
    return TrackLightingSpec(
        system="fixed_bar_120v", feed_system="fixed_bar_120v",
        rail_product_ref=NYMANE_4SPOT.tag, feed_product_ref=NYMANE_4SPOT.tag,
        rail_length=inch(29), stock_length=inch(29), rail_width=inch(2),
        rail_height=inch(0.75), feed_length=inch(4.5), feed_width=inch(4.5),
        feed_height=inch(0.75), feed_end="center", heads=heads, source=NYMANE_4SPOT.source)


_UNAIMED = _spec(tuple(TrackHeadSpec(product=_SPOT, offset=inch(x), azimuth_degrees=270,
                                     tilt_degrees=0, beam_degrees=36)
                       for x in SPOT_OFFSETS_IN))
# West pair on the sink, east pair on the machine front.
LAUNDRY_TRACK_SPEC = _spec(tuple(
    aim_head_at(_UNAIMED, head, (inch(target[0] - RAIL_CENTER_IN[0]).meters,
                                inch(target[1] - RAIL_CENTER_IN[1]).meters,
                                inch(target[2] - CEILING_IN).meters))
    for head, target in zip(_UNAIMED.heads, (TASK_TARGETS_IN[1],) * 2 + (TASK_TARGETS_IN[0],) * 2,
                            strict=True)))
LAUNDRY_TRACK = track_luminaire(
    "ED-T-LT-TRACK-LAUNDRY", LAUNDRY_TRACK_SPEC, type_mark="Y",
    name="Laundry: IKEA NYMÅNE 29\" white bar, four aimed GU10 spots",
).model_copy(update={
    "replaceable_lamp": True, "lamp_base": "GU10", "dimmable": False,
    "lamp": "4 x GU10 LED, 3000 K, CRI 90+, replaceable",
    "parts": (ProductPart(role="lamp", product_ref=GU10_90_30K.tag, quantity=4),)})
LAUNDRY_TRACK_DROP = LAUNDRY_TRACK.height
LAUNDRY_LIGHTING_TYPES = (LAUNDRY_TRACK,)
