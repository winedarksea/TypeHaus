"""Receptacle face dimensions. Inches are nominal at a Decora 1.31" x 2.63" face; a builder
scales them uniformly to the type's face so a face never leaves its envelope."""

from dataclasses import dataclass

INCH = 0.0254


@dataclass(frozen=True)
class ReceptacleGeometryConfig:
    face_width_in: float = 1.31
    face_height_in: float = 2.63
    socket_width_in: float = 1.0
    socket_height_in: float = 1.0
    socket_corner_fraction: float = 0.24
    duplex_row_pitch_in: float = 1.32
    gfci_socket_height_in: float = 0.8
    gfci_row_pitch_in: float = 1.76
    gfci_button_width_in: float = 0.40
    gfci_button_height_in: float = 0.34
    gfci_button_pitch_in: float = 0.54
    blank_gfci_button_width_in: float = 0.80
    blank_gfci_button_height_in: float = 0.50
    blank_gfci_button_pitch_in: float = 0.80
    round_diameter_in: float = 2.5
    round_segments: int = 32
    # Depth shares of the projection, past the slab: socket boss, then the slot marks.
    socket_depth_fraction: float = 0.45
    mark_depth_fraction: float = 0.05
    round_mark_depth_fraction: float = 0.04
    floor_blade_spacing_fraction: float = 0.08
    floor_blade_width_fraction: float = 0.025
    floor_blade_length_fraction: float = 0.075
    floor_ground_size_fraction: float = 0.035
    floor_socket_offset_fraction: float = 0.16
    maximum_parts: int = 24
    maximum_triangles: int = 600


RECEPTACLE_GEOMETRY = ReceptacleGeometryConfig()

# Slot boxes (dx, dz, width, height) in inches from a socket's centre; grounds are an arch
# (dx, dz, width, height) beneath the blades.
SLOT_LAYOUTS: dict[str, tuple[tuple[float, float, float, float], ...]] = {
    "120": ((-0.25, 0.12, 0.07, 0.30), (0.25, 0.12, 0.07, 0.30)),
    "120-20": ((-0.25, 0.12, 0.07, 0.30), (0.25, 0.12, 0.07, 0.30),
               (-0.315, 0.12, 0.20, 0.07)),  # the T arm of the 5-20R neutral
    "240": ((-0.25, 0.12, 0.07, 0.30), (0.25, 0.12, 0.30, 0.07)),
    "240-four-wire": ((-0.25, 0.0, 0.07, 0.30), (0.25, 0.0, 0.07, 0.30),
                      (0.0, 0.30, 0.07, 0.30)),
    "round-30": ((-0.50, 0.15, 0.10, 0.40), (0.50, 0.15, 0.10, 0.40),
                 (0.0, -0.10, 0.40, 0.10)),
    "round-50": ((-0.55, 0.0, 0.12, 0.55), (0.55, 0.0, 0.12, 0.55),
                 (0.0, 0.55, 0.12, 0.45)),
}
GROUND_LAYOUTS: dict[str, tuple[float, float, float, float]] = {
    "120": (0.0, -0.22, 0.15, 0.17),
    "120-20": (0.0, -0.22, 0.15, 0.17),
    "240": (0.0, -0.22, 0.15, 0.17),
    "240-four-wire": (0.0, -0.25, 0.15, 0.17),
    "round-30": (0.0, -0.55, 0.20, 0.22),
    "round-50": (0.0, -0.55, 0.22, 0.24),
}
