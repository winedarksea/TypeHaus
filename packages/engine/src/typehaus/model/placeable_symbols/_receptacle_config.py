"""Schematic receptacle relief, independent of the installation's housing depth."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReceptacleGeometryConfig:
    plate_depth_fraction: float = 0.08
    maximum_plate_depth_m: float = 0.004
    socket_depth_fraction: float = 0.04
    maximum_socket_depth_m: float = 0.002
    mark_depth_fraction: float = 0.01
    maximum_mark_depth_m: float = 0.0005
    plate_width_fraction: float = 0.96
    plate_height_fraction: float = 0.98
    plate_corner_fraction: float = 0.08
    socket_corner_fraction: float = 0.24
    socket_width_fraction: float = 0.64
    quad_socket_width_fraction: float = 0.36
    socket_height_fraction: float = 0.26
    single_socket_height_fraction: float = 0.52
    quad_column_offset_fraction: float = 0.23
    blade_spacing_fraction: float = 0.19
    blade_width_fraction: float = 0.055
    blade_height_fraction: float = 0.27
    ground_width_fraction: float = 0.16
    ground_height_fraction: float = 0.17
    ground_offset_fraction: float = 0.28
    neutral_offset_fraction: float = 0.30
    floor_plate_height_fraction: float = 0.04
    floor_maximum_plate_height_m: float = 0.005
    floor_mark_height_fraction: float = 0.01
    floor_maximum_mark_height_m: float = 0.001
    floor_body_fraction: float = 0.65
    floor_socket_offset_fraction: float = 0.16
    floor_blade_spacing_fraction: float = 0.08
    floor_blade_width_fraction: float = 0.025
    floor_blade_length_fraction: float = 0.075
    floor_ground_size_fraction: float = 0.035
    maximum_parts: int = 24
    maximum_triangles: int = 600


RECEPTACLE_GEOMETRY = ReceptacleGeometryConfig()
