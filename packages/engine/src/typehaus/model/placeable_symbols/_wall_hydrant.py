"""Woodford Model 19 exterior trim and concealed barrel; local -Y faces outdoors."""

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, circle, rect
from typehaus.model.placeable_symbols._hose_hardware import hose_thread
from typehaus.model.placeable_symbols._hydrant_hardware import side_profile
from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.model.placeable_symbols._wall_hydrant_config import MODEL_19
from typehaus.quantities import M_PER_IN


def _transform(part: Part, scale, origin=(0.0, 0.0, 0.0), *, wheel=False) -> Part:
    """Scale analytic normals inversely; wheel turns a Z-axis ring onto the stem."""
    def orient(point):
        return (point[0], -point[2], point[1]) if wheel else point

    mesh = part['mesh']
    positions = tuple(tuple(v * s + o for v, s, o in zip(orient(p), scale, origin, strict=True))
                      for p in mesh['positions'])
    normals = []
    for normal in mesh['normals']:
        vector = tuple(v / s for v, s in zip(orient(normal), scale, strict=True))
        length = math.sqrt(sum(v * v for v in vector))
        normals.append(tuple(v / length for v in vector))
    minimum = tuple(min(p[i] for p in positions) for i in range(3))
    maximum = tuple(max(p[i] for p in positions) for i in range(3))
    return {**part, 'center': tuple((a + b) / 2 for a, b in zip(minimum, maximum, strict=True)),
            'size': tuple(b - a for a, b in zip(minimum, maximum, strict=True)),
            'mesh': {**mesh, 'positions': positions, 'normals': tuple(normals)}}


def wall_hydrant(width: float, depth: float, height: float) -> Geometry:
    """The rear edge is the inlet seat; the flange is one barrel length forward."""
    d = MODEL_19
    rear = d.depth / 2
    wall = rear - d.barrel_length
    axis = d.barrel_axis_height

    def cylinder(x, y, z, diameter, length, *, axis=2, color='brass'):
        return round_cylinder(tuple(v * M_PER_IN for v in (x, y, z)),
                              diameter * M_PER_IN / 2, length * M_PER_IN,
                              axis=axis, color=color)

    parts = [
        cylinder(0, (rear + wall) / 2, axis, d.barrel_diameter,
                 d.barrel_length, axis=1),
        cylinder(0, rear - d.inlet_length / 2, axis, d.inlet_diameter,
                 d.inlet_length, axis=1),
    ]
    flange = cylinder(0, wall - d.flange_thickness / 2, axis, d.flange_width,
                      d.flange_thickness, axis=1, color='plastic-white')
    # Oval flange and wheel preserve their open/round sections at any preview size.
    parts.append(_transform(flange, (1, 1, d.flange_height / d.flange_width),
                            (0, 0, axis * (1 - d.flange_height / d.flange_width) * M_PER_IN)))
    profile = tuple((wall - forward, axis + z) for forward, z in d.casting_profile)
    parts.extend((side_profile(profile, d.casting_width, 'brass'),
                  cylinder(0, wall - d.body_length / 2, axis, d.body_diameter,
                           d.body_length, axis=1),
                  cylinder(0, wall - d.body_length - d.packing_length / 2, axis,
                           d.packing_diameter, d.packing_length, axis=1),
                  cylinder(0, wall - (d.body_length + d.handle_forward) / 2, axis,
                           d.stem_diameter, d.handle_forward - d.body_length, axis=1)))
    for sign in (-1, 1):
        parts.append(cylinder(sign * d.mounting_screw_spacing / 2,
                              wall - d.flange_thickness, axis, d.mounting_screw_diameter,
                              d.mounting_screw_length, axis=1, color='metal'))
    handle_y = wall - d.handle_forward
    ring = hose_thread((0, 0, 0), d.handle_height, d.handle_opening_diameter * d.handle_height,
                       d.handle_thickness, color='metal-black')
    parts.append(_transform(ring, (d.handle_width / d.handle_height, 1, 1),
                            (0, handle_y * M_PER_IN, axis * M_PER_IN), wheel=True))
    parts.append(cylinder(0, handle_y, axis, d.handle_hub_diameter,
                          d.handle_thickness, axis=1, color='metal-black'))
    # The crossbar leaves two clear finger openings in the oval wheel.
    parts.append(side_profile(((handle_y - d.handle_thickness / 2,
                                axis - d.handle_spoke_width / 2),
                               (handle_y + d.handle_thickness / 2,
                                axis - d.handle_spoke_width / 2),
                               (handle_y + d.handle_thickness / 2,
                                axis + d.handle_spoke_width / 2),
                               (handle_y - d.handle_thickness / 2,
                                axis + d.handle_spoke_width / 2)),
                              d.handle_width, 'metal-black'))
    parts.append(cylinder(0, handle_y - d.handle_thickness / 2, axis,
                          d.handle_screw_diameter, d.handle_screw_length, axis=1, color='metal'))
    breaker_bottom = axis + d.breaker_base_height
    parts.extend((cylinder(0, wall - d.breaker_forward, breaker_bottom + d.breaker_height / 2,
                           d.breaker_diameter, d.breaker_height),
                  cylinder(0, wall - d.breaker_forward,
                           breaker_bottom + d.breaker_height - d.breaker_cap_height / 2,
                           d.breaker_diameter, d.breaker_cap_height, color='metal-black'),
                  hose_thread((0, wall - d.nozzle_forward,
                               d.nozzle_bottom + d.nozzle_thread_length + d.nozzle_neck_length / 2),
                              d.nozzle_neck_diameter, d.hose_bore_diameter,
                              d.nozzle_neck_length),
                  hose_thread((0, wall - d.nozzle_forward,
                               d.nozzle_bottom + d.nozzle_thread_length / 2),
                              d.hose_thread_diameter, d.hose_bore_diameter,
                              d.nozzle_thread_length)))
    scale = (width / (d.width * M_PER_IN), depth / (d.depth * M_PER_IN),
             height / (d.height * M_PER_IN))
    scaled_parts = tuple(_transform(part, scale) for part in parts)
    # Plan strokes depend only on W/D, as required by the plan-symbol API.
    strokes = (rect(0, (wall + rear) / 2 * M_PER_IN, d.barrel_diameter * M_PER_IN,
                    d.barrel_length * M_PER_IN, fill='brass'),
               rect(0, wall * M_PER_IN, d.flange_width * M_PER_IN,
                    d.flange_thickness * M_PER_IN, fill='plastic-white'),
               rect(0, handle_y * M_PER_IN, d.handle_width * M_PER_IN,
                    d.handle_thickness * M_PER_IN, fill='metal-black'),
               circle(0, (wall - d.breaker_forward) * M_PER_IN,
                      d.breaker_diameter * M_PER_IN / 2),
               circle(0, (wall - d.nozzle_forward) * M_PER_IN,
                      d.hose_thread_diameter * M_PER_IN / 2))
    return tuple({**stroke, 'points': tuple((x * scale[0], y * scale[1])
                                            for x, y in stroke['points'])}
                 for stroke in strokes), scaled_parts
