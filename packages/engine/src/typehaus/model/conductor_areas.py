"""Chapter 9 Table 5 (2026 NEC): approximate area and diameter of insulated conductors.

Read in print by the owner 2026-11-14. Only the building-wire families conduit fill needs are
coded: THHN/THWN/THWN-2, XHHW/XHHW-2/XHH and TW/THW/THHW/THW-2 (copper or aluminium alike:
Table 5 is by insulation, not metal). Each size maps to ``(area in.2, diameter in.)``; the
print's mm columns are not carried. Note (10): these are worst-case round concentric-lay
values; a known actual diameter and area may be used instead.

**Read, not coded:** the RH*/SF/TF/XF/fluoropolymer/Z/KF types, Table 5A (compact conductors)
and Table 8 (conductor properties, area and dc resistance). Nothing in the engine sizes a
conductor by area or voltage drop, so those stay in ``docs/code-notes/nec-2026-paraphrase-300.md``.
A leaf, sized like ``model/ampacity.SIZES`` (AWG strings, kcmil as bare numbers).
"""

from __future__ import annotations

from typing import Final

#: THHN, THWN, THWN-2: 14 AWG through 1000 kcmil.
THHN: Final = {
    "14": (0.0097, 0.111), "12": (0.0133, 0.130), "10": (0.0211, 0.164), "8": (0.0366, 0.216),
    "6": (0.0507, 0.254), "4": (0.0824, 0.324), "3": (0.0973, 0.352), "2": (0.1158, 0.384),
    "1": (0.1562, 0.446), "1/0": (0.1855, 0.486), "2/0": (0.2223, 0.532),
    "3/0": (0.2679, 0.584), "4/0": (0.3237, 0.642), "250": (0.3970, 0.711),
    "300": (0.4608, 0.766), "350": (0.5242, 0.817), "400": (0.5863, 0.864),
    "500": (0.7073, 0.949), "600": (0.8676, 1.051), "700": (0.9887, 1.122),
    "750": (1.0496, 1.156), "800": (1.1085, 1.188), "900": (1.2311, 1.252),
    "1000": (1.3478, 1.310),
}

#: XHHW, XHHW-2, XHH: 14 AWG through 2000 kcmil.
XHHW: Final = {
    "14": (0.0139, 0.133), "12": (0.0181, 0.152), "10": (0.0243, 0.176), "8": (0.0437, 0.236),
    "6": (0.0590, 0.274), "4": (0.0814, 0.322), "3": (0.0962, 0.350), "2": (0.1146, 0.382),
    "1": (0.1534, 0.442), "1/0": (0.1825, 0.482), "2/0": (0.2190, 0.528),
    "3/0": (0.2642, 0.58), "4/0": (0.3197, 0.638), "250": (0.3904, 0.705),
    "300": (0.4536, 0.76), "350": (0.5166, 0.811), "400": (0.5782, 0.858),
    "500": (0.6984, 0.943), "600": (0.8709, 1.053), "700": (0.9923, 1.124),
    "750": (1.0532, 1.158), "800": (1.1122, 1.190), "900": (1.2351, 1.254),
    "1000": (1.3519, 1.312), "1250": (1.7180, 1.479), "1500": (2.0156, 1.602),
    "1750": (2.3127, 1.716), "2000": (2.6073, 1.822),
}

#: TW, THW, THHW, THW-2: 14 AWG through 2000 kcmil.
THW: Final = {
    "14": (0.0139, 0.133), "12": (0.0181, 0.152), "10": (0.0243, 0.176), "8": (0.0437, 0.236),
    "6": (0.0726, 0.304), "4": (0.0973, 0.352), "3": (0.1134, 0.380), "2": (0.1333, 0.412),
    "1": (0.1901, 0.492), "1/0": (0.2223, 0.532), "2/0": (0.2624, 0.578),
    "3/0": (0.3117, 0.630), "4/0": (0.3718, 0.688), "250": (0.4596, 0.765),
    "300": (0.5281, 0.820), "350": (0.5958, 0.871), "400": (0.6619, 0.918),
    "500": (0.7901, 1.003), "600": (0.9729, 1.113), "700": (1.1010, 1.184),
    "750": (1.1652, 1.218), "800": (1.2272, 1.250), "900": (1.3561, 1.314),
    "1000": (1.4784, 1.372), "1250": (1.8602, 1.539), "1500": (2.1695, 1.662),
    "1750": (2.4773, 1.776), "2000": (2.7818, 1.882),
}

TABLE_5: Final = {"thhn": THHN, "xhhw": XHHW, "thw": THW}


def conductor_area_in2(insulation: str, size: str) -> float:
    """Table 5 area in.2; ``KeyError`` (naming family and size) for one not coded."""
    try:
        return TABLE_5[insulation][size][0]
    except KeyError:
        raise KeyError(f"{str(insulation).upper()} {size}") from None


def conductor_diameter_in(insulation: str, size: str) -> float:
    return TABLE_5[insulation][size][1]
