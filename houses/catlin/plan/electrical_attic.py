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
    # ** THE SEVEN EAVE-LINE RECEPTACLES ARE FLOOR BOXES SINCE 2026-08-29. ** Every one of
    # them — ED-A-STUDIO-RC8/RC9 on the west line, ED-A-EAST-RC5/RC6/RC7 and ED-A-STUDY-RC2
    # on the east, ED-A-POCKET-RC1 in the pocket, plus ED-A-STUDY-RC3 in the south gable's
    # low east corner — was a box at 16" on a 5'-0" knee wall. There is no knee wall: those
    # hosts are 1 1/2" rafter plates now and the roof underside at the eave line is
    # `1 1/2" + x/2`, which is 5 1/4" at 7 5/8" off the wall. A 16" box there is not tight,
    # it is outside the building.
    #
    # `electrical.receptacle_spacing` is purely 2D — it unrolls the room's clear_face and
    # projects each device onto it — so DELETING these would leave the check green and the
    # rooms genuinely short of outlets along their longest walls. They are not deleted and
    # they are not moved in plan: each becomes a FLOOR box on its own authored station,
    # 19 5/8" off the node line either side — which is 8 1/8" clear of the rafter plate's
    # inner face (the plate runs x 6"..11 1/2"). NEC 210.52(A)(3) is explicit that a floor
    # receptacle counts toward the 6'-0" rule when it is within 18" of the wall, and 8 1/8"
    # is well inside that. `_perimeter_position`'s `_NEAR_WALL_M` still claims them.
    #
    # `Mount(kind=FLOOR)` carries no elevation, deliberately: the box is IN the deck.
    ElectricalDevice(uid="NEC052AAAA", tag="ED-A-EAST-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(34, 4.375), ft(31, 3.25)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(270)),
    ElectricalDevice(uid="NEC053AAAA", tag="ED-A-EAST-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(34, 4.375), ft(20, 9.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(270)),
    ElectricalDevice(uid="NEC054AAAA", tag="ED-A-EAST-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(34, 4.375), ft(10, 3.75)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(270)),
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
                     position=pt(ft(34, 4.375), ft(2)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(270)),
    # RC3 is a floor box for the same reason one wall further round: it stands at x 33'-10 3/4"
    # in the SOUTH gable, where the rake gives 14 1/8" of wall — less than the 16" the box was
    # authored at. Its plan station does not move; the gable is what shrank under it.
    ElectricalDevice(uid="NEC058AAAA", tag="ED-A-STUDY-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 10.75), ft(1, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR)),
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
    # ** THE WEST EAVE LINE CARRIES A RECEPTACLE AGAIN (ED-A-STUDIO-RC8, below). ** It was a
    # 5'-0" knee wall when this was written and it is a flat rafter plate now, but the 210.52
    # wall line the check unrolls is the same line either way. It briefly carried nothing:
    # the x=1'-0" chase used to carry DU-S-ERV-HP-FEED's 6" beside a 3", a box roughly
    # 12" wide by 8-9" tall for the wall's whole length, and the answer to that was a 21'-8"
    # bench (FURN-A-STUDIO-PLINTH) whose `work_surface=False` broke the 210.52 wall line the way
    # a doorway does. The 6" was rerouted out of this room on 2026-08-29 (plan/mep_erv.py), the
    # bench went with it, and what is left is ONE 75 mm duct whose west face stands 3 7/8" clear
    # of the gwb at ankle height. A box at 16" passes a foot over it. No cabinet, no break — and
    # so the wall is back in the 210.52 test on its own merits, which is the honest place for it.
    # It takes TWO boxes, not one: RC1 and RC7 carry the corners in from the south and north
    # ends, and a single mid-wall device left the check reporting gaps at both ends of its 12'
    # reach. RC8 at 6'-0" and RC9 at 16'-0" close them with 2'-0" of overlap in the middle.
    # ** RC1 AND RC7 ARE FLOOR BOXES TOO (2026-08-29), for the reason in the eave-line note
    # above and one wall further round. ** Both stand at x=3'-0" — RC1 in the south gable,
    # RC7 in W-A-STU-N — and both those walls are `ToRoof`, so at x=3'-0" they are 19 1/2"
    # tall. A 16" box in a 19 1/2" wall puts its top 1" through the raked plate. They keep
    # their stations and their place in the 210.52 line; only the mounting moved.
    ElectricalDevice(uid="923GJB648D", tag="ED-A-STUDIO-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(3), ft(1, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR)),
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
    # ** RC5 BECAME A GFCI DEVICE ON 2026-08-29 ** — not because it moved, but because the
    # wet bar did: FX-A-STUDIO-BAR-SINK is on this same wall at y 16'-8" now, 4'-8" north of
    # this box, and `_sink_points` projects E3902.10's 6'-0" radius from every Service.DRAIN
    # fixture. CKT-RC-ATTIC stays `gfci=False` and the protection rides the device, which is
    # the house rule (circuits.py). RC4 at y 3'-0" is 13'-8" away and stays ordinary.
    ElectricalDevice(uid="CX9R0H14DZ", tag="ED-A-STUDIO-RC5", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(17, 7.625), ft(12)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # On the bath's south wall and the pocket wall. ** E3902.10's 6'-0" radius is measured from
    # EVERY fixture whose type declares Service.DRAIN, not just from sinks. ** That is
    # `_sink_points`' actual behaviour and it is wider than it sounds: the shower and the water
    # closet project circles too. RC6 lands 3'-8" from FX-A-STUBATH-SH through the bath wall, so
    # it is a GFCI device whatever it is called. ** RC7 IS GFCI BY CHOICE NOW, NOT BY RULE
    # (2026-08-29). ** It used to sit 5'-11" from the bar sink; the bar moved east to
    # (17'-0", 16'-8") and the nearest Service.DRAIN fixture to RC7's (3'-0", 21'-0 5/8") is
    # the water closet at 10'-6", so E3902.10 no longer reaches it. The device stays GFCI:
    # it is a FLOOR box in a room with a wet bar, and dropping protection off an in-deck
    # receptacle to save a few dollars is the wrong trade. Over-protection is never a
    # violation; the comment is what had to be corrected, not the part.
    # The west eave line's pair. x=1'-7 5/8" is the floor-box station described in the
    # eave-line note above, 8 1/8" clear of the rafter plate; deg(90) turns them east into
    # the room, mirroring RC4/RC5's deg(270) on the centre wall opposite. Plain, not GFCI:
    # the nearest Service.DRAIN fixture is the bar sink at (17'-0", 16'-8"), and at 18'-9"
    # (RC8) and 15'-5" (RC9) neither is inside E3902.10's 6'-0" circle.
    ElectricalDevice(uid="F1MW3S3JD5", tag="ED-A-STUDIO-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(19.625), ft(6)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(90)),
    ElectricalDevice(uid="P0RCVAG1XM", tag="ED-A-STUDIO-RC9", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(19.625), ft(16)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(90)),
    ElectricalDevice(uid="TBSBS6V58H", tag="ED-A-STUDIO-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 6), ft(17, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(180)),
    ElectricalDevice(uid="NZQNA1VMKW", tag="ED-A-STUDIO-RC7", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(3), ft(21, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(180)),
    # ** THE WET BAR'S RECEPTACLE, GFCI UNDER E3902.10. ** `_sink_points` collects every fixture
    # whose TYPE declares Service.DRAIN regardless of what the fixture is called, so the bar
    # sink projects a 6'-0" radius into the studio whether it is a bar sink or a lavatory —
    # and it is a lavatory here. CKT-RC-ATTIC is `gfci=False` deliberately (circuits.py: "the
    # handful in an E3902 location … are GFCI devices instead"), so this follows the house rule
    # and is a GFCI DEVICE rather than a re-typed circuit.
    # Follows the bar to W-A-C2's west face on 2026-08-29 (see plan/fixtures.py), onto the
    # same x 17'-7 5/8" line RC4/RC5 already stand on and turned west into the room the same
    # way. `test_wall_mounted_devices_resolve_against_a_wall_face` is what settles that
    # number — authored an inch further west it resolved floating 1" clear of the finish.
    # ** y 16'-8" -> 15'-0 1/2" ON 2026-08-30. ** The sink was straightened onto the wall face
    # and its bowl now spans y 15'-7"..17'-1" (plan/fixtures.py), so 16'-8" stopped being
    # beside the bowl and became directly behind the faucet. 15'-0 1/2" is the middle of the
    # 1'-1" gap between the sink's south edge and APPL-A-STUDIO-FRIDGE's 14'-6" north face:
    # beside both, reachable by both, and `code.E3902_gfci_locations` measures it at 1.4'
    # against E3902.10's 6'-0".
    ElectricalDevice(uid="K9XVXZ9XZ3", tag="ED-A-STUDIO-BAR-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(17, 7.625), ft(15, 0.5)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # The bath's own, GFCI under E3902.1 — every 125V receptacle in a bathroom, sink or no
    # sink — and on the new CKT-BATH-ATTIC rather than the general attic circuit.
    ElectricalDevice(uid="N2Z2AA6EGB", tag="ED-A-STUBATH-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 11.875), ft(18, 6)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-BATH-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # At the ERV, in the pocket. IRC M1305.1.3 wants a receptacle (and a light — see
    # ED-A-POCKET-LT1) at the appliance; the pocket is STORAGE so 210.52 spacing never asks
    # for one, which is exactly why it has to be authored deliberately.
    # ** MOVED TO THE MANIFOLD AND MADE A FLOOR BOX, 2026-08-29. ** M1305.1.3's receptacle
    # has to be AT the appliance, and the appliance moved east to x 7'-0" where a person can
    # reach it (see EQ-A-ERV-MAN-EXH). At its old x 7 5/8" the roof underside is 5 1/4".
    ElectricalDevice(uid="E6RNBJBD76", tag="ED-A-POCKET-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(8, 6), ft(33)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.FLOOR), rotation=deg(90)),
]
