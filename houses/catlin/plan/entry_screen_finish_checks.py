"""Local screening for the supplemental timber; unresolved attachments block acceptance."""

from plan import entry_screen_finish_spec as spec


def _check(name, demand, capacity, unit, basis):
    ratio = demand / capacity
    return {"name": name, "status": "ok" if ratio <= 1 else "over",
            "demand": demand, "capacity": capacity, "unit": unit, "ratio": ratio, "basis": basis}


def local_timber_checks(wind_pressure_psf):
    """Do not credit composite bending, screw slip stiffness or equal ply sharing.

    Each load case is applied in full to a single ply; the member calculations are
    conditional on end restraint. They do not establish the unverified end connection.
    """
    length = spec.NAILER_TOP_IN - spec.NAILER_BOTTOM_IN
    width, depth = spec.TIMBER_WIDTH_IN, spec.TIMBER_PLY_THICKNESS_IN
    inertia = width * depth**3 / 12
    section = width * depth**2 / 6
    modulus = spec.SOUTHERN_PINE_2X6_E_PSI * spec.WOOD_E_WET_FACTOR
    point = max(spec.GUARD_CONCENTRATED_LB, spec.GUARD_INFILL_PSF * spec.GUARD_INFILL_AREA_FT2)
    wind_line = wind_pressure_psf * spec.WIND_TRIBUTARY_WIDTH_IN / 144
    rows = []
    for name, moment, shear, deflection in (
        ("guard concentrated/infill", point * length / 4, point,
         point * length**3 / (48 * modulus * inertia)),
        ("out-of-plane wind", wind_line * length**2 / 8, wind_line * length / 2,
         5 * wind_line * length**4 / (384 * modulus * inertia)),
    ):
        rows += [
            _check(f"{name}: single-ply bending", moment / section,
                   spec.SOUTHERN_PINE_2X6_FB_PSI, "psi",
                   "NDS Supplement Table 4B SP No.2 2x6 Fb=1000; wet Fb factor 1 "
                   "where Fb<=1150, CD=1, CL=1 for this 5.5x1.5 flatwise orientation; no sharing"),
            _check(f"{name}: single-ply shear", 1.5 * shear / (width * depth),
                   spec.SOUTHERN_PINE_FV_PSI * spec.WOOD_FV_WET_FACTOR, "psi",
                   "NDS Table 4B Fv=175, wet CM=0.97; full point at end bounds reaction"),
            _check(f"{name}: single-ply deflection", deflection,
                   spec.LOCAL_DEFLECTION_LIMIT_IN, "in", "project 1/4in local limit; wet E=0.9E"),
        ]
    penetration = min(spec.PLY_SCREW_THREAD_IN,
                      spec.PLY_SCREW_LENGTH_IN - depth)
    withdrawal = min(penetration * spec.PLY_SCREW_WITHDRAWAL_LB_IN,
                     spec.PLY_SCREW_WITHDRAWAL_MAX_LB) * spec.SCREW_WET_FACTOR
    # Report ONE screw, without an unsupported equal-distribution assumption. A group
    # calculation may resolve this failure, but dividing by four would conceal it.
    rows.append(_check("ply transfer: one screw, full load envelope", point, withdrawal, "lb",
                       "ER-192 Table 7: 164 lb/in, Wmax245, actual 1.5in side-grain thread, "
                       "CM0.7, CD1.0; no unverified group distribution"))
    for index, offsets in enumerate(spec.PLY_SCREW_OFFSETS_IN, 1):
        rows += [
            _check(f"interface {index}: screw end distance", spec.PLY_SCREW_MIN_END_IN,
                   min(min(offsets), length - max(offsets)), "in", "ER-192 Table 8"),
            _check(f"interface {index}: screw row spacing", spec.PLY_SCREW_MIN_SPACING_IN,
                   min(b - a for a, b in zip(offsets, offsets[1:])), "in", "ER-192 Table 8"),
        ]
    rows.append(_check("screw edge distance", spec.PLY_SCREW_MIN_EDGE_IN, width / 2,
                       "in", "ER-192 Table 8"))
    timber_weight = sum(s.volume_in3 for s in spec.SUPPORTS if s.profile == "2x6") * spec.LB_PER_IN3
    # East ply bears only 0.5in on the existing 3.5in plate; never use the 4.5in pack
    # width as bearing area or count the timber as supporting the roof.
    east_ply_bearing = 77.125 - (spec.TIMBER_EAST_IN - depth)
    rows.append(_check("east-ply bottom-plate bearing, self weight",
                       timber_weight / spec.TIMBER_PLY_COUNT / (east_ply_bearing * width),
                       spec.SOUTHERN_PINE_FC_PERP_PSI * spec.WOOD_FC_PERP_WET_FACTOR, "psi",
                       "NDS Table 4B Fc-perp565 x CM0.67; actual 0.5x5.5in contact; no roof credit"))
    for name in ("end attachments: installed directions and fit", "local plate load transfer",
                 "end screw penetration, edge distances and cross-grain effects"):
        rows.append({"name": name, "status": "incomplete", "ratio": None,
                     "basis": "; ".join(spec.END_CONNECTION_MISSING)})
    return rows


def support_load_delta():
    """Point-load differences against the previous centre nailer, in wall stations."""
    timber = sum(s.volume_in3 for s in spec.SUPPORTS if s.profile == "2x6") * spec.LB_PER_IN3
    nailer = spec.PREVIOUS_SUPPORT_WEIGHT_LB / 5
    return ((spec.TIMBER_STATION_IN, timber - nailer),
            *((station, nailer) for identity, station in zip(
                spec.NAILER_IDENTITIES, spec.NAILER_STATIONS_IN, strict=True) if identity in (6, 7)))


def concentrated_sill_delta(model):
    """Additional dead-load moment/reactions, separately from averaged wall mass.

    Simple span is the sill's existing hanger support condition. These are incremental
    gravity effects only; existing total-load and connection checks remain prerequisites.
    """
    sill = model.plan.by_tag("BM-BW-SCSILL")
    endpoints = [model.plan.by_tag(tag).position.xy_m for tag in (sill.start_node, sill.end_node)]
    wall = model.wall("W-BW-SCREEN")
    south = min(point[1] for point in endpoints) / 0.0254 - wall.axis[0][1] / 0.0254
    north = max(point[1] for point in endpoints) / 0.0254 - wall.axis[0][1] / 0.0254
    length = north - south
    loads = support_load_delta()
    left = sum(load * (north - station) / length for station, load in loads)
    right = sum(load * (station - south) / length for station, load in loads)
    moments = [(station, left * (station - south)
                - sum(load * max(0, station - at) for at, load in loads)) for station, _ in loads]
    return {"basis": "incremental supplemental wood only; no double addition to wall-line weight",
            "point_loads": [{"station_in": station, "load_lb": load} for station, load in loads],
            "span_in": length, "additional_south_reaction_lb": left,
            "additional_north_reaction_lb": right,
            "maximum_additional_moment_lb_in": max(moment for _, moment in moments),
            "acceptance": "incomplete: total sill stress, local plate distribution and hanger effects "
                          "under concentrated loading require verification"}
