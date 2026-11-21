"""A bolted hold-down on a cast-in SSTB: the two published rows it is read at.

Read 2026-11-20 from Simpson Strong-Tie C-C-2026 (local copy
``out/bw-corner-brace-review/C-C-2026.pdf``):

* **SSTB at stem wall**, p. 43: model, stem width, diameter, l_e and (middle, corner, end)
  ASD allowables, Wind and SDC A&B; the plan views (1 3/4" min edge distance, 5" end and
  corner distance, #4 bar 3-5" from the top, 2 l_e each way, a 16" corner return); fn. 5
  (midwall at 1.5 l_e, 3 l_e between bolts acting together); p. 42: 2,500 psi minimum.
* **HTT4**, p. 63: SPF/HF allowable on its (18) 0.148 x 1 1/2 nail row, minimum member
  1 1/2 x 3 1/2, anchor 5/8", CL 1 5/16" (rod centre off the member face), W 2 1/2".

The anchorage is the lesser of the two rows. Neither document addresses ICF: the core is
read as the stem, as ``hardware/esr2920.py`` reads it.
"""

from __future__ import annotations

from dataclasses import dataclass

CITATION_SSTB = ("Simpson C-C-2026 p. 43, SSTB Bolts at Stem Wall, Wind and SDC A&B; "
                 "Stemwall Plan Views; fn. 5; p. 42 installation")
CITATION_HTT = "Simpson C-C-2026 p. 63, LTT/HTT/HTTH table, HTT4 row"


@dataclass(frozen=True)
class SstbRow:
    stem_in: float
    diameter_in: float
    le_in: float
    wind: tuple[float, float, float]   # (middle, corner, end)


#: p. 43, the 6" stem-wall rows.
SSTB_STEM: dict[str, SstbRow] = {
    "SSTB16": SstbRow(6.0, 0.625, 12.625, (3465.0, 3465.0, 3465.0)),
    "SSTB20": SstbRow(6.0, 0.625, 16.625, (4145.0, 3880.0, 3880.0)),
    "SSTB24": SstbRow(6.0, 0.625, 20.625, (4825.0, 4295.0, 4295.0)),
}
#: Plan views: bolt centre to the concrete face, and to the end (corner or end view).
MIN_EDGE_IN = 1.75
MIN_END_IN = 5.0
#: fn. 5.
MIDWALL_LE = 1.5
SPACING_LE = 3.0
#: Plan views: one #4 bar 3-5" from the top, 2 l_e each side; a corner return of 16".
MIN_BAR = 4
BAR_BAND_IN = (3.0, 5.0)
BAR_LE = 2.0
CORNER_RETURN_IN = 16.0
MIN_FC_PSI = 2500.0


@dataclass(frozen=True)
class HoldownRow:
    allowable_spf_lb: float
    member_in: tuple[float, float]     # thickness x width, minimum
    anchor_in: float
    cl_in: float                       # rod centre off the member face
    width_in: float
    height_in: float


#: p. 63: (18) 0.148 x 1 1/2 into a 1 1/2 x 3 1/2 member — the SPF/HF column.
HOLDOWNS: dict[str, HoldownRow] = {
    "HTT4": HoldownRow(2580.0, (1.5, 3.5), 0.625, 1.3125, 2.5, 12.375),
}


def location(end_in: float, turns: bool, le_in: float) -> tuple[str, int]:
    """``(column name, index)``: middle at 1.5 l_e from the end, else corner or end."""
    if end_in >= MIDWALL_LE * le_in - 1e-6:
        return "middle", 0
    return ("corner", 1) if turns else ("end", 2)
