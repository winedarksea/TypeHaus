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
#   (5' + d/3, d = distance from the x=18' ridge) because that ceiling is a 4:12 cathedral.
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
    ElectricalDevice(uid="QTB0001AAA", tag="ED-B-GYM-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(4, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0002AAA", tag="ED-B-GYM-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(4, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0003AAA", tag="ED-B-GYM-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(13, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0004AAA", tag="ED-B-GYM-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(13, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-B-WORKSHOP: flat panels, per the notes. A workshop wants flat even light over a
    # bench, not the scalloping a can grid gives. The L-shaped room takes one panel in
    # each leg — the west bay south of the sauna, and the north strip.
    ElectricalDevice(uid="QTB0005AAA", tag="ED-B-WORKSHOP-PANEL1", kind=DeviceKind.LIGHT,
                     position=pt(ft(4, 6), ft(6)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    ElectricalDevice(uid="QTB0006AAA", tag="ED-B-WORKSHOP-PANEL2", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(16)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    ElectricalDevice(uid="QTB0007AAA", tag="ED-B-WORKSHOP-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(16), ft(17, 8.626)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP", rotation=deg(0),
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
    # Moved north 2026-08-02, when the ESS closet took the furnace room's SE corner: at
    # (9'-7", 20'-0") the switch would have stood inside RM-B-ESS, and a switch for the
    # furnace-room lights cannot live behind the battery closet's door. The closet left for
    # the NE corner on 2026-08-23 and this did NOT follow it — y=23'-0" is now simply
    # mid-room on the east wall face (W-B-STR3 since that wall was split, and framed 2x6
    # rather than concrete since 2026-08-24 — the face moved 3 1/8" east with it, and this
    # box came with it, x=9'-5" to 9'-8 1/8", still 1" proud of the face), which is where you
    # reach it walking in from D-B-FURN.
    ElectricalDevice(uid="QTB000AAAA", tag="ED-B-FURNACE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 8.125), ft(23)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-PLAY-N is the theatre. Up/down sconces on the east wall are the traditional
    # answer (notes) and the dimmer is the whole point: bright enough to cross the room,
    # dark enough to watch something. Two cans on the same dimmer are the cleaning light.
    ElectricalDevice(uid="QTB000BAAA", tag="ED-B-PLAY-N-SCONCE1", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 10), ft(23, 4.875)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(-90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTB000CAAA", tag="ED-B-PLAY-N-SCONCE2", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 10), ft(29, 11.25)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(-90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTB000DAAA", tag="ED-B-PLAY-N-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(24), ft(22)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N",
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB000EAAA", tag="ED-B-PLAY-N-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(30), ft(22)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N",
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Cans 3 and 4 (2026-08-01, code.R303_1_light_and_ventilation): this windowless room is
    # habitable only under R303.1 Exception 1's 6 fc average. Two sconces + two cans was
    # 3,200 lm / 4.7 fc over 324 sf — short; four cans reaches 5,000 lm / 7.4 fc. Same
    # dimmer as the rest: the whole room goes down together.
    ElectricalDevice(uid="QTB0010AAA", tag="ED-B-PLAY-N-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(24), ft(30)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N",
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0011AAA", tag="ED-B-PLAY-N-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(30), ft(30)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N",
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB000FAAA", tag="ED-B-PLAY-N-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 7), ft(20)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-STAIR: the railing light the notes ask for. A 24V tape at 34" on the stair's
    # west wall, under the handrail — it lights the treads without a fixture in anyone's
    # eyeline coming up. 3-way with the main-storey stair switch, because a stair light
    # that can only be switched from the bottom is a stair light nobody uses.
    LightRun(uid="QRB0001AAA", tag="LR-B-STAIR-RAIL", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(10, 4.375), ft(25, 5)), pt(ft(10, 4.375), ft(34, 10))),
             room="RM-B-STAIR", psu_ref="ED-B-STAIR-LT-PSU",
             controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
             mount=Mount(kind=MountKind.WALL, elevation=inch(34))),
    # The AC/DC supply in a ceiling box, at the head of the run it feeds (notes: "Box in
    # ceiling for AC/DC power supply"). 9'-5" of tape at 3 W/ft is 28 W; x1.25 = 35 W, so
    # the 60 W supply is the catalog size above it.
    ElectricalDevice(uid="QTB000GAAA", tag="ED-B-STAIR-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(11), ft(24, 6)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.CEILING)),
    # Both this and LR-B-STAIR-RAIL above moved 2 5/8" west on 2026-08-24, with the wall
    # face they hang on: W-B-STR3 is a framed 2x6 line now and the shaft's west face is
    # x=10'-3 3/8" instead of the pour's 10'-6". Each still sits 1" proud of that face.
    ElectricalDevice(uid="QTB000HAAA", tag="ED-B-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(10, 4.375), ft(23)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # Moved north from y=21' on 2026-07-30: RM-B-BATH took the shaft's south 3'-0", so the old
    # position is inside the bathroom now and `integrity.placeable_room_mismatch` said so. At
    # y=23'-6" the can is still in the arrival zone at the foot of the flight, between the
    # bathroom door's outswing arc and D-B-NE's opening at 22'-6"..25'-2".
    ElectricalDevice(uid="QTB000JAAA", tag="ED-B-STAIR-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(23, 6)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-B-BATH (2026-07-30). On CKT-LT-BACKUP, deliberately, so this room and the stair
    # foot stay lit together on backup power. Can centred at x=14', clear of the exhaust
    # terminal over the WC at 11'-8"; switch on the latch-jamb side (door swings out, so
    # it isn't behind the leaf).
    ElectricalDevice(uid="QTB000KAAA", tag="ED-B-BATH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(20)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH",
                     controlled_by=("ED-B-BATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB000LAAA", tag="ED-B-BATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(15, 8), ft(21, 5)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH", rotation=deg(180),
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
    # (electrical_notes.md line 24). Panels over the working floor, cans over the counters
    # — a can right above where you stand puts your own shadow on the cutting board, which
    # is why the perimeter gets them and the middle does not.
    ElectricalDevice(uid="QTM0007AAA", tag="ED-M-KITCH-PANEL1", kind=DeviceKind.LIGHT,
                     position=pt(ft(23), ft(30)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    ElectricalDevice(uid="QTM0008AAA", tag="ED-M-KITCH-PANEL2", kind=DeviceKind.LIGHT,
                     position=pt(ft(31), ft(30)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    # Moved x 22'-6" -> 25'-10" (2026-08-24), then -> 25'-2 1/2" (2026-08-26) with the base
    # run's re-composition. At 22'-6" it resolved INSIDE W-M-PAN-S, the new pantry's south
    # partition (axis y=32'-9"), which is also where it drew integrity.placeable_room_mismatch.
    # It is NOT retagged into RM-M-PANTRY: its controlled_by is ED-M-KITCH-SW and the kitchen
    # needs the can. It still follows FURN-M-KIT-E1's centre — the north counter run's west
    # end, now that the run starts at the pantry wall instead of at FURN-M-KIT-PANTRY-E. y is
    # unchanged, so it stays on CAN2's line, 8" south of the counter front, which is the
    # composition.
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
    # ** BOTH EAST CANS WERE STALE, AND THE COMMENT MORE SO. ** The line that stood here
    # said "over the sink" — the sink moved to the NORTH wall in the 2026-07-30 swap, and
    # this can has been lighting the top of APPL-M-HOOD's canopy ever since. CAN4 was over
    # FURN-M-KIT-N2, which the peninsula deletes. Re-laid 2026-08-24 onto what is actually
    # underneath: CAN3 over FURN-M-KIT-N4 (centre y=34'-2 3/8") and CAN4 over the new 24"
    # FURN-M-KIT-N3 (centre y=29'-5 3/8"). x=34'-3" is unchanged — 9 5/8" in from the
    # counter front, the same offset the pair already had.
    ElectricalDevice(uid="QTM000BAAA", tag="ED-M-KITCH-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 3), ft(34, 2.375)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000CAAA", tag="ED-M-KITCH-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 3), ft(29, 5.375)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000DAAA", tag="ED-M-KITCH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(26, 6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # --- kitchen under-cabinet task light (2026-08-24) --------------------------------
    # The kitchen had no task light at all: four ceiling cans over a counter you stand in
    # front of, which is the arrangement this file's own kitchen header warns about.
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
    # Endpoints are literal base joints (2026-08-26 re-composition): WE1 now runs the full
    # W-of-window bay 24'-7"..27'-10" (3'-3", was 2'-6") and WE2 the E-of-window bay
    # 30'-10"..33'-4" (2'-6", was 2'-0") — see plan/placeables.py's kitchen header.
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
    # Extended south to 27'-2 3/8" (2026-08-24) with FURN-M-KIT-WN4, the 15" box filling the
    # gap the mixer garage left: the tape runs the whole continuous 13"-deep upper face from
    # the garage's north side to the range, which is also the whole of the peninsula's east
    # counter and FURN-M-KIT-N3's top.
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
    # 11'-5" of tape (2026-08-26: was 10'-2" before the north pair grew 15" with the base
    # run's re-composition) at 5 W/ft = 57.1 W; x1.25 = 71.3 W. ** That is already past
    # ED-T-LT-PSU-60's 60 VA ** — it cleared by 4.3 VA at the 8'-11" this run was first
    # drawn at, and one 15" cabinet (FURN-M-KIT-WN4) spent that margin and 3.5 VA more,
    # which is exactly why the 200 W supply was specified instead of the 60. It loads to
    # ~36%. NOT a share of
    # ED-M-LIVING-LT-PSU: that one is on CKT-LT-MAIN, and electrical_notes.md line 24 puts
    # kitchen lighting behind the backup relay.
    ElectricalDevice(uid="7VSVT7B8ZS", tag="ED-M-KITCH-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(32), ft(33)), type_ref="ED-T-LT-PSU-200",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.CEILING)),
    # ** NOT beside ED-M-KITCH-SW, and that is worth stating. ** W-M-C5's east face has no
    # free wall left on it at all: FURN-M-KIT-PANTRYC covers y 25'-0 7/8"..27'-0 7/8" and
    # the cold pair covers 27'-0 7/8"..32'-6 5/8", so the existing switch at y=26'-6" is
    # already behind a cabinet — a pre-existing condition this commit neither causes nor
    # fixes, but is not going to make worse by ganging a second device into it. This one
    # goes on W-M-PAN-E's EAST face instead, at the pantry's outside corner, which is the
    # wall you actually pass on the way into the kitchen from the west.
    ElectricalDevice(uid="EX3ZQQPM9K", tag="ED-M-KITCH-SW-UC", kind=DeviceKind.SWITCH,
                     position=pt(ft(24, 7.375), ft(33, 1)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # --- RM-M-PANTRY's vertical slot (2026-08-24) -------------------------------------
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
    # spot on the centre bearing wall for the desk, over a general can.
    ElectricalDevice(uid="QTM000HAAA", tag="ED-M-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(ft(15, 10.5), ft(21, 11.625)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-MAIN", room="RM-M-STUDY", rotation=deg(0),
                     controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),

    # RM-M-BATH1: wet-rated can plus a mirror light over the lavatory, which backs onto
    # the room's north wall (FX-M-BATH1-LAV, plan/fixtures.py).
    ElectricalDevice(uid="QTM000JAAA", tag="ED-M-BATH1-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(m(0.959081), m(7.35676)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1",
                     controlled_by=("ED-M-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # y nudged +6" (2026-07-29), matching FX-M-BATH1-LAV's move for the BATH2 wall push.
    ElectricalDevice(uid="QTM000KAAA", tag="ED-M-BATH1-MIRROR", kind=DeviceKind.LIGHT,
                     position=pt(m(1.36284), m(6.89162)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1", rotation=deg(-180),
                     controlled_by=("ED-M-BATH1-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTM000MAAA", tag="ED-M-BATH1-SW", kind=DeviceKind.SWITCH,
                     # Moved north on the west wall after the toilet/lavatory moved to the
                     # south wall; the old 22'-3" location landed inside the toilet footprint.
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
                     position=pt(ft(0, 7.625), ft(16, 5.375)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2", rotation=deg(90),
                     controlled_by=("ED-M-BATH2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTM000RAAA", tag="ED-M-BATH2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(7, 7.625), ft(14)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-M-LAUNDRY / RM-M-CLOSET / RM-M-MUDROOM: 3" cans. Small rooms want a small
    # aperture — a 4" can in a 22 ft2 laundry is a headlamp.
    # Both cans moved with the closet line on 2026-08-03: the laundry's keeps its position
    # over the machines (+8", with them), the closet's re-centres on the widened corridor.
    ElectricalDevice(uid="QTM000SAAA", tag="ED-M-LAUNDRY-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(10, 8), ft(20, 2)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY",
                     controlled_by=("ED-M-LAUNDRY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000TAAA", tag="ED-M-LAUNDRY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 4.375), ft(21, 2)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTM000VAAA", tag="ED-M-CLOSET-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(15, 8)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000WAAA", tag="ED-M-CLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 4.375), ft(16, 10)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # room re-pointed to RM-M-MUD-CLOSET (2026-08-15), same correction CAN2 took
    # 2026-07-28: the 2026-08-02 closet conversion framed a room around this ceiling point
    # but the light kept naming the old mudroom (`integrity.placeable_room_mismatch`).
    # Nothing moves — a label catching up with a wall.
    ElectricalDevice(uid="QTM000XAAA", tag="ED-M-STORAGE-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(29)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-MUD-CLOSET",
                     controlled_by=("ED-M-STORAGE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # room re-pointed to RM-M-MECH (2026-07-28): its ceiling position now lands inside the
    # framed shaft closet carved out of the mudroom's north end, not the mudroom itself.
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
    ElectricalDevice(uid="QTM0013AAA", tag="ED-M-HALL-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 4.375), ft(22, 9)), type_ref="ED-T-SWITCH",
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
]

# --- Second storey --------------------------------------------------------------------
SECOND_LIGHTING = [
    # RM-S-HALL: the upstairs shadow gap, run as one polyline around three sides of the
    # hall — a cove that stops short of a corner reads as a mistake, so it turns instead.
    LightRun(uid="QRS0001AAA", tag="LR-S-HALL-GAP", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(18, 6), ft(9, 7)), pt(ft(18, 6), ft(30, 4)),
                   pt(ft(21, 6), ft(30, 4)), pt(ft(21, 6), ft(9, 7))),
             room="RM-S-HALL", psu_ref="ED-S-HALL-LT-PSU",
             controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    ElectricalDevice(uid="QTS0001AAA", tag="ED-S-HALL-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(20), ft(30, 6)), type_ref="ED-T-LT-PSU-200",
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
    ElectricalDevice(uid="QTS0005AAA", tag="ED-S-HALL-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 7.625), ft(10)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTS0006AAA", tag="ED-S-HALL-SW2", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 7.625), ft(26, 6)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-S-SUITE: the linear wall lamp the notes ask for over the bed, on the long west
    # wall, plus cans down the west strip and one in the arm past the walk-in.
    # Same 1 5/8" shift as ED-S-SUITE-RC5: W-S-SN1's south face came into the room when the
    # wall became the 8" staggered sound wall. Authored y was 22'-0 1/8" against the old face.
    ElectricalDevice(uid="QTS0007AAA", tag="ED-S-SUITE-LAMP", kind=DeviceKind.LIGHT,
                     position=pt(ft(4, 11.875), ft(21, 10.5)), type_ref="ED-T-LT-WALL-LINEAR",
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
    ElectricalDevice(uid="QTS000EAAA", tag="ED-S-SUITEBATH-MIRROR", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 10), ft(22, 0.625)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITEBATH", rotation=deg(180),
                     controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
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
                     position=pt(ft(1, 9), ft(25, 11.625)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-S-VANITY", rotation=deg(0),
                     controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTS000GAAA", tag="ED-S-VANITY-MIRROR2", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(25, 11.625)), type_ref="ED-T-LT-MIRROR",
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
                     position=pt(ft(9, 7.125), ft(31)), type_ref="ED-T-LT-MIRROR-RING",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1", rotation=deg(-90),
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6))),
    # Mirror is hardwired *and* gets an outlet behind it (electrical_notes.md line 80), so
    # a future replacement doesn't need an electrician. 54" sits inside the mirror's
    # 3'-6"..6'-6" band. GFCI at the receptacle, not just the breaker — 210.8(A)(1).
    ElectricalDevice(uid="QTS000MAAA", tag="ED-S-BATH1-RC-MIRROR",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 7.625), ft(31)), type_ref="ED-T-RECEPTACLE-GFCI",
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

    # Both switches moved x 17'-7 5/8" -> 17'-6 3/4" with the humid liner on W-S-C1
    # (2026-08-18): the wall's plant-room face came 1 1/4" west, and a switch authored to
    # the old face resolves inside the panel.
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
                     position=pt(ft(30, 9.875), ft(0, 8.625)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(180),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    ElectricalDevice(uid="QTS000WAAA", tag="ED-S-STUDY2-STAIR-SC1", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(8, 7.625)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(0),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
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
    # opening so it reads from both the stair and the landing. 4' assembly off the 9'
    # ceiling leaves the shade bottom 5' above the floor, clear of the landing and
    # reachable from the flight. All three name RM-S-HALL — landing, well and east hall
    # are one room since the centre line opened under BM-S-HALL.
    ElectricalDevice(uid="QTS0019AAA", tag="ED-S-LANDING-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(24, 4)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     controlled_by=("ED-S-LANDING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS001AAAA", tag="ED-S-STAIR-CHAND", kind=DeviceKind.LIGHT,
                     position=pt(m(4.26405), m(9.3355)), type_ref="ED-T-LT-CHANDELIER",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     controlled_by=("ED-S-STAIR-SW", "ED-S-LANDING-SW"),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(4))),
    # Moved twice as walls it rode came out; home is now W-S-SN3's north face at
    # y=22'-6 1/4", the wall you walk straight at off the flight — a two-gang box with
    # ED-S-LANDING-SW. Slid west to x=12' on 2026-07-28: ST-M2S now turns left, so the
    # throat is the well's west lane (x 10'-3 3/8"..13'-9 3/4"), and x=17' was a well's
    # width away from where you arrive.
    ElectricalDevice(uid="QTS001BAAA", tag="ED-S-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12), ft(22, 7.375)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]

# --- Attic ----------------------------------------------------------------------------
# The attic ceiling is the 4:12 cathedral off a 5' knee wall, so every ceiling fixture
# states its elevation: 5' + d/3, where d is the plan distance from the x=18' ridge.
# 9'-8" is x=22' or x=14'; 8'-0" is x=27' or x=9'. Sloped-ceiling trims, and the housings
# sit in the rafter bay rather than a joist bay.
ATTIC_LIGHTING = [
    # Was RM-A-DEN's: a 43 ft2 nook with no wall on the way in to put a switch on, so the
    # fixture carries its own (notes: "spotlight sconce with switch on sconce"). No
    # `controlled_by`, deliberately — `integral_switch` on the type exempts it from
    # `electrical.lighting_controls`. Back at x=14'-0" (2026-07-31) after WIN-A-S-JUL-W's
    # width settled at 18": the original position clears the window jamb by 1'-11".
    #
    # ** REASSIGNED TO RM-A-WEST-UNFIN 2026-08-27 ** when the Den was deleted and its space
    # folded into the west loft. Position, type, mount, elevation and circuit are all
    # unchanged — the wall it hangs on (the south gable at x=14'-0") did not move, only the
    # room claim around it did. The integral switch is kept: see the type's note.
    ElectricalDevice(uid="QTA0001AAA", tag="ED-A-DEN-SCONCE", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(0, 8.625)), type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST-UNFIN", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),

    ElectricalDevice(uid="QTA0002AAA", tag="ED-A-EAST-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0003AAA", tag="ED-A-EAST-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(15)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0004AAA", tag="ED-A-EAST-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),

    # RM-A-STUDY: the second of the notes' two studies. Its spot sconce goes on the knee
    # wall, which is only 5' tall — hence a 4' mount, not the 6' used downstairs. The
    # stair sconce lights ST-S2A's landing at the top of the flight.
    ElectricalDevice(uid="QTA0005AAA", tag="ED-A-STUDY-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(3)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY",
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0006AAA", tag="ED-A-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(ft(35, 3.375), ft(2, 3)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(-90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
    ElectricalDevice(uid="QTA0007AAA", tag="ED-A-STUDY-STAIR-SC", kind=DeviceKind.LIGHT,
                     position=pt(ft(35, 3.375), ft(7)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(-90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),

    # RM-A-WEST-UNFIN: 598 ft2 of media room under the west rake. Three cans down the ridge side
    # where the ceiling is high, one out at 8' toward the knee wall.
    ElectricalDevice(uid="QTA0008AAA", tag="ED-A-WEST-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST-UNFIN",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0009AAA", tag="ED-A-WEST-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(20)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST-UNFIN",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA000AAAA", tag="ED-A-WEST-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(30)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST-UNFIN",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA000BAAA", tag="ED-A-WEST-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(20)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST-UNFIN",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    # On W-A-C1B's west face at 6'-0", not W-A-C1's: the two segments are collinear, but
    # the centre wall south of y=5'-7" faces RM-A-STUDY, and RM-A-WEST-UNFIN does not start until
    # that line. A station 5" further south is a switch in the wrong room.
    ElectricalDevice(uid="QTA000CAAA", tag="ED-A-WEST-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7.625), ft(6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST-UNFIN", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]

# --- Garage ---------------------------------------------------------------------------
# Two 4' shop lights on their own switch by the service door, on the house's main lighting
# circuit (garage is freestanding but fed from ED-B-PANEL) rather than the GFCI receptacle
# circuit, which would drop the lights every time a tool trips one. Surface mounted at 8' —
# nothing above the garage ceiling to recess a can into.
GARAGE_LIGHTING = [
    ElectricalDevice(uid="QTG0001AAA", tag="ED-G-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(12), ft(48)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    ElectricalDevice(uid="QTG0002AAA", tag="ED-G-LT2", kind=DeviceKind.LIGHT,
                     position=pt(ft(12), ft(58)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # A third shop light over the service-door landing (2026-08-22). The two above are at
    # y=48' and y=58', the working half of the bay; the landing is at y 40'-6"..43'-6" and
    # the flight below it drops 2'-10" in five risers, and neither light reaches within
    # R303.8's 4'. Stepping off a 34" landing in the dark is the reason the rule exists.
    #
    # Nothing was asking until 2026-08-22 either: R303.8 grades `model.stairs`, and this
    # flight was five concrete `Slab`s. (It reads as an *exterior* stair rather than an
    # interior one because `_stair_is_indoors` asks whether a CONDITIONED room stands over
    # it, and the garage is deliberately unconditioned. R303.7 would want the same luminaire
    # here and not the switching, since five risers is under its six-riser threshold.)
    ElectricalDevice(uid="4PQRD03TG8", tag="ED-G-LT3", kind=DeviceKind.LIGHT,
                     position=pt(ft(6, 6), ft(42)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # On W-G-S's INTERIOR face, so it followed the wall 1" north on 2026-08-26 with the
    # catlin truss (plan/storeys/garage.py::GARAGE_Y_SOUTH), as it did 1/2" on 2026-08-23.
    ElectricalDevice(uid="QTG0003AAA", tag="ED-G-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 6), ft(41, 4.875)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # The garage-door light (2026-08-02): mark R, full-cutoff exterior sconce, on W-G-E's
    # outside face on the 4' pier south of the door (door runs y 45'..61'), clear of the
    # door panel. NO `room=`, deliberately — outside RM-GARAGE is how `electrical.
    # wet_location` / `advisory.dark_sky_lighting` know it's exterior. Elevation 7'-0" is
    # storey-relative (garage datum = stem top at 1'-10" over slab), so it sits 8'-10"
    # over the apron and its 9" housing still clears the 8'-0" top plate.
    ElectricalDevice(uid="QTG0004AAA", tag="ED-G-EXT-LT", kind=DeviceKind.LIGHT,
                     # 2026-08-20: was 24'-3 3/8". The garage wall lost its 3/8" rainscreen
                     # furring that day, so the cladding face — which is what a surface-mounted
                     # sconce screws to — came in 3/8" with it.
                     position=pt(ft(24, 3), ft(43)), type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-MAIN", rotation=deg(90),
                     controlled_by=("ED-G-EXT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
    # Its switch, inside, ganged beside ED-G-SW at the service door (D-G-SERVICE's east
    # jamb is at 6'-6"; the shop-light switch sits at 8'-6", this one 6" west of it) —
    # walk in, one reach turns on the shop lights and the apron light both.
    ElectricalDevice(uid="QTG0005AAA", tag="ED-G-EXT-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8), ft(41, 4.875)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]
