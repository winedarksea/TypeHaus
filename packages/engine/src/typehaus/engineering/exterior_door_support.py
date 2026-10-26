"""Door-approach free bodies; member checks never stand in for connection evidence."""

from math import sqrt


def cantilever_support_report(specification, projection_m, tributary_width_m):
    """ASD timber or strength-design concrete strip, with an independent point load.

    The whole concentrated load is assigned to one support. Uniform and point loads
    are combined conservatively; no load sharing or short-duration increase is credited.
    """
    if projection_m <= 0 or tributary_width_m <= 0:
        raise ValueError("support projection and tributary width must be positive")
    length = projection_m / 0.0254
    width = tributary_width_m / 0.0254
    line_load = (specification.live_load_psf + specification.dead_load_psf) * width / 144
    point = specification.concentrated_load_lb
    moment = point * length + line_load * length**2 / 2
    shear = point + line_load * length
    depth = specification.support_depth.meters / 0.0254
    breadth = specification.support_width.meters / 0.0254
    if specification.support_kind == "timber_outriggers":
        section_modulus = breadth * depth**2 / 6
        inertia = breadth * depth**3 / 12
        bending = moment / section_modulus / specification.timber_bending_psi
        shearing = 1.5 * shear / (breadth * depth) / specification.timber_shear_psi
        deflection = (point * length**3 / 3 + line_load * length**4 / 8) / (
            specification.timber_modulus_psi * inertia
        )
        root_couple = moment / (specification.support_backspan.meters / 0.0254)
        result = dict(
            bending_dcr=bending,
            shear_dcr=shearing,
            deflection_in=deflection,
            deflection_limit_in=length / 360,
            root_couple_lb=root_couple,
            connection_demand_lb=max(shear + root_couple, root_couple),
        )
    else:
        # Section feasibility only: hook development and the interface require their own evidence.
        concrete_strength = specification.concrete_strength_psi
        effective_depth = depth - specification.concrete_cover.meters / 0.0254
        effective_depth -= specification.reinforcement_diameter.meters / 0.0254 / 2
        area = specification.reinforcement_area_in2
        steel_strength = specification.reinforcement_yield_psi
        compression_depth = area * steel_strength / (0.85 * concrete_strength * width)
        capacity = 0.9 * area * steel_strength * (effective_depth - compression_depth / 2)
        shear_capacity = 0.75 * 2 * sqrt(concrete_strength) * width * effective_depth
        result = dict(
            bending_dcr=moment / capacity,
            shear_dcr=shear / shear_capacity,
            reinforcement="one #4 top bar per strip; 2 inch cover",
            connection_demand_lb=moment / effective_depth,
            development_status="UNKNOWN: hooked-bar development into monolithic footing",
        )
    cross_width = specification.cross_bearer_width.meters / 0.0254
    cross_depth = specification.cross_bearer_depth.meters / 0.0254
    cross_moment = point * width / 4 + line_load * width**2 / 8
    result["cross_bearer_bending_dcr"] = (
        cross_moment / (cross_width * cross_depth**2 / 6) / specification.timber_bending_psi
    )
    result["cross_bearer_bearing_demand_psi"] = shear / (cross_width * breadth)
    capacity = specification.support_connection_capacity_lb
    result.update(
        projection_in=length,
        tributary_width_in=width,
        service_moment_lb_in=moment,
        service_shear_lb=shear,
        connection_capacity_lb=capacity,
        connection_source=specification.support_connection_source,
        connection_dcr=result["connection_demand_lb"] / capacity if capacity else None,
    )
    member_pass = (
        max(result["bending_dcr"], result["shear_dcr"], result["cross_bearer_bending_dcr"]) <= 1
    )
    if "deflection_in" in result:
        member_pass &= result["deflection_in"] <= result["deflection_limit_in"]
    result["member_status"] = "PASS" if member_pass else "FAIL"
    result["connection_status"] = (
        "UNKNOWN" if capacity is None else ("PASS" if result["connection_dcr"] <= 1 else "FAIL")
    )
    return result
