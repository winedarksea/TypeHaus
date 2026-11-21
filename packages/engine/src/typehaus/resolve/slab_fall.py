"""A falling pour's plane (decision #138, ``model/slab_fall.SlabFall``).

Leaf and pure: everything here reads the AUTHORED slab (or the resolved solid's carried
plane), so the stair resolver can seat a foot on the floor without waiting for it. The
plane lifts top and bottom together (constant thickness); ``Slab.top_elevation`` is the top
at the low edge, where the lift is zero.

Float math only (Pyodide-safe).
"""

from __future__ import annotations

from typing import Any

from typehaus.model.floors import Slab
from typehaus.quantities import M_PER_IN
from typehaus.resolve.floor_tilt import DeckPlane
from typehaus.resolve.geometry_ir import GMesh

_M_PER_FT = 0.3048
#: The uphill direction, a unit vector: a slab falling north rises toward the south.
_UPHILL = {"north": (0.0, -1.0), "south": (0.0, 1.0), "east": (-1.0, 0.0), "west": (1.0, 0.0)}
_COLLINEAR_M = 1e-9


def fall_plane(slab: Any) -> DeckPlane | None:
    """The lift above ``top_elevation`` as a plane, zero along the low edge; else None."""
    fall = getattr(slab, "fall", None)
    if fall is None:
        return None
    ux, uy = _UPHILL[fall.toward]
    slope = fall.rate_in_per_ft * M_PER_IN / _M_PER_FT
    edge = fall.low_edge.meters
    origin = (0.0, edge) if fall.toward in ("north", "south") else (edge, 0.0)
    return DeckPlane(origin=origin, lift_at_origin_m=0.0, gradient=(ux * slope, uy * slope))


def slab_top_at(slab: Slab, x: float, y: float) -> float:
    """Top of ``slab`` at plan ``(x, y)``: its low-edge top plus the fall's lift."""
    plane = fall_plane(slab)
    top = slab.top_elevation.meters if slab.top_elevation is not None else 0.0
    return top + (plane.lift(x, y) if plane is not None else 0.0)


def sloped_slab_mesh(solid: Any) -> GMesh:
    """The solid's plan ring with its top on the plane, extruded straight down its thickness.

    Every emitter draws a falling pour from this one mesh (IR, glTF, IFC), so they agree.
    A void would need a hole in the caps: refused rather than drawn wrong.
    """
    from typehaus.resolve.connector_geometry.mesh import _triangulate

    if solid.voids:
        raise ValueError(f"{solid.tag}: a falling slab cannot carry voids yet")
    ring = _without_collinear([tuple(p) for p in solid.outline])
    if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1], strict=True)) < 0:
        ring = ring[::-1]  # counter-clockwise in plan, so the top faces up
    thickness = solid.z1_m - solid.z0_m
    count = len(ring)
    top = [(x, y, solid.top_at(x, y)) for x, y in ring]
    positions = tuple(top) + tuple((x, y, z - thickness) for x, y, z in top)
    cx, cy = (sum(p[i] for p in ring) / count for i in (0, 1))
    cap = _triangulate(tuple((x - cx, y - cy, 0.0) for x, y in ring), (0.0, 0.0, 1.0))
    triangles = list(cap) + [(a + count, c + count, b + count) for a, b, c in cap]
    for a in range(count):
        b = (a + 1) % count
        triangles.extend(((a, b + count, b), (a, a + count, b + count)))
    return GMesh(positions=positions, triangles=tuple(triangles))


def solid_mesh(solid: Any) -> GMesh | None:
    """A solid's own mesh: its ``body_mesh``, a falling pour's plane mesh, a dish piece's
    fan (``resolve/slab_dish.py``), else None."""
    if solid.body_mesh is not None:
        return solid.body_mesh
    if getattr(solid, "dish", None) is not None:
        from typehaus.resolve.slab_dish import dish_mesh

        return dish_mesh(solid)
    return sloped_slab_mesh(solid) if solid.top_plane is not None else None


def _without_collinear(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Drop repeated and collinear vertices, which ear clipping cannot take as ears."""
    out = [p for i, p in enumerate(ring) if p != ring[i - 1]]
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i, (bx, by) in enumerate(out):
            (ax, ay), (cx, cy) = out[i - 1], out[(i + 1) % len(out)]
            if abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) <= _COLLINEAR_M:
                out.pop(i)
                changed = True
                break
    return out
