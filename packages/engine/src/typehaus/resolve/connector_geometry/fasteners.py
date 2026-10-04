"""A stock Titen HD ledger anchor, with threads simplified to its nominal shaft."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.connector_geometry.mesh import combine_meshes, plate_mesh
from typehaus.resolve.geometry_ir import GMesh, Vec3


@dataclass(frozen=True)
class LedgerAnchorDimensions:
    # Simpson C-A-2023 pp. 80–91 / THDSS product table: diameter, length and wrench size.
    diameter_in: float = 0.5
    length_in: float = 6.0
    head_across_flats_in: float = 0.75
    # Undimensioned head height is a simplified display contour.
    illustrative_head_height_in: float = 0.3125
    shaft_segments: int = 12


LEDGER_ANCHOR = LedgerAnchorDimensions()


def fastener_mesh(part: str) -> GMesh | None:
    """Head bearing face at y=0, shaft into -y, with published length below the head."""
    if part.strip().upper() not in ("THD50600H6SS", "THD50600H4SS"):
        return None
    dimensions = LEDGER_ANCHOR

    def ring(radius: float, count: int) -> tuple[Vec3, ...]:
        return tuple((radius * math.cos(2 * math.pi * i / count), 0.0,
                      radius * math.sin(2 * math.pi * i / count)) for i in range(count))

    shaft = plate_mesh(ring(dimensions.diameter_in / 2, dimensions.shaft_segments),
                       (0.0, -dimensions.length_in, 0.0))
    hex_radius = dimensions.head_across_flats_in / math.sqrt(3)
    head = plate_mesh(ring(hex_radius, 6),
                      (0.0, dimensions.illustrative_head_height_in, 0.0))
    return combine_meshes(shaft, head)
