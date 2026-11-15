"""Door-approach free bodies; member checks never stand in for connection evidence."""

from math import ceil, sqrt

import numpy as np

#: NDS 2018 §11.3.6 load/slip modulus, wood-to-metal: γ = 270,000 D^1.5 lb/in. Stiffer than
#: this wood-to-wood joint, which concentrates a point load on the nearest screw: a bound.
_SLIP_MODULUS_COEFFICIENT = 270_000.0
#: Point-load scan step along a girt sill course, plus every screw station and both ends.
_SCAN_STEP_IN = 0.25


def girt_course_screw_shares(length_in, screws_in, diameter_in, modulus_psi, inertia_in4,
                             load_lb):
    """``(worst screw lb, load station in, screw station in)`` for a point load anywhere.

    A free-ended Euler-Bernoulli course on one vertical spring per screw
    (``notes/exterior_door_structural_mount.md``, "Girt sill course connection"). ``None``
    when fewer than two distinct screw stations leave the course unstable.
    """
    stations = sorted({round(x, 6) for x in screws_in})
    if len(stations) < 2:
        return None
    steps = max(1, ceil(length_in / _SCAN_STEP_IN))
    nodes = sorted({0.0, round(length_in, 6), *stations,
                    *(round(length_in * i / steps, 6) for i in range(steps + 1))})
    index = {x: i for i, x in enumerate(nodes)}
    k = _slip_modulus_lb_per_in(diameter_in)
    ei = modulus_psi * inertia_in4
    dof = 2 * len(nodes)
    stiffness = np.zeros((dof, dof))
    for i in range(len(nodes) - 1):
        span = nodes[i + 1] - nodes[i]
        block = ei / span**3 * np.array([
            [12, 6 * span, -12, 6 * span], [6 * span, 4 * span**2, -6 * span, 2 * span**2],
            [-12, -6 * span, 12, -6 * span], [6 * span, 2 * span**2, -6 * span, 4 * span**2]])
        stiffness[2 * i:2 * i + 4, 2 * i:2 * i + 4] += block
    rows = [2 * index[round(x, 6)] for x in screws_in]
    for row in rows:
        stiffness[row, row] += k
    loads = np.zeros((dof, len(nodes)))
    loads[[2 * i for i in range(len(nodes))], range(len(nodes))] = load_lb
    try:
        displacement = np.linalg.solve(stiffness, loads)
    except np.linalg.LinAlgError:
        return None
    forces = k * displacement[rows, :]
    screw, load = np.unravel_index(int(np.argmax(forces)), forces.shape)
    return float(forces[screw, load]), nodes[load], float(screws_in[screw])


def _slip_modulus_lb_per_in(diameter_in):
    return _SLIP_MODULUS_COEFFICIENT * diameter_in**1.5


def girt_course_connection_report(length_in, screws_in, diameter_in, modulus_psi,
                                  inertia_in4, load_lb, capacity_lb, source):
    """The worst screw share against the screw's lateral capacity, as report fields."""
    shares = girt_course_screw_shares(length_in, screws_in, diameter_in, modulus_psi,
                                      inertia_in4, load_lb)
    if shares is None:
        return dict(connection_status="UNKNOWN", connection_demand_lb=None,
                    connection_capacity_lb=capacity_lb, connection_dcr=None,
                    connection_source=source)
    worst, load_at, screw_at = shares
    dcr = worst / capacity_lb
    return dict(connection_status="PASS" if dcr <= 1 else "FAIL",
                connection_demand_lb=worst, connection_capacity_lb=capacity_lb,
                connection_dcr=dcr, connection_source=source,
                girt_course_length_in=length_in, girt_course_screws=len(screws_in),
                girt_course_load_at_in=load_at, girt_course_worst_screw_at_in=screw_at)


def foam_bed_support_report(specification):
    """A tread laid continuously on rated foam, not fastened to anything.

    The concentrated load spreads over a square of the tread's own width; the uniform
    live + dead load is added on top. Allowable is the foam's rated psi over the creep
    divisor. There is no root connection and no bar to develop, so neither is UNKNOWN.
    """
    width = specification.approach_board_width.meters / 0.0254
    area = width * width
    uniform = (specification.live_load_psf + specification.dead_load_psf) / 144
    bearing = specification.concentrated_load_lb / area + uniform
    allowable = specification.foam_rated_psi / specification.foam_creep_divisor
    return dict(
        spread_area_in2=area,
        uniform_psi=uniform,
        bearing_psi=bearing,
        allowable_psi=allowable,
        bearing_dcr=bearing / allowable,
        connection_demand_lb=0.0,
        connection_capacity_lb=None,
        connection_source=None,
        connection_dcr=None,
        member_status="PASS" if bearing <= allowable else "FAIL",
        connection_status="NOT_APPLICABLE",
    )


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
