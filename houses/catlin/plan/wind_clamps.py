# haus: editable
# Wind-mitigation seam clamps on the metal skin (owner, 2026-08-20; house walls retired
# 2026-08-26).
#
# Non-penetrating S-5! seam clamps set on the panel seam for one job only: UPLIFT. They carry
# nothing. Distinct from every other S-5! clamp in this plan (``plan/mep_venting.py``,
# ``params/solar.py``), each of which exists to hang an accessory off the seam; these exist
# because a corner is where wind peels a panel off a wall.
#
# **Why corners.** Wind pressure on a building is not uniform: ASCE 7 zones a wall and a roof
# into field, perimeter and corner, and the corner zone sees the highest uplift and suction of
# the three. FM Global DS 1-31 Table 2 — the one prescriptive layout anybody publishes, since
# S-5! itself puts spacing on "the user and/or installer" — adds external seam clamps at CORNER
# clip positions above 90 psf and only reaches the perimeter above 135 psf. So: corners.
#
# ** THE 48 HOUSE-WALL CLAMPS ARE GONE (2026-08-26), AND NOT AS AN ECONOMY. ** They were
# `S-5-S`, and an S clamp closes on a snap-lock leg. The house walls are now
# `pbr-panel-26` — an exposed-fastener PBR panel with no seam of any kind — so there is
# nothing left for the clamp to grip and the part is not merely unnecessary but
# uninstallable. What resisted corner uplift through those clamps is now resisted by the
# panel's own face-fastened screws, which pass through the panel into the girt at every
# rib flat and every course: `takeoff.fasteners.exposed_fastener_cladding_screw_rows`
# bills 3,098 of them, and they are already denser at a corner than the 8"/4'-0" grid
# below ever was.
#
# **The layout that remains, and what it assumes.**
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
# through ASCE 7 to get a design pressure, and no zone width has been calculated — the grid
# above is a reasonable builder's layout, and the count it produces (28) is what the estimate
# bills. That caveat now covers the HOUSE WALLS TOO, in a different form: the screw schedule
# that replaced the clamps there is a uniform field grid, so it carries no corner-zone
# densification at all. **That densification is the lever** if a wind analysis is ever run —
# tightening the screw pitch in the corner zone, not re-authoring clamps onto a panel that
# cannot take them. If one is done, S-5! runs a project configurator and a load test database
# at calculators.s-5.com, and the corner/perimeter zone widths come out of ASCE 7 and FM
# DS 1-28, not out of this file. Expect the count to move.
#
# Clamps are non-penetrating in both profiles: stainless Torx T-30 setscrews dimple the seam
# without piercing it, so there is no sealant, no flashing and no effect on the panel warranty.
# Setscrews ship with the clamp, so there is no separate fastener line. S-5! does require the
# setscrews to be verified with a DIAL-calibrated torque wrench (explicitly not a clicking one)
# where published load values are relied on, which is a QA pass beyond the screw gun.

from typehaus import Connector, ConnectorKind, ft, pt

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
