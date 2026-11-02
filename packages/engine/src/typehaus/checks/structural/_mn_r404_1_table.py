"""Minn. R. 1309.0404 subp. 2, Table R404.1(1), transcribed (→ code.MN_1309_0404_wall_top).

"MAXIMUM ANCHOR BOLT AND BLOCKING SPACING FOR SUPPORTED FOUNDATION WALL". Read from the
Revisor's text (revisor.mn.gov/rules/1309.0404), 2026-11-02; the house's oracle note
(``houses/catlin/notes/main_floor_truss_basis.md`` §4) carries the same nine rows.

Subpart 1: "Floor joists and blocking shall be connected to the sill plate at the top of
wall with an approved connector with listed capacity meeting the top of wall reaction in
Table R404.1(1)." Footnote e: the reaction is the "minimum load to be used for the sizing of
accepted anchors or fasteners". Footnote f: full-depth blocking in the first three joist
spaces, connected to the sill per note e, "within 8 inches of an anchor bolt location".

The table starts at an 8'-0" wall and stops at 10'-0" / 9'-6"; it says nothing about
interpolation, so a wall reads the first row whose height AND backfill both cover it, and
one past the last row is a design, not a lookup.
"""

from __future__ import annotations

#: The table's three soil columns, by its own groupings (footnote a: USCS, Table R405.1).
#: Not ``_r404_table.SOIL_LATERAL_PSF_PER_FT``: this table lists MH and I-CL, that one
#: does not, and a shared map would quietly widen one of them.
SOIL_GROUP_PCF: dict[str, int] = {
    "GW": 30, "GP": 30, "SW": 30, "SP": 30,
    "GM": 45, "GC": 45, "SM": 45, "SM-SC": 45, "ML": 45,
    "SC": 60, "MH": 60, "ML-CL": 60, "I-CL": 60,
}

#: (max wall height ft, max unbalanced backfill ft, soil pcf/ft)
#:   -> (top of wall reaction plf, 1/2" anchor bolt spacing in, blocking spacing in)
TOP_OF_WALL: dict[tuple[float, float, int], tuple[int, int, int]] = {
    (8.0, 7.5, 30): (260, 72, 72),
    (8.0, 7.5, 45): (400, 72, 72),
    (8.0, 7.5, 60): (530, 48, 48),
    (9.0, 8.5, 30): (340, 72, 72),
    (9.0, 8.5, 45): (510, 48, 48),
    (9.0, 8.5, 60): (680, 32, 32),
    (10.0, 9.5, 30): (430, 64, 64),
    (10.0, 9.5, 45): (640, 40, 40),
    (10.0, 9.5, 60): (860, 24, 24),
}


def top_of_wall_row(height_ft: float, fill_ft: float, pcf: int) -> tuple | None:
    """``((height, fill), (reaction, bolt, blocking))`` for the first covering row."""
    for (height, fill, soil), row in sorted(TOP_OF_WALL.items()):
        if soil == pcf and height_ft <= height + 1e-6 and fill_ft <= fill + 1e-6:
            return (height, fill), row
    return None
