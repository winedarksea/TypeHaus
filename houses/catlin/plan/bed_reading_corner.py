# haus: editable
# RM-M-BED reading chair by the west wall (W-M-W4). The SEKTION window seat that stood
# beside it was retired on 2026-10-21. STRANDMON: rotated toward the room, clear of the
# south-wall bookcase and bed, under ED-M-BED-LT.

from typehaus import Furniture
from typehaus.model import deg, m, pt

BED_READING_CORNER = [
    Furniture(uid="NJW8BV7455", tag="FURN-M-BED-ARMCHAIR", type_ref="FURN-ARMCHAIR-STRANDMON",
              room="RM-M-BED", position=pt(m(0.882965), m(0.88992)), rotation=deg(120)),
]
