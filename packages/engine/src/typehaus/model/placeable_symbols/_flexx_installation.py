"""Pan, pitched rails/cabinet and a trapped primary drain in cabinet-local inches.

The nominal type dimensions remain the cabinet, as with the Badger's attached trap.
Installation parts deliberately extend outside it; checks inspect their actual bounds.
"""

import math

from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._gree_flexx import CABINET_IN, FRONT_CONNECTIONS_IN
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

BOX_TRIANGLES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))
CURVE_SEGMENTS = 16
TUBE_SIDES = 24
FLOAT_BODY_HEIGHT_IN = 1.5
FLOAT_BRACKET_SHEET_IN = 0.06


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


def _trap_return(spec, inlet_z):
    """Round U-bend: outlet to bottom is the specified seal depth, not overall drop."""
    x, y = spec.trap_inlet_x.inches, spec.trap_inlet_y.inches
    outlet_z = inlet_z - spec.trap_outlet_drop.inches
    radius = spec.trap_leg_spacing.inches / 2
    bend_z = outlet_z - spec.trap_seal_depth.inches + radius
    stations = [(y, inlet_z, 0), (y, bend_z, 0)]
    for step in range(1, CURVE_SEGMENTS + 1):
        angle = math.pi * step / CURVE_SEGMENTS
        stations.append((y - radius * (1 - math.cos(angle)),
                         bend_z - radius * math.sin(angle), angle))
    stations.append((y - 2 * radius, outlet_z, math.pi))
    # Hollow tube leaves its bore visible rather than capping the trap and vent shut.
    # Field-fabricated elbows occupy more than bare pipe at the lowest point.
    outer_radius = spec.fitting_outer_diameter.inches / 2
    inner_radius = spec.pipe_outer_diameter.inches / 2 - spec.pipe_wall.inches
    vertices, triangles = [], []
    for tube_radius in (outer_radius, inner_radius):
        for sy, sz, tangent in stations:
            for side in range(TUBE_SIDES):
                angle = math.tau * side / TUBE_SIDES
                vertices.append((x + tube_radius * math.cos(angle),
                                 sy + tube_radius * math.cos(tangent) * math.sin(angle),
                                 sz - tube_radius * math.sin(tangent) * math.sin(angle)))
    layer = len(stations) * TUBE_SIDES
    for offset, reverse in ((0, False), (layer, True)):
        for station in range(len(stations) - 1):
            for side in range(TUBE_SIDES):
                a = offset + station * TUBE_SIDES + side
                b = offset + station * TUBE_SIDES + (side + 1) % TUBE_SIDES
                faces = ((a, b, a + TUBE_SIDES), (b, b + TUBE_SIDES, a + TUBE_SIDES))
                triangles.extend(tuple(reversed(face)) if reverse else face for face in faces)
    for station in (0, len(stations) - 1):
        for side in range(TUBE_SIDES):
            a = station * TUBE_SIDES + side
            b = station * TUBE_SIDES + (side + 1) % TUBE_SIDES
            faces = ((a, b, b + layer), (a, b + layer, a + layer))
            triangles.extend(tuple(reversed(face)) if station == 0 else face for face in faces)
    return {**mesh_part(vertices, outward(vertices, triangles), "appliance-white"),
            "role": "flexx:primary-trap"}


def _open_vertical_tube(start, end, radius, wall):
    vertices, triangles = [], []
    for z in (start[2], end[2]):
        for r in (radius, radius - wall):
            vertices.extend((start[0] + r * math.cos(math.tau * side / TUBE_SIDES),
                             start[1] + r * math.sin(math.tau * side / TUBE_SIDES), z)
                            for side in range(TUBE_SIDES))
    for side in range(TUBE_SIDES):
        following = (side + 1) % TUBE_SIDES
        for first, second in ((0, 2), (3, 1), (1, 0), (2, 3)):
            a, b = first * TUBE_SIDES + side, first * TUBE_SIDES + following
            c, d = second * TUBE_SIDES + side, second * TUBE_SIDES + following
            triangles.extend(((a, b, c), (b, d, c)))
    return mesh_part(vertices, outward(vertices, triangles), "appliance-white")


def installation_strokes(spec, width, depth):
    sx, sy = width / CABINET_IN[0], depth / CABINET_IN[1]
    x, y = spec.trap_inlet_x.inches, spec.trap_inlet_y.inches
    primary_x = FRONT_CONNECTIONS_IN["condensate_primary"][0]
    return (rect(0, 0, spec.pan_width.inches * sx, spec.pan_depth.inches * sy),
            line((primary_x * sx, -depth / 2), (primary_x * sx, y * sy)),
            line((primary_x * sx, y * sy), (x * sx, y * sy)),
            line((x * sx, y * sy), (x * sx, (y - spec.trap_leg_spacing.inches) * sy)))


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
    # Hollow 3 x 1.5 x 1/8 rectangular rails, with continuous tapered bearing shims.
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

    primary_x, primary_z = FRONT_CONNECTIONS_IN["condensate_primary"][:2]
    primary = spec.pitched_point_in((primary_x, -CABINET_IN[1] / 2, primary_z))
    tx, ty = spec.trap_inlet_x.inches, spec.trap_inlet_y.inches
    inlet_z = primary[2]
    pipe_radius = spec.pipe_outer_diameter.inches / 2

    def pipe(start, end, role, radius=pipe_radius, *, open_bore=False):
        axes = [index for index in range(3) if abs(end[index] - start[index]) > 1e-9]
        if not axes:
            return  # A tee may coincide with the inlet elbow in a revised setout.
        axis, = axes
        part = round_cylinder(tuple((a + b) / 2 for a, b in zip(start, end, strict=True)),
                              radius, abs(end[axis] - start[axis]), axis=axis,
                              color="appliance-white")
        if open_bore:
            part = _open_vertical_tube(start, end, radius, spec.pipe_wall.inches)
        parts.append({**part, "role": "flexx:" + role})

    elbow = (primary[0], primary[1] - spec.primary_elbow_offset.inches, inlet_z)
    east_elbow = (tx, elbow[1], inlet_z)
    pipe(primary, elbow, "primary-drain-inlet")
    pipe(elbow, east_elbow, "primary-drain-inlet")
    pipe(east_elbow, (tx, ty, inlet_z), "primary-drain-inlet")
    # Oversized fitting envelopes reserve the tee/elbow bulk as well as bare pipe.
    fitting_radius = spec.fitting_outer_diameter.inches / 2
    for x, y, z in (elbow, east_elbow, (tx, ty, inlet_z), spec.trap_outlet_in(inlet_z)):
        pipe((x, y, z - fitting_radius), (x, y, z + fitting_radius),
             "drain-fitting", fitting_radius)
    parts.append(_trap_return(spec, inlet_z))
    pipe((tx, ty, inlet_z), (tx, ty, inlet_z + spec.cleanout_rise_above_inlet.inches),
         "capped-cleanout")
    panel(tx, ty, inlet_z + spec.cleanout_rise_above_inlet.inches,
          inlet_z + spec.cleanout_rise_above_inlet.inches + wall,
          2 * fitting_radius, 2 * fitting_radius, "cleanout-cap", "appliance-white")
    outlet = spec.trap_outlet_in(inlet_z)
    pipe(outlet, (*outlet[:2], inlet_z + spec.vent_rise_above_inlet.inches),
         "downstream-vent", open_bore=True)

    # SS3 97089: conservative body/bracket allowance, not a dimensioned manufacturer body.
    fx = spec.float_switch_x.inches
    fy = -pd / 2 + spec.float_switch_inset.inches
    float_top = floor + sheet + spec.float_trip_depth.inches
    float_bottom = max(floor + sheet, float_top - FLOAT_BODY_HEIGHT_IN)
    float_body = round_cylinder((fx, fy, (float_bottom + float_top) / 2),
                                spec.float_switch_width.inches / 2,
                                float_top - float_bottom, axis=2, color="appliance-white")
    parts.append({**_transformed_part(float_body, lambda p: (
        p[0], fy + (p[1] - fy) * spec.float_switch_depth.inches / spec.float_switch_width.inches,
        p[2])), "role": "flexx:float-switch"})
    panel(fx, -pd / 2, float_top, floor + spec.float_switch_height.inches,
          spec.float_switch_width.inches, FLOAT_BRACKET_SHEET_IN, "float-bracket")
    panel(fx, (fy - pd / 2) / 2, floor + ph, floor + ph + FLOAT_BRACKET_SHEET_IN,
          spec.float_switch_width.inches, spec.float_switch_inset.inches,
          "float-bracket")
    return tuple(_transformed_part(part, lambda p: tuple(
        coordinate * factor for coordinate, factor in zip(p, scale, strict=True)))
                 for part in parts)
