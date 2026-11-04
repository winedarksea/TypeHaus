"""The interior whites: one switch, ``WHITE``, recolours every painted wall, ceiling and trim.

Paint systems read their colour from here (``plan/products_paint.py``); the fixed whites
beside it are the factory finishes the paint has to sit with. Sheen, not colour, separates
walls, ceilings and trim. Not ``# haus: editable``: a catalog. Basis and sources:
``notes/paint_selection.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Colour:
    maker: str
    name: str
    code: str
    hex: str
    lrv: float | None
    source: str

    @property
    def label(self) -> str:
        return " ".join(p for p in (self.maker, self.name, self.code) if p)


# BM publishes LRV but no sRGB; the hex is an aggregator's (notes/paint_selection.md).
BM_CHANTILLY_LACE = Colour("Benjamin Moore", "Chantilly Lace", "OC-65", "#f4f6f1", 90.0,
                           "LRV: Benjamin Moore. Hex: colour aggregator, BM publishes none.")
# The backup: a touch greyer and darker, still no cream under 2700 K.
SW_EXTRA_WHITE = Colour("Sherwin-Williams", "Extra White", "SW 7006", "#eeefea", 85.9,
                        "Sherwin-Williams colour page (hex and LRV).")

# ---- the switch ------------------------------------------------------------------------
WHITE = BM_CHANTILLY_LACE      # walls, ceilings, trim and doors; tinted in any accepted line
# -----------------------------------------------------------------------------------------

# The fixed whites the paint sits beside. A None LRV is unpublished, not zero.
AXSTAD_MATTE_WHITE = Colour("IKEA", "AXSTAD matte white", "NCS S 0300-N", "#f6f4f0", 89.9,
                            "NCS publishes no sRGB: hex and LRV from an aggregator's NCS S "
                            "0300-N. IKEA names the NCS code; the fronts carry no Material.")
MSI_FROST_WHITE = Colour("MSI", "Q Quartz Frost White", "", "#f2efe9", None,
                         "PLACEHOLDER hex (the quartz-counter material's); MSI publishes "
                         "'White-Cool', no LRV or sRGB.")
CORIAN_GLACIER_WHITE = Colour("Corian", "Glacier White", "", "#f4f5f4", None,
                              "PLACEHOLDER hex; LRV unverified, request Corian bulletin "
                              "K-25970LRV.")
PAX_WHITE = Colour("IKEA", "PAX white", "", "#f0f0ed", None,
                   "PLACEHOLDER hex (the pax-frame-white material's); IKEA publishes none.")
