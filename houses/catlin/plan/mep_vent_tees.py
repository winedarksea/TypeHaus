# haus: editable
# Catlin MEP — vent risers from a trap arm's tee up to the overhead vent header.
#
# The headers in plan/mep_venting.py ran over the fixtures with nothing coming down to the
# drain (C6-E7, 2026-11-01): a vent that never meets its drain vents nothing.
# `mep.trap_arm_developed` walks each arm in 3D to the first tee and is the check these
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
            elevations=(inch(231.555), inch(281.0), inch(281.64)),
            serves=("FX-A-STUBATH-WC",)),
    # RM-A-STUBATH's shower: a tee on the pan's trap drop at (16'-2 5/8", 20'-7 5/8"). The riser
    # cannot go north (the hall trimmer, pan and room) so it runs east 20" in the joist bay, up
    # W-A-C2M's 2x6 cavity, and 20" west in W-A-HALL-S onto PR-A-STUBATH-SH-VENT's low end.
    PipeRun(uid="S9JKFZ4JRT", tag="PR-A-STUBATH-SH-TEE", system=PipeSystem.VENT,
            path=(pt(inch(194.625), inch(247.625)), pt(inch(215), inch(247.625)),
                  pt(inch(215), inch(247.625)), pt(inch(215), inch(268)),
                  pt(inch(194.625), inch(268))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(236), inch(237.4), inch(279.5), inch(280.25), inch(281)),
            serves=("FX-A-STUBATH-SH",)),
    # RM-S-SUITEBATH's water closet (individual vent: its leg is UPSTREAM of the lav and tub
    # ties, so UPC 908.2.1.4 rules a wet vent out). Tees off the arm east of the flange, north
    # through the truss's open web (x 137.5"-150.5"), west under SN3 and up at x=112", west of
    # FO-A-HALL's trimmer and clear of DU-S-ERV-HP-FEED, onto PR-S-SUITEBATH-VENT's header.
    # Lav and tub have no lane yet (the supply risers on y=268" and truss 017 box it in).
    PipeRun(uid="696MGSWX4F", tag="PR-S-SUITEBATH-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(140), inch(252.406)), pt(inch(140), inch(266.8)),
                  pt(inch(140), inch(269.25)), pt(inch(112), inch(269.25)),
                  pt(inch(112), inch(268)), pt(inch(112), inch(268)),
                  pt(inch(112), inch(265))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(116.6), inch(117.6), inch(117.9), inch(118.0), inch(118.2),
                        inch(234.0), inch(236.1)),
            serves=("FX-S-SUITEBATH-WC",)),
    # RM-S-VANITY: the stack vent. The double vanity's arm drops into PR-M-S-BATH1-DRAIN at
    # (5'-0", 26'-8"); the vent leaves the top of that drop 1 1/4" north, rises W-S-BD-N's
    # cavity behind the vanity supplies, and returns to PR-S-BATH1-VENT's corner. Arms:
    # LAV2 ~10", LAV1 ~40" against 42".
    PipeRun(uid="AVXXWYAS1N", tag="PR-S-VANITY-VENT", system=PipeSystem.VENT,
            path=(pt(inch(60), inch(320)), pt(inch(60), inch(321.25)),
                  pt(inch(60), inch(321.25)), pt(inch(60), inch(320))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(139.69), inch(139.75), inch(231.25), inch(231.3)),
            serves=("FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # RM-S-BATH1's lavatory: off its arm 1" short of the drop, 1 3/4" toward the room face
    # so it rises W-S-BA-E1B clear of the lav supplies on the axis, and onto
    # PR-S-BATH1-VENT's start. It rises at y=31'-2 1/2", midway between the two angle stops
    # (y 371.5" / 377.5"); at y=31'-1" it ran through PA-S-BATH1-LAV-CW.
    PipeRun(uid="4HVPN3BWQG", tag="PR-S-BATH1-LAV-VENT", system=PipeSystem.VENT,
            path=(pt(inch(120), inch(373)), pt(inch(118.25), inch(374.5)),
                  pt(inch(118.25), inch(374.5)), pt(inch(116.4), inch(372))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(141.4), inch(141.45), inch(230.9), inch(231.0)),
            serves=("FX-S-BATH1-LAV",)),
    # RM-M-BATH1's wall-hung WC: the DuoFit carrier's own vent outlet, straight up W-M-HS1
    # from the fitting to PR-M-BATH2-LAV-VENT's horizontal at 7'-5 1/8" (6"+ over every rim
    # it serves). Common vent to the x=4'-10" riser: sink 1 + WC 3 + powder lav 1 = 5 DFU,
    # inside a 1 1/2" vent's 8 (MN 4714 Table 703.2). Arm 0".
    PipeRun(uid="28G1YA8JD0", tag="PR-M-BATH1-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(24.5), inch(268)), pt(inch(24.5), inch(268))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(0.95), inch(89.148)),
            serves=("FX-M-BATH1-WC",)),
    # RM-M-BATH2's WC: a tee on the closet bend's drop (x 2'-6", y 21'-0 3/4"), 15 1/4" north
    # under the floor to W-M-HS1's bay, up the wet wall onto PR-M-BATH2-LAV-VENT's header.
    PipeRun(uid="TE1ZQ3VJ98", tag="PR-M-BATH2-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(30), inch(252.74)), pt(inch(30), inch(268)),
                  pt(inch(30), inch(268)), pt(inch(30), inch(268))),
            diameter=inch(2), material="pvc",
            elevations=(inch(-20.5), inch(-19.5), inch(-19.4), inch(89.2)),
            serves=("FX-M-BATH2-WC",)),
    # RM-M-BATH2's shower: a tee on the centre drain's drop, east in its bay and up
    # W-M-BA2E2's cavity, north at the ceiling onto PR-M-BATH2-VENT's end.
    PipeRun(uid="F7XXC9XDK5", tag="PR-M-BATH2-SH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(6, 4.615), ft(14, 11)), pt(inch(98.5), ft(14, 11)),
                  pt(inch(98.5), ft(14, 11)), pt(inch(98.5), ft(14, 11)), pt(inch(98.5), inch(204))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-22.0), inch(-21.5), inch(-21.4), inch(115.9), inch(116)),
            serves=("FX-M-BATH2-SH",)),
    # RM-M-LAUNDRY's sink: a tee at the foot of its drop, under the joists to x=13'-0" (past the
    # HW/CW-WASH ends and PR-M-S-SUITE-DRAIN's stack), up W-M-CLN's cavity behind the basin,
    # then west in the truss bay onto PR-M-BATH2-VENT's riser. Arm ~16".
    PipeRun(uid="BQEVC68G5T", tag="PR-M-LSINK-VENT", system=PipeSystem.VENT,
            path=(pt(inch(144), ft(18, 10.625)), pt(inch(156), inch(216)),
                  pt(inch(156), inch(216)), pt(inch(156), inch(216)),
                  pt(inch(98.5), inch(216))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-15.2), inch(-14.9), inch(-14.8), inch(115.9), inch(116)),
            serves=("FX-M-LAUNDRY-SINK",)),
    # RM-B-BATH's lavatory: a tee at the trap outlet in W-B-CW2, up its cavity, west in it and
    # north in W-B-STR2's to PR-B-BATH-VENT's riser at 1'-6 3/8" under the deck. Arm ~2".
    PipeRun(uid="MFDV1SAVZT", tag="PR-B-BATH-LAV-VENT", system=PipeSystem.VENT,
            path=(pt(inch(144), inch(218.25)), pt(inch(144), inch(216)),
                  pt(inch(144), inch(216)), pt(inch(121.6), inch(216)),
                  pt(inch(121.6), inch(229.5))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(-89.32), inch(-89.27), inch(-19.5), inch(-19.25), inch(-18.6)),
            serves=("FX-B-BATH-LAV",)),
]
