"""The exterior darks: two switches, ``METAL`` and ``WINDOW``, recolour the whole facade.

Every dark on the envelope reads its name and colour from here (``plan/assemblies/
materials_exterior_darks.py``, ``plan/products_trim_stock.py``). Products with no matching
colour follow ``METAL.family`` through the tables below. Hexes are the makers' own chips or
published sRGB, never pre-darkened (the viewer crushes a dark, it does not lift it).
The foundation coating independently takes the darkest stock colour (Concrete Grey).
Not ``# haus: editable``: a catalog. Basis and sources: ``notes/exterior_darks.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Finish:
    maker: str
    colour: str
    hex: str
    family: Literal["grey", "black", "bronze"]
    sr: float | None = None
    sri: int | None = None
    line: str = ""

    @property
    def label(self) -> str:
        return " ".join(p for p in (self.maker, self.line, self.colour) if p)

    @property
    def solar(self) -> str:
        return f"SR {self.sr:.2f} / SRI {self.sri}" if self.sr is not None else "no SR published"


# Metal Sales 24 ga PVDF, the only line this house buys (owner, 2026-10-30): Charcoal (17)
# and Black (06) are 26/29 ga Colorfast45 (SMP) only. Chips and SR/SRI: 24 ga PVDF Color
# Guide 9/2026, p.1 swatch fills, p.2 table (read 2026-11-07). Matte Black is not marked
# low gloss there; Slate Grey is.
_MS = dict(maker="Metal Sales", line="24 ga PVDF")
MS_SLATE_GREY_W38 = Finish(**_MS, colour="Slate Grey (W38)", hex="#515055", family="grey",
                           sr=0.30, sri=30)
MS_MATTE_BLACK_106 = Finish(**_MS, colour="Matte Black (106)", hex="#2c2829", family="black",
                            sr=0.27, sri=26)
MS_MEDIUM_BRONZE_H4 = Finish(**_MS, colour="Medium Bronze (H4)", hex="#3b2e25",
                             family="bronze", sr=0.30, sri=31)
MS_DARK_BRONZE_50 = Finish(**_MS, colour="Dark Bronze (50)", hex="#2c2217", family="bronze",
                           sr=0.30, sri=30)

# Drutex Alucover caps take any RAL (configurator lists 213); hexes are RAL's own sRGB
# (ral-farben.de, read 2026-11-07). 9017 is the closest RAL to Matte Black (106); 9005 is
# far blacker.
RAL_7015 = Finish(maker="RAL", colour="7015 Slate grey", hex="#51535a", family="grey")
RAL_7016 = Finish(maker="RAL", colour="7016 Anthracite grey", hex="#3b4044", family="grey")
RAL_7021 = Finish(maker="RAL", colour="7021 Black grey", hex="#323537", family="grey")
RAL_9005 = Finish(maker="RAL", colour="9005 Jet black", hex="#131516", family="black")
RAL_9017 = Finish(maker="RAL", colour="9017 Traffic black", hex="#262625", family="black")

# ---- the two switches --------------------------------------------------------------
# Black family (owner, 2026-11-07): the one family every product line can follow.
METAL = MS_MATTE_BLACK_106     # all exterior metal + everything matched to it
WINDOW = RAL_9017              # the 29 Drutex caps and the 12 Max Light frames
# -------------------------------------------------------------------------------------

# Powder coat (canopy steel posts) is ordered by RAL: the RAL nearest METAL, by CIEDE2000
# between chips (W38 -> 7015, dE 2.0; 106 -> 9017, dE 3.5). No bronze RAL is chosen yet.
POWDER_RAL = {"grey": RAL_7015, "black": RAL_9017}[METAL.family]

# AZEK Captivate swatches sampled from azekexteriors.com (Midnight Black read 2026-11-07).
# Captivate has no dark bronze; Warm Coffee is mid brown.
_AZEK = {
    "grey": Finish(maker="AZEK Captivate", colour="Dark Shale", hex="#5c5b5e", family="grey"),
    "black": Finish(maker="AZEK Captivate", colour="Midnight Black", hex="#222120",
                    family="black"),
    "bronze": Finish(maker="AZEK Captivate", colour="Warm Coffee", hex="#776956",
                     family="bronze"),
}
AZEK = _AZEK[METAL.family]

# Garage stem band, fixed whatever METAL is (owner, 2026-10-30): Una-Clad PVDF aluminium,
# made in Anoka, MN. Hex sampled from the Una-Clad colour chart 1185 03/2026; Elevate
# publishes no SR ("SRI numbers available by request").
UNA_CLAD_MATTE_BLACK = Finish(maker="Una-Clad", line="PVDF aluminium", colour="Matte Black",
                              hex="#2d2d2e", family="black")

# Clopay Classic Steel: Charcoal until a dealer confirms Black at R-12.9 (clopaydoor.com
# says only "available on select models"; Home Depot sells Black as R-6.5 GDU266).
CLOPAY = Finish(maker="Clopay Classic Steel", colour="Charcoal", hex="#535353", family="grey")
