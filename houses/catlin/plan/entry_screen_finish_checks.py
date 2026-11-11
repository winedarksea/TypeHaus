"""Local screening for the supplemental timber; unresolved attachments block acceptance."""

from plan import entry_screen_finish_spec as spec


def _check(name, demand, capacity, unit, basis):
    ratio = demand / capacity
    return {"name": name, "status": "ok" if ratio <= 1 else "over",
            "demand": demand, "capacity": capacity, "unit": unit, "ratio": ratio, "basis": basis}


def local_timber_checks(wind_pressure_psf):
    """Screen the solid 6x6. The member calculations are conditional on end restraint;
    they do not establish the unverified end connection.
    """
    length = spec.NAILER_TOP_IN - spec.NAILER_BOTTOM_IN
    side = spec.TIMBER_WIDTH_IN
    inertia = side**4 / 12
    section = side**3 / 6
    modulus = spec.SOUTHERN_PINE_TIMBER_E_PSI
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
            _check(f"{name}: 6x6 bending", moment / section,
                   spec.SOUTHERN_PINE_TIMBER_FB_PSI, "psi",
                   "NDS Supplement Table 4D SP No.2 timbers, wet row, Fb=850; CD=1"),
            _check(f"{name}: 6x6 shear", 1.5 * shear / side**2,
                   spec.SOUTHERN_PINE_TIMBER_FV_PSI, "psi",
                   "NDS Table 4D Fv=165, wet row; full point at end bounds reaction"),
            _check(f"{name}: 6x6 deflection", deflection,
                   spec.LOCAL_DEFLECTION_LIMIT_IN, "in", "project 1/4in local limit; wet-row E"),
        ]
    timber_weight = (sum(s.volume_in3 for s in spec.SUPPORTS if s.profile == "6x6")
                     * spec.LB_PER_IN3)
    # Bears on the 3.5in plate only; never use the 5.5in depth or credit the roof.
    plate_contact = spec.STUD_EAST_IN - spec.TIMBER_WEST_IN
    rows.append(_check("timber bottom-plate bearing, self weight",
                       timber_weight / (plate_contact * side),
                       spec.SOUTHERN_PINE_TIMBER_FC_PERP_PSI * spec.WOOD_FC_PERP_WET_FACTOR,
                       "psi", "NDS Table 4D Fc-perp375 x CM0.67; actual 3.5x5.5in contact; "
                       "no roof credit"))
    for name in ("end attachments: installed directions and fit", "local plate load transfer",
                 "end screw penetration, edge distances and cross-grain effects"):
        rows.append({"name": name, "status": "incomplete", "ratio": None,
                     "basis": "; ".join(spec.END_CONNECTION_MISSING)})
    return rows


def support_load_delta():
    """Point-load differences against the previous centre nailer, in wall stations."""
    timber = (sum(s.volume_in3 for s in spec.SUPPORTS if s.profile == "6x6")
              * spec.LB_PER_IN3)
    nailer = spec.PREVIOUS_SUPPORT_WEIGHT_LB / 5
    return ((spec.TIMBER_STATION_IN, timber - nailer),
            *((station, nailer) for identity, station in zip(
                spec.NAILER_IDENTITIES, spec.NAILER_STATIONS_IN, strict=True)
              if identity in (6, 7)))


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
            "acceptance": "incomplete: total sill stress, local plate distribution and hanger "
                          "effects under concentrated loading require verification"}
