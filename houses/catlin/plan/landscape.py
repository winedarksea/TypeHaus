# haus: editable
# The four espaliered dwarf apples in the west strip, two on each of params/landscape_gardens.py's
# TRL-W-S / TRL-W-N. Four cultivars so they pollinate one another. Illustrative, unpriced.
from typehaus import Furniture, Mount, MountKind, Plant, deg, ft, pt

APPLES = [
    Plant(uid="3NGGZR7EBH", tag="PL-W-APPLE-1", type_ref="PT-MAL-HONEYCRISP", position=pt(ft(-5), ft(4)),
          training="espalier", trellis_ref="TRL-W-S"),
    Plant(uid="Y7NAKBPAZN", tag="PL-W-APPLE-2", type_ref="PT-MAL-ZESTAR", position=pt(ft(-5), ft(11)),
          training="espalier", trellis_ref="TRL-W-S"),
    Plant(uid="P0FNCVVT6T", tag="PL-W-APPLE-3", type_ref="PT-MAL-HARALSON", position=pt(ft(-5), ft(28)),
          training="espalier", trellis_ref="TRL-W-N"),
    Plant(uid="7VZJP364R0", tag="PL-W-APPLE-4", type_ref="PT-MAL-SNOWSWEET", position=pt(ft(-5), ft(35)),
          training="espalier", trellis_ref="TRL-W-N"),
]

# TR-SG-LEADER-SE's splash pad, under TR-SG-RUNNEL's spout (params/sunken_garden.py): the water
# lands ~0.8' past the lip, ~1.8' off W-RG-EAST's toe, inside this 4' x 3' river-rock pad that
# spreads it onto the lawn (AB Table 2.1 "extra precautions"). 2'-6" south of SL-SG-STAIRPAD
# (St Paul DSI: no icy walkway). The storey is yard-grade at the main datum, so the mount is the
# yard's -3'-4". Illustrative placement.
SITE_FURNITURE = [
    Furniture(uid="247ETCTJ2N", tag="FURN-SG-SPLASH-PAD", type_ref="FT-SPLASH-PAD-RIVER-ROCK",
              position=pt(ft(34), ft(-13)), rotation=deg(0),
              mount=Mount(kind=MountKind.FLOOR, elevation=ft(-3, -4))),
]
