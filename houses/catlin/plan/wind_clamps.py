# haus: editable
# Wind-mitigation seam clamps on the metal skin.
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
# ** THE 48 HOUSE-WALL CLAMPS ARE GONE, AND NOT AS AN ECONOMY. ** They were `S-5-S`, and an
# S clamp closes on a snap-lock leg. The house walls are now `pbr-panel-26` — an
# exposed-fastener PBR panel with no seam of any kind — so there is nothing left for the
# clamp to grip and the part is not merely unnecessary but uninstallable. What resisted
# corner uplift through those clamps is now resisted by the panel's own face-fastened
# screws, which pass through the panel into the girt at every rib flat and every course:
# `takeoff.fasteners.exposed_fastener_cladding_screw_rows` bills 2,623 of them on the house
# walls, and they are already denser at a corner than the 8"/4'-0" grid below ever was.
#
# **The layout that remains, and what it assumes.**
#   garage walls   NONE — see the paragraph above the list below. It was 4 corners x 2
#                  faces x 2 levels = 16 `S-5-N`, back when the wall was 26 ga nail strip;
#                  a corrugated panel has no seam to clamp.
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
# ** THIS IS AN AUTHORED LAYOUT, NOT AN ENGINEERED ONE. ** `plan/site.py` carries a design
# wind speed (V_ult = 115 mph, Exposure B, Risk Category II, MN Rules 1309.0301), so the
# *first* missing input is not missing — but nobody has run it through ASCE 7 Ch. 30 to get
# a design pressure, and **no zone width has been calculated**, which is the input this
# layout actually turns on. A clamp grid is a map of corner/perimeter/field zones; having V
# without the zone map buys nothing. The grid above is a reasonable builder's layout, and
# the count it produces (12, all on the garage ROOF) is what the estimate bills. The same
# caveat covers both the HOUSE and the GARAGE walls, in a different form: the screw
# schedule that replaced the clamps there is a uniform field grid, so it carries no
# corner-zone densification at all. **That densification is the lever** if a wind analysis
# is ever run — tightening the screw pitch in the corner zone, not re-authoring clamps onto
# a panel that cannot take them. If one is done, S-5! runs a project configurator and a load
# test database at calculators.s-5.com, and the corner/perimeter zone widths come out of
# ASCE 7 and FM DS 1-28, not out of this file. Expect the count to move.
#
# Clamps are non-penetrating in both profiles: stainless Torx T-30 setscrews dimple the seam
# without piercing it, so there is no sealant, no flashing and no effect on the panel warranty.
# Setscrews ship with the clamp, so there is no separate fastener line. S-5! does require the
# setscrews to be verified with a DIAL-calibrated torque wrench (explicitly not a clicking one)
# where published load values are relied on, which is a QA pass beyond the screw gun.

from typehaus import Connector, ConnectorKind, ft, pt

# ** THE 16 GARAGE-WALL CLAMPS ARE GONE TOO, for the same reason and by the same argument.
# ** They were `S-5-N`, and an N clamp closes on a nail strip's bulb-and-lip seam.
# GARAGE_WALL_2X6 is `corrugated-panel-26` now — a 7/8" corrugated exposed-fastener panel
# with no seam of any kind — so the part is uninstallable there, not merely unneeded. What
# resisted corner uplift through them is resisted by the panel's own face screws:
# `exposed_fastener_cladding_screw_rows` bills 640 over the four garage walls (500 field +
# 140 sidelap), where the retired grid was 16 clamps at two levels. The NAME survives as an
# empty list rather than being deleted: `plan/manifest.py` splices it, and the swap back —
# `CATLIN_EXT_2X6_SWINBURNE`'s convention — is then re-authoring the sixteen constructors
# here and nothing else. The `S-5-N` PRICE ROW stays too, because the garage ROOF is still
# nail strip and still carries 12 of them.
GARAGE_WALL_WIND_CLAMPS = []

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
