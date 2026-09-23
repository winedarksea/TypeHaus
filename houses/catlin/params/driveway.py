"""The driveway: D-G-OVERHEAD's door line north to the front lot line.

One `Slab`, `SL-DW-DRIVE`, on `yard-grade`, in `DRIVEWAY_FRC_CLASS5` (4" fibre-only
EXPOSED_MIX on 8" of MnDOT Class 5, no foam). It is modelled flat at its high edge, 1"
below the -2'-10" garage slab, which is the sidewalk's convention. The fall to the street
lives on the matching `ImperviousSurface(kind="driveway")` because a `Slab` cannot slope,
and `plan/manifest.py` merges that surface into the site. notes/driveway_layout.md is the
quantity oracle.

** SHAPE. ** It is 16'-0" wide at the door (x 10'..26', the jambs) and tapers at 45° both
sides to 12'-0" (x 12'..24') `FLARE` out, holding 12' to the lot line at y = 84'-6".
12' is the ORDINANCE width: Ord. 23-43 caps a front-yard driveway at 12'-0", and the flare
is what lets a car leave a 16' door. The drive is ~210 sf. Ord. 23-43's paving cap is the
lesser of 15% of the 6,650 sf lot and 1,000 sf, so 15% = 997.5 sf governs. The drive plus
the three `kind="pad"` surfaces sit well under that. `emit/draw/site_metrics.py` shows the
cap in the C-101 coverage table, and no check grades it.

** THE K8 JOINT IS THE 1" GAP, NOT AN ELEMENT. ** `Y0` is the grade beam W-GF-N-DR's
resolved outer face at the door, its aluminium stem band (y 67'-2 5/8" node line + 1/4"
standoff + coil), plus 1". The 1" is the K8 joint in notes/garage_wall_detail_side.md:
1" 40 psi XPS (Foamular 400, ASTM C578 Type VI, the garage slab's grade) under 1/2" of
traffic-rated polyurethane sealant, ~16 LF. It is deliberately not an `IsolationBoard`,
because that element spawns a `thermal_break_transfer` engineering item wanting a seal,
and a flatwork joint needs none. The price row carries the strip.

** CONTROL JOINTS ARE NOT AN ENGINE CONCEPT, SO THEY ARE HERE. ** ACI 332 limits joint
spacing to ~30 x t, or 10' for 4". The 12' panel needs one longitudinal joint on the
centreline, x = 18'. Transverse sawcuts go at <= 10' o.c., two across the 17' run, the
first on the taper line (Y0 + FLARE) so the flare's corners are not re-entrant cracks.

** WHY IT EXISTS. ** Saint Paul DSI will not review a garage a car cannot reach, and the drive
is the only way a vehicle leaves the site, so `plan/site.py`'s rock construction entrance
sits on it. The fall starts 1" below the garage threshold so the drive sheds away from the
slab. `code.R401_3_impervious` does not reach it: that check measures off the house
footprint (y <= 36'), and this starts ~31' north of it.

Walk A (params/landscape_walk.py) meets the east taper with a 1/2" isolation joint.
"""

from __future__ import annotations

from typehaus import ImperviousSurface, Slab, ft, inch, pt

ASSEMBLY = "DRIVEWAY_FRC_CLASS5"
TOP = ft(-2, -11)                    # 1" below the garage slab, at the door
FALL_TO = ft(-3, -3.5)               # at the lot line: 4 1/2" over the run, 2.18%

#: W-GF-N-DR's outer face at the door: node line + 1/4" coil standoff + 0.05" coil.
GRADE_BEAM_FACE_Y = 67.0 + 2.925 / 12.0
JOINT_FT = 1.0 / 12.0                # K8: 1" XPS
Y0 = GRADE_BEAM_FACE_Y + JOINT_FT
Y_LOT = 84.5                         # front (north) lot line
DOOR_X = (10.0, 26.0)                # D-G-OVERHEAD's jambs
DRIVE_X = (12.0, 24.0)               # the 12' ordinance width, centred on x = 18'
FLARE = 2.0                          # 45°: the taper's run equals its 2' step-in

OUTLINE = (
    (DOOR_X[0], Y0), (DOOR_X[1], Y0),
    (DRIVE_X[1], Y0 + FLARE), (DRIVE_X[1], Y_LOT),
    (DRIVE_X[0], Y_LOT), (DRIVE_X[0], Y0 + FLARE),
)


def _ring(points):
    return tuple(pt(ft(x), ft(y)) for x, y in points)


# The uid is minted by typehaus.model.ids.new_uid(): `haus fmt` never visits params/.
SLAB = Slab(uid="BQB250N77B", tag="SL-DW-DRIVE", assembly=ASSEMBLY,
            outline=_ring(OUTLINE), thickness=inch(4.0), top_elevation=TOP)

IMPERVIOUS = (
    ImperviousSurface(label="driveway", outline=_ring(OUTLINE),
                      near_elevation=TOP, far_elevation=FALL_TO, kind="driveway"),
)

MAIN_ELEMENTS = [SLAB]
