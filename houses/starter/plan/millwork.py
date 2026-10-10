# haus: editable
# Base and door casing, derived per room and per door face (resolve/interior_trim.py).
#
# Store-bought by default: a poplar 1x4, primed and painted, base and casing the same board,
# butt-jointed. A house milling its own stock points `material_ref` at a material with
# `requires_custom_milling=True` and the boards move to `haus millwork`. `jamb_allowance` is
# the shim plus the jamb of the doors you buy — ask the supplier.

from typehaus import inch
from typehaus.model import TrimStandard

TRIM = [
    TrimStandard(
        uid="ZSB2PM2AT0", tag="TRIM-STANDARD",
        material_ref="poplar-trim-paint",
        thickness=inch(0.75),
        base_height=inch(3.5),
        casing_width=inch(3.5),
        reveal=inch(0.1875),
        jamb_allowance=inch(1),
        min_leg_width=inch(1.5),
    ),
]
