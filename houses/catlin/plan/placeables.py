# haus: editable
from typehaus import Appliance, ElectricalDevice, Equipment, Fixture, Furniture, Register
from typehaus.model import ft, pt

# Project-local canvas placement targets.  One list per storey keeps source ownership
# explicit while allowing every placeable domain to use the same writeback contract.
BASEMENT_PLACEABLES = [Fixture(uid="5BBZTZNBWN", tag="FX-1", type_ref="FX-LAV", room="RM-B-FURNACE", position=pt(ft(13, 9.375), ft(19, 10.25)))]
MAIN_PLACEABLES = []
GARAGE_PLACEABLES = []
SECOND_PLACEABLES = []
ATTIC_PLACEABLES = []
