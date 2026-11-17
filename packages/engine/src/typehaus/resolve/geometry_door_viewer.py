"""DoorScope DS2000 visible trim, in the closed leaf's wall frame.

Basis: metropolitandoor.com/wp-content/uploads/2018/07/door-scope-_cat.pdf
and canaropa.com/wp-content/uploads/N05601_EN.pdf (50.3 mm screen).
The 2-3/8 inch bore is published; flange sizes, projections and optical trim are
photo-proportioned coordination geometry, not fabrication dimensions or optical simulation.
"""
from dataclasses import dataclass
from math import cos, pi, sin

from typehaus.resolve.geometry_ir import GPart, GSweep, PartCatalogRef


@dataclass(frozen=True)
class DoorScopeDimensions:
    bore_diameter_m: float = .060325
    flange_diameter_m: float = .070
    screen_diameter_m: float = .0503
    flange_depth_m: float = .002
    interior_projection_m: float = .0127
    exterior_projection_m: float = .006
    screen_recess_m: float = .002
    optical_surface_depth_m: float = .001
    exterior_aperture_width_m: float = .018
    exterior_aperture_height_m: float = .009
    groove_depth_m: float = .0006
    # Recesses in the exterior optical head, expressed as radii from the bore radius.
    exterior_ring_radius_ratios: tuple[float, ...] = (.88, .70, .52)
    ring_width_m: float = .0015
    facets: int = 64


DOORSCOPE_DIMENSIONS = DoorScopeDimensions()


def doorscope_parts(key, catalog: PartCatalogRef, center, tangent, normal,
                    leaf_thickness, exterior_sign, dimensions=DOORSCOPE_DIMENSIONS):
    """One metal body and opaque optical faces; all remain one purchased accessory."""
    cx, cy, z = center
    metal, optics = [], []

    def sweep(profile, offset, depth, side):
        # (tangent, vertical) has normal -wall-normal. Reverse for an outward extrusion.
        if side > 0:
            profile = tuple(reversed(profile))
        normal_offset = side * (leaf_thickness / 2 + offset)
        return GSweep(tuple((cx + tangent[0] * a + normal[0] * normal_offset,
                             cy + tangent[1] * a + normal[1] * normal_offset, z + h)
                            for a, h in profile),
                      (normal[0] * side * depth, normal[1] * side * depth, 0))

    def circle(radius):
        return tuple((radius * cos(2*pi*i/dimensions.facets),
                      radius * sin(2*pi*i/dimensions.facets))
                     for i in range(dimensions.facets))

    def bezel(outer_radius, inner_radius, offset, depth, side):
        # Two simple half-annuli keep the screen opening real in both swept-solid exporters.
        for half in (0, 1):
            angles = [pi * (half + i/(dimensions.facets//2))
                      for i in range(dimensions.facets//2 + 1)]
            profile = tuple((outer_radius*cos(a), outer_radius*sin(a)) for a in angles)
            profile += tuple((inner_radius*cos(a), inner_radius*sin(a))
                             for a in reversed(angles))
            metal.append(sweep(profile, offset, depth, side))

    bore_radius = dimensions.bore_diameter_m / 2
    screen_radius = dimensions.screen_diameter_m / 2
    for side in (-1, 1):
        metal.append(sweep(circle(dimensions.flange_diameter_m/2), 0,
                           dimensions.flange_depth_m, side))
        if side == exterior_sign:
            metal.append(sweep(circle(bore_radius), dimensions.flange_depth_m,
                               dimensions.exterior_projection_m-dimensions.flange_depth_m, side))
            for ratio in dimensions.exterior_ring_radius_ratios:
                radius = bore_radius * ratio
                bezel(radius, radius-dimensions.ring_width_m,
                      dimensions.exterior_projection_m, dimensions.groove_depth_m, side)
            w, h = dimensions.exterior_aperture_width_m/2, dimensions.exterior_aperture_height_m/2
            optics.append(sweep(((-w, -h), (w, -h), (w, h), (-w, h)),
                                dimensions.exterior_projection_m,
                                dimensions.optical_surface_depth_m, side))
        else:
            bezel(bore_radius, screen_radius, dimensions.flange_depth_m,
                  dimensions.interior_projection_m-dimensions.flange_depth_m, side)
            optics.append(sweep(circle(screen_radius),
                                dimensions.interior_projection_m-dimensions.screen_recess_m,
                                dimensions.optical_surface_depth_m, side))
    return (GPart(key=key, material_key="door_hardware", solids=tuple(metal), catalog=catalog),
            GPart(key=key+":optics", material_key="shadow_gap", solids=tuple(optics),
                  catalog=catalog))
