"""House-local furniture catalog for items specific to the Catlin plan.

Only items *made to fit this house* belong here: nothing here is a product anyone would
reuse across plans (the test for house-local). The curtain rods, access panels and closet
shelving this house places are library rows (``library.placeables.allowances``).
"""

from __future__ import annotations

from library.placeables.allowances import (
    ACCESS_PANEL_1414,
    ACCESS_PANEL_1429,
    ACCESS_PANEL_2015,
    ACCESS_PANEL_CLG_3029,
    CELLULAR_BLIND_2748,
    CLOSET_SHELF_36,
    CLOSET_SHELF_ROD_60,
    CLOSET_SHELF_ROD_84,
    CLOSET_SHELF_ROD_96,
    CURTAIN_ROD_48,
    CURTAIN_ROD_84,
)

from typehaus.model import (
    BuiltInBookcaseBay,
    BuiltInBookcaseSpec,
    Footprint2D,
    FurnitureCut,
    FurnitureType,
    ModelRepresentation,
    Mount,
    MountKind,
    PlacementStrategy,
    ft,
    inch,
    pt,
)

from .study_booth_types import FOLD_LEAF, STUDY_BENCH, STUDY_DESK, STUDY_FOOTREST

_WALL_MOUNT = Mount(kind=MountKind.WALL)

# One fabricated run, separate from the conventional partition behind it. Dimensions are
# the joiner's clear openings and board stock; every output derives the same twelve boards,
# four shared/end dividers, and three stepped backs from this record.
STUDY_BUILT_IN_BOOKCASE = FurnitureType(
    tag="FT-A-STUDY-BUILTIN", name="Attic study stepped built-in bookcase",
    footprint=(inch(99.375), inch(10.625)), height=inch(60),
    placement=PlacementStrategy.WALL_ATTACHED,
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(
            BuiltInBookcaseBay(clear_width=inch(31.25), height=inch(60), horizontal_board_count=5),
            BuiltInBookcaseBay(clear_width=inch(31.25), height=inch(42), horizontal_board_count=4),
            BuiltInBookcaseBay(clear_width=inch(31.25), height=inch(30), horizontal_board_count=3),
        ),
        shelf_depth=inch(9.875), horizontal_board_thickness=inch(1),
        divider_thickness=inch(0.75), back_thickness=inch(0.75),
        west_filler_width=inch(2.625),
    ),
    wood_material_ref="oak-shelf-5q",
    source="Catlin study fixed casework: front y=105 3/4 in.; x=272..368 3/4 in.; three 31 1/4 in. clear bays with 60/42/30 in. tops and 5/4/3 horizontal boards; 2 5/8 in. west filler closes to W-A-SN-WR.",
)

# 48" is the standard rod length for main-storey windows that use curtains — the widest RO
# is 30" (WT-3048), leaving 9" of stackback each side. 84" is D-M-BALC's french pair (60"
# RO, 12" each side). Depth is the bracket projection, height the rod and finial.
# --- the porch enclosure track -------------------------------------------------------
# NOT A CURTAIN ROD. 2026-09-03: the two 114" rods and the two 98" side rods were replaced
# by a snap-carrier aluminium curtain TRACK, the hardware a screened-porch enclosure is
# actually built on (Mosquito Curtains and equivalents: 8' anodized sticks, 90-degree
# curves, splices and end caps, screwed up through the stick's centre groove).
#
# ** THE PRODUCT CHANGED BECAUSE THE ROD COULD NOT SEAL. ** A rod at 8'-6" under a joist
# soffit at 9'-4 3/4" leaves a ~10" open band across the whole opening, and rings leak at
# the top by construction — a bug highway with a curtain hanging under it. A track screwed
# flush to the soffit closes that band, and it is the same hardware for both panel sets:
# no-see-um mesh in summer, 30-ga marine clear vinyl in spring and fall for wind chill.
# Zippers were rejected as the primary closure (UV and grit make them the wear item and a
# replacement means re-sewing a panel); they survive only at the vinyl set's corner joints.
#
# ``height=inch(1)`` is the extrusion, not a rod-and-finial: ``Mount.elevation`` is the body
# BOTTOM, so the track's top lands on the soffit it fastens to. The 2" footprint depth is
# the stick plus its carriers. ``plan_symbol=None`` as with the rods — scheduled and billed,
# not drawn.
#
# ``MountKind.CEILING``, not WALL. These name no wall, so ``_resolve_location`` returns the
# authored position untouched either way and the resolved Z is byte-identical; all WALL
# bought was ``horizontal_projection_from_wall_m`` for A117.1 s307.2, which is moot above
# 80". CEILING says the true thing: they hang from a soffit.
#
# See notes/porch_enclosure.md for the panels, the magnet seam and the north sweep.
_TRACK_SOURCE = ("notes/porch_enclosure.md — snap-carrier aluminium curtain track, screwed "
                 "up through the centre groove into the balcony joists/rim above; 5 screws "
                 "per 8' stick (the VINYL spacing, so one set of hardware carries both "
                 "panel sets).")
# The FRONT run, one piece since 2026-09-22: x 10'-0"..26'-0" on the -9'-0" spare joist,
# less ~8" at each end where a 90-degree curve substitutes for the last of the stick.
PORCH_TRACK_176 = FurnitureType(
    tag="FT-PORCH-TRACK-176", name='Porch enclosure track, 176"',
    footprint=(inch(176), inch(2)), height=inch(1),
    plan_symbol=None, mount=Mount(kind=MountKind.CEILING), source=_TRACK_SOURCE,
)
# The two FLANK runs, x = 10'-0" and 26'-0", y -9'-0" to -0'-7 1/2": 2 1/2" past the porch
# deck edge on an outrigger, stopping 1/4" off the -0'-7 1/4" cladding face. 100 1/2" long; the
# tag keeps "102" because prices.toml keys the per-each row on it.
PORCH_TRACK_102 = FurnitureType(
    tag="FT-PORCH-TRACK-102", name='Porch enclosure track, 100 1/2"',
    footprint=(inch(100.5), inch(2)), height=inch(1),
    plan_symbol=None, mount=Mount(kind=MountKind.CEILING), source=_TRACK_SOURCE,
)

# 14x14 is the tub waste-and-overflow size, 14x29 the wall-hung WC carrier size — the
# carrier is a tall frame and the panel has to reach the whole of it.
# ** A CEILING PANEL IS A DIFFERENT SHAPE OF TYPE, NOT A REUSE OF THE TWO ABOVE. ** Those
# two are WALL mounts: their `footprint` is (width, frame projection) and their `height` is
# the vertical dimension of the opening. Lay one in a ceiling and the plan rectangle comes
# out 1" deep. For a ceiling panel the whole clear opening is in PLAN and the frame's
# projection is the height, so the fields swap roles and the type has to be its own.
#
# ** 30 x 29, AND IT IS THAT BIG BECAUSE THE LADDER WAS HEADED OFF FOR IT. ** It was 20 x 13
# for one day — the clear bay between two rungs at 16" o.c., which is a hand and a filter and
# nothing else. `Soffit.openings` now exists (model/floors.py), so SF-S-HP1 authors a real
# framed hole: one rung cut, two 32" headers along the box, and 30 x 29 of clear opening
# under the air handler's north two-thirds and its return face. That is a service hatch a
# blower comes out of, and `structural.soffit_opening` grades the header it hangs on.
#
# ** IT IS SEALED AND GASKETED, AND THAT IS A CODE LINE, NOT A DETAIL. ** The obvious
# convenience — leave the soffit's bottom open in the closet and reach straight up — makes
# the CLOSET the return plenum, which is exactly what IMC 601.5(7) forbids. A hinged, gasketed
# door is the compliant version of the same convenience: air does not enter through it, so it
# is a service hatch and not an inlet.

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
# CLOSED BELOW THE COUNTER (owner, 2026-09-28). FX-S-BATH1-LAV's north end panel stands
# 2" in front of this case's whole open face, so nothing under the 36" counter line can be
# reached. A fixed 3/4" plywood front panel (carcass, hidden behind the vanity end; no oak)
# closes floor to 35 1/4"; the lowest open shelf remains at the 36" counter height.
# Shelves top at 36/48/60/72/84" — 11 1/4" clear each — and none
# stands in the closed base. SB-S-BATH1 bills those five.
#
# No ``clearances``: per the casework rule, a built-in's back is the wall and its ends are
# its neighbours, and the floor in front of it is the same floor you stand on to use the
# tub.
BATH1_SHELF_2030 = FurnitureType(
    tag="FT-BATH1-SHELF-2030", name='Bath 1 alcove shelf, 20" x 30"',
    footprint=(inch(20), inch(30)), height=inch(84),
    storage=True, work_surface=False,
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(18.5), height=inch(84),
                                 horizontal_board_count=5, closed_base_height=inch(35.25)),),
        shelf_depth=inch(29.25), horizontal_board_thickness=inch(0.75),
        divider_thickness=inch(0.75), back_thickness=inch(0.75),
        panel_material_ref="maple-ply-prefin-34",
        shelf_nosing_depth=inch(0.75), shelf_nosing_height=inch(1.5),
        face_strip_width=inch(1.5),
    ),
    wood_material_ref="locust-shelf-4q",
    # Locust only where it shows (2026-10-18): one nosing per shelf, a strip per side.
    cut_list=(FurnitureCut(part="shelf nosing", count=5, thickness=inch(0.75),
                           width=inch(1.5), length=inch(18.5)),
              FurnitureCut(part="face strip", count=2, thickness=inch(0.75),
                           width=inch(1.5), length=inch(84))),
    source="Site-built millwork, not a catalogue bookcase: a 3/4\" plywood carcass scribed "
           "to the east end of RM-S-BATH1's tub alcove, whose WEST panel carries "
           "FX-S-BATH1-SH's east flange over a framed 2x4 and is what makes that insert a "
           "legitimate three-wall install. Depth matches the tub (30\"), height matches the "
           "surround head (84\"); the 7/8\" of slack at the east wall is taken as scribe. "
           "Shelves are prefinished maple plywood (SB-S-BATH1); locust heartwood nosings and "
           "face strips, film-finished on all six faces; stainless pins and fasteners only.",
)


# RM-S-SUITEBATH's alcove return, the hall bath's shelf turned to face west (2026-10-03).
# FX-S-SUITEBATH-TUBSH is a flanged insert with its SOUTH end open; this case's north
# divider is that third side, over a framed 2x4 for the flange, and its back panel sits on
# W-S-C2C. 11 1/4" wide is the leftover between the tub and W-S-SBS; 30" deep is the tub's
# own width; 84" is the surround head. Open to the room, no closed base: eight nosed plywood
# boards make seven openings of about 11".
SUITEBATH_SHELF_1130 = FurnitureType(
    tag="FT-SUITEBATH-SHELF-1130", name='Suite bath alcove shelf, 11 1/4" x 30"',
    footprint=(inch(11.25), inch(30)), height=inch(84),
    storage=True, work_surface=False,
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(9.75), height=inch(84),
                                 horizontal_board_count=8),),
        shelf_depth=inch(29.25), horizontal_board_thickness=inch(0.75),
        divider_thickness=inch(0.75), back_thickness=inch(0.75),
        panel_material_ref="maple-ply-prefin-34",
        shelf_nosing_depth=inch(0.75), shelf_nosing_height=inch(1.5),
        face_strip_width=inch(1.5),
    ),
    wood_material_ref="locust-shelf-4q",
    cut_list=(FurnitureCut(part="shelf nosing", count=8, thickness=inch(0.75),
                           width=inch(1.5), length=inch(9.75)),
              FurnitureCut(part="face strip", count=2, thickness=inch(0.75),
                           width=inch(1.5), length=inch(84))),
    source="Site-built millwork: a 3/4\" plywood carcass scribed into the south end of "
           "RM-S-SUITEBATH's tub alcove, open to the west. Its north divider carries "
           "FX-S-SUITEBATH-TUBSH's south flange over a framed 2x4. "
           "Shelves are prefinished maple plywood (SB-S-SUITEBATH); locust heartwood nosings and "
           "face strips, film-finished on all six faces; stainless pins and fasteners only.",
)

# RM-S-SUITEBATH's robe pegs, on W-S-DC2 north of the door leaf (2026-10-03). The closet
# rail's build at 24", four knobs.
SUITEBATH_PEGS_24 = FurnitureType(
    tag="FT-SUITEBATH-PEGS-24", name='Solid oak wall-mounted peg rail, 24", four knobs',
    footprint=(inch(24), inch(4)), height=inch(3.5),
    plan_symbol="peg-rail", mount=Mount(kind=MountKind.WALL),
    wood_material_ref="oak-shelf-4q",
    source="Solid-oak 24 in backplate with four rounded, projecting oak knobs; the "
           "FURN-M-CLOSET-PEGS rail at a shorter length.",
)

# The suite bath's mirror (owner, 2026-10-03): a plain arched shelf mirror over the lav,
# lit by a separate bar above it.
SUITEBATH_MIRROR_ESTERO = FurnitureType(
    tag="FT-SUITEBATH-MIRROR-ESTERO", name='Kate and Laurel Estero arch shelf mirror, 20" x 28"',
    footprint=(inch(20.125), inch(5.5)), height=inch(28),
    plan_symbol="arch-shelf-mirror", mount=Mount(kind=MountKind.WALL),
    product_ref="PROD-KATELAUREL-221484",
    source="Kate and Laurel Estero, gold metal frame, 4\" x 20\" shelf; retailer dimensions.",
)


# --- the media room's U sectional ---------------------------------------------------------
#
# House-local for the reason at the top of this file: it is made to fit this room. 11'-0" of
# back run across a 16'-6" box, 8'-0" of arms reaching toward a 98" screen on the north wall,
# 3'-0" seat depth. Nobody reuses that across plans.
#
# ** IT CANNOT BE THREE CATALOG PIECES. ** FURN-SOFA-84 and FURN-LOVESEAT-60 each declare a
# 2'-6" ``front_zone``, so three of them in a U would each stand in the next one's declared
# walk path (`integrity.clearance_encroachment`, three times over) for a shape whose whole
# point is that the open middle IS the walk path. FURN-SECTIONAL-L's outline is generated by
# ``sectional_points``, hard-coded to an L (a back run plus one chaise); a U is not a
# parameter of it.
#
# So: an explicit ``footprint_shape``, which `resolve/placeables.py` prefers over the
# rectangular ``footprint``, and NO clearance zones at all. The empty ``clearances`` is the
# decision, not an omission — the zone a U wants is the well it encloses, and a ``front_zone``
# projecting off its own back run would land inside its own arms.
#
# The 3D massing draws the "sectional" glyph, which is L-shaped: the same acknowledged
# approximation plan/placeables.py already accepts for the armchair. The *plan* outline —
# what every clearance and collision rule measures — is the true U below.
#
# Every seating family in `model/placeable_symbols/_families.py` — `seating` and
# `sectional` alike — puts its back band at ``+y`` and faces ``-y`` (`plan/placeables.py`
# states the convention). The ring below is authored to it: back run at +y, opening toward
# -y, with FURN-B-PLAY-SECTIONAL carrying ``rotation=deg(180)`` to point the whole thing
# north. `footprint_shape` is read only by `resolve/placeables.py:_local_footprint` for
# collision and wall attachment, never by the symbol that draws — so a ring authored against
# the wrong convention draws a body with its back to the screen with nothing to catch it.
_U_WIDTH = ft(11)
_U_DEPTH = ft(8)
_U_SEAT = ft(3)  # back run and arm depth alike

_U_HALF_W = _U_WIDTH.inches / 2.0
_U_HALF_D = _U_DEPTH.inches / 2.0
_U_ARM = _U_SEAT.inches

MEDIA_SECTIONAL_U = FurnitureType(
    tag="FT-SECTIONAL-U-MEDIA", name="U sectional, 11'-0\" x 8'-0\"",
    footprint=(_U_WIDTH, _U_DEPTH), height=ft(2, 10), plan_symbol="sectional",
    # Back run at +y, opening toward -y: the same convention `seating` and `sectional` draw
    # to, so the outline and the body turn together under one rotation. Walked as one ring
    # from the west arm's open tip: across the arm's end, up its inner face, along the front
    # of the back run, down the east arm's inner face, out its tip, and back along the
    # sectional's own back and west side.
    footprint_shape=Footprint2D(points=(
        pt(inch(-_U_HALF_W), inch(-_U_HALF_D)),
        pt(inch(-_U_HALF_W + _U_ARM), inch(-_U_HALF_D)),
        pt(inch(-_U_HALF_W + _U_ARM), inch(_U_HALF_D - _U_ARM)),
        pt(inch(_U_HALF_W - _U_ARM), inch(_U_HALF_D - _U_ARM)),
        pt(inch(_U_HALF_W - _U_ARM), inch(-_U_HALF_D)),
        pt(inch(_U_HALF_W), inch(-_U_HALF_D)),
        pt(inch(_U_HALF_W), inch(_U_HALF_D)),
        pt(inch(-_U_HALF_W), inch(_U_HALF_D)),
    )),
    source=("owner, 2026-08-22 — a U sectional for RM-B-PLAY-N. Sized to the room: 11'-0\" "
            "of back run in a 16'-6\" box leaves 2'-9\" either side, and 8'-0\" of arms "
            "puts the back run 11'-13' off a 98\" screen. Seat depth 3'-0\", overall height "
            "2'-10\" to match the catalog's seating."),
)


# --- kitchen millwork (the peninsula/pantry-room rework) --------------------------------
#
# FT-KIT-COLDSTORE-FILLER (6 1/4" of scribed panel filling the remainder of a 72" cold bay
# after the Frigidaire Professional pair, 32 7/8" each) is RETIRED, along with its one
# instance: the pantry ROOM's south partition now takes 4 3/4" off that run, leaving a
# 65 3/4" bay — exactly two appliance widths, no remainder to fill. Deleting the type rather
# than leaving it unused is deliberate: an unreferenced house-local type reads as a size
# someone might reach for, and this one was arithmetic, not a product.


# FT-KIT-OVER-COLD-3278 (32 7/8" x 24" x 21", hung at 75" over the Frigidaire columns) and
# FT-KIT-MIXER-GARAGE-24 (24" x 24" x 72", standing on the peninsula at 36") are both
# RETIRED, 2026-09-11, during the kitchen's move onto the IKEA SEKTION frame ladder.
# The later catalog review found that the replacement deep wall frames are not sold in
# these dimensions either. The 2026-09-29 correction reintroduced explicit house-local
# deep upper types in plan/kitchen_deep_cabinets.py:
#
#  * over-cold boxes now use stock SEKT-TS30-20 at 73 1/2" (2026-10-05), tops 93 1/2";
#  * the mixer garage is bottomless FT-KIT-MIXER24-20, stock FT-KIT-STOCK24-30-HUNG
#    and SEKT-TS24-15, topping at 101" (2026-10-23).
#
# Deleted rather than left unused, per FT-KIT-COLDSTORE-FILLER's rule above: an
# unreferenced house-local type reads as a size someone might reach for. The fit-out prose
# each carried on its `source` — the mixer garage's full-extension pull-out, its flush shelf
# face and its two in-cabinet GFCI receptacles — moved to plan/kitchen_casework.py, where the
# instances are, and to prices.toml [allowances], where the money is.


# --- RM-M-PANTRY's shelf stack --------------------------------------------------------
#
# House-local by the test at the top of this file: 73 1/4" is this room's clear span, wall
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
# ** THE MID-SPAN GABLE IS NOT OPTIONAL. ** Shelves are 1 1/4" solid red oak (6/4 since
# 2026-10-16; plan/millwork.py, owner stock). Gabled to 36 1/4", 250 lb at midspan is
# ~484 psi (S = 4.69 in^3) and ~0.053" (I = 2.93 in^4) against L/360 = 0.101". Ungabled the
# full 73 1/4" span is ~977 psi and ~0.44" against 0.203", which fails badly. The gable also
# carries the cleat/blocking layout, and it makes the bottom bay a step rather than a plank.
#
# No 1x3 hardwood nose: that stiffener existed to triple a PLY shelf's effective I and take
# the spring out of gabled ply sag; solid oak needs none of it, and it also closes a
# quantity gap — the nose was ~41 LF of hardwood nothing in the model counted.
#
# ** SOLID WOOD ON CLEATS MOVES, AND THE FASTENING HAS TO LET IT. ** Boards run the 36 1/4"
# bay (grain along it), so seasonal movement is FRONT TO BACK — along the side cleats,
# across their screw line — roughly 1/4" of tangential movement across 18" of red oak over
# a Minnesota RH swing. Screw tight at the FRONT only; elongate every side- and back-cleat
# hole rearward. A solid shelf pinned hard on three sides splits, in year two, not on install.
#
# ** 18" DEEP, NOT 24". ** The room is 26" clear N-S, so 24" left 2" of floor and 18" leaves
# 8". The milling supply drove it, not the ergonomics: the owner's red oak runs to 18"
# wide (a finished 18" board needs ~18 3/4" in the rough once edge-jointed), so 18" is two
# boards per shelf where 24" was two wider, scarcer ones. Published guidance favours 18"
# anyway — 16" is the usual practical reach-in maximum, 20"+ reads too deep to see into.
# ~25% of shelf area is given up for it. Two things still make an 18" reach-in good: the
# shelves are STANDABLE (bottom bay a step, top shelf reachable), and ED-M-PANTRY-LT is a
# vertical slot lighting the depth behind whatever is on each shelf.
#
# Shelf pitch is GRADUATED, not uniform — uniform spacing wastes about two shelves' worth of
# volume, and since every shelf is rated to be stood on regardless of pitch, climbing does
# not need even rungs.
PANTRY_SHELVES_70 = FurnitureType(
    tag="FT-KIT-PANTRY-SHELVES-70", name='Pantry shelf stack, 73 1/4" x 18"',
    footprint=(inch(73.25), inch(18)), height=ft(7),
    storage=True, work_surface=False, plan_symbol="bookcase",
    wood_material_ref="oak-shelf-6q",
    source="Site-built millwork, DESIGNED TO BE CLIMBED — see "
           "notes/pantry_climbable_shelving.md. 1 1/4\" (6/4) solid red oak shelves (owner "
           "stock, scheduled in plan/millwork.py as SB-M-PANTRY) on continuous 1x3 cleats "
           "on three sides, screwed DOWN onto the cleats (load path is cleat -> fastener "
           "-> stud, never shelf -> pin); NO adjustable standards and no shelf pins — a "
           "pin carries a jar, not a person. Screwed tight at the FRONT only, with every "
           "side- and back-cleat hole elongated rearward so 18\" of solid oak can move "
           "without splitting. A full-height 3/4\" ply centre gable at mid-span, notched "
           "around the cleats, floor to top shelf, halves the span to 36 1/4\" and is not "
           "optional — the full span deflects ~0.44\" under 250 lb, past the L/360 this "
           "is graded to as a floor. Two #10 x 3\" structural screws per cleat into solid "
           "wood at EVERY bay, over flat 2x4 blocking laid in each bay BEFORE the gypsum. "
           "Design load: treat as floor, not shelf — 40 psf uniform PLUS a 250-300 lb "
           "concentrated load anywhere, which governs. Graduated spacing: ~20\" bottom bay "
           "(small appliances, bulk), 12\"-14\" middle (boxes, bottles), 8\"-10\" top (cans, "
           "jars). 18\" DEEP by owner's decision (2026-08-29, replacing 24\"), which leaves "
           "8\" of floor in front of the stack.",
)



# --- Shared clearance variants ----------------------------------------------------------
# The eight-seat table's open-corner chair zone and the 84" sofa's seat-width walk band are
# in ``library.placeables.furniture``. Catlin authors only the room-specific placements.


# --- Closet shelf-and-rod, the four dedicated closets --------------------------------------
#
# Ventilated ("wire") shelving on a rod, the standard closet fit-out, and the reason it is
# a ``FurnitureType`` rather than a ``ShelfBank``: a ShelfBank reaches exactly one consumer,
# ``takeoff/hardwood.py``, whose whole subject is BOARDS out of the family's own stock. An
# epoxy-coated steel shelf has no species, no board feet and no cut list — putting one
# through the milling schedule would ask the mill to saw a ventilated shelf. As a placeable
# it bills where it belongs, in ``[placeables]``, and it draws in the closet it fills.
#
# One type per closet because a FurnitureType carries a fixed footprint and these four runs
# are four different lengths. 16" deep is the standard ventilated shelf and the depth a
# jacket on a hanger actually needs; 12" is the linen depth and is what RM-S-NCLOSET's
# 40 3/4" of wall takes without crowding its door.
#
# ``plan_symbol="bookcase"`` for the same reason PANTRY_SHELVES_70 uses it: a shelf run is a
# depth of floor the room does not have, and a plan that draws the closet empty reads as
# room that is there. They are WALL-mounted at rod height, so nothing stands on the floor —
# the symbol is the reach, not an obstruction.



# --- RM-M-BATH2, the over-toilet cabinets ------------------------------------------------
#
# A bought pair on W-M-HS1's bath face (the room's only free wall), surface-mounted: a
# recess is ruled out by the staggered plumbing wall and the WC vent. The 4'-0" bottom is
# the compliance line over the 30" tank; see notes/bath2_over_toilet_cabinet.md.
TANNFORSEN_1806 = FurnitureType(
    tag="FT-IKEA-TANNFORSEN-1806", name='IKEA TÄNNFORSEN wall cabinet, 18" x 6"',
    footprint=(inch(18), inch(6)), height=inch(37),
    storage=True, work_surface=False, plan_symbol="tannforsen-wall",
    source="IKEA TÄNNFORSEN wall cabinet with door, white, art. 405.354.20, $199: "
           "18\" W x 6\" D x 37\" H, one reversible 5/8\" door on two soft-close hinges, "
           "4 adjustable glass shelves, hung on the included suspension rail. Knobs sold separately.",
)


# --- RM-A-STUDIO's wet bar: an IKEA SUNNERSTA kitchenette ----------------------------------
#
# ** RETIRED 2026-09-09: ** the studio's wet bar used to be a house-local 24"x18" base under
# FX-A-STUDIO-BAR-SINK, on the CENTRE WALL (W-A-C2), with D-A-STUBATH swinging out into it —
# the door blocked from opening fully with someone at the sink. The owner picked a real
# product instead: an IKEA SUNNERSTA mini-kitchen, 44 1/8" x 22" x 54 3/4", $149, article
# 40313363 — one piece carrying the sink, the counter and the fridge cavity together, and
# it moves the whole bar off the centre wall onto the bath wall, W-A-BATH-S, which is what
# frees D-A-STUBATH's swing and REG-A-HP-WEST underneath the old fridge. See
# plan/placeables.py and plan/fixtures.py for the siting.
#
# ** ITS TOP IS NOT REVERSIBLE, AND THAT SETTLED WHICH WALL IT WENT ON. ** The bowl is at the
# unit's right-hand end facing it. On the centre wall that puts the bowl 76" from the bath
# vent against a 60" trap-arm limit; on W-A-BATH-S it puts the bowl at the EAST end, nearest
# the stack, which is what makes the short revent in mep_venting.py possible at all.
#
# House-local, not a catalog addition, for the same reason the base it replaces was: one
# product picked for one room. ``storage=True``/``work_surface=True`` carry over from the
# old base; ``clearances`` stays unset, per the casework convention.
STUDIO_KITCHENETTE_4422 = FurnitureType(
    tag="FT-STUDIO-KITCHENETTE-4422", name='SUNNERSTA kitchenette, 44 1/8" x 22"',
    footprint=(inch(44.125), inch(22)), height=inch(54.75),
    storage=True, work_surface=True, plan_symbol="sink-base",
    source="IKEA SUNNERSTA mini-kitchen, article 40313363, $149. 44 1/8\" x 22\" x 54 3/4\", "
           "sink at the right-hand end facing the unit (top is NOT reversible). The US "
           "listing sells the faucet separately; other markets bundle a LAGAN mixer tap and "
           "a LILLVIKEN trap. Carries the fridge cavity underneath.",
)


# --- RM-M-LIVING's fireplace mantel ----------------------------------------------------
#
# The shelf over W-M-FIRE-HEAD. It existed only as `SB-M-FIRE-MANTEL`, a ShelfBank, and a
# ResolvedShelfBank carries width/depth/thickness/count and NO POSITION — no emitter reads
# `model.shelf_banks` at all, so the mantel had a cut list and no body. Nothing in the 3D,
# nothing for a clearance check to see. Hosting the bank on a wall-mounted placeable is the
# house's existing idiom (FURN-B-PLAY-TV, the kitchen wall cabinets, the CASE-*-ST stacker
# course) and gives it a real extruded solid.
#
# Keep the floor-plan glyph unset; the generated board gives the slab its elm appearance.
#
# ** `work_surface` IS LEFT UNSET AND THAT IS LOAD-BEARING. ** `work_surface=False` is the
# value NEC 210.52(A)'s wall-space rule keys on; `None` keeps a shelf 5'-4" in the air out
# of that rule entirely rather than leaning on the 6" floor-contact gate to do it.
MANTEL_ELM_46 = FurnitureType(
    tag="FT-MANTEL-ELM-46", name='Fireplace mantel shelf, 45 1/2" x 11 1/2"',
    footprint=(inch(45.5), inch(11.5)), height=inch(2.25),
    storage=False, plan_symbol=None,
    model_representation=ModelRepresentation(symbol="closet-board"),
    wood_material_ref="elm-mantel-12q",
    source="Site-made solid American elm mantel (walnut until 2026-10-16) in 12/4 stock, 45 1/2\" x 11 1/2\" x 2 1/4\", "
           "flush with the brick panel's ends and cantilevered off blocking let into "
           "W-M-FIRE-HEAD's back face. Its underside sits at 64\" AFF, on the head "
           "course — 24 modular courses of visible brick — and its top at 66 1/4\". "
           "19 5/8\" of clearance from the firebox trim top at 44 3/8\" to the shelf, "
           "against Amantii's 4\" minimum for the BI-30-XTRASLIM; the brick spandrel "
           "over the 44 5/8\" masonry head is a different number (19 3/8\") for a "
           "different thing, and both are stated on the drawing.",
)


# --- the balcony leader's splash basin (2026-09-23) --------------------------------------
#
# TR-SG-RUNNEL's spout lands in it: splash stone first, bird bath in season. A shallow dish
# (<= 2") with open, sloped sides so ice lifts rather than splits it — cast concrete basins
# crack in a Minnesota winter. It spills through a south notch onto a river-rock apron and
# lawn. Rain refills it but summer evaporation empties 2" in ~8-11 days, so it is rinsed and
# topped up every 2-3 days while it holds water (MMCD's mosquito guidance).
SPLASH_BASIN_GRANITE_24 = FurnitureType(
    tag="FT-SPLASH-BASIN-GRANITE-24", name="Granite splash basin / bird bath, 24\"",
    footprint=(inch(24), inch(24)), height=inch(14),
    storage=False, plan_symbol=None,
    source="Natural granite boulder basin, ~24\" x 24\" x 14\", dish <= 2\" deep with "
           "sloped open sides and a notch spilling south; set on 4\" of compacted stone at "
           "yard grade, with a 2' x 6' washed river-rock apron on fabric beyond the notch. "
           "Stone yard selection; no product named.",
)

# --- W-M-STRW's coat-nook bench (2026-10-14) ----------------------------------------------
#
# A notched oak 2x10 let into the stud bays, seat top 18". Wall-carried, so no legs.
STRW_BENCH = FurnitureType(
    tag="FT-MUD-STRW-BENCH", name='Mudroom stud-bay bench, notched oak 2x10, 95 7/8"',
    footprint=(inch(95.875), inch(9.25)), height=inch(1.5),
    storage=False, plan_symbol="wall-desk", wood_material_ref="oak-8q",
    source="8/4 red oak dressed to 1 1/2\" x 9 1/4\", notched 1 5/8\" x 5 9/16\" at each "
           "stud and scribed to the as-built stud stations. Bears on W-M-STRW's oak support "
           "course and is screwed down through the fingers; eased front arris, 3 3/4\" proud "
           "of the stud faces.",
)

# WIN-M-DINING-E's blind (2026-10-16): the library 27x48 blind at the picture window's width.
CELLULAR_BLIND_6348 = CELLULAR_BLIND_2748.model_copy(update=dict(
    tag="FT-CELLULAR-BLIND-6348", name='Cellular blind, nominal 63 x 48" opening',
    footprint=(inch(63), inch(2)),
    source="Generic inside-mount cellular blind for a nominal 63 x 48-inch opening, the "
           "library 27 x 48 blind's construction at this width; product unselected."))

FURNITURE_TYPES = (STUDY_BUILT_IN_BOOKCASE,
                   CURTAIN_ROD_48, CURTAIN_ROD_84, CELLULAR_BLIND_2748, CELLULAR_BLIND_6348,
                   PORCH_TRACK_176,
                   PORCH_TRACK_102,
                   ACCESS_PANEL_1414, ACCESS_PANEL_1429, ACCESS_PANEL_2015, ACCESS_PANEL_CLG_3029,
                   BATH1_SHELF_2030,
                   MEDIA_SECTIONAL_U, SUITEBATH_SHELF_1130,
                   SUITEBATH_PEGS_24, SUITEBATH_MIRROR_ESTERO,
                   PANTRY_SHELVES_70,
                   STUDY_BENCH, STUDY_DESK, FOLD_LEAF, STUDY_FOOTREST,
                   CLOSET_SHELF_ROD_60, CLOSET_SHELF_ROD_84, CLOSET_SHELF_ROD_96,
                   CLOSET_SHELF_36, TANNFORSEN_1806, STUDIO_KITCHENETTE_4422,
                   MANTEL_ELM_46, SPLASH_BASIN_GRANITE_24, STRW_BENCH)
