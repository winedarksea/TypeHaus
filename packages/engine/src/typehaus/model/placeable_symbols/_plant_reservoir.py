"""Opaque lidded BRUTE and a separate service rack; shared by canvas, GLB and IFC.

Outside tank dimensions are published; small fittings and rack equipment are service
 envelopes, not fabrication templates. Water levels belong in the section, not the exterior.
"""

import math

from shapely.geometry import Polygon
from shapely.geometry import box as polygon_box

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, circle, line, prism, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._plant_primitives import slender_segment
from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.model.plant_reservoir import RESERVOIR_GEOMETRY as G
from typehaus.quantities import M_PER_IN

ROUND_SEGMENTS = 32


def _role(part, role):
    return {**part, "role": role}


def _shell():
    radius = G.body_diameter_in / 2
    wall = G.wall_thickness_in
    # Closed bottom and hollow sides, joined at the top rim. No coincident surfaces.
    profile = (
        (0, 0),
        (radius * G.bottom_radius_share, 0),
        (radius, G.rim_height_in),
        (radius - wall, G.rim_height_in),
        (radius * G.bottom_radius_share - wall, wall),
        (0, wall),
    )
    positions, triangles = [], []
    # A fan on each end avoids zero-area triangles at a zero-radius ring.
    for r, z in profile[1:-1]:
        positions.extend(
            (
                r * math.cos(math.tau * i / ROUND_SEGMENTS) * M_PER_IN,
                r * math.sin(math.tau * i / ROUND_SEGMENTS) * M_PER_IN,
                z * M_PER_IN,
            )
            for i in range(ROUND_SEGMENTS)
        )
    for course in range(3):
        for i in range(ROUND_SEGMENTS):
            j = (i + 1) % ROUND_SEGMENTS
            a, b = course * ROUND_SEGMENTS + i, course * ROUND_SEGMENTS + j
            c, d = a + ROUND_SEGMENTS, b + ROUND_SEGMENTS
            triangles.extend(((a, b, c), (b, d, c)))
    positions.extend(((0, 0, 0), (0, 0, wall * M_PER_IN)))
    for i in range(ROUND_SEGMENTS):
        j = (i + 1) % ROUND_SEGMENTS
        triangles.extend(
            (
                (4 * ROUND_SEGMENTS, j, i),
                (4 * ROUND_SEGMENTS + 1, 3 * ROUND_SEGMENTS + i, 3 * ROUND_SEGMENTS + j),
            )
        )
    return mesh_part(positions, triangles, "nordvalla-gray")


def _tube(points, role, color="metal-black", radius=0.125):
    return [
        _role(
            slender_segment(
                tuple(v * M_PER_IN for v in start),
                tuple(v * M_PER_IN for v in end),
                radius * M_PER_IN,
                color,
            ),
            role,
        )
        for start, end in zip(points, points[1:], strict=False)
    ]


def _scaled(parts, width, depth, height, nominal):
    scale = (
        width / (nominal[0] * M_PER_IN),
        depth / (nominal[1] * M_PER_IN),
        height / (nominal[2] * M_PER_IN),
    )
    result = []
    for part in parts:
        part = {
            **part,
            "center": tuple(v * s for v, s in zip(part["center"], scale, strict=True)),
            "size": tuple(v * s for v, s in zip(part["size"], scale, strict=True)),
        }
        if part["points"]:
            part["points"] = tuple((x * scale[0], y * scale[1]) for x, y in part["points"])
        if "mesh" in part:
            mesh = part["mesh"]
            normals = [
                tuple(n / s for n, s in zip(normal, scale, strict=True))
                for normal in mesh["normals"]
            ]
            part["mesh"] = {
                **mesh,
                "positions": tuple(
                    tuple(v * s for v, s in zip(p, scale, strict=True)) for p in mesh["positions"]
                ),
                "normals": tuple(
                    tuple(n / math.sqrt(sum(v * v for v in normal)) for n in normal)
                    for normal in normals
                ),
            }
        result.append(part)
    return tuple(result)


def _box(x, y, z0, z1, width, depth, color, role):
    return _role(
        box(
            x * M_PER_IN,
            y * M_PER_IN,
            z0 * M_PER_IN,
            z1 * M_PER_IN,
            width * M_PER_IN,
            depth * M_PER_IN,
            color,
        ),
        role,
    )


def plant_reservoir(width: float, depth: float, height: float) -> Geometry:
    parts = [_role(_shell(), "reservoir:shell")]
    # Split handles leave actual openings rather than solid blocks on the vessel.
    for sign in (-1, 1):
        for y in (-1.0, 1.0):
            parts.append(
                _box(sign * 8.0, y, 15.6, 16.1, 2, 0.4, "nordvalla-gray", "reservoir:handle")
            )
        parts.append(
            _box(sign * 8.75, 0, 15.6, 16.1, 0.5, 2.4, "nordvalla-gray", "reservoir:handle")
        )
    # A real notch below the free jet: a full disc would block the modeled air gap.
    radius = G.body_diameter_in / 2 * M_PER_IN
    notch_angle = math.asin(1.5 * M_PER_IN / radius)
    angles = [
        math.pi / 2 + notch_angle + (math.tau - 2 * notch_angle) * i / ROUND_SEGMENTS
        for i in range(ROUND_SEGMENTS + 1)
    ]
    lid_ring = tuple((radius * math.cos(a), radius * math.sin(a)) for a in angles)
    lid_ring += ((1.5 * M_PER_IN, 5.0 * M_PER_IN), (-1.5 * M_PER_IN, 5.0 * M_PER_IN))
    lid_outline = Polygon(lid_ring)
    for x in (-3, 3):
        lid_outline = lid_outline.difference(
            polygon_box(
                (x - 0.25) * M_PER_IN, -9 * M_PER_IN, (x + 0.25) * M_PER_IN, -3.75 * M_PER_IN
            )
        )
    lid_ring = tuple(lid_outline.exterior.coords[:-1])
    parts.append(
        _role(
            prism(
                lid_ring,
                G.rim_height_in * M_PER_IN,
                (G.rim_height_in + 0.3) * M_PER_IN,
                "nordvalla-gray",
            ),
            "reservoir:lid",
        )
    )
    # The lid stops at the rim; the fill crosses free air outside the removable lid's notch.
    parts += [
        _box(0, 7.4, 17.2, G.installed_height_in, 0.65, 0.4, "metal", "reservoir:bracket"),
        _box(0, 6.5, 19.63, 20.0, 1.0, 2.2, "metal", "reservoir:float-valve"),
        _box(0, 2.8, 14.5, 15.4, 2.5, 2, "appliance-white", "reservoir:float"),
        _box(-5.4, 1, 1.2, 2.5, 1, 1, "appliance-white", "reservoir:low-water"),
    ]
    parts += _tube(
        ((0, 6.5, 19.8), (0, G.discharge_y_in, 19.8), (0, G.discharge_y_in, G.discharge_height_in)),
        "reservoir:discharge",
        "faucet",
    )
    parts += _tube(((0, 6.5, 19.63), (6, 7, 19.63), (6, 7, 14)), "reservoir:fill")
    parts += _tube(((0, 6.5, 19.63), (0, 2.8, 15)), "reservoir:float-arm", "metal")
    for x in (-3, 3):
        parts += _tube(((x, -4, 1.8), (x, -4, 18), (x, -8.5, 18)), "reservoir:suction")
    strokes = (
        circle(
            0,
            0,
            min(width, depth) * G.body_diameter_in / G.handle_width_in / 2,
            fill="nordvalla-gray",
        ),
        rect(0, 0, width, depth),
        line((0, 0), (0, depth / 3)),
    )
    return strokes, _scaled(
        parts, width, depth, height, (G.handle_width_in, G.envelope_depth_in, G.installed_height_in)
    )


def plant_irrigation_rack(width: float, depth: float, height: float) -> Geometry:
    parts = [_box(0, 0, 3.5, 4, 36, 12, "metal", "irrigation:rack")]
    for x in (-17, 17):
        for y in (-5, 5):
            parts.append(_box(x, y, 0, 24, 1, 1, "metal", "irrigation:upright"))
    parts.append(_box(0, 0, 9.2, 9.5, 34, 10, "metal", "irrigation:power-shelf"))
    for x in G.pump_centres_in:
        parts += [
            _role(
                round_cylinder(
                    ((x - 1) * M_PER_IN, 0, 6.25 * M_PER_IN),
                    1.75 * M_PER_IN,
                    6 * M_PER_IN,
                    axis=0,
                    color="metal",
                ),
                "irrigation:pump",
            ),
            _box(x + 3, 0, 4, 8.5, 3, 4.5, "metal-black", "irrigation:pump-head"),
            _box(x, 0, 4, 4.4, 8, 4, "metal-black", "irrigation:pump-feet"),
            _box(x, -0.4, 9.5, 11, 6.6, 2.7, "metal-black", "irrigation:power-supply"),
            _box(x, 2.5, 17, 22, 3, 2.5, "appliance-white", "irrigation:timer"),
            _box(x, 1.2, 19.5, 21, 2, 0.12, "screen", "irrigation:timer-screen"),
        ]
        parts += _tube(((x - 4, 0, 6), (x - 5.5, 0, 6), (x - 5.5, -5, 12)), "irrigation:suction")
        parts += _tube(((x + 4, 0, 6), (x + 5.5, 0, 6), (x + 5.5, 0, 23)), "irrigation:outlet")
    parts += [
        _box(0, 1, 12, 23, 6, 5, "electrical-plate", "irrigation:control-enclosure"),
        _box(0, -4.8, 13, 17, 4, 1.5, "appliance-white", "irrigation:fill-controller"),
    ]
    strokes = (rect(0, 0, width, depth, fill="metal"),)
    return strokes, _scaled(
        parts, width, depth, height, (G.rack_width_in, G.rack_depth_in, G.rack_height_in)
    )


def plant_leak_sensors(width: float, depth: float, height: float) -> Geometry:
    parts = [
        _box(-1.5, 0, 0, 1.3, 3, 3, "electrical-plate", "irrigation:wet-switch"),
        _box(1.5, 0, 0, 0.12, 2, 3, "metal", "irrigation:fill-sensor"),
    ]
    return (rect(0, 0, width, depth),), _scaled(parts, width, depth, height, (6, 3, 1.3))


def plant_fill_shutoff(width: float, depth: float, height: float) -> Geometry:
    """FloodStop component at the manual stop, upstream of the flexible fill tube."""
    parts = [
        _box(0, 0, 0, 1, 2.5, 1.8, "faucet", "irrigation:fill-valve"),
        _box(0, 0, 1, 3, 2.7, 1.8, "metal-black", "irrigation:valve-actuator"),
    ]
    return (rect(0, 0, width, depth),), _scaled(parts, width, depth, height, (3, 2, 3))
