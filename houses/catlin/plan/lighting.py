# haus: editable
# Catlin lighting layout — every luminaire, LED run, 24V supply and lighting control,
# room by room, from the "Lighting Notes" section of plans/electrical_notes.md.
#
# `# haus: editable` is REQUIRED: ElectricalDevice is UI-movable, and the loader raises
# `loader.uneditable_movable_element` for one authored elsewhere. Type catalog is the
# non-editable plan/lighting_types.py (uses frozenset, forbidden here).
#
# The sixteen generic ED-T-LIGHT fixtures once one-per-room in plan/mep.py were re-typed
# in place (uid/IFC GlobalId preserved) rather than deleted; everything below is what got
# *added* around them. ED-T-LIGHT itself is retired.
#
# Conventions used throughout:
# - Rotation names the wall a fixture backs onto: deg(0) north, deg(90) west,
#   deg(180) south, deg(-90) east (local +y is the object's back).
# - `Mount(CEILING, recessed_into_host_surface=True)` with no elevation puts a can's base
#   on the ceiling plane, housing in the joist bay above. Attic cans state an elevation
#   (1 1/2" + x/2, x = distance from the nearer eave) because that ceiling is a 6:12
#   cathedral off a rafter plate. Those fittings live in plan/lighting_attic.py.
# - `Mount(CEILING, drop=<type height>)` lands a pendant's canopy on the ceiling; shade
#   bottom = ceiling minus the type's full assembly height.
# - `controlled_by` names switch(es) on the *load*. Two tags is a 3-way pair. A fixture
#   whose type carries `integral_switch` names none, by design.
# - 24V runs carry no `circuit`: their PSU does, sized at 1.25x connected tape watts and
#   checked by `electrical.light_run_psu`.
#
# Uids are QT/QR + storey letter + serial (Crockford base32, no I/L/O/U → model/ids.py).

from typehaus import (
    DeviceKind,
    ElectricalDevice,
    LightRun,
    Mount,
    MountKind,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# --- Basement -------------------------------------------------------------------------
# All of it on CKT-LT-BACKUP: electrical_notes.md line 24 puts basement and kitchen
# lighting behind the smart-relay backup subsystem, so the house keeps light in the two
# rooms you would actually need it in when the grid drops.
BASEMENT_LIGHTING = [
    # RM-B-GYM: the fan-light (ED-B-GYM-LT, re-typed in plan/mep.py) plus a 4-can grid.
    #
    # ** THE GRID MOVED OFF THE CONCRETE, y 4'-6"/13'-6" -> 6'-0"/12'-0" (2026-09-06). **
    # SL-M-DECK's band starts at y=13'-0", so CAN3 and CAN4 at y=13'-6" stood 6" inside a
    # 14 3/8" solid deck: 4 3/8" of cast cap over a 10" EPS stay-in-place form on 1/2" steel
    # furring, under the 5/8" gypsum R316.4 requires as the thermal barrier over that foam.
    # There is nothing to recess into at any depth and cutting the barrier is what the layer
    # exists to prevent. The room is 18' x 18', so y=6'-0"/12'-0" is its thirds and reads
    # better than the 4'-6"/13'-6" it replaces; both rows now sit over the wood joist bays
    # south of the band, where a 2"-deep canless fixture is a legitimate detail.
    # ** No lumen consequence: ** RM-B-GYM passes code.R303_1_light_and_ventilation on its
    # 33.3 sf of glazing, not on Exception 1's 6 fc, so moving light around costs nothing.
    ElectricalDevice(uid="QTB0001AAA", tag="ED-B-GYM-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0002AAA", tag="ED-B-GYM-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0003AAA", tag="ED-B-GYM-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(12)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0004AAA", tag="ED-B-GYM-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(12)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-B-WORKSHOP: flat panels, per the notes. A workshop wants flat even light over a
    # bench, not the scalloping a can grid gives. The L-shaped room takes one panel in
    # each leg — the west bay beside the sauna, and the north strip. The west leg narrowed
    # to 3'-8 3/16" clear when the sauna rotated (2026-09-05) and PANEL1 came in to x=2'-6";
    # the same day's shrink took the bay back out to 7'-10 3/16" (x 0'-8"..8'-6 3/16"), so
    # the panel returns to the bay's centre at x=4'-7 1/8", rounded to 4'-7".
    ElectricalDevice(uid="QTB0005AAA", tag="ED-B-WORKSHOP-PANEL1", kind=DeviceKind.LIGHT,
                     position=pt(m(0.93205), m(2.36993)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5)), rotation=deg(90)),
    ElectricalDevice(uid="QTB0006AAA", tag="ED-B-WORKSHOP-PANEL2", kind=DeviceKind.LIGHT,
                     # Dragged 2026-09-05 and kept; the metres the UI wrote back are
                     # restated as inches, rounded to the nearest inch and no further —
                     # 7'-2" x 15'-11" is where it is, not a round station pretending to be
                     # one.
                     position=pt(inch(86), inch(191)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    # ** IT MOVED ONTO THE NEW DOOR'S WALL (2026-09-07). ** It was 7" west of O-B-HALL's
    # west jamb on W-B-CW2's workshop face, 8 5/16" from what is now a wall tee at
    # N-B-BA-SE, and it was justified by a cased opening that no longer exists. The way in
    # is D-B-SHOP, so the switch goes on W-B-HALL-W's workshop face (x=163.3025", the
    # device 0.135" into it, the same seat ED-B-STAIR-SW takes on W-B-BA-E) at y=14'-2 7/16",
    # 5" north of the door's north jamb at 13'-9 7/16".
    #
    # ** THAT IS THE HINGE SIDE, AND IT IS THE ONLY SIDE. ** This house's habit is the latch
    # jamb (see ED-B-BATH-SW) so the switch is not behind the leaf. D-B-SHOP's latch jamb is
    # the SOUTH one and there are 5 5/8" of wall between it and W-B-SA-N2's face — no box,
    # no king stud, nothing fits. North it is. The leaf only covers this station if it is
    # swung the full 180 degrees flat against the wall, which is a workshop door parked, not
    # a workshop door open; at 90 degrees the switch is in the clear and it is the first
    # thing your hand finds coming through.
    #
    # ** x IS THE BOX'S CENTRE, NOT ITS FACE. ** 163.4375" is where the plate lands — the
    # face at 163.3025" plus the 0.135" seat — and authoring it as the position put the
    # whole 2" body 1" further east, 1.61" inside W-B-HALL-W's studs
    # (`test_wall_mounted_devices_resolve_against_a_wall_face`). A device footprint is a
    # plan rectangle CENTRED on `position`, so the centre is an inch back: 162.4375".
    # ED-B-STAIR-SW reads the same way against a wall on its other side.
    ElectricalDevice(uid="QTB0007AAA", tag="ED-B-WORKSHOP-SW", kind=DeviceKind.SWITCH,
                     position=pt(inch(162.4375), inch(170.4375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP", rotation=deg(270),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The under-stair storage (new 2026-09-05). ED-T-LT-SPOT-SW is the
    # house's integral-switch down-spot — the same article ED-A-STUDIO-SCONCE uses — which
    # is the right fixture for a low space you reach into rather than stand in: NEC 210.70
    # wants a lighting outlet with a switch you can reach, and `integral_switch=True` is
    # what exempts it from `electrical.lighting_controls` (lighting_types.py says so on the
    # type). `room` is RM-B-STAIR since the closet stopped being a `Room` of its own the
    # same day (storeys/basement.py ROOMS) — the fixture did not move an inch.
    #
    # On W-B-STR3's Type X face (x=10'-3 1/4") 2" proud of it, 2'-0" north of D-B-CLOSET's
    # far jamb, at 4'-6" AFF. The elevation is set by the RAKE, not by habit: the flight
    # overhead is 6'-1 5/8" up at this y, and a 9" fixture at 54" tops out 10 5/8" under it.
    ElectricalDevice(uid="JYMY6WGGP3", tag="ED-B-CLOSET-LT", kind=DeviceKind.LIGHT,
                     position=pt(inch(125.25), ft(28, 8)), type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54))),

    # RM-B-SAUNA had NO LIGHT AND NO SWITCH until 2026-09-05 — the room was drawn, rotated
    # and shrunk without one, and nothing in this engine grades a missing lighting outlet
    # (there is no NEC 210.70 check), so it stayed invisible. One fixture, in the south-west
    # corner on the south liner at 5'-0" AFF: the far end of that liner from EQ-B-SAUNA-HTR
    # (which is on the east one now) and in the
    # room's coolest corner, west of WIN-B-SAUNA's west jamb (x=12'-1"), and 3'-6" above
    # FURN-B-SAUNA-BENCH-S's 18" top so nothing shades it.
    ElectricalDevice(uid="AEYMMW1KDG", tag="ED-B-SAUNA-LT", kind=DeviceKind.LIGHT,
                     position=pt(inch(120), inch(11.5)), type_ref="ED-T-LT-SAUNA-VT",
                     circuit="CKT-LT-BACKUP", room="RM-B-SAUNA",
                     controlled_by=("ED-B-SAUNA-SW",), rotation=deg(0),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(60))),
    # The switch is OUTSIDE the hot room — a standard wall switch is rated to 40 C ambient
    # and a sauna is not, which is why the fixture above needed its own 125 C listing and
    # why this cannot simply be an integral-switch J1. It sits on W-B-CS's GYM face, 4 3/8"
    # north of D-B-SAUNA's north jamb (y=5'-1 11/16"), so it is the switch you reach for on
    # the way in. `room` is RM-B-GYM for the same reason: the device is in the gym.
    ElectricalDevice(uid="MDVC5HGQZ8", tag="ED-B-SAUNA-SW", kind=DeviceKind.SWITCH,
                     position=pt(inch(220.375), inch(66)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-FURNACE: same panels. This is the room the electrician and the plumber work in.
    ElectricalDevice(uid="QTB0008AAA", tag="ED-B-FURNACE-PANEL1", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(23)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    ElectricalDevice(uid="QTB0009AAA", tag="ED-B-FURNACE-PANEL2", kind=DeviceKind.LIGHT,
                     position=pt(m(1.52108), m(8.91654)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    # y=23'-0" is mid-room on the east wall face (W-B-STR3, framed 2x6), x=9'-5" to 9'-8 1/8"
    # — 1" proud of the face — which is where you reach it walking in from D-B-FURN.
    ElectricalDevice(uid="QTB000AAAA", tag="ED-B-FURNACE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 8.125), ft(23)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-PLAY-N is the theatre. Up/down sconces are the traditional answer (notes) and the
    # dimmer is the whole point: bright enough to cross the room, dark enough to watch
    # something.
    #
    # ** THE FOUR CANS ARE GONE (2026-09-06, owner's call), BECAUSE THIS CEILING CANNOT
    # TAKE ONE. ** ED-B-PLAY-N-CAN1..4 (uids QTB000DAAA, QTB000EAAA, QTB0010AAA, QTB0011AAA)
    # all stood inside SL-M-DECK: 4 3/8" of cast cap over a 10" EPS stay-in-place form, on
    # 1/2" steel furring, under the 5/8" gypsum IRC R316.4 requires as the thermal barrier
    # over that foam. The whole 18' x 18' room is on it. There is no cavity — plan/mep.py's
    # duct routing has said so for weeks ("NO cavity at all, so every foot of that run is
    # surface-mounted") — and the only way to recess anything is to cut the one layer that
    # is there to stop a fire reaching the foam. The right fitting count for a ceiling like
    # that is zero.
    #
    # ** SIX SCONCES, NOT TWO, AND THE ARITHMETIC IS THE REASON. ** This windowless room is
    # habitable only under R303.1 Exception 1's 6 fc average, and
    # code.R303_1_light_and_ventilation counts POINT luminaires only — LightRuns are
    # deliberately excluded from `_room_lumens` ("a cove can only add light, which makes the
    # number conservative"), so the cove below is worth exactly 0 fc to the check no matter
    # how long it is. The floor is 6 fc x 324 sf / (CU 0.60 x LLF 0.80) = 4,050 lm.
    # Two sconces alone is 1,400 lm / 2.1 fc and FAILS. Six ED-T-LT-SCONCE-UD at 700 lm is
    # 4,200 lm / 6.2 fc and passes. ** THAT IS 0.2 fc OF MARGIN AND IT IS THE WHOLE MARGIN: **
    # drop one sconce, or swap the type for anything dimmer, and this room is a FAIL. An
    # eighth-sconce scheme was offered and 6 was the call.
    #
    # Three a side on the two side walls at the room's quarter points, y = 22'-6", 27'-0",
    # 31'-6" — SCONCE1/2 keep their uids and move onto the outer east stations, so the
    # schedule reads as one six-piece run rather than a pair plus four. Nothing is on either
    # side wall to foul at 6'-6": the bookcases are on the south wall, the 98" screen and
    # the sectional are in the middle third.
    ElectricalDevice(uid="QTB000BAAA", tag="ED-B-PLAY-N-SCONCE1", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 10), ft(22, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(-90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTB000CAAA", tag="ED-B-PLAY-N-SCONCE2", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 10), ft(31, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(-90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="7VRS9XJKG7", tag="ED-B-PLAY-N-SCONCE3", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 10), ft(27)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(-90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    # West wall. ** THE TWO DEVICE LINES ARE NOT MIRRORED, AND THAT IS CORRECT: ** the east
    # side is W-B-E2, a 16.17" foundation wall, and the west is W-B-CN/CN2 at 12", so a
    # station mirrored about x=27'-0" would stand 6" off the west face. x=18'-8" puts a
    # 4"-deep body's back ON that face (216" axis + 6" half-thickness + 2"), which is what
    # `test_wall_mounted_devices_resolve_against_a_wall_face` grades — the resolved body,
    # never the authored point. The two banks line up in ELEVATION and in y, which is what
    # reads in the room.
    ElectricalDevice(uid="NYEVZE2RN5", tag="ED-B-PLAY-N-SCONCE4", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 8), ft(22, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="4XZRS7P3VR", tag="ED-B-PLAY-N-SCONCE5", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 8), ft(27)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="JBZ1PYPYF0", tag="ED-B-PLAY-N-SCONCE6", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 8), ft(31, 6)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    # ** THE AMBIENT COVE WAS DESIGNED, PRICED AND THEN WITHDRAWN (2026-09-06), AND THE
    # REASON IS THE BATTERY, NOT THE CEILING. ** Two surface COB channels up the side walls
    # at 7'-4" were the ambient tier the cans used to be — nothing recessed, nothing through
    # the R316.4 board, washing a soffit that cannot be cut into. 2 x 15'-6" at 3 W/ft is
    # 93 W and wants an ED-T-LT-PSU-200.
    #
    # CKT-LT-BACKUP cannot carry it. This is the ALWAYS_ON tier on a 14.3 kWh battery, and
    # per plan/lighting_types.py a PSU sums at its supply's RATING, not the tape's draw —
    # the same deliberate overstatement that already took battery-only autonomy from 46.3 h
    # to 41.3 h for the kitchen's ED-M-KITCH-LT-PSU. A second 200 VA driver takes it to
    # 37.5 h and flips `cycle_48h.sustains_always_on` to False: the house's headline
    # two-day answer, bought with a decorative cove. The tier has about 52 VA of headroom
    # and every honest version of this cove is over it — a 60 VA driver still lands at
    # 39.8 h, and a 120 V integral-driver run bills its real 93 W and lands at 39.0 h.
    # `test_backup_calc.py` is the assertion; the basement has exactly one lighting circuit
    # and it is this one, so there is nowhere else to put it without a new breaker.
    #
    # ** IF IT IS WANTED, IT IS A CIRCUIT DECISION, NOT A LIGHTING ONE: ** give the cove its
    # own non-backup breaker and its own switch, and it costs the backup tier nothing. It
    # was never worth anything to code.R303_1_light_and_ventilation either way — a LightRun
    # counts 0 lm — so nothing but the room's feel is riding on it.
    ElectricalDevice(uid="QTB000FAAA", tag="ED-B-PLAY-N-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 7), ft(20)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-STAIR: the railing light the notes ask for. A 24V tape at 34" on the stair's
    # west wall, under the handrail — it lights the treads without a fixture in anyone's
    # eyeline coming up. 3-way with the main-storey stair switch, because a stair light
    # that can only be switched from the bottom is a stair light nobody uses.
    #
    # ** A KNOWN LIMIT, MADE VISIBLE BY THE 2026-09-05 CLOSET AND NOT CAUSED BY IT. **
    # `LightRun` carries ONE `Mount` elevation for its whole path, and 34" is measured off
    # the SLAB, not off the raking nosing line — so this tape does not climb with the flight
    # it lights. From y=25'-8" to y=31'-0" it lies under the arriving flight, which is the
    # under-stair storage; north of that it is under the landing deck. Nothing
    # grades a light run's room, so no check says this. Fixing it needs a raked run, which
    # the schema does not have (see `serves_stair` on Railing for the same problem solved
    # for guards).
    LightRun(uid="QRB0001AAA", tag="LR-B-STAIR-RAIL", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(10, 4.375), ft(25, 8)), pt(ft(10, 4.375), ft(34, 10))),
             room="RM-B-STAIR", psu_ref="ED-B-STAIR-LT-PSU",
             controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
             mount=Mount(kind=MountKind.WALL, elevation=inch(34))),
    # The AC/DC supply in a ceiling box, at the head of the run it feeds (notes: "Box in
    # ceiling for AC/DC power supply"). 9'-5" of tape at 3 W/ft is 28 W; x1.25 = 35 W, so
    # the 60 W supply is the catalog size above it. **It moved to the lower landing's
    # ceiling on 2026-09-05**: (11', 26') is inside the under-stair storage, and a stair
    # light's supply does not belong behind the stored goods.
    ElectricalDevice(uid="QTB000GAAA", tag="ED-B-STAIR-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(15, 6), ft(33)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.CEILING)),
    # The 3-way at the stair foot. It hung on W-B-STR3's east face at (10'-4 3/8", 26'-6")
    # until 2026-09-05, which the under-stair closet then enclosed — so it moved across the
    # well onto **W-B-WELL's east face** (x=14'-0 15/16") at the same height, level with the
    # bathroom's north wall. That is the hall side, which is where you reach for it.
    # y=25'-10" and not 25'-6": at the bathroom's north wall line the box straddles
    # W-B-BA-E's own end — that wall's gypsum runs to x=14'-2 1/16", four inches past this
    # face — and reads as 0.8" buried. Four inches north is clear of it and still the first
    # thing your hand finds at the stair foot.
    ElectricalDevice(uid="QTB000HAAA", tag="ED-B-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(inch(169.9375), ft(25, 10)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # The can lights the HALL — the slot between W-B-BA-E and W-B-CN2 — centred in it and
    # level with D-B-BATH's leaf. The slot was 3'-2 5/8" and the can sat at x=15'-9";
    # sliding W-B-BA-E 1 5/16" west onto the well partition's line (2026-09-05) made it
    # **3'-3 15/16", x 14'-2 1/16"..17'-6"**, whose centre is x=15'-10". x=14' would still
    # put the can inside W-B-BA-E's studs. It no longer runs "south to O-B-HALL": since
    # 2026-09-07 the slot runs to the sauna wall and this is the first of four cans on it.
    ElectricalDevice(uid="QTB000JAAA", tag="ED-B-STAIR-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(23, 6)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** THREE MORE CANS DOWN THE EXTENDED HALL (2026-09-07). ** The hall is 15'-6" of
    # windowless circulation now and CAN1 alone lit its north quarter. Same type, same
    # circuit, same two-way pair, on the same x=190" centre line — the new wall's east face
    # lands at 170.0725" and W-B-CN2's west face at 210", so the centre did not move when
    # the slot grew. (South of y=13'-10" the east side is W-B-CS3's face at 212.615" and the
    # true centre is 191 5/16"; holding 190" keeps the ladder straight, which is worth more
    # than 1 5/16" on a 3" aperture.)
    #
    # ** 27 VA, AND THAT IS THE WHOLE BUDGET QUESTION. ** CKT-LT-BACKUP is the ALWAYS_ON
    # tier on a 14.3 kWh battery with about 52 VA of headroom — the number the withdrawn
    # play-room cove was measured against forty lines up. Three 9 VA cans fit inside it with
    # 25 VA to spare and `cycle_48h.sustains_always_on` holds; `test_backup_calc.py` is the
    # assertion, and a fourth can is not free.
    #
    # ** THE MIDDLE ONE IS AT 15'-0", NOT THE 15'-6" A 4'-0" LADDER WANTS. ** PR-B-HW-SAUNA
    # crosses the hall east-west at y=15'-6", 2 9/16" below the finished ceiling, and a
    # recessed can wants that plane for its trim. 15'-0" is 6" clear of the pipe and leaves
    # 4'-0"/4'-6"/3'-6" spacings, which nobody standing in a 3'-4" hall can read.
    #
    # Recessing is legitimate here: SL-M-DECK is the x 18'-36' half, so this hall's ceiling
    # is FS-M-WEST's joist bays and there is depth for a 5" housing.
    ElectricalDevice(uid="J2YZPDZ9MP", tag="ED-B-STAIR-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(19, 6)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="780QDKJASC", tag="ED-B-STAIR-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(15)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="K96T60Y9RX", tag="ED-B-STAIR-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(11, 6)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-B-BATH (2026-07-30; rotated 2026-09-05). On CKT-LT-BACKUP, deliberately, so this
    # room and the stair foot stay lit together on backup power. Can on the room's centre
    # line between the vanity and the water closet, clear of REG-B-EXH1 over the WC at
    # 24'-1 5/8"; switch on the latch-jamb side (door swings out, so it isn't behind the
    # leaf).
    ElectricalDevice(uid="QTB000KAAA", tag="ED-B-BATH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(12), ft(21, 6)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH",
                     controlled_by=("ED-B-BATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # x follows W-B-BA-E: the wall slid 1 5/16" west on 2026-09-05 and the switch went with
    # it, back onto the new finish face at 13'-7 5/16". Left where it was it stood 1 5/16"
    # inside the studs — `test_wall_mounted_devices_resolve_against_a_wall_face` caught it,
    # and no `haus check` rule does.
    ElectricalDevice(uid="QTB000LAAA", tag="ED-B-BATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(inch(162.3125), ft(24, 2)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH", rotation=deg(270),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]

# --- Main storey ----------------------------------------------------------------------
MAIN_LIGHTING = [
    # RM-M-LIVING, the lounge end: the shadow-gap coves the notes lead with. Two runs, one
    # down each side, mounted at the 9' ceiling plane — installed with the drywall and
    # fixed to the board rather than to the framing, so the reveal stays a sound break
    # rather than becoming a rigid path between the room and the joists.
    LightRun(uid="QRM0001AAA", tag="LR-M-LIVING-W", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(18, 6), ft(1)), pt(ft(18, 6), ft(21, 6))),
             room="RM-M-LIVING", psu_ref="ED-M-LIVING-LT-PSU",
             controlled_by=("ED-M-LIVING-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    LightRun(uid="QRM0002AAA", tag="LR-M-LIVING-E", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(35, 6), ft(1)), pt(ft(35, 6), ft(21, 6))),
             room="RM-M-LIVING", psu_ref="ED-M-LIVING-LT-PSU",
             controlled_by=("ED-M-LIVING-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # 41' of tape at 3 W/ft = 123 W; x1.25 = 154 W, so the 200 W supply. It sits in the
    # ceiling just north of both runs, where the kitchen soffit gives it a service hatch.
    ElectricalDevice(uid="QTM0001AAA", tag="ED-M-LIVING-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(19), ft(22, 6)), type_ref="ED-T-LT-PSU-200",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.CEILING)),
    # The lounge can grid. ED-M-LIVING-LT (re-typed, plan/mep.py) is the fourth corner and
    # stays on the backup circuit — one light in the main room that survives an outage.
    ElectricalDevice(uid="QTM0002AAA", tag="ED-M-LIVING-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0003AAA", tag="ED-M-LIVING-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0004AAA", tag="ED-M-LIVING-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The daylight set: mark A1, same 4" can but 4000K, on its own switch leg so the lounge
    # can run warm evenings / cool when worked in. Interleaved as a diamond inside the warm
    # 2x2, symmetric about (27', 7'), so either set alone still lights the room evenly.
    # Same circuit as the warm cans — only the switch leg needs to be separate.
    ElectricalDevice(uid="QTM0019AAA", tag="ED-M-LIVING-CAND1", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(4)), type_ref="ED-T-LT-CAN4-4000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM001AAAA", tag="ED-M-LIVING-CAND2", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(10)), type_ref="ED-T-LT-CAN4-4000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM001BAAA", tag="ED-M-LIVING-CAND3", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(7)), type_ref="ED-T-LT-CAN4-4000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM001CAAA", tag="ED-M-LIVING-CAND4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(7)), type_ref="ED-T-LT-CAN4-4000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Second gang beside ED-M-LIVING-SW (plan/mep.py, at 26'-0"), 4" over on the same wall.
    # A dimmer rather than the warm set's plain switch: the daylight cans are the ones you
    # turn down, since they are the set that is on when you do not want the full 4800 lm.
    ElectricalDevice(uid="QTM001DAAA", tag="ED-M-LIVING-SW-DAY", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(12, 4)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),

    # The dining fixture, centred on FURN-M-DINING. A 3'-6" assembly off a 9' ceiling puts
    # the shade bottom at 5'-6" — about 3' over a 30" table, which is the height that lights
    # the table without blocking the person across it.
    ElectricalDevice(uid="QTM0005AAA", tag="ED-M-DINING-PEND", kind=DeviceKind.LIGHT,
                     position=pt(ft(26, 11), ft(17, 4)), type_ref="ED-T-LT-PENDANT",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-DINING-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(3, 6))),
    ElectricalDevice(uid="QTM0006AAA", tag="ED-M-DINING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(16)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The kitchen end of the same room, on the backup circuit with the basement
    # (electrical_notes.md line 24).
    #
    # ** THE TWO 2x4 PANELS ARE GONE, 2026-09-06, AND FOUR CANS REPLACE THEM. ** They were
    # 4000 K / CRI 80 / 4800 lm commercial troffers surface-mounted 1.5" below a
    # residential ceiling — the only 4000 K/CRI 80 fixtures on this floor, in the same
    # open-plan sightline as 3000 K/CRI 90 cans, a CRI 95 under-cabinet tape and the dining
    # pendant. ** NOTHING GRADES COLOUR TEMPERATURE: ** there is no CCT-consistency check,
    # so the schedule would have carried two colours of white forever.
    #
    # The comment this replaces argued "panels over the working floor, cans over the
    # counters — a can right above where you stand puts your own shadow on the cutting
    # board". That reasoning is about standing AT A COUNTER, and it is why CAN1-CAN4 sit
    # 8-9 5/8" off the counter fronts rather than over them. It says nothing about the open
    # floor in the middle of the room, where there is no work surface to shadow.
    #
    # ~9,600 lm of panel down to 3,600 lm of can, and the whole room on one colour
    # temperature.
    #
    # ** NOTHING GRADES A CAN'S POSITION EITHER, SO THE LAYOUT WAS MEASURED. ** A 2x2 on the
    # panels' own x centres (23'/31') straddling their y=30' line was the first draft and
    # fails twice against the resolved model: (31', 28'-6") lands 5/8" off
    # FURN-M-KIT-PENINSULA's back edge at y=28'-5 3/8" — a can over the head of whoever is
    # standing at that counter, which is the very shadow case the paragraph above describes
    # — and (31', 31'-6") sits 1'-4 1/2" from ED-M-KITCH-CAN2. So instead:
    #
    # CAN6/7/8 are a **row of three at y=30'-6"** on a 4'-0" pitch, mid-depth in the galley
    # floor: 2'-0" north of the peninsula's back edge and 2'-11" south of the north counter
    # face, with CAN1-CAN4 already washing both of those. CAN5 takes the west walkway
    # between FURN-M-KIT-PANTRYC and the peninsula's west end, which the 2x2 also covered
    # and a bare row of three would not. Measured against the resolved footprints: every one
    # of the four is >= 1'-11 3/4" from any cabinet or appliance and >= 2'-4" from any
    # existing can.
    ElectricalDevice(uid="7WE319EHB5", tag="ED-M-KITCH-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(23), ft(27)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="Z256WYTAN6", tag="ED-M-KITCH-CAN6", kind=DeviceKind.LIGHT,
                     position=pt(ft(23), ft(30, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="T5YZRQ2P6K", tag="ED-M-KITCH-CAN7", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(30, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QXW0T5DB2J", tag="ED-M-KITCH-CAN8", kind=DeviceKind.LIGHT,
                     position=pt(ft(31), ft(30, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # x=25'-2 1/2" follows FURN-M-KIT-E1's centre — the north counter run's west end, at the
    # pantry wall. It is NOT retagged into RM-M-PANTRY: its `controlled_by` is ED-M-KITCH-SW
    # and the kitchen needs the can. y stays on CAN2's line, 8" south of the counter front.
    ElectricalDevice(uid="QTM0009AAA", tag="ED-M-KITCH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(25, 2.5), m(9.9884)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000AAAA", tag="ED-M-KITCH-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(m(9.29111), m(9.99009)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # CAN3 over FURN-M-KIT-N4 (centre y=34'-2 3/8") and CAN4 over FURN-M-KIT-N3 (centre
    # y=29'-5 3/8"), each over the cabinet actually underneath. x=34'-3" is 9 5/8" in from
    # the counter front.
    ElectricalDevice(uid="QTM000BAAA", tag="ED-M-KITCH-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 3), ft(34, 2.375)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000CAAA", tag="ED-M-KITCH-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(m(10.1775), m(9.33823)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** MOVED OFF W-M-C5 (2026-09-06): THE KITCHEN'S MAIN SWITCH WAS BEHIND A CABINET. **
    # At y=26'-6" it sat 13 1/8" inside FURN-M-KIT-PANTRYC, the 24" x 96" pantry carcass —
    # the switch for every fixture in this list, unreachable without emptying a cupboard.
    # ** AND NO STATION ON W-M-C5 FIXES IT. ** That wall runs y 25'-10"..33'-1", 87" of it,
    # and 84 5/8" is behind PANTRYC or the fridge/freezer columns; the 2 3/8" left at the
    # north end is a corner stud pack. The comment below ED-M-KITCH-SW-UC already said this
    # and called it "a pre-existing condition this commit neither causes nor fixes" — this
    # commit fixes it.
    #
    # W-M-C3's east face instead, in the 11" of free wall between D-M-STUDY's jamb pack
    # (which reaches y=256.97", measured off the resolved `framing_bumper`, not the 30"
    # leaf) and N-M-C2 at y=268". y=21'-10 1/2" centres the 4" body at 3 1/2" clear of
    # each — the wall you pass walking into the kitchen through the BM-M-HALL beam line,
    # which is open from y 21'-8" to 25'-10" and is why the kitchen has no door-side wall
    # of its own. ED-M-KITCH-SW-UC stays at the pantry corner: that one dims the counter
    # tape you stand at, this one is the room's general lighting you reach for on the way in.
    #
    # ** ED-M-LIVING-RC7 IS THE SAME DEFECT ON THIS WALL AND IS NOT FIXED HERE. ** It sits
    # at y=21'-1 1/4", inside D-M-STUDY's jamb pack (y 223.03"..256.97"), at 16" AFF. Found
    # while measuring this move; a receptacle is a spacing decision (electrical.py's
    # NEC 210.52 run) and not this switch's to make. See plans/TODO.md.
    ElectricalDevice(uid="QTM000DAAA", tag="ED-M-KITCH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(21, 10.5)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # --- kitchen under-cabinet task light -----------------------------------------------
    # Ceiling cans alone over a counter you stand in front of light your own shadow onto
    # the work surface, which is the arrangement this file's own kitchen header warns about.
    #
    # ** ED-T-LT-STRIP24 IS THE WRONG TAPE FOR THIS AND IS DELIBERATELY NOT USED. ** The
    # cove tape is 3 W/ft, near 120 lm/ft; a work counter wants 350-500 lm/ft. These run on
    # ED-T-LT-STRIP24-TASK (mark U, 5 W/ft, ~400 lm/ft) — same 24V family, different
    # product. See its note in plan/lighting_types.py.
    #
    # ** FOUR RUNS, NOT ONE, AND THE PATHS ARE 1" BEHIND THE UPPERS' FRONT EDGE. ** Four
    # because the north pair is broken by WIN-M-KITCH over the sink and the east pair by the
    # range and APPL-M-HOOD. Front-mounted because front-mounted tape lights the WORK
    # SURFACE — back-mounted tape lights the backsplash and puts your own shadow on the
    # board. (On a 13" upper over a 24" base the two land within an inch of each other, so
    # the reason has to be the thing written down, not the coordinate.) The light rail and
    # the deep frosted diffuser are on the type, and both are spec: a bare diode line is
    # visible from a seated position at the peninsula and reflects as a row of dots in a
    # polished counter.
    # Endpoints are literal base joints: WE1 runs the full W-of-window bay 24'-7"..27'-10"
    # and WE2 the E-of-window bay 30'-10"..33'-4" — see plan/placeables.py's kitchen header.
    LightRun(uid="63DMV159RN", tag="LR-M-KIT-N-WE1", type_ref="ED-T-LT-STRIP24-TASK",
             path=(pt(ft(24, 7), ft(34, 5.375)), pt(ft(27, 10), ft(34, 5.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    LightRun(uid="0ZE5GQV7CQ", tag="LR-M-KIT-N-WE2", type_ref="ED-T-LT-STRIP24-TASK",
             path=(pt(ft(30, 10), ft(34, 5.375)), pt(ft(33, 4), ft(34, 5.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    # Runs south to 27'-2 3/8" with FURN-M-KIT-WN4, the 15" box filling the gap the mixer
    # garage left: the tape runs the whole continuous 13"-deep upper face from the garage's
    # north side to the range, the whole of the peninsula's east counter and FURN-M-KIT-N3's
    # top.
    LightRun(uid="N9243MWVM0", tag="LR-M-KIT-E-WN3", type_ref="ED-T-LT-STRIP24-TASK",
             path=(pt(ft(34, 5.375), ft(27, 2.375)), pt(ft(34, 5.375), ft(30, 5.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    # 66", not 54": this one is under the REHUNG FURN-M-KIT-WN1. At 54" it would be a strip
    # of tape across WIN-M-KIT-E's glass.
    LightRun(uid="D1YNDEW7NK", tag="LR-M-KIT-E-WN1", type_ref="ED-T-LT-STRIP24-TASK",
             path=(pt(ft(34, 5.375), ft(32, 11.375)), pt(ft(34, 5.375), ft(35, 4.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(66))),
    # 11'-5" of tape at 5 W/ft = 57.1 W; x1.25 = 71.3 W — already past ED-T-LT-PSU-60's
    # 60 VA, which is why the 200 W supply is specified. It loads to ~36%. NOT a share of
    # ED-M-LIVING-LT-PSU: that one is on CKT-LT-MAIN, and electrical_notes.md line 24 puts
    # kitchen lighting behind the backup relay.
    ElectricalDevice(uid="7VSVT7B8ZS", tag="ED-M-KITCH-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(32), ft(33)), type_ref="ED-T-LT-PSU-200",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.CEILING)),
    # ** NOT ON W-M-C5, and that is worth stating. ** That wall's east face has no free wall
    # left on it at all: FURN-M-KIT-PANTRYC covers y 25'-4 7/8"..27'-4 7/8" and the cold
    # pair covers 27'-4 7/8"..32'-10 5/8" (both extents RE-MEASURED 2026-09-06 — the
    # figures here were 4" south of the model, stale since PANTRYC last moved), leaving
    # 2 3/8" of corner stud pack out of 87". This one goes on W-M-PAN-E's EAST face at the
    # pantry's outside corner, which is the wall you actually pass on the way into the
    # kitchen from the west. ED-M-KITCH-SW was behind PANTRYC on the strength of that same
    # dead wall and has now MOVED to W-M-C3 — see its own note above; the sentence that
    # used to stand here calling it "a pre-existing condition this commit neither causes
    # nor fixes" is spent.
    ElectricalDevice(uid="EX3ZQQPM9K", tag="ED-M-KITCH-SW-UC", kind=DeviceKind.SWITCH,
                     position=pt(ft(24, 7.375), ft(33, 1)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # --- RM-M-PANTRY's vertical slot -----------------------------------------------------
    # A POINT DEVICE, NOT A LightRun — see ED-T-LT-SLOT72's note in plan/lighting_types.py
    # for why a vertical run silently bills zero feet and sizes its supply at 0 W.
    # 1'-6" to 7'-6" on the pantry's west wall (W-M-C5B's east face), so the slot lights the
    # DEPTH behind whatever is on each shelf; overhead alone is the worst option in a
    # reach-in, because every shelf below the top sits in its own shadow.
    #
    # 120V with an integral driver, deliberately: there is no cavity here for a 24V PSU.
    # Load and switch share CKT-LT-BACKUP, so electrical.lighting_controls draws no NEC
    # 210.7 finding.
    #
    # ** Refinement worth taking at rough-in, not modelled: ** a door-jamb switch instead of
    # (or wired parallel to) the wall switch, so opening the bypass lights the pantry — the
    # standard for a closet. Optionally a second layer of shelf-edge strips at the front
    # underside of each shelf, facing back. 3000-4000K either way.
    ElectricalDevice(uid="2A635YS6VW", tag="ED-M-PANTRY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 5.125), ft(33, 4.375)), type_ref="ED-T-LT-SLOT72",
                     circuit="CKT-LT-BACKUP", room="RM-M-PANTRY", rotation=deg(90),
                     controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(1, 6))),
    # Switched from the KITCHEN side, the way a closet is. The only wall left on that face
    # is the 8 7/8" east of D-M-PANTRY's rough opening.
    ElectricalDevice(uid="1M4ZM8DRWH", tag="ED-M-PANTRY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(24, 2), ft(32, 9.625)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-M-BED: a four-can grid (ED-M-BED-LT is the SW corner of it, plan/mep.py).
    ElectricalDevice(uid="QTM000EAAA", tag="ED-M-BED-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000FAAA", tag="ED-M-BED-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000GAAA", tag="ED-M-BED-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-M-STUDY has no exterior wall, so the notes' "sconce to the side of the window"
    # applies to the two studies that do (RM-S-STUDY2, RM-A-STUDY). This one gets a down
    # spot for the desk, over a general can.
    #
    # ** ON THE EAST WALL, NOT THE NORTH. ** A spot on the north wall (behind
    # FURN-M-STUDY-DESK, which faces south from the south wall) would be a BACKLIGHT — a
    # silhouette on camera — bright against WP-M-STUDY-FELT, the backdrop the camera sees.
    # The south wall is out too: a 20"-deep desk puts a monitor in front of it.
    #
    # So: the EAST wall's north sliver, the 12 15/16" of W-M-C3 north of D-M-STUDY's RO
    # (y 21'-0 11/16"..22'-1 5/8"). x is 2" — half this type's 4" depth — off that wall's
    # resolved study face at 17'-8 5/8", per the face-position convention in
    # plan/electrical.py. `rotation=deg(-90)` backs it onto the east wall and aims it west.
    # ED-M-STUDY-SW is on the same sliver at 48", so the two are vertically clear.
    #
    # The booth is a facing pair — FURN-M-STUDY-BENCH along the north wall,
    # FURN-M-STUDY-DESK in the SW corner — so the occupant sits with their back to the
    # north wall and faces south, and the camera on the desk looks north at them. From
    # (17'-6 5/8", 21'-5") at 6'-0" this is a SIDE key about 3'-0" off their left cheek,
    # aimed across the bench: off the backdrop, not behind the subject, not competing with a
    # monitor. It is above the bench's east end (seat 18") with 4'-6" of clear, so nothing
    # standing on the bench reaches it.
    #
    # REG-M-SUP4 is in the CEILING three feet over it at (17'-2", 20'-8") — 4 5/8" west and
    # 9" south of directly above, the 9" being a joist line — rather than in this sliver,
    # which already holds this fitting and a switch. The room's stale-air pickup is LOW, on
    # the south wall's east end: the east wall below this sconce is D-M-STUDY's rough
    # opening down to 21'-0 11/16" and FURN-M-STUDY-BENCH from there to the corner. See
    # plan/mep_registers.py for both.
    #
    # ** NEITHER THIS NOR ED-M-STUDY-LT MAY BE DELETED. ** RM-M-STUDY is windowless and
    # passes `code.R303_1_light_and_ventilation` only on Exception 1's electric-light
    # substitute — 1500 lm from the point luminaires carrying room="RM-M-STUDY" (LightRun
    # coves are excluded by `_room_lumens`). Moving one within the room is safe; removing
    # one is a FAIL.
    ElectricalDevice(uid="QTM000HAAA", tag="ED-M-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(ft(17, 6.625), ft(21, 5)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-MAIN", room="RM-M-STUDY", rotation=deg(-90),
                     controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),

    # RM-M-BATH1: wet-rated can plus a mirror light over the lavatory, which backs onto
    # the room's north wall (FX-M-BATH1-LAV, plan/fixtures.py).
    ElectricalDevice(uid="QTM000JAAA", tag="ED-M-BATH1-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(m(0.959081), m(7.35676)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1",
                     controlled_by=("ED-M-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Matches FX-M-BATH1-LAV's position, and tracks W-M-HS1's face: RM-M-BATH2 on the wall's
    # far side retyped it to a 6 3/4" wet wall for its water closet, so BATH1's face is at
    # 22'-7 3/8", not 22'-6 3/8" — the fitting has to follow or it resolves inside the studs.
    # Nothing about BATH1 changed; it is the other room's wall.
    ElectricalDevice(uid="QTM000KAAA", tag="ED-M-BATH1-MIRROR", kind=DeviceKind.LIGHT,
                     position=pt(m(1.36284), ft(22, 8.385)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1", rotation=deg(-180),
                     controlled_by=("ED-M-BATH1-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTM000MAAA", tag="ED-M-BATH1-SW", kind=DeviceKind.SWITCH,
                     # On the west wall, clear of the toilet/lavatory footprints on the
                     # south wall.
                     position=pt(ft(5, 7.625), ft(25, 8.375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-M-BATH2: two wet cans (one over the future tub/shower end) and a mirror light on
    # the west wall. The radiant-floor stat ED-M-BATH2-FH-STAT is a separate control and
    # does not switch any of this.
    ElectricalDevice(uid="QTM000NAAA", tag="ED-M-BATH2-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(2, 6), ft(16)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     controlled_by=("ED-M-BATH2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000PAAA", tag="ED-M-BATH2-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(5, 6), ft(19, 6)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     controlled_by=("ED-M-BATH2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000QAAA", tag="ED-M-BATH2-MIRROR", kind=DeviceKind.LIGHT,
                     position=pt(inch(7.635), inch(173.375)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2", rotation=deg(90),
                     controlled_by=("ED-M-BATH2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTM000RAAA", tag="ED-M-BATH2-SW", kind=DeviceKind.SWITCH,
                     position=pt(m(0.500866), m(4.04922)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2", rotation=deg(0),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-M-LAUNDRY / RM-M-CLOSET / RM-M-MUDROOM: 3" cans. Small rooms want a small
    # aperture — a 4" can in a 22 ft2 laundry is a headlamp.
    # The laundry's can sits over the machines; the closet's is centred on the corridor.
    ElectricalDevice(uid="QTM000SAAA", tag="ED-M-LAUNDRY-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(10, 8), ft(20, 2)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY",
                     controlled_by=("ED-M-LAUNDRY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** BOTH THESE SWITCHES FOLLOW W-M-BA2E's FACE, AND IT MOVED (2026-09-09). ** The bath2
    # east line went 2" east and the W-M-BA2E2 jog came off, so ONE finished face at
    # x=101 3/8" now serves both — 99 3/8" and 106 3/4" before. A wall device's footprint is
    # CENTRED on its position, so a 2"-deep switch sits at 102 3/8", half its body off the
    # face. Left where they were, one buried 2 13/16" into the studs and the other floated
    # 5 3/8" into the room, and `haus check` graded neither.
    ElectricalDevice(uid="QTM000TAAA", tag="ED-M-LAUNDRY-SW", kind=DeviceKind.SWITCH,
                     position=pt(inch(102.385), ft(21, 2)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # ** A SECOND CAN, AND THE FIRST ONE MOVES, 2026-09-06. ** 48.4 sf, 8'-11 1/2" clear,
    # on ONE 650 lm CAN3 at mid-span: 6.4 fc at the engine's own CU 0.60 x LLF 0.80,
    # for a room whose whole job is telling navy from black. ** NOTHING EVER LOOKED AT IT: **
    # `electrical.room_lighting` only grades _HABITABLE occupancies and RM-M-CLOSET is
    # Occupancy.STORAGE.
    #
    # FURN-M-CLOSET-SHELF is a 96" rod centred at x=13'-0", spanning x 9'-0"..17'-0". One
    # can mid-span lights the rod's centre and leaves both ends dim, so the pair sits on
    # the rod's quarter points (11'-0" and 15'-0"). y stays at 15'-8", which the resolved
    # footprint puts 8 5/8" clear in front of the shelf's own front edge (y=16'-4 5/8") —
    # lighting the hanging clothes' FACES rather than the top of the shelf. Measure that
    # off the shelf, not off `Room.clear_face`, which is inset from the wall AXIS and is
    # not the finish face. 1,300 lm over 48.4 sf = 12.9 fc.
    #
    # ** MEP CHECKED, AND THE MOVE WEST IS THE TIGHT HALF OF IT. ** Four services cross this
    # ceiling: PR-B-HW-SUITE-RUN, PR-B-CW-SUITE-RUN, PR-M-S-SUITE-DRAIN-RUN and
    # DU-M-ERV-R-BED1-RUN. Measured off the resolved plan solids, CAN1 at x=11'-0" is
    # 7 5/16" from the hot run against 11 5/8" at its old x=13'-0" — the move HALVED that
    # clearance, and it is still ~5" of clear round a 4" housing. CAN2 at x=15'-0" is
    # 1'-5 1/4" clear of the nearest. ** Nothing grades a can against a pipe **, so if
    # either can ever moves west again, re-measure rather than assume.
    ElectricalDevice(uid="QTM000VAAA", tag="ED-M-CLOSET-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(11), ft(15, 8)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="1N2XSTDANE", tag="ED-M-CLOSET-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(15), ft(15, 8)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000WAAA", tag="ED-M-CLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(inch(102.385), ft(16, 10)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # room=RM-M-MUD-CLOSET: the closet conversion framed a room around this ceiling point,
    # and the light's `room` has to name it or `integrity.placeable_room_mismatch` fires.
    # Nothing moves — a label catching up with a wall.
    ElectricalDevice(uid="QTM000XAAA", tag="ED-M-STORAGE-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(29)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-MUD-CLOSET",
                     controlled_by=("ED-M-STORAGE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # room=RM-M-MECH: its ceiling position lands inside the framed shaft closet carved out
    # of the mudroom's north end, not the mudroom itself.
    ElectricalDevice(uid="QTM000YAAA", tag="ED-M-STORAGE-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(3), ft(34, 6)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-MECH",
                     controlled_by=("ED-M-STORAGE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000ZAAA", tag="ED-M-STORAGE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 8.125), ft(27)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-M-HALL: three 3" cans down the run, on a 3-way pair — a 14' hall switched from
    # one end only is the classic thing to get wrong.
    ElectricalDevice(uid="QTM0010AAA", tag="ED-M-HALL-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(6, 6), ft(24)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-HALL-SW", "ED-M-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0011AAA", tag="ED-M-HALL-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(11), ft(24)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-HALL-SW", "ED-M-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0012AAA", tag="ED-M-HALL-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(15, 6), ft(24)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-HALL-SW", "ED-M-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # West end of the run, on W-M-BAE's hall face just south of D-M-BATH1 (door spans
    # y 23'-4"..25'-4", the only piece of wall a plate fits on). Moved here 2026-07-31 from
    # x=4'-5", which was 1'-7" inside RM-M-BATH1 (wall at x=6'-0") — `integrity.
    # placeable_room_mismatch` had been reporting it. rotation 90 faces east into the hall.
    # y +1" on 2026-08-29 for the same reason as ED-M-BATH1-MIRROR above: W-M-HS2 retyped to
    # the 6 3/4" wet wall with W-M-HS1, so the hall's south face came 1" north and the plate's
    # bottom 3/8" was left standing in it. At 22'-10" the plate runs y 22'-8"..23'-0" and is
    # still 4" clear of D-M-BATH1's opening at 23'-4" — that door is what bounds it north.
    ElectricalDevice(uid="QTM0013AAA", tag="ED-M-HALL-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 4.375), ft(22, 10)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTM0014AAA", tag="ED-M-HALL-SW2", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7), ft(22, 7.375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The stair head. Both kept their tags and positions when RM-M-STAIR retired into
    # RM-M-LIVING (2026-07-30) — they still light the well, they are just no longer in a
    # room of their own. The switch is also one end of the basement railing run's 3-way.
    ElectricalDevice(uid="QTM0015AAA", tag="ED-M-STAIR-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(27)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-STAIR-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0016AAA", tag="ED-M-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(10, 4.375), ft(28)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The porch fan (notes: "Large ceiling fan (60\") on porch ceiling"). Damp rated: it
    # hangs under SL-SG-DECK, the balcony slab, open on three sides. Mounted at 8'-6" so
    # the 1'-6" assembly tops out flush against that 10' deck underside.
    ElectricalDevice(uid="QTM0017AAA", tag="ED-M-PORCH-FAN", kind=DeviceKind.LIGHT,
                     position=pt(ft(18), ft(-4.833)), type_ref="ED-T-LT-FAN60",
                     circuit="CKT-LT-MAIN", controlled_by=("ED-M-PORCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 6))),
    ElectricalDevice(uid="QTM0018AAA", tag="ED-M-PORCH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(24, 10), ft(0, 7.625)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The porch flood (2026-08-02): mark S, narrow-throw full-cutoff spot, on the balcony's
    # centre rear pillar PT-SG-BR2 (a post, not a Wall, so this is free-positioned).
    # rotation 0 throws south down the deck; 8'-0" up the 10' pillar clears eye line and
    # deck edge. NO `room=`: like the porch fan, it must read as exterior to the wet-
    # location and dark-sky checks.
    ElectricalDevice(uid="QTM001EAAA", tag="ED-M-PORCH-FLOOD", kind=DeviceKind.LIGHT,
                     position=pt(ft(18), ft(-0.8333)), type_ref="ED-T-LT-FLOOD-NARROW",
                     circuit="CKT-LT-MAIN", rotation=deg(0),
                     controlled_by=("ED-M-PORCH-FLOOD-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
    # Own switch, second gang beside ED-M-PORCH-SW — separate leg, not shared: the fan
    # runs whole evenings, the flood is the you-heard-something light, and sharing one
    # switch would glare the flood on every night the fan spins.
    ElectricalDevice(uid="QTM001FAAA", tag="ED-M-PORCH-FLOOD-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(25, 2), ft(0, 7.625)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # ST-SG-PORCH's top-landing light (2026-09-03). R303.8 wants a luminaire at the top
    # landing of an exterior stair, and `code.R303_8_exterior_stairway_illumination` looks
    # for one within 4'-0" of the flight's plan outline on its `to_storey`. Nothing already
    # authored reaches: ED-M-PORCH-FAN and ED-M-PORCH-FLOOD are both at x=18'-0", ten feet
    # west of the flight's x 28'-6"..32'-2" and further still from its y -9'-0"..-6'-0".
    #
    # ** IT LEFT THE HOUSE WALL ON 2026-09-04. ** It hung on W-M-S2 at (30'-0", -0'-9 3/4")
    # while the flight ran along the house. The flight is now in the pocket's south half, so
    # the nearest point of W-M-S2 is 5'-2" from it and the 4'-0" reach above is not a figure
    # to argue with — R303.8 would report a stair with no light, correctly.
    #
    # So it moved onto **W-SG-E1's east face at the head of the flight**, which is the top
    # landing itself rather than a wall six feet away from it. x 28'-8 1/2" puts the 5" body's
    # BACK on that face at x 28'-6" (a device footprint is CENTRED on its position, so the
    # position owes the face half the depth — the ED-G-EXT-LT-E convention, and NOT the 1 5/8"
    # the two disconnects use: those are 3 1/4" cans and their offset buries this one an inch
    # into the concrete). `rotation=deg(90)` turns the body's depth onto x so it stands off an
    # east face, the ED-M-LIVING-KFZ1 convention.
    #
    # y is -9'-3", three inches SOUTH of the flight rather than beside it: the body stands 5"
    # proud of a face the treads run right up to, and at shin height in the middle of a stair
    # that is a hazard, not a light. It sits south rather than north because the north end of
    # this wall face is the two condenser disconnects and their NEC 110.26(A) working space
    # (plan/electrical.py) — a luminaire projecting 5" into that space is the same objection
    # from the other side.
    #
    # PT-SG-BF3 at the far end: the round came 5 1/4" north on 2026-09-03 and now reaches
    # y -9'-4", one inch south of this fitting. It is not a clash from either direction.
    # In PLAN the 12" round is tangent to this wall face at y -9'-10", not here, so the
    # nearest concrete is 5" away; in ELEVATION the column starts at the wall top and this
    # fitting hangs 8" below it. Both numbers move if `_y_front_pillar` moves again.
    #
    # ** -0'-8" IS A STEP LIGHT, AND THAT IS THE POINT. ** W-SG-E1's top is 0'-0", so this
    # face has no 7'-0" to mount at; 8" below the top puts the fitting 2'-2" over the pad,
    # washing the treads from beside them instead of throwing a shadow of the user down the
    # flight. It clears the 18"-24" cold-climate snow band the stands are sized against. The
    # fitting is unchanged and so is the circuit — this is the same wet-rated full-cutoff
    # luminaire on the same switch leg, on a different wall.
    #
    # NO `room=`, the ED-M-PORCH-FAN / ED-G-EXT-LT-E precedent — that absence is how
    # `electrical.wet_location` and `advisory.dark_sky_lighting` know a device is outside.
    #
    # ED-T-LT-SCONCE-EXT rather than a new full-cutoff downlight type: it is the same
    # full-cutoff wet-rated exterior fitting as the ED-G-EXT-LT-E/-W pair, and it is
    # already priced. A freshly minted LuminaireType with no prices.toml row is silently
    # DROPPED from the takeoff, so a new type here would have bought a fixture the bill
    # never showed.
    #
    # Controlled by ED-M-PORCH-FLOOD-SW rather than a third switch: NEC 210.70(A)(2)(b)
    # wants the exterior light switched from inside, that switch already is, and the flood
    # and the stair light are wanted on the same errand.
    ElectricalDevice(uid="QTM001GAAA", tag="ED-M-STAIR-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(28, 8.5), ft(-9, -3)), type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-MAIN", rotation=deg(90),
                     controlled_by=("ED-M-PORCH-FLOOD-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(0, -8))),
]

# --- Second storey --------------------------------------------------------------------
SECOND_LIGHTING = [
    # RM-S-HALL: the upstairs shadow gap, run as one polyline around three sides of the
    # hall — a cove that stops short of a corner reads as a mistake, so it turns instead.
    #
    # ** IT TURNS AT y=27'-6" NOW, NOT 30'-4". ** SF-S-HP1's south edge is at y=27'-8" and
    # its face is at 7'-3"; a cove at 9'-0" north of that line would be BURIED inside the
    # bulkhead, lighting the inside of a soffit. It turns 2'-10" sooner and the north end of
    # the hall is lit by the box's own face instead. 44'-6" -> 38'-10" of strip, which is a
    # real change to the takeoff, not a drafting tidy. Still four vertices.
    LightRun(uid="QRS0001AAA", tag="LR-S-HALL-GAP", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(18, 6), ft(9, 7)), pt(ft(18, 6), ft(27, 6)),
                   pt(ft(21, 6), ft(27, 6)), pt(ft(21, 6), ft(9, 7))),
             room="RM-S-HALL", psu_ref="ED-S-HALL-LT-PSU",
             controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The driver moved with the cove: (20'-0", 30'-6") is inside EQ-S-HP1-AH's footprint
    # since the 2026-09-04 HP1 move. (19'-0", 27'-2") keeps the relationship it always had
    # — a driver hidden in SF-S-DUCT, 12" west of ED-S-HALL-CAN3 — on the other side of the
    # y=27'-8" seam from the machine.
    ElectricalDevice(uid="QTS0001AAA", tag="ED-S-HALL-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(19), ft(27, 2)), type_ref="ED-T-LT-PSU-200",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.CEILING)),
    # CAN1-3 recess into the SF-S-DUCT dropped duct soffit face (drop 14" -> 7'-10"),
    # not the 9' structural ceiling above it.
    ElectricalDevice(uid="QTS0002AAA", tag="ED-S-HALL-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(20), ft(13)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True,
                                 elevation=ft(7, 10))),
    ElectricalDevice(uid="QTS0003AAA", tag="ED-S-HALL-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(20), ft(20)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True,
                                 elevation=ft(7, 10))),
    ElectricalDevice(uid="QTS0004AAA", tag="ED-S-HALL-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(20), ft(27)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True,
                                 elevation=ft(7, 10))),
    # Both x's follow the hall face of W-S-BW1/BW2, INT_2X4_RC (plan/storeys/second.py) —
    # the resilient channel faces the hall, because the hall is what the bedrooms are being
    # protected from. Authored x is the face LESS 1" (box back on the face, 2" box):
    # 21'-8 1/8" - 1" = 21'-7 1/8".
    ElectricalDevice(uid="QTS0005AAA", tag="ED-S-HALL-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 7.125), ft(10)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTS0006AAA", tag="ED-S-HALL-SW2", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 7.125), ft(26, 6)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-S-SUITE: the linear wall lamp the notes ask for over the bed, on the long west
    # wall, plus cans down the west strip and one in the arm past the walk-in.
    # y tracks W-S-SN1's south face (same station as ED-S-SUITE-RC5), the 8" staggered
    # sound wall.
    ElectricalDevice(uid="QTS0007AAA", tag="ED-S-SUITE-LAMP", kind=DeviceKind.LIGHT,
                     position=pt(ft(4, 11.875), inch(263.125)), type_ref="ED-T-LT-WALL-LINEAR",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE", rotation=deg(180),
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
    ElectricalDevice(uid="QTS0008AAA", tag="ED-S-SUITE-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(15)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0009AAA", tag="ED-S-SUITE-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(20)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000AAAA", tag="ED-S-SUITE-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 6), ft(14, 2)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    ElectricalDevice(uid="QTS000BAAA", tag="ED-S-CLOSET-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 10), ft(10, 8)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-UPPER", room="RM-S-CLOSET",
                     controlled_by=("ED-S-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000CAAA", tag="ED-S-CLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 10.875), ft(11, 11)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-S-CLOSET", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-S-SUITEBATH: ED-S-SUITEBATH-LT is now a wet can; a second sits over the shower in
    # the NE corner, and the mirror light goes on the south wall over FX-S-SUITEBATH-LAV.
    ElectricalDevice(uid="QTS000DAAA", tag="ED-S-SUITEBATH-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(16, 2), ft(20, 6)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITEBATH",
                     controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** THE PRIMARY SUITE'S MIRROR BECAME THE LIT ONE ON 2026-09-06 (owner's call), AND
    # THAT ALSO FIXES A ROOM MISMATCH THAT HAD BEEN SITTING IN THIS FILE. **
    # ED-T-LT-MIRROR-RING's own comment called it "the master's lit mirror" and the only
    # instance of it stood in RM-S-BATH1, the hall bath. The owner wants the integrated LED
    # mirror — not a plain mirror flanked by sconces — in the PRIMARY bath, so the type comes
    # here and the hall bath keeps its own (a second P1; the two rooms are the two that were
    # ever candidates for one).
    #
    # 30" round over a 30" vanity is the right size, and this is a MIRROR rather than a bar
    # above one, which matters: a bar over a mirror sits above the brow line and casts
    # brow/nose/chin shadows DOWN onto the thing you are trying to see, where a front-lit
    # mirror cross-lights at eye height. Running both would be redundant, so the bar goes.
    #
    # ``elevation`` drops from 6'-6" (a bar ABOVE a mirror) to 3'-6" (the BASE of a 30"
    # mirror, putting its centre at 5'-0"), matching how ED-S-BATH1-MIRROR is authored.
    ElectricalDevice(uid="QTS000EAAA", tag="ED-S-SUITEBATH-MIRROR", kind=DeviceKind.LIGHT,
                     # y = 264.625" (W-S-SBN's bath face) less half of the Robern's 1 3/4"
                     # body. The bar this replaced was 3" deep and sat at 263.625".
                     position=pt(ft(13, 10), inch(263.75)), type_ref="ED-T-LT-MIRROR-RING",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITEBATH", rotation=deg(180),
                     controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6))),
    # ** THE ROBERN IS CORD-AND-PLUG, so it needs a receptacle of its own ** — not the same
    # outlet as ED-S-SUITEBATH-RC1, which is the NEC 210.52(D) counter-height one and stays.
    # Same pattern and the same 54" band as ED-S-BATH1-RC-MIRROR. GFCI at the receptacle,
    # not just at the breaker (210.8(A)(1)). The cord runs behind the glass to a plate
    # BESIDE it; it used to plug in behind it, which is the defect fixed below.
    #
    # ** IT MUST NOT LAND WHERE A MOUNTING CLEAT OR THE BOTTOM BRACKET GOES, and the mirror's
    # own install sheet is the authority on where those are ** (the round unit's cleat
    # spacing was not confirmable and has to be read off the sheet in the carton). Two things
    # for the framer and the electrician before the wall closes: block a FULL-WIDTH flat 2x
    # band, because the two outer brackets sit only about +/-5" from the centreline and will
    # not find 16" o.c. studs at an arbitrary vanity centre; and pull a conductor for a
    # SECOND switch leg, because Robern requires the defogger to be switched independently
    # of the lights.
    #
    # ** MOVED OUT FROM BEHIND THE GLASS, x=13'-10" -> 12'-3 1/2" (2026-09-06), with
    # ED-S-BATH1-RC-MIRROR, which it was authored from. ** At x=166" it was dead centre of
    # the 30" mirror (x 151"..181") at 54" AFF: a GFCI DEVICE on a circuit that is not GFCI
    # at the breaker, so its test/reset button was the whole protective path and it was
    # sealed behind a hardwired mirror. x=147.5" puts the 4 1/2" plate at 145 1/4"..149 3/4",
    # 1 1/4" clear of the mirror's west edge and clear of FX-S-SUITEBATH-WC (x 127"..142").
    # It now stacks directly over ED-S-SUITEBATH-RC1 at x=148"/44" with 5 1/2" between the
    # two plates, which is how it reads on the wall: the counter outlet and the mirror's,
    # one above the other.
    #
    # ** EAST WAS THE OBVIOUS SIDE AND IT IS NOT AVAILABLE: ** x 181"..211 1/2" of this
    # north wall is inside FX-S-SUITEBATH-TUBSH's own footprint.
    #
    # Unlike the hall bath this room does NOT depend on this outlet for 210.52(D) —
    # ED-S-SUITEBATH-RC1 is 2 1/2" off the lav carcass and carries it either way.
    ElectricalDevice(uid="CE0KDETNZH", tag="ED-S-SUITEBATH-RC-MIRROR",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(147.5), ft(21, 11.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND", room="RM-S-SUITEBATH", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    # The lit shower niche (plans/TODO.md §Plumbing: Schluter-KERDI-BOARD-SNLT).
    # In W-S-C2C, the alcove wall that's neither glazed south nor a door: 2'-4" of head
    # channel centred on the alcove (y 17'-0"..22'-0") at y=19'-6", x=17'-9" (3" proud of
    # wall centre). Head at 5'-0" — niche sill is 4'-0", clearing the tub deck by 2'-4" and
    # putting a bottle at hand height. 24V, no branch circuit — driver does. 2'-4" at 3 W/ft
    # = 7 W, well under the 60 W supply.
    LightRun(uid="QRS0004AAA", tag="LR-S-NICHE", type_ref="ED-T-LT-NICHE-SNLT",
             path=(pt(ft(17, 9), ft(18, 4)), pt(ft(17, 9), ft(20, 8))),
             room="RM-S-SUITEBATH", psu_ref="ED-S-NICHE-PSU",
             controlled_by=("ED-S-SUITEBATH-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="QTS000E1AA", tag="ED-S-NICHE-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(m(5.74792), m(6.74617)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.CEILING)),

    # RM-S-VANITY: two lavatories, two mirror lights, both on the north wet wall.
    ElectricalDevice(uid="QTS000FAAA", tag="ED-S-VANITY-MIRROR1", kind=DeviceKind.LIGHT,
                     position=pt(ft(1, 9), ft(26, 1.625)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-S-VANITY", rotation=deg(0),
                     controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTS000GAAA", tag="ED-S-VANITY-MIRROR2", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(26, 1.625)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-S-VANITY", rotation=deg(0),
                     controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),

    # RM-S-BATH1: two wet cans, one over the shower, and the mirror the brief is most
    # specific about — a 36" front-lit ring on the room's east wall, on the lavatory's
    # centre line (the lav faces east across the room). Front-lit, not edge-lit: an
    # edge-lit ring backlights the face and is useless to shave or do makeup by. The
    # controller has to remember its last setting and its standby LED has to be dim.
    ElectricalDevice(uid="QTS000HAAA", tag="ED-S-BATH1-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(3), ft(29)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1",
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000JAAA", tag="ED-S-BATH1-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(33)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1",
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000KAAA", tag="ED-S-BATH1-MIRROR", kind=DeviceKind.LIGHT,
                     # x moved 5/8" east on 2026-09-06: the Robern's body is 1 3/4" deep
                     # where the authored ring was 3", so the old centre left the glass
                     # floating 0.6" off W-S-BD-E's face. The FACE has not moved (9'-8 5/8");
                     # the centre is face less half the new depth.
                     position=pt(inch(115.75), ft(31)), type_ref="ED-T-LT-MIRROR-RING",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1", rotation=deg(-90),
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6))),
    # Mirror is hardwired *and* gets an outlet beside it (electrical_notes.md line 80), so a
    # future replacement doesn't need an electrician. GFCI at the RECEPTACLE, not at the
    # breaker — 210.8(A)(1), and CKT-RC-SECOND is deliberately not GFCI at the panel
    # (circuits.py: thirty outlets behind one 5 mA trip is not buildable).
    #
    # ** MOVED OUT FROM BEHIND THE GLASS, y=31'-0" -> 32'-6 3/4" (2026-09-06). ** At
    # y=372" it was dead centre of ED-S-BATH1-MIRROR (a 30" Robern, y 357"..387", 42"..72"
    # AFF) at 54" AFF — sealed behind a hardwired mirror. That is the one thing a GFCI
    # DEVICE must never be: its circuit is not GFCI at the breaker, so the test/reset button
    # was the entire protective path and no hand could reach it. The house states this
    # principle for exactly this case twice already and then took the opposite decision here
    # (see ED-M-BATH2-TUB-RC in plan/electrical.py, and CKT-BATH2-TUB in plan/circuits.py).
    #
    # ** AND IT WAS ALSO THIS ROOM'S ONLY RECEPTACLE, so deleting it was never available: **
    # code.E3901_6_bathroom_receptacle passes RM-S-BATH1 on this outlet and nothing else.
    # Moving it keeps that pass — y=390.75" is still hard against FX-S-BATH1-LAV's carcass
    # (y 345.88"..393.88"), 0" to the basin's outside edge against 210.52(D)'s 36".
    #
    # y=390.75" is the 7 1/2" of wall between the mirror's north edge and
    # FURN-S-BATH1-SHELF at y=394.5": a 4 1/2" plate leaves 1 1/2" and 1 3/4". The 11 1/8"
    # south of the mirror is wider but ED-S-BATH1-SW already has 4 1/2" of it at y=354".
    # 54" AFF is kept, not dropped to the house's 44" vanity height: at 44" the plate
    # (41 3/4"..46 1/4") would foul the mirror's own 42" base line the moment the glass is
    # centred any further north.
    ElectricalDevice(uid="QTS000MAAA", tag="ED-S-BATH1-RC-MIRROR",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 7.625), inch(390.75)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND", room="RM-S-BATH1", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    ElectricalDevice(uid="QTS000NAAA", tag="ED-S-BATH1-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 7.625), ft(29, 6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # The hall bath's lit niche (2026-08-02), mirroring the suite's LR-S-NICHE — same
    # KERDI-BOARD-SNLT board and rules (notes/shower_niche.md: board IS the membrane,
    # driver lead exits through the head channel, sealed with KERDI-FIX).
    # Alcove's back wall is the glazed exterior, so this niche goes in the tub's west END
    # wall (W-S-CH-W, a dry mechanical-chase wall) instead, with the 12"x28" board stood
    # VERTICAL — the alcove's clear run there is only ~25". Head channel: 1'-0" of tape at
    # the same 5'-0" bottle-height head as the suite's, centred at y=34'-4", x=3'-0"
    # (3" proud of wall centre).
    LightRun(uid="QRS0005AAA", tag="LR-S-BATH1-NICHE", type_ref="ED-T-LT-NICHE-SNLT",
             path=(pt(ft(3), ft(33, 10)), pt(ft(3), ft(34, 10))),
             room="RM-S-BATH1", psu_ref="ED-S-BATH1-NICHE-PSU",
             controlled_by=("ED-S-BATH1-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # Own 60 W driver, in the ceiling outside the shower zone (serviceable without opening
    # tile). NOT a share of ED-S-NICHE-PSU: that's 30' away across the plan, and the
    # catalog's per-area-supply rule (plan/lighting_types.py) forbids a 24V home run that
    # long. 1'-0" at 3 W/ft = 3 W, well under the 60 W box.
    ElectricalDevice(uid="QTS001CAAA", tag="ED-S-BATH1-NICHE-PSU",
                     kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(7), ft(31, 6)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.CEILING)),

    # Both switches sit at x=17'-6 3/4", the humid liner on W-S-C1's plant-room face — a
    # switch authored to the bare wall face resolves inside the panel.
    # RM-S-PLANT: two suspended tubes over the plants at the south windows, on a timer so
    # they run a photoperiod rather than whenever somebody remembers. The fan-light
    # (ED-S-PLANT-LT, re-typed) moves the humid air a plant room makes.
    ElectricalDevice(uid="QTS000PAAA", tag="ED-S-PLANT-TUBE1", kind=DeviceKind.LIGHT,
                     position=pt(ft(3, 4), ft(2)), type_ref="ED-T-LT-TUBE6",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(2, 3))),
    ElectricalDevice(uid="QTS000QAAA", tag="ED-S-PLANT-TUBE2", kind=DeviceKind.LIGHT,
                     position=pt(ft(8, 8), ft(2)), type_ref="ED-T-LT-TUBE6",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(2, 3))),
    ElectricalDevice(uid="QTS000RAAA", tag="ED-S-PLANT-SW-TIMER", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7), ft(2)), type_ref="ED-T-SWITCH-TIMER",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-S-STUDY2: the notes' study sconces — down spots on the *side* walls, set back
    # from the south window wall, so the desk is lit without a lit head in the glass after
    # dark. Two stair sconces step up the north wall beside ST-S2A's flight to the attic.
    ElectricalDevice(uid="QTS000SAAA", tag="ED-S-STUDY2-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(31), ft(3)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000TAAA", tag="ED-S-STUDY2-SPOT1", kind=DeviceKind.LIGHT,
                     position=pt(m(7.74783), m(0.217857)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(180),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    ElectricalDevice(uid="QTS000VAAA", tag="ED-S-STUDY2-SPOT2", kind=DeviceKind.LIGHT,
                     position=pt(m(9.10893), m(0.219983)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(180),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    # x=29'-0", z=7'-6": ST-S2A climbs westward at 7 1/2" per 10" of run, so a station too
    # far west buries the fixture in its own flight — at x=25'-0" the tread top is 95 1/2"
    # storey-relative against a 10'-0" floor-to-floor storey, leaving no band for an 8"
    # fixture. At x=29'-0" the tread top is 59 1/2" storey-relative, so ft(7,6) sits 30 1/2"
    # above the tread with the fixture topping out at 98" -- clear of the deck over, the
    # same relationship SC2 keeps at x=32' (45 1/2" over a 32 1/2" tread).
    #
    # ** NO CHECK CAUGHT THIS. ** `code.R303_7_stairway_illumination` counts luminaires
    # serving the flight (nine for ST-S2A, so it never depended on SC1),
    # `electrical.room_lighting` counts by room, and the fc advisory is planar. Nothing in
    # the engine compares a wall-mount elevation against the stair it lights.
    ElectricalDevice(uid="QTS000WAAA", tag="ED-S-STUDY2-STAIR-SC1", kind=DeviceKind.LIGHT,
                     position=pt(ft(29), ft(8, 7.625)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(0),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6))),
    ElectricalDevice(uid="QTS000XAAA", tag="ED-S-STUDY2-STAIR-SC2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(8, 7.625)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(0),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),

    # RM-S-BED1/2/3: identical four-can grids flanking each bed wall.
    ElectricalDevice(uid="QTS0010AAA", tag="ED-S-BED1-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(11, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED1",
                     controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0011AAA", tag="ED-S-BED1-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(15, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED1",
                     controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0012AAA", tag="ED-S-BED1-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(15, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED1",
                     controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0013AAA", tag="ED-S-BED2-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(20, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0014AAA", tag="ED-S-BED2-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(24, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0015AAA", tag="ED-S-BED2-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(24, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0016AAA", tag="ED-S-BED3-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(29, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED3",
                     controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0017AAA", tag="ED-S-BED3-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(33, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED3",
                     controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0018AAA", tag="ED-S-BED3-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(33, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED3",
                     controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # The landing end of RM-S-HALL + the stairwell chandelier, hung over the ST-M2S
    # opening so it reads from both the stair and the landing. Both name RM-S-HALL —
    # landing, well and east hall are one room since the centre line opened under
    # BM-S-HALL.
    #
    # There is no can over the landing itself: that point is inside FO-A-HALL, open to the
    # roof, with no host surface for a recessed can. The chandelier below is the fixture
    # for it instead — a double-height pendant hanging over the well — and the landing's own
    # switch (ED-S-LANDING-SW) runs it.
    #
    # ** THE CHANDELIER'S VOLUME NOW RUNS TO THE ROOF UNDERSIDE. ** At x=13'-11 7/8" that is
    # 5'-0" + x/3 = 9'-8" above the attic deck, so 19'-8" above the second floor.
    #
    # It is authored with an EXPLICIT `elevation` and NOT with `drop`, and the difference
    # matters. `resolve/placeables.py` subtracts a `drop` from `floor +
    # storey.default_ceiling_height` — the 9'-0" plane that does not exist over this open
    # well. `elevation` is read as the body's BASE directly, so ft(5) puts the shade bottom
    # at 5'-0" over the second floor, clear of the landing and reachable from the flight;
    # the fitting hangs on ~14'-8" of stem from the rafters above it, reading from the main
    # floor as well as from the landing.
    ElectricalDevice(uid="QTS001AAAA", tag="ED-S-STAIR-CHAND", kind=DeviceKind.LIGHT,
                     position=pt(m(4.26405), m(9.3355)), type_ref="ED-T-LT-CHANDELIER",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     controlled_by=("ED-S-STAIR-SW", "ED-S-LANDING-SW"),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(5))),
    # On W-S-SN3's north face at y=22'-6 1/4", the wall you walk straight at off the
    # flight — a two-gang box with ED-S-LANDING-SW. x=12' is inside the well's west lane
    # (x 10'-3 3/8"..13'-9 3/4"), where ST-M2S turns left, and is where you arrive.
    ElectricalDevice(uid="QTS001BAAA", tag="ED-S-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12), ft(22, 8.375)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]

# --- Attic ----------------------------------------------------------------------------
# The attic's fittings live in plan/lighting_attic.py (this file was over AGENTS.md's 500
# lines). The attic is a 6:12 cathedral off a 1 1/2" rafter plate, so the ceiling is
# `1 1/2" + x/2` above the attic floor, mirrored past x=18'. Every attic ceiling fixture
# states its elevation, sloped-ceiling trims, housings in the rafter bay — see that file's
# own header.
# --- Garage ---------------------------------------------------------------------------
# Two 4' shop lights on their own switch by the service door, on the house's main lighting
# circuit (garage is freestanding but fed from ED-B-PANEL) rather than the GFCI receptacle
# circuit, which would drop the lights every time a tool trips one. Surface mounted at 8' —
# nothing above the garage ceiling to recess a can into.
GARAGE_LIGHTING = [
    ElectricalDevice(uid="QTG0001AAA", tag="ED-G-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(18), ft(48)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    ElectricalDevice(uid="QTG0002AAA", tag="ED-G-LT2", kind=DeviceKind.LIGHT,
                     position=pt(ft(18), ft(58)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # A third shop light over the service-door landing. The two above are at y=48' and
    # y=58', the working half of the bay; the landing is at y 40'-6"..43'-6" and the flight
    # below it drops 2'-10" in five risers, neither light reaching within R303.8's 4'.
    # Stepping off a 34" landing in the dark is the reason the rule exists. (It reads as an
    # *exterior* stair rather than an interior one because `_stair_is_indoors` asks whether
    # a CONDITIONED room stands over it, and the garage is deliberately unconditioned. R303.7
    # would want the same luminaire here and not the switching, since five risers is under
    # its six-riser threshold.)
    ElectricalDevice(uid="4PQRD03TG8", tag="ED-G-LT3", kind=DeviceKind.LIGHT,
                     position=pt(ft(8, 6), ft(42)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # On W-G-S's INTERIOR face (plan/storeys/garage.py::GARAGE_Y_SOUTH) — see
    # plan/electrical.py's GARAGE_DEVICES comment for the face-position arithmetic.
    ElectricalDevice(uid="QTG0003AAA", tag="ED-G-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(10, 6), ft(41, 4.375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The garage-door lights (2026-08-02; a PAIR since 2026-09-07): mark R, full-cutoff
    # exterior sconces. The single light followed the overhead door onto W-G-N earlier the
    # same day — the door is the thing it lights, and the door faces north now — and it was
    # then mirrored, because one sconce on one side of a 16' door lights half an apron and
    # reads as an accident on a symmetrical elevation. W-G-N runs x 6'..30' and the opening
    # takes x 10'..26', leaving a 4'-0" pier at each end; each light stands on its pier's
    # centre, 2'-0" clear of both the jamb and the corner. Both aim north (`rotation=deg(0)`).
    #
    # ** THE TAG WAS `ED-G-EXT-LT`. ** It is `-E` now and `-W` is its twin: a pair whose
    # members do not share a naming scheme is a pair only in the drawing. Nothing
    # prefix-matches between the two (see the ED-M-STAIR-LT / RL-SG-PORCH- precedent for why
    # that is worth checking), and prices.toml's ED-T-LT-SCONCE-EXT row now carries 3 ea.
    #
    # NO `room=`, deliberately — outside RM-GARAGE is how `electrical.wet_location` /
    # `advisory.dark_sky_lighting` know these are exterior.
    #
    # ** ELEVATION DROPPED 1'-4" WITH THE PAIRING. ** 5'-8" is storey-relative (garage datum
    # = stem top at 1'-10" over slab), so each sits 7'-6" over the apron — 6" over
    # D-G-OVERHEAD's 7'-0" head, which is what makes the two of them read as framing the
    # door rather than floating up under the eave. The old 7'-0" put them at 8'-10", nearly
    # at the 9'-10" plate. The 9" housing tops out at 8'-3" over the apron, still 1'-7"
    # under the plate.
    #
    # ** y IS THE FIXTURE'S CENTRE, NOT THE WALL FACE, on both. ** A wall device's footprint
    # is centred on its position, so a 5" sconce owes the cladding face half its depth or it
    # resolves buried in the panel — which nothing in `haus check` grades, though
    # test_wall_mounted_devices_resolve_against_a_wall_face does. W-G-N's cladding outer face
    # is 64'-9 1/2" (GARAGE_Y_NORTH + the 7/8" corrugated panel), so the centre is 2 1/2"
    # proud of it at 65'-0".
    ElectricalDevice(uid="QTG0004AAA", tag="ED-G-EXT-LT-E", kind=DeviceKind.LIGHT,
                     # x=28'-0" is 2'-0" in from the NE corner. The uid is the original
                     # light's: this element did not stop existing when it was retagged.
                     position=pt(ft(28), ft(65)), type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-MAIN", rotation=deg(0),
                     controlled_by=("ED-G-EXT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 8))),
    ElectricalDevice(uid="GT8NZ3DTSX", tag="ED-G-EXT-LT-W", kind=DeviceKind.LIGHT,
                     # x=8'-0" is 2'-0" in from the NW corner, the exact mirror of -E about
                     # the door's centreline at x=18'-0". Same circuit, same switch: the pair
                     # is one control, not two.
                     position=pt(ft(8), ft(65)), type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-MAIN", rotation=deg(0),
                     controlled_by=("ED-G-EXT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 8))),
    # Its switch, inside, ganged beside ED-G-SW at the service door (D-G-SERVICE's west
    # jamb is at 8'-6"; the shop-light switch sits at 10'-6", this one 6" west of it —
    # ** AND BOTH OF THOSE STATIONS ARE INSIDE THE ROUGH OPENING, WHICH IS A PRE-EXISTING
    # DEFECT CARRIED FORWARD, NOT A NEW ONE. ** `from_node` offsets the NEAR jamb, so
    # D-G-SERVICE's RO is 8'-6"..11'-6" and its EAST jamb is 11'-6", not the 8'-6" this note
    # has claimed since the switches were authored. Nothing grades a wall device against an
    # opening. The 2026-09-07 move translated both switches faithfully rather than quietly
    # re-siting them; putting them east of the real east jamb (~12'-0" / 12'-6") is a small
    # separate edit and is the right fix) —
    # walk in, one reach turns on the shop lights and BOTH door lights. One switch for the
    # pair, not one each: they light a single opening and there is no reason to run half of
    # it. It stays here though its luminaires crossed to the far wall: the switch belongs at
    # the door you enter by, not under the lamp.
    ElectricalDevice(uid="QTG0005AAA", tag="ED-G-EXT-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(10), ft(41, 4.375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]
