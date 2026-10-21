"""Catlin's proposed elm-top appearance for the purchased puzzle coffee table."""

from typehaus.library.placeables import PUZZLE_COFFEE_TABLE

# Reuse the living-room elm appearance only; stock and fabrication are undecided.
# With no cut list, this visual study adds no parts to the milling schedule.
PUZZLE_COFFEE_TABLE_ELM_PREVIEW = PUZZLE_COFFEE_TABLE.model_copy(update={
    "name": 'Lift-top puzzle coffee table, 44.5" x 23.8", proposed elm top',
    "wood_material_ref": "elm-slat-5q",
    "source": PUZZLE_COFFEE_TABLE.source + " Catlin appearance study: proposed American "
              "elm replacement top, not the seller's supplied material. Replacement "
              "construction, stock and cost remain undecided.",
})
