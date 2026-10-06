"""Flat diaphragm straps follow a roof surface, rather than folding over its peak lengthwise."""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes, plate_mesh
from typehaus.resolve.connector_geometry.ties import STEEL_THICKNESS_IN, STRAPS
from typehaus.resolve.geometry_ir import GMesh, Vec2
from typehaus.resolve.model import ResolvedRoof
from typehaus.resolve.roof_geometry import (
    roof_plane_z,
    roof_ridge_coordinate,
    roof_slope_coordinate,
    roof_slope_factor,
)


def roof_strap_mesh(roof: ResolvedRoof, point: Vec2, part: str) -> GMesh:
    """Seat a stock strap directly beneath the deck, preserving developed width and length.

    Length runs parallel to the ridge. A strap on the ridge folds across its WIDTH;
    splitting that face prevents the centre strap from cutting through the top chords.
    This geometry establishes a mounting plane, never an installed nailing capacity.
    """
    dimensions = STRAPS[part.upper().removesuffix("Z")]
    factor = roof_slope_factor(roof)
    centre = roof_slope_coordinate(roof, point)
    half_width = dimensions.width_in * M_PER_IN / (2 * factor)
    half_length = dimensions.length_in * M_PER_IN / 2
    stations = [centre - half_width, centre + half_width]
    ridge = roof_ridge_coordinate(roof)
    if ridge is not None and stations[0] < ridge < stations[1]:
        stations.insert(1, ridge)
    thickness = STEEL_THICKNESS_IN[dimensions.gauge]
    along = point[0] if roof.ridge_direction == "x" else point[1]

    def vertex(across: float, run: float) -> tuple[float, float, float]:
        xy = (run, across) if roof.ridge_direction == "x" else (across, run)
        return xy[0] / M_PER_IN, xy[1] / M_PER_IN, roof_plane_z(roof, across) / M_PER_IN

    leaves = []
    for low, high in zip(stations, stations[1:], strict=False):
        pitch = (roof_plane_z(roof, high) - roof_plane_z(roof, low)) / (high - low)
        normal_factor = math.hypot(1.0, pitch)
        across_normal = -pitch * thickness / normal_factor
        extrusion = ((0.0, across_normal, thickness / normal_factor)
                     if roof.ridge_direction == "x"
                     else (across_normal, 0.0, thickness / normal_factor))
        leaves.append(plate_mesh((vertex(low, along - half_length),
                                  vertex(high, along - half_length),
                                  vertex(high, along + half_length),
                                  vertex(low, along + half_length)), extrusion))
    return combine_meshes(*leaves)
