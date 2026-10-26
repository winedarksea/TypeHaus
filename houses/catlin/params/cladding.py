"""Installed cladding faces measured outward from the sheathing datum."""
from plan.assemblies.board_batten import EXT_2X6_BOARD_BATTEN
from plan.assemblies.envelope_walls import EXT_2X6


def _outboard_inches(assembly):
    names = [layer.name for layer in assembly.layers]
    return sum(layer.thickness.inches for layer in assembly.layers[names.index("sheathing") + 1:])


HOUSE_EW_OUTBOARD_IN = _outboard_inches(EXT_2X6)
HOUSE_NS_OUTBOARD_IN = _outboard_inches(EXT_2X6_BOARD_BATTEN)
