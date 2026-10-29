# haus: editable
# Workshop and theater branches (owner decision 2026-10-28, notes/basement_surface_wiring.md).
# Everything else on the basement concrete is NM-B overhead in a derived EMT sleeve; these
# two get raceway because they will be re-pulled.

from typehaus import (
    ConduitRun,
    DeviceKind,
    ElectricalDevice,
    Mount,
    MountKind,
    Service,
    SleevePenetration,
    inch,
    pt,
)

BRANCH_PULL_BOXES = [
    # Over the bench, between RC1 and RC2, in the gypsum ceiling behind a blank cover.
    ElectricalDevice(uid="38ARN77QK2", tag="ED-B-WORKSHOP-JB", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-JBOX", room="RM-B-WORKSHOP", position=pt(inch(20), inch(102)),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Above FURN-B-PLAY-TV. Surface on the ceiling, blank cover: the gypsum here is hung on
    # SL-M-DECK's concrete band, so there is no cavity to recess into. The storey's ceiling
    # plane is -1'-0 1/2"; this room's finished ceiling is -1'-2 1/16", and the 4" box hangs
    # from it (drop 5 9/16").
    ElectricalDevice(uid="X6HGS71F6Y", tag="ED-B-PLAY-N-JB", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-JBOX", room="RM-B-PLAY-N", position=pt(inch(321), inch(414)),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(5.5625))),
]

BRANCH_RACEWAYS = [
    # 1" EMT + THHN, panel 2 to the bench box (router proposal A, 2026-10-29): up out of the
    # panel top beside DU-B-ERV-R-SAUNA-SUP (x 9 1/4", clear of its 4" body at x 12 1/2"),
    # east in the joist bay, south through the I-joist webs at -3 1/2" (over the two drops'
    # -5 15/16" bores), down into the box.
    # Carries CKT-WORKSHOP-240 now; 1" leaves room for more circuits or a 60-100 A subpanel
    # feeder (#3 + #8 THHN fits at 40%).
    ConduitRun(uid="4AQ25GM4Y2", tag="CD-B-WORKSHOP", trade_size=inch(1),
               service=Service.POWER_240,
               path=(pt(inch(9.25), inch(300)), pt(inch(9.25), inch(300)),
                     pt(inch(20), inch(300)), pt(inch(20), inch(102)),
                     pt(inch(20), inch(102))),
               elevations=(inch(-19.44), inch(-3.5), inch(-3.5), inch(-3.5), inch(-8.5)),
               from_ref="ED-B-PANEL-2", to_ref="ED-B-WORKSHOP-JB",
               circuits=("CKT-WORKSHOP-240",)),
    # 3/4" EMT + THHN drops: out of the bench box's top, south or north through the webs,
    # west in the bay to the wall, down its face to the surface box's top knockout. Clear of
    # the sauna supply duct (x 10 1/2"-14 1/2") and CD-B-DATA-SHOP (x 10" at -4'-0").
    ConduitRun(uid="F0T4ZHEEG3", tag="CD-B-WORKSHOP-RC1", trade_size=inch(0.75),
               service=Service.POWER_240,
               path=(pt(inch(20), inch(100)), pt(inch(20), inch(100)), pt(inch(20), inch(72)),
                     pt(inch(8.46), inch(72)), pt(inch(8.46), inch(72))),
               elevations=(inch(-8.5), inch(-5.94), inch(-5.94), inch(-5.94), inch(-63.19)),
               from_ref="ED-B-WORKSHOP-JB", to_ref="ED-B-WORKSHOP-RC1",
               circuits=("CKT-WORKSHOP-240",)),
    # CKT-RC-BSMT arrives in the bench box as NM; THHN from there to the quad.
    ConduitRun(uid="H969HXHVQ6", tag="CD-B-WORKSHOP-RC2", trade_size=inch(0.75),
               service=Service.POWER_120,
               path=(pt(inch(20), inch(104)), pt(inch(20), inch(104)), pt(inch(20), inch(132)),
                     pt(inch(8.46), inch(132)), pt(inch(8.46), inch(132))),
               elevations=(inch(-8.5), inch(-5.94), inch(-5.94), inch(-5.94), inch(-63.19)),
               from_ref="ED-B-WORKSHOP-JB", to_ref="ED-B-WORKSHOP-RC2",
               circuits=("CKT-RC-BSMT",)),
    # 3/4" EMT capped spare, panel to the TV-wall box: a dedicated AV circuit pulls in later
    # without opening the ceiling. No new circuit now; the panel is nearly full. Off an LB
    # on the panel top and under the gypsum at -1'-1 7/16" (west of PR-B-SAUNA-VENT's x=4'-3
    # 1/2" leg, ducking 1.6" under PR-B-HW-BATH's x=7'-3 5/8" leg and rising back over the
    # vent's x=9'-0" leg, 2.8" over CD-B-KITCHEN and CD-B-DATA-MEDIA: the
    # furnace room has no lane beside those two, W-B-STR3's face is at x=9'-9 1/4"),
    # through W-B-STR2's top plate and RM-B-BATH on CD-B-DATA-MEDIA's lanes one step further
    # from CD-B-KITCHEN, down to their -1'-4 1/4" in the hall and through W-B-CN at
    # y=26'-0" (SP-B-CN-CD-SPARE). Pull boxes at 7 (RM-B-BATH) and 12 (RM-B-PLAY-N): no
    # section passes 360 degrees.
    ConduitRun(uid="FD1J045HS6", tag="CD-B-PLAY-SPARE", trade_size=inch(0.75),
               service=None,
               path=(pt(inch(10), inch(349.375)), pt(inch(40), inch(349.375)),
                     pt(inch(40), inch(243.5)), pt(inch(80), inch(243.5)),
                     pt(inch(82), inch(243.5)), pt(inch(95), inch(243.5)),
                     pt(inch(97), inch(243.5)), pt(inch(162.25), inch(243.5)),
                     pt(inch(162.25), inch(230.75)), pt(inch(194.75), inch(230.75)),
                     pt(inch(194.75), inch(312)), pt(inch(194.75), inch(312)),
                     pt(inch(232.5), inch(312)), pt(inch(232.5), inch(361.5)),
                     pt(inch(321), inch(361.5)), pt(inch(321), inch(414))),
               elevations=(inch(-13.44), inch(-13.44), inch(-13.44), inch(-13.44),
                           inch(-15.05), inch(-15.05), inch(-13.44), inch(-13.44), inch(-13.44),
                           inch(-13.44), inch(-13.44), inch(-16.25), inch(-16.25), inch(-16.25),
                           inch(-16.25), inch(-16.25)),
               pull_points=(7, 12),
               from_ref="ED-B-PANEL", to_ref="ED-B-PLAY-N-JB"),
    # 3/4" EMT + THHN from the TV box to the receptacle behind the panel, down the wall face
    # (face + half the OD); CKT-RC-BSMT's NM enters the box.
    ConduitRun(uid="8XNJPBCK9B", tag="CD-B-PLAY-N-RC1", trade_size=inch(0.75),
               service=Service.POWER_120,
               path=(pt(inch(321), inch(414)), pt(inch(321), inch(423.54)),
                     pt(inch(321), inch(423.54))),
               elevations=(inch(-16.06), inch(-16.06), inch(-75.94)),
               from_ref="ED-B-PLAY-N-JB", to_ref="ED-B-PLAY-N-RC1",
               circuits=("CKT-RC-BSMT",)),
]

BRANCH_SLEEVES = [
    # Cast-in, located before the basement pour (as SP-B-CN-CD-DATA, 1 1/2" north of it).
    SleevePenetration(uid="MKJNJTJKD3", tag="SP-B-CN-CD-SPARE", host_ref="W-B-CN",
                      position=pt(inch(216), inch(312)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.POWER_120,
                      axis="horizontal", center_elevation=inch(-16.25)),
]
