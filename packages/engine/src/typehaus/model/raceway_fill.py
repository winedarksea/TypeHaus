"""Chapter 9 conduit fill (2026 NEC): Table 1, Table 2 and the Notes to Tables, over Table 4.

Read in print by the owner 2026-11-14 (Notes to Tables (1)-(10), Tables 1, 2, 4, 5, 5A, 8).
The data is in ``raceway_areas`` (Table 4) and ``conductor_areas`` (Table 5); rules are
paraphrased in
``docs/code-notes/nec-2026-paraphrase-300.md`` and ``checks/mep/raceway_fill.py`` grades a
model against them. A leaf: no resolved model here. Areas are in.2, lengths in inches.

Notes carried as code: (3) the EGC counts (``total_area_in2``); (4) a nipple of 24 in. or
less fills to 60 % and needs no 310.15(C)(1) adjustment (``fill_percent_for``,
``adjustment_exempt``); (7) round the permitted count up at a decimal of 0.8 or more
(``permitted_count``); (9) a multiconductor cable is one conductor, its circle taken on the
major diameter where elliptical, e.g. NM (``cable_area_in2``). The rest are in ``NOTES``.
"""


from __future__ import annotations

import math
from typing import Final

from typehaus.model.raceway_areas import table_4_row

#: Note (4): nipples to this length (excluding connectors) between boxes or cabinets.
NIPPLE_MAX_LENGTH_IN: Final = 24.0
NIPPLE_FILL_FRACTION: Final = 0.60
#: Note (7): a ratio whose decimal reaches this rounds up to the next whole conductor.
ROUND_UP_DECIMAL: Final = 0.8
#: Informational Note 2: jamming is possible with three conductors when raceway ID over
#: conductor OD falls between these.
JAMMING_RATIO: Final = (2.8, 3.2)

#: Table 1: percent of cross-section by conductor count (1, 2, over 2).
TABLE_1_PERCENT: Final = {1: 53, 2: 31}
TABLE_1_PERCENT_OVER_2: Final = 40

#: Notes to Tables the engine does not compute, as paraphrase for findings.
NOTES: Final = {
    1: "Annex C gives the maximum count of same-size conductors per trade size",
    2: "Table 1 is for a complete conduit or tubing system, not a section that only "
       "protects exposed wiring from physical damage",
    5: "a conductor Chapter 9 does not list (e.g. multiconductor or optical fibre cable) "
       "is counted at its actual dimensions",
    6: "mixed sizes use actual dimensions or Table 5/5A, with Table 4 for the raceway",
    8: "bare conductors take their Table 8 dimensions",
    10: "Table 5 values are worst-case round concentric-lay-stranded; Table 5A is compact "
        "stranded; known actual diameter and area may be used",
}


def fill_percent(conductor_count: int) -> int:
    """Table 1: 53 for one, 31 for two, 40 over two."""
    if conductor_count < 1:
        raise ValueError("a raceway with no conductor has no Table 1 row")
    return TABLE_1_PERCENT.get(conductor_count, TABLE_1_PERCENT_OVER_2)


def fill_percent_for(conductor_count: int, nipple_length_in: float | None = None) -> int:
    """Table 1, or 60 under Note (4): a nipple of 24 in. or less (connectors excluded)."""
    if nipple_length_in is not None and nipple_length_in <= NIPPLE_MAX_LENGTH_IN + 1e-9:
        return int(NIPPLE_FILL_FRACTION * 100)
    return fill_percent(conductor_count)


def fill_fraction(conductor_count: int, nipple_length_in: float | None = None) -> float:
    return fill_percent_for(conductor_count, nipple_length_in) / 100.0


def adjustment_exempt(nipple_length_in: float | None) -> bool:
    """Note (4): 310.15(C)(1) adjustment factors need not apply to such a nipple."""
    return nipple_length_in is not None and nipple_length_in <= NIPPLE_MAX_LENGTH_IN + 1e-9


def fill_limit_in2(material: str, trade_in: float, conductor_count: int,
                   nipple_length_in: float | None = None) -> float:
    """The area the conductors may total, in.2, from the printed cell (not recomputed)."""
    return table_4_row(material, trade_in).area_in2(
        fill_percent_for(conductor_count, nipple_length_in))


def cable_area_in2(major_diameter_in: float) -> float:
    """Note (9): a multiconductor cable is one conductor, a circle on its major diameter
    (an elliptical cable such as NM takes the long axis)."""
    return math.pi / 4.0 * major_diameter_in ** 2


def total_area_in2(conductor_areas_in2: list[float], egc_area_in2: float = 0.0) -> float:
    """Note (3): the equipment grounding or bonding conductor, insulated or bare, is counted
    at its actual dimensions (a bare one's from Table 8, read but not coded)."""
    return sum(conductor_areas_in2) + egc_area_in2


def permitted_count(area_limit_in2: float, area_each_in2: float) -> int:
    """Note (7), same-size conductors: whole conductors the limit holds, rounding the ratio
    UP where its decimal is 0.8 or more."""
    ratio = area_limit_in2 / area_each_in2
    whole = math.floor(ratio + 1e-9)
    return whole + 1 if round(ratio - whole, 6) >= ROUND_UP_DECIMAL else whole


#: Table 2: trade size -> (one-shot and full-shoe benders, other bends), inches. The print
#: also gives millimetres: the one-shot column in ``TABLE_2_MM``.
TABLE_2_IN: Final = {
    0.5: (4.0, 4.0), 0.75: (4.5, 5.0), 1.0: (5.75, 6.0), 1.25: (7.25, 8.0), 1.5: (8.25, 10.0),
    2.0: (9.5, 12.0), 2.5: (10.5, 15.0), 3.0: (13.0, 18.0), 3.5: (15.0, 21.0), 4.0: (16.0, 24.0),
    5.0: (24.0, 30.0), 6.0: (30.0, 36.0),
}
#: (one-shot mm, other mm), as printed.
TABLE_2_MM: Final = {
    0.5: (101.6, 101.6), 0.75: (114.3, 127.0), 1.0: (146.05, 152.4), 1.25: (184.15, 203.2),
    1.5: (209.55, 254.0), 2.0: (241.3, 304.8), 2.5: (266.7, 381.0), 3.0: (330.2, 457.2),
    3.5: (381.0, 533.4), 4.0: (406.4, 609.6), 5.0: (609.6, 762.0), 6.0: (762.0, 914.4),
}


def min_bend_radius_in(trade_in: float, one_shot: bool) -> float:
    """Table 2 radius of a bend: the one-shot/full-shoe column, else the other-bends column."""
    return TABLE_2_IN[trade_in][0 if one_shot else 1]
