# haus: editable
# Catlin electrical — the ATTIC storey's NEC 210.52 fill, split out of plan/electrical.py
# (that file ran past AGENTS.md's 500-line cap).
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
from typehaus.model import Location, WallAttachment

NEC_FILL_ATTIC = [
    ElectricalDevice(uid="NEC048AAAA", tag="ED-A-EAST-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C2", face="right", distance_from_start=inch(56.25),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="NEC049AAAA", tag="ED-A-EAST-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C2B", face="right", distance_from_start=inch(20.875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="NEC050AAAA", tag="ED-A-EAST-RC3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-N1", face="left", distance_from_start=inch(198.625),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Removed east-eave floor boxes: ED-A-EAST-RC5 (NEC052AAAA) and RC7 (NEC054AAAA).
    # Their stations had only about 1' of headroom. The storage loft keeps its ridge,
    # north and south wall outlets; habitable-room spacing does not apply here.
    # Previously retired: RC4 (NEC051AAAA), RC6 (NEC053AAAA). Never reuse these UIDs.
    # 3/8" north of W-A-SN-REAR's north finish (y=10'-1"). Face-mounted in the unfinished
    # east loft and looking south; it moved with the rear partition rather than remaining
    # inside the new wall footprint.
    ElectricalDevice(uid="NEC055AAAA", tag="ED-A-EAST-RC8", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-SN-REAR", face="left", distance_from_start=inch(51.375),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # RC1 shifts east to x=30' so the south gable stays covered without an eave box.
    ElectricalDevice(uid="NEC056AAAA", tag="ED-A-STUDY-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-S3", face="left", distance_from_start=inch(144),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Removed study east-eave floor box RC2 (NEC057AAAA); its roof-to-floor boundary
    # remains an explicit spacing UNKNOWN pending the inspector's interpretation.
    # RC3 (NEC058AAAA) was previously removed as a redundant corner box. UIDs retired.
    ElectricalDevice(uid="NEC059AAAA", tag="ED-A-STUDY-RC4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-S3", face="left", distance_from_start=inch(70.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="NEC060AAAA", tag="ED-A-STUDY-RC5", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C1", face="right", distance_from_start=inch(54.375),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Studio outlets use the ridge and north/south partitions. RC1 and RC7 moved from
    # floor boxes at x=3' to wall attachments at x=6': enough wall for a 16"-AFF box,
    # reachable from the room, and within 6' of each gable's west end.
    # Removed west-eave floor boxes RC8 (F1MW3S3JD5) and RC9 (P0RCVAG1XM); UIDs retired.
    # The rafter plate closes the room graph but does not settle NEC wall-space status.
    ElectricalDevice(uid="923GJB648D", tag="ED-A-STUDIO-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-S1", face="left", distance_from_start=inch(72),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="AN95ADVNCZ", tag="ED-A-STUDIO-RC2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-S1", face="left", distance_from_start=inch(96),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="8H8X3VKAC2", tag="ED-A-STUDIO-RC3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-S2", face="left", distance_from_start=inch(52),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Two on the centre wall's west face.
    ElectricalDevice(uid="80A9PJCFAC", tag="ED-A-STUDIO-RC4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C1", face="left", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # ** RC5 STAYS A GFCI DEVICE, AND SINCE 2026-09-09 IT IS BY CHOICE RATHER THAN BY RULE. **
    # It was made GFCI because the wet bar stood on this same wall: `_sink_points` projects
    # E3902.10's 6'-0" radius from every Service.DRAIN fixture, and the bar sink was 4'-8"
    # north of this box. The bar is on W-A-BATH-S now (plan/placeables.py) and the bowl
    # measures 6'-2 1/2" from here — 2 1/2" OUTSIDE the circle. That margin is not worth
    # banking: the bowl's position within the SUNNERSTA's top is an unmeasured number
    # (plan/fixtures.py), and 3" of it either way puts this box back inside E3902.10. Same
    # trade RC7 carries two blocks down — over-protection is never a violation. CKT-RC-ATTIC
    # stays `gfci=False` and the protection rides the device, which is the house rule
    # (circuits.py). RC4 at y 3'-0" is further again and stays ordinary.
    ElectricalDevice(uid="CX9R0H14DZ", tag="ED-A-STUDIO-RC5", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C2", face="left", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # RC6 serves the bath's south wall; RC7 retains its existing GFCI protection
    # after moving onto the north partition. Neither change alters the circuit.
    # ** RC10 EXISTS BECAUSE ED-A-STUBATH-GFCI STOPPED COVERING FOR IT. **
    # W-A-STU-W is the bath's west wall and the studio's east wall at once, only 6 3/4" of
    # staggered partition apart — `electrical.receptacle_spacing` accepts any device within
    # 0.5 m of a room's boundary, so the bathroom receptacle used to silently answer
    # 210.52(A) for both rooms. Moved to serve E3901.6 instead, it exposed the studio's
    # real gap: 5'-0" of wall from the jog at (9'-7 1/2", 17'-3 3/8") north to W-A-HALL-S
    # with nothing on it.
    # x 9'-3 1/8" is one inch proud of that face (the wall's layers band x 112.115"..
    # 118.885"), y 18'-6" is centred in the run so 6'-0" each way reaches both ends and
    # turns the north corner. Plain, not GFCI: the nearest Service.DRAIN fixture is the bar
    # sink, and the bath's own fixtures are behind a wall a cord cannot pierce.
    ElectricalDevice(uid="SZ4K3PX817", tag="ED-A-STUDIO-RC10", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC", room="RM-A-STUDIO",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),

                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-STU-W", face="left", distance_from_start=inch(5.46875),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # ** RC6 MOVED EAST OF THE DOOR, 15'-6" -> 17'-2" (2026-09-09), BECAUSE IT WAS INSIDE THE
    # ROUGH OPENING. ** D-A-STUBATH slid east with the kitchenette and its RO is
    # 13'-11 1/2"..15'-11 1/2" now; 15'-6" is inside it. ** NOTHING GRADES THAT ** — no rule in this engine
    # tests a wall device against an opening — so it is caught here and by eye, and it is
    # exactly the defect ED-G-SW/ED-G-EXT-SW still carry in the garage. West of the unit is not
    # available (the kitchenette starts 8 7/16" off this wall's own west end), so east of the
    # door it is: 17'-2" leaves 1'-2 1/2" to the jamb and 10" to the W-A-C2 corner. It stays a
    # GFCI device — the bowl is 4'-2" away through the same wall face, inside E3902.10.
    ElectricalDevice(uid="TBSBS6V58H", tag="ED-A-STUDIO-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     # ** MOVED 1" OUT WITH W-A-BATH-S'S RETYPE, 2026-09-20 (H8). ** The wall went
                     # INT_2X4_PARTITION -> INT_2X6_PLUMBING so PR-A-BAR-VENT's 2" vent could bore
                     # its studs legally, and both faces moved 1" off the axis with it. This box is
                     # authored 1.000" off the GYPSUM face (the 0.01" paint film is not in the
                     # offset), so it moves the same 1".
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-BATH-S", face="right", distance_from_start=inch(90.5),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="NZQNA1VMKW", tag="ED-A-STUDIO-RC7", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-STU-N", face="right", distance_from_start=inch(72),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # ** THE WET BAR'S RECEPTACLE, GFCI UNDER E3902.10. ** `_sink_points` collects every fixture
    # whose TYPE declares Service.DRAIN regardless of what the fixture is called, so the bar
    # sink projects a 6'-0" radius into the studio whether it is a bar sink or a lavatory —
    # and it is a lavatory here. CKT-RC-ATTIC is `gfci=False` deliberately (circuits.py: "the
    # handful in an E3902 location … are GFCI devices instead"), so this follows the house rule
    # and is a GFCI DEVICE rather than a re-typed circuit.
    # ** IT FOLLOWED THE BAR ONTO W-A-BATH-S, AND IT IS AT 4'-10" BECAUSE THE UNIT IS
    # 4'-6 3/4" TALL (2026-09-09). ** It stood on W-A-C2's west face at 3'-6", beside a 3'-0"
    # counter. The SUNNERSTA is 54 3/4" to the top of its rail, so every station under 4'-7"
    # on this wall is BEHIND the unit — the "a tall unit swallows a receptacle from the NEC
    # ring and the spacing check never notices" case, and this engine has no rule that would
    # have said so. 4'-10" clears the rail by 3 1/4" and the 6:12 underside at this station is
    # 7'-0", so there is a foot of wall above it.
    #
    # x=13'-4" is 7 1/2" east of the bowl, over the unit's east end (which stops at
    # 13'-7 1/2") and 7 1/2" west of D-A-STUBATH's rough opening — the one band on this wall
    # that is neither behind the unit's rail nor inside the door. `code.E3902_gfci_locations` measures it at
    # 0.7' against E3902.10's 6'-0". `rotation=deg(180)` faces it south into the studio, off
    # the wall's south face at y 17'-0 5/8" — the same line RC6 stands on, and the number
    # `test_wall_mounted_devices_resolve_against_a_wall_face` settles.
    ElectricalDevice(uid="K9XVXZ9XZ3", tag="ED-A-STUDIO-BAR-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     # ** MOVED 1" OUT WITH W-A-BATH-S'S RETYPE, 2026-09-20 (H8). ** The wall went
                     # INT_2X4_PARTITION -> INT_2X6_PLUMBING so PR-A-BAR-VENT's 2" vent could bore
                     # its studs legally, and both faces moved 1" off the axis with it. This box is
                     # authored 1.000" off the GYPSUM face (the 0.01" paint film is not in the
                     # offset), so it moves the same 1".
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(58)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-BATH-S", face="right", distance_from_start=inch(44.5),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The bath's own, GFCI under E3902.1 — every 125V receptacle in a bathroom, sink or no
    # sink — and on the new CKT-BATH-ATTIC rather than the general attic circuit.
    # Its prior station failed `code.E3901_6_bathroom_receptacle` (IRC E3901.6 / NEC
    # 210.52(D): one receptacle within 36" of each lavatory basin) — right room, right
    # height, right circuit, wrong wall.
    # It goes on W-A-HALL-S's south face instead, in the 5 3/4" of clear wall between
    # FX-A-STUBATH-WC (ends x 146 7/8") and the vanity (starts x 152 5/8"): x 150" centres a
    # 4" plate in that gap, and y 264 5/8" puts the body's back on the face at 265 5/8"
    # (the wall's axis is y 268", its layers band 265 5/8"..270 3/8").
    # ** THE GAP NARROWED TO 5/8" A SIDE WHEN THE BOWL BECAME A 24" VANITY (2026-09-09) AND
    # THERE IS NOWHERE ELSE ON THIS WALL LEFT. ** The east end of the counter is not an
    # option any more — it used to have 5.6" of wall to the shower and now it dies flat into
    # the pan's west panel. Widening the vanity past 24", or sliding it west, deletes the
    # only station that satisfies IRC E3901.6's 36"-of-a-basin rule. The basin centres at
    # x 164 5/8", so this plate is 14 5/8" from it and has plenty of that margin; what it has
    # no margin in is the wall itself.
    ElectricalDevice(uid="N2Z2AA6EGB", tag="ED-A-STUBATH-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-BATH-ATTIC", room="RM-A-STUBATH",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-HALL-S", face="right", distance_from_start=inch(30),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # At the ERV, in the pocket. IRC M1305.1.3 wants a receptacle (and a light — see
    # ED-A-POCKET-LT1) at the appliance; the pocket is STORAGE so 210.52 spacing never asks
    # for one, which is exactly why it has to be authored deliberately.
    # On W-A-BA-E's pocket face, ~5' from EQ-A-ERV-MAN-EXH: "near" the appliance for
    # M1305.1.3. A wall box, not a floor box (owner 2026-10-22): cheaper, and the 6:12 rake
    # leaves ~5' of wall here. Clear of VR-M-STACK's jog at y 34'-4".
    ElectricalDevice(uid="E6RNBJBD76", tag="ED-A-POCKET-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-BA-E", face="right", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]
