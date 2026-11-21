"""Simpson LUC concealed-flange face-mount hangers, off C-C-2026 (read 2026-11-20).

p. 110: "LUC — Concealed-flange hanger available for 2x6, 2x8, 2x10 and 2x12 lumber. Ideal
for end of ledger/header or post conditions." An LUS's 1" outside flanges make it 3 9/16"
wide (p. 112), wider than a 4x4 face; the LUC's stay inside its 1 9/16" seat. Sold in ZMAX
only. Allowables are the SPF/HF table (pp. 119-120): every post these land on is SPF or
better, and the DF/SP row (pp. 114-115) is higher. Footnote 1 (p. 123): uplift is already
increased for wind; side-grain nailing, so the p. 110 end-grain 0.67 does not apply.

Screwed, not nailed: a post can carry hangers on opposite faces at one seat (the cut rim
through P-M-STRWELL-S), and a 0.162 x 3 1/2 header nail from each side would meet in a
3 1/2" post. p. 26 replaces the 0.162 x 3 1/2 face-mount header nail with a #10 x 1 1/2 SD
screw (SD10112) and the 0.148 x 1 1/2 joist nail with a #9 x 1 1/2 (SD9112), both 1.00
download/uplift; footnote 5 forbids mixing nails and screws in one connection. Each side
then reaches ~1 7/16" into the post, so opposite faces stay ~5/8" apart.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_CONCEALED_FLANGE_HANGER,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

_SPF = ("Simpson Strong-Tie Wood Construction Connectors C-C-2026, \"Face-Mount Hangers - "
        "Solid Sawn Lumber (SPF/HF)\"")

LUC26Z_CONCEALED_HANGER = StructuralHardware(
    tag="simpson-luc26z-concealed-hanger",
    name="LUC26Z concealed-flange face-mount hanger, 2x6/2x8 (ZMAX)",
    role=ROLE_CONCEALED_FLANGE_HANGER,
    manufacturer=_SIMPSON,
    model="LUC26Z",
    fits_nominal=("2x6", "2x8"),
    source="Simpson Strong-Tie LUC26Z — 18 ga, W 1-9/16\", H 4-3/4\", B 1-3/4\", flanges "
           "concealed (C-C-2026 pp. 110, 119); listed on both the 2x6 and the 2x8 joist rows",
    allowable=AllowableLoads(
        uplift_lb=630.0,
        download_lb=610.0,
        load_duration_factor=1.0,
        species="SPF/HF carrier and joist",
        fasteners="(6) SD10112 into the header, (4) SD9112 into the joist (p. 26, 1.00)",
        citation=(_SPF + " p. 119, 2x8 joist size, LUC26Z row: uplift (160) 630, floor (100) "
                  "610, snow (115) 695, roof (125) 755 lb. download_lb is the floor column. "
                  "DF/SP p. 114: 730 / 845 / 965 / 1,040"),
    ),
)

LUC210Z_CONCEALED_HANGER = StructuralHardware(
    tag="simpson-luc210z-concealed-hanger",
    name="LUC210Z concealed-flange face-mount hanger, 2x10/2x12 (ZMAX)",
    role=ROLE_CONCEALED_FLANGE_HANGER,
    manufacturer=_SIMPSON,
    model="LUC210Z",
    fits_nominal=("2x10", "2x12"),
    source="Simpson Strong-Tie LUC210Z — 18 ga, W 1-9/16\", H 7-3/4\", B 1-3/4\", flanges "
           "concealed (C-C-2026 pp. 110, 120)",
    allowable=AllowableLoads(
        uplift_lb=845.0,
        download_lb=1020.0,
        load_duration_factor=1.0,
        species="SPF/HF carrier and joist",
        fasteners="(10) SD10112 into the header, (6) SD9112 into the joist (p. 26, 1.00)",
        citation=(_SPF + " p. 120, 2x10 joist size, LUC210Z row: uplift (160) 845, floor "
                  "(100) 1,020, snow (115) 1,155, roof (125) 1,250 lb. DF/SP p. 115: 985 / "
                  "1,410 / 1,605 / 1,735"),
    ),
)
