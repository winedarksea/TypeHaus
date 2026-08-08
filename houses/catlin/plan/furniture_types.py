"""House-local furniture catalog for items specific to the Catlin plan.

Both mudroom closets left in 2026-08-02: the north closet became RM-M-MECH (2026-07-28)
and the south closet FURN-M-MUD-CLOSET-S became RM-M-MUD-CLOSET (storeys/main.py) — a
framed 2x4 partition closet with a sliding bypass door, keeping the original's no-swing
intent. The workbench and the shoe bench were generic and moved to
``library.placeables.furniture`` as FURN-G-WORKBENCH / FURN-M-MUD-BENCH.

What is here now (2026-08-07) are two families the shared catalog has no business carrying,
because both are *made to fit this house*: curtain rods sized to these window widths, and
access panels sized to the fittings behind these walls. Neither is a product anyone would
reuse across plans, which is the test for house-local.

Both families are ``plan_symbol=None`` on purpose. A rod at 7'-0" and a panel in a wall
face are not floor-plan objects — drawing a glyph for either would put a rectangle on the
plan where the room is empty. They are here to be *scheduled and billed*, and to exist in
3D at the height someone has to build them at.
"""

from __future__ import annotations

from typehaus.model import FurnitureType, Mount, MountKind, inch

_WALL_MOUNT = Mount(kind=MountKind.WALL)

_ROD_SOURCE = ("plans/TODO.md — window treatments. Width is the rod, not the opening: a "
               "rod runs past the RO on both sides so the stack sits on wall, not glass.")
# 48" covers every main-storey window in the house — the widest RO on a rod is 30"
# (WT-3048), which leaves 9" of stackback each side. 84" is D-M-BALC's french pair (60"
# RO, 12" each side). Depth is the bracket projection, height the rod and finial.
CURTAIN_ROD_48 = FurnitureType(
    tag="FT-CURTAIN-ROD-48", name='Curtain rod, 48"',
    footprint=(inch(48), inch(4)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)
CURTAIN_ROD_84 = FurnitureType(
    tag="FT-CURTAIN-ROD-84", name='Curtain rod, 84"',
    footprint=(inch(84), inch(4)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)
# The porch rods are a different product, not a longer version of the same one: outdoor
# fabric on a pillar-to-pillar span, so the rod is heavier, the finish is exterior, and the
# span is set by the structure (a front pillar bay) rather than by an opening.
CURTAIN_ROD_OUTDOOR_114 = FurnitureType(
    tag="FT-CURTAIN-ROD-OUTDOOR-114", name='Outdoor curtain rod, 114"',
    footprint=(inch(114), inch(6)), height=inch(2),
    plan_symbol=None, mount=_WALL_MOUNT, source=_ROD_SOURCE,
)

_PANEL_SOURCE = ("plans/TODO.md — plumbing access. Framed metal panel in a finished wall "
                 "face; size is the clear opening, depth the frame's projection.")
# 14x14 is the tub waste-and-overflow size, 14x29 the wall-hung WC carrier size — the
# carrier is a tall frame and the panel has to reach the whole of it.
ACCESS_PANEL_1414 = FurnitureType(
    tag="FT-ACCESS-PANEL-1414", name='Access panel, 14" x 14"',
    footprint=(inch(14), inch(1)), height=inch(14),
    plan_symbol=None, mount=_WALL_MOUNT, source=_PANEL_SOURCE,
)
ACCESS_PANEL_1429 = FurnitureType(
    tag="FT-ACCESS-PANEL-1429", name='Access panel, 14" x 29"',
    footprint=(inch(14), inch(1)), height=inch(29),
    plan_symbol=None, mount=_WALL_MOUNT, source=_PANEL_SOURCE,
)

FURNITURE_TYPES = (CURTAIN_ROD_48, CURTAIN_ROD_84, CURTAIN_ROD_OUTDOOR_114,
                   ACCESS_PANEL_1414, ACCESS_PANEL_1429)
