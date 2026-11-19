"""North/south panel variants: the girt support plane stays fixed.

The band girt behind the joint is derived from it (``rainscreen_strips``)."""
from typehaus import inch

from .envelope_walls import EXT_2X6
from .interior_wet import PLANT_EXT_2X6_HUMID

BOARD_BATTEN_DEPTH = inch(0.75)
#: The BBD75 band, house-wide (2026-11-19; 228" before). Just over the balcony, where the
#: Transition Trim extends over the deck edge as its rear flashing (TR-SG-BAND-*). Its band
#: girt (joint -2" to +1.5") lands on the 120" storey course, and the upper gable panel
#: stays under BBD75's 20' limit.
BBD_BAND_JOINT = inch(125.5)


def _with_board_batten(assembly, tag):
    layers = tuple(
        layer.model_copy(update={"material_ref": "board-batten-24",
                                 "thickness": BOARD_BATTEN_DEPTH,
                                 "panel_joint_elevations": (BBD_BAND_JOINT,),
                                 "joint_trim_material_ref": "bbd-transition-trim"})
        if layer.name == "cladding" else layer
        for layer in assembly.layers)
    return assembly.model_copy(update={"tag": tag, "layers": layers})


EXT_2X6_BOARD_BATTEN = _with_board_batten(EXT_2X6, "EXT_2X6_BOARD_BATTEN")
PLANT_EXT_2X6_HUMID_BOARD_BATTEN = _with_board_batten(
    PLANT_EXT_2X6_HUMID, "PLANT_EXT_2X6_HUMID_BOARD_BATTEN")
