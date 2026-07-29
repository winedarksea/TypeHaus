"""Wall bodies as IR solids: one prism per depth-bearing layer, jamb-split around openings.

Moved verbatim (in behaviour, not in shape of code) out of ``emit/gltf/walls.py``, which was
one of the four places this math lived. The rules it encodes are load-bearing and easy to get
subtly wrong, so they are stated once here:

* one solid per **depth-bearing** layer — cavity fill shares the structure layer's polygon, so
  extruding it too would only z-fight;
* a layer hosting openings is cut into piers, a flat sill band under each opening, and a header
  over it;
* a gable/ToRoof wall **rakes**: its top follows the roof slope, interpolated per plan point.
  Piers and square headers follow the rake; the sill band stays flat under the opening;
* an arched head becomes a curved soffit carrying the cylinder's *analytic* normals, so an
  importer shades it as one curve rather than as N flat strips.

The raked top rides :attr:`GPrism.top` (per-vertex elevations) and the arch rides a
:class:`GMesh`, which is what both were added to the IR for.
"""

from __future__ import annotations

import math

from typehaus.resolve.geometry_ir import GMesh, GPrism, GSolid, Vec3
from typehaus.resolve.geometry_prims import (
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    _lerp,
    _slice,
    _thin_rect_edges,
)
from typehaus.resolve.model import ResolvedWall


def wall_top_at(wall: ResolvedWall, x: float, y: float) -> float:
    """A raked (ToRoof/gable) wall's top elevation at a plan point, along the wall axis.

    A wall with no rake tops out flat at ``z1_m``.
    """
    if wall.top_z0_m is None and wall.top_z1_m is None:
        return wall.z1_m
    start = wall.z1_m if wall.top_z0_m is None else wall.top_z0_m
    end = wall.z1_m if wall.top_z1_m is None else wall.top_z1_m
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    len2 = dx * dx + dy * dy
    t = 0.0 if len2 < 1e-9 else min(1.0, max(0.0, ((x - x0) * dx + (y - y0) * dy) / len2))
    return start + (end - start) * t


def is_raked(wall: ResolvedWall) -> bool:
    return wall.top_z0_m is not None or wall.top_z1_m is not None


def _prism(ring, z0: float, z1: float, top_at) -> GPrism:
    """A wall slice: raked to ``top_at`` when the wall is raked, else flat to ``z1``."""
    ring_t = tuple((float(x), float(y)) for x, y in ring)
    if top_at is None:
        return GPrism(ring=ring_t, z0_m=z0, z1_m=z1)
    tops = tuple(top_at(x, y) for x, y in ring_t)
    return GPrism(ring=ring_t, z0_m=z0, z1_m=max(tops), top=tops)


def _arch_spandrel_mesh(edges, opening_start: float, opening_end: float, z1: float,
                        springline: float, radius: float) -> GMesh:
    """One continuous curved head, not a stack of prism strips.

    The soffit is a cylinder about a horizontal axis through the springlines, so each sample
    carries the analytic surface normal and is marked curved. A sample clipped by the wall top
    no longer sits on that circle, so it is not marked, and the facets touching it fall back to
    their geometric normal.
    """
    segment_count = _arch_soffit_segment_count(radius)
    (edge_start, edge_end) = edges[0]
    run = math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1]) or 1.0
    ux, uy = (edge_end[0] - edge_start[0]) / run, (edge_end[1] - edge_start[1]) / run

    positions: list[Vec3] = []
    normals: list[Vec3] = []
    curved: set[int] = set()
    for segment in range(segment_count + 1):
        offset, height = _arch_soffit_sample(segment, segment_count, radius)
        fraction = opening_start + (opening_end - opening_start) * (
            (offset + radius) / (2.0 * radius))
        crown = springline + height
        soffit = min(z1, crown)
        front = _lerp(edges[0][0], edges[0][1], fraction)
        back = _lerp(edges[1][0], edges[1][1], fraction)
        base = len(positions)
        positions.extend(((front[0], front[1], soffit), (back[0], back[1], soffit),
                          (front[0], front[1], z1), (back[0], back[1], z1)))
        analytic = (offset / radius * ux, offset / radius * uy, height / radius)
        # Only the two soffit corners lie on the cylinder; the top corners are on the flat
        # top. A sample clipped by the wall top has left the circle, so it is not curved
        # either and its facets fall back to the geometric normal.
        normals.extend((analytic, analytic, (0.0, 0.0, 1.0), (0.0, 0.0, 1.0)))
        if soffit >= crown - 1e-9:
            curved.update((base, base + 1))

    triangles: list[tuple[int, int, int]] = []
    for segment in range(segment_count):
        current, next_ = segment * 4, (segment + 1) * 4
        triangles.append((current, next_ + 1, next_))            # curved soffit
        triangles.append((current, current + 1, next_ + 1))
        triangles.append((current + 2, next_ + 2, next_ + 3))    # flat top
        triangles.append((current + 2, next_ + 3, current + 3))
        triangles.append((current, next_, next_ + 2))            # wall-depth faces
        triangles.append((current, next_ + 2, current + 2))
        triangles.append((current + 1, current + 3, next_ + 3))
        triangles.append((current + 1, next_ + 3, next_ + 1))
    for section in (0, segment_count * 4):                        # jamb faces at springline
        triangles.append((section, section + 2, section + 3))
        triangles.append((section, section + 3, section + 1))

    return GMesh(positions=tuple(positions), triangles=tuple(triangles),
                 normals=tuple(normals), curved_vertices=frozenset(curved))


def layer_solids(wall: ResolvedWall, polygon, openings) -> tuple[GSolid, ...]:
    """Every solid one depth-bearing layer of ``wall`` contributes."""
    top_at = (lambda x, y: wall_top_at(wall, x, y)) if is_raked(wall) else None
    ops = sorted(openings, key=lambda o: o.center_along_m)
    if not ops:
        return (_prism(polygon, wall.z0_m, wall.z1_m, top_at),)

    length = math.hypot(wall.axis[1][0] - wall.axis[0][0],
                        wall.axis[1][1] - wall.axis[0][1]) or 1.0
    edges = _thin_rect_edges(polygon, wall.axis)
    z0, z1 = wall.z0_m, wall.z1_m
    solids: list[GSolid] = []
    cursor = 0.0
    for op in ops:
        o0 = max(0.0, (op.center_along_m - op.width_m / 2) / length)
        o1 = min(1.0, (op.center_along_m + op.width_m / 2) / length)
        if o1 <= o0:
            continue
        if o0 > cursor + 1e-6:  # solid pier before this opening
            solids.append(_prism(_slice(edges, cursor, o0), z0, z1, top_at))
        bottom = min(z0 + op.sill_m, z1)
        head = min(bottom + op.height_m, z1)
        if bottom > z0 + 1e-6:  # sill band — always flat, below the rake
            solids.append(GPrism(ring=tuple(_slice(edges, o0, o1)), z0_m=z0, z1_m=bottom))
        if op.arch_rise_m > 1e-6:
            # v1: arch heads stay flat-topped even under a rake (a rare combination); the
            # raked square header below handles the common gable-end case.
            springline = bottom + max(0.0, op.height_m - op.arch_rise_m)
            if z1 > springline + 1e-6:
                solids.append(_arch_spandrel_mesh(edges, o0, o1, z1, springline,
                                                  op.width_m / 2.0))
        else:
            header = _slice(edges, o0, o1)
            if top_at is not None:
                # Only emit when the whole strip's raked top clears the opening head, or the
                # header would invert.
                if min(top_at(px, py) for (px, py) in header) > head + 1e-6:
                    solids.append(_prism(header, head, z1, top_at))
            elif z1 > head + 1e-6:
                solids.append(GPrism(ring=tuple(header), z0_m=head, z1_m=z1))
        cursor = max(cursor, o1)
    if cursor < 1.0 - 1e-6:  # trailing pier
        solids.append(_prism(_slice(edges, cursor, 1.0), z0, z1, top_at))
    return tuple(solids)
