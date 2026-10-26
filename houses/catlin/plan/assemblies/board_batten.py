"""North/south panel variants: the girt support plane stays fixed."""
from typehaus import inch

from .envelope_walls import EXT_2X6
from .interior_wet import PLANT_EXT_2X6_HUMID

BOARD_BATTEN_DEPTH = inch(0.75)


def _with_board_batten(assembly, tag):
    layers = tuple(layer.model_copy(update={"material_ref": "board-batten-24",
                                           "thickness": BOARD_BATTEN_DEPTH})
                   if layer.name == "cladding" else layer for layer in assembly.layers)
    return assembly.model_copy(update={"tag": tag, "layers": layers})


EXT_2X6_BOARD_BATTEN = _with_board_batten(EXT_2X6, "EXT_2X6_BOARD_BATTEN")
PLANT_EXT_2X6_HUMID_BOARD_BATTEN = _with_board_batten(
    PLANT_EXT_2X6_HUMID, "PLANT_EXT_2X6_HUMID_BOARD_BATTEN")
