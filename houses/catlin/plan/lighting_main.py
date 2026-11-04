# haus: editable
# Catlin lighting — the MAIN storey's pantry, bedroom, study and baths.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
#
# Conventions (rotation, mounts, controlled_by, 24V PSUs, uids): plan/lighting_basement.py.

from .laundry_lighting_types import LAUNDRY_SUPPLY_MOUNT, LAUNDRY_TRACK_DROP

from typehaus import (
    DeviceKind,
    ConduitRun,
    ElectricalDevice,
    LightRun,
    Mount,
    MountKind,
    Service,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

MAIN_LIGHTING = [
    # --- RM-M-PANTRY's jamb channels (2026-10-30) ---------------------------------------
    # One per inside face of FURN-M-PANTRY-SHELVES' three uprights, 12".."84" AFF, centred 1"
    # behind the shelf front at y=34'-0 1/4". The ends are hosted on the side walls at the
    # 1/8" scribe plus the 3/4" ply. The centre pair are fixed to the gable at x=21'-4", with
    # no wall behind them, so they are FLOOR mounts at a stated height (a WALL mount must bear
    # on a wall face). All four are 24V on ED-M-PANTRY-LT-PSU and switch with it.
    ElectricalDevice(uid="2A635YS6VW", tag="ED-M-PANTRY-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-JAMB72", psu_ref="ED-M-PANTRY-LT-PSU",
                     room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C5B", face="right", distance_from_start=inch(11.25),
                         normal_gap=inch(0.875), rotation_offset=deg(0)))),
    ElectricalDevice(uid="4W9J90JKEH", tag="ED-M-PANTRY-LT2", kind=DeviceKind.LIGHT,
                     position=pt(inch(255.25), inch(408.25)), rotation=deg(-90),
                     type_ref="ED-T-LT-JAMB72", psu_ref="ED-M-PANTRY-LT-PSU",
                     room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.FLOOR, elevation=inch(12))),
    ElectricalDevice(uid="9H4SK1RZVM", tag="ED-M-PANTRY-LT3", kind=DeviceKind.LIGHT,
                     position=pt(inch(256.75), inch(408.25)), rotation=deg(90),
                     type_ref="ED-T-LT-JAMB72", psu_ref="ED-M-PANTRY-LT-PSU",
                     room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.FLOOR, elevation=inch(12))),
    ElectricalDevice(uid="GP9JMATM58", tag="ED-M-PANTRY-LT4", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-JAMB72", psu_ref="ED-M-PANTRY-LT-PSU",
                     room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-PAN-E", face="left", distance_from_start=inch(11.25),
                         normal_gap=inch(0.875), rotation_offset=deg(-180)))),
    # Their driver, surface-mounted over the case top above the gable at 90" AFF: reachable
    # from the top shelf, ventilated, and under the 8'-4" cold-water crossing. Since the
    # channels went to generic COB (2026-10-31), 4 x 18 W x 1.25 = 90 W: a 96 W Class 2 HLG,
    # on/off with the occupancy sensor (the pantry needs no dimming).
    ElectricalDevice(uid="DZVAFADH7Y", tag="ED-M-PANTRY-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-MAIN", room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(90)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1B", face="left", distance_from_start=inch(39),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # PIR-only occupancy sensor (Leviton ODS10-IDW) on the INSIDE face of W-M-PAN-E, in the
    # 8" strip ahead of the shelves: plate centre 4 1/2" north of the south wall finish,
    # box centre 56" AFF (clears the kitchen-side box at 46" in the same bay). The lens's
    # south half is masked so it sees along the shelves, not the kitchen. It switches the
    # driver's 120V, so all four channels.
    ElectricalDevice(uid="1M4ZM8DRWH", tag="ED-M-PANTRY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-OCC-PANTRY",
                     circuit="CKT-LT-MAIN", room="RM-M-PANTRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(56)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-PAN-E", face="left", distance_from_start=inch(6.76),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-M-BED (premium tier, 2026-10-31), on a 3-WAY with ED-M-BED-SW2 at D-M-BED2. A south
    # row at y=3'-4": ED-M-BED-LT (plan/mep_electrical) over the reading chair's lap, CAN5 a
    # gimbal washing the bookcases, CAN2 over the desk top ahead of the user. CAN3/CAN4 flank
    # the bed at y=8'-8", 52" either side of its centre and off the mattress, in the one bay
    # the ERV returns leave free. Two bed sconces replaced the north reading bar.
    ElectricalDevice(uid="QTM000EAAA", tag="ED-M-BED-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(16, 10.75), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000FAAA", tag="ED-M-BED-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(5, 1.875), ft(8, 8)), type_ref="ED-T-LT-CAN4-PREM",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000GAAA", tag="ED-M-BED-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 9.875), ft(8, 8)), type_ref="ED-T-LT-CAN4-PREM",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="2FXG2TPSRY", tag="ED-M-BED-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(9, 4), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The other end of the 3-way, on W-M-C1's bedroom face beside D-M-BED2. Since
    # 2026-10-05 that door hinges SOUTH at y=6'-9" and latches NORTH at y=9'-5", so the
    # switches moved to the north jamb: y=9'-11" leaves 4" from the box edge to the jamb,
    # outside the leaf. W-M-C1's bedroom paint plane is x=212.115".
    #
    # CKT-LT-MAIN, the same circuit as every can it switches. Both ends are plain
    # ED-T-LEV-SW3 3-ways (2026-10-31): the bed sconces are the low layer, not a dimmer.
    ElectricalDevice(uid="08SZS6SKK5", tag="ED-M-BED-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="left", distance_from_start=inch(119),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Two swing-arm sconces replaced the headboard bar and its switch (2026-10-31), one
    # each side of FURN-M-BED, ~44" off its centre (outside the mattress), on
    # BK-M-BDN1-SCONCE / BK-M-BDN2-SCONCE. J1, the WAC Sprig, since 2026-11-02: each
    # switches at its canopy toggle. The west box stays west of PR-B-CW-HYD-RISER in W-M-BDN1
    # at x=6'-0"; the east one's body stays west of ED-M-BED-SW's box (centre x=13'-8").
    ElectricalDevice(uid="K18FY9C6C0", tag="ED-M-BED-SCONCE-W", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SPOT-SW", circuit="CKT-LT-MAIN", room="RM-M-BED",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(49)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN1", face="right", distance_from_start=inch(69),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="NT2TZWZ8E0", tag="ED-M-BED-SCONCE-E", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SPOT-SW", circuit="CKT-LT-MAIN", room="RM-M-BED",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(49)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN2", face="right", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # ** THE BEDROOM FAN (2026-09-20), AND IT REVIVES MARK N RATHER THAN ADDING A TYPE. **
    # ED-T-LT-FAN52 has been catalog-only since ED-B-GYM-LT retyped to the N3 hugger for
    # blade headroom, and its own comment names a downrod placement as what it is kept for.
    # This is that placement: RM-M-BED's resolved clear_height_m is 2.69875 = 8'-10 1/4",
    # so N's 18" assembly leaves the blades at 7'-4 1/4" — 4 1/4" over the 7'-0"
    # blade-to-floor minimum every fan IFU states. ** NOTHING GRADES THAT: ** there is no
    # blade-to-floor check in the engine, so this comment and the type's `height` are the
    # only guard, exactly as on ED-B-GYM-LT.
    #
    # TRUE ROOM CENTRE. The clear face runs x 0.635"..215.365", y 0.635"..155.365", so
    # (9'-0", 6'-6") is the centre of it to the sixteenth. The cans (a south row at y=3'-4",
    # CAN3/CAN4 at y=8'-8") are deliberately NOT centred on it: the fan is the thing a person
    # looks up at. The 26" sweep clears the nearest can centre (CAN5 at (9'-4", 3'-4")) by
    # ~12" and every wall by 6'-0"+. REG-M-SUP3 moved 2'-0"
    # west for this (plan/mep_registers.py) — it sat on the room seed, 6" away, which is a
    # canopy-on-register overlap nothing in the engine would have reported.
    #
    # ** CONSTANT HOT, AND THE SWITCH IS A PLAIN ED-T-LEV-SW1, NOT A DIMMER. ** Mark N's
    # `source` says in capitals that a DC fan cannot be speed-controlled by a conventional
    # wall dimmer and that a Caseta dimmer will corrupt its receiver. The fan gets its own
    # leg and its own plain switch; speed and light are the hardwired Bluetooth wall control
    # plus the remote.
    # CKT-LT-MAIN, the same circuit as the load it switches — a switch on another circuit
    # than its load FAILs electrical.lighting_controls (NEC 210.7).
    ElectricalDevice(uid="SFVAJZ0YEM", tag="ED-M-BED-FAN", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(6, 6)), type_ref="ED-T-LT-FAN52",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-FAN-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(18))),
    # Second gang beside ED-M-BED-SW2 at D-M-BED2, the room's entry from the living room,
    # on the house's 4" gang spacing (ED-M-LIVING-SW's second gang, ED-M-PORCH-FLOOD-SW).
    # NORTH of it since 2026-10-05, away from the latch jamb, at y=10'-3".
    ElectricalDevice(uid="KCDD6WVW46", tag="ED-M-BED-FAN-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="left", distance_from_start=inch(123),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-M-STUDY-CLOSET has no exterior wall, so the notes' "sconce to the side of the window"
    # applies to the two studies that do (RM-S-STUDY2, RM-A-STUDY). This one gets a down
    # spot for the desk, over a general can.
    #
    # ** ON THE EAST WALL, NOT THE NORTH. ** A spot on the north wall (behind
    # FURN-M-STUDY-DESK, which faces south from the south wall) would be a BACKLIGHT — a
    # silhouette on camera — bright against WP-M-STUDY-FELT, the backdrop the camera sees.
    # The south wall is out too: a 20"-deep desk puts a monitor in front of it.
    #
    # So: the EAST wall's north sliver, the 11 13/16" of W-M-C3 north of D-M-STUDY's derived RO
    # (y 21'-1 13/16"..22'-1 5/8"). x is 2" — half this type's 4" depth — off that wall's
    # resolved study face at 17'-8 5/8", per the face-position convention in
    # plan/electrical.py. `rotation=deg(-90)` backs it onto the east wall and aims it west.
    # ED-M-STUDY-SW is on the same sliver at 48", so the two are vertically clear.
    #
    # The booth is a facing pair — FURN-M-STUDY-BENCH along the north wall,
    # FURN-M-STUDY-DESK in the SW corner — so the occupant sits with their back to the
    # north wall and faces south, and the camera on the desk looks north at them. From
    # (17'-6 5/8", 21'-8 1/2") at 6'-0" this is a SIDE key about 3'-0" off their left cheek,
    # aimed across the bench: off the backdrop, not behind the subject, not competing with a
    # monitor. It is above the bench's east end (seat 18") with 4'-6" of clear, so nothing
    # standing on the bench reaches it.
    #
    # REG-M-SUP4 is in the CEILING three feet over it at (17'-2", 20'-8") — 4 5/8" west and
    # 12 1/2" south of directly above; its ceiling grille stays on a joist-bay line,
    # which already holds this fitting and a switch. The room's stale-air pickup is LOW, on
    # the south wall's east end: the east wall below this sconce is D-M-STUDY's rough
    # opening down to 21'-0 11/16" and FURN-M-STUDY-BENCH from there to the corner. See
    # plan/mep_registers.py for both.
    #
    # ** KEEP AT LEAST ONE OF THIS AND ED-M-STUDY-LT. ** RM-M-STUDY-CLOSET is windowless and
    # passes `code.R303_1_light_and_ventilation` only on Exception 1's electric-light
    # substitute: 787 lm (500 can + 287 spot) over its 16 sf is 23.6 fc against 6 (LightRun
    # coves are excluded by `_room_lumens`). Either alone still passes; neither is a FAIL.
    ElectricalDevice(uid="QTM000HAAA", tag="ED-M-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET", controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="left", distance_from_start=inch(45.5),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-M-BATH1: one can over the lavatory, 22" off the mirror wall and east of the ERV
    # trunk, plus the mirror light; the basin backs onto the shared south wet wall
    # (FX-M-BATH1-LAV, plan/fixtures.py). No shower, so mark A.
    ElectricalDevice(uid="QTM000JAAA", tag="ED-M-BATH1-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(4, 6.5), ft(24, 5.5)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1",
                     controlled_by=("ED-M-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000MAAA", tag="ED-M-BATH1-SW", kind=DeviceKind.SWITCH,
                     # East wall, south of the north-shifted doorway, 3/16" clear of the
                     # door's 1 1/2" bath-face casing (2026-10-29).
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BAE", face="right", distance_from_start=inch(41.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # RM-M-BATH2: two layers, two controls (2026-10-12, notes/bath2_lighting.md).
    # DAY, 5000 K on a plain toggle (ED-M-BATH2-SW-DAY): three B1 cans and the P3 make-up
    # Karlie task light (plan/mirrors.py). EVENING, 2700 K on ED-M-BATH2-SW-EVE:
    # the B2 shower can and the E3 tub cove off ED-M-BATH2-PSU (16.5 W on the 60 W OMNIDRIVE
    # X, which has no minimum load). NIGHT: RC1's guide light (2026-11-03). The Halo Plus uses
    # its own touch dimmer and unswitched plug power (2026-10-22). CAN1 is the vanity can, 23" off
    # the mirror; CAN2 is centred on the tub. The radiant-floor stat ED-M-BATH2-FH-STAT is a
    # separate control and switches none of this.
    ElectricalDevice(uid="QTM000NAAA", tag="ED-M-BATH2-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(2, 6), ft(15, 4)), type_ref="ED-T-LT-CAN4-WET-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     controlled_by=("ED-M-BATH2-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000PAAA", tag="ED-M-BATH2-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(6, 6.5), ft(19, 4)), type_ref="ED-T-LT-CAN4-WET-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     controlled_by=("ED-M-BATH2-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Inside the glass in the y 176"-192" bay, clear of the truss chords.
    ElectricalDevice(uid="N45GBJ06HG", tag="ED-M-BATH2-CAN-SH", kind=DeviceKind.LIGHT,
                     position=pt(ft(5, 3), ft(15, 4)), type_ref="ED-T-LT-CAN4-WET-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     controlled_by=("ED-M-BATH2-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="5KYF1YKZM6", tag="ED-M-BATH2-CAN-SH-EVE", kind=DeviceKind.LIGHT,
                     position=pt(ft(6), ft(15, 4)), type_ref="ED-T-LT-CAN4-WET-2700",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     controlled_by=("ED-M-BATH2-SW-EVE",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Over the tub, in the ceiling's shadow gap at W-M-BA2E's face, north of the glass to
    # HS1: the LR-M-LIVING-* idiom, fixed to the board. It replaced the deck-nosing run
    # LR-M-BATH2-TUBDECK (owner, 2026-10-22: no LEDs near the floor). 5.5 ft against the
    # old 5.4, so the PSU line stands. Damp-rated E3, as NEC 410.10(D) wants within 8' of
    # the rim. Clear of the cans and the towel bars at 55".
    LightRun(uid="WEQM9XB2MM", tag="LR-M-BATH2-TUB-CLG", type_ref="ED-T-LT-STRIP24-2700",
             path=(pt(inch(94.4375), inch(196)), pt(inch(94.4375), inch(262))),
             room="RM-M-BATH2", psu_ref="ED-M-BATH2-PSU",
             controlled_by=("ED-M-BATH2-SW-EVE",), emission_side="right",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # In the ceiling's y 192"-208" bay, outside the shower zone and off the extract trunk.
    ElectricalDevice(uid="ESWYM2QANP", tag="ED-M-BATH2-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(2, 6), ft(16, 8)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.CEILING)),
    # A 2-gang over the vanity's south end: day toggle (the old ED-M-BATH2-SW, same uid)
    # and the evening toggle 4" west. A third gang does not fit: ED-M-BATH2-FH-STAT is at
    # x 9 3/4"-13 3/4" and D-M-BATH2's casing starts ~22".
    ElectricalDevice(uid="QTM000RAAA", tag="ED-M-BATH2-SW-DAY", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN1", face="left", distance_from_start=inch(19.71875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="EDGKW1FCES", tag="ED-M-BATH2-SW-EVE", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN1", face="left", distance_from_start=inch(15.71875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The rail is north of the tall machine body: both task axes remain clear of it.
    # Surface mounting leaves the existing ceiling ducts and framing intact.
    ElectricalDevice(uid="QTM000SAAA", tag="ED-M-LAUNDRY-TRACK", kind=DeviceKind.LIGHT,
                     position=pt(inch(130.7), inch(258)), type_ref="ED-T-LT-TRACK-LAUNDRY",
                     psu_ref="ED-M-LAUNDRY-PSU", room="RM-M-LAUNDRY",
                     controlled_by=("ED-M-LAUNDRY-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=LAUNDRY_TRACK_DROP)),
    ElectricalDevice(uid="QTM02YAAAA", tag="ED-M-LAUNDRY-PSU", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-LT-PSU-PUREEDGE-40", circuit="CKT-LT-MAIN",
                     room="RM-M-LAUNDRY", controlled_by=("ED-M-LAUNDRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=LAUNDRY_SUPPLY_MOUNT),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BA2E", face="left", distance_from_start=inch(11),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Class 2 surface feed: above the accessible supply, then along the ceiling to the
    # west end canopy. Its upper surface stays below 108"; no ceiling bay is disturbed.
    ConduitRun(uid="QRM02YAAAA", tag="CR-M-LAUNDRY-24V",
               from_ref="ED-M-LAUNDRY-PSU", to_ref="ED-M-LAUNDRY-TRACK",
               service=Service.POWER_24, trade_size=inch(0.5),
               path=(pt(inch(104.815), inch(257)), pt(inch(104.815), inch(257.5)),
                     pt(inch(112.7), inch(257.5)), pt(inch(112.7), inch(258))),
               elevations=(inch(90.37), inch(107.5), inch(107.5), inch(107.5))),
    # ** BOTH THESE SWITCHES FOLLOW W-M-BA2E's FACE, AND IT MOVED (2026-09-09). ** The bath2
    # east line went 2" east and the W-M-BA2E2 jog came off, so ONE finished face at
    # x=101 3/8" now serves both — 99 3/8" and 106 3/4" before. A wall device's footprint is
    # CENTRED on its position, so a 2"-deep switch sits at 102 3/8", half its body off the
    # face. Left where they were, one buried 2 13/16" into the studs and the other floated
    # 5 3/8" into the room, and `haus check` graded neither.
    ElectricalDevice(uid="QTM000TAAA", tag="ED-M-LAUNDRY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BA2E", face="left", distance_from_start=inch(14),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]
