"""The Trex colour this house chose: Enhance Basics in Tide Pool (owner 2026-10-22).

The library ships the board colour-unselected. The house swaps in its own copy under the
same tag, so every deck layer, tread, price row and golden keeps its reference and only
the look and the product identity change. Not ``# haus: editable``: the swap is a
comprehension, which the editable dialect forbids. notes/composite_decking.md.
"""

from __future__ import annotations

from typehaus import Material, TrimFastening
from typehaus.library import TREX_ENHANCE_BASICS, TREX_ENHANCE_BASICS_PRODUCT

# Mean of the centre half of Trex's own Tide Pool swatch photo
# (images.trex.com/.../enh-001-tp-decking-swatch-TP010608E2S56, read 2026-10-22). The 3"
# sample shot under studio light reads lighter, #a7a193; check a physical sample.
TIDE_POOL_COLOR = "#8e847b"

TREX_TIDE_POOL_PRODUCT = TREX_ENHANCE_BASICS_PRODUCT.model_copy(update={
    "model": "Enhance Basics, Tide Pool (TP)",
    "name": "Square-edge composite deck board, Tide Pool",
    "url": "https://www.trex.com/products/decking/enhance/tide-pool/",
    "source": "Owner selection 2026-10-22. Trex Enhance Basics in Tide Pool, colour prefix "
              "TP, heat-mitigating; actual 0.94 x 5.5 in stock.",
})
TREX_TIDE_POOL = TREX_ENHANCE_BASICS.model_copy(update={
    "name": "Trex Enhance Basics composite decking, Tide Pool (square edge)",
    "color": TIDE_POOL_COLOR,
    "source": TREX_ENHANCE_BASICS.source.replace("color unselected", "Tide Pool (2026-10-22)"),
})


# D-B-SUNKEN's box sides (owner, 2026-11-03): the matching fascia, ripped ~6" deep for the
# jambs and head, frame to the brick's back. The house's one composite colour.
TREX_TIDE_POOL_FASCIA = Material(
    tag="trex-tide-pool-fascia",
    name="Trex Enhance fascia, Tide Pool, 0.56 x 7 1/4 in x 12 ft",
    density=1000.0, r_per_inch=1.0, perm_rating=0.5, hatch="lumber", color=TIDE_POOL_COLOR,
    finish="composite-deck-board",
    source="Trex Enhance fascia board, Tide Pool, actual 0.56 x 7.25 in x 12 ft; ripped to "
           "~6 in for D-B-SUNKEN's jambs and head (owner 2026-11-03).",
    trim_fastening=TrimFastening(
        part="T08175FS75", pitch_in=18.0, rows=2,
        source="Trex Fascia Instructions TF-0823: approved fascia fasteners at 18 in. max; "
               "2 per row on a 2x8-deep face (the ~6 in rip); Simpson Fascia-Fastening "
               "Solution is a listed fastener"),
)
# The top course under D-B-SUNKEN's tread: the curb's 15 psi foam cut down and replaced.
XPS_40_TREAD_BED = Material(
    tag="xps-40", name="XPS rigid insulation, 40 psi (ASTM C578 Type VI)",
    r_per_inch=5.0, perm_rating=1.1, hatch="rigid", color="#f2b8c6", foam_plastic=True,
    source="ASTM C578 Type VI, 40 psi min at yield or 10% deformation (e.g. Owens Corning "
           "FOAMULAR 400); D-B-SUNKEN's tread bed, graded at 40/3 psi for creep.",
)
# Since 2026-11-17 the bed is 60 psi under a bearing plate; xps-40 stays as the revert.
XPS_60_TREAD_BED = Material(
    tag="xps-60", name="XPS rigid insulation, 60 psi (ASTM C578 Type VII)",
    r_per_inch=5.0, perm_rating=1.1, hatch="rigid", color="#e9a7b8", foam_plastic=True,
    source="ASTM C578 Type VII, 60 psi min at yield or 10% deformation (e.g. Owens Corning "
           "FOAMULAR 600); D-B-SUNKEN's tread bed under its plate, graded at 60/3 psi for creep.",
)
HOUSE_DECK_MATERIALS = (TREX_TIDE_POOL_FASCIA, XPS_40_TREAD_BED, XPS_60_TREAD_BED)


def with_selected_decking(materials):
    """``materials`` with the library Trex row replaced by this house's colour."""
    return (*(TREX_TIDE_POOL if m.tag == TREX_TIDE_POOL.tag else m for m in materials),
            *HOUSE_DECK_MATERIALS)
