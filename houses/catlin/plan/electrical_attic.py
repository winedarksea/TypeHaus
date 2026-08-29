# haus: editable
# Catlin electrical — the ATTIC storey's NEC 210.52 fill, split out of plan/electrical.py on
# 2026-08-29. That file was 1,700 lines against AGENTS.md's 500 before the guest studio added
# ten devices to it.
#
# ** AN EDITABLE FILE CANNOT `from plan import ...` **, so this module imports only from
# `typehaus` and plan/manifest.py composes the two lists. The rest of the attic's electrical —
# the PV junction boxes, the data trunk and the data devices — stays in electrical.py with its
# siblings; what moved is the receptacle schedule, which is the part that is per-room and the
# part the studio grew.
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

NEC_FILL_ATTIC = [
    ElectricalDevice(uid="NEC048AAAA", tag="ED-A-EAST-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(18, 4.375), ft(13, 8.25)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC049AAAA", tag="ED-A-EAST-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(18, 4.375), ft(24, 0.875)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC050AAAA", tag="ED-A-EAST-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(19, 5.375), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC051AAAA", tag="ED-A-EAST-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29, 11.25), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC052AAAA", tag="ED-A-EAST-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(31, 3.25)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC053AAAA", tag="ED-A-EAST-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(20, 9.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC054AAAA", tag="ED-A-EAST-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(10, 3.75)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # y 9'-3 3/8" -> 9'-11 3/8" (2026-08-27): W-A-SN thickened to 12 3/4" for the study's
    # bookcase wall, and at the old y this device sat INSIDE the wall. Nothing checks that,
    # which is why it is written down. 9'-11 3/8" is the same 3/8" off the new north face
    # that 9'-3 3/8" was off the old one, so it is still a face-mounted receptacle in
    # RM-A-EAST-UNFIN looking south.
    ElectricalDevice(uid="NEC055AAAA", tag="ED-A-EAST-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26, 6.375), ft(9, 11.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # RC1/RC2 moved 2026-07-31: both used to sit over the FO-A-STAIR well (1 3/4"/6 5/8" of
    # deck, a 9' drop to reach). RC1 -> south wall between RC4/RC3; RC2 -> east wall south of
    # the well, closing the 7'-10" run from RC3 round the corner.
    ElectricalDevice(uid="NEC056AAAA", tag="ED-A-STUDY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC057AAAA", tag="ED-A-STUDY-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(2)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC058AAAA", tag="ED-A-STUDY-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 10.75), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC059AAAA", tag="ED-A-STUDY-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(23, 10.5), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC060AAAA", tag="ED-A-STUDY-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(4, 6.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    # --- the guest studio, 2026-08-29 ------------------------------------------------
    # ** EVERY POSITION BELOW IS ITS WALL'S FINISH FACE PLUS 1". ** A device position is a
    # plain plan point and nothing in the resolver pulls it onto a wall, so a box authored ON
    # the face resolves half its body inside the studs, and one authored a few inches off
    # resolves in mid-air. `test_wall_mounted_devices_resolve_against_a_wall_face` grades both
    # ends of that and caught four of these at 1.38" buried on the first pass. The 1" is half
    # the box depth and is the offset every other device in this file carries.
    #
    # ** THE WEST KNEE WALL CARRIES NO RECEPTACLE, AND THAT IS BY DESIGN. ** The x=1'-0" ERV
    # chase runs its whole length, and FURN-A-STUDIO-PLINTH (plan/placeables.py) boxes it. A
    # counterless fixed cabinet within 6" of the floor is a BREAK in the 210.52 wall line
    # (`_fixed_cabinet_intervals`), exactly as a doorway is — so the plinth removes that wall
    # from the spacing test HONESTLY, rather than forcing an outlet in behind a duct box.
    ElectricalDevice(uid="923GJB648D", tag="ED-A-STUDIO-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(3), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="AN95ADVNCZ", tag="ED-A-STUDIO-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(8), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="8H8X3VKAC2", tag="ED-A-STUDIO-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(13), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # Two on the centre wall's west face.
    ElectricalDevice(uid="80A9PJCFAC", tag="ED-A-STUDIO-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 7.625), ft(3)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="CX9R0H14DZ", tag="ED-A-STUDIO-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 7.625), ft(12)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # On the bath's south wall and the pocket wall. ** E3902.10's 6'-0" radius is measured from
    # EVERY fixture whose type declares Service.DRAIN, not just from sinks. ** That is
    # `_sink_points`' actual behaviour and it is wider than it sounds: the shower and the water
    # closet project circles too. RC6 lands 3'-8" from FX-A-STUBATH-SH through the bath wall, so
    # it is a GFCI device whatever it is called; RC7 is a GFCI device for the same
    # reason: at x=3'-0" it is 5'-11" from the bar sink, and moving it west to 1'-6" to escape
    # that circle opened a 210.52 gap in the middle of W-A-STU-N. The receptacle has to be
    # where the wall space is; the protection is what moves.
    ElectricalDevice(uid="TBSBS6V58H", tag="ED-A-STUDIO-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 6), ft(17, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(180)),
    ElectricalDevice(uid="NZQNA1VMKW", tag="ED-A-STUDIO-RC7", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(3), ft(22, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(180)),
    # ** THE WET BAR'S RECEPTACLE, GFCI UNDER E3902.10. ** `_sink_points` collects every fixture
    # whose TYPE declares Service.DRAIN regardless of what the fixture is called, so the bar
    # sink projects a 6'-0" radius into the studio whether it is a bar sink or a lavatory —
    # and it is a lavatory here. CKT-RC-ATTIC is `gfci=False` deliberately (circuits.py: "the
    # handful in an E3902 location … are GFCI devices instead"), so this follows the house rule
    # and is a GFCI DEVICE rather than a re-typed circuit.
    ElectricalDevice(uid="K9XVXZ9XZ3", tag="ED-A-STUDIO-BAR-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 3.125), ft(20)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(90)),
    # The bath's own, GFCI under E3902.1 — every 125V receptacle in a bathroom, sink or no
    # sink — and on the new CKT-BATH-ATTIC rather than the general attic circuit.
    ElectricalDevice(uid="N2Z2AA6EGB", tag="ED-A-STUBATH-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 11.875), ft(18, 6)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-BATH-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # At the ERV, in the pocket. IRC M1305.1.3 wants a receptacle (and a light — see
    # ED-A-POCKET-LT1) at the appliance; the pocket is STORAGE so 210.52 spacing never asks
    # for one, which is exactly why it has to be authored deliberately.
    ElectricalDevice(uid="E6RNBJBD76", tag="ED-A-POCKET-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0, 7.625), ft(33)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
]
