# haus: editable
# Catlin MEP — concrete penetrations — the sleeves and stubs cast into slabs and walls.
#
# plan/mep.py re-exports the storey lists below (AGENTS.md §1.1), so the manifest is
# unchanged.
#
# Positions are the exact pre-pour centers the concrete crew works from, validated against
# the fixture drain point (`mep.sleeve_alignment`); nothing here is derived. Framed-floor
# drops (e.g. the second-floor hall bath into wet wall W-S-BD-N) need no sleeve at all.
#
# SL-M-DECK is the 414 SF concrete band over the dining end only (x 18'-36', y 13'-36'); the
# other 819 SF is FS-M-WEST and FS-M-EAST, I-joists at 16" o.c. A pipe crossing a joist bay
# is bored or dropped between the joists on site — nothing to cast, nothing to get wrong
# before the pour, which is the only reason a SleevePenetration exists. What survives is the
# kitchen group at x 28'-29', inside the band and passing through 12 5/8" of deck.

from typehaus import (
    PipeRun,
    Service,
    SleevePenetration,
    ft,
    inch,
    pt,
)
from typehaus.model import m

SLEEVES = [
    # Authored at FX-M-KITCH-SINK's `drain_position` (0.00" alignment) — see fixtures.py.
    SleevePenetration(uid="BFQH6F04VQ", tag="SP-M-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(29, 4), ft(35)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-KITCH-SINK"),
]

# Supply risers through the concrete band — every hot/cold branch crossing SL-M-DECK still
# needs its own cast-in sleeve (`mep.sleeve_coverage`). Only the kitchen's pair is left: the
# bath, laundry and suite risers all rise through joist bays now.
SUPPLY_SLEEVES = [
    # Same offset magnitude from the sink centre as SP-M-KITCH above.
    SleevePenetration(uid="CMPS07AAAA", tag="SP-M-CW-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(29, 9.6), ft(34, 1.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS08AAAA", tag="SP-M-HW-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(30, 3.6), ft(33, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
]

# Second-storey waste stacks. The upstairs bathrooms drain down through framed walls and
# floors — joists everywhere they land, not concrete. Empty, and kept rather than deleted
# so plan/mep.py's re-export and the manifest stay as they are, and so the next stack that
# does cross the band has an obvious home.
STACK_SLEEVES = []

# Slab-on-grade stub-ups. A fixture on grade has no wall drain stack — its trap arm runs
# *under* the slab — so the penetration is set pre-pour like the deck sleeves above, at the
# fixture's own `drain_position` for an exact alignment match: a bathroom at the stair foot,
# and the sauna's shower end (curbed pan + floor drain).
SLAB_STUBS = [
    # Upsized to 3" for a WC (needing a closet bend) in place of the old utility sink.
    SleevePenetration(uid="CBP901AAAA", tag="SP-B-BATH-WC", host_ref="SL-B-FLOOR",
                      position=pt(ft(11, 8), ft(20)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-B-BATH-WC"),
    SleevePenetration(uid="CBP904AAAA", tag="SP-B-BATH-LAV", host_ref="SL-B-FLOOR",
                      position=pt(ft(17), ft(20)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-B-BATH-LAV"),
    # The sauna's two. The pan's is under the centre of the 36" x 36" curbed shower; the floor
    # drain's is the drain body itself, which is why its position and the fixture's are the
    # same point with no `drain_position` override on either.
    SleevePenetration(uid="CBP905AAAA", tag="SP-B-SAUNA-SH", host_ref="SL-B-FLOOR",
                      position=pt(ft(15, 8.5), ft(12, 0.1875)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-SH"),
    SleevePenetration(uid="CBP906AAAA", tag="SP-B-SAUNA-FD", host_ref="SL-B-FLOOR",
                      position=pt(ft(13, 6), ft(12, 0.1875)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-FD"),
    # Where the ceiling collector turns down to become the under-slab building drain; 4",
    # matching the building drain. `mep.sleeve_coverage` holds the crossing.
    SleevePenetration(uid="CBP902AAAA", tag="SP-B-SLAB-MAIN", host_ref="SL-B-FLOOR",
                      position=pt(ft(3), ft(15, 6)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6)),
]

# Horizontal sleeves through the basement's cast concrete walls: every ceiling-level run
# crossing the y=18' centre walls or the perimeter is a cast-in hole (`mep.sleeve_coverage`).
# center_elevation is project-frame absolute (the walls span -9'-1 7/16"..-13 7/16");
# positions along y=18' keep >= 5" between neighbours so the 4"-tolerance matcher stays
# unambiguous.
#
# SP-B-CS2-KITCH and SP-B-SEWER-EXIT — the drains' own crossings — carry re-stated absolute
# elevations, since every ``PipeRun.elevations`` in this house is basement-storey-relative
# and these sleeves are the only absolute numbers in the drainage path.
# ``mep.sewer_exit_invert`` is what would catch a mismatch.
#
# What is left crosses concrete that is still concrete: the x=18' bearing line
# (W-B-CS2/W-B-CN), the perimeter, and the footings. Every crossing of a framed wall
# (W-B-CW, W-B-CW2, W-B-CW3, W-B-CE, W-B-STR2, W-B-CS) takes a bored hole on the day, not a
# sleeve set before a pour.
WALL_SLEEVES = [
    # W-B-CS2 (x=18', y 13'-10"..18') — the kitchen drain's crossing of the centre line,
    # up at the ceiling well above D-B-GYM's 6'-8" head.
    SleevePenetration(uid="CBPW15AAAA", tag="SP-B-CS2-KITCH", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(16, 6)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=inch(-21.8571)),
    SleevePenetration(uid="CBPW21AAAA", tag="SP-B-CS2-CW", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(16)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-1.1933)),
    SleevePenetration(uid="CBPW22AAAA", tag="SP-B-CS2-HW", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(15, 6)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-1.3033)),
    # PR-B-COND crosses W-B-CS (2x6 stud, not concrete) with a bored hole, not a sleeve —
    # same reasoning as the framed-wall crossings above.
    # Perimeter exits.
    # Building drain leaves *under* FT-B-S1, not through W-B-S1 (2026-07-30): the walls stop
    # at -9'-4" (the slab top), below the sewer connection, so this is an under-footing
    # protection sleeve (IRC P2604, `mep.footing_clearance`) at the footing centerline.
    # center_elevation = invert (-10'-3 11/16") + half the 4" pipe = -125.7055", matched to
    # within 1/2" by `mep.sewer_exit_invert`.
    SleevePenetration(uid="CBPW18AAAA", tag="SP-B-SEWER-EXIT", host_ref="FT-B-S1",
                      position=pt(ft(3), ft(0)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6), axis="horizontal",
                      center_elevation=inch(-125.7055)),
    # The water service's one wall crossing. It follows PR-G-HYDRANT-CW down to -8'-10": the
    # run holds 6' under a grade of -2'-10", and a sleeve that stayed at -6'-0" would be a
    # bore the pipe misses by 2'-10". It sits 6" above the basement walls' own bottom, which
    # is as low as this crossing can go before it is in the footing instead.
    #
    # With the service entry at the front of the lot (plan/site.py) the lateral enters the
    # house exactly once: this is the ENTRY, the only crossing, and the point
    # PR-B-CW-TRUNK tees off at.
    SleevePenetration(uid="CBPW20AAAA", tag="SP-B-N3-HYD", host_ref="W-B-N4",
                      position=pt(ft(5), ft(35, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-8, -10)),
]

# The hydrant line's garage-foundation protection (IRC P2604): the buried run passes 22"
# below FT-GF-S-DR's 6'-8" bearing plane, on its centerline, inside a protection sleeve —
# being *under* a footing is the worst case in its 45° influence cone, not clearance from it.
#
# `mep.footing_clearance` requires the run to actually thread the sleeve, not merely pass
# near the footing (checks/mep/plumbing_concrete.py) — see params/foundations.py for the
# hydrant's station at (5'-0", 59'-6"), chosen to clear the west footing entirely.
GARAGE_SLEEVES = [
    # It crosses the garage's south foundation line at x=5'-0", at -8'-10", inside a 2"
    # protection sleeve. `host_ref=FT-GF-S1` because D-G-SERVICE's jambs sit on the stud
    # module (SERVICE_DOOR_OFFSET, params/foundations.py), which put the grade beam under
    # the door (FT-GF-S-DR) east of this crossing — x=5'-0" is now under the ordinary stem
    # footing beside it. `integrity.sleeve_in_opening` catches a sleeve naming a host it no
    # longer sits in.
    SleevePenetration(uid="CGPW01AAAA", tag="SP-GF-S-HYD", host_ref="FT-GF-S1",
                      position=pt(ft(5), ft(41, 0.875)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-8, -10)),
]
