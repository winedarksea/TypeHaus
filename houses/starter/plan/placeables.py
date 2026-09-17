# haus: editable
from typehaus import (Appliance, DeviceKind, DuctSystem, ElectricalDevice, Equipment,
                      EquipmentKind, Fixture, Furniture, Location, Mount, MountKind, Register,
                      WallAttachment, deg, ft, inch, m, pt)

# Canvas placement targets: the editor's Place tool appends furniture, fixtures, appliances,
# equipment, registers and devices here, one list per storey. The imports cover every name
# a placed object is written with, so a first placement never needs a hand edit.
# Rotation 0 puts an object's back at +y (project north).

MAIN_PLACEABLES = []

UPPER_PLACEABLES = []
