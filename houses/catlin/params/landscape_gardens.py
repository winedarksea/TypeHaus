"""The gardens: two rain gardens, the bluestem grid south of W-RG-BLOCK, the espalier frame.

Filed on ``yard-grade``. Plants are illustrative and unpriced; the basins' media and stone
and the leader extensions price (``prices.toml``). Oracles: notes/rain_garden_sizing.md,
notes/grid_garden.md, notes/espalier_trellis.md.

Coordinates are feet in the house frame (x east, y north). Grade is -2'-10" at the house
and -3'-1" in the garage-side strips; the south yard is -3'-4".
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

# --- rain gardens -----------------------------------------------------------------------
# Two basins, mirrored about the lot's centre line x=18'-0", each hugging its side lot line
# (x=-7' / 43') by 1'-0" and running 35' north beside the garage. Each takes one garage
# leader and one house leader, so each carries 1,110.8 sf of roof and needs 92.6 cf at 1".
# The owner accepted the Manual's 10' lot-line and foundation setbacks falling short on
# 2026-09-21 (~1' and ~6.5' to the garage stem); both report as advisory UNKNOWNs. The
# south ends stay 10.5' clear of the basement corners (0, 36) / (36, 36).
LOT_MID_FT = 18.0
RG_X_W, RG_X_E = -6.0, -1.0         # the west basin; the east is its mirror
RG_Y_S, RG_Y_N = 47.0, 82.0
RG_RIM = ft(-3, -1)                 # the garage-side grade station, both sides
RG_PONDING = inch(12)               # 9" until 2026-09-23: 88.5 cf no longer held the west
RG_SIDE_SLOPE = 2.0                 # run per rise: 2'-0" of slope at 12" of ponding
RG_MEDIA = inch(12)
RG_STONE = inch(6)
_SLOPE_FT = RG_SIDE_SLOPE * RG_PONDING.feet


def _rect(x0: float, y0: float, x1: float, y1: float):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)), pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


# Zone 3 (rim and side slopes): 'Jazz' on the house bluestem grid; zone 1 (the floor):
# switchgrass, 'October Sky' and 'Northwind' alternating, with iris and milkweed. Same
# layout code, same rendering.
_GRID = GridLayout(spacing=inch(15))
# The floor is 1'-0" wide at 12" of ponding: a 6" inset keeps ONE row on its centre line
# (the default half-spacing, 7 1/2", keeps none and the floor went bare).
_FLOOR_GRID = GridLayout(spacing=inch(15), edge_inset=inch(6),
                         type_refs=("PT-PAN-OCTSKY", "PT-PAN-NORTHWIND"))
_MID_SLOPE = ft(RG_RIM.feet - RG_PONDING.feet / 2.0)


def _basin(side: str, uids: tuple[str, str, str, str], bed_prefix: str):
    """A basin and its three beds; ``side`` "W" is authored, "E" is its mirror."""
    x0, x1 = (RG_X_W, RG_X_E) if side == "W" else (2 * LOT_MID_FT - RG_X_E,
                                                       2 * LOT_MID_FT - RG_X_W)
    garden = RainGarden(
        uid=uids[0], tag=f"RG-{side}-BASIN",
        outline=_rect(x0, RG_Y_S, x1, RG_Y_N),
        rim_elevation=RG_RIM, ponding_depth=RG_PONDING, side_slope=RG_SIDE_SLOPE,
        media_depth=RG_MEDIA, media="MnDOT 3877.2 Type G bioretention soil (mix B)",
        stone_depth=RG_STONE, stone="MnDOT 3149 coarse filter aggregate, washed",
        inlet_refs=(f"TR-G-LEADER-{side}", f"TR-RF-LEADER-{side}"),
        # Over the rim at the north end, onto the front yard falling to the street.
        overflow_ref="daylight",
    )
    beds = [
        PlantingBed(uid=uids[1], tag=f"{bed_prefix}-SLOPE-W", type_ref="PT-SCH-JAZZ",
                    outline=_rect(x0, RG_Y_S, x0 + _SLOPE_FT, RG_Y_N),
                    grid=_GRID, ground_elevation=_MID_SLOPE),
        PlantingBed(uid=uids[2], tag=f"{bed_prefix}-SLOPE-E", type_ref="PT-SCH-JAZZ",
                    outline=_rect(x1 - _SLOPE_FT, RG_Y_S, x1, RG_Y_N),
                    grid=_GRID, ground_elevation=_MID_SLOPE),
        PlantingBed(uid=uids[3], tag=f"{bed_prefix}-FLOOR", type_ref="PT-PAN-OCTSKY",
                    outline=_rect(x0 + _SLOPE_FT, RG_Y_S + _SLOPE_FT,
                                  x1 - _SLOPE_FT, RG_Y_N - _SLOPE_FT),
                    grid=_FLOOR_GRID, ground_elevation=ft(RG_RIM.feet - RG_PONDING.feet),
                    accents=AccentRule(type_refs=("PT-IRI-VERS", "PT-ASC-INCA"), every=5,
                                       a=1, b=2)),
    ]
    return garden, beds


RAIN_GARDEN, RG_BEDS = _basin(
    "W", ("GRDNRG0000", "GRDNPB0001", "GRDNPB0002", "GRDNPB0003"), "PB-RG")
# "PB-RGE", not "PB-RG-E": a tag that extends another's prefix double-bills a prefix match.
RAIN_GARDEN_E, RG_E_BEDS = _basin(
    "E", ("XNMR3NGZ8J", "QVSA31HR4Y", "6KFZGTX63Y", "TTEM5PP402"), "PB-RGE")

# --- the Longwood grid ------------------------------------------------------------------
# South of W-RG-BLOCK (south face -33'-10", levelling pad to about -34'-6"), 15" square,
# out to 1'-0" inside the west, east and rear lot lines.
# One accent in nine on a diagonal lattice, mostly 'Moonbeam': from the house and the porch
# the field still reads as one lawn-like texture.
GRID_BED = PlantingBed(
    uid="GRDNPB0004", tag="PB-S-GRID", type_ref="PT-SCH-JAZZ",
    outline=_rect(-6.0, -47.5, 42.0, -34.5),
    grid=_GRID, ground_elevation=ft(-3, -4),
    accents=AccentRule(type_refs=("PT-COR-MOONBEAM", "PT-COR-MOONBEAM", "PT-COR-MOONBEAM",
                                  "PT-SED-ANGELINA", "PT-COR-MOONBEAM", "PT-COR-MOONBEAM",
                                  "PT-COR-MOONBEAM", "PT-HEU-CARAMEL"),
                       every=9, a=1, b=3),
)

# --- the espalier frame -----------------------------------------------------------------
# 2'-0" off the west lot line, in two runs that leave the power line (y=18', 3' deep) its
# 24" locate tolerance zone and more: the posts nearest it stand at y=14' and y=25'. The
# two runs are 13' each, mirrored about y=19'-6", with two apples apiece.
_TRELLIS = dict(post_spacing=ft(8), post="4x4", post_material="kdat", post_height=ft(7),
                post_embed=ft(3), wire_heights=(inch(18), inch(36), inch(54), inch(72)))
TRELLISES = [
    Trellis(uid="GRDNTR0001", tag="TRL-W-S", path=(pt(ft(-5), ft(1)), pt(ft(-5), ft(14))),
            **_TRELLIS),
    Trellis(uid="GRDNTR0002", tag="TRL-W-N", path=(pt(ft(-5), ft(25)), pt(ft(-5), ft(38))),
            **_TRELLIS),
]

MAIN_ELEMENTS = [RAIN_GARDEN, *RG_BEDS, RAIN_GARDEN_E, *RG_E_BEDS, GRID_BED, *TRELLISES]
