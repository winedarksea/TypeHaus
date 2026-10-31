"""Exact 3D overlap between elements: the true-solid clash audit the 2.5D checks cannot do.

Each element is unioned into one solid; an STRtree over plan boxes, a z test and the summed
overlap of its solids' boxes find the candidate pairs; the intersection volume is exact.
Most overlaps are by design (a connector in its wall, trim lapping a face), so the useful
reading is a ratchet over kind pairs, not a verdict. A host and its own ``::framing``
element are never paired: studs filling their own cavity layer are the assembly, and that
one pair would outweigh every real clash in the ratchet.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely import STRtree, box

from typehaus.resolve.geometry_ir import GeometryModel
from typehaus.solids3d.convert import to_manifold, union

#: Below this an intersection is coincident faces and float noise, not a clash.
MIN_OVERLAP_M3 = 1e-6


@dataclass(frozen=True)
class Overlap:
    uid_a: str
    uid_b: str
    kind_a: str
    kind_b: str
    volume_m3: float


def overlap_pairs(geometry: GeometryModel, min_volume_m3: float = MIN_OVERLAP_M3,
                  ) -> list[Overlap]:
    """Every element pair whose solids share more than ``min_volume_m3``, kinds sorted."""
    elements, parts, boxes = [], [], []
    for element in sorted(geometry.elements, key=lambda item: item.uid):
        solids = [solid for solid in (to_manifold(item) for part in element.parts
                                      for item in part.solids) if not solid.is_empty()]
        if solids:
            elements.append(element)
            parts.append(solids)
            boxes.append(np.array([solid.bounding_box() for solid in solids]))
    hulls = np.array([[*b[:, :3].min(axis=0), *b[:, 3:].max(axis=0)] for b in boxes])
    tree = STRtree([box(h[0], h[1], h[3], h[4]) for h in hulls])
    left, right = tree.query(tree.geometries, predicate="intersects")
    unions: dict[int, object] = {}
    found: list[Overlap] = []
    for i, j in zip(left.tolist(), right.tolist(), strict=True):
        a, b = elements[i], elements[j]
        if i >= j or a.uid + "::framing" == b.uid or b.uid + "::framing" == a.uid:
            continue
        if (_box_overlap(hulls[i:i + 1], hulls[j:j + 1]) <= min_volume_m3
                or _box_overlap(boxes[i], boxes[j]) <= min_volume_m3):
            continue  # an intersection never exceeds its boxes' overlap
        for index in (i, j):
            if index not in unions:
                unions[index] = union(parts[index])
        volume = (unions[i] ^ unions[j]).volume()
        if volume <= min_volume_m3:
            continue
        if (a.kind, a.uid) > (b.kind, b.uid):
            a, b = b, a
        found.append(Overlap(a.uid, b.uid, a.kind, b.kind, volume))
    return sorted(found, key=lambda item: (item.kind_a, item.kind_b, item.uid_a, item.uid_b))


def overlaps(geometry: GeometryModel, min_volume_m3: float = MIN_OVERLAP_M3,
             ) -> dict[tuple[str, str], tuple[int, float]]:
    """``(kind_a, kind_b) -> (pair count, total overlap m^3)``, for a ratchet golden."""
    totals: dict[tuple[str, str], tuple[int, float]] = {}
    for item in overlap_pairs(geometry, min_volume_m3):
        count, volume = totals.get((item.kind_a, item.kind_b), (0, 0.0))
        totals[(item.kind_a, item.kind_b)] = (count + 1, volume + item.volume_m3)
    return totals


def _box_overlap(first: np.ndarray, second: np.ndarray) -> float:
    """Summed overlap volume of every box in ``first`` with every box in ``second``."""
    low = np.maximum(first[:, None, :3], second[None, :, :3])
    high = np.minimum(first[:, None, 3:], second[None, :, 3:])
    return float(np.prod(np.clip(high - low, 0.0, None), axis=2).sum())
