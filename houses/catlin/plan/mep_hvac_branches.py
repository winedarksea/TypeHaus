# haus: editable
# Catlin MEP — System 1's three bedroom supply branches, off DU-S-HP-SUP (plan/mep_hvac.py).
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
# branch limit.

from typehaus import DuctRouting, DuctRun, DuctSystem, ft, inch, pt

DUCTS_HVAC_BRANCHES_SECOND = [
    DuctRun(uid="AFRBDV5JT6", tag="DU-S-HP-BED1", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(12, 4)), pt(inch(265.375), ft(12, 4))),
            elevations=(inch(100.125), inch(100.125)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
    DuctRun(uid="QBDPVD0HE2", tag="DU-S-HP-BED2", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(19, 8)), pt(inch(265.375), ft(19, 8))),
            elevations=(inch(100.125), inch(100.125)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
    DuctRun(uid="FJGDT6V42D", tag="DU-S-HP-BED3", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(27, 6)), pt(inch(265.375), ft(27, 6))),
            elevations=(inch(100.125), inch(100.125)),
            diameter=inch(6), routing=DuctRouting.EXPOSED,
            material="galvanized", design_cfm=80),
]
