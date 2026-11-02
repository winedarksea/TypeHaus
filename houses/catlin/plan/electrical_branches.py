# haus: editable
# Workshop and theater branches (owner decision 2026-10-28, notes/basement_surface_wiring.md).
# Everything else on the basement concrete is NM-B overhead in a derived EMT sleeve; these
# two get raceway because they will be re-pulled.

from typehaus import (
    ConduitRun,
    DeviceKind,
    ElectricalDevice,
    Location,
    Mount,
    MountKind,
    Service,
    SleevePenetration,
    WallAttachment,
    deg,
    ft,
    inch,
    pt,
)

BRANCH_PULL_BOXES = [
    # Over the bench, between RC1 and RC2: a surface box on the gypsum, blank cover, so the
    # exposed trunk and drops reach its side knockouts (drop = 5/8" board + the 4" box).
    # 8 x 8 since 2026-10-29: a straight pull of the 1" trunk (NEC 314.28(A)(1)).
    ElectricalDevice(uid="38ARN77QK2", tag="ED-B-WORKSHOP-JB", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-JBOX-8X8", room="RM-B-WORKSHOP", position=pt(inch(20), inch(102)),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4.625))),
    # Behind FURN-B-PLAY-TV, on the north wall at 48" AFF, over RC1 and clear of the panel's
    # face (the mount stands it 3 1/2" off the wall; box and cover take 2-5/8"). It was a
    # surface box on the theater ceiling until 2026-11-02: that ceiling is gypsum on resilient
    # channel with no boxes or lights (notes/theater_ceiling_acoustics.md), and a box on a
    # bare concrete wall is the house's own surface-device idiom. x=25'-11 1/4" sits in the
    # 13" web opening CD-B-PLAY-SPARE comes down through, so the spare drops straight in.
    ElectricalDevice(uid="X6HGS71F6Y", tag="ED-B-PLAY-N-JB", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-JBOX", room="RM-B-PLAY-N",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-N1", face="left", distance_from_start=inch(120.75),
                         normal_gap=inch(0), rotation_offset=deg(180)))),
]

BRANCH_RACEWAYS = [
    # 1" EMT + THHN, panel 2 to the bench box, exposed below the joists (owner, 2026-10-29:
    # no bores through ~15 I-joist webs). Router proposal A, adjusted: its x 9 1/4" lane cut
    # W-B-CW's end stud lengthwise. Out of the panel top (78" AFF) at x 9 1/2", up and
    # south on clamp-backs at 7'-7" AFF, angling 7/8" east so it crosses W-B-CW in its west
    # clear bay clear of the stud (the sauna ducts moved a bay east, 2026-10-31); up at
    # y 12'-6" (clear of RC2's drop) to the box's side knockout, 2" under the gypsum.
    # 360 degrees, panel to box. Carries CKT-WORKSHOP-240; 1" leaves room for more circuits
    # or a 60-100 A subpanel feeder (#3 + #8 THHN fits at 40%).
    ConduitRun(uid="4AQ25GM4Y2", tag="CD-B-WORKSHOP", trade_size=inch(1),
               service=Service.POWER_240,
               path=(pt(inch(9.5), ft(25)), pt(inch(9.5), ft(25)),
                     pt(inch(10.75), ft(12, 6)), pt(inch(10.75), ft(12, 6)),
                     pt(ft(1, 7.375), ft(12, 6)), pt(ft(1, 7.375), ft(8, 6))),
               elevations=(inch(-31.4375), inch(-18.5), inch(-18.5), inch(-15.125),
                           inch(-15.125), inch(-15.125)),
               from_ref="ED-B-PANEL-2", to_ref="ED-B-WORKSHOP-JB",
               circuits=("CKT-WORKSHOP-240",)),
    # 3/4" EMT + THHN drops, exposed like the trunk: out of the box's south (RC1, router
    # proposal B) or west side (RC2), along the ceiling to the wall, down its face to the
    # surface box's top knockout. The router's cheaper lanes dropped mid-room and crossed
    # at receptacle height, with nothing to strap to.
    ConduitRun(uid="F0T4ZHEEG3", tag="CD-B-WORKSHOP-RC1", trade_size=inch(0.75),
               service=Service.POWER_240,
               path=(pt(ft(1, 8), ft(8, 4)), pt(ft(1, 8), ft(6)), pt(inch(8.4375), ft(6)),
                     pt(inch(8.4375), ft(6))),
               elevations=(inch(-15.125), inch(-15.125), inch(-15.125), inch(-63.1875)),
               from_ref="ED-B-WORKSHOP-JB", to_ref="ED-B-WORKSHOP-RC1",
               circuits=("CKT-WORKSHOP-240",)),
    # CKT-RC-BSMT arrives in the bench box as NM; THHN from there to the quad.
    ConduitRun(uid="H969HXHVQ6", tag="CD-B-WORKSHOP-RC2", trade_size=inch(0.75),
               service=Service.POWER_120,
               path=(pt(inch(17.5), ft(8, 8)), pt(inch(8.4375), ft(8, 8)),
                     pt(inch(8.4375), ft(11)), pt(inch(8.4375), ft(11))),
               elevations=(inch(-15.125), inch(-15.125), inch(-15.125), inch(-63.1875)),
               from_ref="ED-B-WORKSHOP-JB", to_ref="ED-B-WORKSHOP-RC2",
               circuits=("CKT-RC-BSMT",)),
    # 3/4" EMT capped spare, panel to the TV-wall box: a dedicated AV circuit pulls in later
    # without opening the ceiling. No new circuit now; the panel is nearly full. Up out of
    # the panel top (78" AFF) and under the gypsum at -1'-1 7/16" (west of PR-B-SAUNA-VENT's x=4'-3
    # 1/2" leg, ducking 1.6" under PR-B-HW-BATH's x=7'-3 5/8" leg on 6" ramps (15° bends) and rising back over the
    # vent's x=9'-0" leg, 2.8" over CD-B-KITCHEN and CD-B-DATA-MEDIA: the
    # furnace room has no lane beside those two, W-B-STR3's face is at x=9'-9 1/4"),
    # through W-B-STR2's top plate and RM-B-BATH, then up the hall to a body at y=25'-6" (south
    # of FO-M-STAIR, which is open well from y=26'-0 3/8").
    #
    # ** OVER the theater ceiling since 2026-11-02 (decision #112). ** From that body a ramp
    # rises into FS-M-WEST's bay, over the x=18' plate (the framed W-B-CN is bearing; no bore),
    # and rides FS-M-NE's truss bay y=25'-6" at -8 3/4" to x=25'-11 1/4", turns north through the
    # 13" web opening of each truss to y=35'-3 1/2" and drops against the north wall (1/2" off
    # the face, as RC1's drop does) to the box's top knockout. 206 degrees after the hall
    # body; pull boxes at 8 (RM-B-BATH) and 11 (the hall).
    ConduitRun(uid="FD1J045HS6", tag="CD-B-PLAY-SPARE", trade_size=inch(0.75),
               service=None,
               path=(pt(inch(9.5), inch(349.375)), pt(inch(9.5), inch(349.375)),
                     pt(inch(40), inch(349.375)),
                     pt(inch(40), inch(243.5)), pt(inch(76), inch(243.5)),
                     pt(inch(82), inch(243.5)), pt(inch(95), inch(243.5)),
                     pt(inch(101), inch(243.5)), pt(inch(162.25), inch(243.5)),
                     pt(inch(162.25), inch(230.75)), pt(inch(194.75), inch(230.75)),
                     pt(inch(194.75), inch(306)), pt(inch(208), inch(306)),
                     pt(inch(311.25), inch(306)), pt(inch(311.25), inch(423.54)),
                     pt(inch(311.25), inch(423.54))),
               elevations=(inch(-31.4375), inch(-13.44), inch(-13.44), inch(-13.44), inch(-13.44),
                           inch(-15.05), inch(-15.05), inch(-13.44), inch(-13.44), inch(-13.44),
                           inch(-13.44), inch(-13.44), inch(-8.75), inch(-8.75), inch(-8.75), inch(-57.7)),
               pull_points=(8, 11),
               from_ref="ED-B-PANEL", to_ref="ED-B-PLAY-N-JB"),
    # 3/4" EMT + THHN from the TV box straight down the wall face to the receptacle below it
    # (face + half the OD); CKT-RC-BSMT's NM enters the box.
    ConduitRun(uid="8XNJPBCK9B", tag="CD-B-PLAY-N-RC1", trade_size=inch(0.75),
               service=Service.POWER_120,
               path=(pt(inch(311.25), inch(423.54)), pt(inch(311.25), inch(423.54))),
               elevations=(inch(-61.7), inch(-75.7025)),  # box top on the 0.735" carpet
               from_ref="ED-B-PLAY-N-JB", to_ref="ED-B-PLAY-N-RC1",
               circuits=("CKT-RC-BSMT",)),
]

BRANCH_SLEEVES = []
