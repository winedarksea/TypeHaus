"""The sidewalk: driveway -> garage east side -> north entry landing -> house east -> porch stair.

One `Slab` per leg on `yard-grade`, `SIDEWALK_FRC_CLASS5` (4" fibre-only concrete on 6" of
MnDOT Class 5). The full section is 12 | 16 pocket | 36 walk | 16 pocket | 12 = 92"; the
east side of the house is one-sided, 36 walk | 16 pocket | 12 = 64", because the house to
lot line is only 6'-4". Pockets are 16" sonotube voids (`FloorOpening(purpose=PLANTING)`)
at 4'-0" o.c. down each pocket zone, the run's slack split evenly between its two ends —
except leg A, which is anchored to the corner it turns into leg B (see `_A_STATIONS`).
Control joints fall on the same stations.

Each slab is modelled flat at its high edge, 1" over the -2'-10" grade so it never cuts the
earth sheet; the fall lives on a matching `ImperviousSurface(kind="walk")`, merged into
the site by `plan/manifest.py`. 1/2" isolation gaps at the garage stem flashing, the
canopy column PT-BW-RNE, the HP1 pad and the stair pad. notes/sidewalk_layout.md.
"""

from __future__ import annotations

import math

from typehaus import (
    FloorOpening,
    FloorOpeningPurpose,
    ImperviousSurface,
    PlantingBed,
    PocketLayout,
    Slab,
    ft,
    inch,
    pt,
)

ASSEMBLY = "SIDEWALK_FRC_CLASS5"
TOP = ft(-2, -9)                 # 1" over grade
POCKET_R_IN = 8.0
POCKET_OC_FT = 4.0
_END_INSET_FT = 2.0              # the minimum; the run's slack is split between both ends
_FACETS = 16
GAP_FT = 0.5 / 12.0             # isolation joint

# Pocket-zone centres across the section, from the leg's reference edge (feet).
FULL = (20.0 / 12.0, 72.0 / 12.0)    # 12 + 8, and 92 - 20
ONE_SIDED = (44.0 / 12.0,)           # 36 walk + 8, measured off the house side


def _ring(points):
    return tuple(pt(ft(x), ft(y)) for x, y in points)


def _rect(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


# --- legs -------------------------------------------------------------------------------
# A: in front of the garage, from the driveway's east edge (x=24') to past the garage NE
#    corner, 92" deep off the garage face (stem Z-flashing at y=67'-3 1/2" plus 1/2").
# B: down the garage east side, stem flashing at x=30'-0 7/8" plus 1/2", to clear of the
#    canopy column PT-BW-RNE (y 41'-11 3/4"..42'-11 3/4").
# C: the landing connector, walk only, notched round PT-BW-RNE to reach the paver landing's
#    east edge (x=30') south of it; its south edge leaves a 3" gravel drip strip on the HP1
#    pad's north edge, clear of the unit's defrost.
# D: the house east side, one-sided 64", off the NE/SE corner trims (x=36'-7 7/8") plus 1/2".
#    It absorbs the old side patio; no pockets along the patio's 12' (y 10'..22').
# No leg E: SL-SG-STAIRPAD (params/sunken_garden.py) runs east to D's west edge, less the
#    1/2" joint, and is the walk's south end.
A = _rect(24.0 + GAP_FT, 67.29 + GAP_FT, 37.78, 67.29 + GAP_FT + 92.0 / 12.0)
B = _rect(30.07 + GAP_FT, 42.98 + GAP_FT, 37.78, A[0][1])
D_X0 = 36.66 + GAP_FT
D_X1 = D_X0 + 64.0 / 12.0
C = ((30.0 + GAP_FT, 39.6), (D_X1, 39.6), (D_X1, B[0][1]), (30.5 + GAP_FT, B[0][1]),
     (30.5 + GAP_FT, 41.98 - GAP_FT), (30.0 + GAP_FT, 41.98 - GAP_FT))
D = _rect(D_X0, -9.0, D_X1, 39.6)

# NO POCKET SITS AT A LEADER'S FOOT, and neither east leader can have one: TR-RF-LEADER-E
# stands at x=36'-10 9/16", over leg D's 36" walking band, where a 16" void would leave
# 1.6" of concrete at the slab edge. Both east leaders drop onto the walk; their extensions
# are a later detail (notes/sidewalk_layout.md §3, §5).


def _stations(start: float, end: float) -> list[float]:
    """Pocket stations, 4'-0" o.c., CENTRED in the run, never inside `_END_INSET_FT`."""
    run = end - start
    n = int((run - 2 * _END_INSET_FT) // POCKET_OC_FT) + 1
    if n < 1:
        return []
    inset = (run - (n - 1) * POCKET_OC_FT) / 2
    return [round(start + inset + k * POCKET_OC_FT, 4) for k in range(n)]


def _pockets(rect, along: str, zones, ref_high: bool = False,
             skip=lambda s: False, stations=None) -> list[tuple[float, float]]:
    (x0, y0), _, (x1, y1), _ = rect
    centres = []
    if along == "x":
        for s in stations or _stations(x0, x1):
            for z in zones:
                centres.append((s, y1 - z if ref_high else y0 + z))
    else:
        for s in stations or _stations(y0, y1):
            for z in zones:
                centres.append((x1 - z if ref_high else x0 + z, s))
    return [c for c in centres if not skip(c[0] if along == "x" else c[1])]


# LEG A IS ANCHORED TO THE CORNER IT TURNS, NOT CENTRED IN ITS OWN RUN. Its two pocket rows
# cross leg B's whole width, so its stations have to BE leg B's pocket columns: the pocket
# band then turns the L in line — the inner corner at B's west column, the outer at its east
# — and leg B's 36" walk arrives under open concrete instead of under a void. Anything else
# drops a pocket into the turn. Spacing is the section's own 52" row pitch, marched west
# while 12" of concrete is left at the end; B and D end at joints with no band to meet and
# centre in their runs.
_A_OC = FULL[1] - FULL[0]
_A_STATIONS: list[float] = []
_s = B[0][0] + FULL[1]
while _s - POCKET_R_IN / 12.0 >= A[0][0] + 1.0:
    _A_STATIONS.append(round(_s, 4))
    _s -= _A_OC
_A_STATIONS.reverse()


POCKET_CENTRES = {
    "A": _pockets(A, "x", FULL, stations=_A_STATIONS),
    "B": _pockets(B, "y", FULL),
    # One-sided: the zone is measured off the HOUSE (west) edge. The skip is a CENTRE test
    # over the retired patio's own 12' — padded by a radius it lands within 0.4" of a
    # station and the count turns on floating-point noise.
    "D": _pockets(D, "y", ONE_SIDED, skip=lambda y: 10.0 <= y <= 22.0),
}


def _circle(x: float, y: float):
    r = POCKET_R_IN / 12.0
    return _ring((x + r * math.cos(2 * math.pi * k / _FACETS),
                  y + r * math.sin(2 * math.pi * k / _FACETS)) for k in range(_FACETS))


OPENINGS: dict[str, list[FloorOpening]] = {
    leg: [FloorOpening(uid=f"WKP{leg}{n:03d}000", tag=f"FO-WK-{leg}{n + 1:02d}",
                       outline=_circle(x, y), purpose=FloorOpeningPurpose.PLANTING)
          for n, (x, y) in enumerate(centres)]
    for leg, centres in POCKET_CENTRES.items()
}


def _slab(leg: str, ring, top=TOP) -> Slab:
    return Slab(uid=f"WKSB{leg}00000", tag=f"SL-WK-{leg}", assembly=ASSEMBLY,
                outline=_ring(ring), thickness=inch(4.0), top_elevation=top,
                openings=tuple(o.tag for o in OPENINGS.get(leg, ())))


SLABS = [_slab("A", A), _slab("B", B), _slab("C", C), _slab("D", D)]

POCKET_BED = PlantingBed(
    uid="GRDNPB0005", tag="PB-WK-POCKETS", type_ref="PT-CAL-NEPETA",
    pockets=PocketLayout(slab_refs=("SL-WK-A", "SL-WK-B", "SL-WK-D"),
                         type_refs=("PT-CAL-NEPETA", "PT-ALL-MILLENIUM", "PT-SPO-TARA",
                                    "PT-SAL-PURP")),
)

# The fall, 2% or more, away from whatever the leg abuts. Pocket voids are NOT subtracted
# from the impervious area, which is conservative.
IMPERVIOUS = (
    # R401.3 measures A and C over their long runs (10.9' and 12'), so each falls 3".
    ImperviousSurface(label="walk A, garage north", outline=_ring(A),
                      near_elevation=TOP, far_elevation=ft(-3), kind="walk"),
    ImperviousSurface(label="walk B, garage east", outline=_ring(B),
                      near_elevation=TOP, far_elevation=ft(-3), kind="walk"),
    ImperviousSurface(label="walk C, landing connector", outline=_ring(C),
                      near_elevation=TOP, far_elevation=ft(-3), kind="walk"),
    ImperviousSurface(label="walk D, house east", outline=_ring(D),
                      near_elevation=TOP, far_elevation=ft(-2, -11), kind="walk"),  # 2" over 7.2'
)

MAIN_ELEMENTS = [*SLABS, *(o for leg in OPENINGS.values() for o in leg), POCKET_BED]
