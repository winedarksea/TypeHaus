"""Movable furniture as separate, to-scale pieces, each graded for an easy print.

Never thickened: a chair is printed true or not at all. A piece passes when it is a valid
solid, its smallest drawn feature (read exactly off the recorder's primitives, not measured
off the mesh) is at least ``min_feature_mm``, it stands on at least ``MIN_BASE_SHARE`` of its
own footprint, it is no taller than ``MAX_SLENDERNESS`` base widths, and it needs little
support. Like a storey, a piece is tried upright and then upside down, so a table stands on
its top. Thin plates are fused into their base first (``plates.py``). At 1:128 most chairs
still fail on their legs, and the report says so.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from typehaus.print3d.collect import PrintItem
from typehaus.print3d.pieces import Piece, support_area_mm2
from typehaus.print3d.policy import PrintSettings
from typehaus.solids3d import require_manifold3d

MIN_BASE_SHARE = 0.30
MAX_SLENDERNESS = 4.0
#: Support area allowed, as a share of the footprint.
MAX_SUPPORT_SHARE = 0.25


@dataclass(frozen=True)
class Rejection:
    tag: str
    reason: str


def furniture_pieces(items: list[PrintItem], mm_per_m: float, settings: PrintSettings,
                     ) -> tuple[list[Piece], list[Rejection]]:
    m3d = require_manifold3d()
    pieces: list[Piece] = []
    rejected: list[Rejection] = []
    for item in items:
        reason = _grade_solid(m3d, item, mm_per_m, settings)
        orientation = None
        if reason is None:
            solid = item.solid.scale((mm_per_m, mm_per_m, mm_per_m))
            graded = [(label, candidate, _grade_stance(candidate)) for label, candidate in
                      (("upright", solid), ("flipped", solid.rotate((180.0, 0.0, 0.0))))]
            passing = [(label, candidate) for label, candidate, why in graded if why is None]
            reason = None if passing else graded[0][2]
            orientation, solid = passing[0] if passing else (None, None)
        if reason is not None:
            rejected.append(Rejection(item.tag, reason))
            continue
        x0, y0, z0, x1, y1, z1 = solid.bounding_box()
        rested = solid.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, -z0))
        pieces.append(Piece(item.tag, rested, (x1 - x0, y1 - y0, z1 - z0),
                            support_area_mm2(rested), orientation))
    return pieces, rejected


def _grade_solid(m3d, item: PrintItem, mm_per_m: float, settings: PrintSettings) -> str | None:
    if item.solid.status() != m3d.Error.NoError or item.solid.volume() <= 0:
        return "not a closed solid"
    thinnest = min((p.min_feature_m for p in item.primitives), default=0.0) * mm_per_m
    if thinnest < settings.feature_mm:
        return f"smallest feature {thinnest:.2f} mm < {settings.feature_mm:.2f} mm"
    return None


def _grade_stance(solid) -> str | None:
    """Why ``solid`` (print mm, as it would sit on the bed) is not an easy print, or None."""
    footprint = solid.project()
    footprint_area = footprint.area()
    base_area, base_width = _base(solid)
    if footprint_area <= 0 or base_area < MIN_BASE_SHARE * footprint_area:
        return f"base contact {base_area / max(footprint_area, 1e-9):.0%} of footprint"
    height = solid.bounding_box()[5] - solid.bounding_box()[2]
    if base_width <= 0 or height / base_width > MAX_SLENDERNESS:
        return f"height {height:.1f} mm is over {MAX_SLENDERNESS:g}x its base width"
    support = support_area_mm2(solid)
    if support > MAX_SUPPORT_SHARE * footprint_area:
        return f"needs {support:.0f} mm^2 of support"
    return None


def _base(solid) -> tuple[float, float]:
    """Area and least width of what the piece stands on (faces at its lowest z)."""
    from shapely.geometry import MultiPoint

    mesh = solid.to_mesh()
    points = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
    tris = np.asarray(mesh.tri_verts, dtype=int)
    floor = points[:, 2].min()
    on_floor = (points[tris][:, :, 2] <= floor + 1e-3).all(axis=1)
    flat = tris[on_floor]
    if not len(flat):
        return 0.0, 0.0
    a, b, c = (points[flat[:, k]] for k in range(3))
    area = float(np.abs(np.cross(b - a, c - a)[:, 2]).sum() / 2)
    with np.errstate(divide="ignore", invalid="ignore"):  # a base of collinear points
        hull = MultiPoint([tuple(p[:2]) for p in points[np.unique(flat)]]
                          ).minimum_rotated_rectangle
    if hull.geom_type != "Polygon":
        return area, 0.0
    corners = list(hull.exterior.coords)[:3]
    sides = [float(np.hypot(corners[i + 1][0] - corners[i][0], corners[i + 1][1] - corners[i][1]))
             for i in range(2)]
    return area, min(sides)
