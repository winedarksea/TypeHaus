"""Simplified folded Simpson ties, using C-C-2026 dimensioned product drawings.

Catalog dimensions and local installation datums are recorded in
``docs/simpson-tie-geometry.md``. Nail punching, stamping and bend radii are omitted.
Parts keep their catalog size: a supplied wood width never stretches a stock tie.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.connector_geometry.mesh import (
    box_mesh,
    combine_meshes,
    plate_mesh,
    transform_mesh,
)
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.kbs_geometry import kbs_mesh

# Nominal Manufacturers' Standard Gauge sheet thicknesses; coating is not modelled.
STEEL_THICKNESS_IN = {12: 0.1046, 14: 0.0747, 16: 0.0598, 18: 0.0478, 20: 0.0359}


@dataclass(frozen=True)
class HurricaneTieDimensions:
    leaf_width_in: float
    upper_height_in: float
    lower_height_in: float
    gauge: int = 18
    opening_width_in: float = 0.0
    return_depth_in: float = 0.0


HURRICANE_TIES = {
    "H2.5A": HurricaneTieDimensions(1.375, 3.8125, 2.1875),
    "H10A": HurricaneTieDimensions(5.0, 3.5, 2.75,
                                   opening_width_in=1.5625, return_depth_in=1.1875),
}


@dataclass(frozen=True)
class AngleDimensions:
    leaf_width_in: float
    height_in: float
    gauge: int


ANGLES = {
    "A35": AngleDimensions(1.4375, 4.5, 18),
    "LS30": AngleDimensions(2.25, 3.375, 18),
    "HGAM10": AngleDimensions(3.0, 3.0, 14),
}


@dataclass(frozen=True)
class StrapDimensions:
    width_in: float
    length_in: float
    gauge: int


STRAPS = {
    "LSTA24": StrapDimensions(1.25, 24.0, 20),
    "MSTA12": StrapDimensions(1.25, 12.0, 18),
    "CS16": StrapDimensions(1.25, 0.0, 16),
}


@dataclass(frozen=True)
class EmbeddedStrapDimensions:
    width_in: float
    exposed_height_in: float
    embedment_depth_in: float
    gauge: int
    spoon_projection_in: float


EMBEDDED_STRAPS = {
    "STHD14": EmbeddedStrapDimensions(3.0, 26.125, 14.0, 12, 5.0),
    "STHD14RJ": EmbeddedStrapDimensions(3.0, 39.625, 14.0, 12, 5.0),
    "STHD10": EmbeddedStrapDimensions(3.0, 24.625, 10.0, 12, 5.0),
    "STHD10RJ": EmbeddedStrapDimensions(3.0, 38.125, 10.0, 12, 5.0),
    "HETA20": EmbeddedStrapDimensions(1.125, 16.0, 4.0, 16, 1.0),
}


@dataclass(frozen=True)
class TieSilhouetteConfig:
    """Undimensioned silhouettes, normalized to the catalog's dimensioned envelope.

    These are visual contour simplifications, not fabrication measurements.
    MASA's transverse width is a visual estimate: the public catalog omits it.
    """

    corner_clip_in: float = 0.125
    angle_waist_fraction: float = 0.30
    angle_waist_lower_fraction: float = 0.35
    angle_waist_upper_fraction: float = 0.65
    lateral_plate_tab_fraction: float = 0.16
    lateral_plate_tabs: int = 3
    embedded_spoon_return_fraction: float = 0.25
    heta_spoon_height_in: float = 0.5
    masa_width_in: float = 3.0
    masa_fork_leaf_width_in: float = 0.75
    masa_nailing_leg_length_in: float = 4.25
    masa_embedment_projection_in: float = 4.0
    masa_embedment_depth_in: float = 3.375
    masa_default_sill_height_in: float = 1.5
    masa_spoon_tip_width_fraction: float = 0.65
    masa_spoon_return_in: float = 0.25
    tension_tie_upper_width_in: float = 3.25
    tension_tie_height_in: float = 6.9375
    tension_tie_seat_width_in: float = 1.625
    tension_tie_seat_depth_in: float = 1.625
    tension_tie_slot_width_in: float = 0.125
    tension_tie_web_height_fraction: float = 0.50
    tension_tie_bolt_hole_diameter_in: float = 0.5625
    tension_tie_hole_segments: int = 12
    stud_tie_leaf_width_in: float = 1.25
    knee_brace_width_in: float = 5.0
    knee_brace_leg_length_in: float = 4.875
    knee_brace_angle_radians: float = math.pi / 4.0
    masonry_angle_width_in: float = 3.5


SILHOUETTE = TieSilhouetteConfig()
STUD_TIES = {"SP4": (3.5625, 7.25), "SP6": (5.5625, 7.75)}
LATERAL_PLATE_WIDTH_IN = 3.0
LATERAL_PLATE_HEIGHT_IN = 4.25


def _xz_leaf(profile_in: tuple[tuple[float, float], ...], thickness_in: float,
             transverse_offset_in: float = 0.0) -> GMesh:
    return plate_mesh(tuple((x, transverse_offset_in, z) for x, z in profile_in),
                      (0.0, -thickness_in, 0.0))


def _hurricane_tie(part: str) -> GMesh:
    dimensions = HURRICANE_TIES[part]
    thickness = STEEL_THICKNESS_IN[dimensions.gauge]
    width = dimensions.leaf_width_in
    upper_height, lower_height = dimensions.upper_height_in, dimensions.lower_height_in
    clip = SILHOUETTE.corner_clip_in
    if part == "H2.5A":
        # Both leaves share a vertical bent heel; their diagonal edges form the neck.
        neck_height = upper_height - lower_height
        lower_leaf = _xz_leaf(((-width, -lower_height + clip),
                              (-width + clip, -lower_height), (-clip, -lower_height),
                              (0.0, -lower_height + clip), (0.0, neck_height),
                              (-width, 0.0)), thickness)
        upper_profile = ((0.0, 0.0, 0.0), (0.0, width, neck_height),
                         (0.0, width, upper_height - clip),
                         (0.0, width - clip, upper_height),
                         (0.0, clip, upper_height), (0.0, 0.0, upper_height - clip))
        return combine_meshes(lower_leaf, plate_mesh(upper_profile, (-thickness, 0.0, 0.0)))

    half_width = width / 2.0
    half_opening = dimensions.opening_width_in / 2.0
    backing = _xz_leaf(((-half_width + clip, -lower_height),
                        (half_width - clip, -lower_height),
                        (half_width, -lower_height + clip),
                        (half_width, upper_height - clip),
                        (half_width - clip, upper_height), (half_opening, upper_height),
                        (half_opening, 0.0), (-half_opening, 0.0),
                        (-half_opening, upper_height), (-half_width + clip, upper_height),
                        (-half_width, upper_height - clip),
                        (-half_width, -lower_height + clip)), thickness)
    returns = tuple(plate_mesh(((x, 0.0, 0.0), (x, dimensions.return_depth_in, 0.0),
                               (x, dimensions.return_depth_in, upper_height),
                               (x, 0.0, upper_height)), (direction * thickness, 0.0, 0.0))
                    for x, direction in ((-half_opening, -1.0), (half_opening, 1.0)))
    return combine_meshes(backing, *returns)


def _flat_or_ridge_strap(dimensions: StrapDimensions, slope_radians: float) -> GMesh:
    half_width, half_length = dimensions.width_in / 2.0, dimensions.length_in / 2.0
    thickness = STEEL_THICKNESS_IN[dimensions.gauge]
    slope = abs(slope_radians)
    cosine, sine = math.cos(slope), math.sin(slope)
    leaves = []
    for direction in (-1.0, 1.0):
        transverse_end = direction * half_length * cosine
        endpoint_z = -half_length * sine
        leaves.append(plate_mesh(((-half_width, 0.0, 0.0),
                                  (half_width, 0.0, 0.0),
                                  (half_width, transverse_end, endpoint_z),
                                  (-half_width, transverse_end, endpoint_z)),
                                 (0.0, direction * thickness * sine, thickness * cosine)))
    return combine_meshes(*leaves)


def _angle_tie(part: str) -> GMesh:
    dimensions = ANGLES[part]
    thickness = STEEL_THICKNESS_IN[dimensions.gauge]
    width, height = dimensions.leaf_width_in, dimensions.height_in
    if part == "HGAM10":
        half_width = SILHOUETTE.masonry_angle_width_in / 2.0
        return combine_meshes(box_mesh((-half_width, 0.0, -thickness),
                                       (half_width, width, 0.0)),
                              box_mesh((-half_width, -thickness, 0.0),
                                       (half_width, 0.0, height)))
    waist_width = width * (1.0 - SILHOUETTE.angle_waist_fraction)
    waist_bottom = height * SILHOUETTE.angle_waist_lower_fraction
    waist_top = height * SILHOUETTE.angle_waist_upper_fraction
    profile = ((0.0, 0.0), (width, 0.0), (width, waist_bottom),
               (waist_width, waist_bottom), (waist_width, waist_top),
               (width, waist_top), (width, height), (0.0, height))
    first = _xz_leaf(profile, thickness)
    second = plate_mesh(tuple((0.0, x, z) for x, z in profile), (-thickness, 0.0, 0.0))
    return combine_meshes(first, second)


def _lateral_tie_plate() -> GMesh:
    width, height = LATERAL_PLATE_WIDTH_IN, LATERAL_PLATE_HEIGHT_IN
    inset = width * SILHOUETTE.lateral_plate_tab_fraction
    spacing = height / SILHOUETTE.lateral_plate_tabs
    right_edge = [(width / 2.0 - inset, -height / 2.0)]
    for station in range(SILHOUETTE.lateral_plate_tabs):
        z0 = -height / 2.0 + station * spacing
        right_edge.extend(((width / 2.0 - inset, z0 + spacing / 4.0),
                           (width / 2.0, z0 + spacing / 4.0),
                           (width / 2.0, z0 + 3.0 * spacing / 4.0),
                           (width / 2.0 - inset, z0 + 3.0 * spacing / 4.0)))
    right_edge.append((width / 2.0 - inset, height / 2.0))
    left_edge = [(-x, z) for x, z in reversed(right_edge)]
    return _xz_leaf(tuple(right_edge + left_edge), STEEL_THICKNESS_IN[20])


def _embedded_strap(part: str) -> GMesh:
    dimensions = EMBEDDED_STRAPS[part]
    thickness = STEEL_THICKNESS_IN[dimensions.gauge]
    half_width = dimensions.width_in / 2.0
    depth, projection = dimensions.embedment_depth_in, dimensions.spoon_projection_in
    if part == "HETA20":
        spoon_height = SILHOUETTE.heta_spoon_height_in
        vertical = box_mesh((-half_width, -thickness, -depth + spoon_height),
                            (half_width, 0.0, dimensions.exposed_height_in))
        spoon = plate_mesh(((-half_width, 0.0, -depth + spoon_height),
                            (half_width, 0.0, -depth + spoon_height),
                            (half_width, projection, -depth),
                            (-half_width, projection, -depth)),
                           (0.0, thickness * spoon_height / math.hypot(projection, spoon_height),
                            thickness * projection / math.hypot(projection, spoon_height)))
        return combine_meshes(vertical, spoon)
    vertical = box_mesh((-half_width, -thickness, 0.0),
                        (half_width, 0.0, dimensions.exposed_height_in))
    return_length = projection * SILHOUETTE.embedded_spoon_return_fraction
    shaft_end_y = projection - return_length
    normal_length = math.hypot(depth, shaft_end_y)
    shaft = plate_mesh(((-half_width, 0.0, 0.0), (half_width, 0.0, 0.0),
                        (half_width, shaft_end_y, -depth),
                        (-half_width, shaft_end_y, -depth)),
                       (0.0, thickness * depth / normal_length,
                        thickness * shaft_end_y / normal_length))
    toe = box_mesh((-half_width, shaft_end_y, -depth),
                   (half_width, projection, -depth + thickness))
    return combine_meshes(vertical, shaft, toe)


def _mudsill_anchor(sill_height_in: float) -> GMesh:
    config, thickness = SILHOUETTE, STEEL_THICKNESS_IN[16]
    half_width = config.masa_width_in / 2.0
    horizontal_nailing_leg = config.masa_nailing_leg_length_in - sill_height_in
    if not 0.0 < sill_height_in < config.masa_nailing_leg_length_in:
        raise ValueError("MASA sill height must be positive and shorter than its nailing legs")
    arms: list[GMesh] = []
    for x0, x1 in ((-half_width, -half_width + config.masa_fork_leaf_width_in),
                   (half_width - config.masa_fork_leaf_width_in, half_width)):
        arms.extend((box_mesh((x0, -thickness, 0.0), (x1, 0.0, sill_height_in)),
                     box_mesh((x0, 0.0, sill_height_in),
                              (x1, horizontal_nailing_leg, sill_height_in + thickness))))
    embedded_end_y = config.masa_embedment_projection_in - config.masa_spoon_return_in
    depth = config.masa_embedment_depth_in
    tip_half_width = half_width * config.masa_spoon_tip_width_fraction
    normal_length = math.hypot(embedded_end_y, depth)
    shovel = plate_mesh(((-half_width, 0.0, 0.0), (half_width, 0.0, 0.0),
                         (tip_half_width, embedded_end_y, -depth),
                         (-tip_half_width, embedded_end_y, -depth)),
                        (0.0, thickness * depth / normal_length,
                         thickness * embedded_end_y / normal_length))
    toe = box_mesh((-tip_half_width, embedded_end_y, -depth),
                   (tip_half_width, config.masa_embedment_projection_in, -depth + thickness))
    return combine_meshes(*arms, shovel, toe)


def _tension_tie_seat() -> GMesh:
    config, thickness = SILHOUETTE, STEEL_THICKNESS_IN[14]
    half_width = config.tension_tie_seat_width_in / 2.0
    half_depth = config.tension_tie_seat_depth_in / 2.0
    radius = config.tension_tie_bolt_hole_diameter_in / 2.0
    angles = sorted({*(2.0 * math.pi * index / config.tension_tie_hole_segments
                       for index in range(config.tension_tie_hole_segments)),
                     *(math.atan2(y, x) % (2.0 * math.pi)
                       for x, y in ((half_width, half_depth), (-half_width, half_depth),
                                    (-half_width, -half_depth), (half_width, -half_depth)))})
    outer, inner = [], []
    for angle in angles:
        cosine, sine = math.cos(angle), math.sin(angle)
        reach = min(half_width / abs(cosine) if abs(cosine) > 1e-10 else math.inf,
                    half_depth / abs(sine) if abs(sine) > 1e-10 else math.inf)
        outer.append((reach * cosine, half_depth + reach * sine))
        inner.append((radius * cosine, half_depth + radius * sine))
    cells = []
    for index in range(len(angles)):
        following = (index + 1) % len(angles)
        profile = (outer[index], outer[following], inner[following], inner[index])
        cells.append(plate_mesh(tuple((x, y, 0.0) for x, y in profile), (0.0, 0.0, thickness)))
    return combine_meshes(*cells)


def _tension_tie() -> GMesh:
    config, thickness = SILHOUETTE, STEEL_THICKNESS_IN[14]
    half_width = config.tension_tie_upper_width_in / 2.0
    half_seat = config.tension_tie_seat_width_in / 2.0
    half_slot = config.tension_tie_slot_width_in / 2.0
    web_height = config.tension_tie_height_in * config.tension_tie_web_height_fraction
    clip = config.corner_clip_in
    left_profile = ((-half_seat, 0.0), (-half_width, web_height),
                    (-half_width, config.tension_tie_height_in - clip),
                    (-half_width + clip, config.tension_tie_height_in),
                    (-half_slot, config.tension_tie_height_in),
                    (-half_slot, config.tension_tie_seat_depth_in), (-half_seat + thickness, 0.0))
    back = (_xz_leaf(left_profile, thickness),
            _xz_leaf(tuple((-x, z) for x, z in left_profile), thickness))
    sides = tuple(plate_mesh(((x, 0.0, 0.0),
                             (x, config.tension_tie_seat_depth_in, 0.0),
                             (x, 0.0, web_height)), (direction * thickness, 0.0, 0.0))
                  for x, direction in ((-half_seat, 1.0), (half_seat, -1.0)))
    return combine_meshes(_tension_tie_seat(), *back, *sides)


def _stud_plate_tie(part: str) -> GMesh:
    opening_width, length = STUD_TIES[part]
    thickness = STEEL_THICKNESS_IN[20]
    half_leaf = SILHOUETTE.stud_tie_leaf_width_in / 2.0
    half_opening = opening_width / 2.0
    bridge = box_mesh((-half_leaf, -half_opening, 0.0), (half_leaf, half_opening, thickness))
    return combine_meshes(bridge,
                          box_mesh((-half_leaf, -half_opening - thickness, -length),
                                   (half_leaf, -half_opening, 0.0)),
                          box_mesh((-half_leaf, half_opening, -length),
                                   (half_leaf, half_opening + thickness, 0.0)))


def _knee_brace() -> GMesh:
    config, thickness = SILHOUETTE, STEEL_THICKNESS_IN[12]
    half_width, length = config.knee_brace_width_in / 2.0, config.knee_brace_leg_length_in
    first = box_mesh((-half_width, -length, -thickness), (half_width, 0.0, 0.0))
    second = box_mesh((-half_width, 0.0, -thickness), (half_width, length, 0.0))
    cosine = math.cos(config.knee_brace_angle_radians)
    sine = math.sin(config.knee_brace_angle_radians)
    return combine_meshes(first, transform_mesh(second, y_axis=(0.0, cosine, -sine),
                                                z_axis=(0.0, sine, cosine)))


def tie_mesh(part: str, *, member_width_in: float | None = None,
             member_depth_in: float | None = None, slope_radians: float = 0.0,
             strap_length_in: float | None = None) -> GMesh | None:
    """Return stock-size tie geometry in metres, with inputs expressed in inches.

    Hurricane ties use plate-top zero; concrete straps use pour-top zero; flat
    straps use their centre/crest; angles use the inner heel at their bottom;
    DTT2 uses seat-bottom zero; SP uses its plate-top bridge. ``CS16`` requires an
    authored cut length. ``STHD`` is displayed as the documented STHD14 representative.
    """
    normalized = part.strip().upper()
    coating_aliases = {"H2.5AZ": "H2.5A", "H2.5ASS": "H2.5A",
                       "H10ASS": "H10A", "A35Z": "A35", "A35SS": "A35",
                       "LS30Z": "LS30", "MSTA12Z": "MSTA12", "LTP4Z": "LTP4",
                       "HETA20Z": "HETA20", "STHD": "STHD14"}
    normalized = coating_aliases.get(normalized, normalized)
    if normalized in HURRICANE_TIES:
        return _hurricane_tie(normalized)
    if normalized in STRAPS:
        dimensions = STRAPS[normalized]
        if normalized == "CS16":
            if strap_length_in is None:
                return None
            if not math.isfinite(strap_length_in) or strap_length_in <= 0.0:
                raise ValueError("CS16 cut length must be finite and positive")
            dimensions = StrapDimensions(dimensions.width_in, strap_length_in, dimensions.gauge)
        return _flat_or_ridge_strap(dimensions, slope_radians if normalized == "LSTA24" else 0.0)
    if normalized in ANGLES:
        return _angle_tie(normalized)
    if normalized == "LTP4":
        return _lateral_tie_plate()
    if normalized in EMBEDDED_STRAPS:
        return _embedded_strap(normalized)
    if normalized == "MASA":
        return _mudsill_anchor(member_depth_in if member_depth_in is not None
                              else SILHOUETTE.masa_default_sill_height_in)
    if normalized == "DTT2Z":
        return _tension_tie()
    if normalized in STUD_TIES:
        return _stud_plate_tie(normalized)
    if normalized == "KBS1Z":
        return kbs_mesh((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0),
                        (math.sqrt(0.5), 0.0, math.sqrt(0.5)),
                        (math.sqrt(0.5), 0.0, -math.sqrt(0.5)), (0.0, 1.0, 0.0))
    if normalized == "APVKB45-6":
        return _knee_brace()
    return None
