"""East cassette head and base flashing; brace cap remains independently drained."""
from plan.entry_screen_finish_spec import FINISH_BOTTOM_IN, FINISH_TOP_IN, PANEL_RUNS_IN

from params.north_entry_frame import (
    DECK_SHEET_SOUTH_Y_FT,
    LANDING_WEST_FT,
)
from typehaus import Flashing, FormedFlashingSection, TrimKind, ft, inch, pt

STUD_EAST_IN = LANDING_WEST_FT * 12 + 1.75
FLASHING_NOSE_IN = LANDING_WEST_FT * 12 + 2.75 - 0.1875
FLASHING_WIDTH_IN = FLASHING_NOSE_IN - STUD_EAST_IN


def _run(tag, uid, top, start, end, *, upstand):
    centre = (STUD_EAST_IN + FLASHING_NOSE_IN) / 2
    return Flashing(
        uid=uid, tag=tag, kind=TrimKind.DRIP_FLASHING,
        path=(pt(inch(centre), ft(DECK_SHEET_SOUTH_Y_FT) + inch(start)),
              pt(inch(centre), ft(DECK_SHEET_SOUTH_Y_FT) + inch(end))),
        top_elevation=inch(top), depth=inch(0.5), thickness=inch(FLASHING_WIDTH_IN),
        material="entry-screen-bone-white-aluminum", host_ref="W-BW-SCREEN", back_side="left",
        section=FormedFlashingSection(profile="counter", sheet_thickness=inch(0.050),
                                     slope=0.25 / 12, upstand=inch(upstand),
                                     drip=inch(0.5), hem=inch(0.125)),
    )


FINISH_ELEMENTS = [
    _run(f"TR-BW-METAL-{level}-{index}", f"BWM{level[0]}{index:06d}", top, start, end,
         upstand=upstand)
    for level, top, upstand in (("BASE", FINISH_BOTTOM_IN - 0.125, 3.5),
                                ("HEAD", FINISH_TOP_IN + 0.125, 0.25))
    for index, (start, end) in enumerate(PANEL_RUNS_IN, 1)
]
