"""Low-poly PROPH80 T0 RH120-M, front toward -y.

Rheem RH-PIHP-SC Rev. 6 p.2 supplies A/B/C/E/G/K; the jacket divisions,
controls and grilles are scaled from its elevation and p.1 photograph:
https://media.rheem.com/blobazrheem/wp-content/uploads/sites/36/2024/12/Plug-in-with-HydroBoost-and-LeakGuard-Spec-Sheet.pdf
W/D describe the 24¼-inch tank diameter, as in the catalog, not the projecting
HydroBoost cover and fittings. No optional ducts or LeakGuard valve are fitted.
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, box, circle, prism
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

TANK_DIAMETER_IN = 24.25
OVERALL_HEIGHT_IN = 74.1875
HEAT_PUMP_BASE_IN = 55.0
RISER_TOP_IN = 54.3125
RISER_SHOULDER_IN = 34.0
HOT_PORT_IN = (14.1, -5.1, 42.375)
COLD_PORT_IN = (10.7, -11.9, 5.0625)
CONDENSATE_PORT_IN = (-7.5, -11.0, 59.0)
RELIEF_PORT_IN = (-5.3, -14.5, 46.0)
EXHAUST_ANGLE_DEG = 70.0  # clockwise from front, matching the authored exhaust clearance
EXHAUST_RADIUS_IN = 5.25
TOP_GRILLE_ROWS = 7
EXHAUST_GRILLE_ROWS = 7
JACKET_COLOR = "proterra-jacket"
TRIM_COLOR = "metal"


def _cylinder(center, radius, length, *, axis=2, color=JACKET_COLOR, turn=0.0) -> Part:
    part = round_cylinder((0, 0, 0), radius, length, axis=axis, color=color)
    cosine, sine = math.cos(math.radians(turn)), math.sin(math.radians(turn))

    def rotate(point):
        x, y, z = point
        return (x * cosine - y * sine, x * sine + y * cosine, z)

    mesh = part["mesh"]
    positions = [tuple(a + b for a, b in zip(rotate(point), center, strict=True))
                 for point in mesh["positions"]]
    return _with_mesh(part, positions, [rotate(normal) for normal in mesh["normals"]])


def _with_mesh(part, positions, normals) -> Part:
    bounds = [(min(p[i] for p in positions), max(p[i] for p in positions)) for i in range(3)]
    return {**part, "center": tuple((lo + hi) / 2 for lo, hi in bounds),
            "size": tuple(hi - lo for lo, hi in bounds),
            "mesh": {**part["mesh"], "positions": tuple(positions), "normals": tuple(normals)}}


def _radial_fitting(tip, *, color="brass") -> Part:
    x, y, z = tip
    radius = math.hypot(x, y)
    length = radius - 11.7
    center_radius = radius - length / 2
    return _cylinder((x / radius * center_radius, y / radius * center_radius, z),
                     0.52, length, axis=1, color=color,
                     turn=math.degrees(math.atan2(y, x)) - 90)


def _scale_part(part: Part, scale: tuple[float, float, float]) -> Part:
    if "mesh" in part:
        mesh = part["mesh"]
        positions = [tuple(value * factor for value, factor in zip(point, scale, strict=True))
                     for point in mesh["positions"]]
        normals = []
        for normal in mesh["normals"]:
            transformed = tuple(value / factor for value, factor in zip(normal, scale, strict=True))
            magnitude = math.sqrt(sum(value * value for value in transformed))
            normals.append(tuple(value / magnitude for value in transformed))
        return _with_mesh(part, positions, normals)
    return {**part,
            "center": tuple(value * factor for value, factor in
                            zip(part["center"], scale, strict=True)),
            "size": tuple(value * factor for value, factor in
                          zip(part["size"], scale, strict=True)),
            "points": tuple((x * scale[0], y * scale[1]) for x, y in part["points"])}


def rheem_proterra_plugin_80(width: float, depth: float, height: float) -> Geometry:
    radius = TANK_DIAMETER_IN / 2
    parts = [
        _cylinder((0, 0, HEAT_PUMP_BASE_IN / 2), radius, HEAT_PUMP_BASE_IN),
        _cylinder((0, 0, (HEAT_PUMP_BASE_IN + OVERALL_HEIGHT_IN) / 2), radius,
                  OVERALL_HEIGHT_IN - HEAT_PUMP_BASE_IN),
    ]
    for bottom, top in ((0, 0.75), (54.7, 55.2), (73.5, OVERALL_HEIGHT_IN)):
        parts.append(_cylinder((0, 0, (bottom + top) / 2), radius + 0.03,
                               top - bottom, color=TRIM_COLOR))
    # Raised covers sit clear of the curved jacket, so neither seams nor the screen z-fight.
    for bottom, top in ((9.5, 18.5), (36.0, 45.0)):
        parts.append(box(0, -12.0, bottom, top, 6.0, 0.45, TRIM_COLOR))
    parts.extend((box(0, -12.05, 58.0, 72.5, 6.5, 0.65, "metal-black"),
                  box(0, -12.4, 68.2, 71.2, 4.6, 0.12, "screen"),
                  _cylinder((0, -12.12, 50.5), 1.5, 0.15, axis=1, color="proterra-badge")))
    for x in (-1.5, 0.0, 1.5):
        parts.append(box(x, -12.48, 67.0, 67.45, 0.65, 0.08, TRIM_COLOR))
    # The top's intake slots are seven dark strips, rather than hundreds of perforations.
    for row in range(TOP_GRILLE_ROWS):
        y = 2.0 + row * 1.15
        half_width = math.sqrt((radius - 1.0) ** 2 - y * y)
        parts.append(box(0, y, OVERALL_HEIGHT_IN - 0.02, OVERALL_HEIGHT_IN,
                         half_width * 2, 0.42, "metal-black"))
    parts.append(box(0, 0.2, OVERALL_HEIGHT_IN - 0.02, OVERALL_HEIGHT_IN,
                     19.0, 0.2, "metal-black"))

    # Round side exhaust, capped by a sparse grille; no fan internals or duct adapter.
    angle = math.radians(EXHAUST_ANGLE_DEG)
    outward = (math.sin(angle), -math.cos(angle))
    parts.append(_cylinder((outward[0] * 12, outward[1] * 12, 65.5),
                           EXHAUST_RADIUS_IN, 0.9, axis=1, color="metal-black",
                           turn=EXHAUST_ANGLE_DEG))
    for row in range(EXHAUST_GRILLE_ROWS):
        offset = (row - (EXHAUST_GRILLE_ROWS - 1) / 2) * 1.25
        half_width = math.sqrt((EXHAUST_RADIUS_IN - 0.3) ** 2 - offset * offset)
        ring = [(x * math.cos(angle) - y * math.sin(angle),
                 x * math.sin(angle) + y * math.cos(angle))
                for x, y in ((-half_width, -12.6), (half_width, -12.6),
                             (half_width, -12.4), (-half_width, -12.4))]
        parts.append(prism(ring, 65.5 + offset - 0.16, 65.5 + offset + 0.16, JACKET_COLOR))

    lower_riser = ((8.4, -8.0), (9.8, -10.5), (11.9, -8.1), (10.7, -6.8))
    upper_riser = ((7.824, -9.324), (9.642, -11.491), (12.287, -8.604),
                   (14.489, -3.882), (11.813, -3.165), (9.0, -7.0))
    parts.extend((prism(lower_riser, COLD_PORT_IN[2], RISER_SHOULDER_IN, "metal-black"),
                  prism(upper_riser, RISER_SHOULDER_IN, RISER_TOP_IN, "metal-black"),
                  _radial_fitting(HOT_PORT_IN), _radial_fitting(COLD_PORT_IN),
                  _radial_fitting(RELIEF_PORT_IN),
                  _radial_fitting(CONDENSATE_PORT_IN, color="metal-black")))
    scale = (width / TANK_DIAMETER_IN, depth / TANK_DIAMETER_IN, height / OVERALL_HEIGHT_IN)
    # The model override keeps the established round plan glyph height-independent.
    strokes = (circle(0, 0, min(width, depth) / 2, fill=JACKET_COLOR),)
    return strokes, tuple(_scale_part(part, scale) for part in parts)
