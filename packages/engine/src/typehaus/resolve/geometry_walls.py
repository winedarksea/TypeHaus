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

from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_ir import GMesh, GPrism, GSolid, Vec3
from typehaus.resolve.geometry_prims import (
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    _lerp,
    arch_soffit_circle,
    _slice,
    _thin_rect_edges,
)
from typehaus.resolve.intervals import subtract as _subtract_spans
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
                        springline: float, half_span: float, rise: float) -> GMesh:
    """One continuous curved head, not a stack of prism strips.

    The soffit is a cylinder about a horizontal axis through the springlines, so each sample
    carries the analytic surface normal and is marked curved. A sample clipped by the wall top
    no longer sits on that circle, so it is not marked, and the facets touching it fall back to
    their geometric normal.
    """
    radius, half_angle, depth = arch_soffit_circle(half_span, rise)
    segment_count = _arch_soffit_segment_count(radius, half_angle)
    (edge_start, edge_end) = edges[0]
    run = math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1]) or 1.0
    ux, uy = (edge_end[0] - edge_start[0]) / run, (edge_end[1] - edge_start[1]) / run

    positions: list[Vec3] = []
    normals: list[Vec3] = []
    curved: set[int] = set()
    for segment in range(segment_count + 1):
        offset, height = _arch_soffit_sample(segment, segment_count, radius, half_angle)
        # Fractions run over the *opening*, so the divisor is the half-span, not the radius —
        # on a segmental arch the circle is wider than the hole it springs from.
        fraction = opening_start + (opening_end - opening_start) * (
            (offset + half_span) / (2.0 * half_span))
        crown = springline + height
        soffit = min(z1, crown)
        front = _lerp(edges[0][0], edges[0][1], fraction)
        back = _lerp(edges[1][0], edges[1][1], fraction)
        base = len(positions)
        positions.extend(((front[0], front[1], soffit), (back[0], back[1], soffit),
                          (front[0], front[1], z1), (back[0], back[1], z1)))
        # The outward radial direction at this sample. ``height`` is measured off the
        # springline, so the circle's centre is ``depth`` below it — zero for a semicircle,
        # which is why this read ``height / radius`` while every arch was one.
        analytic = (offset / radius * ux, offset / radius * uy, (height + depth) / radius)
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


def layer_solids(wall: ResolvedWall, polygon, openings,
                 band: tuple[float, float] | None = None) -> tuple[GSolid, ...]:
    """Every solid one depth-bearing layer of ``wall`` contributes.

    ``band`` is the layer's own absolute (z0, z1) when its assembly gives it one
    (``Layer.extent`` — a protection panel above grade, a splash course at the base);
    ``None`` means the layer runs the wall's full height, which is what every layer did
    before banding existed. Every renderer and exporter of a wall body comes through here,
    so clamping in this one function is what makes a banded layer real in glTF, in IFC and
    in ``geometry_build`` at once.

    A raked top still wins over the band's top: the band says how far up the layer *wants*
    to run, and a gable rake is where the wall itself stops.
    """
    top_at = (lambda x, y: wall_top_at(wall, x, y)) if is_raked(wall) else None
    z0, z1 = band if band is not None else (wall.z0_m, wall.z1_m)
    if z1 - z0 <= 1e-9:
        return ()
    if top_at is not None and band is not None:
        # A rake and a band both cap this layer, and the lower of the two wins. Clamping to
        # the band's floor as well keeps a rake that has already fallen past it — the far
        # end of a gable wall, under a band that starts partway up — from inverting the
        # prism instead of producing nothing.
        top_at = lambda x, y, _rake=top_at, _floor=z0: max(min(_rake(x, y), z1), _floor)  # noqa: E731
    ops = sorted(openings, key=lambda o: o.center_along_m)
    if not ops:
        return (_prism(polygon, z0, z1, top_at),)

    _origin, _tangent, _normal, axis_length = wall_frame(wall)
    length = axis_length or 1.0
    edges = _thin_rect_edges(polygon, wall.axis)

    # The piers are the [0, 1]-fraction band not claimed by any opening's cutout — a gap
    # computation, the same one ``framing/furring.py`` runs per station (→
    # ``resolve/intervals.py``). Computed as one pass up front rather than threaded through
    # the per-opening loop below, which only emits each pier at the point it falls due
    # (immediately before the next opening it precedes, or trailing after the last one) so
    # the solids come out in the same left-to-right order the wall draws in.
    valid_ops: list[tuple[object, float, float]] = []
    cuts: list[tuple[float, float]] = []
    for op in ops:
        o0 = max(0.0, (op.center_along_m - op.width_m / 2) / length)
        o1 = min(1.0, (op.center_along_m + op.width_m / 2) / length)
        if o1 <= o0:
            continue
        valid_ops.append((op, o0, o1))
        cuts.append((o0, o1))
    piers = _subtract_spans(0.0, 1.0, cuts)

    solids: list[GSolid] = []
    pier_index = 0
    for op, o0, o1 in valid_ops:
        while pier_index < len(piers) and piers[pier_index][1] <= o0 + 1e-6:
            solids.append(_prism(_slice(edges, *piers[pier_index]), z0, z1, top_at))
            pier_index += 1
        # Openings are positioned from the *wall* base — a sill height is a property of the
        # wall, not of whichever layer happens to be in front of it — then clipped into this
        # layer's band, which is what makes a band that misses an opening entirely simply
        # not cut for it.
        raw_bottom = wall.z0_m + op.sill_m
        bottom = min(max(raw_bottom, z0), z1)
        head = min(max(raw_bottom + op.height_m, z0), z1)
        if bottom > z0 + 1e-6:  # sill band — always flat, below the rake
            solids.append(GPrism(ring=tuple(_slice(edges, o0, o1)), z0_m=z0, z1_m=bottom))
        if op.arch_rise_m > 1e-6:
            # v1: arch heads stay flat-topped even under a rake (a rare combination); the
            # raked square header below handles the common gable-end case.
            springline = raw_bottom + max(0.0, op.height_m - op.arch_rise_m)
            if z1 > springline + 1e-6:
                solids.append(_arch_spandrel_mesh(edges, o0, o1, z1, springline,
                                                  op.width_m / 2.0, op.arch_rise_m))
        else:
            header = _slice(edges, o0, o1)
            if top_at is not None:
                # Only emit when the whole strip's raked top clears the opening head, or the
                # header would invert.
                if min(top_at(px, py) for (px, py) in header) > head + 1e-6:
                    solids.append(_prism(header, head, z1, top_at))
            elif z1 > head + 1e-6:
                solids.append(GPrism(ring=tuple(header), z0_m=head, z1_m=z1))
    while pier_index < len(piers):  # trailing pier(s)
        solids.append(_prism(_slice(edges, *piers[pier_index]), z0, z1, top_at))
        pier_index += 1
    return tuple(solids)
