# haus: editable
# Catlin lighting — the MAIN storey's pantry, bedroom, study and baths.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
#
# Conventions (rotation, mounts, controlled_by, 24V PSUs, uids): plan/lighting_basement.py.

from .laundry_lighting_types import LAUNDRY_TRACK_DROP

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
from typehaus.model import Location, WallAttachment

MAIN_LIGHTING = [
    # --- RM-M-PANTRY's jamb channels (2026-10-30; centre pair retired 2026-11-20) ------
    # One per end upright's inside face of FURN-M-PANTRY-SHELVES, 12".."84" AFF, centred 1"
    # behind the shelf front at y=34'-0 1/4", facing each other across the open 72" bay
    # (the gable that shaded it is now a strut post). Hosted on the side walls at the 1/8"
    # scribe plus the 3/4" ply; 24V on ED-M-PANTRY-LT-PSU, switched with it. Fallback if
    # wanted: a pair on the strut post's side faces. LT2 (4W9J90JKEH) and LT3 (9H4SK1RZVM)
    # are those retired GlobalIds.
    ElectricalDevice(uid="2A635YS6VW", tag="ED-M-PANTRY-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-JAMB72", psu_ref="ED-M-PANTRY-LT-PSU",
                     room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C5B", face="right", distance_from_start=inch(11.25),
                         normal_gap=inch(0.875), rotation_offset=deg(0)))),
    ElectricalDevice(uid="GP9JMATM58", tag="ED-M-PANTRY-LT4", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-JAMB72", psu_ref="ED-M-PANTRY-LT-PSU",
                     room="RM-M-PANTRY", controlled_by=("ED-M-PANTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-PAN-E", face="left", distance_from_start=inch(11.25),
                         normal_gap=inch(0.875), rotation_offset=deg(-180)))),
    # Their driver, surface-mounted over the case top above the strut post at 90" AFF:
    # reachable from the top shelf, ventilated, and under the 8'-4" cold-water crossing.
    # 2 x 18 W x 1.25 = 45 W on a 96 W Class 2 HLG: oversized since the centre pair went,
    # kept as authored. On/off with the occupancy sensor (the pantry needs no dimming).
    ElectricalDevice(uid="DZVAFADH7Y", tag="ED-M-PANTRY-LT-PSU", kind=DeviceKind.LED_DRIVER,
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
    # driver's 120V, so both channels.
    ElectricalDevice(uid="1M4ZM8DRWH", tag="ED-M-PANTRY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-OCC-PANTRY", box_use="bracket",
                     circuit="CKT-LT-MAIN", room="RM-M-PANTRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(56)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-PAN-E", face="left", distance_from_start=inch(6.76),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-M-BED (premium tier, 2026-10-31), on a 3-WAY with ED-M-BED-SW2 at D-M-BED2. All five
    # cans are symmetric about the bed axis x=9'-5 7/8". South row at y=3'-4" (joist mid-bay):
    # CAN6 the STRANDMON's reading light, CAN5 a gimbal washing the bookcases, CAN2 over the
    # desk top ahead of the user. CAN3/CAN4 flank the bed at y=8'-8", 52" either side of its
    # centre and off the mattress, in the one bay the ERV returns leave free. Two bed sconces
    # replaced the north reading bar.
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
                     position=pt(ft(9, 5.875), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="R7WHQQE70G", tag="ED-M-BED-CAN6", kind=DeviceKind.LIGHT,
                     position=pt(ft(2, 1), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The other end of the 3-way, on W-M-C1's bedroom face beside D-M-BED2. Since
    # 2026-10-05 that door hinges SOUTH at y=6'-9" and latches NORTH at y=9'-5", so the
    # switches moved to the north jamb: y=9'-11 3/8" leaves 4 3/8" from the box edge to the jamb,
    # outside the leaf. W-M-C1's bedroom paint plane is x=212.115".
    #
    # CKT-LT-MAIN, the same circuit as every can it switches. Both ends are plain
    # ED-T-LEV-SW3 3-ways (2026-10-31): the bed sconces are the low layer, not a dimmer.
    ElectricalDevice(uid="08SZS6SKK5", tag="ED-M-BED-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-MAIN", room="RM-M-BED",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="left", distance_from_start=inch(119.375),
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
    # looks up at. The 26" sweep clears the nearest can centre (CAN5 at (9'-5 7/8", 3'-4")) by
    # ~10" and every wall by 6'-0"+. REG-M-SUP3 moved 2'-0"
    # west for this (plan/mep_registers_main.py) — it sat on the room seed, 6" away, which is a
    # canopy-on-register overlap nothing in the engine would have reported.
    #
    # ** CONSTANT HOT, AND THE SWITCH IS A PLAIN ED-T-LEV-SW1, NOT A DIMMER. ** Mark N's
    # `source` says in capitals that a DC fan cannot be speed-controlled by a conventional
    # wall dimmer and that a Caseta dimmer will corrupt its receiver. The fan gets its own
    # leg and its own plain switch; speed and light are the hardwired Bluetooth wall control
    # plus the remote.
    # CKT-LT-MAIN, the same circuit as the load it switches — a switch on another circuit
    # than its load FAILs electrical.lighting_controls (NEC 210.7).
    # 2 1/4" south of the bed-centred 6'-6" since 2026-11-20: its fan brace box clears joist 5.
    ElectricalDevice(uid="SFVAJZ0YEM", tag="ED-M-BED-FAN", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), inch(75.75)), type_ref="ED-T-LT-FAN52",
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
                         wall_ref="W-M-C1", face="left", distance_from_start=inch(123.375),
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
    # plan/mep_registers_main.py for both.
    #
    # ** KEEP AT LEAST ONE OF THIS, ED-M-STUDY-DESK-LT AND ED-M-STUDY-LT ** for
    # `electrical.room_lighting` (R303.1 does not reach a study closet: not habitable).
    # `advisory.room_illuminance` wants 300 lx: 1,094 lm (520 can + 2 x 287 sconces) over 16 sf
    # is 353 lx; without the desk sconce it read 260.
    ElectricalDevice(uid="QTM000HAAA", tag="ED-M-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET", controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="left", distance_from_start=inch(46.25),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The study's NIGHT layer (owner, 2026-11-24; it replaced the TERTIAL desk lamp): a second
    # Sprig on the walnut west wall over FURN-M-STUDY-DESK, switched at its canopy toggle (J1).
    # A front-side light: ahead of and to the right of the seated occupant, on the camera's
    # side, never behind them on the felt. Body 4'-8" up, over seated eye (~4'-1") and 2' over
    # the desk top; the 9 7/8" arm reaches the desk's west half. Its box nails to stud-001.
    # Day is ED-M-STUDY-LT.
    ElectricalDevice(uid="ZJTRRMEFQT", tag="ED-M-STUDY-DESK-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(56)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-LS", face="right", distance_from_start=inch(10.875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

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
    # its own touch dimmer and unswitched plug power (2026-10-22). CAN1 is the vanity can, 27" off
    # the mirror and south in its bay, clear of the flat ERV trunk at x=27" and DU-M-ERV-R-BATH2
    # (2026-11-08); CAN2 is centred on the tub. The radiant-floor stat ED-M-BATH2-FH-STAT is a
    # separate control and switches none of this.
    ElectricalDevice(uid="QTM000NAAA", tag="ED-M-BATH2-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(inch(34), inch(180.5)), type_ref="ED-T-LT-CAN4-WET-5000",
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
    # ** ON THE LAUNDRY CEILING, ACROSS W-M-BA2E (owner, 2026-11-17). ** It was above
    # BATH2's board with no hatch (electrical.led_gear_access); now surface-mounted beside
    # the tub run's north end, out of the wet room, between RET3's valve and the track.
    ElectricalDevice(uid="ESWYM2QANP", tag="ED-M-BATH2-PSU", kind=DeviceKind.LED_DRIVER,
                     position=pt(inch(112), inch(242)), rotation=deg(90),
                     type_ref="ED-T-LT-PSU-60", circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY",
                     mount=Mount(kind=MountKind.CEILING, drop=inch(3.74))),
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

    # The bar is north of the tall machine body: all four task axes remain clear of it.
    # IKEA NYMÅNE since 2026-11-21 (owner). Its centre box is a 1-1/4" octagon ~1/8" under
    # DU-M-ERV-R-KITCH: ERV ducts lie 5/8" over the board across the whole room, so no
    # 2-1/8" box fits and a pancake is too small for 12 AWG. The PureEdge supply,
    # ED-M-LAUNDRY-PSU, and its Class 2 feed CR-M-LAUNDRY-24V went with the rail.
    ElectricalDevice(uid="QTM000SAAA", tag="ED-M-LAUNDRY-TRACK", kind=DeviceKind.LIGHT,
                     position=pt(inch(128.4), inch(260)), type_ref="ED-T-LT-TRACK-LAUNDRY",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY", box_use="ceiling-shallow",
                     controlled_by=("ED-M-LAUNDRY-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=LAUNDRY_TRACK_DROP)),
    # ED-M-LAUNDRY-SW moved off W-M-BA2E (2026-11-07): with the door 11 1/2" east that face
    # was 20" behind the strike wall. It is inside the strike jamb now, between stud-001
    # and the king.
    ElectricalDevice(uid="QTM000TAAA", tag="ED-M-LAUNDRY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-LAUNDRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-HS3", face="right", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
