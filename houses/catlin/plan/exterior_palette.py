"""The exterior darks: two switches, ``METAL`` and ``WINDOW``, recolour the whole facade.

Every dark on the envelope reads its name and colour from here (``plan/assemblies/
materials_exterior_darks.py``, ``plan/products_trim_stock.py``). Products with no matching
colour follow ``METAL.family`` through the tables below. Hexes are the makers' own chips or
published sRGB, never pre-darkened (the viewer crushes a dark, it does not lift it).
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
# and Black (06) are 26/29 ga Colorfast45 (SMP) only. Swatches: 24 ga PVDF guide 02/2026;
# SR/SRI: the 24 ga guide (H&H Metals copy).
_MS = dict(maker="Metal Sales", line="24 ga PVDF")
MS_SLATE_GREY_W38 = Finish(**_MS, colour="Slate Grey (W38)", hex="#4d4b50", family="grey",
                           sr=0.30, sri=30)
MS_MATTE_BLACK_106 = Finish(**_MS, colour="Matte Black (106)", hex="#252122", family="black",
                            sr=0.27, sri=26)
MS_MEDIUM_BRONZE_H4 = Finish(**_MS, colour="Medium Bronze (H4)", hex="#3a2c1a",
                             family="bronze", sr=0.30, sri=31)
MS_DARK_BRONZE_50 = Finish(**_MS, colour="Dark Bronze (50)", hex="#372c22", family="bronze",
                           sr=0.30, sri=30)

# Drutex Alucover caps take any RAL; hexes are RAL's own sRGB (ral-farben.de).
RAL_7016 = Finish(maker="RAL", colour="7016 Anthracite grey", hex="#3b4044", family="grey")
RAL_7021 = Finish(maker="RAL", colour="7021 Black grey", hex="#323537", family="grey")
RAL_9005 = Finish(maker="RAL", colour="9005 Jet black", hex="#131516", family="black")

# ---- the two switches --------------------------------------------------------------
METAL = MS_SLATE_GREY_W38      # all exterior metal + everything matched to it
WINDOW = RAL_7016              # the 32 Drutex units' Alucover cap
# -------------------------------------------------------------------------------------

# Andersen 400 has no grey (White, Sandtone, Canvas, Terratone, Forest Green, Dark Bronze,
# Black); swatches sampled from andersenwindows.com.
_ANDERSEN_BLACK = Finish(maker="Andersen 400", colour="Black", hex="#323433", family="black")
_ANDERSEN_DARK_BRONZE = Finish(maker="Andersen 400", colour="Dark Bronze", hex="#493f3d",
                               family="bronze")
ANDERSEN = {"grey": _ANDERSEN_BLACK, "black": _ANDERSEN_BLACK,
            "bronze": _ANDERSEN_DARK_BRONZE}[METAL.family]

# AZEK Captivate (2025 swatch set). Captivate has no dark bronze; Warm Coffee is mid brown.
_AZEK = {
    "grey": Finish(maker="AZEK Captivate", colour="Dark Shale", hex="#5c5b5e", family="grey"),
    "black": Finish(maker="AZEK Captivate", colour="Midnight Black", hex="#20201f",
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

# Clopay Classic Steel: Charcoal is the only dark at R-12.9 (Black is R-6.5, GDU266).
CLOPAY = Finish(maker="Clopay Classic Steel", colour="Charcoal", hex="#535353", family="grey")
