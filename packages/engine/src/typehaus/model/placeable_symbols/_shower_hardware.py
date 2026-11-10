"""Recognizable shower parts from shared stations; shape allowances are illustrative."""

import math

from typehaus.model.placeable_symbols._frame import Part, box
from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.model.shower_assembly import ShowerAssemblySpec
from typehaus.quantities import M_PER_IN

# Illustrative envelopes, not manufacturer rough-in dimensions (inches).
PLATE_RADIUS = 3.25
PLATE_THICKNESS = 0.25
HANDLE_PROJECTION = 2.25
ARM_PROJECTION = 8.0
HEAD_RADIUS = 3.375
HEAD_THICKNESS = 1.0
PIPE_RADIUS = 0.3125
HOSE_SEGMENTS = 24
HOSE_DROP = 26.0


def shower_hardware_parts(spec: ShowerAssemblySpec) -> tuple[Part, ...]:
    nx, ny = spec.wall_direction
    wall_axis = 0 if nx else 1
    parts: list[Part] = []
    color = spec.finish

    def cylinder(name, point, radius, length, axis, finish=color):
        part = round_cylinder(point, radius * M_PER_IN, length * M_PER_IN,
                              axis=axis, color=finish)
        part["role"] = f"shower:{name}"
        parts.append(part)

    def pipe(name, start, end, radius=PIPE_RADIUS, finish=color):
        # Axis-aligned risers and arms; short hose links use their enclosing solids.
        center = tuple((a + b) / 2 for a, b in zip(start, end, strict=True))
        delta = tuple(abs(a - b) for a, b in zip(start, end, strict=True))
        axis = max(range(3), key=lambda i: delta[i])
        if sum(value > 1e-8 for value in delta) == 1:
            cylinder(name, center, radius, delta[axis] / M_PER_IN, axis, finish)
        else:
            size = tuple(value + 2 * radius * M_PER_IN for value in delta)
            part = box(center[0], center[1], center[2] - size[2] / 2,
                       center[2] + size[2] / 2, size[0], size[1], finish)
            part["role"] = f"shower:{name}"
            parts.append(part)

    depth = spec.valve_dimensions.inlet_depth.meters
    body = spec.point(depth=depth)
    cylinder("valve-body", body, 1.25, 2, wall_axis, "metal")
    for port in spec.inlet_ports():
        pipe(port.tag, body, tuple(value.meters for value in port.position), finish="metal")
    pipe("valve-stem", body, spec.point(), 0.5, "metal")
    points = {component.name: spec.component_point(component) for component in spec.components}
    for component in spec.components:
        x, y, z = points[component.name]
        if component.kind in ("diverter", "head", "outlet"):
            parent = points.get(component.connection, spec.point())
            parent_back = (parent[0] + nx * depth, parent[1] + ny * depth, parent[2])
            child_back = (x + nx * depth, y + ny * depth, z)
            if not (component.kind == "handheld" and component.connection == "head"):
                pipe(component.name + "-feed", parent_back,
                     (parent_back[0], parent_back[1], z), finish="metal")
                pipe(component.name + "-feed-offset", (parent_back[0], parent_back[1], z),
                     child_back, finish="metal")
                pipe(component.name + "-wall-outlet", child_back, (x, y, z), finish="metal")
        name = component.name
        if component.kind in ("control", "temperature", "volume", "diverter"):
            radius = PLATE_RADIUS if component.kind == "control" else 1.15
            cylinder(name + "-plate", (x - nx * M_PER_IN / 8, y - ny * M_PER_IN / 8, z),
                     radius, PLATE_THICKNESS, wall_axis)
            tip = (x - nx * HANDLE_PROJECTION * M_PER_IN,
                   y - ny * HANDLE_PROJECTION * M_PER_IN, z)
            pipe(name, (x, y, z), tip, 0.45)
            pipe(name + "-lever", tip, (tip[0], tip[1], tip[2] - 1.8 * M_PER_IN), 0.2)
        elif component.kind == "head":
            tip = (x - nx * ARM_PROJECTION * M_PER_IN, y - ny * ARM_PROJECTION * M_PER_IN, z)
            pipe(name + "-arm", (x, y, z), tip)
            cylinder(name, (tip[0], tip[1], z - HEAD_THICKNESS * M_PER_IN / 2),
                     HEAD_RADIUS, HEAD_THICKNESS, 2)
            cylinder(name + "-spray", (tip[0], tip[1], z - HEAD_THICKNESS * M_PER_IN),
                     HEAD_RADIUS * 0.9, 0.1, 2, "metal-black")
        elif component.kind == "outlet":
            cylinder(name, (x - nx * M_PER_IN / 2, y - ny * M_PER_IN / 2, z),
                     0.75, 1, wall_axis)
        elif component.kind == "spout":
            tip = (x - nx * 6 * M_PER_IN, y - ny * 6 * M_PER_IN, z)
            pipe(name, (x, y, z), tip, 0.75)
            pipe(name + "-outlet", tip, (tip[0], tip[1], z - M_PER_IN), 0.5)
            pipe(name + "-supply", body, (body[0], body[1], z), finish="metal")
            pipe(name + "-stub", (body[0], body[1], z), (x, y, z), finish="metal")
        else:
            # The handpiece is separately recognizable even when docked beside a combo head.
            face = (x - nx * 3 * M_PER_IN, y - ny * 3 * M_PER_IN, z)
            cylinder(name, face, 1.3, 0.6, wall_axis)
            pipe(name + "-grip", face, (face[0], face[1], z - 5 * M_PER_IN), 0.45)
            anchor = points[component.connection]
            start = (anchor[0] - nx * M_PER_IN, anchor[1] - ny * M_PER_IN, anchor[2])
            end = (face[0], face[1], z - 5 * M_PER_IN)
            last = start
            for index in range(1, HOSE_SEGMENTS + 1):
                t = index / HOSE_SEGMENTS
                current = tuple(a + (b - a) * t for a, b in zip(start, end, strict=True))
                current = (*current[:2], current[2] - HOSE_DROP * M_PER_IN * math.sin(math.pi * t))
                pipe(name + "-hose", last, current, 0.15)
                last = current
    return tuple(parts)
