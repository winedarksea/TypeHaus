"""The sidewalk: driveway -> garage east side -> north entry landing -> house east -> porch stair.

One `Slab` per leg on `yard-grade`, `SIDEWALK_FRC_CLASS5` (4" fibre-only concrete on 6" of
MnDOT Class 5). Leg A in front of the garage is the full section,
12 | 16 pocket | 36 walk | 16 pocket | 12 = 92"; legs B and D are one-sided,
36 walk | 16 pocket | 12 = 64", walk against the building: the house to lot line is only
6'-4", and east of the garage RG-E-BASIN owns the strip beyond. Pockets are 16" sonotube voids (`FloorOpening(purpose=PLANTING)`)
at 4'-0" o.c. down each pocket zone, the run's slack split evenly between its two ends —
except leg A, which is anchored to the corner it turns into leg B (see `_A_STATIONS`).
Control joints fall on the same stations.

Each slab is modelled flat at its high edge, 1" over the -2'-10" grade so it never cuts the
earth sheet; the fall lives on a matching `ImperviousSurface(kind="walk")`, merged into
the site by `plan/manifest.py`. 1/2" isolation gaps at the garage stem flashing, the
canopy columns PT-BW-RE/-RNE, the entry tiers, the HP1 pad and the stair pad.
notes/sidewalk_layout.md.
"""

from __future__ import annotations

from typehaus.geometry import ring
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
)

from params.breezeway import STAIR_FOOT_X_FT, STAIR_Y0_FT, STAIR_Y1_FT
from params.driveway import DRIVE_X, FLARE, Y0 as DRIVE_Y0
from params.hp1_north_pad import HP1_PAD
from params.north_entry_frame import GARAGE_SEAT_Y_FT, PIER_LINE_Y_FT, ROOF_COLUMN_EAST_X_FT

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


_ring = ring


def _rect(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


# --- legs -------------------------------------------------------------------------------
# A: in front of the garage, from the driveway's east edge (x=24') to leg B's east edge,
#    92" deep off the garage face (stem Z-flashing at y=67'-3 1/2" plus 1/2").
#    Its SW corner is notched round the drive's 45° flare, 1/2" off it (`A_RING`).
# B: down the garage east side, one-sided 64" off the stem flashing at x=30'-0 7/8" plus
#    1/2", to clear of the canopy column PT-BW-RNE (y 41'-11 3/4"..42'-11 3/4"). It was the
#    full 92" until 2026-09-23; its east 28" is where RG-E-BASIN (x 37'..42') mirrors the
#    west basin, 1'-7" of lawn off the slab.
# C: the entry walk, walk only. Under the canopy it is the full passage width, 3" off both
#    claddings, from ST-BW-ENTRY's foot (less the joint to SL-BW-TIER1) east to the two
#    canopy columns; it passes between PT-BW-RE and PT-BW-RNE, notched round both. Just
#    east of them it stays full width to the HP1 pad, wrapping PT-BW-RE, then narrows to run
#    on east to leg D. Both pad edges it meets keep a 3" gravel drip strip, clear of the
#    unit's defrost. It replaced the drained paver landing under the canopy on 2026-09-23;
#    its top is the flight's springing (breezeway.py).
# D: the house east side, one-sided 64", off the NE/SE corner trims (x=36'-7 7/8") plus 1/2".
#    It absorbs the old side patio; no pockets along the patio's 12' (y 10'..22').
# No leg E: SL-SG-STAIRPAD (params/sunken_garden.py) runs east to D's west edge, less the
#    1/2" joint, and is the walk's south end.
B_X0 = 30.07 + GAP_FT
B_X1 = B_X0 + 64.0 / 12.0
A = _rect(24.0 + GAP_FT, 67.29 + GAP_FT, B_X1, 67.29 + GAP_FT + 92.0 / 12.0)
B = _rect(B_X0, 42.98 + GAP_FT, B_X1, A[0][1])
D_X0 = 36.66 + GAP_FT
D_X1 = D_X0 + 64.0 / 12.0
_COL_R_FT = 0.5                  # PT-BW-RE/-RNE are "12 round"
_COL_W = ROOF_COLUMN_EAST_X_FT - _COL_R_FT - GAP_FT
_COL_E = ROOF_COLUMN_EAST_X_FT + _COL_R_FT + GAP_FT
_RE_N = PIER_LINE_Y_FT + _COL_R_FT + GAP_FT
_RNE_S = GARAGE_SEAT_Y_FT - _COL_R_FT - GAP_FT
_C_FOOT_X = STAIR_FOOT_X_FT + GAP_FT
_DRIP_FT = 3.0 / 12.0
_HP1_W = min(v.x.feet for v in HP1_PAD.outline) - _DRIP_FT
C = ((_C_FOOT_X, STAIR_Y0_FT), (_COL_W, STAIR_Y0_FT), (_COL_W, _RE_N), (_COL_E, _RE_N),
     (_COL_E, STAIR_Y0_FT), (_HP1_W, STAIR_Y0_FT), (_HP1_W, 39.6), (D_X1, 39.6), (D_X1, B[0][1]), (_COL_E, B[0][1]), (_COL_E, _RNE_S),
     (_COL_W, _RNE_S), (_COL_W, STAIR_Y1_FT), (_C_FOOT_X, STAIR_Y1_FT))
D = _rect(D_X0, -9.0, D_X1, 39.6)

# The flare's east edge is the line x + y = K; offset 1/2" square to it, K grows by GAP*√2.
_K = DRIVE_X[1] + FLARE + DRIVE_Y0 + GAP_FT * math.sqrt(2.0)
A_RING = ((_K - A[0][1], A[0][1]), A[1], A[2], A[3], (A[0][0], _K - A[0][0]))

# NO POCKET SITS AT A LEADER'S FOOT, and neither east leader can have one: TR-RF-LEADER-E
# stands at x=36'-10 9/16", over leg D's 36" walking band, where a 16" void would leave
# 1.6" of concrete at the slab edge. Both east leaders' risers pass down through the walk to
# their buried extensions into RG-E-BASIN (notes/rain_garden_sizing.md §6).


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
# cross leg B's whole width, so its first station has to BE leg B's pocket column, and the
# next one the section's own 52" row pitch west of it — which lands tangent to B's 36" walk
# on its west side: leg B's walk arrives under open concrete instead of under a void.
# Anything else drops a pocket into the turn. Marched west while 12" of concrete is left at
# the end; B and D end at joints with no band to meet and centre in their runs.
_A_OC = FULL[1] - FULL[0]
_A_STATIONS: list[float] = []
_s = B[0][0] + ONE_SIDED[0]
while _s - POCKET_R_IN / 12.0 >= A[0][0] + 1.0:
    _A_STATIONS.append(round(_s, 4))
    _s -= _A_OC
_A_STATIONS.reverse()


POCKET_CENTRES = {
    "A": _pockets(A, "x", FULL, stations=_A_STATIONS),
    "B": _pockets(B, "y", ONE_SIDED),
    # One-sided: the zone is measured off the HOUSE (west) edge. The skip is a CENTRE test
    # over the retired patio's own 12' — padded by a radius it lands within 0.4" of a
    # station and the count turns on floating-point noise.
    "D": _pockets(D, "y", ONE_SIDED, skip=lambda y: 10.0 <= y <= 22.0),
}


def _circle(x: float, y: float):
    r = POCKET_R_IN / 12.0
    return _ring((x + r * math.cos(2 * math.pi * k / _FACETS),
                  y + r * math.sin(2 * math.pi * k / _FACETS)) for k in range(_FACETS))


# Struck after the grid is laid, so the others keep their tags. A01 is the garage NE
# corner's, beside TR-G-LEADER-E's drop (plan/storeys/garage.py).
DROPPED = frozenset({"FO-WK-A01"})

OPENINGS: dict[str, list[FloorOpening]] = {
    leg: [FloorOpening(uid=f"WKP{leg}{n:03d}000", tag=f"FO-WK-{leg}{n + 1:02d}",
                       outline=_circle(x, y), purpose=FloorOpeningPurpose.PLANTING)
          for n, (x, y) in enumerate(centres) if f"FO-WK-{leg}{n + 1:02d}" not in DROPPED]
    for leg, centres in POCKET_CENTRES.items()
}


def _slab(leg: str, ring, top=TOP) -> Slab:
    return Slab(uid=f"WKSB{leg}00000", tag=f"SL-WK-{leg}", assembly=ASSEMBLY,
                outline=_ring(ring), thickness=inch(4.0), top_elevation=top,
                openings=tuple(o.tag for o in OPENINGS.get(leg, ())))


SLABS = [_slab("A", A_RING), _slab("B", B), _slab("C", C), _slab("D", D)]

POCKET_BED = PlantingBed(
    uid="GRDNPB0005", tag="PB-WK-POCKETS", type_ref="PT-CAL-NEPETA",
    # The cycle starts at Allium, not Calamintha, because FO-WK-A01 (a Calamintha) was
    # struck: rotated one place, every surviving pocket keeps its species.
    pockets=PocketLayout(slab_refs=("SL-WK-A", "SL-WK-B", "SL-WK-D"),
                         type_refs=("PT-ALL-MILLENIUM", "PT-SPO-TARA", "PT-SAL-PURP",
                                    "PT-CAL-NEPETA")),
)

# The fall, 2% or more, away from whatever the leg abuts. Pocket voids are NOT subtracted
# from the impervious area, which is conservative.
IMPERVIOUS = (
    # R401.3 measures A over its long run (10.9'), so it falls 3". C falls east from the
    # stair foot, its high edge, 3 1/2": R401.3 reads it 12.2' off the garage's SE corner.
    ImperviousSurface(label="walk A, garage north", outline=_ring(A_RING),
                      near_elevation=TOP, far_elevation=ft(-3), kind="walk"),
    ImperviousSurface(label="walk B, garage east", outline=_ring(B),
                      near_elevation=TOP, far_elevation=ft(-3), kind="walk"),
    ImperviousSurface(label="walk C, entry walk", outline=_ring(C),
                      near_elevation=TOP, far_elevation=ft(-3, -0.5), kind="walk"),
    ImperviousSurface(label="walk D, house east", outline=_ring(D),
                      near_elevation=TOP, far_elevation=ft(-2, -11), kind="walk"),  # 2" over 7.2'
)

MAIN_ELEMENTS = [*SLABS, *(o for leg in OPENINGS.values() for o in leg), POCKET_BED]
