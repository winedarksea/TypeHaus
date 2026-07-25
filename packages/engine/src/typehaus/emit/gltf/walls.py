"""Wall bodies: one prism per depth-bearing layer, jamb-split around its hosted openings and
raked to the roof slope where the wall is a gable/ToRoof wall."""

from __future__ import annotations

import math

from typehaus.emit.gltf.geometry import _slice, _thin_rect_edges
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _layer_color
from typehaus.resolve.model import ResolvedWall


def _wall_top_at(wall: ResolvedWall, x: float, y: float) -> float:
    """A raked (ToRoof/gable) wall's top elevation at a plan point, interpolated along the wall
    axis. Mirrors ui/src/components/Panel3D.tsx ``rakedTopAt``; a wall with no rake tops out flat
    at ``z1_m``."""
    if wall.top_z0_m is None and wall.top_z1_m is None:
        return wall.z1_m
    start = wall.z1_m if wall.top_z0_m is None else wall.top_z0_m
    end = wall.z1_m if wall.top_z1_m is None else wall.top_z1_m
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    len2 = dx * dx + dy * dy
    t = 0.0 if len2 < 1e-9 else min(1.0, max(0.0, ((x - x0) * dx + (y - y0) * dy) / len2))
    return start + (end - start) * t


def _emit_wall_slice(mb, ring, z0, z1, color, top_at) -> None:
    """A solid wall slice (pier / full layer): raked to ``top_at`` when the wall is raked, else a
    flat prism to ``z1``."""
    if top_at is not None:
        mb.add_raked_prism(ring, z0, top_at, color)
    else:
        mb.add_prism(ring, z0, z1, color)


def _add_wall_body(mb: _MeshBuilder, wall: ResolvedWall, lod: str, openings=()) -> None:
    """Draw a wall's selectable body (its depth-layer prisms). Framing members are emitted as a
    separate ``framing`` node by the caller, so the framed LOD leaves the body empty and lets the
    stud model stand on its own."""
    if lod == "framed" and wall.members:
        return
    # Core LOD draws one prism per depth-bearing layer, carved around any hosted openings so
    # windows/doors read as voids and the arched front wall reads as piers + an arched head.
    # Cavity fill shares the structure layer's polygon, so extruding it too would only z-fight.
    # A gable/ToRoof wall rakes its top to the roof slope; ``top_at`` interpolates that top per
    # plan point (None for ordinary flat walls). Piers and the square header follow the rake;
    # the sill band stays flat under the opening (mirrors wallLayerPieces' topIsRaked rules).
    raked = wall.top_z0_m is not None or wall.top_z1_m is not None
    top_at = (lambda x, y: _wall_top_at(wall, x, y)) if raked else None
    ops = sorted(openings, key=lambda o: o.center_along_m)
    length = math.hypot(wall.axis[1][0] - wall.axis[0][0],
                        wall.axis[1][1] - wall.axis[0][1]) or 1.0
    for layer in wall.depth_layers():
        if not layer.polygon:
            continue
        color = _layer_color(layer)
        if not ops:
            _emit_wall_slice(mb, layer.polygon, wall.z0_m, wall.z1_m, color, top_at)
            continue
        _add_layer_with_openings(mb, layer.polygon, wall.axis, wall.z0_m, wall.z1_m,
                                 length, ops, color, top_at)


def _add_layer_with_openings(mb, poly, axis, z0, z1, length, ops, color, top_at=None) -> None:
    edges = _thin_rect_edges(poly, axis)
    cursor = 0.0
    for op in ops:
        o0 = max(0.0, (op.center_along_m - op.width_m / 2) / length)
        o1 = min(1.0, (op.center_along_m + op.width_m / 2) / length)
        if o1 <= o0:
            continue
        if o0 > cursor + 1e-6:  # solid pier before this opening
            _emit_wall_slice(mb, _slice(edges, cursor, o0), z0, z1, color, top_at)
        bottom = min(z0 + op.sill_m, z1)
        head = min(bottom + op.height_m, z1)
        if bottom > z0 + 1e-6:  # sill band under the opening — always flat, below the rake
            mb.add_prism(_slice(edges, o0, o1), z0, bottom, color)
        if op.arch_rise_m > 1e-6:  # spandrel above a semicircular/segmental arch soffit
            # v1: arch heads stay flat-topped even under a rake (a rare combination); the
            # raked square header below handles the common gable-end window/door case.
            springline = bottom + max(0.0, op.height_m - op.arch_rise_m)
            radius = op.width_m / 2.0
            if z1 > springline + 1e-6:
                mb.add_arched_spandrel(edges, o0, o1, z1, springline, radius, color)
        else:  # square-head header, raked to the roof slope where the wall is raked
            header = _slice(edges, o0, o1)
            if top_at is not None:
                # Only emit when the whole strip's raked top clears the opening head, or the
                # header would invert (mirrors wallLayerPieces minTop > openingTop).
                if min(top_at(px, py) for (px, py) in header) > head + 1e-6:
                    mb.add_raked_prism(header, head, top_at, color)
            elif z1 > head + 1e-6:
                mb.add_prism(header, head, z1, color)
        cursor = max(cursor, o1)
    if cursor < 1.0 - 1e-6:  # trailing pier
        _emit_wall_slice(mb, _slice(edges, cursor, 1.0), z0, z1, color, top_at)
