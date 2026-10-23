"""Catalog dimensions shared by connector placement and body geometry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LateralTiePlateDimensions:
    """LTP4 envelope, matching the C-C-2026 drawing used by the body builder."""

    width_in: float = 3.0
    height_in: float = 4.25


LATERAL_TIE_PLATE_DIMENSIONS = LateralTiePlateDimensions()
