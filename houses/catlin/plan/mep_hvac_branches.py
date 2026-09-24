# haus: editable
# Catlin MEP — System 1's three bedroom supply branches, off DU-S-HP-SUP (plan/mep_hvac.py).
#
# Until 2026-09-23 REG-S-HP-BED1/2/3 named the trunk and nothing reached them: an unmodelled
# "boot through W-S-BW1/2/3's stud bay" that could not have been built. Each was a CEILING
# grille, sat on or beside an FS-ATTIC joist, and reached 1 3/8" into the hall wall.
#
# BED1 and BED2 are SIDE COLLARS: a 6" stub straight east off the trunk's east face at its
# 100 1/8" centreline, across SF-S-DUCT's empty east lane, through W-S-BW1/2's stud bay (under
# the plates at 104 3/8") to a high sidewall grille on the bedroom face — the REG-S-HP-STAIR
# idiom with a wall in the way. Each stub is on a clean 14 1/2" bay centre south of its door:
# BED1 12'-4" (studs 11'-8"/13'-0"), BED2 19'-8" (studs 19'-0"/20'-4"). Two field items:
# - the 2 5/8" shadow gap between the box's east face (21'-5 1/2") and the wall's hall face
#   (21'-8 1/8") is open to the hall below; close it across the stub with a lining return.
# - the hall face's resilient channel at 96"..98 1/2" is cut in that one bay; no height
#   between the trunk and the plates clears it.
# They are EXPOSED with an authored centreline, as DU-S-HP-SUITE is: a run naming SF-S-DUCT is
# graded across the box's width, and these leave it through its side.
#
# BED3 cannot do this: north of 27'-8" the trunk is in SF-S-HP1 beside the return plenum. It
# is the DU-S-HP-SOUTH idiom instead — a RISER out of the trunk inside SF-S-DUCT, then a leg
# EAST in the 27'-4" FS-ATTIC bay (the last inside SF-S-DUCT) over the hall wall's plates to
# an unmodelled 90 degree ceiling boot. Two runs, because a run carries one `routing`. The bay
# sits over BED3's SOUTH edge — joist 020 bears on W-S-BD2 — and the grille lands ~6" north
# of that wall's face. Riser elevations: 100 1/8" is the trunk's centreline (the tee), 111 1/8"
# the centreline a 6" duct derives in an FS-ATTIC bay.
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
    DuctRun(uid="BT159ZSXAT", tag="DU-S-HP-BED3-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(27, 4)), pt(ft(19, 6), ft(27, 4))),
            elevations=(inch(100.125), inch(111.125)),
            diameter=inch(6), routing=DuctRouting.SOFFIT, soffit_ref="SF-S-DUCT",
            material="galvanized", design_cfm=80),
    DuctRun(uid="FJGDT6V42D", tag="DU-S-HP-BED3", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(27, 4)), pt(ft(22, 9), ft(27, 4))),
            diameter=inch(6), routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC",
            material="galvanized", design_cfm=80),
]
