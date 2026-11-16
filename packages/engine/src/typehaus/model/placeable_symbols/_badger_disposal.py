"""Badger 5 under-sink assembly, with the discharge turned toward local -x.

Envelope and discharge setout follow InSinkErator submittal 81720. Small housing,
mounting and label details are representative; this is not a fabrication model.
The catalog footprint describes the motor body; the supplied elbow projects past it.
https://www.insinkerator.com/documents/badger-5-specifications-en-81720.pdf
"""

import math

from typehaus.model.placeable_symbols._frame import box, circle
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

BODY_DIAMETER_IN = 6.3125
ASSEMBLY_HEIGHT_IN = 11.5
PIPE_RADIUS_IN = 0.75
ELBOW_BEND_RADIUS_IN = 0.875
ELBOW_BEND_SEGMENTS = 12
PIPE_RADIAL_SEGMENTS = 24
# Bottom, top, radius, finish. The narrow neck reaches the underside of the bowl.
HOUSING_COURSES_IN = (
    (0, 0.35, 2.55, "metal"),
    (0.35, 1.0, 2.85, "metal"),
    (1.0, 5.4, 3.0, "disposal-gray"),
    (5.4, 5.65, 3.15625, "metal-black"),
    (5.65, 8.9, 3.10, "disposal-gray"),
    (8.9, 9.35, 2.75, "disposal-gray"),
    (9.35, 9.8, 2.05, "metal-black"),
    (9.8, 10.15, 2.35, "chrome"),
    (10.15, 10.85, 1.65, "chrome"),
    (10.85, 11.1, 2.25, "chrome"),
    (11.1, 11.5, 1.55, "chrome"),
)


def _discharge_elbow():
    # Centreline reaches x=-5 at the side-discharge station, z=5; the bend
    # continues down to the supplied tailpiece. The trap is a separate assembly.
    bend = ELBOW_BEND_RADIUS_IN
    path = [(-2.8, 5.0, 0.0)]
    for step in range(ELBOW_BEND_SEGMENTS + 1):
        angle = math.pi / 2 * step / ELBOW_BEND_SEGMENTS
        path.append((-5 + bend - bend * math.sin(angle),
                     5 - bend + bend * math.cos(angle), angle))
    path.append((-5, 1.0, math.pi / 2))
    positions, triangles = [], []
    for x, z, turn in path:
        for segment in range(PIPE_RADIAL_SEGMENTS):
            angle = math.tau * segment / PIPE_RADIAL_SEGMENTS
            positions.append((x - PIPE_RADIUS_IN * math.sin(turn) * math.sin(angle),
                              PIPE_RADIUS_IN * math.cos(angle),
                              z + PIPE_RADIUS_IN * math.cos(turn) * math.sin(angle)))
    for course in range(len(path) - 1):
        for segment in range(PIPE_RADIAL_SEGMENTS):
            a = course * PIPE_RADIAL_SEGMENTS + segment
            b = course * PIPE_RADIAL_SEGMENTS + (segment + 1) % PIPE_RADIAL_SEGMENTS
            c, d = a + PIPE_RADIAL_SEGMENTS, b + PIPE_RADIAL_SEGMENTS
            triangles.extend(((a, b, c), (b, d, c)))
    # Close the supplied pipe solid; its far cap is hidden by the installed trap.
    for course, reverse in ((0, True), (len(path) - 1, False)):
        center = len(positions)
        positions.append((path[course][0], 0, path[course][1]))
        for segment in range(PIPE_RADIAL_SEGMENTS):
            a = course * PIPE_RADIAL_SEGMENTS + segment
            b = course * PIPE_RADIAL_SEGMENTS + (segment + 1) % PIPE_RADIAL_SEGMENTS
            triangles.append((center, b, a) if reverse else (center, a, b))
    return mesh_part(positions, outward(positions, triangles), "metal-black")


def badger_disposal(width: float, depth: float, height: float):
    parts = []
    for bottom, top, radius, color in HOUSING_COURSES_IN:
        parts.append(round_cylinder((0, 0, (bottom + top) / 2), radius,
                                    top - bottom, axis=2, color=color))
    # Quick Lock ears and three clamp screws make the mounting assembly legible.
    for angle_degrees in (30, 150, 270):
        angle = math.radians(angle_degrees)
        x, y = 1.95 * math.cos(angle), 1.95 * math.sin(angle)
        parts.append(round_cylinder((x, y, 10.45), 0.12, 0.85, axis=2, color="chrome"))
        parts.append(box(x, y, 9.85, 10.1, 0.55, 0.45, "chrome"))
    # Dishwasher knockout matches the house's upper-body inlet, on the opposite side.
    parts.append(round_cylinder((2.85, 0, 9), 0.4375, 0.612, axis=0,
                                color="metal-black"))
    parts.append(round_cylinder((-3.05, 0, 5), 1.05, 0.3, axis=0, color="metal-black"))
    parts.append(_discharge_elbow())
    # Front rating label, bottom reset and service-wrench socket.
    parts.append(box(0, -2.96, 2.2, 4.65, 2.0, 0.12, "appliance-white"))
    parts.append(box(0, -3.025, 3.85, 4.4, 1.75, 0.02, "metal-black"))
    parts.append(round_cylinder((1.35, -0.7, 0.08), 0.18, 0.16, axis=2,
                                color="disposal-reset"))
    parts.append(round_cylinder((0, 0, 0.025), 0.23, 0.05, axis=2, color="metal-black"))
    scale = (width / BODY_DIAMETER_IN, depth / BODY_DIAMETER_IN,
             height / ASSEMBLY_HEIGHT_IN)
    scaled = []
    for part in parts:
        result = {**part,
                  "center": tuple(v * s for v, s in zip(part["center"], scale, strict=True)),
                  "size": tuple(v * s for v, s in zip(part["size"], scale, strict=True))}
        if "mesh" in part:
            mesh = part["mesh"]
            normals = [tuple(v / s for v, s in zip(n, scale, strict=True))
                       for n in mesh["normals"]]
            result["mesh"] = {**mesh,
                "positions": tuple(tuple(v * s for v, s in zip(p, scale, strict=True))
                                   for p in mesh["positions"]),
                "normals": tuple(tuple(v / math.sqrt(sum(c * c for c in n)) for v in n)
                                 for n in normals)}
        scaled.append(result)
    return (circle(0, 0, min(width, depth) / 2),), tuple(scaled)
