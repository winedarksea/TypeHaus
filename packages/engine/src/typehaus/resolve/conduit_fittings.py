"""Every part a raceway takes besides the tube: elbows, couplings, connectors, straps, boxes.

The raceway sibling of :func:`~typehaus.resolve.mep_fittings.fitting_records`, kept apart
because most of these parts are not at a vertex: a coupling is per stick, a strap per span.
Counts follow the installation articles, not a catalog:

* **Elbow** — each turn ``polyline_fittings`` finds (≥10°). EMT and PVC only: ENT flexes.
  Whether a field bend costs a part is the house's price, not this count.
* **Coupling** — one per extra stick (10 ft EMT/PVC), per pull-to-pull section, plus one at
  each chain joint (two polylines drawn as one raceway). ENT comes on a coil.
* **Connector** — one per section end. A derived NM sleeve takes an *offset* connector at
  its box and a nonmetallic *bushing* at its open top (NEC 334.15(B)); a floor-heat sensor
  tube is *capped* at the floor so the sensor can be replaced.
* **Strap** — within 3 ft of each termination, then every 10 ft (EMT, 358.30), 3 ft (ENT,
  362.30), 3-8 ft by size (PVC, Table 352.30). One strap serves a run of up to 6 ft. None
  on a cast-in run; a floor-heat lead is strapped only over its vertical (stud-bay) length.
* **Pull box** — one per ``pull_points`` index.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.conduit_pulls import raceway_chains
from typehaus.resolve.mep_fittings import FAMILY_RACEWAY, polyline_fittings
from typehaus.resolve.mep_queries import conduit_vertical_profile
from typehaus.resolve.model import ResolvedConduitRun, ResolvedModel

_M_PER_FT = 0.3048
#: Stick length by material, ft; None is a coil (no couplings).
STICK_FT = {"emt": 10.0, "pvc": 10.0, "ent": None}
#: (within ft of a termination, then every ft) by material.
STRAP_SPACING_FT = {"emt": (3.0, 10.0), "ent": (3.0, 3.0), "pvc": (3.0, 3.0)}
#: PVC's spacing grows with size (NEC Table 352.30): (largest trade size in, every ft).
PVC_SPACING_FT = ((1.0, 3.0), (2.0, 5.0), (3.0, 6.0), (5.0, 7.0), (6.0, 8.0))
#: A segment steeper than this is vertical (a stud-bay drop, not a floor pass).
_VERTICAL_RATIO = 10.0

ELBOW = "elbow"
COUPLING = "coupling"
CONNECTOR = "connector"
OFFSET_CONNECTOR = "offset_connector"
BUSHING = "bushing"
END_CAP = "end_cap"
STRAP = "strap"
PULL_BOX = "pull_box"


@dataclass(frozen=True)
class ConduitPart:
    """``count`` of one part on one run."""

    run_tag: str
    kind: str
    material: str
    trade_size_in: float
    count: int


def straps_for(length_ft: float, material: str, trade_size_in: float = 0.0) -> int:
    """Straps over one run between two terminations (358.30 and its siblings)."""
    if length_ft <= 1e-6:
        return 0
    end_ft, every_ft = STRAP_SPACING_FT.get(material, STRAP_SPACING_FT["emt"])
    if material == "pvc":
        every_ft = next((ft for size, ft in PVC_SPACING_FT if trade_size_in <= size + 1e-6),
                        PVC_SPACING_FT[-1][1])
    if length_ft <= 2 * end_ft:
        return 1  # one strap can be within reach of both ends
    middle = max(0.0, length_ft - 2 * end_ft)
    return 2 + max(0, math.ceil(middle / every_ft - 1e-9) - 1)


def couplings_for(length_ft: float, material: str) -> int:
    stick = STICK_FT.get(material, 10.0)
    if stick is None or length_ft <= stick:
        return 0
    return math.ceil(length_ft / stick - 1e-9) - 1


def _points(run: ResolvedConduitRun) -> list[tuple[float, float, float]]:
    profile = conduit_vertical_profile(run)
    if profile is None:
        return []
    path, z = profile
    return [(x, y, zz) for (x, y), zz in zip(path, z, strict=True)]


def _section_lengths_ft(points: list[tuple[float, float, float]], pulls: tuple[int, ...],
                        vertical_only: bool) -> list[float]:
    """Length of each pull-to-pull section, ft (only its vertical legs when asked)."""
    cuts = set(pulls)
    out, run = [], 0.0
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        plan = math.hypot(b[0] - a[0], b[1] - a[1])
        rise = abs(b[2] - a[2])
        if not vertical_only or rise > _VERTICAL_RATIO * plan:
            run += math.dist(a, b)
        if i in cuts:
            out.append(run / _M_PER_FT)
            run = 0.0
    out.append(run / _M_PER_FT)
    return out


def _run_parts(run: ResolvedConduitRun, joints: int) -> dict[str, int]:
    points = _points(run)
    if len(points) < 2:
        return {}
    material = run.material
    parts: dict[str, int] = {}
    if material != "ent" and not run.cast_in:
        # A turn at a pull box is the box's, not an elbow.
        boxes = [points[i] for i in run.pull_points if i < len(points)]
        parts[ELBOW] = sum(
            1 for record in polyline_fittings(run.tag, FAMILY_RACEWAY, "raceway", points,
                                              run.trade_size_m)
            if not any(math.dist(record.point, box) < 1e-6 for box in boxes))
    lengths = _section_lengths_ft(points, run.pull_points, False)
    parts[COUPLING] = sum(couplings_for(length, material) for length in lengths) + joints
    if run.derived == "nm_sleeve":
        parts[OFFSET_CONNECTOR] = 1
        parts[BUSHING] = 1
    elif run.derived == "fh_sensor":
        parts[CONNECTOR] = 1
        parts[END_CAP] = 1
    elif run.derived == "fh_cold_lead":
        parts[CONNECTOR] = 1
        parts[BUSHING] = 1
    else:
        parts[CONNECTOR] = 2 * len(lengths) - 2 * joints
    if not (run.cast_in and run.derived is None):
        strapped = _section_lengths_ft(points, run.pull_points,
                                       vertical_only=run.derived in ("fh_sensor",
                                                                     "fh_cold_lead"))
        size_in = run.trade_size_m / M_PER_IN
        parts[STRAP] = sum(straps_for(length, material, size_in) for length in strapped)
    parts[PULL_BOX] = len(run.pull_points)
    return {kind: count for kind, count in parts.items() if count > 0}


def conduit_parts(model: ResolvedModel) -> list[ConduitPart]:
    """Every raceway part, per run, in model order."""
    runs = list(model.conduits)
    # A chain joint (one raceway drawn as two runs) is a coupling, not two connectors;
    # it is billed on the feeding run.
    joints: dict[str, int] = {}
    for chain in raceway_chains([run for run in runs if run.derived is None]):
        for tag in chain[:-1]:
            joints[tag] = joints.get(tag, 0) + 1
    out: list[ConduitPart] = []
    for run in runs:
        size = round(run.trade_size_m / M_PER_IN, 2)
        for kind, count in _run_parts(run, joints.get(run.tag, 0)).items():
            out.append(ConduitPart(run.tag, kind, run.material, size, count))
    return out
