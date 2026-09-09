# haus: editable
# Catlin lighting — the ATTIC storey, split out of plan/lighting.py on 2026-08-29.
#
# The file was 1,158 lines against AGENTS.md's 500 and the guest studio added to it. Split by
# STOREY rather than by device kind, which is how a reader looks for a fitting and how
# plan/manifest.py already consumes these lists — it takes one `*_LIGHTING` tuple per storey,
# so moving one out is a manifest import change and nothing else.
#
# ** AN EDITABLE FILE CANNOT `from plan import ...` ** — the dialect forbids it — so this module
# imports only from `typehaus` and the manifest composes. Same reason plan/mep.py is an
# aggregator and is not editable.
from typehaus import (
    DeviceKind,
    ElectricalDevice,
    Mount,
    MountKind,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# ** EVERY CEILING ELEVATION IN THIS FILE ANSWERS TO ONE LINE (2026-08-29). ** The attic
# went 6:12 on a 1 1/2" rafter plate, so the roof underside above the attic finished floor is
#
#     H(x) = 1 1/2" + x/2,   mirrored past x = 18'-0"
#
# A recessed can sits IN that plane, so its mount elevation IS H at its station — there is no
# ceiling to hang below. The old plane was 5'-0" + x/3, which was 8" HIGHER at x=7' and 30"
# LOWER at the ridge, so every fitting here moved, and several had to change station as well.
#
# The rule that decides a station: 7'-0" of ceiling arrives 13'-9" from either eave, so the
# comfortable band for a can is x 13'-9"..22'-3" — 8'-6" wide, centred on the ridge. Cans
# outboard of it are not wrong, they are just low, and a 4" can at 3'-7" is a shin height,
# not a lighting position. Everything below moved INTO that band or became a surface fixture.
#
# ** NOTHING IN THIS FILE MAY BE DELETED. ** RM-A-STUDIO lost the four eave windows on the
# same pass, so its R303.1 Exception 1 lumen count (see the studio block) is doing more work
# than it was, not less. That rule held through the 2026-09-06 rework below: every uid in
# this file is still here, and the lumen count went UP.
#
# ** 2026-09-06 — THE STOREY CAME OFF ITS RECESSED CANS, AND THE REASON IS NOT THE ONE THE
# REVIEW GAVE. ** The finding was that a 6" can housing eats the ROOF assembly's whole
# 6 7/8" batt zone and punches the 5" of ccSPF that is the only air barrier R806.5 rests on.
# ** THE 6" WAS WRONG DATA. ** Lotus's LL4SR sheet — the product this house has named all
# along — reads 2" deep, "Type IC Rated - No Housing Required", "Driver Inside Connection
# Box", Air-Tight, Approved Location "Insulated Ceilings, Open Plenum, Wet". At 2" it sits
# inside the batt and never reaches the foam, and the type is corrected in
# plan/lighting_types.py. So the cans were never the code problem they were written up as.
#
# What is real, and is why they went anyway (owner's call), is the AIM: a flat trim in a
# 6:12 plane throws its cone 26.6 deg off plumb and scallops one wall of every room. Wall
# fittings on the CENTRE LINE — W-A-C1/C1B/C2/C2B, the only full-height walls this storey
# has, since both gables rake to a 1 1/2" plate at the eave — light the slope the way the
# slope wants to be lit. ** ONE CAN IS DELIBERATELY KEPT: ** ED-A-STUBATH-CAN1, over a
# shower pan, where a sconce is the wrong fitting and a 26.6 deg tilt aims INTO the room
# rather than away from it. Its own note says so.
#
# ** AND THE LUMEN FLOOR IS THE CONSTRAINT THAT SHAPED THE LAYOUT, NOT TASTE. ** RM-A-STUDIO
# is on R303.1 Exception 1 and needs 12.5 lm per square foot of point luminaires; a LightRun
# counts for nothing. The studio has exactly one mountable wall (the centre wall, ~11 ft of
# it free of the bar), which is why the scheme is five sconces plus a real pendant over the
# bar and not eight sconces. See the studio block for the arithmetic.
ATTIC_LIGHTING = [
    # A 43 ft2 nook with no wall on the way in to put a switch on, so the fixture carries
    # its own (notes: "spotlight sconce with switch on sconce"). No `controlled_by`,
    # deliberately — `integral_switch` on the type exempts it from
    # `electrical.lighting_controls`. x=14'-0" clears the window jamb by 1'-11".
    # Room reassigned through RM-A-DEN -> west loft -> RM-A-STUDIO; position, type, mount,
    # elevation and circuit are all unchanged, and its 600 lm now count toward RM-A-STUDIO's
    # R303.1 Exception 1 (see below).
    ElectricalDevice(uid="QTA0001AAA", tag="ED-A-STUDIO-SCONCE", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(0, 8.625)), type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),

    # RM-A-EAST-UNFIN, 475 sf of unfinished storage under the east rake. The three cans that
    # were one line at x=22'-0" become three up/down sconces on the centre wall's EAST face,
    # x=18'-5 3/8" — that face's finish plane (x=18'-3 3/8") plus a 4"-deep body's own half,
    # which is the offset ED-A-STUDY-SPOT already uses on the same wall. Spacing goes
    # 15'/22'/28' -> 15'/20'-6"/26' so the fourth station (ED-A-EAST-LT, in
    # plan/mep_electrical.py, which sat at the SAME point as CAN3 and lit it twice) has
    # somewhere of its own at 31'-6", clear of ED-A-EAST-SW's plate at y=32'-5 1/2".
    # ** NO LUMEN CONSEQUENCE: ** storage is not a habitable room, so R303.1 never applied
    # here — this room is the one place on the storey where the change is free.
    ElectricalDevice(uid="QTA0002AAA", tag="ED-A-EAST-SCONCE2", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 5.375), ft(26)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN", rotation=deg(90),
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTA0003AAA", tag="ED-A-EAST-SCONCE3", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 5.375), ft(15)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN", rotation=deg(90),
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTA0004AAA", tag="ED-A-EAST-SCONCE4", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 5.375), ft(20, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN", rotation=deg(90),
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),

    # RM-A-STUDY: the second of the notes' two studies. The stair sconce lights ST-S2A's
    # landing at the top of the flight.
    #
    # The study's two cans join ED-A-STUDY-SPOT on the centre wall's east face, at
    # y=4'-6" and (in plan/mep_electrical.py) y=8'-0", above SPOT's own 2'-3" station and
    # its 4'-0" mount, so the three read as one vertical family rather than two ceiling
    # holes and a spot.
    # ** RM-A-STUDY PASSES R303.1 ON GLAZING, NOT ON EXCEPTION 1, so no lumen floor binds
    # here — but by 0.4 sf (13.6 sf against 8% of 165.1 = 13.2 sf), so it is one window
    # change away from binding. ** After this swap the room still holds 2,400 lm against the
    # 2,064 Exception 1 would ask for, which is the margin that made a two-for-two swap
    # acceptable instead of a three-for-two.
    ElectricalDevice(uid="QTA0005AAA", tag="ED-A-STUDY-SCONCE2", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 5.375), ft(4, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    # On the CENTRE wall (W-A-C1, x=18'-0"), study side — x 18'-5 3/8" is that wall's
    # study-side finish face plus a sconce body's own reveal — at 2'-3" in y, 4'-0" mount,
    # thrown east across the room. There is no knee wall on this gable: W-A-E1 is a 1 1/2"
    # plate and the roof underside at x=35'-3 3/8" is only 5 3/4", too low to mount at.
    # `electrical.room_lighting` reads `room=`, not position, so this is a station move only.
    ElectricalDevice(uid="QTA0006AAA", tag="ED-A-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 5.375), ft(2, 3)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
    # Mount 3'-9": at x=27'-3 3/4" the south gable's rake gives 4'-5 5/8", and a 4'-0" mount
    # would stand 3/8" through it. This fitting lights ST-S2A's landing, drawn against the
    # flight.
    ElectricalDevice(uid="QTA0007AAA", tag="ED-A-STUDY-STAIR-SC", kind=DeviceKind.LIGHT,
                     position=pt(m(8.32505), m(0.222461)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(180),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 9))),

    # Every tag in this block is ED-A-STUDIO-*, not ED-A-WEST-*: `electrical.room_lighting`
    # matches devices to a room by NAME — `ED-{room.tag[3:]}-*` — so a fitting must carry its
    # own room's prefix or it counts toward the wrong room's total. The three prefixes
    # ED-A-STUDIO-, ED-A-STUBATH- and ED-A-POCKET- are disjoint, which is also why the bath is
    # tagged RM-A-STUBATH rather than RM-A-STUDIO-BATH (see storeys/attic_studio.py).
    #
    # ** THE LUMEN COUNT IS R303.1 EXCEPTION 1, AND IT IS WHY THIS ROOM IS LIT THE WAY IT
    # IS. ** The studio's glazing is 21.33 sf against 0.08 x 356.6 = 28.52 sf, and openable
    # is 10.67 against 14.26 — both short, and NO GLAZING IS ADDED because the south gable's
    # six-opening mirror about x=18' is not negotiable (houses/catlin/CLAUDE.md). So the room
    # takes Exception 1, and four of `_exception_1`'s gates matter here:
    #   * a luminaire must be ASSIGNED to the room — `room=` is the whole match, position is
    #     never read;
    #   * every one must state `lumens` on its LuminaireType or the verdict is UNKNOWN rather
    #     than PASS;
    #   * ** a LightRun COUNTS FOR NOTHING ** — `_room_lumens` excludes cove and tape runs by
    #     its own docstring. Point luminaires only;
    #   * 6 fc delivered, computed as lumens x 0.60 x 0.80 / area_sf — i.e. LUMENS >= 12.5 x
    #     the room's square feet, which at 356.6 sf is 4,457 lm.
    #
    # ** SIX CANS BECAME FIVE SCONCES AND A PENDANT (2026-09-06), UID FOR UID. ** CAN1..CAN5
    # keep their uids as WALL1..WALL5 and CAN6's uid carries the bar pendant, so the "nothing
    # in this file may be deleted" rule in the header holds literally. The count went
    # 6,000 lm -> 5,900 lm, 8.08 fc -> 7.95 fc: still 32% clear of the floor, which is the
    # same "survive the room growing 30%" margin the six-can scheme was specified to hold.
    #
    # ** THE LAYOUT IS DICTATED BY THERE BEING ONE WALL. ** Both gables rake to a 1 1/2"
    # plate, so the only full-height wall in a 356 sf room is the centre wall, x=18'-0",
    # west face at x=17'-8 5/8" and the device line 2" off it at 17'-6 5/8" (a 4"-deep
    # body's own half — the offset ED-A-STUDY-SPOT uses on the far side of the same wall).
    # Five at 2'-6" centres from y=2'-0" to y=12'-0", clear of ED-A-STUDIO-SW's plate at
    # y=6'-0"/46" by height.
    #
    # ** THE WALL'S NORTH END IS FREE AGAIN AND NO SIXTH SCONCE IS WANTED (2026-09-09). **
    # The bar used to take y 12'-6"..17'-1" of this wall and that is what stopped the run at
    # 12'-0"; the whole 17'-4" is bare now that the kitchenette is on W-A-BATH-S. The count
    # stands anyway: five plus the 1,800 lm pendant is 5,900 lm against a 4,457 lm floor —
    # 32% clear, the margin this scheme was specified to hold — and a sixth fitting buys
    # light where nobody stands and spends the ALWAYS_ON headroom the backup cycle is graded
    # against. ** IT IS NOT EIGHT EITHER: ** eight would not fit the wall even now with the
    # switch and the two device lines on it.
    ElectricalDevice(uid="QTA0008AAA", tag="ED-A-STUDIO-WALL1", kind=DeviceKind.LIGHT,
                     position=pt(inch(210.6), ft(2)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTA000BAAA", tag="ED-A-STUDIO-WALL2", kind=DeviceKind.LIGHT,
                     position=pt(inch(210.6), ft(4, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QP7K1NEC12", tag="ED-A-STUDIO-WALL3", kind=DeviceKind.LIGHT,
                     position=pt(inch(210.6), ft(7)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="KR49G4VP4A", tag="ED-A-STUDIO-WALL4", kind=DeviceKind.LIGHT,
                     position=pt(inch(210.6), ft(9, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="6M2C9K60B8", tag="ED-A-STUDIO-WALL5", kind=DeviceKind.LIGHT,
                     position=pt(inch(210.6), ft(12)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    # The bar pendant (owner, 2026-09-06), FOLLOWED THE BAR ONTO W-A-BATH-S AND LOST ITS DROP
    # (2026-09-09). It hung at (16'-9", 14'-10") on a 2'-6" drop under the centre wall's
    # 8'-6 3/4" ceiling. Over the kitchenette the rake gives 6'-3" at the unit's west end and
    # 7'-2" at its east, so 30" of drop would put the shade below head height.
    #
    # ** THE OUTPUT IS WHAT COULD NOT CHANGE, SO THE FITTING DID. ** This is 31% of the room's
    # code lumens: drop it, or substitute anything under 1,800 lm, and RM-A-STUDIO goes to a
    # FAIL on R303.1 (see the lumen floor in the header). Same 1,800 lm fixture, same circuit,
    # same switch — a near-flush 4" drop instead of a hung one.
    #
    # It sits over the BOWL at (12'-8 1/2", 16'-2 5/8"), not over the middle of the unit: that is
    # the tall end (`1 1/2" + x/2` = 6'-8 7/8") and the end a person actually stands at. A 4"
    # drop puts the shade bottom at ~6'-4 7/8", over a counter and not over the floor.
    ElectricalDevice(uid="7QXE07XJ69", tag="ED-A-STUDIO-BAR-PEND", kind=DeviceKind.LIGHT,
                     position=pt(inch(152.5), inch(194.625)), type_ref="ED-T-LT-PENDANT-BAR",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4))),
    # On W-A-C1B's west face at 6'-0", position unchanged: the two centre-wall segments are
    # collinear, but the wall south of y=5'-7" faces RM-A-STUDY and the studio does not start
    # until that line. A station 5" further south is a switch in the wrong room.
    ElectricalDevice(uid="QTA000CAAA", tag="ED-A-STUDIO-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7.625), ft(6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # ** THE ONE RECESSED CAN THIS STOREY KEEPS, AND THE REASON IS THE SHOWER. ** Everything
    # else here went to a wall fitting on 2026-09-06; a sconce over a 36" pan is the wrong
    # article, and the 26.6 deg tilt a flat trim takes in a 6:12 plane — the objection that
    # moved the rest — aims this one DOWN-SLOPE INTO THE ROOM, at the person, which is where
    # you want it. The fixture is legitimate here on the corrected data: Lotus's LL4SR is 2"
    # deep, Type IC, Air-Tight, Wet and Plenum rated, approved for insulated ceilings, so it
    # sits inside the ROOF assembly's 6 7/8" batt and never reaches the 5" of ccSPF that
    # carries R806.5. Retyped wet-listed because its station falls inside the bath box. Same
    # 900 lm; not part of the studio's count.
    ElectricalDevice(uid="QTA0009AAA", tag="ED-A-STUBATH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 9), ft(19, 6)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-A-STUBATH",
                     controlled_by=("ED-A-STUBATH-SW",),
                     # 7'-0" exactly: x 13'-9" is where H(x) reaches 7'-0", which is why
                     # this can did not have to move when the roof did — it was already on
                     # the one station in this bath the new plane keeps.
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(7),
                                 recessed_into_host_surface=True)),
    # The over-mirror bar (owner, 2026-09-06). On W-A-HALL-S's bath face (y=22'-1 5/8"), on
    # FX-A-STUBATH-LAV's centreline, back on the face — a 2"-deep body at y=22'-0 5/8".
    # ** IT FOLLOWED THE BASIN 2 5/8" EAST, 13'-6" -> 13'-8 5/8" (2026-09-09), ** when the
    # bare bowl became a 24" vanity (plan/fixtures.py). A 24" bar over a 24" carcass is only
    # centred if both are; off-centre it reads as a mistake from the doorway.
    # 6'-6" is the height both RM-S-VANITY bars take. ED-T-LT-MIRROR is the
    # 24" damp-rated bar already in the schedule, so this is a second instance of an
    # existing row and not a new product: 1,300 lm of front light at a basin, which the
    # ceiling can (a downlight behind your head) never gave this mirror.
    ElectricalDevice(uid="3W86JZVH61", tag="ED-A-STUBATH-MIRROR", kind=DeviceKind.LIGHT,
                     position=pt(inch(164.625), inch(264.625)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-A-STUBATH", rotation=deg(180),
                     controlled_by=("ED-A-STUBATH-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    # On W-A-BATH-S's north face — the wall you reach for on the way in. It was first put on
    # W-A-STU-W beside the lavatory, and `test_wall_mounted_devices_resolve_against_a_wall_face`
    # reported it floating 1.6" off that face; the door wall is both the better station and the
    # one whose finish face the house's standard 1" box offset lands on cleanly.
    #
    # ** IT MOVED WEST WITH THE DOOR, 14'-3" -> 13'-3" (2026-09-09). ** D-A-STUBATH's rough
    # opening is 13'-11 1/2"..15'-11 1/2" now, so 14'-3" fell INSIDE it. 13'-3" is on the
    # LATCH side (the hinge is the east jamb) with 8 1/2" to the jamb, and it is also the only
    # band left in this cavity: PR-A-BAR-VENT rises at x=12'-8 1/2", so
    # the box has to sit east of that riser and west of the jamb pack. ** NOTHING GRADES
    # EITHER OF THOSE ** — no rule tests a wall device against a rough opening or against a
    # pipe in its own bay — so both clearances are held here and by eye in the viewer.
    ElectricalDevice(uid="DD20R7F44T", tag="ED-A-STUBATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(13, 3), ft(17, 7.375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-STUBATH",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # The pocket's light: its old station (14'-0", 30'-0") fell inside FO-A-HALL, open to
    # the roof with no ceiling to recess into. Retyped can -> ED-T-LT-SHOP4, a 4' surface
    # strip, damp rated, 4,400 lm — the pocket runs x 0..10' under the west rake (ceiling
    # 1 1/2" to 5'-1 1/2"), too shallow anywhere for a recessed 4" can. At x=7'-0"
    # (3'-7 1/2" of ceiling) beside the ERV manifold, satisfying IRC M1305.1.3's light at
    # the appliance. No `recessed_into_host_surface`: this one is surface mounted.
    ElectricalDevice(uid="QTA000AAAA", tag="ED-A-POCKET-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(7), ft(30)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-UPPER", room="RM-A-POCKET",
                     controlled_by=("ED-A-POCKET-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(3, 4.5))),
    ElectricalDevice(uid="G5RDBXPZVD", tag="ED-A-POCKET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 6), ft(22, 0.625)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-POCKET", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]
