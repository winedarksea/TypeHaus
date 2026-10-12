# haus: editable
# The three bench uids survive retyping/relocation. Separate 42" and 24" platforms
# avoid the shared tiered symbol's half-height rule. All dimensions: sauna_types.py.
from typehaus import Furniture, Mount, MountKind
from typehaus.model import deg, inch

from .sauna_types import (LOWER_HEIGHT_IN, LOWER_POSITION, READING_POSITION,
                          STEP_POSITION, UPPER_POSITION)

SAUNA_SEATING = [
    Furniture(uid="CBF601AAAA", tag="FURN-B-SAUNA-UPPER",
              type_ref="FT-CATLIN-SAUNA-UPPER-78", room="RM-B-SAUNA",
              position=UPPER_POSITION,
              rotation=deg(90)),
    Furniture(uid="CBF602AAAA", tag="FURN-B-SAUNA-LOWER",
              type_ref="FT-CATLIN-SAUNA-LOWER-78", room="RM-B-SAUNA",
              position=LOWER_POSITION,
              rotation=deg(90)),
    Furniture(uid="V218FXRSH2", tag="FURN-B-SAUNA-READING",
              type_ref="FT-CATLIN-SAUNA-READING-58", room="RM-B-SAUNA",
              position=READING_POSITION,
              rotation=deg(180)),
    Furniture(uid="P6D0GBNTE5", tag="FURN-B-SAUNA-STEP",
              type_ref="FT-CATLIN-SAUNA-STEP", room="RM-B-SAUNA",
              position=STEP_POSITION),
    Furniture(uid="6R4B3Q6JQR", tag="FURN-B-SAUNA-RECLINER",
              type_ref="FT-CATLIN-SAUNA-RECLINER", room="RM-B-SAUNA",
              position=READING_POSITION,
              rotation=deg(90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(LOWER_HEIGHT_IN))),
    # The pad and slats share a base; placing it on the back's bounding-box top would float it.
    Furniture(uid="12WDH8YAKG", tag="FURN-B-SAUNA-MATTRESS",
              type_ref="FT-CATLIN-SAUNA-MATTRESS", room="RM-B-SAUNA",
              position=READING_POSITION,
              rotation=deg(90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(LOWER_HEIGHT_IN))),
]
