# haus: editable
# Catlin lighting — the GARAGE.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
#
# Conventions (rotation, mounts, controlled_by, 24V PSUs, uids): plan/lighting_basement.py.

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

# --- Garage ---------------------------------------------------------------------------
# Five Q shop lights on one switch by the service door, on CKT-LT-GARAGE (since 2026-10-31;
# CKT-LT-MAIN before), the garage's own lighting circuit in ED-G-PANEL, not the GFCI
# receptacle circuit, which would drop the lights every time a tool trips one. Surface mounted at 8' —
# nothing above the garage ceiling to recess a can into.
GARAGE_LIGHTING = [
    ElectricalDevice(uid="QTG0001AAA", tag="ED-G-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(18), ft(50, 6)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    ElectricalDevice(uid="QTG0002AAA", tag="ED-G-LT2", kind=DeviceKind.LIGHT,
                     position=pt(ft(18), ft(60, 6)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # A third shop light over ST-G-SERVICE, the service door's flight. The two above are at
    # y=50'-6" and y=60'-6", the working half of the bay; the flight drops 2'-10" in five
    # risers from the threshold and neither reaches within R303.8's 4' of it. Stepping
    # through the door onto a top tread in the dark is the reason the rule exists. (It reads as an
    # *exterior* stair rather than an interior one because `_stair_is_indoors` asks whether
    # a CONDITIONED room stands over it, and the garage is deliberately unconditioned. R303.7
    # would want the same luminaire here and not the switching, since five risers is under
    # its six-riser threshold.)
    ElectricalDevice(uid="4PQRD03TG8", tag="ED-G-LT3", kind=DeviceKind.LIGHT,
                     # Centred on the flight (x 6'-11 5/8"..9'-11 5/8", y 43'-9 3/8"..
                     # 47'-6 1/8") since the interior landing went, 2026-10-13.
                     position=pt(ft(8, 5.625), ft(45, 7.75)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # LT4/LT5 (2026-10-31): one over each bay at mid-depth, y=55'-6", south of where the open
    # overhead door's panel stops (~59'-2") and clear of the opener head at x=18'-0".
    ElectricalDevice(uid="PQX96QHYWG", tag="ED-G-LT4", kind=DeviceKind.LIGHT,
                     position=pt(ft(11), ft(55, 6)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    ElectricalDevice(uid="F64CZX32H8", tag="ED-G-LT5", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(55, 6)), type_ref="ED-T-LT-SHOP4",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     controlled_by=("ED-G-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # On W-G-S's INTERIOR face (plan/storeys/garage.py::GARAGE_Y_SOUTH) — see
    # plan/electrical.py's GARAGE_DEVICES comment for the face-position arithmetic.
    #
    # ** x=10'-8" IS EAST OF THE DOOR'S JACK, AND 76" IS 48 4/5" ABOVE THE TOP TREAD. **
    # D-G-SERVICE's RO is 6'-7"..9'-7" since it moved into the SW corner, its east king ends
    # at 9'-10", and this switch and ED-G-EXT-SW below stand 4" and 10" east of that. Both
    # were INSIDE the old rough opening (a defect the 2026-09-07 rotation carried forward).
    # A garage device's `Mount.elevation` is measured off the ROOM FLOOR
    # (`resolve/room_floor.py`), the slab at -2'-10". It was 80" — 46" over the interior
    # landing — until that landing went (2026-10-13); the flight's top tread is at -6.8"
    # absolute, 27.2" over the slab, so 76" puts the gang 48.8" over the tread you stand on
    # and 42" over the threshold you walk in on.
    ElectricalDevice(uid="QTG0003AAA", tag="ED-G-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-HBL-SW1",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-S", face="left", distance_from_start=inch(56),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Blank-face GFCI beside the switch: the opener's ceiling outlet ED-G-GDO-RC is on its
    # load side, so its reset is in reach (NEC 210.8) and a tripped opener leaves the lights on.
    ElectricalDevice(uid="T2P1VW9FJE", tag="ED-G-GDO-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-DF", plate="stainless",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-S", face="left", distance_from_start=inch(59),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

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
    # integrity.wall_mount_on_face does. W-G-N's cladding outer face
    # is 64'-9 1/2" (GARAGE_Y_NORTH + the 7/8" corrugated panel), so the centre is 2 1/2"
    # proud of it at 65'-0".
    ElectricalDevice(uid="QTG0004AAA", tag="ED-G-EXT-LT-E", kind=DeviceKind.LIGHT,
                     # x=28'-0" is 2'-0" in from the NE corner. The uid is the original
                     # light's: this element did not stop existing when it was retagged.
                     type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-GARAGE", controlled_by=("ED-G-EXT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 8)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-N", face="right", distance_from_start=inch(24),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="GT8NZ3DTSX", tag="ED-G-EXT-LT-W", kind=DeviceKind.LIGHT,
                     # x=8'-0" is 2'-0" in from the NW corner, the exact mirror of -E about
                     # the door's centreline at x=18'-0". Same circuit, same switch: the pair
                     # is one control, not two.
                     type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-GARAGE", controlled_by=("ED-G-EXT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 8)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-N", face="right", distance_from_start=inch(264),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Its switch, inside, beside ED-G-SW at the service door: 6" west of it and 4" east of
    # the door's east king (see ED-G-SW for the stations and the 76" elevation; nothing
    # grades a wall device against an opening, so a move of that door must move both by
    # hand). Walk in, one reach turns on the shop lights and BOTH door lights. One switch
    # for the pair, not one each: they light a single opening and there is no reason to run
    # half of it. It stays here though its luminaires crossed to the far wall: the switch
    # belongs at the door you enter by, not under the lamp. A D315S relay, so HA can light
    # the apron at dusk and on the opener's arrival.
    ElectricalDevice(uid="QTG0005AAA", tag="ED-G-EXT-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-S", face="left", distance_from_start=inch(50),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # --- The garage's exterior linear (2026-09-11): two eave soffits + the gable face -----
    #
    # ** THE EAVES ARE EAST AND WEST, AND THAT IS GEOMETRY, NOT A CHOICE. ** RF-GARAGE is a
    # gable with `ridge_direction="y"`, so the slopes fall east and west over W-G-E / W-G-W
    # and the two GABLE ENDS are north and south. The north wall — the facade, the one with
    # the overhead door in it — is a RAKE, so the third run climbs it rather than being "the
    # north eave".
    #
    # ** HOSTED ON THE SILL TO SOFFIT (decision #143). ** The QSG-3211 is clipped under the
    # stock receiver's solid flange, its inside edge tight to the corrugated panel, so it
    # covers no intake slot; `resolve/trim_led.py` derives x, z and the ends from the trim.
    # The stated points below are those derived values; they only have to land within 6".
    #
    # Each eave runs cladding face to cladding face, 24'-1 3/4", in two halves (Class 2,
    # below): the south halves keep the original tags.
    LightRun(uid="N2XWJEVXGS", tag="LR-G-EAVE-W", type_ref="ED-T-LT-LINEAR-EXT",
             path=(pt(ft(5, 10.489), ft(43, 1.75)), pt(ft(5, 10.489), ft(55, 2.625))),
             psu_ref="ED-G-EAVE-W-PSU", controller_ref="ED-G-EAVE-W-CTRL", controlled_by=("ED-G-SOFFIT-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 8.96))),
    LightRun(uid="T7GB8BJ2JP", tag="LR-G-EAVE-W2", type_ref="ED-T-LT-LINEAR-EXT",
             path=(pt(ft(5, 10.489), ft(55, 2.625)), pt(ft(5, 10.489), ft(67, 3.5))),
             psu_ref="ED-G-EAVE-W2-PSU", controller_ref="ED-G-EAVE-W2-CTRL", controlled_by=("ED-G-SOFFIT-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 8.96))),
    LightRun(uid="QPT63YW4TW", tag="LR-G-EAVE-E", type_ref="ED-T-LT-LINEAR-EXT",
             path=(pt(ft(30, 1.511), ft(43, 1.75)), pt(ft(30, 1.511), ft(55, 2.625))),
             psu_ref="ED-G-EAVE-E-PSU", controller_ref="ED-G-EAVE-E-CTRL", controlled_by=("ED-G-SOFFIT-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 8.96))),
    LightRun(uid="7G3Y0ST61X", tag="LR-G-EAVE-E2", type_ref="ED-T-LT-LINEAR-EXT",
             path=(pt(ft(30, 1.511), ft(55, 2.625)), pt(ft(30, 1.511), ft(67, 3.5))),
             psu_ref="ED-G-EAVE-E2-PSU", controller_ref="ED-G-EAVE-E2-CTRL", controlled_by=("ED-G-SOFFIT-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 8.96))),
    # The north gable: the same detail up RF-GARAGE's two rake soffits, corner -> ridge, the
    # rake's own Sill to Soffit hosting it. Split at the ridge: the east rake keeps the tag.
    # `full_cutoff` is a DETAIL (aperture down); CEILING under the soffit reads as sheltered.
    LightRun(uid="12K1TBK2FC", tag="LR-G-GABLE-N", type_ref="ED-T-LT-LINEAR-EXT",
             path=(pt(ft(18), ft(67, 4.136)), pt(ft(30, 0.875), ft(67, 4.136))),
             rise=(ft(4, 0.292), ft(0)),
             psu_ref="ED-G-GABLE-N-PSU", controller_ref="ED-G-GABLE-N-CTRL", controlled_by=("ED-G-SOFFIT-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 2.002))),
    LightRun(uid="WJ6P1GC7H2", tag="LR-G-GABLE-N2", type_ref="ED-T-LT-LINEAR-EXT",
             path=(pt(ft(5, 11.125), ft(67, 4.136)), pt(ft(18), ft(67, 4.136))),
             rise=(ft(0), ft(4, 0.292)),
             psu_ref="ED-G-GABLE-N2-PSU", controller_ref="ED-G-GABLE-N2-CTRL", controlled_by=("ED-G-SOFFIT-SW",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 2.002))),
    # ** ITS OWN CONTROL, NOT ED-G-EXT-SW, AND THE REASON IS DUTY CYCLE. ** Ganging ~73 LF of
    # perimeter linear onto the door pair's switch would force one of two bad habits: either
    # the two sconces burn all evening because somebody wanted the building lit, or the
    # building is never lit because nobody wants to leave the sconces on. They are two
    # LAYERS, not two halves of one thing — ED-G-EXT-LT-E/-W are a "somebody is at the door"
    # light aimed at the apron, and these three runs are an ambient wash that wants to come
    # on at dusk and go off by itself. HA schedules it through the runs' Matter controllers;
    # this paddle (plain since 2026-11-03) is a hard-off left on. Unattended is the whole
    # point: a run left on until somebody notices is the dark-sky failure mode.
    #
    # Third in the gang at the service door, 6" east of ED-G-SW on the 6" spacing those two
    # already use (10'-2", 10'-8", 11'-2"), same 76" over the slab, 48.8" over the top tread.
    # Same circuit as the loads it switches, so no NEC 210.7 two-circuit box.
    # Mark W is 24V RGBW (4.5 W/ft). ** CLASS 2 (owner, 2026-10-31): ** the tape is unlisted,
    # so every segment is on a <=100 VA Class 2 supply, the certified part: an HLG-100 (96 W)
    # per half run, 12' x 4.5 x 1.25 = 68 W (gable halves 72 W). Each driver is INDOORS at
    # 96" on the wall nearest its half, with its controller 12" along the wall. ** MATTER
    # SINCE 2026-11-07 ** (owner: moisture is the concern, Matter preferred): a GL-C-208M in a
    # vented NEMA 4X box (ED-T-LT-CTRL-MATTER), the tape's W on its warm terminal: HA pins
    # color_temp at the warmest kelvin for the dusk white (notes/smart_home.md).
    ElectricalDevice(uid="7RB4FGXA5Q", tag="ED-G-EAVE-W-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-W", face="left", distance_from_start=inch(200),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="5TFZDH6TEV", tag="ED-G-EAVE-W-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-MATTER", psu_ref="ED-G-EAVE-W-PSU", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-W", face="left", distance_from_start=inch(188),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="YX5KGQZP6W", tag="ED-G-EAVE-W2-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-W", face="left", distance_from_start=inch(72),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="BN45YA6PCY", tag="ED-G-EAVE-W2-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-MATTER", psu_ref="ED-G-EAVE-W2-PSU", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-W", face="left", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="6EGKQSPTH2", tag="ED-G-EAVE-E-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-E", face="left", distance_from_start=inch(100),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="2P06FQVMBP", tag="ED-G-EAVE-E-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-MATTER", psu_ref="ED-G-EAVE-E-PSU", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-E", face="left", distance_from_start=inch(88),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="V7SSVTKSDT", tag="ED-G-EAVE-E2-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-E", face="left", distance_from_start=inch(216),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="F5NJA2SN4G", tag="ED-G-EAVE-E2-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-MATTER", psu_ref="ED-G-EAVE-E2-PSU", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-E", face="left", distance_from_start=inch(228),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="D8THMTHKHZ", tag="ED-G-GABLE-N-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-N", face="left", distance_from_start=inch(30),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="77SGFSDD3D", tag="ED-G-GABLE-N-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-MATTER", psu_ref="ED-G-GABLE-N-PSU", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-N", face="left", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="VT871B9SWE", tag="ED-G-GABLE-N2-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-N", face="left", distance_from_start=inch(262),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="B5X6YRRPHS", tag="ED-G-GABLE-N2-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-MATTER", psu_ref="ED-G-GABLE-N2-PSU", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-N", face="left", distance_from_start=inch(276),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="S7ANA4Q300", tag="ED-G-SOFFIT-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-HBL-SW1",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-S", face="left", distance_from_start=inch(62),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]
