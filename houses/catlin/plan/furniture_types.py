"""House-local furniture catalog for items specific to the Catlin plan.

Both mudroom closets left in 2026-08-02: the north closet became RM-M-MECH (2026-07-28)
and the south closet FURN-M-MUD-CLOSET-S became RM-M-MUD-CLOSET (storeys/main.py) — a
framed 2x4 partition closet with a sliding bypass door, keeping the original's no-swing
intent. The workbench and the shoe bench were generic and moved to
``library.placeables.furniture`` as FURN-G-WORKBENCH / FURN-M-MUD-BENCH.

What is here now are three families the shared catalog has no business carrying, because
each is *made to fit this house*: curtain rods sized to these window widths, access panels
sized to the fittings behind these walls (both 2026-08-07), and one built-in shelf scribed
to one bathroom alcove (2026-08-21). None is a product anyone would reuse across plans,
which is the test for house-local.

The first two families are ``plan_symbol=None`` on purpose. A rod at 7'-0" and a panel in a
wall face are not floor-plan objects — drawing a glyph for either would put a rectangle on
the plan where the room is empty. They are here to be *scheduled and billed*, and to exist
in 3D at the height someone has to build them at. The shelf is the opposite case: it stands
on the floor and occupies 20" of a small room, so it has to draw.
"""

from __future__ import annotations

from typehaus.model import Footprint2D, FurnitureType, Mount, MountKind, ft, inch, pt

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
# The porch's two SIDE bays, 2026-08-22. Same product as the 114" front pair, cut to the
# 8'-8" side run less its corner gaps.
#
# ** THIS IS THE FALLBACK, AND THE CONTINUOUS U WAS TRIED FIRST. ** An outdoor U-rod is a
# real article — straight track plus corner connectors, one curtain running the whole way —
# and ``Furniture`` could carry it: one position and one rectangular footprint per element,
# so a U is segments on a shared path, exactly as the real product is. What defeats it is
# the porch, not the schema. Two pillars stand in the way of the only lines a U could take:
#   * PT-SG-BF2 sits ON the front guard line at x=18'-0", 5 1/2" square, y -9'-8 3/4" to
#     -9'-3 1/4". A front rod stays continuous past it only if the whole path moves north of
#     -9'-3 1/4", and at the 6" bracket projection this type carries that is a QUARTER INCH
#     of clearance against a 6x6 in weather. Nobody builds a quarter inch.
#   * The side pillar line (x 8'-0" / 28'-0") is 6" OUTBOARD of the guard at 8'-6"/27'-6",
#     so a rod hung on the pillars drops its curtain outside the 42" railing.
# Pulling the path inboard far enough to answer both costs 6" of an 8'-8" porch on three
# sides, needs three new types and moves two rods that are already right — to buy continuity
# across a pillar the curtain cannot pass at any line. Four bay panels is what the structure
# actually offers: the front is two bays because PT-SG-BF2 divides it, and the sides are one
# each. Recorded in plans/TODO.md so the decision is not re-litigated from the product alone.
CURTAIN_ROD_OUTDOOR_98 = FurnitureType(
    tag="FT-CURTAIN-ROD-OUTDOOR-98", name='Outdoor curtain rod, 98"',
    footprint=(inch(98), inch(6)), height=inch(2),
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

# --- built-in millwork ----------------------------------------------------------------
#
# The shelf that closes RM-S-BATH1's tub alcove (2026-08-21). FX-S-BATH1-SH is a flanged
# 60x30 insert, which wants studs on three sides, and it only had two: the chase wall to the
# west and the exterior wall to the north, with its east end standing open in 1'-8 7/8" of
# dead floor. This carcass IS that third side — its west panel is the alcove's east return,
# with a 2x4 framed behind it to nail the flange to — so one built article turns a framing
# defect and an unreachable pocket into the only storage within reach of the tub.
#
# The two dimensions are the alcove's, not a catalog's: 30" deep is the tub's own depth, so
# the two front faces land on one line, and 84" is the tub surround's head, so the north
# wall reads as a single built element from floor to 7'-0" instead of a box beside a tub.
#
# ``plan_symbol="bookcase"`` is not an approximation here — ``shelving(shelves=5)`` builds
# two side panels, a back and five shelves, which is literally what this is.
#
# No ``clearances``: per the casework rule, a built-in's back is the wall and its ends are
# its neighbours, and the floor in front of it is the same floor you stand on to use the
# tub.
BATH1_SHELF_2030 = FurnitureType(
    tag="FT-BATH1-SHELF-2030", name='Bath 1 alcove shelf, 20" x 30"',
    footprint=(inch(20), inch(30)), height=inch(84),
    storage=True, work_surface=False, plan_symbol="bookcase",
    source="Site-built millwork, not a catalogue bookcase: a 3/4\" plywood carcass scribed "
           "to the east end of RM-S-BATH1's tub alcove, whose WEST panel carries "
           "FX-S-BATH1-SH's east flange over a framed 2x4 and is what makes that insert a "
           "legitimate three-wall install. Depth matches the tub (30\"), height matches the "
           "surround head (84\"); the 7/8\" of slack at the east wall is taken as scribe.",
)


# --- the media room's U sectional ---------------------------------------------------------
#
# House-local for the reason at the top of this file: it is made to fit this room. 11'-0" of
# back run across a 16'-6" box, 8'-0" of arms reaching toward a 98" screen on the north wall,
# 3'-0" seat depth. Nobody reuses that across plans.
#
# ** IT CANNOT BE THREE CATALOG PIECES. ** FURN-SOFA-84 and FURN-LOVESEAT-60 each declare a
# 2'-6" ``front_zone``, so three of them arranged in a U would each stand in the next one's
# declared walk path and draw `integrity.clearance_encroachment` three times over — for a
# shape whose whole point is that the open middle IS the walk path. And FURN-SECTIONAL-L's
# outline is generated by ``sectional_points``, which is hard-coded to an L (a back run plus
# one chaise); a U is not a parameter of it.
#
# So: an explicit ``footprint_shape``, which `resolve/placeables.py` prefers over the
# rectangular ``footprint``, and NO clearance zones at all. The empty ``clearances`` is the
# decision, not an omission — the zone a U wants is the well it encloses, and a ``front_zone``
# projecting off its own back run would land inside its own arms.
#
# The 3D massing draws the "sectional" glyph, which is L-shaped: the same acknowledged
# approximation plan/placeables.py already accepts for the armchair. The *plan* outline —
# what every clearance and collision rule measures — is the true U below.
_U_WIDTH = ft(11)
_U_DEPTH = ft(8)
_U_SEAT = ft(3)  # back run and arm depth alike

_U_HALF_W = _U_WIDTH.inches / 2.0
_U_HALF_D = _U_DEPTH.inches / 2.0
_U_ARM = _U_SEAT.inches

MEDIA_SECTIONAL_U = FurnitureType(
    tag="FT-SECTIONAL-U-MEDIA", name="U sectional, 11'-0\" x 8'-0\"",
    footprint=(_U_WIDTH, _U_DEPTH), height=ft(2, 10), plan_symbol="sectional",
    # Opening toward +y in local coordinates, so an unrotated instance faces north — which
    # is where the screen is. Walked as one ring: south face, up the east arm, back down its
    # inner face, across the top of the back run, and up the west arm's inner face.
    footprint_shape=Footprint2D(points=(
        pt(inch(-_U_HALF_W), inch(-_U_HALF_D)),
        pt(inch(_U_HALF_W), inch(-_U_HALF_D)),
        pt(inch(_U_HALF_W), inch(_U_HALF_D)),
        pt(inch(_U_HALF_W - _U_ARM), inch(_U_HALF_D)),
        pt(inch(_U_HALF_W - _U_ARM), inch(-_U_HALF_D + _U_ARM)),
        pt(inch(-_U_HALF_W + _U_ARM), inch(-_U_HALF_D + _U_ARM)),
        pt(inch(-_U_HALF_W + _U_ARM), inch(_U_HALF_D)),
        pt(inch(-_U_HALF_W), inch(_U_HALF_D)),
    )),
    source=("owner, 2026-08-22 — a U sectional for RM-B-PLAY-N. Sized to the room: 11'-0\" "
            "of back run in a 16'-6\" box leaves 2'-9\" either side, and 8'-0\" of arms "
            "puts the back run 11'-13' off a 98\" screen. Seat depth 3'-0\", overall height "
            "2'-10\" to match the catalog's seating."),
)


FURNITURE_TYPES = (CURTAIN_ROD_48, CURTAIN_ROD_84, CURTAIN_ROD_OUTDOOR_114,
                   CURTAIN_ROD_OUTDOOR_98,
                   ACCESS_PANEL_1414, ACCESS_PANEL_1429, BATH1_SHELF_2030,
                   MEDIA_SECTIONAL_U)
