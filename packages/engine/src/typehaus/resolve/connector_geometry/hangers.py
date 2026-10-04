"""Simplified folded Simpson hangers in the carried member's support-face frame.

Catalog envelopes and gauge are retained; holes, nail domes and bend radii are omitted.
See docs/simpson-hanger-geometry.md for drawing sources and outline simplifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, isclose, sin

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import (
    box_mesh,
    combine_meshes,
    plate_mesh,
    transform_mesh,
    translate_mesh,
)
from typehaus.resolve.geometry_ir import GMesh

# C-C-2026 p. 24 nominal uncoated steel; finish buildup is omitted consistently.
SHEET_THICKNESS_IN = {14: 0.075, 16: 0.060, 18: 0.048}
MEMBER_SIZE_TOLERANCE_IN = 1 / 32
FAMILY_ONLY_IJOIST_FLANGE_WIDTHS_IN = (2.0, 2.5)


@dataclass(frozen=True)
class HangerDimensions:
    clear_width_in: float
    height_in: float
    bearing_depth_in: float
    gauge: int
    face_flange_width_in: float


# Simpson C-C-2026 pp. 113–117, 219–221: W, H and B are product dimensions,
# never the nominal lumber section or a percentage of the carried member's depth.
LUS_DIMENSIONS = {
    "LUS24": HangerDimensions(1.5625, 3.125, 1.75, 18, 1.0),
    "LUS26": HangerDimensions(1.5625, 4.75, 1.75, 18, 1.0),
    "LUS28": HangerDimensions(1.5625, 6.625, 1.75, 18, 1.0),
    "LUS210": HangerDimensions(1.5625, 7.8125, 1.75, 18, 1.0),
    "LUS24-2": HangerDimensions(3.125, 3.125, 2.0, 18, 1.0),
    "LUS26-2": HangerDimensions(3.125, 4.875, 2.0, 18, 1.0),
    "LUS28-2": HangerDimensions(3.125, 7.0, 2.0, 18, 1.0),
    "LUS210-2": HangerDimensions(3.125, 9.0, 2.0, 18, 1.0),
    "LUS214-2": HangerDimensions(3.125, 10.9375, 2.0, 18, 1.0),
    "LUS28-3": HangerDimensions(4.625, 6.25, 2.0, 18, 1.0),
    "LUS210-3": HangerDimensions(4.625, 8.1875, 2.0, 18, 1.0),
    "LUS46": HangerDimensions(3.5625, 4.75, 2.0, 18, 1.0625),
    "LUS48": HangerDimensions(3.5625, 6.75, 2.0, 18, 1.0625),
    "LUS410": HangerDimensions(3.5625, 8.75, 2.0, 18, 1.0625),
    "LUS414": HangerDimensions(3.5625, 10.75, 2.0, 18, 1.0625),
}

HU_DIMENSIONS = {
    "HU28": HangerDimensions(1.5625, 5.25, 2.25, 14, 1.25),
    "HU210": HangerDimensions(1.5625, 7.125, 2.25, 14, 1.25),
    "HU212": HangerDimensions(1.5625, 9.0, 2.25, 14, 1.25),
    "HU28-2": HangerDimensions(3.125, 6.3125, 2.5, 14, 1.25),
    "HU210-2": HangerDimensions(3.125, 8.625, 2.5, 14, 1.25),
    "HU212-2": HangerDimensions(3.125, 10.5625, 2.5, 14, 1.25),
    "HU210-3": HangerDimensions(4.6875, 8.0625, 2.5, 14, 1.25),
    "HU212-3": HangerDimensions(4.6875, 9.8125, 2.5, 14, 1.25),
    "HU44": HangerDimensions(3.5625, 2.875, 2.5, 14, 1.25),
    "HU46": HangerDimensions(3.5625, 4.75, 2.5, 14, 1.25),
    "HU48": HangerDimensions(3.5625, 6.125, 2.5, 14, 1.25),
    "HU410": HangerDimensions(3.5625, 8.375, 2.5, 14, 1.25),
    "HU412": HangerDimensions(3.5625, 10.375, 2.5, 14, 1.25),
}

# C-C-2026 pp. 158–161: IUS clear W exceeds the designation's flange width.
IUS_FLANGE_WIDTHS = {"1.81": (1.75, 1.875), "2.06": (2.0, 2.125),
                     "2.37": (2.3125, 2.4375), "2.56": (2.5625, 2.625),
                     "3.56": (3.5, 3.625)}
IUS_HEIGHTS = {"9.5": 9.5, "11.88": 11.875, "14": 14.0, "16": 16.0}
IUS_DIMENSIONS = {
    f"IUS{width}/{depth}": HangerDimensions(clear, height, 2.0, 18, 1.125)
    for width, (_, clear) in IUS_FLANGE_WIDTHS.items()
    for depth, height in IUS_HEIGHTS.items()
}

# C-C-2026 pp. 115–117, 158–161. Concealed flanges remain inside the seat width.
HUCQ_DIMENSIONS = {
    "HUCQ210-2-SDS": HangerDimensions(3.25, 9.0, 3.0, 14, 1.25),
    "HUCQ210-3-SDS": HangerDimensions(4.625, 9.0, 3.0, 14, 1.25),
    "HUCQ410-SDS": HangerDimensions(3.5625, 9.0, 3.0, 14, 1.25),
    "HUCQ412-SDS": HangerDimensions(3.5625, 11.0, 3.0, 14, 1.25),
}
LSSR_DIMENSIONS = {
    "LSSR1.81": HangerDimensions(1.8125, 8.9375, 4.125, 18, 1.25),
    "LSSR2.1": HangerDimensions(2.125, 8.9375, 4.125, 18, 1.25),
    "LSSR2.37": HangerDimensions(2.375, 8.9375, 4.125, 18, 1.25),
    "LSSR2.56": HangerDimensions(2.5625, 8.9375, 4.125, 18, 1.25),
    "LSSR210-2": HangerDimensions(3.125, 8.9375, 5.125, 16, 1.25),
    "LSSR410": HangerDimensions(3.625, 8.9375, 5.125, 16, 1.25),
}
HHUS410_DIMENSIONS = HangerDimensions(3.625, 9.0, 3.0, 14, 2.0)
THA422_DIMENSIONS = HangerDimensions(3.625, 22.0, 1.75, 16, 1.75)

# These are silhouette simplifications from the illustrated outlines, not catalog
# manufacturing dimensions. They affect the reliefs, not W/H/B or steel thickness.
SIDE_UPPER_REACH_RATIO = 0.65
SIDE_SEAT_TAPER_HEIGHT_RATIO = 0.20
IUS_WAIST_HEIGHT_RATIOS = (0.28, 0.42, 0.55)
IUS_WAIST_REACH_RATIO = 0.35
IUS_LOCATOR_TAB_DEPTH_IN = 0.25
IUS_LOCATOR_TAB_WIDTH_RATIO = 0.45
LSSR_HEADER_BOTTOM_HEIGHT_RATIO = 0.45
LSSR_FRONT_RELIEF_HEIGHT_RATIOS = (0.28, 0.45, 0.84, 0.90)
LSSR_SEAT_LENGTH_IN = 1.25
LSSR_SEAT_CHEEK_HEIGHT_IN = 2.0
LSC_STRIP_LENGTH_IN = 11.0625
LSC_STRINGER_LEAF_LENGTH_IN = 6.75
LSC_STRIP_WIDTH_IN = 1.5
LSC_EAR_LENGTH_RATIO = 0.35
THA422_SIDE_HEIGHT_IN = 7.875
THA_MINIMUM_TOP_WRAP_IN = 2.0


def _side_plate(x: float, outline_yz: tuple[tuple[float, float], ...],
                extrusion_x: float) -> GMesh:
    return plate_mesh(tuple((x, y, z) for y, z in outline_yz), (extrusion_x, 0.0, 0.0))


def _flanges(dimensions: HangerDimensions, *, concealed: bool,
             bottom_z_in: float = 0.0) -> tuple[GMesh, GMesh]:
    half_width = dimensions.clear_width_in / 2
    thickness = SHEET_THICKNESS_IN[dimensions.gauge]
    height = dimensions.height_in - thickness
    flange_width = min(dimensions.face_flange_width_in, half_width) if concealed else (
        dimensions.face_flange_width_in)
    left = (-half_width, -half_width + flange_width) if concealed else (
        -half_width - thickness - flange_width, -half_width)
    right = (half_width - flange_width, half_width) if concealed else (
        half_width, half_width + thickness + flange_width)
    return (box_mesh((left[0], -thickness, bottom_z_in), (left[1], 0.0, height)),
            box_mesh((right[0], -thickness, bottom_z_in), (right[1], 0.0, height)))


def _folded_hanger(dimensions: HangerDimensions, *, concealed: bool = False,
                   ius: bool = False) -> GMesh:
    half_width = dimensions.clear_width_in / 2
    thickness = SHEET_THICKNESS_IN[dimensions.gauge]
    height = dimensions.height_in - thickness
    bearing = dimensions.bearing_depth_in
    upper_reach = bearing * SIDE_UPPER_REACH_RATIO
    outline: tuple[tuple[float, float], ...]
    if ius:
        waist_start, waist_centre, waist_end = (
            height * ratio for ratio in IUS_WAIST_HEIGHT_RATIOS)
        outline = ((0.0, 0.0), (bearing, 0.0), (bearing, waist_start),
                   (bearing * IUS_WAIST_REACH_RATIO, waist_centre),
                   (bearing, waist_end), (bearing, height), (0.0, height))
    else:
        outline = ((0.0, 0.0), (bearing, 0.0),
                   (upper_reach, height * SIDE_SEAT_TAPER_HEIGHT_RATIO),
                   (upper_reach, height), (0.0, height))
    parts = [box_mesh((-half_width - thickness, 0.0, -thickness),
                      (half_width + thickness, bearing, 0.0)),
             _side_plate(-half_width, outline, -thickness),
             _side_plate(half_width, outline, thickness),
             *_flanges(dimensions, concealed=concealed)]
    if ius:
        tab_width = dimensions.face_flange_width_in * IUS_LOCATOR_TAB_WIDTH_RATIO
        for sign in (-1, 1):
            tab_minimum = sign * half_width + (0.0 if sign > 0 else -tab_width)
            parts.append(box_mesh((tab_minimum, -IUS_LOCATOR_TAB_DEPTH_IN, height - thickness),
                                  (tab_minimum + tab_width, 0.0, height)))
    return combine_meshes(*parts)


def _slope(mesh: GMesh, angle: float) -> GMesh:
    return transform_mesh(mesh, y_axis=(0.0, cos(angle), sin(angle)),
                          z_axis=(0.0, -sin(angle), cos(angle)))


def _lssr_hanger(dimensions: HangerDimensions, slope_radians: float) -> GMesh:
    half_width = dimensions.clear_width_in / 2
    thickness = SHEET_THICKNESS_IN[dimensions.gauge]
    reach = dimensions.bearing_depth_in  # LSSR's catalog calls this A, not B.
    height = dimensions.height_in - thickness
    mounting_bottom = height * LSSR_HEADER_BOTTOM_HEIGHT_RATIO
    seat_front_y = reach * cos(slope_radians)
    relief_y = seat_front_y - dimensions.face_flange_width_in
    low, lower_notch, upper_notch, high = (
        height * ratio for ratio in LSSR_FRONT_RELIEF_HEIGHT_RATIOS)
    outline = ((0.0, mounting_bottom), (seat_front_y, 0.0),
               (seat_front_y, low), (relief_y, lower_notch),
               (relief_y, upper_notch), (seat_front_y, high),
               (seat_front_y, height), (0.0, height))
    body = combine_meshes(_side_plate(-half_width, outline, -thickness),
                          _side_plate(half_width, outline, thickness),
                          *_flanges(dimensions, concealed=False,
                                    bottom_z_in=mounting_bottom))
    # The mounting wings stay upright; the hinged front seat follows the rafter.
    front_seat_y = reach - LSSR_SEAT_LENGTH_IN
    seat = combine_meshes(
        box_mesh((-half_width, front_seat_y, -thickness), (half_width, reach, 0.0)),
        box_mesh((-half_width - 2 * thickness, front_seat_y, 0.0),
                 (-half_width - thickness, reach, LSSR_SEAT_CHEEK_HEIGHT_IN)),
        box_mesh((half_width + thickness, front_seat_y, 0.0),
                 (half_width + 2 * thickness, reach, LSSR_SEAT_CHEEK_HEIGHT_IN)))
    body_bottom_z_in = reach * sin(slope_radians)
    return combine_meshes(translate_mesh(body, (0.0, 0.0, body_bottom_z_in * M_PER_IN)),
                          _slope(seat, slope_radians))


def _lsc_hanger(slope_radians: float) -> GMesh:
    thickness = SHEET_THICKNESS_IN[18]
    half_width = LSC_STRIP_WIDTH_IN / 2
    header_length = LSC_STRIP_LENGTH_IN - LSC_STRINGER_LEAF_LENGTH_IN
    ear_length = LSC_STRINGER_LEAF_LENGTH_IN * LSC_EAR_LENGTH_RATIO
    header = combine_meshes(
        box_mesh((-half_width, -thickness, 0.0), (half_width, 0.0, header_length)),
        box_mesh((half_width, 0.0, header_length - ear_length),
                 (half_width + thickness, LSC_STRIP_WIDTH_IN, header_length)))
    seat = combine_meshes(
        box_mesh((-half_width, 0.0, -thickness),
                 (half_width, LSC_STRINGER_LEAF_LENGTH_IN, 0.0)),
        box_mesh((half_width, LSC_STRINGER_LEAF_LENGTH_IN - ear_length, 0.0),
                 (half_width + thickness, LSC_STRINGER_LEAF_LENGTH_IN,
                  LSC_STRIP_WIDTH_IN)))
    return combine_meshes(header, _slope(seat, slope_radians))


def _tha422_hanger(member_depth_in: float | None, support_width_in: float | None) -> GMesh:
    dimensions = THA422_DIMENSIONS
    thickness = SHEET_THICKNESS_IN[dimensions.gauge]
    half_width = dimensions.clear_width_in / 2
    stock_length = dimensions.height_in
    top_wrap = support_width_in if support_width_in is not None else THA_MINIMUM_TOP_WRAP_IN
    bend_height = member_depth_in
    if bend_height is None or not THA422_SIDE_HEIGHT_IN <= bend_height <= (
            stock_length - THA_MINIMUM_TOP_WRAP_IN):
        bend_height = stock_length
    side_dimensions = HangerDimensions(dimensions.clear_width_in, THA422_SIDE_HEIGHT_IN,
                                        dimensions.bearing_depth_in, dimensions.gauge,
                                        dimensions.face_flange_width_in)
    parts = [_folded_hanger(side_dimensions)]
    for sign in (-1, 1):
        outer_x = half_width + thickness
        x0, x1 = ((outer_x, outer_x + dimensions.face_flange_width_in) if sign > 0 else
                  (-outer_x - dimensions.face_flange_width_in, -outer_x))
        if bend_height > THA422_SIDE_HEIGHT_IN:
            parts.append(box_mesh((x0, -thickness, THA422_SIDE_HEIGHT_IN - thickness),
                                  (x1, 0.0, bend_height - thickness)))
        remaining_stock = stock_length - bend_height
        if remaining_stock > 0:
            horizontal_length = min(top_wrap, remaining_stock)
            parts.append(box_mesh((x0, -horizontal_length, bend_height - thickness),
                                  (x1, 0.0, bend_height)))
            return_length = remaining_stock - horizontal_length
            if return_length > 0:
                parts.append(box_mesh((x0, -horizontal_length - thickness,
                                       bend_height - return_length),
                                      (x1, -horizontal_length, bend_height)))
    return combine_meshes(*parts)


def _sawn_model(family: str, width: float | None, depth: float | None) -> str | None:
    if width is None or depth is None:
        return None
    # A family-only annotation cannot establish an engineered-member product. This
    # real stamping is a representative for the current 2-1/2-inch I-joist rows.
    if family == "LUS" and any(isclose(width, flange, abs_tol=MEMBER_SIZE_TOLERANCE_IN)
                                for flange in FAMILY_ONLY_IJOIST_FLANGE_WIDTHS_IN) and (
            isclose(depth, 11.875, abs_tol=MEMBER_SIZE_TOLERANCE_IN)):
        return "LUS210-2"
    dimensions = LUS_DIMENSIONS if family == "LUS" else HU_DIMENSIONS
    for nominal_width, suffix in ((1.5, "2"), (3.0, "2"), (3.5, "4"), (4.5, "2")):
        fits_single_rim = family == "LUS" and nominal_width == 1.5 and 0 < width <= 1.5
        if not fits_single_rim and not isclose(width, nominal_width,
                                              abs_tol=MEMBER_SIZE_TOLERANCE_IN):
            continue
        ply_suffix = "-2" if nominal_width == 3.0 else "-3" if nominal_width == 4.5 else ""
        if family == "LUS":
            size = 4 if depth <= 3.5 else 6 if depth <= 5.5 else 8 if depth <= 7.25 else (
                10 if depth <= 11.25 else 14)
        else:
            size = 4 if depth <= 3.5 else 6 if depth <= 5.5 else 8 if depth <= 7.25 else (
                10 if depth <= 9.25 else 12)
        model = f"{family}{suffix}{size}{ply_suffix}"
        return model if model in dimensions else None
    return None


def _ius_model(width: float | None, depth: float | None) -> str | None:
    if width is None or depth is None:
        return None
    height_name = next((name for name, height in IUS_HEIGHTS.items()
                        if isclose(depth, height, abs_tol=MEMBER_SIZE_TOLERANCE_IN)), None)
    width_name = next((name for name, (maximum_flange, _) in IUS_FLANGE_WIDTHS.items()
                       if width <= maximum_flange + MEMBER_SIZE_TOLERANCE_IN), None)
    return f"IUS{width_name}/{height_name}" if width_name and height_name else None


def hanger_mesh(part: str, *, member_width_in: float | None = None,
                member_depth_in: float | None = None, slope_radians: float = 0.0,
                support_width_in: float | None = None) -> GMesh | None:
    """Return a catalog hanger; unknown designations/dimensionless families return None.

    Local x spans the clear opening, +y leaves the support face, z=0 is the carried
    bottom at that face. Only adjustable seats follow signed pitch along local +y.
    Authored dimensions win even when the supplied member does not fit the product.
    """
    model = part.strip().upper()
    for finish in ("SS", "Z", "PC"):
        if model.endswith(finish):
            model = model[:-len(finish)]
            break
    if model == "LSC":
        return _lsc_hanger(slope_radians)
    if model == "THA422":
        return _tha422_hanger(member_depth_in, support_width_in)
    if model == "LSSR":
        if member_width_in is None:
            return None
        model = next((name for name, dims in LSSR_DIMENSIONS.items()
                      if member_width_in <= dims.clear_width_in), "")
    if model in LSSR_DIMENSIONS:
        return _lssr_hanger(LSSR_DIMENSIONS[model], slope_radians)
    if model == "IUS":
        model = _ius_model(member_width_in, member_depth_in) or ""
    if model in IUS_DIMENSIONS:
        return _folded_hanger(IUS_DIMENSIONS[model], ius=True)
    if model == "LUS":
        model = _sawn_model("LUS", member_width_in, member_depth_in) or ""
    if model in LUS_DIMENSIONS:
        return _folded_hanger(LUS_DIMENSIONS[model])
    if model == "HHUS410":
        return _folded_hanger(HHUS410_DIMENSIONS)
    if model in ("HU", "HUC"):
        concealed = model == "HUC"
        selected = _sawn_model("HU", member_width_in, member_depth_in)
        return _folded_hanger(HU_DIMENSIONS[selected], concealed=concealed) if selected else None
    if model.startswith("HUC") and not model.startswith("HUCQ"):
        plain_model = "HU" + model[3:]
        if plain_model in HU_DIMENSIONS:
            return _folded_hanger(HU_DIMENSIONS[plain_model], concealed=True)
    if model in HU_DIMENSIONS:
        return _folded_hanger(HU_DIMENSIONS[model])
    if model == "HUCQ":
        selected = _sawn_model("HU", member_width_in, member_depth_in)
        aliases = {"HU210-2": "HUCQ210-2-SDS", "HU212-2": "HUCQ210-2-SDS",
                   "HU210-3": "HUCQ210-3-SDS", "HU212-3": "HUCQ210-3-SDS",
                   "HU48": "HUCQ410-SDS", "HU410": "HUCQ410-SDS",
                   "HU412": "HUCQ412-SDS"}
        model = aliases.get(selected or "", "")
    if model in HUCQ_DIMENSIONS:
        return _folded_hanger(HUCQ_DIMENSIONS[model], concealed=True)
    return None
