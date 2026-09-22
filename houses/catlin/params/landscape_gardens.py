"""The gardens: the west rain garden, the bluestem grid south of W-RG-BLOCK, the espalier frame.

Filed on ``yard-grade``. Plants are illustrative and unpriced; the basin's media and stone
and the leader extensions price (``prices.toml``). Oracles: notes/rain_garden_sizing.md,
notes/grid_garden.md, notes/espalier_trellis.md.

Coordinates are feet in the house frame (x east, y north). Grade is -2'-10" at the house
and -3'-1" in the garage-west strip; the south yard is -3'-4".
"""

from __future__ import annotations

from typehaus import (
    AccentRule,
    GridLayout,
    PlantingBed,
    RainGarden,
    Trellis,
    ft,
    inch,
    pt,
)

# --- rain garden ------------------------------------------------------------------------
# Hugs the west lot line (x=-7') by 1'-0", as far from the garage as the lot allows: the
# owner accepted the Manual's 10' lot-line and foundation setbacks falling short on
# 2026-09-21 (~1' and ~6' here); both report as advisory UNKNOWNs. The south end stays
# 11' clear of the house basement corner (0, 36).
RG_X_W, RG_X_E = -6.0, -1.0
RG_Y_S, RG_Y_N = 47.0, 82.0
RG_RIM = ft(-3, -1)                 # the garage-west grade station
RG_PONDING = inch(9)
RG_SIDE_SLOPE = 2.0                 # run per rise: 1'-6" of slope at 9" of ponding
RG_MEDIA = inch(12)
RG_STONE = inch(6)
_SLOPE_FT = RG_SIDE_SLOPE * RG_PONDING.feet


def _rect(x0: float, y0: float, x1: float, y1: float):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)), pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


RAIN_GARDEN = RainGarden(
    uid="GRDNRG0000", tag="RG-W-BASIN",
    outline=_rect(RG_X_W, RG_Y_S, RG_X_E, RG_Y_N),
    rim_elevation=RG_RIM, ponding_depth=RG_PONDING, side_slope=RG_SIDE_SLOPE,
    media_depth=RG_MEDIA, media="MnDOT 3877.2 Type G bioretention soil (mix B)",
    stone_depth=RG_STONE, stone="MnDOT 3149 coarse filter aggregate, washed",
    inlet_refs=("TR-G-LEADER-W", "TR-RF-LEADER-W"),
    # Over the rim at the north end, onto the front yard falling to the street.
    overflow_ref="daylight",
)

# Zone 3 (rim and side slopes): 'Jazz' on the house bluestem grid; zone 1 (the floor):
# fox sedge with iris and milkweed. Same layout code, same rendering.
_GRID = GridLayout(spacing=inch(15))
_MID_SLOPE = ft(RG_RIM.feet - RG_PONDING.feet / 2.0)
RG_BEDS = [
    PlantingBed(uid="GRDNPB0001", tag="PB-RG-SLOPE-W", type_ref="PT-SCH-JAZZ",
                outline=_rect(RG_X_W, RG_Y_S, RG_X_W + _SLOPE_FT, RG_Y_N),
                grid=_GRID, ground_elevation=_MID_SLOPE),
    PlantingBed(uid="GRDNPB0002", tag="PB-RG-SLOPE-E", type_ref="PT-SCH-JAZZ",
                outline=_rect(RG_X_E - _SLOPE_FT, RG_Y_S, RG_X_E, RG_Y_N),
                grid=_GRID, ground_elevation=_MID_SLOPE),
    PlantingBed(uid="GRDNPB0003", tag="PB-RG-FLOOR", type_ref="PT-CAR-VULP",
                outline=_rect(RG_X_W + _SLOPE_FT, RG_Y_S + _SLOPE_FT,
                              RG_X_E - _SLOPE_FT, RG_Y_N - _SLOPE_FT),
                grid=_GRID, ground_elevation=ft(RG_RIM.feet - RG_PONDING.feet),
                accents=AccentRule(type_refs=("PT-IRI-VERS", "PT-ASC-INCA"), every=5,
                                   a=1, b=2)),
]

# --- the Longwood grid ------------------------------------------------------------------
# South of W-RG-BLOCK (south face -33'-10", levelling pad to about -34'-6"), 15" square.
# One accent in nine on a diagonal lattice, mostly 'Moonbeam': from the house and the porch
# the field still reads as one lawn-like texture.
GRID_BED = PlantingBed(
    uid="GRDNPB0004", tag="PB-S-GRID", type_ref="PT-SCH-JAZZ",
    outline=_rect(4.0, -46.0, 32.0, -34.5),
    grid=_GRID, ground_elevation=ft(-3, -4),
    accents=AccentRule(type_refs=("PT-COR-MOONBEAM", "PT-COR-MOONBEAM", "PT-COR-MOONBEAM",
                                  "PT-SED-ANGELINA", "PT-COR-MOONBEAM", "PT-COR-MOONBEAM",
                                  "PT-COR-MOONBEAM", "PT-HEU-CARAMEL"),
                       every=9, a=1, b=3),
)

# --- the espalier frame -----------------------------------------------------------------
# 2'-0" off the west lot line, in two runs that leave the power line (y=18', 3' deep) its
# 24" locate tolerance zone and more: the posts nearest it stand at y=14' and y=25'.
_TRELLIS = dict(post_spacing=ft(8), post="4x4", post_material="kdat", post_height=ft(7),
                post_embed=ft(3), wire_heights=(inch(18), inch(36), inch(54), inch(72)))
TRELLISES = [
    Trellis(uid="GRDNTR0001", tag="TRL-W-S", path=(pt(ft(-5), ft(1)), pt(ft(-5), ft(14))),
            **_TRELLIS),
    Trellis(uid="GRDNTR0002", tag="TRL-W-N", path=(pt(ft(-5), ft(25)), pt(ft(-5), ft(31))),
            **_TRELLIS),
]

MAIN_ELEMENTS = [RAIN_GARDEN, *RG_BEDS, GRID_BED, *TRELLISES]
