"""Shared door product catalog — the pocket-door family (→ CONTRIBUTING.md).

Doors were the conspicuous gap in the library. ``Library.door_types`` has always existed,
but every ``DoorType`` in the repo was authored house-locally, so two houses wanting the
same 30" interior door had to describe it twice. A door type is a product definition with
no house-specific geometry — each ``Door`` instance authors its own host and position — so
nothing about one was ever house-specific.

The pocket family goes first because it is the one door whose *type* carries real
consequences the plan cannot infer. A pocket:

- frames at roughly ``2W + 1"``, not ``W``. Every published kit sizes the rough opening
  that way, and ``resolve.framing.tables.pocket_run`` is that formula.
- leaves a run of wall as long as the leaf again with no stud to fasten to, no bay to bore
  and no depth to recess a box into. ``mep.pocket_occupancy`` refuses anything in it.
- is width-limited by the *kit*, not by the opening. The commodity series stop at 36" and
  125 lb; past that is a different, heavier product, which is why 48" is a separate record
  citing a separate source rather than one more row on the same ladder.

Widths follow the published kit ladders exactly. Heights do not vary: 6'-8" is the only
height the standard series is built for, and a taller pocket is a made-to-order frame.
"""

from __future__ import annotations

from typehaus import DoorType, u_us
from typehaus.quantities import ft

# The commodity ladder. One frame kit per door width, all-steel split studs on an extruded
# aluminium track, rated 125 lb per door and 3-1/2" minimum wall structure — an ordinary
# 2x4 partition takes it, which is why a pocket needs no assembly of its own.
_JOHNSON_1500 = (
    "Johnson Hardware 1500PF series pocket door frame kit "
    "(https://johnsonhardware.com/1500-series-pocket-door-frame-kits)"
)
# Past the commodity ladder the frame, the track and the hangers all change. Cavity Sliders'
# timber-framed cavity unit is published to 4'0" x 8'0" and carries the weight a 4'-0"
# solid-core leaf actually is.
_CAVITY_SLIDER = (
    "Cavity Sliders CS For Wood cavity slider pocket frame, 2x4 stud "
    "(https://www.cavitysliders.com/cavislider/cavity-slider-pocket-door-frame/2x4-stud/)"
)

DT_POCKET_INT_24 = DoorType(
    tag="DT-POCKET-INT-24", width=ft(2), height=ft(6, 8), operation="pocket", source=_JOHNSON_1500
)
DT_POCKET_INT_28 = DoorType(
    tag="DT-POCKET-INT-28",
    width=ft(2, 4),
    height=ft(6, 8),
    operation="pocket",
    source=_JOHNSON_1500,
)
DT_POCKET_INT_30 = DoorType(
    tag="DT-POCKET-INT-30",
    width=ft(2, 6),
    height=ft(6, 8),
    operation="pocket",
    source=_JOHNSON_1500,
)
DT_POCKET_INT_32 = DoorType(
    tag="DT-POCKET-INT-32",
    width=ft(2, 8),
    height=ft(6, 8),
    operation="pocket",
    source=_JOHNSON_1500,
)
DT_POCKET_INT_36 = DoorType(
    tag="DT-POCKET-INT-36", width=ft(3), height=ft(6, 8), operation="pocket", source=_JOHNSON_1500
)
# The heavy-duty end of the family. Not a 1500PF size: that series stops at 36"/125 lb, and
# a 4'-0" solid-core leaf is past both. Keep the source distinct — a takeoff that orders a
# 1500PF kit for this door gets a frame the leaf will pull off the wall.
DT_POCKET_INT_48 = DoorType(
    tag="DT-POCKET-INT-48", width=ft(4), height=ft(6, 8), operation="pocket", source=_CAVITY_SLIDER
)

POCKET_DOOR_TYPES = (
    DT_POCKET_INT_24,
    DT_POCKET_INT_28,
    DT_POCKET_INT_30,
    DT_POCKET_INT_32,
    DT_POCKET_INT_36,
    DT_POCKET_INT_48,
)

# ``function`` is stated only where the PRODUCT decides it: an exterior swing is keyed, a
# sectional's only hardware is its operator, a bifold or bypass runs on its own track and
# takes no lockset. The interior swings and the pocket frames below leave it None on purpose
# — the same DT-INT-SWING32 is a passage set at a study and a privacy set at a bath, and a
# planning catalog cannot know which. A house that prices hardware per function states it on
# its own type (or splits the type), which is exactly what the field is for.
_STANDARD_SOURCE = (
    "Commodity door product class; select a listed product meeting the declared dimensions "
    "and performance."
)

STANDARD_DOOR_TYPES = (
    DoorType(
        tag="DT-EXT-SWING36",
        width=ft(3),
        height=ft(6, 8),
        exterior=True,
        function="entry",
        u_factor=u_us(0.20),
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-EXT-FRENCH60",
        width=ft(5),
        height=ft(6, 8),
        exterior=True,
        function="entry",
        operation="double_swing",
        glazed=True,
        tempered=True,
        u_factor=u_us(0.20),
        shgc=0.35,
        vt=0.5,
        source=_STANDARD_SOURCE,
    ),
    DoorType(tag="DT-INT-SWING24", width=ft(2), height=ft(6, 8), source=_STANDARD_SOURCE),
    DoorType(tag="DT-INT-SWING30", width=ft(2, 6), height=ft(6, 8), source=_STANDARD_SOURCE),
    DoorType(tag="DT-INT-SWING32", width=ft(2, 8), height=ft(6, 8), source=_STANDARD_SOURCE),
    DoorType(tag="DT-INT-SWING36", width=ft(3), height=ft(6, 8), source=_STANDARD_SOURCE),
    DoorType(
        tag="DT-INT-SWING30-GLAZED",
        width=ft(2, 6),
        height=ft(6, 8),
        glazed=True,
        tempered=True,
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-INT-SWING36-TRIMLESS",
        width=ft(3),
        height=ft(6, 8),
        trimless=True,
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-INT-BIFOLD56",
        width=ft(4, 8),
        height=ft(6, 8),
        operation="bifold",
        function="closet",
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-INT-BYPASS48",
        width=ft(4),
        height=ft(6, 8),
        operation="slide",
        function="closet",
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-INT-BYPASS60",
        width=ft(5),
        height=ft(6, 8),
        operation="slide",
        function="closet",
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-INT-DOUBLE60",
        width=ft(5),
        height=ft(6, 8),
        operation="double_swing",
        core="solid",
        source=_STANDARD_SOURCE,
    ),
    DoorType(
        tag="DT-EXT-OVERHEAD192",
        width=ft(16),
        height=ft(7),
        exterior=True,
        operation="overhead",
        function="overhead",
        source=_STANDARD_SOURCE,
    ),
)

ALL_DOOR_TYPES = (*POCKET_DOOR_TYPES, *STANDARD_DOOR_TYPES)
