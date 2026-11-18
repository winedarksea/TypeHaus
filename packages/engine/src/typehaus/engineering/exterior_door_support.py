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
    (``notes/exterior_door_sill_beam.md`` §3). ``None``
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


def sill_beam_report(span_in, width_in, depth_in, modulus_psi, bending_psi, shear_psi,
                     load_lb, deflection_limit_in):
    """A sill beam simply supported between its seats' screw-group centroids, the point at
    midspan for bending and deflection and at a seat for shear
    (``notes/exterior_door_sill_beam.md`` §2)."""
    moment = load_lb * span_in / 4
    bending = moment / (width_in * depth_in**2 / 6) / bending_psi
    shear = 1.5 * load_lb / (width_in * depth_in) / shear_psi
    deflection = load_lb * span_in**3 / (48 * modulus_psi * width_in * depth_in**3 / 12)
    ok = max(bending, shear) <= 1 and deflection <= deflection_limit_in
    return dict(sill_beam_span_in=span_in, sill_beam_moment_lb_in=moment,
                sill_beam_bending_dcr=bending, sill_beam_shear_dcr=shear,
                sill_beam_deflection_in=deflection,
                sill_beam_deflection_limit_in=deflection_limit_in,
                member_status="PASS" if ok else "FAIL")


def screw_spacing_failures(screws, members, spacing):
    """Every published-minimum miss of a screw layout, as messages; empty is a pass.

    ``screws``: ``(station, z, row)`` inches. ``members``: ``(name, s0, s1, z0, z1, loaded)``
    inches, ``loaded`` the edge the screw bears toward in that member (``"top"``/``"bottom"``);
    a member counts for a screw whose station it spans. ``spacing`` is a
    ``hardware.catalog.FastenerSpacing``. Grain runs along the station axis.
    """
    tol = 1e-6
    out = []
    for station, z, row in screws:
        for name, s0, s1, z0, z1, loaded in members:
            if not s0 - tol <= station <= s1 + tol:
                continue
            end = min(station - s0, s1 - station)
            if end < spacing.end_distance - tol:
                out.append(f"row {row} at {station:.3f} in: end distance {end:.3f} in in the "
                           f"{name} < {spacing.end_distance:g} in")
            top, bottom = z1 - z, z - z0
            to_loaded, to_free = (top, bottom) if loaded == "top" else (bottom, top)
            if to_loaded < spacing.loaded_edge - tol:
                out.append(f"row {row} at {station:.3f} in: loaded edge {to_loaded:.3f} in in "
                           f"the {name} < {spacing.loaded_edge:g} in")
            if to_free < spacing.unloaded_edge - tol:
                out.append(f"row {row} at {station:.3f} in: unloaded edge {to_free:.3f} in in "
                           f"the {name} < {spacing.unloaded_edge:g} in")
    rows = {}
    for station, z, row in screws:
        rows.setdefault(row, []).append((station, z))
    for row, items in rows.items():
        stations = sorted(s for s, _ in items)
        for a, b in zip(stations, stations[1:], strict=False):
            if b - a < spacing.in_row_spacing - tol:
                out.append(f"row {row}: in-row spacing {b - a:.3f} in < "
                           f"{spacing.in_row_spacing:g} in")
    # The staggered minimum holds only where neighbouring rows sit half a pitch apart along
    # the grain (Table 5 note 4); closer than that, the in-line minimum applies.
    heights = sorted({round(z, 6) for _, z, _ in screws})
    for a, b in zip(heights, heights[1:], strict=False):
        lower = [s for s, z, _ in screws if abs(z - a) < tol]
        upper = [s for s, z, _ in screws if abs(z - b) < tol]
        offset = min(abs(p - q) for p in lower for q in upper)
        staggered = offset >= spacing.in_row_spacing / 2 - tol
        minimum = spacing.row_spacing if staggered else spacing.in_line_row_spacing
        if b - a < minimum - tol:
            out.append(f"{'staggered' if staggered else 'in-line'} row spacing {b - a:.3f} in "
                       f"< {minimum:g} in")
    return out


def foam_bed_support_report(specification):
    """A tread laid continuously on rated foam, not fastened to anything.

    The concentrated load spreads over a square of the tread's own width — through a bearing
    plate where one is authored, else through the board's own underside, which a profiled
    board only earns with an authored contact area (UNKNOWN without one). The uniform live +
    dead load is added on top. Allowable is the foam's rated psi over the creep divisor.
    There is no root connection and no bar to develop, so neither is UNKNOWN.
    """
    width = specification.approach_board_width.meters / 0.0254
    contact = specification.approach_contact_area_in2
    if specification.bearing_plate_material_ref is not None:
        area, basis = width * width, "bearing plate over the full footprint"
    elif contact is not None:
        area, basis = min(contact, width * width), "authored contact area"
    elif specification.approach_profiled_underside:
        return dict(spread_area_in2=None, bearing_psi=None, bearing_dcr=None,
                    spread_basis="profiled underside, no plate or contact area",
                    connection_demand_lb=0.0, connection_capacity_lb=None,
                    connection_source=None, connection_dcr=None,
                    member_status="UNKNOWN", connection_status="NOT_APPLICABLE")
    else:
        area, basis = width * width, "flat underside over the full footprint"
    uniform = (specification.live_load_psf + specification.dead_load_psf) / 144
    bearing = specification.concentrated_load_lb / area + uniform
    allowable = specification.foam_rated_psi / specification.foam_creep_divisor
    return dict(
        spread_area_in2=area,
        spread_basis=basis,
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
