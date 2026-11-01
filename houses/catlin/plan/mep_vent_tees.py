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

from typehaus import PipeRun, PipeSystem, inch, pt

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
    # PR-S-BATH1-VENT's start.
    PipeRun(uid="4HVPN3BWQG", tag="PR-S-BATH1-LAV-VENT", system=PipeSystem.VENT,
            path=(pt(inch(120), inch(373)), pt(inch(118.25), inch(373)),
                  pt(inch(118.25), inch(373)), pt(inch(116.4), inch(372))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(141.4), inch(141.45), inch(230.9), inch(231.0)),
            serves=("FX-S-BATH1-LAV",)),
]
