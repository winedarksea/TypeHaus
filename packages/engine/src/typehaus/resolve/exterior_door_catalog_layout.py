"""Catalog installation datums derived once for geometry and clearance reports."""

from dataclasses import dataclass
from math import ceil, radians, tan

_IN = 0.0254


@dataclass(frozen=True)
class CatalogInstallationLayout:
    start: float
    base: float
    seat: float
    sill_end: float
    end: float
    outlet: float
    landing_gap: float | None
    landing_edge: float | None
    crest: float
    width: float
    unit_width: float
    membrane: float
    slope: float
    approach_back: float
    approach_front: float
    thickness: float
    board_count: int
    apron_back: float
    pan_front: float
    pan_back: float
    count: int
    spacing: float
    projection: float
    support_top: float


def catalog_installation_layout(model, wall, opening, assembly, clad):
    placement = assembly.exterior_placement
    installation = placement.specification
    spec = installation.catalog_installation
    sign = placement.outward_sign
    inner = sign * placement.frame_inner_m
    # Keep the back of the factory sill clear of the pan's upstand.
    start = inner + installation.wrap_isolation_thickness.meters
    base = assembly.rough_opening_z_m
    seat = base + spec.pan_height.meters
    sill_end = start + max(x for x, _ in spec.sill_outline_m)
    end = sill_end + spec.sill_extender_depth.meters
    outlet = sign * clad + installation.casing_thickness.meters
    outlet += installation.drainage_gap.meters / 4
    exterior = assembly.adjacent_floors[0 if sign < 0 else 1]
    landing_gap = None
    landing_edge = None
    floor = next((f for f in model.floors if exterior and f.tag == exterior.deck_tag), None)
    if floor is not None:
        from shapely.geometry import LineString, Polygon

        from typehaus.resolve.geometry import opening_center, wall_frame

        center = opening_center(wall, opening)
        _, _, normal, _ = wall_frame(wall)
        ray = LineString(
            [
                (center[0] + normal[0] * sign * d, center[1] + normal[1] * sign * d)
                for d in (outlet, outlet + installation.landing_search.meters)
            ]
        )
        crossing = Polygon(floor.deck_outline, holes=list(floor.deck_voids)).intersection(ray)
        if not crossing.is_empty:
            depths = [
                sign * sum((p[i] - center[i]) * normal[i] for i in (0, 1))
                for line in getattr(crossing, "geoms", (crossing,))
                for p in getattr(line, "coords", ())
            ]
            if depths:
                edge = min(depths)
                landing_edge = edge
                outlet = max(outlet, edge - installation.drainage_gap.meters)
                landing_gap = edge - outlet
    crest = seat + max(z for _, z in spec.sill_outline_m)
    width = opening.width_m - 2 * installation.return_thickness.meters
    product = next(t for t in model.plan.library.door_types if t.tag == opening.type_ref)
    unit_width = (
        product.catalog_dimensions.unit_width.meters if product.catalog_dimensions else width
    )
    membrane = installation.wrap_isolation_thickness.meters
    nose = (
        max(z for x, z in spec.sill_outline_m if x > 0.95 * max(x for x, _ in spec.sill_outline_m))
        + seat
    )
    if spec.sill_extender_ref:
        extension_drop = spec.sill_extender_depth.meters * tan(
            radians(spec.sill_extender_slope_degrees)
        )
        extension_top = spec.sill_extender_height.meters - extension_drop
        nose = seat + extension_top
    slope = spec.approach_slope_ratio
    approach_back = max(seat + 0.5 * _IN, nose)
    approach_front = approach_back - (outlet - end) * slope
    thickness = spec.approach_thickness.meters
    board_count = ceil(width / spec.approach_board_width.meters)
    # Drop the apron below the approach/bearers without burying the sill's level bearing.
    apron_back = (
        approach_front
        - thickness
        - spec.cross_bearer_depth.meters
        - spec.minimum_drainage_clearance.meters
        - membrane
    )
    pan_front = apron_back - (outlet - end) * slope
    pan_back = base + spec.pan_height.meters - membrane
    count = max(2, ceil(width / spec.support_spacing.meters) + 1)
    spacing = (width - spec.support_width.meters) / (count - 1)
    projection = outlet - sign * placement.frame_outer_m
    support_top = pan_front - membrane
    return CatalogInstallationLayout(
        start,
        base,
        seat,
        sill_end,
        end,
        outlet,
        landing_gap,
        landing_edge,
        crest,
        width,
        unit_width,
        membrane,
        slope,
        approach_back,
        approach_front,
        thickness,
        board_count,
        apron_back,
        pan_front,
        pan_back,
        count,
        spacing,
        projection,
        support_top,
    )
