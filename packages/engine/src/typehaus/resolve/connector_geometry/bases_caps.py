"""Simplified Simpson bases, caps and heavy angles at their bearing/heel datums.

Dimensions are inches; shared mesh helpers convert them to metres. Base z=0 is concrete
top; cap z=0 is beam soffit; angle z=0/y=0 are the two inner bearing faces. See
``docs/simpson-base-cap-geometry.md`` for primary drawings and deliberately omitted detail.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, plate_mesh
from typehaus.resolve.geometry_ir import GMesh

# Nominal sheet steel, before coating. Gauge minima in code reports are manufacturing
# tolerances, not the intended thickness for a visual model.
STEEL_GAUGE_THICKNESS_IN = {7: 0.1793, 10: 0.1345, 12: 0.1046, 16: 0.0598, 18: 0.0478}
POST_STANDOFF_IN = 1.0
SIMPLIFIED_CORNER_CLIP_IN = 0.125


@dataclass(frozen=True)
class AdjustableBaseDimensions:
    clear_width_in: float
    length_in: float
    height_in: float
    standoff_gauge: int
    strap_gauge: int


# Simpson C-C-2026 pp. 76–77: W/L/H and separate Base/Strap gauge columns.
ADJUSTABLE_BASE_DIMENSIONS = {
    "ABU44": AdjustableBaseDimensions(3.5625, 3.0, 5.5, 16, 12),
    "ABU44R": AdjustableBaseDimensions(4.0625, 3.0, 5.25, 16, 12),
    "ABU66": AdjustableBaseDimensions(5.5, 5.0, 6.0625, 12, 10),
    "ABU66R": AdjustableBaseDimensions(6.0625, 5.0, 5.8125, 12, 10),
}


@dataclass(frozen=True)
class ColumnBaseDimensions:
    clear_width_in: float
    seat_length_in: float
    strap_width_in: float
    height_in: float
    embedment_in: float
    standoff_gauge: int = 12
    strap_gauge: int = 10


# CBSQ66-SDS2: C-C-2024 p. 79; matching drawing/dimensions in C-C-2026 p. 85.
COLUMN_BASE_DIMENSIONS = ColumnBaseDimensions(5.5, 5.5, 3.0, 8.75, 6.875)


@dataclass(frozen=True)
class ColumnCapDimensions:
    beam_clear_width_in: float
    post_clear_width_in: float
    seat_length_in: float = 11.0
    saddle_height_in: float = 7.0
    post_strap_length_in: float = 8.5
    post_strap_width_in: float = 2.5
    gauge: int = 7


# Simpson C-C-2026 pp. 98–99: W1 is the beam channel; W2 is the transverse post straps.
COLUMN_CAP_DIMENSIONS = {
    "CCQ44SDS2.5": ColumnCapDimensions(3.625, 3.625),
    "CCQ46SDS2.5": ColumnCapDimensions(3.625, 5.5),
    "CCQ66SDS2.5": ColumnCapDimensions(5.5, 5.5),
    "CCQ4.625.50SDS": ColumnCapDimensions(4.625, 5.5),
}


@dataclass(frozen=True)
class PostCapDimensions:
    clear_width_in: float = 5.5
    seat_length_in: float = 7.0
    beam_leaf_height_in: float = 3.0
    post_leaf_height_in: float = 1.625
    post_leaf_width_in: float = 2.625
    gauge: int = 16


POST_CAP_DIMENSIONS = PostCapDimensions()  # C-C-2026 p. 97, PC6Z.


@dataclass(frozen=True)
class AdjustableCapDimensions:
    nominal_post_width_in: float = 5.5
    beam_leaf_length_in: float = 8.5
    beam_leaf_height_in: float = 3.0
    post_leaf_height_in: float = 2.5
    post_return_in: float = 1.5
    gauge: int = 18


ADJUSTABLE_CAP_DIMENSIONS = AdjustableCapDimensions()  # C-C-2026 p. 94–95, AC6.
END_CAP_DIMENSIONS = AdjustableCapDimensions(beam_leaf_length_in=6.5)  # ESR-2604 Table 3.


@dataclass(frozen=True)
class AngleDimensions:
    length_in: float
    horizontal_leg_in: float
    vertical_leg_in: float
    gauge: int


# C-C-2026 pp. 313/315. L50's 5" is its longitudinal length, not either leg width.
ANGLE_DIMENSIONS = {
    "L50": AngleDimensions(5.0, 2.375, 1.375, 16),
    "HL33": AngleDimensions(2.5, 3.25, 3.25, 7),
    "HL35": AngleDimensions(5.0, 3.25, 3.25, 7),
}


def _clipped_vertical_leaf(
    x_min_in: float, x_max_in: float, y_in: float, z_min_in: float,
    z_max_in: float, thickness_in: float,
) -> GMesh:
    clip = SIMPLIFIED_CORNER_CLIP_IN
    return plate_mesh((
        (x_min_in, y_in, z_min_in), (x_max_in, y_in, z_min_in),
        (x_max_in, y_in, z_max_in - clip),
        (x_max_in - clip, y_in, z_max_in),
        (x_min_in + clip, y_in, z_max_in),
        (x_min_in, y_in, z_max_in - clip),
    ), (0.0, thickness_in, 0.0))


def _raised_seat_mesh(
    length_in: float, width_in: float, seat_thickness_in: float,
    support_bottom_in: float,
) -> GMesh:
    half_length, half_width = length_in / 2.0, width_in / 2.0
    seat_bottom = POST_STANDOFF_IN - seat_thickness_in
    # The end aprons support a thin raised pan while its middle remains hollow for the
    # anchor/embedded strap. Filling this inch with a block hides the actual drainage gap.
    return combine_meshes(
        box_mesh((-half_length, -half_width, seat_bottom),
                 (half_length, half_width, POST_STANDOFF_IN)),
        box_mesh((-half_length, -half_width, support_bottom_in),
                 (-half_length + seat_thickness_in, half_width, seat_bottom)),
        box_mesh((half_length - seat_thickness_in, -half_width, support_bottom_in),
                 (half_length, half_width, seat_bottom)),
    )


def _adjustable_base_mesh(dimensions: AdjustableBaseDimensions) -> GMesh:
    half_length = dimensions.length_in / 2.0
    half_width = dimensions.clear_width_in / 2.0
    strap_thickness = STEEL_GAUGE_THICKNESS_IN[dimensions.strap_gauge]
    return combine_meshes(
        box_mesh((-half_length, -half_width - strap_thickness, 0.0),
                 (half_length, half_width + strap_thickness, strap_thickness)),
        _clipped_vertical_leaf(-half_length, half_length, -half_width,
                               strap_thickness, dimensions.height_in, -strap_thickness),
        _clipped_vertical_leaf(-half_length, half_length, half_width,
                               strap_thickness, dimensions.height_in, strap_thickness),
        _raised_seat_mesh(dimensions.length_in, dimensions.clear_width_in,
                          STEEL_GAUGE_THICKNESS_IN[dimensions.standoff_gauge],
                          strap_thickness),
    )


def _column_base_mesh() -> GMesh:
    dimensions = COLUMN_BASE_DIMENSIONS
    half_width = dimensions.clear_width_in / 2.0
    half_strap = dimensions.strap_width_in / 2.0
    strap_thickness = STEEL_GAUGE_THICKNESS_IN[dimensions.strap_gauge]
    # The cast-in component is one U strap, with two exposed narrow leaves and a return
    # below concrete. Its 6-7/8" embedment must remain visible in foundation cutaways.
    return combine_meshes(
        _clipped_vertical_leaf(-half_strap, half_strap, -half_width,
                               -dimensions.embedment_in, dimensions.height_in, -strap_thickness),
        _clipped_vertical_leaf(-half_strap, half_strap, half_width,
                               -dimensions.embedment_in, dimensions.height_in, strap_thickness),
        box_mesh((-half_strap, -half_width, -dimensions.embedment_in),
                 (half_strap, half_width, -dimensions.embedment_in + strap_thickness)),
        _raised_seat_mesh(dimensions.seat_length_in, dimensions.clear_width_in,
                          STEEL_GAUGE_THICKNESS_IN[dimensions.standoff_gauge], 0.0),
    )


def _column_cap_mesh(dimensions: ColumnCapDimensions) -> GMesh:
    thickness = STEEL_GAUGE_THICKNESS_IN[dimensions.gauge]
    half_length = dimensions.seat_length_in / 2.0
    half_beam = dimensions.beam_clear_width_in / 2.0
    half_post = dimensions.post_clear_width_in / 2.0
    half_strap = dimensions.post_strap_width_in / 2.0
    meshes = [
        box_mesh((-half_length, -half_beam, -thickness),
                 (half_length, half_beam, 0.0)),
        _clipped_vertical_leaf(-half_length, half_length, -half_beam, -thickness,
                               dimensions.saddle_height_in - thickness, -thickness),
        _clipped_vertical_leaf(-half_length, half_length, half_beam, -thickness,
                               dimensions.saddle_height_in - thickness, thickness),
    ]
    # Default post leaves run across the beam: a CCQ46 must accommodate a 5-1/2" post
    # under a 3-5/8" channel without moving the beam leaves outside their actual opening.
    for side in (-1.0, 1.0):
        inner_x = side * half_post
        meshes.append(plate_mesh((
            (inner_x, -half_strap, -thickness),
            (inner_x, half_strap, -thickness),
            (inner_x, half_strap, -thickness - dimensions.post_strap_length_in),
            (inner_x, -half_strap, -thickness - dimensions.post_strap_length_in),
        ), (side * thickness, 0.0, 0.0)))
    return combine_meshes(*meshes)


def _post_cap_mesh() -> GMesh:
    dimensions = POST_CAP_DIMENSIONS
    thickness = STEEL_GAUGE_THICKNESS_IN[dimensions.gauge]
    half_length, half_width = dimensions.seat_length_in / 2, dimensions.clear_width_in / 2
    half_post_leaf = dimensions.post_leaf_width_in / 2
    return combine_meshes(
        box_mesh((-half_length, -half_width, -thickness),
                 (half_length, half_width, 0.0)),
        *(_clipped_vertical_leaf(-half_length, half_length, side * half_width,
                                -thickness, dimensions.beam_leaf_height_in,
                                side * thickness) for side in (-1.0, 1.0)),
        *(box_mesh((-half_post_leaf, min(side * half_width, side * (half_width + thickness)),
                    -thickness - dimensions.post_leaf_height_in),
                   (half_post_leaf, max(side * half_width, side * (half_width + thickness)),
                    -thickness)) for side in (-1.0, 1.0)),
    )


def _adjustable_post_cap_mesh(
    dimensions: AdjustableCapDimensions, *, end_cap: bool, member_width_in: float | None,
) -> GMesh:
    thickness = STEEL_GAUGE_THICKNESS_IN[dimensions.gauge]
    half_post = dimensions.nominal_post_width_in / 2.0
    joint_width = (dimensions.nominal_post_width_in
                   if member_width_in is None else member_width_in)
    if joint_width <= 0.0:
        raise ValueError("adjustable post cap member width must be positive")
    half_width = joint_width / 2.0
    x_min = -half_post if end_cap else -dimensions.beam_leaf_length_in / 2.0
    x_max = x_min + dimensions.beam_leaf_length_in
    meshes: list[GMesh] = []
    for side in (-1.0, 1.0):
        y = side * half_width
        meshes.extend((
            _clipped_vertical_leaf(x_min, x_max, y, 0.0,
                                   dimensions.beam_leaf_height_in, side * thickness),
            box_mesh((-half_post, min(y, y + side * thickness),
                      -dimensions.post_leaf_height_in),
                     (half_post, max(y, y + side * thickness), 0.0)),
        ))
        # Each manufactured piece has one perpendicular post return. The opposing piece
        # wraps the diagonal corner; adding returns at both ends invents extra steel.
        return_x = side * half_post
        meshes.append(box_mesh(
            (min(return_x, return_x + side * thickness),
             min(y, y - side * dimensions.post_return_in), -dimensions.post_leaf_height_in),
            (max(return_x, return_x + side * thickness),
             max(y, y - side * dimensions.post_return_in), 0.0),
        ))
    return combine_meshes(*meshes)


def _angle_mesh(dimensions: AngleDimensions) -> GMesh:
    thickness = STEEL_GAUGE_THICKNESS_IN[dimensions.gauge]
    half_length = dimensions.length_in / 2.0
    return combine_meshes(
        box_mesh((-half_length, -thickness, -thickness),
                 (half_length, dimensions.horizontal_leg_in, 0.0)),
        box_mesh((-half_length, -thickness, 0.0),
                 (half_length, 0.0, dimensions.vertical_leg_in)),
    )


def base_cap_mesh(
    part: str, *, member_width_in: float | None = None, member_depth_in: float | None = None,
) -> GMesh | None:
    """Return a catalog-sized local mesh, or None for an unsupported part.

    Only adjustable AC/ACE pairs use ``member_width_in`` to space their separate pieces.
    Beam depth does not stretch manufactured steel; ``member_depth_in`` is accepted for
    the common connector dispatcher. Coatings alter color, not these simplified shapes.
    """
    normalized = part.strip().upper().replace("-", "")
    for suffix in ("HDG", "SS", "Z", "PC"):
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break
    if normalized in ADJUSTABLE_BASE_DIMENSIONS:
        return _adjustable_base_mesh(ADJUSTABLE_BASE_DIMENSIONS[normalized])
    if normalized in {"CBSQ66", "CBSQ66SDS2"}:
        return _column_base_mesh()
    if normalized in COLUMN_CAP_DIMENSIONS:
        return _column_cap_mesh(COLUMN_CAP_DIMENSIONS[normalized])
    if normalized == "PC6":
        return _post_cap_mesh()
    if normalized in {"AC6", "ACE6"}:
        end_cap = normalized == "ACE6"
        return _adjustable_post_cap_mesh(
            END_CAP_DIMENSIONS if end_cap else ADJUSTABLE_CAP_DIMENSIONS,
            end_cap=end_cap, member_width_in=member_width_in,
        )
    if normalized in ANGLE_DIMENSIONS:
        return _angle_mesh(ANGLE_DIMENSIONS[normalized])
    return None
