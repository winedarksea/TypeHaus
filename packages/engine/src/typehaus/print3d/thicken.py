"""Thicken an element in its own frame until a printer can lay it down.

Per element, never per primitive: a five-layer wall thickened layer by layer would grow
fivefold. Each element is one affine transform, so nothing is remeshed. A wall scales across
its axis and grows by the same absolute amount along it, which closes the notch an outside
corner would open; a floor, ceiling or slab scales along z; a roof along its own normal; and
anything else along its thinnest axis, about its centre. Past ``max_thicken`` an element is
dropped rather than distorted, and the report says so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from typehaus.print3d.collect import PrintItem
from typehaus.print3d.policy import PrintSettings, Treatment

_ALONG_Z = frozenset({"floor", "ceiling", "slab", "slab_band", "slab_platform",
                      "slab_finish", "countertop", "pad", "site"})


@dataclass(frozen=True)
class Thickness:
    """What happened to one item: its thin dimension in print mm and the factor applied."""

    item: PrintItem
    thin_mm: float
    factor: float  # 1.0 untouched; 0.0 dropped
    solid: object | None


def thicken(item: PrintItem, mm_per_m: float, settings: PrintSettings) -> Thickness:
    if item.treatment is Treatment.LOOSE:
        return Thickness(item, 0.0, 1.0, item.solid)
    target = settings.wall_mm if item.treatment is Treatment.BODY else settings.feature_mm
    origin, axes = _frame(item)
    vertices = np.asarray(item.solid.to_mesh().vert_properties, dtype=float)[:, :3]
    local = (vertices - origin) @ axes.T
    low, high = local.min(axis=0), local.max(axis=0)
    extents = high - low
    thin_axis = 1 if item.axis is not None else 2 if item.kind in _ALONG_Z or _is_roof(
        item) else int(np.argmin(extents))
    thin_mm = float(extents[thin_axis]) * mm_per_m
    if thin_mm >= target:
        return Thickness(item, thin_mm, 1.0, item.solid)
    factor = target / max(thin_mm, 1e-9)
    if item.treatment is Treatment.TRIM or factor > settings.max_thicken:
        return Thickness(item, thin_mm, 0.0, None)
    scale = np.ones(3)
    scale[thin_axis] = factor
    if item.axis is not None and extents[0] > 0:  # grow along by the same absolute amount
        scale[0] = 1 + (factor - 1) * extents[thin_axis] / extents[0]
    centre = origin + ((low + high) / 2) @ axes
    linear = axes.T @ np.diag(scale) @ axes
    offset = centre - linear @ centre
    matrix = np.hstack([linear, offset[:, None]])
    return Thickness(item, thin_mm, factor, item.solid.transform(matrix.tolist()))


def _frame(item: PrintItem) -> tuple[np.ndarray, np.ndarray]:
    """Origin and orthonormal rows (along, across, normal) of the item's own frame."""
    if item.axis is not None:
        (x0, y0), (x1, y1) = item.axis
        length = math.hypot(x1 - x0, y1 - y0) or 1.0
        along = np.array([(x1 - x0) / length, (y1 - y0) / length, 0.0])
        return np.array([x0, y0, 0.0]), np.array([along, [-along[1], along[0], 0.0],
                                                  [0.0, 0.0, 1.0]])
    if _is_roof(item):
        normal = _dominant_up_normal(item.solid)
        helper = np.array([1.0, 0.0, 0.0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
        first = np.cross(normal, helper)
        first /= np.linalg.norm(first)
        return np.zeros(3), np.array([first, np.cross(normal, first), normal])
    return np.zeros(3), np.eye(3)


def _is_roof(item: PrintItem) -> bool:
    return item.kind == "roof"


def _dominant_up_normal(solid) -> np.ndarray:
    """The area-weighted normal of a roof's upward faces: its slope, for a single plane."""
    mesh = solid.to_mesh()
    points = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
    tris = np.asarray(mesh.tri_verts, dtype=int)
    first = points[tris[:, 0]]
    cross = np.cross(points[tris[:, 1]] - first, points[tris[:, 2]] - first)
    up = cross[cross[:, 2] > 0].sum(axis=0)
    norm = np.linalg.norm(up)
    return up / norm if norm > 0 else np.array([0.0, 0.0, 1.0])
