# haus: editable
from typehaus import Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Register

# Project-local canvas placement targets.  One list per storey keeps source ownership
# explicit while allowing every placeable domain to use the same writeback contract.
BASEMENT_PLACEABLES = []
MAIN_PLACEABLES = []
GARAGE_PLACEABLES = []
SECOND_PLACEABLES = []
ATTIC_PLACEABLES = []
