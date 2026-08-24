# haus: editable
# Wind-mitigation seam clamps on the metal skin (owner, 2026-08-20).
#
# Non-penetrating S-5! seam clamps set on the panel seam for one job only: UPLIFT. They carry
# nothing. Distinct from every other S-5! clamp in this plan (``plan/mep_venting.py``,
# ``plan/mep_electrical.py``, ``params/solar.py``), each of which exists to hang an accessory
# off the seam; these exist because a corner is where wind peels a panel off a wall.
#
# **Why corners.** Wind pressure on a building is not uniform: ASCE 7 zones a wall and a roof
# into field, perimeter and corner, and the corner zone sees the highest uplift and suction of
# the three. FM Global DS 1-31 Table 2 — the one prescriptive layout anybody publishes, since
# S-5! itself puts spacing on "the user and/or installer" — adds external seam clamps at CORNER
# clip positions above 90 psf and only reaches the perimeter above 135 psf. So: corners.
#
# **The layout authored here, and what it assumes.**
#   house walls    4 corners x 2 faces x 6 levels = 48 clamps, `S-5-S`. One clamp on the FIRST
#                  SEAM of each face — 8" in from the corner, half the 16" pan module — at
#                  4'-0" vertical centres from +4'-0" to +24'-0". The house siding is snap-lock
#                  (`standing-seam-snaplock`), which is a clipped system, and S-5!'s governing
#                  rule is that clamp spacing must never EXCEED the panel's own clip spacing.
#                  4'-0" is inside any residential clip spacing, so this satisfies it.
#   garage walls   4 corners x 2 faces x 2 levels = 16 clamps, `S-5-N`. The garage wall is
#                  26 ga nail strip, a bulb-and-lip profile that takes the N clamp, not the S.
#                  Only two levels because the wall is 8'-0" tall.
#   garage roof    4 eave corners x 3 seams = 12 clamps, `S-5-N`, on the first three seams in
#                  from each rake, at the eave. The garage roof is nail strip, which has no
#                  concealed clips at all — uplift is resisted by the face-fastened flange
#                  alone — so the corner zone is exactly where a clamp earns its keep.
#
#   ** The main house roof gets NONE, on purpose. ** It is mechanically field-seamed
#   (`standing-seam`): the seam is folded 180 degrees over the clip by a powered seamer, which
#   is already the strongest uplift connection in the metal-roofing catalogue. Adding external
#   clamps to it would be belt over a belt. The 48 PV clamps up there (`params/solar.py`) are
#   a different part doing a different job.
#
# ** THIS IS AN AUTHORED LAYOUT, NOT AN ENGINEERED ONE. ** Nobody has run a site wind speed
# through ASCE 7 to get a design pressure, and no zone width has been calculated — the 8"/4'-0"
# grid above is a reasonable builder's layout, and the count it produces (76) is what the
# estimate bills. If a wind analysis is ever done, S-5! runs a project configurator and a load
# test database at calculators.s-5.com, and the corner/perimeter zone widths come out of ASCE 7
# and FM DS 1-28, not out of this file. Expect the count to move.
#
# Clamps are non-penetrating in both profiles: stainless Torx T-30 setscrews dimple the seam
# without piercing it, so there is no sealant, no flashing and no effect on the panel warranty.
# Setscrews ship with the clamp, so there is no separate fastener line. S-5! does require the
# setscrews to be verified with a DIAL-calibrated torque wrench (explicitly not a clicking one)
# where published load values are relied on, which is a QA pass beyond the screw gun.

from typehaus import Connector, ConnectorKind, ft, pt

MAIN_WIND_CLAMPS = [
    Connector(uid="AN409TVXAB", tag="CN-M-WIND-SWS-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(0)), elevation=ft(4), size="S-5-S"),
    Connector(uid="2FASPJW1PC", tag="CN-M-WIND-SWW-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(0, 8)), elevation=ft(4), size="S-5-S"),
    Connector(uid="JDS2XQYA0V", tag="CN-M-WIND-SWS-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(0)), elevation=ft(8), size="S-5-S"),
    Connector(uid="0BG9WV265B", tag="CN-M-WIND-SWW-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(0, 8)), elevation=ft(8), size="S-5-S"),
    Connector(uid="PRHDGE7W6F", tag="CN-M-WIND-SES-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(0)), elevation=ft(4), size="S-5-S"),
    Connector(uid="JRD1D5QVQR", tag="CN-M-WIND-SEE-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(0, 8)), elevation=ft(4), size="S-5-S"),
    Connector(uid="2KVNMVF7TH", tag="CN-M-WIND-SES-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(0)), elevation=ft(8), size="S-5-S"),
    Connector(uid="ZBEQKM0XHY", tag="CN-M-WIND-SEE-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(0, 8)), elevation=ft(8), size="S-5-S"),
    Connector(uid="TGN0B67HYP", tag="CN-M-WIND-NEN-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(36)), elevation=ft(4), size="S-5-S"),
    Connector(uid="PXTVPBKCC8", tag="CN-M-WIND-NEE-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(35, 4)), elevation=ft(4), size="S-5-S"),
    Connector(uid="MY8FRBASXD", tag="CN-M-WIND-NEN-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(36)), elevation=ft(8), size="S-5-S"),
    Connector(uid="T0NWZ4EXYZ", tag="CN-M-WIND-NEE-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(35, 4)), elevation=ft(8), size="S-5-S"),
    Connector(uid="9XRADF67MN", tag="CN-M-WIND-NWN-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(36)), elevation=ft(4), size="S-5-S"),
    Connector(uid="YA9973Z3P6", tag="CN-M-WIND-NWW-4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(35, 4)), elevation=ft(4), size="S-5-S"),
    Connector(uid="6818X03B14", tag="CN-M-WIND-NWN-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(36)), elevation=ft(8), size="S-5-S"),
    Connector(uid="SRA0QEP02W", tag="CN-M-WIND-NWW-8", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(35, 4)), elevation=ft(8), size="S-5-S"),
]

SECOND_WIND_CLAMPS = [
    Connector(uid="AD23MYP907", tag="CN-S-WIND-SWS-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(0)), elevation=ft(12), size="S-5-S"),
    Connector(uid="P3BQVSTM4Q", tag="CN-S-WIND-SWW-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(0, 8)), elevation=ft(12), size="S-5-S"),
    Connector(uid="HZH59R02ZC", tag="CN-S-WIND-SWS-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(0)), elevation=ft(16), size="S-5-S"),
    Connector(uid="27C5RN9GJ1", tag="CN-S-WIND-SWW-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(0, 8)), elevation=ft(16), size="S-5-S"),
    Connector(uid="3W5KBFGRS3", tag="CN-S-WIND-SES-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(0)), elevation=ft(12), size="S-5-S"),
    Connector(uid="WRTQDQFXST", tag="CN-S-WIND-SEE-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(0, 8)), elevation=ft(12), size="S-5-S"),
    Connector(uid="3T608FSNVS", tag="CN-S-WIND-SES-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(0)), elevation=ft(16), size="S-5-S"),
    Connector(uid="99RM3FV0J4", tag="CN-S-WIND-SEE-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(0, 8)), elevation=ft(16), size="S-5-S"),
    Connector(uid="VFNJAQHW8C", tag="CN-S-WIND-NEN-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(36)), elevation=ft(12), size="S-5-S"),
    Connector(uid="6HP0CACQBB", tag="CN-S-WIND-NEE-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(35, 4)), elevation=ft(12), size="S-5-S"),
    Connector(uid="03KKD0CK9X", tag="CN-S-WIND-NEN-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(36)), elevation=ft(16), size="S-5-S"),
    Connector(uid="4TC6MWHEVH", tag="CN-S-WIND-NEE-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(35, 4)), elevation=ft(16), size="S-5-S"),
    Connector(uid="90FDDDT77P", tag="CN-S-WIND-NWN-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(36)), elevation=ft(12), size="S-5-S"),
    Connector(uid="ZJSAGY96SJ", tag="CN-S-WIND-NWW-12", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(35, 4)), elevation=ft(12), size="S-5-S"),
    Connector(uid="HZSA8PPVZK", tag="CN-S-WIND-NWN-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(36)), elevation=ft(16), size="S-5-S"),
    Connector(uid="J68N6HZERH", tag="CN-S-WIND-NWW-16", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(35, 4)), elevation=ft(16), size="S-5-S"),
]

ATTIC_WIND_CLAMPS = [
    Connector(uid="WSF2PDDJ0W", tag="CN-A-WIND-SWS-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(0)), elevation=ft(20), size="S-5-S"),
    Connector(uid="25WP3B3T42", tag="CN-A-WIND-SWW-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(0, 8)), elevation=ft(20), size="S-5-S"),
    Connector(uid="9A3AR80MJ2", tag="CN-A-WIND-SWS-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(0)), elevation=ft(24), size="S-5-S"),
    Connector(uid="E36BZ5TY52", tag="CN-A-WIND-SWW-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(0, 8)), elevation=ft(24), size="S-5-S"),
    Connector(uid="K78JKMXX2W", tag="CN-A-WIND-SES-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(0)), elevation=ft(20), size="S-5-S"),
    Connector(uid="JGVF0T2BG6", tag="CN-A-WIND-SEE-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(0, 8)), elevation=ft(20), size="S-5-S"),
    Connector(uid="2N6FW3CEY1", tag="CN-A-WIND-SES-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(0)), elevation=ft(24), size="S-5-S"),
    Connector(uid="4WE3GZ9RRG", tag="CN-A-WIND-SEE-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(0, 8)), elevation=ft(24), size="S-5-S"),
    Connector(uid="NFBCN6MP3V", tag="CN-A-WIND-NEN-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(36)), elevation=ft(20), size="S-5-S"),
    Connector(uid="571290M0F7", tag="CN-A-WIND-NEE-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(35, 4)), elevation=ft(20), size="S-5-S"),
    Connector(uid="J0QSM840RK", tag="CN-A-WIND-NEN-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(35, 4), ft(36)), elevation=ft(24), size="S-5-S"),
    Connector(uid="FH3XXZ81M0", tag="CN-A-WIND-NEE-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(36), ft(35, 4)), elevation=ft(24), size="S-5-S"),
    Connector(uid="G7HWVPBKDS", tag="CN-A-WIND-NWN-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(36)), elevation=ft(20), size="S-5-S"),
    Connector(uid="S3W4V8Z371", tag="CN-A-WIND-NWW-20", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(35, 4)), elevation=ft(20), size="S-5-S"),
    Connector(uid="ANPCW5B4NF", tag="CN-A-WIND-NWN-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(36)), elevation=ft(24), size="S-5-S"),
    Connector(uid="HMK4K79SXY", tag="CN-A-WIND-NWW-24", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(35, 4)), elevation=ft(24), size="S-5-S"),
]

GARAGE_WALL_WIND_CLAMPS = [
    Connector(uid="ZMXXXTTBSF", tag="CN-G-WIND-SWS-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(40, 6.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="ZPYEZKF2DG", tag="CN-G-WIND-SWW-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(41, 2.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="BVTX087BDT", tag="CN-G-WIND-SWS-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(40, 6.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="88QT3J6KG5", tag="CN-G-WIND-SWW-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(41, 2.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="BJEDJZK5XC", tag="CN-G-WIND-SES-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(23, 4), ft(40, 6.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="N6WR6E6WXR", tag="CN-G-WIND-SEE-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(24), ft(41, 2.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="NS69RY1MST", tag="CN-G-WIND-SES-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(23, 4), ft(40, 6.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="V1XFQPPM5R", tag="CN-G-WIND-SEE-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(24), ft(41, 2.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="0MAMBGRPN5", tag="CN-G-WIND-NEN-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(23, 4), ft(64, 6.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="6R71B28N71", tag="CN-G-WIND-NEE-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(24), ft(63, 10.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="FZ9TS47AFQ", tag="CN-G-WIND-NEN-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(23, 4), ft(64, 6.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="3Y6N8DPYB3", tag="CN-G-WIND-NEE-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(24), ft(63, 10.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="HADQW5MENK", tag="CN-G-WIND-NWN-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(64, 6.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="F6ZR7QMZR1", tag="CN-G-WIND-NWW-2_5", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(63, 10.875)), elevation=ft(2, 6), size="S-5-N"),
    Connector(uid="1Z32Z8B879", tag="CN-G-WIND-NWN-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(64, 6.875)), elevation=ft(6), size="S-5-N"),
    Connector(uid="J1AARSTCX4", tag="CN-G-WIND-NWW-6_0", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0), ft(63, 10.875)), elevation=ft(6), size="S-5-N"),
]

GARAGE_ROOF_WIND_CLAMPS = [
    Connector(uid="M2BE9KCQQ7", tag="CN-G-WIND-RFSW-1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, -8), ft(39, 2.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="PPM5H4K6EK", tag="CN-G-WIND-RFSW-2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(39, 2.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="QAZ18JEVTF", tag="CN-G-WIND-RFSW-3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(2), ft(39, 2.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="X9PQ5K1CYX", tag="CN-G-WIND-RFSE-1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(24, 8), ft(39, 2.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="6Y59G1FQDX", tag="CN-G-WIND-RFSE-2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(23, 4), ft(39, 2.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="H8GJE348NE", tag="CN-G-WIND-RFSE-3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(22), ft(39, 2.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="QNY7KXYE7F", tag="CN-G-WIND-RFNE-1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(24, 8), ft(65, 10.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="S67JTBKR21", tag="CN-G-WIND-RFNE-2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(23, 4), ft(65, 10.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="5WVHPSXHFD", tag="CN-G-WIND-RFNE-3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(22), ft(65, 10.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="8REEX7CC35", tag="CN-G-WIND-RFNW-1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, -8), ft(65, 10.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="4YB7X5WM5X", tag="CN-G-WIND-RFNW-2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(0, 8), ft(65, 10.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
    Connector(uid="CM84J5D2KA", tag="CN-G-WIND-RFNW-3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(2), ft(65, 10.875)), elevation=ft(7, 11.44),
              connects=("RF-GARAGE",), size="S-5-N"),
]
