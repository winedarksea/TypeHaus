# haus: editable
# Catlin MEP — System 1's sidewall supply branches (plan/mep_hvac.py).
#
# Until 2026-09-23 REG-S-HP-BED1/2/3 named the trunk and nothing reached them: an unmodelled
# "boot through W-S-BW1/2/3's stud bay" that could not have been built. Each was a CEILING
# grille, sat on or beside an FS-ATTIC joist, and reached 1 3/8" into the hall wall.
#
# All three bedrooms are SIDE COLLARS: a 6" stub straight east off the trunk's east face at its
# 100 1/8" centreline, across SF-S-DUCT's empty east lane, through W-S-BW1/2/3 (under
# the plates at 104 3/8") to a high sidewall grille on the bedroom face — the REG-S-HP-STAIR
# idiom with a wall in the way. BED1/2 are on clean 14 1/2" bay centres south of their doors:
# BED1 12'-4" (studs 11'-8"/13'-0"), BED2 19'-8" (studs 19'-0"/20'-4"). Two field items:
# - the 2 5/8" shadow gap between the box's east face (21'-5 1/2") and the wall's hall face
#   (21'-8 1/8") is open to the hall below; close it across the stub with a lining return.
# - the hall face's resilient channel at 96"..98 1/2" is cut in that one bay; no height
#   between the trunk and the plates clears it.
# They are EXPOSED with an authored centreline, as DU-S-HP-SUITE is: a run naming SF-S-DUCT is
# graded across the box's width, and these leave it through its side.
#
# BED3's centre is y=27'-6", above the door header and north of its south king: the 6"
# collar spans y=27'-3"..27'-9", leaving 1/2" to the king's north edge at 27'-2 1/2".
# W-S-BD2's north stud face is farther south, at 26'-9 3/4". EQ-S-ERV-MIX's south end is
# trimmed 1/2" to 27'-11", keeping 2" for hangers beside this branch and the whole return
# grille inside the plenum. This replaces the former attic rise and ceiling boot.
#
# 6" round galvanized at 80 cfm is `size_for_cfm`'s answer: 407 fpm, under Manual D's 700 fpm
# branch limit. BED2/BED3 sit 3/4" under the trunk centre (2026-11-09) so the suite return's
# lane clears their crowns by 1"; hangers re-hung or bracketed off the east plate.
#
# RM-S-SUITE's ducted return (2026-11-09, notes/system1_return_path.md): 80 cfm, balancing the
# 100 supply less the bath's 20, so D-S-SUITE is sealed. 6x4 at 80 cfm is 480 fpm. Two runs: the
# bay leg in FS-ATTIC's y 176-192" bay, then a drop into SF-S-DUCT's east lane to
# EQ-S-ERV-MIX's south face — one run would be graded across the box's whole width.
# 8x4 hits the BED2/BED3 hanger straps at x~249.7". The 24 V cove feeder stays clear of the lane.
#
# RM-S-BED3's ducted return (2026-11-11): 80 cfm, balancing its supply; it replaced the attic
# ERV pickup DU-A-ERV-R-BED3. Moved 2026-11-11 from over D-S-BED3 (15" from REG-S-HP-BED3,
# short-circuiting) to W-S-BW4 in the room's NW corner, 6'-5" north of the supply: a side
# take-off into DU-S-HP-RET's east face, which runs 8 1/4" behind the bedroom face there.
# 6 wide x 12 tall at 80 cfm is 160 fpm, on the south half of the grille's neck: y 404"..410"
# clears BW4's stud at 402" by 1 1/4", SF-S-HP1's east 2x2 at 412 5/8" by 1 7/8", and the
# trunk's turn west (inside corner y=411"). It ends on the trunk's centreline, the take-off
# idiom. EXPOSED for the bedroom-collar reason. Lined stub: the blower is a few feet away
# (open item).

from typehaus import DuctRouting, DuctRun, DuctSystem, ft, inch, pt

DUCTS_HVAC_BRANCHES_SECOND = [
    # 4in at 50 cfm = 573 fpm. Start is inside the trunk; end is the register box back.
    # Elevation follows the grille at the endpoint; the start shares its current centre.
    DuctRun(uid="STAIRBOOT1", tag="DU-S-HP-STAIR", system=DuctSystem.SUPPLY,
            path=(pt(inch(234), inch(282.625)), pt(inch(223.26), inch(282.625))),
            elevations=(inch(101.625), inch(101.625)),
            end_terminal_ref="REG-S-HP-STAIR", diameter=inch(4),
            routing=DuctRouting.EXPOSED, material="galvanized", design_cfm=50),
    # This boot leaves through SF-S-DUCT's east lining between its ladder rails.
    # EXPOSED follows the bedroom-collar idiom: the soffit occupancy check requires
    # named runs to remain inside the box's clear width. Framing clearance is tested.
    DuctRun(uid="STDYBOOT01", tag="DU-S-HP-STUDY2", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), inch(43.5)), pt(inch(261.25), inch(43.5))),
            elevations=(inch(99.125), inch(99.125)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=75),
    DuctRun(uid="AFRBDV5JT6", tag="DU-S-HP-BED1", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(12, 4)), pt(inch(265.375), ft(12, 4))),
            elevations=(inch(100.125), inch(100.125)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
    DuctRun(uid="QBDPVD0HE2", tag="DU-S-HP-BED2", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(19, 8)), pt(inch(265.375), ft(19, 8))),
            elevations=(inch(99.375), inch(99.375)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
    DuctRun(uid="FJGDT6V42D", tag="DU-S-HP-BED3", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(27, 6)), pt(inch(265.375), ft(27, 6))),
            elevations=(inch(99.375), inch(99.375)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
    # Centre 112 1/4" storey: 5/8" over the x=18' pass-through box's bottom rail. Underived,
    # it sat on the bay floor, inside that rail.
    DuctRun(uid="0E3JTBJFFN", tag="DU-S-HP-SUITE-RET", system=DuctSystem.RETURN,
            path=(pt(inch(104), inch(184)), pt(inch(254), inch(184))),
            elevations=(inch(112.25), inch(112.25)),
            width=inch(6), depth=inch(4), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-ATTIC", material="galvanized", design_cfm=80),
    # Centre 105 3/8" storey: 1" over BED2/BED3's crowns, 1/8" under the hall ceiling board.
    DuctRun(uid="3NR7A186BJ", tag="DU-S-HP-SUITE-RET-LANE", system=DuctSystem.RETURN,
            path=(pt(inch(254), inch(184)), pt(inch(254), inch(184)), pt(inch(254), inch(335))),
            elevations=(inch(112.25), inch(105.375), inch(105.375)),
            width=inch(6), depth=inch(4), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", material="galvanized", design_cfm=80),
    DuctRun(uid="2CFDX4Z7TG", tag="DU-S-HP-BED3-RET", system=DuctSystem.RETURN,
            path=(pt(inch(265.25), inch(407)), pt(inch(252), inch(407))),
            elevations=(inch(95), inch(95)),
            width=inch(6), depth=inch(12), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
]
