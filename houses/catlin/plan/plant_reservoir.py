# haus: editable
# Reservoir and independently removable service rack, no drain. Design and commissioning:
# notes/plant_reservoir.md. Full handle envelope is 18 inches. The rack's east edge is 182",
# west of the door swing's x>=186" strip. The lid lifts below WIN-S-PLANT4's 32" sill.

from typehaus import Appliance, Mount, MountKind, deg, inch, pt

PLANT_RESERVOIR_PLACED = [
    Appliance(
        uid="YRDYECWWYV",
        tag="APPL-S-PLANT-RESERVOIR",
        type_ref="APPL-PLANT-RESERVOIR",
        room="RM-S-PLANT",
        position=pt(inch(166), inch(17.75)),
        rotation=deg(180),
    ),
    Appliance(
        uid="PLNTRACK01",
        tag="APPL-S-PLANT-IRRIGATION",
        type_ref="APPL-PLANT-IRRIGATION-RACK",
        room="RM-S-PLANT",
        position=pt(inch(164), inch(37)),
        rotation=deg(180),
    ),
    Appliance(
        uid="PLNTWIRED1",
        tag="APPL-S-PLANT-WIRED-LEAK",
        type_ref="APPL-PLANT-WIRED-LEAK",
        room="RM-S-PLANT",
        position=pt(inch(166), inch(28.8)),
    ),
    Appliance(
        uid="PLNTFILL01",
        tag="APPL-S-PLANT-FILL-VALVE",
        type_ref="APPL-PLANT-FILL-VALVE",
        room="RM-S-PLANT",
        position=pt(inch(155), inch(9.75)),
        mount=Mount(kind=MountKind.FLOOR, elevation=inch(13)),
    ),
]
