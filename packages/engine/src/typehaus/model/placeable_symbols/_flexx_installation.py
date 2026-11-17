"""Pan, pitched rails/cabinet and a fitting-built primary drain in cabinet-local inches.

The nominal type dimensions remain the cabinet, as with the Badger's attached trap.
Installation parts deliberately extend outside it; checks inspect their actual bounds.
The drain is drawn as its fittings: adapter, 90, union, inlet tee + capped cleanout,
two-90 trap and outlet tee + open vent, each hub at its catalogue centre-to-hub length.
"""

import math

from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._gree_flexx import CABINET_IN, FRONT_CONNECTIONS_IN
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

BOX_TRIANGLES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))
TUBE_SIDES = 24
FLOAT_BODY_HEIGHT_IN = 1.5
FLOAT_BRACKET_SHEET_IN = 0.06
#: Roles of the trap assembly proper (inlet tee to outlet tee, cleanout and vent).
TRAP_ROLES = frozenset({"flexx:primary-trap", "flexx:capped-cleanout", "flexx:cleanout-cap",
                        "flexx:downstream-vent"})
#: Every drain role, feeder included; each part joins the collision set on its own.
DRAIN_ROLES = TRAP_ROLES | {"flexx:primary-adapter", "flexx:primary-drain-inlet",
                            "flexx:drain-fitting", "flexx:drain-union",
                            "flexx:secondary-plug"}
PAN_ROLES = frozenset({"flexx:emergency-pan-floor", "flexx:emergency-pan-rim"})


def _transformed_part(part, transform):
    if "mesh" in part:
        vertices = part["mesh"]["positions"]
        triangles = part["mesh"]["triangles"]
    else:
        cx, cy, cz = part["center"]
        sx, sy, sz = part["size"]
        vertices = [(cx + x * sx / 2, cy + y * sy / 2, cz + z * sz / 2)
                    for x, y, z in ((-1, -1, -1), (1, -1, -1), (1, 1, -1),
                                    (-1, 1, -1), (-1, -1, 1), (1, -1, 1),
                                    (1, 1, 1), (-1, 1, 1))]
        triangles = BOX_TRIANGLES
    vertices = [transform(vertex) for vertex in vertices]
    return {**mesh_part(vertices, outward(vertices, triangles), part["color"]),
            "role": part.get("role", "flexx:installation")}


def _frame(start, end):
    axis = tuple(b - a for a, b in zip(start, end, strict=True))
    length = math.sqrt(sum(v * v for v in axis))
    axis = tuple(v / length for v in axis)
    helper = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = (axis[1] * helper[2] - axis[2] * helper[1], axis[2] * helper[0] - axis[0] * helper[2],
         axis[0] * helper[1] - axis[1] * helper[0])
    norm = math.sqrt(sum(v * v for v in u))
    u = tuple(v / norm for v in u)
    v = (axis[1] * u[2] - axis[2] * u[1], axis[2] * u[0] - axis[0] * u[2],
         axis[0] * u[1] - axis[1] * u[0])
    return u, v


def _ring(center, u, v, radius):
    return [tuple(c + radius * (math.cos(a) * du + math.sin(a) * dv)
                  for c, du, dv in zip(center, u, v, strict=True))
            for a in (math.tau * side / TUBE_SIDES for side in range(TUBE_SIDES))]


def _cylinder(start, end, radius, role, color="appliance-white"):
    """Closed round solid on any axis (the sloped feeder included)."""
    u, v = _frame(start, end)
    vertices = [*_ring(start, u, v, radius), *_ring(end, u, v, radius), start, end]
    n = TUBE_SIDES
    triangles = []
    for side in range(n):
        following = (side + 1) % n
        triangles.extend(((side, following, n + side), (following, n + following, n + side),
                          (2 * n, following, side), (2 * n + 1, n + side, n + following)))
    return {**mesh_part(vertices, outward(vertices, triangles), color), "role": role}


def _open_tube(start, end, radius, wall, role, color="appliance-white"):
    """Hollow pipe whose bore stays visible: the vent is open, not capped shut."""
    u, v = _frame(start, end)
    rings = [_ring(start, u, v, radius), _ring(start, u, v, radius - wall),
             _ring(end, u, v, radius), _ring(end, u, v, radius - wall)]
    vertices = [p for ring in rings for p in ring]
    n = TUBE_SIDES
    triangles = []
    for side in range(n):
        following = (side + 1) % n
        for first, second in ((0, 2), (3, 1), (1, 0), (2, 3)):
            a, b = first * n + side, first * n + following
            c, d = second * n + side, second * n + following
            triangles.extend(((a, b, c), (b, d, c)))
    return {**mesh_part(vertices, outward(vertices, triangles), color), "role": role}


def _toward(center, direction, length):
    return tuple(c + d * length for c, d in zip(center, direction, strict=True))


def primary_port_in(spec):
    x, z = FRONT_CONNECTIONS_IN["condensate_primary"][:2]
    return spec.pitched_point_in((x, -CABINET_IN[1] / 2, z))


def drain_parts(spec):
    """The primary feeder, trap, cleanout, vent and secondary plug as fittings."""
    fit = spec.fittings
    s = spec.drain_setout(primary_port_in(spec))
    pipe_r, hub_r = fit.pipe_outer_diameter.inches / 2, fit.hub_outer_diameter.inches / 2
    elbow_h, tee_h = fit.elbow_center_to_hub.inches, fit.tee_center_to_hub.inches
    parts = []

    def hubs(center, directions, length, role):
        parts.extend(_cylinder(center, _toward(center, d, length), hub_r, role)
                     for d in directions)

    south, north, east, west = (0, -1, 0), (0, 1, 0), (1, 0, 0), (-1, 0, 0)
    up, down = (0, 0, 1), (0, 0, -1)
    parts.append(_cylinder(s.port, _toward(s.port, south, fit.adapter_projection.inches),
                           hub_r, "flexx:primary-adapter"))
    for start, end in ((s.port, s.elbow), (s.elbow, s.inlet_tee)):
        parts.append(_cylinder(start, end, pipe_r, "flexx:primary-drain-inlet"))
    hubs(s.elbow, (north, east), elbow_h, "flexx:drain-fitting")
    half = fit.union_length.inches / 2
    parts.append(_cylinder(_toward(s.union, west, half), _toward(s.union, east, half),
                           fit.union_outer_diameter.inches / 2, "flexx:drain-union"))
    hubs(s.inlet_tee, (west, up, down), tee_h, "flexx:drain-fitting")
    # Trap: down the inlet leg, two 90s on a nipple, up to the outlet tee.
    for start, end in ((s.inlet_tee, s.upper_bend), (s.upper_bend, s.lower_bend),
                       (s.lower_bend, s.outlet_tee)):
        parts.append(_cylinder(start, end, pipe_r, "flexx:primary-trap"))
    hubs(s.upper_bend, (up, south), elbow_h, "flexx:primary-trap")
    hubs(s.lower_bend, (north, up), elbow_h, "flexx:primary-trap")
    hubs(s.outlet_tee, (down, up, south), tee_h, "flexx:primary-trap")
    parts.append(_cylinder(s.inlet_tee, s.cleanout_top, pipe_r, "flexx:capped-cleanout"))
    cap_top = _toward(s.cleanout_top, up, fit.cap_length.inches - fit.cap_socket_depth.inches)
    parts.append(_cylinder(_toward(s.cleanout_top, down, fit.cap_socket_depth.inches), cap_top,
                           hub_r, "flexx:cleanout-cap"))
    parts.append(_open_tube(s.outlet_tee, s.vent_top, pipe_r, fit.pipe_wall.inches,
                            "flexx:downstream-vent"))
    # No second line: the secondary connection keeps its plug (envelope: plug_projection).
    x, z = FRONT_CONNECTIONS_IN["condensate_secondary"][:2]
    plug = spec.pitched_point_in((x, -CABINET_IN[1] / 2, z))
    parts.append(_cylinder(plug, _toward(plug, south, fit.plug_projection.inches), hub_r,
                           "flexx:secondary-plug"))
    return parts


def installation_strokes(spec, width, depth):
    sx, sy = width / CABINET_IN[0], depth / CABINET_IN[1]
    s = spec.drain_setout(primary_port_in(spec))
    route = (s.port, s.elbow, s.inlet_tee, s.outlet_tee)
    return (rect(0, 0, spec.pan_width.inches * sx, spec.pan_depth.inches * sy),
            *(line((a[0] * sx, a[1] * sy), (b[0] * sx, b[1] * sy))
              for a, b in zip(route, route[1:], strict=False)))


def installed_flexx_parts(cabinet_parts, spec, width, depth, height):
    scale = tuple(value / reference for value, reference in
                  zip((width, depth, height), CABINET_IN, strict=True))
    # Work in inches before one final scale; the pitch applies to case and markers only.
    parts = [_transformed_part(part, spec.pitched_point_in) for part in cabinet_parts]
    lift = spec.cabinet_lift_in
    floor = -lift
    sheet = spec.pan_sheet.inches
    pw, pd, ph = spec.pan_width.inches, spec.pan_depth.inches, spec.pan_height.inches

    def panel(x, y, z0, z1, dx, dy, role, color="metal"):
        parts.append({**box(x, y, z0, z1, dx, dy, color), "role": "flexx:" + role})

    panel(0, 0, floor, floor + sheet, pw, pd, "emergency-pan-floor")
    for side in (-1, 1):
        panel(side * (pw - sheet) / 2, 0, floor + sheet, floor + ph,
              sheet, pd, "emergency-pan-rim")
        panel(0, side * (pd - sheet) / 2, floor + sheet, floor + ph,
              pw - 2 * sheet, sheet, "emergency-pan-rim")
    # Hollow rectangular rails, with continuous tapered bearing shims.
    rw, wall = spec.rail_width.inches, spec.rail_wall.inches
    rail_floor = floor + sheet
    for center in spec.rail_centers:
        x = center.inches
        for z0, z1 in ((rail_floor, rail_floor + wall), (-wall, 0)):
            panel(x, 0, z0, z1, rw, CABINET_IN[1], "support-rail")
        for side in (-1, 1):
            panel(x + side * (rw - wall) / 2, 0, rail_floor + wall, -wall,
                  wall, CABINET_IN[1], "support-rail")
        # A very thin front bearing avoids a degenerate mesh at the wedge tip.
        wedge = box(x, 0, -wall, 0, rw, CABINET_IN[1], "metal")
        parts.append({**_transformed_part(wedge, lambda p: (
            p[0], p[1], p[2] + (p[2] + wall) / wall * (p[1] + CABINET_IN[1] / 2)
            * spec.cabinet_slope_in_per_ft / 12)), "role": "flexx:pitch-shim"})

    parts.extend(drain_parts(spec))

    # Float switch: conservative body/bracket allowance, not a dimensioned manufacturer body.
    fx = spec.float_switch_x.inches
    fy = -pd / 2 + spec.float_switch_inset.inches
    float_top = floor + sheet + spec.float_trip_depth.inches
    float_bottom = max(floor + sheet, float_top - FLOAT_BODY_HEIGHT_IN)
    depth_ratio = spec.float_switch_depth.inches / spec.float_switch_width.inches
    float_body = _cylinder((fx, fy, float_bottom), (fx, fy, float_top),
                           spec.float_switch_width.inches / 2, "flexx:float-switch")
    parts.append(_transformed_part(float_body, lambda p: (
        p[0], fy + (p[1] - fy) * depth_ratio, p[2])))
    panel(fx, -pd / 2, float_top, floor + spec.float_switch_height.inches,
          spec.float_switch_width.inches, FLOAT_BRACKET_SHEET_IN, "float-bracket")
    panel(fx, (fy - pd / 2) / 2, floor + ph, floor + ph + FLOAT_BRACKET_SHEET_IN,
          spec.float_switch_width.inches, spec.float_switch_inset.inches,
          "float-bracket")
    return tuple(_transformed_part(part, lambda p: tuple(
        coordinate * factor for coordinate, factor in zip(p, scale, strict=True)))
                 for part in parts)
