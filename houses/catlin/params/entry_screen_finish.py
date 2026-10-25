"""Local east veneer head/base flashing; separate from the west-draining brace cap."""
from typehaus import Flashing, FormedFlashingSection, TrimKind, ft, inch, pt
from params.north_entry_frame import (
    DECK_SHEET_NORTH_Y_FT, DECK_SHEET_SOUTH_Y_FT, LANDING_WEST_FT,
)
from plan.entry_screen_finish_spec import (
    BACKER_THICKNESS_IN, BOND_MEMBRANE_THICKNESS_IN, BRICK_THICKNESS_IN,
    DRAINAGE_THICKNESS_IN, FINISH_BOTTOM_IN, FINISH_TOP_IN, HEAD_PROJECTION_IN,
    PACKING_THICKNESS_IN, PLYWOOD_THICKNESS_IN, SETTING_MORTAR_THICKNESS_IN,
    WRB_THICKNESS_IN,
)

STUD_EAST_IN = LANDING_WEST_FT * 12 + 1.75
PLYWOOD_FACE_IN = STUD_EAST_IN + PACKING_THICKNESS_IN + PLYWOOD_THICKNESS_IN
BRICK_FACE_IN = (PLYWOOD_FACE_IN + WRB_THICKNESS_IN + DRAINAGE_THICKNESS_IN
                 + BACKER_THICKNESS_IN + BOND_MEMBRANE_THICKNESS_IN
                 + SETTING_MORTAR_THICKNESS_IN + BRICK_THICKNESS_IN)
FLASHING_NOSE_IN = BRICK_FACE_IN + HEAD_PROJECTION_IN
FLASHING_WIDTH_IN = FLASHING_NOSE_IN - PLYWOOD_FACE_IN


def _run(tag, uid, top, *, upstand):
    centre = (PLYWOOD_FACE_IN + FLASHING_NOSE_IN) / 2
    return Flashing(
        uid=uid, tag=tag, kind=TrimKind.DRIP_FLASHING,
        path=(pt(inch(centre), ft(DECK_SHEET_SOUTH_Y_FT)),
              pt(inch(centre), ft(DECK_SHEET_NORTH_Y_FT))),
        top_elevation=inch(top), depth=inch(0.5), thickness=inch(FLASHING_WIDTH_IN),
        material="metal-dark-exterior", host_ref="W-BW-SCREEN", back_side="left",
        section=FormedFlashingSection(profile="counter", sheet_thickness=inch(0.032),
                                     slope=0.25 / 12, upstand=inch(upstand),
                                     drip=inch(0.5), hem=inch(0.125)),
)



FINISH_ELEMENTS = [
    _run("TR-BW-BRICK-BASE", "BWBRFL0001", FINISH_BOTTOM_IN - 0.125, upstand=3.5),
    _run("TR-BW-BRICK-HEAD", "BWBRFL0002", FINISH_TOP_IN + 0.125, upstand=0.25),
]
