# haus: editable
# Attic — habitable hot-roofed cathedral storey (WP3.1, WP3.11); 2x6 envelope walls.
# 5' knee walls east/west (eave sides), gable walls north/south frame ToRoof,
# ridge runs N-S over the center wall line, 4:12, zero overhang (first-class).
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    Door,
    DeckLayer,
    FloorOpening,
    FloorSystem,
    FollowRoof,
    JoistSpec,
    Node,
    Occupancy,
    Pitch,
    Railing,
    RailingKind,
    Roof,
    RoofForm,
    Room,
    Stair,
    StructuralRole,
    ToRoof,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

NODES = [
    Node(uid="CAN001AAAA", tag="N-A-SW", position=pt(ft(0), ft(0))),
    Node(uid="CAN002AAAA", tag="N-A-S1", position=pt(ft(10), ft(0))),
    Node(uid="CAN003AAAA", tag="N-A-S2", position=pt(ft(18), ft(0))),
    # Vestibule screen line. 22'-8", not the source's 22.31 (2026-08-01 gable pass): this
    # node is where W-A-S4 starts, and a wall's stud grid lays out from its start node, so
    # this x sets the phase of every bay centre on the east half of the south gable. At
    # 22'-4" the east half was 4" out of phase with a mirror of the west half — 36' minus
    # 22'-4" is 13'-8", which is not a multiple of 16" — which is the "the plan, not the
    # window" phase error the old WIN-A-S3/S4 note described. 22'-8" is 272" = 16 x 17, so
    # W-A-S4's bay centres and W-A-S1's are the same phase and mirror exactly about x=18'.
    # The screen is a dangling pair that closes no room polygon (see W-A-VE below), so the
    # 4" costs nothing but its own position; it moves the screen *away* from the stair well
    # at x 21'-1 3/4", widening that gap rather than pinching it.
    Node(uid="CAN011AAAA", tag="N-A-V1", position=pt(ft(22, 8), ft(0))),
    Node(uid="CAN004AAAA", tag="N-A-SE", position=pt(ft(36), ft(0))),
    Node(uid="CAN005AAAA", tag="N-A-E1", position=pt(ft(36), ft(9))),
    Node(uid="CAN006AAAA", tag="N-A-NE", position=pt(ft(36), ft(36))),
    Node(uid="CAN007AAAA", tag="N-A-N1", position=pt(ft(18), ft(36))),
    Node(uid="CAN008AAAA", tag="N-A-NW", position=pt(ft(0), ft(36))),
    # Den north wall, y=5'-7" (source 5.611); band wall, y=9'-0" (source 9.228).
    Node(uid="CAN009AAAA", tag="N-A-C1", position=pt(ft(18), ft(5, 7))),
    Node(uid="CAN012AAAA", tag="N-A-C2", position=pt(ft(18), ft(9))),
    Node(uid="CAN010AAAA", tag="N-A-D1", position=pt(ft(10), ft(5, 7))),
    Node(uid="CAN013AAAA", tag="N-A-V2", position=pt(ft(22, 8), ft(5, 7))),
    # A legitimate wing-wall terminus: the vestibule's north screen stops at the stair
    # well's west edge, exactly as the source's Den north wall does.
    Node(uid="CAN014AAAA", tag="N-A-V3", position=pt(ft(21, 2), ft(5, 7)),
         open_end=True),
]

WALLS = [
    # Gable ends (south/north) — raked studs, sloped plates via ToRoof (WP3.11).
    Wall(uid="CAW101AAAA", tag="W-A-S1", start_node="N-A-SW", end_node="N-A-S1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW102AAAA", tag="W-A-S2", start_node="N-A-S1", end_node="N-A-S2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW103AAAA", tag="W-A-S3", start_node="N-A-S2", end_node="N-A-V1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S2"),
    Wall(uid="CAW114AAAA", tag="W-A-S4", start_node="N-A-V1", end_node="N-A-SE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S2"),
    Wall(uid="CAW104AAAA", tag="W-A-N1", start_node="N-A-NE", end_node="N-A-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N1"),
    Wall(uid="CAW105AAAA", tag="W-A-N2", start_node="N-A-N1", end_node="N-A-NW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N2"),
    # Knee walls (east/west eave sides) — 5', carry the low roof edge.
    Wall(uid="CAW106AAAA", tag="W-A-E1", start_node="N-A-SE", end_node="N-A-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E1"),
    Wall(uid="CAW107AAAA", tag="W-A-E2", start_node="N-A-E1", end_node="N-A-NE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E2"),
    Wall(uid="CAW108AAAA", tag="W-A-W1", start_node="N-A-NW", end_node="N-A-SW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-W1"),
    # Center bearing wall under the ridge, full length, frames to the roof. This is
    # NOT a partition: RB-HOUSE bears on it continuously, so it is the reason the roof
    # is a structural-ridge system (rafters simply span ridge->knee wall, no thrust on
    # the 5' knee walls). Opening this line up without a beam would dump ~1.5 klf of
    # thrust into the knee walls. 2x6 to match the bearing stack below (W-S-C1/C3).
    Wall(uid="CAW109AAAA", tag="W-A-C1", start_node="N-A-S2", end_node="N-A-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C1"),
    Wall(uid="CAW115AAAA", tag="W-A-C1B", start_node="N-A-C1", end_node="N-A-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C2"),
    # y 9'..36'. Between y=22'-4" and 30'-10" the storey below carries no wall — that run
    # is BM-S-HALL, three plies of 11-7/8" LVL — so this wall (and RB-HOUSE through it)
    # lands on the beam there. `stacks_on` names W-S-C4B, the centre-wall segment north of
    # the opening, because the tiebreaker has to name a *wall*.
    Wall(uid="CAW110AAAA", tag="W-A-C2", start_node="N-A-C2", end_node="N-A-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C4B"),
    # South rooms: den (west of center) + study (east of center). Framed to the roof
    # deck like the other attic partitions, and since 2026-07-31 the den follows the roof
    # too (see its Room.ceiling below) — it lost its 7'-6" dropped ceiling to the south
    # gable's juliet pair, whose 8'-0" head the drop would have buried.
    #
    # WHY THE DEN MOVED WEST INSTEAD OF ONTO ITS SOURCE FOOTPRINT (see the structural-ridge
    # note above): the source draws the Den at x 13'-9"..22'-4", straddling the bearing line,
    # and its own centre wall is dashed and stops short of the south gable. RB-HOUSE bears
    # continuously on W-A-C1/C1B/C2, so that line cannot open up. Shifting the Den to
    # x 10'-0"..18'-0", y 0..5'-7" keeps *both* source dimensions (8'-0" x 4'-10 1/2" clear)
    # and lets RM-A-WEST run full depth to the south gable for x 0..10', which is what the
    # source's "588.12 sq ft, 17'-3 3/4" x 35'-4"" west loft actually is. The cost is
    # ~21 sf: our Den takes 8' of the west loft's south end where the source's takes 4'-3".
    Wall(uid="CAW111AAAA", tag="W-A-DN", start_node="N-A-D1", end_node="N-A-C1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW112AAAA", tag="W-A-DW", start_node="N-A-S1", end_node="N-A-D1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW113AAAA", tag="W-A-SN", start_node="N-A-C2", end_node="N-A-E1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    # Stair vestibule screen: the source's Den east + north walls, kept near where the
    # source draws them (y 5.611 exactly; x moved from the source's 22.31 to 22'-8" by the
    # 2026-08-01 gable pass — see N-A-V1) even though the Den itself moved west. They wrap
    # the head of ST-S2A so the arrival is enclosed on the Study side. Being a dangling pair
    # they close no polygonized face, so RM-A-STUDY still reads as one room around them —
    # which is also how the source's 123.39 sf "Study" reads. That is also what makes the
    # 4" x-shift free: nothing dimensions off this line except the screen itself.
    Wall(uid="CAW116AAAA", tag="W-A-VE", start_node="N-A-V1", end_node="N-A-V2",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW117AAAA", tag="W-A-VN", start_node="N-A-V3", end_node="N-A-V2",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
]

OPENINGS = [
    Door(uid="CAD201AAAA", tag="D-A-HALVES", host="W-A-C2", type_ref="DT-INT-SWING32",
         position=from_node("N-A-N1", ft(4))),
    Door(uid="CAD202AAAA", tag="D-A-DEN", host="W-A-DN", type_ref="DT-INT-SWING30",
         position=from_node("N-A-D1", ft(1))),
    # The band wall's opening onto the stair head — the source's 2'-7 1/2" gap at
    # x 18'-6"..21'-1 3/4", the only way between the east loft and the stair vestibule.
    Door(uid="CAD203AAAA", tag="D-A-STUDY", host="W-A-SN", type_ref="DT-INT-SWING30",
         position=from_node("N-A-C2", ft(0, 8.875))),                 # x 19'-11 7/8"
    Door(uid="CAD204AAAA", tag="D-A-VEST", host="W-A-VE", type_ref="DT-INT-SWING30",
         position=from_node("N-A-V1", ft(0, 11.25))),                 # y 2'-2 1/4"
    # South gable, 2026-08-01 pass: two WT-1448 flanking the juliet pair below, and that
    # is the whole gable — four openings, mirror-symmetric about the ridge.
    #
    # WHAT THIS REPLACED, AND WHY. The 2026-07-30 pass put four WT-1424 here, one on each
    # of the lower storeys' four south columns (x 3'-4", 8'-8", 28'-0", 33'-4"). It was
    # right about the framing and wrong about the elevation: 14x24 next to the 18x64 juliet
    # pair is a 4:1 jump, so the four read as vents rather than windows, on a second head
    # line (4'-8") 3'-4" below the pair's, with 8' of blank gable between the two groups.
    # And the gable was not symmetric — this file's own rule (CLAUDE.md: "gables read
    # symmetric about the ridge before they answer to anything below") lost to the columns.
    #
    # The corner pair went first. At x 3'-4" the 4:12 rake leaves 6'-1" of wall and at
    # x 33'-8" it leaves 6'-0"; nothing can stand there that does not look like a stamp.
    # Cutting them is what lets the survivors grow, because the two that remain (x 8'-8"
    # and its mirror) stand where the wall is 8'-8" at the outer jamb — 2'-0" of clear
    # above a 6'-8" head. So they take WT-1448 and the gable reads as one graded group
    # stepping with the rake: heads at 6'-8" then 8'-0", one 2'-8" sill under all four.
    #
    # WHY NOT WT-1864 FOR THE FLANKERS, which would have made the four one family and
    # needed no new type: an 18" RO breaks a stud, so it takes the jamb pack, and on a
    # nonbearing wall that header is a 2-2x6 (5.5"). At the nearest usable stud line
    # (x 8'-0"/28'-0") the header's outer end lands at x 7'-0", where the roof underside is
    # 8'-3.7" and the header top wants 8'-5.5" — 1.8" short. It is the header, not the
    # glass, that the rake refuses. A 14" RO fits inside a bay and takes no pack at all
    # (resolve/framing/openings.py needs_jamb_pack), so only its own head has to clear.
    #
    # SYMMETRY. WIN-A-S3 sits at x 27'-4", the exact mirror of WIN-A-S2's 8'-8", which is
    # only possible because N-A-V1 moved to 22'-8" this pass — see the note there. Both are
    # bay centres on their own host's grid (8" + 16n from the wall start), as a 14" RO must
    # be. The cost is that neither flanker caps a lower-storey column any more: the columns
    # are 8'-8"/28'-0" and a mirror of 8'-8" is 27'-4", so on the east half the gable and
    # the storeys below now disagree by 8". That is the same 8" phase error the main and
    # second storeys carry, and the gable rule says the ridge wins.
    #
    # Tags: WIN-A-S1/S4 (the retired corner pair) are gone rather than renumbered, so S2/S3
    # keep their uids and IFC GlobalIds. The sequence reads S2, JUL-W, JUL-E, S3 west→east.
    Window(uid="CAX302AAAA", tag="WIN-A-S2", host="W-A-S1", type_ref="WT-1448",
           position=from_node("N-A-SW", ft(8, 1)), sill_height=ft(2, 8)),   # x 8'-8"
    Window(uid="CAX303AAAA", tag="WIN-A-S3", host="W-A-S4", type_ref="WT-1448",
           position=from_node("N-A-V1", ft(4, 1)), sill_height=ft(2, 8)),   # x 27'-4"
    # ...and the middle of the same gable, which the flankers leave blank: a pair of 18x64
    # casements straddling the ridge, reading together like a juliet balcony without being
    # one. No door, no guard, no walking surface — the 2'-8" sill (the storey-wide south
    # line, held here on purpose) clears R312.2's 24" fall-protection trigger by 8", so the
    # rule never fires. The head at 8'-0" is 3'-3" under the roof underside at each window's
    # outer jamb, far clear of the silent shortening in resolve/geometry_openings.py — this
    # pair's height is a proportion decision, not a rake one.
    #
    # WHY THE PAIR SHRANK (2026-07-31, hours after it was first drawn at 32x76 on the
    # x 16'-0"/20'-0" bay centres): 80" x 76" of glass took over a gable whose other four
    # openings were then 14x24, and the two units read as two windows rather than one
    # mullioned opening. 50" x 64" overall is the same composition at a size the facade can
    # hold. The 2026-08-01 pass came at the same gap from the other end — the flankers grew
    # to 14x48 instead of the pair shrinking further — so 50x64 stands.
    #
    # WHY STUD LINES AND NOT BAY CENTRES: the gable's stud grid is continuous across the
    # ridge — W-A-S2 lays out from N-A-S1 (x 10'-0") and W-A-S3 from N-A-S2 (x 18'-0"), and
    # 8'-0" is exactly six modules — so a pair symmetric about the ridge has only two
    # positions: the bay centres at x 16'-0"/20'-0" (48" apart) or the stud lines at
    # x 16'-8"/19'-4" (32" apart). That fixes `pier + RO width` at 48" or 32", and the
    # 32" pairing is the only one that brings the units closer. An 18" RO centred on a stud
    # line interrupts that one stud and nothing else (resolve/framing/stud_module.py: at 16"
    # o.c. with 1-1/2" studs, anything up to 30" clears the flanking lines), so the tighter
    # pair is also the cheaper frame — one broken stud each instead of the 32" unit's two.
    #
    # WHY 18" AND NOT 20": the clear pier between the two ROs is 14", centred on W-A-C1 and
    # the RB-HOUSE south bearing point. W-A-C1's 5-1/2" stud body plus a jack and king each
    # side is 11-1/2", so 14" carries the bearing with 2-1/2" to spare and lets the kings
    # double as the T-intersection's drywall backing; a 20" pair leaves 12", which is the
    # arithmetic minimum and no more. That pier is also the composition's mullion: it is why
    # the two units read as one opening.
    #
    # Tags are descriptive rather than positional because the WIN-A-S* numbers ran west→east
    # and a mid-facade insertion could not join that sequence without renumbering the lot.
    # (The 2026-08-01 pass retired S1 and S4, which would now make the numbers contiguous
    # again — but renaming these two would break their IFC GlobalIds for cosmetics.)
    Window(uid="CAX311AAAA", tag="WIN-A-S-JUL-W", host="W-A-S2", type_ref="WT-1864",
           position=from_node("N-A-S1", ft(5, 11)), sill_height=ft(2, 8)),  # x 16'-8"
    Window(uid="CAX312AAAA", tag="WIN-A-S-JUL-E", host="W-A-S3", type_ref="WT-1864",
           position=from_node("N-A-S2", ft(0, 7)), sill_height=ft(2, 8)),   # x 19'-4"
    # The source attic has no north, east or west opening at all; these three are kept for
    # daylight and cross-ventilation and are this storey's only openings with no counterpart.
    Window(uid="CAX304AAAA", tag="WIN-A-N1", host="W-A-N2", type_ref="WT-3036",
           position=from_node("N-A-NW", ft(6, 1)), sill_height=ft(2)),
    Window(uid="CAX305AAAA", tag="WIN-A-N2", host="W-A-N1", type_ref="WT-3036",
           position=from_node("N-A-NE", ft(6, 9)), sill_height=ft(2)),
    # Knee-wall windows, one at each end of the east and west walls (2026-07-30 facade
    # pass). The 5' knee walls are the one place in the house where the 14" family is
    # chosen for height rather than width: at sill 2'-6" the head sits at 4'-6", 3" under
    # the double top plate, which is all a 5' wall has to give. Placing them in pairs at
    # the ends rather than one in the middle gives each long blank flank two accents and
    # lets the corner rooms — not just the middle of the loft — see out.
    #
    # WIN-A-W-N is the old WIN-A-W-SM (uid kept, so its IFC GlobalId survives), moved off
    # the wall's midpoint at y=18'. Every centre is a bay centre on its own host's grid.
    # West lands 3'-4" in from both corners, exactly symmetric about y=18'. East is 4"
    # off that at its north end: W-A-E2's grid starts at N-A-E1 (y=9'), not at the corner,
    # so 32'-8" is not a bay centre there and 32'-4" is the nearest one.
    Window(uid="CAX308AAAA", tag="WIN-A-W-S", host="W-A-W1", type_ref="WT-1424",
           position=from_node("N-A-NW", ft(32, 1)), sill_height=ft(2, 6)),   # y 3'-4"
    Window(uid="CAX306AAAA", tag="WIN-A-W-N", host="W-A-W1", type_ref="WT-1424",
           position=from_node("N-A-NW", ft(2, 9)), sill_height=ft(2, 6)),    # y 32'-8"
    Window(uid="CAX309AAAA", tag="WIN-A-E-S", host="W-A-E1", type_ref="WT-1424",
           position=from_node("N-A-SE", ft(2, 9)), sill_height=ft(2, 6)),    # y 3'-4"
    Window(uid="CAX310AAAA", tag="WIN-A-E-N", host="W-A-E2", type_ref="WT-1424",
           position=from_node("N-A-E1", ft(22, 9)), sill_height=ft(2, 6)),   # y 32'-4"
]

ROOMS = [
    Room(uid="CAR401AAAA", tag="RM-A-WEST", seed=pt(ft(9), ft(20)),
         occupancy=Occupancy.MEDIA, floor_finish="carpet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR402AAAA", tag="RM-A-EAST", seed=pt(ft(27), ft(20)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    # Cathedral like the other three (2026-07-31): the 7'-6" dropped ceiling it used to
    # carry would have buried the 8'-0" head of WIN-A-S-JUL-W, which stands in this room's
    # stretch of the south gable. Under RF-HOUSE the Den's clear face (x 10'-18') runs
    # 9'-4" to 12'-0" of headroom, so R305 is satisfied with room to spare.
    Room(uid="CAR403AAAA", tag="RM-A-DEN", seed=pt(ft(14), ft(4)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR404AAAA", tag="RM-A-STUDY", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
]

ALARMS = [
    Alarm(uid="CAA701AAAA", tag="AL-A-COMBO", kind=AlarmKind.COMBO, room="RM-A-WEST",
          circuit="CKT-LT-BACKUP"),
]

# The hot roof itself: gable, 4:12, ridge N-S, zero overhang (first-class #29).
# No fascia: the standing-seam siding and roofing are one continuous skin over the flush
# edge — the resolver carries the wall metal to the roofing underside and caps the joint
# with corner trim (resolve/roof_trim.py), and the ridge cap derives from the roof's vent
# channel. The box gutter and drip edge ride in params/roof_trim.py (authored runs, not
# derivable from a plane).

ROOFS = [
    Roof(uid="CARF01AAAA", tag="RF-HOUSE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-A-E1", "W-A-E2", "W-A-W1"),
         assembly="CATLIN_ROOF", overhang=ft(0), ridge_direction="y",
         # The barge-board answer for a roof that cannot have a barge board (2026-08-01).
         # With zero overhang the formed corner trim is the only piece standing at the rake,
         # and it was ordered in the panels' own white — so the gable read as a knife edge.
         # Ordered in the casings' charcoal instead, its 4" leg draws a 4-1/2" dark band
         # down both rakes, round both eaves and along the ridge: one outline, no new
         # geometry, no custom fabrication, just a second coil colour.
         edge_trim_material="metal-dark-exterior"),
]

BEAMS = [
    # Ridge beam over the center wall line: 3 plies of 1.75x11.875 LVL (5.25x11.875).
    # Continuously supported by the W-A-C1/C2 bearing wall directly beneath it — not a
    # 36' clear span between the gables (no LVL spans that at ~500 plf). bearing_refs
    # names the wall it seats on, which is what the framing schedule prints.
    Beam(uid="CABM01AAAA", tag="RB-HOUSE", start_node="N-A-S2",
         end_node="N-A-N1", size="3-1.75x11.875 LVL",
         bearing_refs=("W-A-C1", "W-A-C2")),
]

# The well is the source's (x 21'-1 3/4"..35'-9", y 5'-10 3/4"..8'-11 3/8"), snapped to the
# *finished* faces around it the way FO-S-STAIR is: east is the east wall's inside gwb face
# (36' less 6 5/8" of sheathing + stud + board), north is W-S-SS2's south gwb face (9'-0"
# less 2 3/8"), and the south edge is then a clean 3'-0" back so ST-S2A's 3'-0" width fits
# the well exactly. That is what puts the outer winder carriage on a wall it can bear on;
# the port had this edge on the x=36' sheathing plane, where the carriage's wall ledger
# resolved *outside* the building.
#
# The well lands in RM-S-STUDY2 below, which is where the source draws the flight; the port
# had it in RM-S-BED1, which is also why D-S-BED1 used to open into the stair band.
FLOOR_OPENINGS = [
    FloorOpening(uid="CAF601AAAA", tag="FO-A-STAIR",
                 outline=(pt(ft(21, 2), ft(5, 9.625)),
                          pt(ft(35, 5.375), ft(5, 9.625)),
                          pt(ft(35, 5.375), ft(8, 9.625)),
                          pt(ft(21, 2), ft(8, 9.625)))),
]

FLOOR = [
    FloorSystem(uid="CAF602AAAA", tag="FS-ATTIC",
                joists=JoistSpec(member="11.875 I-joist", spacing=inch(16),
                                 direction="x",
                                 # BM-S-HALL is the centre line for its 8'-6"; the joists
                                 # either side of the hall opening hang off it.
                                 bearing_refs=("W-S-W3", "W-S-C1", "W-S-E2",
                                               "BM-S-HALL")),
                subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
                openings=("FO-A-STAIR",)),
]

# Guard the open south edge of the attic stair well in RM-A-STUDY. This reuses the balcony
# guard's 42" metal fascia-mounted railing family and post spacing, but starts at the attic
# walking surface rather than the exterior deck datum.
STAIR_GUARD = Railing(
    uid="CARL01AAAA", tag="RL-A-STAIR", type_ref="RAILING-INT-STAIR-GUARD", path=(
        pt(ft(21, 2), ft(5, 9.625)),
        pt(ft(35, 5.375), ft(5, 9.625)),
    ),
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
    base_elevation=ft(20), post_spacing=inch(60), post_size="2x2", rail_count=2,
    mount="fascia", assembly="RAILING_DARK_METAL",
)

STAIRS = [
    Stair(uid="CST703AAAA", tag="ST-S2A", floor_opening="FO-A-STAIR",
          from_storey="second", to_storey="attic", width=ft(3), newel_profile="6x6",
          # Enter north at the east edge, then three lower winders turn the climb west.
          # `start` is the origin the run walks from (resolve/stairs/dispatch.py), and with
          # run_reversed on x that is the well's SE corner.
          layout="right_angle_winder", turn_direction="left",
          run_direction="x", run_reversed=True, winder_count=3,
          # The turn is a tiered box (Haun), and a box has to be carried on its outside
          # edges: W-S-E1 takes the east leg, W-S-SS2 the north one. Both are the walls the
          # well was snapped to, so a ledger lands on their finished faces. Without naming
          # them the box corners post down onto bare I-joist deck, which
          # `structural.landing_post_bearing` correctly refuses.
          bearing_refs=("W-S-E1", "W-S-SS2"),
          start=pt(ft(35, 5.375), ft(5, 9.625))),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *ROOFS, *BEAMS, *FLOOR_OPENINGS,
            *FLOOR, STAIR_GUARD, *STAIRS]
