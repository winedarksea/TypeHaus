# haus: editable
# Catlin MEP — System 1's three bedroom supply branches, off DU-S-HP-SUP (plan/mep_hvac.py).
#
# Until 2026-09-23 REG-S-HP-BED1/2/3 named the trunk and nothing reached them: an unmodelled
# "boot through W-S-BW1/2/3's stud bay" that could not have been built. Each grille sat on or
# beside an FS-ATTIC joist, reached 1 3/8" into the hall wall, and BED3's was north of the
# point where the trunk leaves SF-S-DUCT for SF-S-HP1, beside the return plenum.
#
# Each branch is the DU-S-HP-SOUTH idiom: a RISER standing up out of the trunk inside
# SF-S-DUCT, then a bay leg running EAST in one FS-ATTIC bay to a 90 degree ceiling boot
# (unmodelled, like REG-S-HP-STUDY2's). Two runs, because a run carries one `routing` and one
# `soffit_ref`. The leg rides over the hall wall's top plates (104 3/8"..107 3/8"), so nothing
# is bored or notched.
#
# FS-ATTIC joists run in x at y=16n, so a bay is centred on 8" + 16n:
# - BED1 at 12'-8": 14'-0" would crowd DU-S-HP-SUITE's tee at 14'-1 7/8"; south of D-S-BED1.
# - BED2 at 20'-8": the 22'-0" bay holds DU-S-ERV-HP-FEED; south of D-S-BED2.
# - BED3 at 27'-4": the last bay inside SF-S-DUCT (it ends at 27'-8"). It sits over BED3's
#   SOUTH edge — joist 020 bears on W-S-BD2 — and the grille lands ~6" north of that wall's
#   face. A sidewall grille IN W-S-BD2 is not buildable: a 2x4 cannot take a 6" boot.
#
# 6" round galvanized at 80 cfm is `size_for_cfm`'s answer: 407 fpm, under Manual D's 700 fpm
# branch limit. Riser elevations are storey-relative: 100 1/8" is the trunk's centreline (the
# tee), 111 1/8" the centreline a 6" duct derives in an FS-ATTIC bay.

from typehaus import DuctRouting, DuctRun, DuctSystem, ft, inch, pt

DUCTS_HVAC_BRANCHES_SECOND = [
    DuctRun(uid="Y85GQW7GD3", tag="DU-S-HP-BED1-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(12, 8)), pt(ft(19, 6), ft(12, 8))),
            elevations=(inch(100.125), inch(111.125)),
            diameter=inch(6), routing=DuctRouting.SOFFIT, soffit_ref="SF-S-DUCT",
            material="galvanized", design_cfm=80),
    DuctRun(uid="AFRBDV5JT6", tag="DU-S-HP-BED1", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(12, 8)), pt(ft(22, 9), ft(12, 8))),
            diameter=inch(6), routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC",
            material="galvanized", design_cfm=80),
    DuctRun(uid="JH7KT62NJN", tag="DU-S-HP-BED2-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(20, 8)), pt(ft(19, 6), ft(20, 8))),
            elevations=(inch(100.125), inch(111.125)),
            diameter=inch(6), routing=DuctRouting.SOFFIT, soffit_ref="SF-S-DUCT",
            material="galvanized", design_cfm=80),
    DuctRun(uid="QBDPVD0HE2", tag="DU-S-HP-BED2", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(20, 8)), pt(ft(22, 9), ft(20, 8))),
            diameter=inch(6), routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC",
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
