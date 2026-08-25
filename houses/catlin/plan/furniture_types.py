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


# --- kitchen millwork, 2026-08-24 (the peninsula/pantry-room rework) --------------------
#
# FT-KIT-COLDSTORE-FILLER stood here and is RETIRED with this commit, along with its one
# instance. It was 6 1/4" of scribed panel: the remainder of a 72" cold bay after the
# Frigidaire Professional pair (32 7/8" each). The pantry ROOM's south partition now takes
# 4 3/4" off the north end of that run, so the bay is 65 3/4" — exactly two appliance
# widths — and the remainder it existed to fill is gone. Deleting the type rather than
# leaving it unused is deliberate: an unreferenced house-local type reads as a size someone
# might reach for, and this one is arithmetic, not a product.


# The over-appliance box the retired CASE-OVER-36 can no longer be. Two 36" boxes need 72";
# the bay is 65 3/4". 32 7/8" is not a cabinet size and never will be — it is an APPLIANCE
# width, carried up so each box's ends land on its own column's sides and the run divides
# with no filler at either end. Same 24" depth and 24" height as CASE-OVER-36 (see the
# library type's note: base depth so the four fronts line up on x=20'-3 3/8" and the
# appliances stand 10" proud, clearing their own door swing).
OVER_COLD_3278 = FurnitureType(
    tag="FT-KIT-OVER-COLD-3278", name='32 7/8" over-appliance cabinet',
    footprint=(inch(32.875), ft(2)), height=ft(2), plan_symbol="wall-cabinet",
    storage=True, work_surface=False,
    source=('site-built to the appliance, 2026-08-24 — 32 7/8" is the Frigidaire '
            'Professional column width, not a cabinet module. Millwork, not a catalog box.'),
)


# --- the peninsula's mixer garage -----------------------------------------------------
#
# ** THIS IS WHERE THE STANDING MIXER LIVES, AND IT IS NOT A LIFT. ** The first pass at the
# owner's "mixer slides straight out onto the peninsula, outlet in the cabinet" put a
# Rev-A-Shelf spring lift in a BASE bay and three flush pop-ups in the countertop. Both were
# a misreading, corrected 2026-08-24: the mixer is meant to sit at counter level already,
# in a cabinet ABOVE the top, and slide straight out onto the counter beside it — no lifting
# a 25 lb machine up out of a base cabinet, and no holes cut in the stone.
#
# 24" x 24" x 72": it stands ON the peninsula's countertop at 36" and runs to the 108"
# ceiling, so its bottom shelf IS the counter plane and the pull-out slides level. 72" is
# not a stock cabinet height and cannot be — the dimension is "counter to ceiling" in THIS
# room. Built as two ganged boxes behind one face frame is fine and is a shop decision; it
# is modelled as the one article it reads as.
#
# It takes the peninsula's EAST 24", against the east wall, which is what makes it possible:
# a counter-to-ceiling box in the middle of a peninsula would hang from the ceiling with
# nothing behind it. That end was dead frontage before this — a seated diner's legs would
# have gone where FURN-M-KIT-PANTRY-S1 stands — so the cabinet costs no seat. Three stools
# was the honest count before it and still is.
#
# No ``clearances``, per the casework rule; the counter in front of it is the counter.
MIXER_GARAGE_24 = FurnitureType(
    tag="FT-KIT-MIXER-GARAGE-24", name='24" counter-to-ceiling mixer garage',
    footprint=(inch(24), inch(24)), height=ft(6),
    storage=True, work_surface=False, plan_symbol="tall-cabinet",
    source="Site-built millwork, 36\" to 108\" on FURN-M-KIT-PENINSULA's countertop at its "
           "east end, against the east wall. Bottom bay is a HEAVY-DUTY FULL-EXTENSION "
           "PULL-OUT SHELF at the counter plane, rated for a ~30 lb stand mixer plus bowl "
           "and travelling its full depth, so the machine comes out onto the open counter "
           "rather than being lifted. Shelf face flush with the counter so nothing has to "
           "be picked up over a lip. Two GFCI receptacles inside at 42\" "
           "(ED-M-LIVING-KGF4/KMX1) — WIRE THEM BEFORE THE BOX GOES IN. Upper bays are "
           "ordinary adjustable shelving; a roll-up or lift-up door keeps a raised door out "
           "of the room, and is a millwork selection, not a model element.",
)


# --- RM-M-PANTRY's shelf stack --------------------------------------------------------
#
# House-local by the test at the top of this file: 70 1/4" is this room's clear span, wall
# face to wall face, and nothing else.
#
# ** IT IS DESIGNED TO BE STOOD ON, AND THAT IS A STRUCTURAL CLAIM, NOT A FINISH. ** There
# is no model field for "rated to climb", and each of the three mechanisms that could carry
# it is a dead end: ``Furniture`` cannot take ``install_parts`` (only ``PipeAccessory`` and
# ``Appliance`` are ``_install_part_carriers``); an ``Assembly`` is a layered WALL stack,
# not a shelf; and ``FramingSpec.blocking_heights`` is a property of the assembly, so a
# three-sided cleat would mean cloning three assemblies — the exterior truss wall among
# them, re-running its Glaser gate, its energy table and truss_wall_opening_support against
# an unreviewed tag — to bill some 40 bf of 2x4. So the build lives on ``source`` (the
# FT-BATH1-SHELF-2030 precedent) and in notes/pantry_climbable_shelving.md.
#
# ** THE MID-SPAN GABLE IS NOT OPTIONAL, AT EITHER DEPTH. ** A 3/4" ply shelf cannot span
# 70 1/4" under a person. At the 24" width below, 250 lb at midspan gives M = PL/4 =
# 4,391 in-lb on S = 2.25 in^3 — about 1,950 psi against a 1,500-2,000 psi flatwise
# allowable — and 1.65" of sag. The stress is borderline and the DEFLECTION is an outright
# failure. A full-height centre gable halves the span to ~34 3/4": ~965 psi and ~0.20".
# The 1x3 hardwood nose glued on edge is what takes the rest of the spring out — a
# 3/4" x 2 1/2" edge nearly triples the shelf's effective I and is the cheapest stiffener
# there is. (At the 16" depth this was first drawn at, the same numbers are 2,900 psi and
# 2.4" full-span, 1,460 psi and 0.30" gabled: going deeper HELPS the shelf, because b grows
# with the depth while the span does not.)
#
# ** 24" DEEP IS THE OWNER'S CALL, 2026-08-24, AND IT IS PAST THE PUBLISHED GUIDANCE. **
# 16" is the usual practical maximum for a reach-in (14" is better) and 20"+ is normally
# called too deep to see into. At 24" in a 30"-deep room there is 6" of floor left in front
# of the stack: this is a walk-UP pantry reached from the doorway, not a walk-in, and the
# back 8" of every shelf is a second row you have to move the front row to reach. That is
# the trade, made deliberately for the volume. Two things make it work rather than merely
# fit: the shelves are STANDABLE, so the bottom bay is a step and the back of the top shelf
# is reachable; and ED-M-PANTRY-LT is a vertical slot, which is the one fixture that lights
# the depth behind what is on each shelf.
#
# Shelf pitch is GRADUATED, not uniform — uniform spacing wastes about two shelves' worth of
# volume, and since every shelf is rated to be stood on regardless of pitch, climbing does
# not need even rungs.
PANTRY_SHELVES_70 = FurnitureType(
    tag="FT-KIT-PANTRY-SHELVES-70", name='Pantry shelf stack, 70 1/4" x 24"',
    footprint=(inch(70.25), inch(24)), height=ft(7),
    storage=True, work_surface=False, plan_symbol="bookcase",
    source="Site-built millwork, DESIGNED TO BE CLIMBED — see "
           "notes/pantry_climbable_shelving.md. 3/4\" birch ply shelves on continuous 1x3 "
           "cleats on three sides, glued and screwed DOWN onto the cleats (load path is "
           "cleat -> fastener -> stud, never shelf -> pin); NO adjustable standards and no "
           "shelf pins — a pin carries a jar, not a person. A full-height 3/4\" ply centre "
           "gable at mid-span, notched around the cleats, floor to top shelf, is what makes "
           "the 70 1/4\" span legal to stand on and is not optional. 1x3 hardwood nose glued "
           "and screwed on edge at each shelf front. Two #10 x 3\" structural screws per "
           "cleat into solid wood at EVERY bay, over flat 2x4 blocking laid in each bay "
           "BEFORE the gypsum. Design load: treat as floor, not shelf — 40 psf uniform PLUS "
           "a 250-300 lb concentrated load anywhere, which governs. Graduated spacing: "
           "~20\" bottom bay (small appliances, bulk), 12\"-14\" middle (boxes, bottles), "
           "8\"-10\" top (cans, jars). 24\" DEEP by owner's decision (2026-08-24), which "
           "leaves 6\" of floor in front of the stack — reached from the doorway, not "
           "walked into.",
)


FURNITURE_TYPES = (CURTAIN_ROD_48, CURTAIN_ROD_84, CURTAIN_ROD_OUTDOOR_114,
                   CURTAIN_ROD_OUTDOOR_98,
                   ACCESS_PANEL_1414, ACCESS_PANEL_1429, BATH1_SHELF_2030,
                   MEDIA_SECTIONAL_U, OVER_COLD_3278, MIXER_GARAGE_24,
                   PANTRY_SHELVES_70)
