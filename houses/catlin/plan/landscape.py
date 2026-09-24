# haus: editable
# The three espaliered dwarf apples in the west strip, on params/landscape_gardens.py's
# TRL-W-S / TRL-W-N. Three cultivars so they pollinate one another. Illustrative, unpriced.
from typehaus import Furniture, Mount, MountKind, Plant, deg, ft, pt

APPLES = [
    Plant(uid="3NGGZR7EBH", tag="PL-W-APPLE-1", type_ref="PT-MAL-HONEYCRISP", position=pt(ft(-5), ft(4)),
          training="espalier", trellis_ref="TRL-W-S"),
    Plant(uid="Y7NAKBPAZN", tag="PL-W-APPLE-2", type_ref="PT-MAL-ZESTAR", position=pt(ft(-5), ft(11)),
          training="espalier", trellis_ref="TRL-W-S"),
    Plant(uid="P0FNCVVT6T", tag="PL-W-APPLE-3", type_ref="PT-MAL-HARALSON", position=pt(ft(-5), ft(28)),
          training="espalier", trellis_ref="TRL-W-N"),
]

# TR-SG-LEADER-SE's basin, under TR-SG-RUNNEL's spout (params/sunken_garden.py): 6" off
# W-RG-EAST's yard face, 2'-6" south of SL-SG-STAIRPAD. The storey is yard-grade at the
# main datum, so the mount is the yard's -3'-4". Illustrative placement; stone yard pick.
SITE_FURNITURE = [
    Furniture(uid="247ETCTJ2N", tag="FURN-SG-SPLASH-BASIN", type_ref="FT-SPLASH-BASIN-GRANITE-24",
              position=pt(ft(33), ft(-12, -6)), rotation=deg(0),
              mount=Mount(kind=MountKind.FLOOR, elevation=ft(-3, -4))),
]
