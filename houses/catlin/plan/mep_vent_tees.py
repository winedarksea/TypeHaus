# haus: editable
# Catlin MEP — vent risers from a trap arm's tee up to the overhead vent header.
#
# The headers in plan/mep_venting.py ran over the fixtures with nothing coming down to the
# drain (C6-E7, 2026-11-01): a vent that never meets its drain vents nothing.
# `mep.trap_arm_length` walks each arm in 3D to the first tee and is the check these
# feed; fixtures still listed there as unconnected are the open vent work.
#
# FILED ON ``main`` (datum 0'-0"), like SECOND_DRAINS, so every elevation is project-absolute
# and reads straight against the drains it tees off.

from typehaus import PipeRun, PipeSystem, ft, inch, pt

VENT_TEES = [
    # RM-A-STUBATH's water closet: a sanitary tee at the top of PR-A-STUBATH-DRAIN's drop in
    # W-S-DC2 / W-A-STU-W: a tee on the arm's 1/8 bend at (9'-9", 19'-5 1/2"), up the wet
    # wall's east half beside PR-A-BAR-LAV-HW, and 1 1/2" west onto PR-A-BAR-VENT's
    # horizontal at 3'-5 5/8" over the attic floor. Arm ~23". 1 1/2" is UPC 904.1's half of
    # the 3" drain; a 2" does not pass the hot line in this cavity.
    PipeRun(uid="H6YX0DPRXC", tag="PR-A-STUBATH-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(117), inch(233.5)), pt(inch(117), inch(233.5)),
                  pt(inch(115.5), inch(233.5))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(231.555), inch(283.0), inch(283.55)),
            serves=("FX-A-STUBATH-WC",)),
    # RM-A-STUBATH's shower: plumb from a sanitary tee on its drain at (17'-11", 20'-7 5/8") —
    # the top of a drop in W-A-C2M's cavity, 20 3/8" east of the pan in the joist bay (the riser
    # cannot go north: hall trimmer, pan and room), then 20" along the cavity and 20" west in
    # W-A-HALL-S onto SH-VENT's low end.
    PipeRun(uid="S9JKFZ4JRT", tag="PR-A-STUBATH-SH-TEE", system=PipeSystem.VENT,
            path=(pt(inch(215), inch(247.625)), pt(inch(215), inch(247.625)),
                  pt(inch(215), inch(268)), pt(inch(194.625), inch(268))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(236.55), inch(279.5), inch(280.25), inch(281)),
            serves=("FX-A-STUBATH-SH",)),
    # RM-S-SUITEBATH: three individual vents in W-S-SN3, each plumb off its arm's crown
    # (905.2), ending on PR-S-SUITEBATH-VENT's in-wall leg at ~+17'-10" (FO-A-HALL's trimmer
    # pair fills FS-ATTIC over the wall east of x=10'-0", so nothing rises there).
    # WC: off the collector's loop under the wall at x=11'-10 1/2", up the south half of the
    # cavity (1/2" off PR-S-SUITE-WC-CW), stepping to the axis under the grab-bar backing and
    # 1" west, clear of ED-S-STAIR-SW's box on the hall face.
    PipeRun(uid="696MGSWX4F", tag="PR-S-SUITEBATH-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(142.5), inch(266.25)), pt(inch(142.5), inch(266.25)),
                  pt(inch(141.5), inch(268)), pt(inch(141.5), inch(268)),
                  pt(inch(141.5), inch(266.25))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(116.28), inch(150.5), inch(152.6), inch(213.5), inch(215.39)),
            serves=("FX-S-SUITEBATH-WC",)),
    # Lavatory: off the arm's 3 1/4" tee straight up the axis, 1 7/8" off both stops' lines,
    # then 2" west on a 45 under ED-S-SUITEBATH-MIRROR's box (above the rim's 6", MN 905.3).
    PipeRun(uid="HWQ8NKKF76", tag="PR-S-SUITEBATH-LAV-VENT", system=PipeSystem.VENT,
            path=(pt(inch(165.5), inch(268)), pt(inch(165.5), inch(268)),
                  pt(inch(163.5), inch(268)), pt(inch(163.5), inch(268)),
                  pt(inch(163.5), inch(266.25))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(141.43), inch(190), inch(192.1), inch(212.9), inch(214.77)),
            serves=("FX-S-SUITEBATH-LAV",)),
    # Tub-shower: off the arm 2 3/8" past the trap, 45 deg north through the plate onto the
    # axis at x=16'-5 5/8" (between stud 010 and the cold riser), up to the in-wall leg's head.
    PipeRun(uid="3N5Q44A8PA", tag="PR-S-SUITEBATH-TUB-VENT", system=PipeSystem.VENT,
            path=(pt(inch(197.615), inch(264)), pt(inch(197.615), inch(268)),
                  pt(inch(197.615), inch(268)), pt(inch(197.615), inch(266.25))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(117.38), inch(122.0), inch(212.0), inch(213.8)),
            serves=("FX-S-SUITEBATH-TUBSH",)),
    # RM-S-VANITY: the stack vent. The double vanity's arm drops into PR-M-S-BATH1-DRAIN at
    # (5'-0", 26'-8") from a sanitary tee at the TOP of that drop (140.38", 1.12" under LAV1's
    # weir, inside the 1 1/2" arm diameter). The vent leaves it on a 45 deg leg 1 1/4" north
    # (the lavatory supplies cross x=60" on y=318.75"/319.5" at 146"-150") and rises plumb in
    # W-S-BD-N's cavity past rim+6" (172") to PR-S-BATH1-VENT's corner. Arms: LAV2 ~10",
    # LAV1 ~40" against 42".
    PipeRun(uid="AVXXWYAS1N", tag="PR-S-VANITY-VENT", system=PipeSystem.VENT,
            path=(pt(inch(60), inch(320)), pt(inch(60), inch(321.25)),
                  pt(inch(60), inch(321.25)), pt(inch(60), inch(320))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(140.38), inch(141.7), inch(231.25), inch(231.3)),
            serves=("FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # RM-S-BATH1's lavatory: a sanitary tee at the top of its drop, 3 1/4" (>= 2 x 1 1/2") from
    # the drain point where the arm turns south in W-S-BA-E1B. It rises plumb at x=120" past the
    # lav's rim+6" (172"), clear of the 212" hot, then steps 1 3/4" west (the hot crosses
    # y=374.5" at x=120" and 212") and onto PR-S-BATH1-VENT's start. At y=374.5", midway between
    # the two angle stops (y 371.5" / 377.5"); at y=31'-1" it ran through PA-S-BATH1-LAV-CW.
    PipeRun(uid="4HVPN3BWQG", tag="PR-S-BATH1-LAV-VENT", system=PipeSystem.VENT,
            path=(pt(inch(120), inch(374.5)), pt(inch(120), inch(374.5)),
                  pt(inch(118.25), inch(374.5)), pt(inch(118.25), inch(374.5)),
                  pt(inch(116.4), inch(372))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(141.43), inch(173.0), inch(176.0), inch(230.9), inch(231.0)),
            serves=("FX-S-BATH1-LAV",)),
    # RM-S-BATH1's WC: plumb from the sanitary tee that ends its arm in W-S-BD-N's cavity
    # (20.28", 320.5", 115.5"; arm 56"). A 45 deg+ leg moves it 3/4" north off the drop, clear
    # of the vanity's hot (y=319.5") and the LAV1 drain, and it rises past rim+6" (157") to
    # 231", then east 19 3/4" onto PR-S-BATH1-VENT's corner at x=40".
    PipeRun(uid="HJDACC7GS7", tag="PR-S-BATH1-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(20.278), inch(320.5)), pt(inch(20.278), inch(321.25)),
                  pt(inch(20.278), inch(321.25)), pt(inch(40), inch(320))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(115.5), inch(116.4), inch(231.0), inch(231.5)),
            serves=("FX-S-BATH1-WC",)),
    # RM-S-BATH1's tub-shower: plumb from the sanitary tee at the top of its drop (30 1/4",
    # 402.8", 116.7"), up the chase's south band (clear of EXH riser, CD-M-DATA-PORCH,
    # W-S-CH-W's studs) past the rim+6" (211"), east onto PR-S-BATH1-VENT at 231".
    PipeRun(uid="S57D33HC70", tag="PR-S-BATH1-SH-VENT", system=PipeSystem.VENT,
            path=(pt(inch(30.3), inch(402.8)), pt(inch(30.3), inch(402.8)),
                  pt(inch(40), inch(402.8))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(116.7), inch(231.0), inch(233.7)),
            serves=("FX-S-BATH1-SH",)),
    # RM-M-BATH1's wall-hung WC: the DuoFit carrier's own vent outlet, straight up W-M-HS1
    # from the fitting to PR-M-BATH2-LAV-VENT's horizontal at 7'-5 1/8" (6"+ over every rim
    # it serves). Common vent to the x=4'-10" riser: sink 1 + WC 3 + powder lav 1 = 5 DFU,
    # inside a 1 1/2" vent's 8 (MN 4714 Table 703.2). Arm 0".
    PipeRun(uid="28G1YA8JD0", tag="PR-M-BATH1-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(24.5), inch(268)), pt(inch(24.5), inch(268))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(0.95), inch(89.148)),
            serves=("FX-M-BATH1-WC",)),
    # RM-M-BATH2's WC: a 45 wye on the closet drop 16" under the flange (2 1/2" over
    # CO-B-WC2-HEAD's fitting), NNE under joists 16/17 and the seam joist at -13 1/2" — between
    # the ceiling plane and PR-B-WC1-DRAIN's crown — then up W-M-HS1 at x=3'-1 9/16", east of
    # BATH1's DuoFit carrier, onto PR-M-BATH2-LAV-VENT's header. 1 1/2" (half the 3" drain)
    # because that 2" band has no room for a 2". MN 905.3 is NOT met: no 45-degree path from
    # the bend clears three joists, so the level leg sits below the rim (DESIGN-LOG).
    PipeRun(uid="TE1ZQ3VJ98", tag="PR-M-BATH2-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(30), inch(252.74)), pt(inch(30.7), inch(253.44)),
                  pt(inch(37.5625), inch(268)), pt(inch(37.5625), inch(268))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-14.5), inch(-13.5), inch(-13.45), inch(89.29)),
            serves=("FX-M-BATH2-WC",)),
    # RM-M-BATH2's shower: a sanitary tee at the top of PR-B-SH2-DRAIN's drop under W-M-BA2E2
    # (8'-2", 15'-0 1/2"), 1/2" under the 3" under-floor weir; plumb in the cavity between the
    # face backings to 115.4", over DU-M-ERV-R-SUITEBATH's y=16'-4" leg, then north onto
    # PR-M-BATH2-TUB-VENT's riser. Arm 24".
    PipeRun(uid="F7XXC9XDK5", tag="PR-M-BATH2-SH-VENT", system=PipeSystem.VENT,
            path=(pt(inch(98), inch(180.5)), pt(inch(98), inch(180.5)),
                  pt(inch(98), inch(204))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-3.5), inch(115.4), inch(115.5)),
            serves=("FX-M-BATH2-SH",)),
    # RM-M-BATH2's tub: a sanitary tee at the top of PR-B-TUB2-DRAIN's drop, under W-M-BA2E2
    # at (8'-2", 17'-0") in the 16'-1 1/4"..17'-2 3/4" bay, which has no partition block (the
    # next bay's x=8'-1" block shuts every station there). Plumb in the cavity between
    # stud-002/-001 and the face backings onto PR-M-BATH2-VENT's first leg. Arm 27".
    PipeRun(uid="R0C3TZ3120", tag="PR-M-BATH2-TUB-VENT", system=PipeSystem.VENT,
            path=(pt(inch(98), inch(204)), pt(inch(98), inch(204))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-3.5), inch(115.9)),
            serves=("FX-M-BATH2-TUB",)),
    # RM-M-LAUNDRY's sink: a sanitary tee at the TOP of its drop, where the waste crosses the
    # floor (the trap is the cabinet's). The vent leaves at 46 degrees into W-M-CLN's bay
    # between stud-007 and stud-008, enters the wall 12 1/2" up, rises plumb at (13'-0",
    # 18'-1 1/2") and jogs onto y=18'-0" at the ceiling, clear of the CLN partition blocks'
    # cheeks, onto PR-M-BATH2-VENT. Arm 0"; 15" over CO-B-LSINK's fitting.
    PipeRun(uid="BQEVC68G5T", tag="PR-M-LSINK-VENT", system=PipeSystem.VENT,
            path=(pt(inch(144), ft(18, 10.625)), pt(inch(156), inch(217.5)),
                  pt(inch(156), inch(217.5)), pt(inch(156), inch(216)),
                  pt(inch(98.5), inch(216))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(0), inch(15.5), inch(115.85), inch(115.9), inch(116)),
            serves=("FX-M-LAUNDRY-SINK",)),
    # RM-B-BATH's lavatory: a tee at the trap outlet, a 45-degree rise into W-B-CW2, up its cavity, west in it and
    # north in W-B-STR2's to PR-B-BATH-VENT's riser at 1'-6 3/8" under the deck. Arm ~2".
    PipeRun(uid="MFDV1SAVZT", tag="PR-B-BATH-LAV-VENT", system=PipeSystem.VENT,
            path=(pt(inch(144), inch(218.25)), pt(inch(144), inch(216)),
                  pt(inch(144), inch(216)), pt(inch(121.6), inch(216)),
                  pt(inch(121.6), inch(229.5))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-89.32), inch(-86.8), inch(-19.5), inch(-19.25), inch(-18.6)),
            serves=("FX-B-BATH-LAV",)),
    # RM-B-BATH's water closet: a sanitary tee at the end of the branch's 45-degree run, (10'-0",
    # 20'-0") under W-B-STR2 (arm 70" against Table 1002.2's 72"), plumb in the wall's cavity,
    # then west and south onto PR-B-BATH-VENT's west end at (9'-0", 19'-1 1/2").
    PipeRun(uid="KBNJYZPWCZ", tag="PR-B-BATH-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(120), inch(240)), pt(inch(120), inch(240)),
                  pt(inch(108), inch(240)), pt(inch(108), inch(229.5))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-119.3), inch(-20.9), inch(-19.0), inch(-15.7)),
            serves=("FX-B-BATH-WC",)),
]
