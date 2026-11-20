"""ICC-ES ESR-2920, Table 1: STHD/LSTHD cast-in strap hold-downs on wood vertical members.

Read 2026-11-20 from https://icc-es.org/wp-content/uploads/report-directory/ESR-2920.pdf
(reissued February 2026): §3.1.1, §3.2.5, §3.2.6 and §4.2 (pp. 1-4), Table 1 (p. 6),
Figure 1 (p. 7). Cross-read against Simpson C-C-2026 pp. 66-68, which prints the same rows.
Values are ASD lbf, 2,500 psi concrete, columns (midwall, corner, endwall).
"""

from __future__ import annotations

from dataclasses import dataclass

CITATION = ("ICC-ES ESR-2920 (reissued Feb 2026) Table 1, p. 6; Figure 1, p. 7; §4.2; "
            "Simpson C-C-2026 pp. 66-68")


@dataclass(frozen=True)
class StrapRow:
    """One Table 1 row: embedment, nails, and (midwall, corner, endwall) allowables."""

    le_in: float
    nails_wind: int
    wind_uncracked: tuple[float, float, float]
    wind_cracked: tuple[float, float, float]
    nails_sdc_cf: int
    sdc_cf_uncracked: tuple[float, float, float]
    sdc_cf_cracked: tuple[float, float, float]


#: (minimum stem wall thickness in, model without "RJ") -> row. RJ rows are the same.
TABLE_1: dict[tuple[int, str], StrapRow] = {
    (6, "LSTHD8"): StrapRow(8.0, 20, (2985, 2590, 1620), (2565, 2225, 1395),
                            16, (2270, 2090, 1220), (2250, 1950, 1220)),
    (6, "STHD10"): StrapRow(10.0, 24, (3535, 3535, 1960), (2910, 2910, 1635),
                            18, (2750, 2750, 1615), (2550, 2550, 1435)),
    (6, "STHD14"): StrapRow(14.0, 30, (4935, 4935, 3065), (4935, 4935, 3065),
                            22, (3695, 3695, 2685), (3695, 3695, 2685)),
    (8, "LSTHD8"): StrapRow(8.0, 20, (2985, 2590, 2135), (2565, 2225, 1835),
                            16, (2615, 2125, 1635), (2250, 1950, 1610)),
    (8, "STHD10"): StrapRow(10.0, 28, (4755, 4075, 3015), (4020, 3350, 2480),
                            20, (3400, 2940, 2295), (3400, 2940, 2175)),
    (8, "STHD14"): StrapRow(14.0, 30, (5285, 5285, 4410), (5285, 5285, 4410),
                            24, (3815, 3815, 3500), (3815, 3815, 3500)),
}
STEM_THICKNESSES_IN = (8, 6)
LOCATIONS = ("midwall", "corner", "endwall")

#: Table 1 "Strap Length (L)": standard and rim-joist, inches.
STANDARD_LENGTH_IN = {"LSTHD8": 18.625, "STHD10": 24.625, "STHD14": 26.125}
RJ_LENGTH_IN = {"LSTHD8": 32.125, "STHD10": 38.125, "STHD14": 39.625}
#: Figure 1: the spoon's horizontal reach from the strap face, (min, max) inches.
SPOON_PROJECTION_IN = {"LSTHD8": (4.0, 4.5), "STHD10": (4.75, 5.25), "STHD14": (4.75, 5.25)}
#: §3.1.1: the cast-in portion is 2 5/8" wide.
EMBEDDED_WIDTH_IN = 2.625
#: §3.2.5.
MIN_FC_PSI = 2500.0
#: §3.2.6 / §4.2: one No. 4 bar 3-5" below the top of foundation, in the failure region.
MIN_BAR = 4
BAR_BAND_IN = (3.0, 5.0)
#: Figure 1: minimum rebar length 2 x le each side (midwall), past the strap (endwall); a
#: corner bar turns it, 2 x le (LSTHD8, STHD10) or 24" (STHD14) along the return.
REBAR_LE = 2.0
CORNER_LEG_IN = {"LSTHD8": None, "STHD10": None, "STHD14": 24.0}
#: Figure 1: 1/2" minimum end distance (corner, endwall); Table 1 fn. 7: midwall is based
#: on 1.5 x le end distance and straps acting together sit at least 3 x le apart.
MIN_END_DISTANCE_IN = 0.5
MIDWALL_END_LE = 1.5
SPACING_LE = 3.0
#: Figure 1 / C-C-2026 p. 66: an RJ strap crosses up to 17" clear "without any loss of strap
#: nailing". No clear span is printed for the standard strap: Figure 1 draws it over one 2x
#: sill, so that is all a standard strap is read at. (17 - 13 1/2 = 3 1/2" is arithmetic on
#: the two lengths, not a published limit.)
RJ_CLEAR_SPAN_MAX_IN = 17.0
STANDARD_CLEAR_SPAN_IN = 1.5
#: C-C-2026 p. 66: no horizontal cold joint within the embedment depth.
COLD_JOINT_RULE = "C-C-2026 p. 66 installation note (a)"

#: An unsized family name and the sizes it could be bought as.
FAMILIES = {"STHD": ("STHD10", "STHD14"), "LSTHD": ("LSTHD8",)}


def is_strap_holdown(part: str | None) -> bool:
    return str(part or "").upper().strip().startswith(("STHD", "LSTHD"))


def is_rim_joist(part: str) -> bool:
    return part.upper().strip().endswith("RJ")


def sizes(part: str) -> tuple[str, ...]:
    """Table 1 models ``part`` could be: itself (RJ stripped), or every size of a family."""
    base = part.upper().strip().removesuffix("RJ")
    if base in FAMILIES:
        return FAMILIES[base]
    return (base,) if base in STANDARD_LENGTH_IN else ()


def max_clear_span_in(part: str) -> float:
    """The unnailed span (pour top to the first stud) the strap is published across."""
    return RJ_CLEAR_SPAN_MAX_IN if is_rim_joist(part) else STANDARD_CLEAR_SPAN_IN


#: A strap jogged above the pour is not a published installation: §4.2's one cycle is bent
#: back plumb "to aid wall placement", and C-C-2026 p. 68 casts an off-face strap plumb at
#: the framing (spoon straightened, 8" wall). 12 ga at 2 5/8" yields at T x jog ~ 0.23 k-in.
JOG_RULE = ("ESR-2920 Figure 1 and C-C-2026 p. 68 show the strap rising plumb from where it "
            "is cast; §4.2's one cycle aids wall placement and prints no offset")


def allowable(size: str, stem_in: int, location: str, cracked: bool,
              seismic_cf: bool = False) -> float:
    row = TABLE_1[(stem_in, size)]
    cols = ((row.sdc_cf_cracked if cracked else row.sdc_cf_uncracked) if seismic_cf
            else (row.wind_cracked if cracked else row.wind_uncracked))
    return float(cols[LOCATIONS.index(location)])
