"""A wrapped duct's insulation as a solid: the OD every clearance check already measures.

``mep_envelopes.run_radii`` and ``framing_envelope`` grade a wrapped run at its insulated
outside size, while the swept solid was the bare bore — so 3D, glTF and sections drew a duct
an inch thinner a side than the one the checks cleared. This sweeps the wrap as its own solid.

**The wrap stops at the sheathing.** A leg that leaves through a wall rough opening naming it
in ``penetration_for`` is foamed bare through the sheathing and everything outboard (catlin's
ERV hood legs), so the wrap's path is clipped at the room-side face of that wall's sheathing.
One plane per opening; nothing per segment.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel

Point3 = tuple[float, float, float]


def _sheathing_plane(model: ResolvedModel, wall_tag: str
                     ) -> tuple[tuple[float, float], tuple[float, float], float] | None:
    """``(origin, outward unit normal, offset)``: a point is outboard when ``f > 0``.

    ``f(p) = (p - origin) . normal - offset`` is zero on the sheathing's room-side face.
    Sides come off each layer's centroid along the wall normal, as
    ``mep_sleeves._framed_envelope_band`` reads them, so layer order does not matter.
    """
    from shapely.geometry import Polygon

    wall = model.wall(wall_tag)
    if wall is None or len(wall.axis) < 2:
        return None
    sheathing = next((ly for ly in wall.layers if ly.function == "sheathing"), None)
    structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
    if sheathing is None or structure is None or len(sheathing.polygon) < 3:
        return None
    (x0, y0), (x1, y1) = wall.axis[0], wall.axis[-1]
    norm = math.hypot(x1 - x0, y1 - y0)
    if norm < 1e-9:
        return None
    nx, ny = -(y1 - y0) / norm, (x1 - x0) / norm

    def along(point) -> float:
        return (point[0] - x0) * nx + (point[1] - y0) * ny

    sheath = Polygon(sheathing.polygon)
    if along(sheath.centroid.coords[0]) < along(Polygon(structure.polygon).centroid.coords[0]):
        nx, ny = -nx, -ny  # outboard is the sheathing's side of the studs
    inner = min((x - x0) * nx + (y - y0) * ny for x, y in sheath.exterior.coords)
    return (x0, y0), (nx, ny), inner


def _clip(points: list[Point3], plane) -> list[Point3]:
    """The run up to the first time it crosses outboard of ``plane``."""
    (ox, oy), (nx, ny), offset = plane

    def f(p: Point3) -> float:
        return (p[0] - ox) * nx + (p[1] - oy) * ny - offset

    if not points or f(points[0]) > 0 and f(points[-1]) > 0:
        return points
    # Walk from the inboard end so the kept piece is the one in the house.
    ordered = points if f(points[0]) <= 0 else list(reversed(points))
    kept = [ordered[0]]
    for p, q in zip(ordered, ordered[1:], strict=False):
        fp, fq = f(p), f(q)
        if fq <= 0:
            kept.append(q)
            continue
        t = fp / (fp - fq) if abs(fp - fq) > 1e-12 else 0.0
        kept.append(tuple(a + (b - a) * t for a, b in zip(p, q, strict=False)))
        break
    return kept


def wrap_path(model: ResolvedModel, duct_tag: str, points: list[Point3]) -> list[Point3]:
    """``points`` clipped at the sheathing of every wall whose rough opening names the run."""
    for opening in model.openings:
        if duct_tag not in (opening.penetration_for or ()):
            continue
        plane = _sheathing_plane(model, opening.host_wall)
        if plane is not None:
            points = _clip(points, plane)
    return points
