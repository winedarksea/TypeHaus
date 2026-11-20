"""RM-M-PANTRY's shelf stack: the case, its strut post and the west return (2026-11-20).

House-local: 73 1/4" is this room's 73 1/2" clear span less a 1/8" scribe each end.
Safe to climb, not built for it; arithmetic in notes/pantry_climbable_shelving.md.

One open bay between two floor-bearing 3/4" maple-ply end uprights, no back. Each level is
one continuous 6/4 red oak board (SB-M-PANTRY) on an oak end cleat each side, screwed up
through them (round hole front, slot rear), 1/4" off the north wall. Mid-span it rests on a
cut-down B-Line B409 bracket off a P1000 strut post lagged to W-M-N1B's x=21'-4" stud, the
board's rear edge notched round the post. In front of the post the ~16 1/2" lane lets a 15"
bin slide east to the doorway.
"""

from typehaus.model import (
    BuiltInBookcaseBay,
    BuiltInBookcaseSpec,
    FurnitureCut,
    FurnitureType,
    ProductPart,
    ft,
    inch,
)

# East's old schedule on every board: 15 3/4 / 16 3/4 / 18 / 8 1/2 / 8 3/4 / 8 3/4 clear.
# The 35"->53" opening takes the mixer and the microwave, ED-M-PANTRY-RC1 at 48".
_TOPS = (inch(17), inch(35), inch(54.25), inch(64), inch(74), inch(84))

PANTRY_SHELVES_70 = FurnitureType(
    tag="FT-KIT-PANTRY-SHELVES-70", name='Pantry open shelf stack, 73 1/4" x 18"',
    footprint=(inch(73.25), inch(18)), height=ft(7),
    storage=True, work_surface=False, plan_symbol="bookcase",
    wood_material_ref="oak-shelf-6q",
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(71.75), height=inch(84),
                                 horizontal_board_count=6, board_tops=_TOPS),),
        shelf_depth=inch(18), horizontal_board_thickness=inch(1.25),
        divider_thickness=inch(0.75), back_thickness=inch(0),
        panel_material_ref="maple-ply-prefin-34", board_material_ref="oak-shelf-6q",
    ),
    # One cleat per board end, 2" short of the front.
    cut_list=(FurnitureCut(part="shelf cleat", count=12, thickness=inch(0.75),
                           width=inch(2.5), length=inch(16), material_ref="oak-shelf-4q"),),
    # The west upright is 25 3/4" deep: its forward 7 3/4" is FT-KIT-PANTRY-RETURN's west
    # end, billed here only. It screws to the west-wall framing, never to W-M-PAN-S's cassette.
    parts=(ProductPart(role="frame", product_ref="PROD-MAPLE-PLY-PREFIN-34",
                       cut=(inch(25.75), inch(84))),
           ProductPart(role="frame", product_ref="PROD-MAPLE-PLY-PREFIN-34",
                       cut=(inch(18), inch(84)))),
    source="Site-built millwork, safe to climb (notes/pantry_climbable_shelving.md). Two 3/4\" "
           "prefinished maple ply end uprights, floor-bearing, screwed to the corner framing; "
           "six continuous 1 1/4\" red oak boards (SB-M-PANTRY) on bench-fixed oak end cleats "
           "and one strut bracket each at mid-span (FT-KIT-PANTRY-STRUT). No back, no blocking, "
           "no shelf pins. Design load 40 psf, or 250-300 lb anywhere.",
)

# Floor to the top board's underside. Open face south; one bracket under each board, the
# post lagged through its web to the stud at every bracket, so it cannot rotate.
PANTRY_STRUT = FurnitureType(
    tag="FT-KIT-PANTRY-STRUT", name='Pantry shelf strut post, P1000 x 82 3/4" with 6 brackets',
    footprint=(inch(1.625), inch(1.625)), height=inch(82.75),
    storage=False, work_surface=False,
    parts=(ProductPart(role="frame", product_ref="PROD-UNISTRUT-P1000-PG", length=inch(82.75)),
           ProductPart(role="fitting", product_ref="PROD-BLINE-B409-18-ZN", quantity=6),
           ProductPart(role="fitting", product_ref="PROD-LAG-3-8X5-ZN", quantity=6)),
    source="Unistrut P1000 post, B-Line B409-18 brackets cut to 15 5/8\" (cold-galvanized "
           "end), each bolted to the post on a spring channel nut; 3/8\" x 5\" lag through the web "
           "just above each bracket into W-M-N1B's stud. Boards notched 1 3/4\" x 1 5/8\" round "
           "the post and screwed up through a slot in the bracket.",
)

# 12" clear x 7 3/4" deep in the 8" strip at the west wall, ends on the west upright's
# forward part (drawn, not billed, here) and its own floor-standing ply panel; boards
# butted to the main boards' fronts, not glued. 1/4" off W-M-PAN-S, nothing fixed to it.
PANTRY_RETURN = FurnitureType(
    tag="FT-KIT-PANTRY-RETURN", name='Pantry west return, 13 1/2" x 7 3/4"',
    footprint=(inch(13.5), inch(7.75)), height=ft(7),
    storage=True, work_surface=False, plan_symbol="bookcase",
    wood_material_ref="oak-shelf-6q",
    built_in_bookcase=BuiltInBookcaseSpec(
        bays=(BuiltInBookcaseBay(clear_width=inch(12), height=inch(84),
                                 horizontal_board_count=6, board_tops=_TOPS),),
        shelf_depth=inch(7.75), horizontal_board_thickness=inch(1.25),
        divider_thickness=inch(0.75), back_thickness=inch(0),
        panel_material_ref="maple-ply-prefin-34", board_material_ref="oak-shelf-6q",
    ),
    cut_list=(FurnitureCut(part="return cleat", count=12, thickness=inch(0.75),
                           width=inch(2.5), length=inch(6), material_ref="oak-shelf-4q"),),
    parts=(ProductPart(role="frame", product_ref="PROD-MAPLE-PLY-PREFIN-34",
                       cut=(inch(7.75), inch(84))),),
    source="Site-built with FT-KIT-PANTRY-SHELVES-70: six 1 1/4\" red oak boards "
           "(SB-M-PANTRY-RETURN) on oak cleats between the west upright's forward 7 3/4\" and "
           "a 7 3/4\" x 84\" maple ply end panel standing on the floor.",
)

PANTRY_SHELF_TYPES = (PANTRY_SHELVES_70, PANTRY_STRUT, PANTRY_RETURN)
