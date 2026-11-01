"""The north entry's LUS face-mount hangers, off C-C-2026 p. 114 (geometry review C3-E11/E12).

Split from ``simpson_hangers.py`` for the 500-line rule; same idiom and roles.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_TREATED,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

#: C-C-2026 p. 114, "Face-Mount Hangers — Solid Sawn Lumber (DF/SP)", read 2026-10-31 off
#: the 2026-2027 catalog PDF. Footnote 1 (p. 118): uplift already increased for wind.
_C_C_2026_P114 = ("Simpson Strong-Tie Wood Construction Connectors C-C-2026 p. 114, "
                  "\"Face-Mount Hangers - Solid Sawn Lumber (DF/SP)\", read 2026-10-31")

#: The north entry's two seat beams (a 2-2x8, 3" x 7 1/4") off the 6x6 KDAT canopy columns
#: (catlin CN-BW-HGR-CW/-CNW, geometry review C3-E12). Capacity-only for the reason HU28-2Z
#: is: a second ROLE_FACE_MOUNT_JOIST_HANGER in STRUCTURAL_HARDWARE would make the derived
#: hanger role ambiguous. p. 114 prints LUS26-2 on both the DBL 2x6 and the DBL 2x8 rows —
#: H 4 7/8" is 67% of a 2x8, inside the catalog's own 2x8 selection.
LUS26_2Z_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lus26-2z-face-mount-hanger",
    name="LUS26-2Z face-mount hanger, double 2x6/2x8 (ZMAX)",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LUS26-2Z",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("2-2x6", "2-2x8"),
    source="Simpson Strong-Tie LUS26-2 in ZMAX (G185) — 18 ga, W 3-1/8\", H 4-7/8\", B 2\" "
           "(C-C-2026 p. 114); ZMAX per IRC R317.3.1 on a preservative-treated carrier, a "
           "stocked retail SKU",
    allowable=AllowableLoads(
        uplift_lb=1060.0,
        download_lb=1030.0,
        load_duration_factor=1.0,
        species="DF/SP — the southern pine KDAT post and beam it joins",
        fasteners="(4) 0.162 x 3-1/2 into the header, (4) 0.162 x 3-1/2 into the joist "
                  "(double-shear)",
        citation=(_C_C_2026_P114 + ", DBL 2x8 joist size, LUS26-2 row: uplift (160) 1,060, "
                  "floor (100) 1,030, snow (115) 1,170, roof (125) 1,265 lb. download_lb is "
                  "the floor column; dry values — take NDS C_M 0.70 in wet service"),
    ),
)

#: The single-2x8 screen sill BM-BW-SCSILL off the same columns (catlin CN-BW-HGR-SCS-S/-N,
#: geometry review C3-E11). The derived LUS28Z rows bill under the LUSZ family record; this
#: one gives the exact designation its own allowable.
LUS28Z_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lus28z-face-mount-hanger",
    name="LUS28Z face-mount hanger, 2x8 (ZMAX)",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LUS28Z",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("2x8",),
    source="Simpson Strong-Tie LUS28 in ZMAX (G185) — 18 ga, W 1-9/16\", H 6-5/8\", "
           "B 1-3/4\" (C-C-2026 p. 114); ZMAX per IRC R317.3.1 on a preservative-treated "
           "carrier",
    allowable=AllowableLoads(
        uplift_lb=1165.0,
        download_lb=1100.0,
        load_duration_factor=1.0,
        species="DF/SP — the southern pine KDAT post and sill it joins",
        fasteners="(6) 0.148 x 3 into the header, (4) 0.148 x 3 into the joist (double-shear)",
        citation=(_C_C_2026_P114 + ", 2x8 joist size, LUS28 row: uplift (160) 1,165, floor "
                  "(100) 1,100, snow (115) 1,260, roof (125) 1,350 lb. download_lb is the "
                  "floor column; dry values — take NDS C_M 0.70 in wet service"),
    ),
)
