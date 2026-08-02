# haus: editable
# Catlin lighting layout — every luminaire, LED run, 24V supply and lighting control,
# room by room, from the "Lighting Notes" section of plans/electrical_notes.md.
#
# `# haus: editable` is REQUIRED here, not stylistic: ElectricalDevice is a UI-movable
# element, and the loader raises `loader.uneditable_movable_element` (a hard build error)
# for one authored in a plain module. The type catalog these reference is the non-editable
# plan/lighting_types.py — it uses frozenset, which this dialect forbids.
#
# Sixteen generic ED-T-LIGHT fixtures used to stand one per room in plan/mep.py. They are
# not deleted: each was re-typed in place to the real fixture its room wants, so its uid —
# and therefore its IFC GlobalId — survives. Everything below is what was *added* around
# them. ED-T-LIGHT itself is retired; every light in the house now names a real product
# with a schedule mark, the garage's shop lights included.
#
# Conventions used throughout:
# - Rotation names the wall a fixture backs onto: deg(0) north, deg(90) west,
#   deg(180) south, deg(-90) east. (Local +y is the object's back — the same rule the
#   kitchen casework in plan/placeables.py follows.)
# - `Mount(CEILING, recessed_into_host_surface=True)` with no elevation puts a can's base
#   on the ceiling plane and its housing in the joist bay above — which is what recessed
#   means. Attic cans state an elevation because the ceiling there is a 4:12 cathedral off
#   a 5' knee wall: its height is 5' + d/3 where d is the distance from the x=18' ridge.
# - `Mount(CEILING, drop=<the type's height>)` lands a hanging fixture's canopy on the
#   ceiling; the type's height is the whole assembly, so the shade bottom is ceiling minus
#   that number (→ model/placeable_symbols/lighting.pendant).
# - `controlled_by` names the switch(es) on the *load*, because a switch usually drives
#   several fixtures and a fixture is what a plan reader looks up. Two tags is a 3-way
#   pair. A fixture whose type carries `integral_switch` names none, by design.
# - 24V runs carry no `circuit`: their PSU does. The PSU is a JUNCTION_BOX device, sized
#   at 1.25 x the connected tape watts and checked by `electrical.light_run_psu`.
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
                     position=pt(ft(16), ft(17, 7)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP", rotation=deg(0),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-FURNACE: same panels. This is the room the electrician and the plumber work in.
    ElectricalDevice(uid="QTB0008AAA", tag="ED-B-FURNACE-PANEL1", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(23)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    ElectricalDevice(uid="QTB0009AAA", tag="ED-B-FURNACE-PANEL2", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(32)), type_ref="ED-T-LT-PANEL",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(1.5))),
    ElectricalDevice(uid="QTB000AAAA", tag="ED-B-FURNACE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 7), ft(20)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-PLAY-N is the theatre. Up/down sconces on the east wall are the traditional
    # answer (notes) and the dimmer is the whole point: bright enough to cross the room,
    # dark enough to watch something. Two cans on the same dimmer are the cleaning light.
    ElectricalDevice(uid="QTB000BAAA", tag="ED-B-PLAY-N-SCONCE1", kind=DeviceKind.LIGHT,
                     position=pt(ft(35, 7), ft(24)), type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(-90),
                     controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTB000CAAA", tag="ED-B-PLAY-N-SCONCE2", kind=DeviceKind.LIGHT,
                     position=pt(ft(35, 7), ft(30)), type_ref="ED-T-LT-SCONCE-UD",
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
    # Cans 3 and 4 (2026-08-01, code.R303_1_light_and_ventilation). This room has no glazing
    # at all, so it is habitable only under R303.1 Exception 1, and the exception's first half
    # is 6 footcandles average at the work plane. Two sconces and two cans is 3,200 lm, which
    # over 324 sf estimates 4.7 fc — short. Two more cans put it at 5,000 lm / 7.4 fc with
    # margin to spare, and the room ends up on the same four-can grid RM-B-GYM already runs
    # at the same 324 sf. On the same dimmer as the other four fixtures: the whole point of
    # this room is that all of it goes down together, and a code minimum is a *capability*,
    # not a setting anyone has to sit under.
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
                     position=pt(ft(18, 5), ft(20)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-B-STAIR: the railing light the notes ask for. A 24V tape at 34" on the stair's
    # west wall, under the handrail — it lights the treads without a fixture in anyone's
    # eyeline coming up. 3-way with the main-storey stair switch, because a stair light
    # that can only be switched from the bottom is a stair light nobody uses.
    LightRun(uid="QRB0001AAA", tag="LR-B-STAIR-RAIL", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(10, 7), ft(25, 5)), pt(ft(10, 7), ft(34, 10))),
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
    ElectricalDevice(uid="QTB000HAAA", tag="ED-B-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(10, 5), ft(23)), type_ref="ED-T-SWITCH",
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

    # RM-B-BATH (2026-07-30). One can and one switch, on the same CKT-LT-BACKUP the rest of
    # the stair block is on — deliberately, so the light at the bottom of the stair and the
    # light in the room off it both stay lit when the backup panel is carrying the house.
    # The can is centred over the room's length at x=14', clear of the exhaust terminal over
    # the WC at 11'-8". The switch is inside the room on the partition beside the door's latch
    # jamb (the leaf swings out, so the switch is behind you as you enter, not behind the leaf).
    ElectricalDevice(uid="QTB000KAAA", tag="ED-B-BATH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(20)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH",
                     controlled_by=("ED-B-BATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB000LAAA", tag="ED-B-BATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(15, 8), ft(21, 4)), type_ref="ED-T-SWITCH",
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
    # The daylight set: mark A1, the same 4" can with its module set to 4000K, on its own
    # switch leg so the lounge can be run warm in the evening and cool when it is being
    # worked in. Interleaved as a diamond inside the warm 2x2 — points at the mid-span of
    # each side, all symmetric about (27', 7') — so either set alone still lights the room
    # evenly instead of lighting half of it. Same CKT-LT-MAIN as the warm cans: this is
    # 48 VA more on a lighting branch, and it is the switch leg, not the circuit, that has
    # to be separate for the two colours to be usable independently.
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
                     position=pt(ft(26, 4), ft(12)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),

    # The dining fixture, centred on FURN-M-DINING. A 3'-6" assembly off a 9' ceiling puts
    # the shade bottom at 5'-6" — about 3' over a 30" table, which is the height that lights
    # the table without blocking the person across it.
    ElectricalDevice(uid="QTM0005AAA", tag="ED-M-DINING-PEND", kind=DeviceKind.LIGHT,
                     position=pt(ft(26, 11), ft(17, 4)), type_ref="ED-T-LT-PENDANT",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-DINING-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(3, 6))),
    ElectricalDevice(uid="QTM0006AAA", tag="ED-M-DINING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 5), ft(16)), type_ref="ED-T-SWITCH-DIM",
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
    ElectricalDevice(uid="QTM0009AAA", tag="ED-M-KITCH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(22, 6), ft(33, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000AAAA", tag="ED-M-KITCH-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(30, 6), ft(33, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Over the sink at (34'-5", 32'-8").
    ElectricalDevice(uid="QTM000BAAA", tag="ED-M-KITCH-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 3), ft(32, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000CAAA", tag="ED-M-KITCH-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 3), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000DAAA", tag="ED-M-KITCH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 5), ft(24, 6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING", rotation=deg(90),
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
                     position=pt(ft(17, 7), ft(19, 6)), type_ref="ED-T-LT-SCONCE-SPOT",
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
    # y nudged +6" (2026-07-29), matching FX-M-BATH1-LAV's move for the BATH2 wall push.
    ElectricalDevice(uid="QTM000KAAA", tag="ED-M-BATH1-MIRROR", kind=DeviceKind.LIGHT,
                     position=pt(m(1.36284), m(6.84082)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1", rotation=deg(-180),
                     controlled_by=("ED-M-BATH1-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTM000MAAA", tag="ED-M-BATH1-SW", kind=DeviceKind.SWITCH,
                     # Moved north on the west wall after the toilet/lavatory moved to the
                     # south wall; the old 22'-3" location landed inside the toilet footprint.
                     position=pt(m(1.71265), m(7.83151)), type_ref="ED-T-SWITCH",
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
                     position=pt(ft(0, 5), ft(18)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2", rotation=deg(90),
                     controlled_by=("ED-M-BATH2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTM000RAAA", tag="ED-M-BATH2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(7, 7), ft(14)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-M-LAUNDRY / RM-M-CLOSET / RM-M-MUDROOM: 3" cans. Small rooms want a small
    # aperture — a 4" can in a 22 ft2 laundry is a headlamp.
    ElectricalDevice(uid="QTM000SAAA", tag="ED-M-LAUNDRY-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(10, 8), ft(19, 6)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY",
                     controlled_by=("ED-M-LAUNDRY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000TAAA", tag="ED-M-LAUNDRY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 5), ft(21, 2)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTM000VAAA", tag="ED-M-CLOSET-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(15, 5)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000WAAA", tag="ED-M-CLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 5), ft(16, 10)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTM000XAAA", tag="ED-M-STORAGE-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(29)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
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
                     position=pt(ft(9, 7), ft(27)), type_ref="ED-T-SWITCH",
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
    # West end of the run, on W-M-BAE's hall face just south of D-M-BATH1 (the door spans
    # y 23'-4" to 25'-4", so this is the only piece of that wall a plate fits on). Moved here
    # 2026-07-31: it was authored at x=4'-5", which is 1'-7" *inside* RM-M-BATH1 — the wall
    # is at x=6'-0" — so the hall's west 3-way was on the wrong side of the bathroom wall and
    # `integrity.placeable_room_mismatch` had been reporting it. rotation 90 faces it east
    # into the hall, which is what it always meant.
    ElectricalDevice(uid="QTM0013AAA", tag="ED-M-HALL-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 4.5), ft(22, 9)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTM0014AAA", tag="ED-M-HALL-SW2", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7), ft(22, 3)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING", rotation=deg(-90),
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
                     position=pt(ft(10, 5), ft(28)), type_ref="ED-T-SWITCH",
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
                     position=pt(ft(8, 9), ft(-1.25)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", rotation=deg(90),
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
                     position=pt(ft(21, 7), ft(10)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    ElectricalDevice(uid="QTS0006AAA", tag="ED-S-HALL-SW2", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 7), ft(26, 6)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

    # RM-S-SUITE: the linear wall lamp the notes ask for over the bed, on the long west
    # wall, plus cans down the west strip and one in the arm past the walk-in.
    ElectricalDevice(uid="QTS0007AAA", tag="ED-S-SUITE-LAMP", kind=DeviceKind.LIGHT,
                     position=pt(m(1.52039), m(6.71945)), type_ref="ED-T-LT-WALL-LINEAR",
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
                     position=pt(ft(9, 11), ft(11, 11)), type_ref="ED-T-SWITCH",
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
                     position=pt(m(4.2162), m(6.70351)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITEBATH", rotation=deg(180),
                     controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    # The lit shower niche (plans/TODO.md §Plumbing: "Have lighting in the shower niche of
    # master bedroom, it looks cool, Schluter-KERDI-BOARD-SNLT").
    #
    # It goes in W-S-C2C, the east wall FX-S-SUITEBATH-TUBSH's alcove backs onto — the one
    # wall of the alcove that is neither the room's glazed south side nor a door. The tape
    # is 2'-4" of the 28"-wide niche's head channel, centred on the alcove's y 17'-0"..22'-0"
    # at y=19'-6", so it lights the shelf from above rather than glaring out of it.
    # x=17'-9" is the recess face, 3" proud of the wall centre line.
    #
    # Head at 5'-0": the niche sill sits at 4'-0", which clears the tub deck by 2'-4" and
    # puts a bottle at hand height standing up, and the channel is at its 1'-0" head.
    #
    # 24V like every other tape in the house, so it has no branch circuit of its own — its
    # driver does. 2'-4" at 3 W/ft is 7 W; the 60 W supply is the smallest catalog size and
    # it sits in the ceiling above, outside the shower zone, where it can be serviced.
    LightRun(uid="QRS0004AAA", tag="LR-S-NICHE", type_ref="ED-T-LT-NICHE-SNLT",
             path=(pt(ft(17, 9), ft(18, 4)), pt(ft(17, 9), ft(20, 8))),
             room="RM-S-SUITEBATH", psu_ref="ED-S-NICHE-PSU",
             controlled_by=("ED-S-SUITEBATH-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="QTS000E1AA", tag="ED-S-NICHE-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(16, 6), ft(21, 6)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITEBATH",
                     mount=Mount(kind=MountKind.CEILING)),

    # RM-S-VANITY: two lavatories, two mirror lights, both on the north wet wall.
    ElectricalDevice(uid="QTS000FAAA", tag="ED-S-VANITY-MIRROR1", kind=DeviceKind.LIGHT,
                     position=pt(ft(1, 9), ft(26, 1)), type_ref="ED-T-LT-MIRROR",
                     circuit="CKT-LT-UPPER", room="RM-S-VANITY", rotation=deg(0),
                     controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6))),
    ElectricalDevice(uid="QTS000GAAA", tag="ED-S-VANITY-MIRROR2", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(26, 1)), type_ref="ED-T-LT-MIRROR",
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
                     position=pt(ft(9, 9), ft(31)), type_ref="ED-T-LT-MIRROR-RING",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1", rotation=deg(-90),
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6))),
    # The mirror is hardwired *and* gets an outlet behind it (electrical_notes.md line 80):
    # a lit mirror is the one bathroom fixture people replace on a whim, and a blank wall
    # box behind the next one is the difference between an afternoon and an electrician.
    # 54" puts it inside the 3'-6"..6'-6" band the mirror covers. GFCI at the breaker is
    # not enough here — 210.8(A)(1) wants the *receptacle* protected in a bathroom.
    ElectricalDevice(uid="QTS000MAAA", tag="ED-S-BATH1-RC-MIRROR",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 10), ft(31)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND", room="RM-S-BATH1", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54))),
    ElectricalDevice(uid="QTS000NAAA", tag="ED-S-BATH1-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(9, 9), ft(29, 6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),

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
                     position=pt(m(7.30459), m(0.225468)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(180),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    ElectricalDevice(uid="QTS000VAAA", tag="ED-S-STUDY2-SPOT2", kind=DeviceKind.LIGHT,
                     position=pt(m(9.7904), m(0.228557)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(180),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
    ElectricalDevice(uid="QTS000WAAA", tag="ED-S-STUDY2-STAIR-SC1", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(8, 9)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", rotation=deg(0),
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="QTS000XAAA", tag="ED-S-STUDY2-STAIR-SC2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(8, 9)), type_ref="ED-T-LT-SCONCE-STAIR",
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

    # The landing end of RM-S-HALL + the stairwell chandelier. The chandelier hangs over
    # the ST-M2S opening, so it is seen from the stair and from the landing at once —
    # which is the whole reason a stairwell is the one place a house puts a chandelier.
    # Its 4' assembly off the 9' ceiling leaves the shade bottom 5' above the second
    # floor, well clear of anything on the landing and reachable from the flight for a
    # lamp change. All three now name RM-S-HALL: the landing, the well and the east hall
    # are one room since the centre line opened up under BM-S-HALL.
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
    # Moved off the centre wall's stair-side face (17'-7", 26'-0") when that wall came out,
    # then off W-S-BD-N2 when *that* came out with O-S-STAIRTOP. Its home is W-S-SN3's
    # north face at y=22'-6 1/4" — the wall you walk straight at stepping south off the
    # flight — one two-gang box with ED-S-LANDING-SW (plan/mep.py), which moves with it.
    # Slid west from x=17' on 2026-07-28: ST-M2S turns left now, so the throat you step out
    # of is the well's *west* lane (x 10'-3 3/8"..13'-9 3/4") and x=12' is what that lane
    # walks at. At x=17' the switch was a well's width away from where you arrive.
    ElectricalDevice(uid="QTS001BAAA", tag="ED-S-STAIR-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12), ft(22, 7)), type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]

# --- Attic ----------------------------------------------------------------------------
# The attic ceiling is the 4:12 cathedral off a 5' knee wall, so every ceiling fixture
# states its elevation: 5' + d/3, where d is the plan distance from the x=18' ridge.
# 9'-8" is x=22' or x=14'; 8'-0" is x=27' or x=9'. Sloped-ceiling trims, and the housings
# sit in the rafter bay rather than a joist bay.
ATTIC_LIGHTING = [
    # RM-A-DEN: a 43 ft2 nook with no wall on the way in to put a switch on, so the
    # fixture carries its own (notes: "upper wall spotlight sconce for task lighting with
    # switch on sconce"). Naming no `controlled_by` is deliberate and `integral_switch`
    # on the type is what exempts it from `electrical.lighting_controls`.
    # Moved to x 13'-0" and back to x 14'-0" on 2026-07-31: WIN-A-S-JUL-W was briefly 32"
    # wide with its west jamb at x 14'-8", which left 8" to the sconce and crowded it
    # against the charcoal casing and the interior jamb extension. Narrowing the pair to
    # 18" put that jamb at x 15'-11", so the original position has 1'-11" of clearance —
    # more than the 20" the temporary move bought — and the sconce goes back on the Den's
    # own centre line.
    ElectricalDevice(uid="QTA0001AAA", tag="ED-A-DEN-SCONCE", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(0, 5)), type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-UPPER", room="RM-A-DEN", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),

    ElectricalDevice(uid="QTA0002AAA", tag="ED-A-EAST-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0003AAA", tag="ED-A-EAST-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(15)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0004AAA", tag="ED-A-EAST-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST",
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
                     position=pt(ft(35, 6), ft(3)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(-90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
    ElectricalDevice(uid="QTA0007AAA", tag="ED-A-STUDY-STAIR-SC", kind=DeviceKind.LIGHT,
                     position=pt(ft(35, 6), ft(7)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(-90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),

    # RM-A-WEST: 598 ft2 of media room under the west rake. Three cans down the ridge side
    # where the ceiling is high, one out at 8' toward the knee wall.
    ElectricalDevice(uid="QTA0008AAA", tag="ED-A-WEST-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0009AAA", tag="ED-A-WEST-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(20)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA000AAAA", tag="ED-A-WEST-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(30)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA000BAAA", tag="ED-A-WEST-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(20)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST",
                     controlled_by=("ED-A-WEST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA000CAAA", tag="ED-A-WEST-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7), ft(6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-WEST", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]

# --- Garage ---------------------------------------------------------------------------
# Two 4' shop lights on their own switch by the service door, on the house's main lighting
# circuit — the garage is freestanding but fed from ED-B-PANEL, and putting the light on the
# GFCI-protected receptacle circuit would mean losing it every time a tool trips one.
# Surface mounted at 8', which is the garage's ceiling: there is nothing above it to recess
# a can into.
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
    ElectricalDevice(uid="QTG0003AAA", tag="ED-G-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8, 6), ft(41, 3)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-GARAGE", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]
