"""Direct-mounted MDO edge supports and accessible garage tie-block relief."""

from plan.entry_screen_finish_spec import (
    SUPPORTS,
    PLY_SCREWS,
    PLY_SCREW_HEAD_DIAMETER_IN,
    PLY_SCREW_HEAD_PROJECTION_IN,
    TIE_RELIEF_BOTTOM_IN,
    TIE_RELIEF_START_IN,
    TIE_RELIEF_TOP_IN,
)

from params.north_entry_frame import (
    DECK_JOIST_TOP_FT,
    DECK_SHEET_SOUTH_Y_FT,
    LANDING_WEST_FT,
)
from typehaus import Flashing, RoughOpening, TrimKind, from_node, ft, inch, pt

STUD_EAST_IN = LANDING_WEST_FT * 12 + 1.75
# Trim solids coordinate supplemental timber in the existing stud cavity. Their mass
# is already included in the MDO material's effective areal density.
FINISH_ELEMENTS = [
    Flashing(
        uid=(f"BWMDO{int(support.tag.rsplit('-', 1)[1]):05d}"
             if "NAILER" in support.tag else f"BWMDT{i:05d}"),
        tag=support.tag,
        kind=TrimKind.WRB_COUNTERFLASHING,
        path=(
            pt(inch((support.west_in + support.east_in) / 2),
               ft(DECK_SHEET_SOUTH_Y_FT) + inch(support.station_start_in)),
            pt(inch((support.west_in + support.east_in) / 2),
               ft(DECK_SHEET_SOUTH_Y_FT) + inch(support.station_end_in)),
        ),
        top_elevation=inch(support.top_in),
        depth=inch(support.top_in - support.bottom_in),
        thickness=inch(support.east_in - support.west_in),
        material="kdat",
        host_ref="W-BW-SCREEN",
        vertical=True,
    )
    for i, support in enumerate(SUPPORTS, 1)
]

# Conservative head envelopes are included in the complete service-door sweep. Hidden
# interface screws are installed before the next ply; all axes point west into side grain.
for index, (east, station, elevation) in enumerate(PLY_SCREWS, 1):
    FINISH_ELEMENTS.append(Flashing(
        uid=f"BWMDP{index:05d}", tag=f"TR-BW-MDO-PLY-SCREW-{index}",
        kind=TrimKind.WRB_COUNTERFLASHING,
        path=(pt(inch(east + PLY_SCREW_HEAD_PROJECTION_IN / 2),
                 ft(DECK_SHEET_SOUTH_Y_FT) + inch(station - PLY_SCREW_HEAD_DIAMETER_IN / 2)),
              pt(inch(east + PLY_SCREW_HEAD_PROJECTION_IN / 2),
                 ft(DECK_SHEET_SOUTH_Y_FT) + inch(station + PLY_SCREW_HEAD_DIAMETER_IN / 2))),
        top_elevation=inch(elevation + PLY_SCREW_HEAD_DIAMETER_IN / 2),
        depth=inch(PLY_SCREW_HEAD_DIAMETER_IN), thickness=inch(PLY_SCREW_HEAD_PROJECTION_IN),
        material="entry-screen-white-hardware", host_ref="W-BW-SCREEN"))

FINISH_ELEMENTS.append(
    RoughOpening(
        uid="BWMTIECUT1",
        tag="AO-BW-MDO-TIE-RELIEF",
        host="W-BW-SCREEN",
        position=from_node("N-BW-SCREEN-S", inch(TIE_RELIEF_START_IN)),
        width=inch(79.375 - TIE_RELIEF_START_IN),
        height=inch(TIE_RELIEF_TOP_IN - TIE_RELIEF_BOTTOM_IN),
        sill_height=inch(TIE_RELIEF_BOTTOM_IN - DECK_JOIST_TOP_FT * 12),
        depth=inch(0.750),
        depth_from="interior",
        framing_required=False,
    )
)

# Conservative 3/8in head diameter and 1/8in projection, included in the door sweep.
from plan.entry_screen_finish_spec import PANEL_RUNS_IN  # noqa: E402

for panel, (start, end) in enumerate(PANEL_RUNS_IN, 1):
    rows = [start + 0.375, end - 0.375]
    rows += [s for s in (16, 32, 48, 64) if start + 0.75 < s < end - 0.75]
    for column, station in enumerate(rows):
        edge = column < 2
        count = 9 if edge else 5
        for row in range(count):
            z = 2.375 + row * (47.125 - 2.375) / (count - 1)
            if (
                panel == 4
                and station > TIE_RELIEF_START_IN
                and TIE_RELIEF_BOTTOM_IN - 0.1875 < z < TIE_RELIEF_TOP_IN + 0.1875
            ):
                continue
            FINISH_ELEMENTS.append(
                Flashing(
                    uid=f"BWMDS{panel}{column}{row}",
                    tag=f"TR-BW-MDO-SCREW-{panel}-{column}-{row}",
                    kind=TrimKind.WRB_COUNTERFLASHING,
                    path=(
                        pt(
                            inch(STUD_EAST_IN + 0.8125),
                            ft(DECK_SHEET_SOUTH_Y_FT) + inch(station - 0.1875),
                        ),
                        pt(
                            inch(STUD_EAST_IN + 0.8125),
                            ft(DECK_SHEET_SOUTH_Y_FT) + inch(station + 0.1875),
                        ),
                    ),
                    top_elevation=inch(z + 0.1875),
                    depth=inch(0.375),
                    thickness=inch(0.125),
                    material="entry-screen-white-hardware",
                    host_ref="W-BW-SCREEN",
                )
            )
