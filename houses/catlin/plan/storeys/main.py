# haus: editable
# Main floor — 36'x36' at sheathing, 16" o.c. module, east half open living (WP3.1).
# Exterior walls: CATLIN_EXT_2X6, sheathing exterior face on the 0/36 lines.
# Bearing lines: west wall, center N-S wall (x=18), east wall (18' I-joist spans, E-W).
# Smaller windows follow the stud-bay rules: WT-1424 fits one bay unbroken; WT-3036
# breaks one stud (non-bearing walls only); WT-2736 adds jacks on bearing walls.
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    Door,
    DoorType,
    FloorHeat,
    FloorOpening,
    Node,
    Occupancy,
    RadiantSystem,
    Room,
    RoughOpening,
    Slab,
    Stair,
    StructuralRole,
    Wall,
    Window,
    WindowType,
    face,
    from_node,
    ft,
    in_slab,
    inch,
    pt,
    u_us,
)
from typehaus.model import m

# --- library-of-the-house types ----------------------------------------------
DOOR_TYPES = [
    DoorType(tag="DT-EXT36", width=ft(3), height=ft(6, 8), exterior=True,
             u_factor=u_us(0.20)),
    DoorType(tag="DT-FRENCH36", width=ft(3), height=ft(6, 8), exterior=True,
             operation="double_swing", u_factor=u_us(0.20)),
    DoorType(tag="DT-PATIO60", width=ft(5), height=ft(6, 8), exterior=True,
             operation="slide", u_factor=u_us(0.25)),
    DoorType(tag="DT-INT32", width=ft(2, 8), height=ft(6, 8)),
    DoorType(tag="DT-INT30", width=ft(2, 6), height=ft(6, 8)),
    DoorType(tag="DT-INT30-GLASS", width=ft(2, 6), height=ft(6, 8), glazed=True),
    # Frameless jamb system (no applied casing — drywall return jamb), flush with the gwb.
    DoorType(tag="DT-INT30-TRIMLESS", width=ft(2, 6), height=ft(6, 8), trimless=True),
    DoorType(tag="DT-INT24", width=ft(2), height=ft(6, 8)),
    DoorType(tag="DT-INT60", width=ft(5), height=ft(6, 8), operation="bifold"),
    DoorType(tag="DT-INT56", width=ft(4, 8), height=ft(6, 8), operation="bifold"),
    DoorType(tag="DT-GARAGE192", width=ft(16), height=ft(7), exterior=True,
             operation="overhead"),
]
# One size per width family: every placement of a family shares one height, chosen as
# the tallest that still fits the family's most constrained wall anywhere in the house.
WINDOW_TYPES = [
    # 14" RO — falls between studs on the 16" grid without breaking a stud line. 24"
    # tall because the 5' attic knee wall (WIN-A-W-SM) needs room for the modeled
    # header above the opening below its top plate.
    WindowType(tag="WT-1424", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="awning"),
    # 27" RO — bearing-wall size (N*2-9): one stud broken, jacks added. 36" tall
    # because the garage's 8' wall can't take a 60" height at a 42" sill (header would
    # land above the top plate). 27x36 still clears R310 egress (6.75 sf > 5.7).
    WindowType(tag="WT-2736", width=inch(27), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 30" RO — non-load-bearing size (N*2-6): one stud broken. 36" tall keeps the
    # attic-gable heads below the cathedral-roof framing.
    WindowType(tag="WT-3036", width=inch(30), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 36" RO — concrete basement wall only (no stud module to respect down there).
    WindowType(tag="WT-3660", width=ft(3), height=ft(5), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # Same unit, same glass, no sash: a picture window for the openings that are there for
    # daylight and view only. It is a separate *type* rather than a note on WT-3660 because
    # a fixed unit is a different product on the quote and carries no ventilation or egress
    # credit — the existing tags stay as they are, since they are referenced house-wide.
    WindowType(tag="WT-3660-FIX", width=ft(3), height=ft(5), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="fixed"),
    # The mudroom's picture unit: same 14" RO / 24" tall glass as WT-1424 (still the one
    # size that clears a 16" stud bay unbroken), no sash — it is there for daylight over
    # the bench, not ventilation. A separate type for the same reason WT-3660-FIX is
    # separate from WT-3660: fixed vs. operable is a different product on the schedule.
    WindowType(tag="WT-1424-FIX", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="fixed"),
]

NODES = [
    # Perimeter (splits mirror the basement + partition tees)
    Node(uid="CMN001AAAA", tag="N-M-SW", position=pt(ft(0), ft(0))),
    Node(uid="CMN002AAAA", tag="N-M-S1", position=pt(ft(18), ft(0))),
    Node(uid="CMN003AAAA", tag="N-M-SE", position=pt(ft(36), ft(0))),
    Node(uid="CMN004AAAA", tag="N-M-E1", position=pt(ft(36), ft(18))),
    Node(uid="CMN005AAAA", tag="N-M-NE", position=pt(ft(36), ft(36))),
    Node(uid="CMN006AAAA", tag="N-M-N1", position=pt(ft(18), ft(36))),
    Node(uid="CMN007AAAA", tag="N-M-N2", position=pt(ft(10), ft(36))),
    Node(uid="CMN008AAAA", tag="N-M-NW", position=pt(ft(0), ft(36))),
    Node(uid="CMN009AAAA", tag="N-M-W1", position=pt(ft(0), ft(26, 4))),
    Node(uid="CMN010AAAA", tag="N-M-W2", position=pt(ft(0), ft(21, 8))),
    Node(uid="CMN011AAAA", tag="N-M-W3", position=pt(ft(0), ft(13, 4))),
    # Center bearing line ties
    Node(uid="CMN012AAAA", tag="N-M-C1", position=pt(ft(18), ft(13, 4))),
    Node(uid="CMN013AAAA", tag="N-M-C2", position=pt(ft(18), ft(21, 8))),
    # N-M-C3 came south from y=26'-4" to the stair wall's line on 2026-07-28. It used to be
    # the W-M-C4B/W-M-C5 split; with W-M-C4/C4B gone it is BM-M-HALL's north bearing, and it
    # has to be where W-M-STRS lands or the stair well leaks into the living room through the
    # gap between them. Nothing runs along y=26'-4" east of x=10', so it was free to move.
    Node(uid="CMN014AAAA", tag="N-M-C3", position=pt(ft(18), ft(25, 10))),
    # Interior tees
    # N-M-STR1 and N-M-C3B moved north from y=25'-0" to y=25'-10" with W-M-STRS (2026-07-28),
    # and N-M-C3B then retired into N-M-C3: with the centre line open between them they were
    # two names for the same point. 25'-10" is as far north as the stair wall can go — see
    # FLOOR_OPENINGS.
    Node(uid="CMN015AAAA", tag="N-M-STR1", position=pt(ft(10), ft(25, 10))),
    Node(uid="CMN024AAAA", tag="N-M-STRJ", position=pt(ft(10), ft(26, 4))),
    # W-M-BAE shifts 2' east (2026-07-28); the mudroom door remains at its existing
    # 6" tee clearance.
    Node(uid="CMN016AAAA", tag="N-M-BA1", position=pt(ft(6), ft(26, 4))),
    Node(uid="CMN017AAAA", tag="N-M-BA2", position=pt(ft(6), ft(21, 8))),
    Node(uid="CMN018AAAA", tag="N-M-D1", position=pt(ft(8), ft(21, 8))),
    Node(uid="CMN019AAAA", tag="N-M-D2", position=pt(ft(8), ft(17, 4))),
    Node(uid="CMN020AAAA", tag="N-M-D3", position=pt(ft(8), ft(13, 4))),
    Node(uid="CMN021AAAA", tag="N-M-E2", position=pt(ft(13, 4), ft(17, 4))),
    Node(uid="CMN022AAAA", tag="N-M-E3", position=pt(ft(13, 4), ft(21, 8))),
    Node(uid="CMN023AAAA", tag="N-M-E4", position=pt(ft(18), ft(17, 4))),
    # RM-M-MECH: the framed MEP shaft closet in the house's NW corner (2026-07-28),
    # replacing FURN-M-MUD-CLOSET-N. 6' wide (west wall to 6" shy of D-M-ENTRY's far
    # jamb at 6'-6") x 2'-8" deep — the radon+plumbing chase rides its SW corner, aligned
    # with the matching notch moved into RM-S-BATH1's NW corner directly above it.
    Node(uid="CMN025AAAA", tag="N-M-MECH1", position=pt(ft(0), ft(33, 4))),
    Node(uid="CMN026AAAA", tag="N-M-MECH2", position=pt(ft(6), ft(33, 4))),
    Node(uid="CMN027AAAA", tag="N-M-MECH3", position=pt(ft(6), ft(36))),
]

WALLS = [
    # --- exterior loop (CCW), sheathing-ext on the line -----------------------
    Wall(uid="CMW101AAAA", tag="W-M-S1", start_node="N-M-SW", end_node="N-M-S1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW102AAAA", tag="W-M-S2", start_node="N-M-S1", end_node="N-M-SE",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW103AAAA", tag="W-M-E1", start_node="N-M-SE", end_node="N-M-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CMW104AAAA", tag="W-M-E2", start_node="N-M-E1", end_node="N-M-NE",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CMW105AAAA", tag="W-M-N1", start_node="N-M-NE", end_node="N-M-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW106AAAA", tag="W-M-N2", start_node="N-M-N1", end_node="N-M-N2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    # Split at N-M-MECH3, where RM-M-MECH's east wall tees into the north wall
    # (2026-07-28, MEP shaft closet). corner_style_end moves to W-M-N3B, which now
    # carries the actual NW building corner.
    Wall(uid="CMW107AAAA", tag="W-M-N3", start_node="N-M-N2", end_node="N-M-MECH3",
         assembly="CATLIN_EXT_2X6",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N3"),
    Wall(uid="CMW135AAAA", tag="W-M-N3B", start_node="N-M-MECH3", end_node="N-M-NW",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N3"),
    # Split at N-M-MECH1, where RM-M-MECH's south wall tees into the west wall
    # (2026-07-28, MEP shaft closet).
    Wall(uid="CMW136AAAA", tag="W-M-W1B", start_node="N-M-NW", end_node="N-M-MECH1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW108AAAA", tag="W-M-W1", start_node="N-M-MECH1", end_node="N-M-W1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW109AAAA", tag="W-M-W2", start_node="N-M-W1", end_node="N-M-W2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW110AAAA", tag="W-M-W3", start_node="N-M-W2", end_node="N-M-W3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W2"),
    Wall(uid="CMW111AAAA", tag="W-M-W4", start_node="N-M-W3", end_node="N-M-SW",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W2"),
    # --- center bearing wall (2x6), stacks on the basement concrete line ------
    Wall(uid="CMW112AAAA", tag="W-M-C1", start_node="N-M-S1", end_node="N-M-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS"),
    Wall(uid="CMW113AAAA", tag="W-M-C2", start_node="N-M-C1", end_node="N-M-E4",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS2"),
    Wall(uid="CMW114AAAA", tag="W-M-C3", start_node="N-M-E4", end_node="N-M-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS2"),
    # y 21'-8" .. 25'-10" IS NOT A WALL — it is the BM-M-HALL flitch of LVL, the main-storey
    # twin of BM-S-HALL directly above it. W-M-C4 / W-M-C4B used to stand here; the whole
    # 4'-2" is now open so the hall and the living room read as one room (2026-07-28), the
    # way the second storey already does under its own beam. The bearing stack is unbroken
    # because the beam is *in* it: see BEAMS below.
    Wall(uid="CMW116AAAA", tag="W-M-C5", start_node="N-M-C3", end_node="N-M-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CN"),
    # --- stair / storage block --------------------------------------------------
    # This wall line carries the cut second-floor joists and stacks directly over the
    # basement concrete stair wall. It is split at the two tees on it: the storage wall at
    # N-M-STRJ and the stair wall at N-M-STR1, now 6" apart. W-M-STRW2 is that 6" — the jog
    # of wall between RM-M-MUDROOM's south wall and the head of the stairs.
    Wall(uid="CMW117AAAA", tag="W-M-STRW", start_node="N-M-N2",
         end_node="N-M-STRJ", assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR"),
    Wall(uid="CMW134AAAA", tag="W-M-STRW2", start_node="N-M-STRJ",
         end_node="N-M-STR1", assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR"),
    # The wall at the top of the stairs, pushed north 10" to y=25'-10" (2026-07-28) so it
    # closes against the wells again after they moved. Its north face at 26'-0 3/8" is both
    # wells' south edge: D-M-STAIR opens onto ST-B2M's top nosing in the west lane, RO-1 onto
    # ST-M2S's first tread in the east one. Its east end tees into N-M-C3, which is W-M-C5's
    # south end and BM-M-HALL's north bearing.
    Wall(uid="CMW118AAAA", tag="W-M-STRS", start_node="N-M-STR1",
         end_node="N-M-C3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW119AAAA", tag="W-M-STOS", start_node="N-M-W1",
         end_node="N-M-BA1", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW120AAAA", tag="W-M-STOS2", start_node="N-M-BA1",
         end_node="N-M-STRJ", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- powder bath west of hallway -------------------------------------------
    Wall(uid="CMW121AAAA", tag="W-M-BAE", start_node="N-M-BA1",
         end_node="N-M-BA2", assembly="INT_2X6_PLUMBING", top=ft(9)),
    # --- hallway south wall band ------------------------------------------------
    Wall(uid="CMW122AAAA", tag="W-M-HS1", start_node="N-M-W2",
         end_node="N-M-BA2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW123AAAA", tag="W-M-HS2", start_node="N-M-BA2",
         end_node="N-M-D1", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW124AAAA", tag="W-M-HS3", start_node="N-M-D1",
         end_node="N-M-E3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW125AAAA", tag="W-M-HS4", start_node="N-M-E3",
         end_node="N-M-C2", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- bath2 / laundry / study / closet block ---------------------------------
    Wall(uid="CMW126AAAA", tag="W-M-BA2E", start_node="N-M-D1",
         end_node="N-M-D2", assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CMW127AAAA", tag="W-M-BA2E2", start_node="N-M-D2",
         end_node="N-M-D3", assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CMW128AAAA", tag="W-M-LS", start_node="N-M-E2",
         end_node="N-M-E3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW129AAAA", tag="W-M-CLN", start_node="N-M-D2",
         end_node="N-M-E2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW130AAAA", tag="W-M-CLN2", start_node="N-M-E2",
         end_node="N-M-E4", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- bedroom north wall ------------------------------------------------------
    Wall(uid="CMW131AAAA", tag="W-M-BDN1", start_node="N-M-W3",
         end_node="N-M-D3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW132AAAA", tag="W-M-BDN2", start_node="N-M-D3",
         end_node="N-M-C1", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- RM-M-MECH: framed MEP shaft closet, NW corner (2026-07-28) -------------
    Wall(uid="CMW137AAAA", tag="W-M-MECH-S", start_node="N-M-MECH1",
         end_node="N-M-MECH2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW138AAAA", tag="W-M-MECH-E", start_node="N-M-MECH2",
         end_node="N-M-MECH3", assembly="INT_2X4_PARTITION", top=ft(9)),
]

OPENINGS = [
    # Exterior
    # Pushed east to N-M-N2 (2026-07-28, mudroom conversion): near jamb 6" off the tee
    # where W-M-STRW's bearing stack ties into this wall — as tight as the header's jack
    # studs and the stair wall's own king studs both want — so the closet run west of the
    # door reaches the west wall almost whole. See RM-M-MUDROOM below.
    Door(uid="CMD201AAAA", tag="D-M-ENTRY", host="W-M-N3", type_ref="DT-EXT36",
         position=from_node("N-M-N2", ft(0, 6))),
    Door(uid="CMD202AAAA", tag="D-M-BALC", host="W-M-S2", type_ref="DT-PATIO60",
         position=from_node("N-M-S1", ft(1, 4))),
    # Interior
    # x 10'-8 1/16"..13'-4 1/16": the west lane, which since ST-B2M was mirrored is the one
    # the basement flight arrives in — so this is now the door onto the basement stairs, and
    # RO-1 beside it is the cased way onto ST-M2S. The two swapped roles with the mirror;
    # neither moved.
    Door(uid="CMD203AAAA", tag="D-M-STAIR", host="W-M-STRS", type_ref="DT-INT32",
         position=from_node("N-M-STR1", ft(0, 8.0625)), flip_swing=True),
    # Pushed east to N-M-STRJ (2026-07-28, mudroom conversion): same 6" tee clearance as
    # D-M-ENTRY above it, off the bearing stair wall's jack studs. Renamed with the room.
    Door(uid="CMD204AAAA", tag="D-M-MUD", host="W-M-STOS2", type_ref="DT-INT32",
         position=from_node("N-M-STRJ", ft(0, 6))),
    Door(uid="CMD205AAAA", tag="D-M-BATH1", host="W-M-BAE", type_ref="DT-INT24",
         position=from_node("N-M-BA1", ft(1))),
    # RM-M-MECH's single utility door, on the closet's east (right, as seen from the
    # mudroom) wall — a hinged door for the mechanical/shaft closet, not the sliding
    # bypass style of the mudroom's own storage closets (2026-07-28).
    Door(uid="CMD211AAAA", tag="D-M-MECH", host="W-M-MECH-E", type_ref="DT-INT24",
         position=from_node("N-M-MECH2", ft(0, 4))),
    Door(uid="CMD206AAAA", tag="D-M-BATH2", host="W-M-BDN1", type_ref="DT-INT30",
         position=from_node("N-M-W3", ft(1, 6.5))),
    Door(uid="CMD207AAAA", tag="D-M-LAUN", host="W-M-HS3", type_ref="DT-INT56",
         position=from_node("N-M-D1", ft(0, 4))),
    Door(uid="CMD208AAAA", tag="D-M-STUDY", host="W-M-C3", type_ref="DT-INT30",
         position=from_node("N-M-E4", ft(1, 2.6875)), flip_swing=True),
    Door(uid="CMD210AAAA", tag="D-M-BED", host="W-M-BDN2", type_ref="DT-INT32",
         position=from_node("N-M-D3", ft(5))),
    # Second bedroom <-> living connection, straight through the centre bearing wall.
    # Trimless (drywall return jamb, no casing) so it reads as a slot in the wall from
    # both rooms. W-M-C1 is BEARING, so the solver's framing tables put a structural
    # header over the 2'-6" opening on their own — nothing extra to author here.
    Door(uid="CMD212AAAA", tag="D-M-BED2", host="W-M-C1", type_ref="DT-INT30-TRIMLESS",
         position=from_node("N-M-S1", ft(5))),
    # O-M-HALL, the 2'-8" cased pass-through from the living room into the hall, retired
    # 2026-07-28 with its host wall W-M-C4: the whole 4'-2" it stood in is the opening now.
    # Cased pass-through: living room → dressing corridor (per floorplan).
    Window(uid="CMX301AAAA", tag="WIN-M-BED-W1", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(4, 2.5)),
           sill_height=ft(2)),
    Window(uid="CMX302AAAA", tag="WIN-M-BED-W2", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(9, 6.5)),
           sill_height=ft(2)),
    Window(uid="CMX303AAAA", tag="WIN-M-BED-S1", host="W-M-S1",
           type_ref="WT-3036", position=from_node("N-M-SW", ft(4, 1)),
           sill_height=ft(2)),
    Window(uid="CMX304AAAA", tag="WIN-M-BED-S2", host="W-M-S1",
           type_ref="WT-3036", position=from_node("N-M-SW", ft(9, 5)),
           sill_height=ft(2)),
    Window(uid="CMX305AAAA", tag="WIN-M-BATH2", host="W-M-W3",
           type_ref="WT-1424", position=from_node("N-M-W3", ft(4, 5)),
           sill_height=ft(4)),
    # Picture unit at the wall's stud-grid midpoint: W-M-W1 runs 9'-8" node-to-node, so the
    # true middle is 4'-10" off N-M-NW, but studs on this wall lay out from N-M-NW's own
    # corner (8"+16n) and the closest bay centre to that middle is 4'-8" — 2" off true
    # centre, one 14" RO short of breaking a stud. `from_node` measures to the near edge,
    # not the centre, so the offset below is the bay centre (4'-8") less half the 14" RO.
    # Sill at 3'-0" clears FURN-M-MUD-BENCH's 18" seat the same way WIN-B-SAUNA clears its
    # bench below.
    Window(uid="CMX306AAAA", tag="WIN-M-MUD", host="W-M-W1",
           type_ref="WT-1424-FIX", position=from_node("N-M-NW", ft(4, 1)),
           sill_height=ft(3)),
    Window(uid="CMX307AAAA", tag="WIN-M-LIV-S1", host="W-M-S2",
           type_ref="WT-3036", position=from_node("N-M-SE", ft(3, 5)),
           sill_height=ft(2)),
    Window(uid="CMX308AAAA", tag="WIN-M-LIV-S2", host="W-M-S2",
           type_ref="WT-3036", position=from_node("N-M-SE", ft(7, 5)),
           sill_height=ft(2)),
    Window(uid="CMX309AAAA", tag="WIN-M-LIV-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(6, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX310AAAA", tag="WIN-M-LIV-E2", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(10, 10.5)),
           sill_height=ft(2, 6)),
    # The dining pair, pushed south of where it started (centres were 22' and 26'). The 48"
    # pantry closet now takes the east wall from 22'-8" to 26'-8" and a tall cabinet over a
    # window is not a window, so the glass moved rather than the casework: centres 16'-0" and
    # 20'-8", the northern one clearing the pantry's south end by 8 1/2" of framing.
    #
    # The pair no longer reads at the 4' spacing the living windows below it use, and cannot:
    # E1 crosses onto the south wall segment, and each segment lays its studs out from its own
    # start, so W-M-E1's grid (16" from y=0) and W-M-E2's (16" from y=18') are 8" out of phase
    # with each other. A 27" RO in a bearing wall has to break exactly one stud, which pins
    # each centre to its own host's grid — 16'-0" is 12 bays up W-M-E1, 20'-8" is 2 bays up
    # W-M-E2 — and 4'-8" apart is where that lands them. The node at y=18' is a collinear
    # split rather than a corner, so the wall itself runs through unbroken.
    Window(uid="CMX311AAAA", tag="WIN-M-DIN-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(14, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX312AAAA", tag="WIN-M-DIN-E2", host="W-M-E2",
           type_ref="WT-2736", position=from_node("N-M-E1", ft(1, 6.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX313AAAA", tag="WIN-M-KITCH", host="W-M-E2",
           type_ref="WT-2736", position=from_node("N-M-NE", ft(2, 2.5)),
           sill_height=ft(3, 6)),
    # The cooking window, and the north wall's only one. A recirculating hood moves no air
    # outdoors, so the only way to clear a scorched pan is to open something next to the
    # stove: a 14" awning, immediately west of the range and reachable across the counter.
    # Centre x = 24'-8" is a bay centre on the 16" module, so it breaks no stud; sill 42"
    # clears the 36" counter by 6". The 30x60 that used to sit east of the range at
    # 29'-5"..31'-11" is gone: that stretch of wall is now one 5'-6" run of uppers, which is
    # the trade this kitchen wants — a north window on a north wall buys little light, and the
    # east wall's WIN-M-KITCH already lights the sink.
    Window(uid="82WVR597PA", tag="WIN-M-KITCH-N", host="W-M-N1", type_ref="WT-1424",
           position=from_node("N-M-NE", ft(10, 9)), sill_height=ft(3, 6)),
    # Exterior
    RoughOpening(uid="S4PSJ99JQF", tag="RO-1", host="W-M-STRS", position=from_node("N-M-STR1", ft(4, 4.375)), width=ft(3), height=ft(6, 8), sill_height=m(0)),
]

ROOMS = [
    # RM-M-HALL (CMR408AAAA) was retired into this claim on 2026-07-28, the way the second
    # storey retired RM-S-LANDING and RM-S-STAIR into RM-S-HALL when *its* centre line
    # opened. Taking W-M-C4/C4B out under BM-M-HALL leaves one polygonized face spanning the
    # living room and the old hall band, and two seeds in one face bill the floor twice.
    # The 706 sf that results is the honest area of the room you can now walk around.
    Room(uid="CMR401AAAA", tag="RM-M-LIVING", seed=pt(ft(27), ft(12)),
         occupancy=Occupancy.LIVING, floor_finish="oak"),
    Room(uid="CMR402AAAA", tag="RM-M-BED", seed=pt(ft(9), ft(6)),
         occupancy=Occupancy.BEDROOM, floor_finish="oak"),
    Room(uid="CMR403AAAA", tag="RM-M-BATH1", seed=pt(ft(2), ft(24, 6)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CMR404AAAA", tag="RM-M-BATH2", seed=pt(ft(4), ft(18)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CMR405AAAA", tag="RM-M-LAUNDRY", seed=pt(ft(10, 6), ft(20)),
         occupancy=Occupancy.LAUNDRY, floor_finish="tile"),
    Room(uid="CMR406AAAA", tag="RM-M-STUDY", seed=pt(ft(15, 8), ft(20)),
         occupancy=Occupancy.OFFICE, floor_finish="oak"),
    Room(uid="CMR407AAAA", tag="RM-M-CLOSET", seed=pt(ft(13), ft(15, 4)),
         occupancy=Occupancy.STORAGE, floor_finish="oak"),
    # Retagged from RM-M-STORAGE with the mudroom conversion (2026-07-28): entry vestibule
    # now, not bulk storage, but still Occupancy.STORAGE — there is no MUDROOM occupancy in
    # the closed enum and STORAGE is the closer fit of what exists (unheated-adjacent,
    # hard-finish floor) than LIVING or HALLWAY would be.
    Room(uid="CMR409AAAA", tag="RM-M-MUDROOM", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
    Room(uid="CMR410AAAA", tag="RM-M-STAIR", seed=pt(ft(14, 6), ft(31)),
         occupancy=Occupancy.STAIR, floor_finish="oak"),
    # Framed MEP shaft closet, replacing FURN-M-MUD-CLOSET-N (2026-07-28): the
    # radon+plumbing riser rides its SW corner. STORAGE is the closed enum's closest fit
    # for a mechanical closet, same reasoning as RM-M-MUDROOM above.
    Room(uid="CMR411AAAA", tag="RM-M-MECH", seed=pt(ft(3), ft(34, 6)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
]

ALARMS = [
    Alarm(uid="CMA701AAAA", tag="AL-M-BED", kind=AlarmKind.COMBO, room="RM-M-BED",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CMA702AAAA", tag="AL-M-HALL", kind=AlarmKind.COMBO, room="RM-M-LIVING",
          circuit="CKT-LT-BACKUP"),
]

# Electric radiant floor — the two main-storey comfort zones (2026-07-25). Neither is a
# heating system: the minisplits carry the house and these warm the two floors people stand
# on barefoot, both of which sit just south of the 18' midline.
#
# Sizing is one number applied twice: mat at 12 W/ft2, which is what a 120V floor cable
# delivers at the `spacing=3"` serpentine authored here (12 W/ft2 over 4 lineal feet of
# cable per square foot = 3 W/ft, the working range for floor cable). The circuits in
# plan/circuits.py carry the resulting VA. `in_slab(1/2")` is the setting bed, not the
# structure: SL-M-DECK is 9" of concrete and nothing is cast into it — the mat is laid on
# the cured deck and buried in the thinset/self-leveller under the finish.
#
# Zones are drawn 4" in from every clear face, because mat cannot run to a wall. `stat` is
# the *slab sensor* point; the line-voltage thermostats are ED-M-BATH2-FH-STAT and
# ED-M-DINING-FH-STAT in plan/electrical.py.
FLOOR_HEAT = [
    # RM-M-BATH2's floor. The zone is an L around the WC, shower and tub: radiant cable
    # stays in the open south strip and the narrow centre aisle, with a deliberate 2"+
    # installation gap at every fixture footprint. Keeping the keepouts in this authored
    # polygon makes `advisory.floor_heat_fixture_keepout` verify the actual loop geometry.
    FloorHeat(uid="CMH801AAAA", tag="FH-M-BATH2", room_ref="RM-M-BATH2",
              zone=(pt(ft(0, 5), ft(13, 9)), pt(ft(7, 7), ft(13, 9)),
                    pt(ft(7, 7), ft(15, 8)), pt(ft(4), ft(15, 8)),
                    pt(ft(4), ft(21, 5)), pt(ft(3, 8), ft(21, 5)),
                    pt(ft(3, 8), ft(15, 8)), pt(ft(0, 5), ft(15, 8))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3), embed=in_slab(inch(0.5)),
              stat=pt(ft(2), ft(17, 6))),
    # Under the dining table. FURN-M-DINING covers x 22'-11"..30'-11", y 15'-7"..19'-1"; the
    # zone takes the table's exact width and runs y 13'-9"..21'-0" so it reaches under both
    # chair rows (FURN-M-CHAIR-S* at y=14'-6", -N* at y=20'-2") — feet, not the table legs,
    # are what this is for. 8'-0" x 7'-3" = 58.0 ft2, free-standing in RM-M-LIVING with no
    # room_ref, since the living room is 642 ft2 and only this patch of it is heated.
    FloorHeat(uid="CMH802AAAA", tag="FH-M-DINING",
              zone=(pt(ft(22, 11), ft(13, 9)), pt(ft(30, 11), ft(13, 9)),
                    pt(ft(30, 11), ft(21)), pt(ft(22, 11), ft(21))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3), embed=in_slab(inch(0.5)),
              stat=pt(ft(26, 11), ft(17, 4))),
]

# Structural deck of the main floor: 9" concrete over the basement.
SLABS = [
    Slab(uid="CMS501AAAA", tag="SL-M-DECK",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(9), openings=("FO-M-STAIR",), assembly="CATLIN_DECK_9_INT"),
]

# The opening is drawn to the *finished* well, not to the wall centrelines: it is the
# shaft a stair actually climbs, and the u-split resolver anchors its flights to the
# opening's near corner. West/east are W-B-STR's and W-B-CN's basement concrete faces —
# 12" concrete is thicker than the 2x6 walls stacked on it, so the basement is the
# narrowest point of the shaft and the one that sizes the flights.
#
# Run, north to south (2026-07-28): the well now *ends* on the wall instead of starting on
# one. North is W-B-N2's inside concrete face at y=35'-0", which the main deck bears on —
# the well used to stop 11 7/8" short of it and leave a slab sliver nothing could use.
#
# South is W-M-STRS's stair-side face at 26'-0 3/8", which is where the *second* storey's
# stair puts it and not a free choice. FO-S-STAIR's south edge is ST-M2S's springing point —
# its first tread starts there — so any wall north of that line would stand on that tread.
# The two wells therefore share one south edge, the stair wall's north face, and each takes
# whatever run its own north limit leaves.
#
# For this one that is 8'-11 5/8": the IRC R311.7.6 36" landing plus six 11 15/16" treads.
# Deeper than the 11" the shorter well used to give and deliberately not trimmed back to it
# — trimming would only reopen the ledge in front of D-M-STAIR. 11 15/16" against a 7 11/16"
# riser is a slow, comfortable basement flight, well inside R311.7.5.2's 10" minimum.
FLOOR_OPENINGS = [
    FloorOpening(uid="CMF601AAAA", tag="FO-M-STAIR",
                 outline=(pt(ft(10, 6), ft(26, 0.375)), pt(ft(17, 6), ft(26, 0.375)),
                          pt(ft(17, 6), ft(35)), pt(ft(10, 6), ft(35))),
                 bearing_refs=("W-M-STRW", "W-M-STRW2")),
]

# 7'-0" well = 3'-3 3/4" + 4 1/2" well partition + 3'-3 3/4". Each flight clears the
# IRC R311.7.1 36" minimum above the handrail with room for the rail to project; the
# landing is the R311.7.6 36" minimum measured in the direction of travel.
#
# `turn_direction="left"` mirrors the pair across the well (2026-07-28): the flight springs
# from the basement in the *east* lane (x 14'-2 1/4"..17'-6") and arrives on the main floor
# in the *west* one (x 10'-6"..13'-9 3/4"), which is D-M-STAIR's lane. ST-M2S is mirrored
# with it, so the east lane is now the flight *up* to the second floor, behind RO-1. Each
# of the stair wall's two openings therefore faces a lane you can walk into, which is the
# arrangement it always had — the mirror swapped which opening serves which stair.
#
# No guard is authored at the head: W-M-STRS spans the whole south edge, and its two
# openings each stand over a flight rather than over a drop.
STAIRS = [
    Stair(uid="CST701AAAA", tag="ST-B2M", floor_opening="FO-M-STAIR",
          from_storey="basement", to_storey="main", width=ft(3, 3.75),
          layout="u_split_landing", run_direction="y", turn_direction="left",
          start=pt(ft(10, 6), ft(26, 0.375)), landing_depth=ft(3)),
]

# The beam that lets the main-storey centre line be open between the hall and the living
# room (2026-07-28) — the twin of BM-S-HALL one storey up, and authored the same way.
#
# CLAUDE.md's house fact is that x=18' is a bearing line from the footings to RB-HOUSE.
# This does not open it up: the LVL is the bearing line for these 4'-2", and the wall lands
# back on the stack either side.
#
# Load, per foot of beam:
#   FS-SECOND    18' tributary (half of each 18' I-joist span either side of the centre
#                line), 40 psf LL + 15 psf DL                              ~ 990 plf
# plus one point load, not a line: over this stretch the storey above has no centre wall at
# all — BM-S-HALL replaced it — so everything above (attic floor, RB-HOUSE, the second-storey
# plate) arrives as that beam's end reactions rather than as a uniform run. Its south
# reaction, ~8.1 k, lands at y=22'-4", 8" north of this beam's own south bearing.
#
# Over the 4'-2" clear span that is M = 5.7 ft-k and V = 8.9 k at the south end, most of the
# latter being that reaction going almost straight into the jack pack 8" away. Three plies
# of 1.75x11.875 LVL give Sx = 123 in^3 (26.7 ft-k at Fb = 2,600 psi) and 62 in^2 of shear
# area (11.8 k), and deflect well inside L/360 = 0.14". Same section and ply count as
# BM-S-HALL and RB-HOUSE — one LVL depth on the job — and it is the shear, not the moment,
# that sizes it.
#
# It bears on the ends of the wall segments it replaced — W-M-C3 south, W-M-C5 north — each
# of which needs a jack pack under it, and both stack onto the basement concrete centre wall
# W-B-CN and down to the footings, so the reaction has somewhere to go.
# Framed FLUSH, not dropped: `top_elevation` pins its top to the second-storey datum, which
# is top-of-joist, so FS-SECOND's I-joists hang off it in face-mount hangers and its soffit
# lands on the 9'-0" plate line of the walls either side. That keeps the 9' ceiling unbroken
# across the opening — a dropped beam would hang its full 11-7/8" into it.
BEAMS = [
    Beam(uid="CMBM01AAAA", tag="BM-M-HALL", start_node="N-M-C2", end_node="N-M-C3",
         size="3-1.75x11.875 LVL", bearing_refs=("W-M-C3", "W-M-C5"),
         top_elevation=ft(10)),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SLABS,
            *FLOOR_OPENINGS, *STAIRS, *BEAMS]
