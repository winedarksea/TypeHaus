"""Representative openings of a laser-cut chevron grille (Reggio Chevron)."""
from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN

# Visual defaults read off the product photo, not a cut file.
_BORDER_IN = 1.0
_COLUMN_IN = 2.0
_WEB_IN = 0.15
_DROP_IN = 0.5
_SLOT_IN = 0.3
_ROW_PITCH_IN = 0.75


def chevron_openings(width, height):
    """Rows of V slots inside a solid border, centred on the face."""
    border = min(_BORDER_IN * M_PER_IN, width / 6, height / 6)
    field_w, field_h = width - 2 * border, height - 2 * border
    columns = max(1, round(field_w / (_COLUMN_IN * M_PER_IN)))
    column = field_w / columns
    web, drop, slot = (v * M_PER_IN for v in (_WEB_IN, _DROP_IN, _SLOT_IN))
    pitch = _ROW_PITCH_IN * M_PER_IN
    rows = math.floor((field_h - drop - slot - web) / pitch) + 1
    if rows < 1 or column <= web:
        return ()  # too small for one slot: a plain plate
    # Centre the stack of rows in the field.
    y_start = -(drop + slot + (rows - 1) * pitch) / 2
    slots = []
    for row in range(rows):
        y = y_start + row * pitch
        for col in range(columns):
            x0 = -field_w / 2 + col * column + web / 2
            x1 = x0 + column - web
            xc = (x0 + x1) / 2
            slots.append(((x0, y + drop), (xc, y), (x1, y + drop),
                          (x1, y + drop + slot), (xc, y + slot), (x0, y + drop + slot)))
    return tuple(slots)
