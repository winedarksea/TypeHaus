# haus: editable
# The three espaliered dwarf apples in the west strip, on params/landscape_gardens.py's
# TRL-W-S / TRL-W-N. Three cultivars so they pollinate one another. Illustrative, unpriced.
from typehaus import Plant, ft, pt

APPLES = [
    Plant(uid="3NGGZR7EBH", tag="PL-W-APPLE-1", type_ref="PT-MAL-HONEYCRISP", position=pt(ft(-5), ft(4)),
          training="espalier", trellis_ref="TRL-W-S"),
    Plant(uid="Y7NAKBPAZN", tag="PL-W-APPLE-2", type_ref="PT-MAL-ZESTAR", position=pt(ft(-5), ft(11)),
          training="espalier", trellis_ref="TRL-W-S"),
    Plant(uid="P0FNCVVT6T", tag="PL-W-APPLE-3", type_ref="PT-MAL-HARALSON", position=pt(ft(-5), ft(28)),
          training="espalier", trellis_ref="TRL-W-N"),
]
