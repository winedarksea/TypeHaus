"""RM-S-PLANT's PVC liner panel: Extrutech P1600 white, Trusscore white equal (owner 2026-10-22).

The library ships `pvc-panel` as a product class. The house swaps in its own copy under the
same tag, so both liner layers, the price row, `trade_rules` and the section goldens keep
their reference and only the product identity changes. Not ``# haus: editable``: the swap
is a comprehension, which the editable dialect forbids. notes/plant_room.md.
"""

from __future__ import annotations

from typehaus import Product

EXTRUTECH_P1600 = Product(
    tag="PROD-EXTRUTECH-P1600", brand="Extrutech Plastics", model="P1600",
    name="P1600 flat interlocking wall and ceiling liner panel, 1/2 x 16 in., white, glossy; "
         "or Trusscore Wall&CeilingBoard white (TC16xx) equal",
    url="https://epiplastics.com/wp-content/uploads/P1600WallCeiling-8-17.pdf",
    source="Owner selection 2026-10-22, after a materials review flagged UV in the plant room. "
           "Basis of design: 100% virgin exterior-grade PVC (the only UV-relevant claim in the "
           "class), ICC-ES ESR-4583, Class A, FSI 10 / SDI 450, ASTM D3273/D3274 no mould, "
           "20-yr limited warranty on white, cut to the inch up to 20 ft so walls and ceiling "
           "take no end joints. Kleen-Rite lists it at $4.00/LF of panel (~$3.00/SF), read "
           "2026-10-22. ** SDI 450 IS EXACTLY IRC R302.9.2's LIMIT: confirm on the current "
           "ESR at order. ** Accepted equal: Trusscore Wall&CeilingBoard white, semi-gloss, "
           "LRV 0.90, FSI 10 / SDI 380, ~$3.90/SF (Home Depot special order); its warranty "
           "excludes sun discolouration. ONE BRAND FOR THE WHOLE ROOM, walls and ceiling, "
           "with that brand's own white PVC trims: sheens and T&G profiles do not mix. "
           "Install per Extrutech's panel instructions (2015): ends cut 1/4-5/16 in. short, "
           "seam gap by install temperature, screws snug not tight, stainless. PVC "
           "heat-distorts at 120 F: keep heaters and the grow tubes 24 in. off it. Support "
           "spacing: confirm against ESR-4583; the liner furring is 1x4 at 16 in. o.c.",
)


def with_selected_liner(materials):
    """``materials`` with the library `pvc-panel` row named as this house's product."""
    return tuple(_selected(m) if m.tag == "pvc-panel" else m for m in materials)


def _selected(material):
    return material.model_copy(update={
        "name": 'Extrutech P1600 PVC liner panel, white (1/2"), or Trusscore white equal',
        "product_ref": EXTRUTECH_P1600.tag,
        "source": material.source + "; house selection 2026-10-22: Extrutech P1600 white "
                  "(Trusscore Wall&CeilingBoard white equal), plan/plant_liner_selection.py",
    })
