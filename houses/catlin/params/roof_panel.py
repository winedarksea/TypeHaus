"""House panel stations and seam crowns, derived from the authored assembly."""
import math

from params.cladding import HOUSE_EW_OUTBOARD_IN, HOUSE_NS_OUTBOARD_IN
from plan.assemblies.envelope_roofs import ROOF as HOUSE_ROOF
from plan.assemblies.board_batten import EXT_2X6_BOARD_BATTEN

PITCH = 6 / 12
PANEL_PITCH_IN = 16.0
RIDGE_IN = 18 * 12.0
PLATE_TOP_IN = 20 * 12 + 2.25
STRUCTURE = next(layer for layer in HOUSE_ROOF.layers if layer.function.value == 'structure')
STRUCTURE_INDEX = HOUSE_ROOF.layers.index(STRUCTURE)
ABOVE_DECK = HOUSE_ROOF.layers[STRUCTURE_INDEX + 1:]
ROOFING = next(layer for layer in ABOVE_DECK if layer.name == 'roofing')
ROOFING_BASE_IN = sum(layer.thickness.inches for layer in ABOVE_DECK[:ABOVE_DECK.index(ROOFING)])
ROOFING_TOP_IN = ROOFING_BASE_IN + ROOFING.thickness.inches
# The roof footprint is the cladding face; the bearing plate is 5.5 inches deep.
EAVE_X_IN = -HOUSE_EW_OUTBOARD_IN
EAVE_DECK_IN = PLATE_TOP_IN + STRUCTURE.thickness.inches - 5.5 * PITCH
# Roof metal laps the outer furring face by .6 inch, independent of the profile height.
RAKE_CLADDING_IN = next(layer.thickness.inches for layer in EXT_2X6_BOARD_BATTEN.layers
                       if layer.function.value == 'cladding')
RAKE_METAL_OUTBOARD_IN = HOUSE_NS_OUTBOARD_IN - RAKE_CLADDING_IN + .6
SEAM_STATIONS_IN = tuple(RIDGE_IN + k * PANEL_PITCH_IN for k in range(
    math.ceil((-RAKE_METAL_OUTBOARD_IN - RIDGE_IN) / PANEL_PITCH_IN),
    math.floor((36 * 12 + RAKE_METAL_OUTBOARD_IN - RIDGE_IN) / PANEL_PITCH_IN) + 1))


def seam_top_inches(x_inches):
    return (EAVE_DECK_IN + (RIDGE_IN - abs(x_inches - RIDGE_IN) - EAVE_X_IN) * PITCH
            + ROOFING_TOP_IN * math.hypot(1, PITCH))


def clamp_columns_inches(start, width, end_inset=6.0):
    candidates = [station for station in SEAM_STATIONS_IN
                  if start + end_inset <= station <= start + width - end_inset]
    if len(candidates) < 2:
        raise ValueError('PV module has fewer than two seams inside its clamp zone')
    return candidates[0], candidates[-1]
