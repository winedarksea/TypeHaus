# haus: editable
# The workshop's benchtop solder-fume extractor (types: plan/workshop_fume_types.py). At the
# back of FURN-B-WORKSHOP-BENCH-N just north of the bench seam and REG-B-RET1's valve; it is
# moved to the joint in use. Cord to ED-B-WORKSHOP-RC2 (quadruplex, 42" AFF, y=11'-0").
from typehaus import Appliance, Mount, MountKind
from typehaus.model import deg, ft, inch, pt

WORKSHOP_FUME = [
    Appliance(uid="56GRERXHWS", tag="APPL-B-WORKSHOP-FUME", type_ref="APPL-HAKKO-FA400-04",
              room="RM-B-WORKSHOP", position=pt(inch(13), ft(9, 3)), rotation=deg(90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(34)),
              plugs_into=("ED-B-WORKSHOP-RC2",)),
]
