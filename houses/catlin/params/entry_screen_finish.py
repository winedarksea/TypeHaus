"""Direct-mounted MDO edge supports, the lower centre timber and the panel screws."""

from plan.entry_screen_finish_spec import SCREEN_LENGTH_IN, SUPPORTS

from params.north_entry_frame import (
    DECK_SHEET_SOUTH_Y_FT,
    GARAGE_CLADDING_Y_FT,
    SCREEN_AXIS_X_FT,
)
from typehaus import Flashing, TrimKind, ft, inch, pt

STUD_EAST_IN = SCREEN_AXIS_X_FT * 12 + 1.75
# The panel schedule is in inches off N-BW-SCREEN-S; hold it to the wall it cuts.
assert abs((GARAGE_CLADDING_Y_FT - DECK_SHEET_SOUTH_Y_FT) * 12 - SCREEN_LENGTH_IN) < 1e-6
# Trim solids coordinate supplemental timber in the existing stud cavity. Their mass
# is already included in the MDO material's effective areal density.
FINISH_ELEMENTS = [
    Flashing(
        uid=(f"BWMDO{int(support.tag.rsplit('-', 1)[1]):05d}"
             if "NAILER" in support.tag else "BWMDT00007"),  # held when nailer -5 went
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

# Conservative 3/8in head diameter and 1/8in projection, included in the door sweep.
from plan.entry_screen_finish_spec import PANEL_RUNS_IN  # noqa: E402

for panel, (start, end) in enumerate(PANEL_RUNS_IN, 1):
    rows = [start + 0.375, end - 0.375]
    rows += [s for s in (16, 32, 48, 64) if start + 0.75 < s < end - 0.75]
    for column, station in enumerate(rows):
        edge = column < 2
        count = 9 if edge else 5
        heights = [(row, 2.375 + row * (47.125 - 2.375) / (count - 1)) for row in range(count)]
        for row, z in heights:
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
