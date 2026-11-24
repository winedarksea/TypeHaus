"""IKEA HEKTAR floor lamp, dark gray (US art. 702.165.44).

Published (US/CA listings): 71 in high, 12 in (31.5 cm) shade diameter, 13 in (34 cm) base
diameter, E26 globe bulb sold separately, 53 W max; aluminium shade, steel tube, EVA weight;
the head tilts on a side-knob yoke. Estimated from IKEA's assembly drawing and photos, not
published: base height and dome, tube diameter (~1/2 in), the 75 deg bend and 5.4 in run to
the yoke, the 15 deg downward aim, shade depth (6.5 in) and profile, the globe size.
The geometry is built in inches about the stem axis, then fitted to W x D x H. Its true plan
box is ``ENVELOPE_IN`` (the shade overhangs the base toward -y, where it aims; the base
fills +y and the width), 71 in high. The cord is omitted.
Reference: https://www.ikea.com/us/en/p/hektar-floor-lamp-dark-gray-70216544/
"""

from __future__ import annotations

import math
from functools import cache

import numpy as np

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, ellipse, polygon
from typehaus.model.placeable_symbols._mesh import outward
from typehaus.model.placeable_symbols._turned_profile import turned_profile

HEIGHT_IN = 71.0
BASE_R, SHADE_R = 6.5, 6.0
TUBE_R = 0.24
BEND_DEG, BEND_R, REACH = 75.0, 1.5, 5.4  # stem leans forward, then runs to the yoke
AIM_DEG = 15.0  # shade axis, below horizontal toward -y
PIVOT_A = 3.2  # side pins sit this far along the shade axis from its back
YOKE_UP = 5.75  # yoke bar clears the body radius (5.4)
FINISH = "luminaire-housing"
SEG, TUBE_SEG = 40, 12
EX = np.array((1.0, 0.0, 0.0))

# Shade meridian as (radius, axial from the back): outer skin out, inner skin back.
SHADE = ((0, 0), (4.2, 0), (5.0, .25), (5.35, .9), (5.4, 3.4), (6.0, 6.5),
         (5.9, 6.5), (5.3, 3.5), (5.25, .95), (4.9, .35), (4.1, .1), (0, .1))
BASE = ((0, 0), (6.2, 0), (6.5, .15), (6.5, .8), (6.0, 1.2), (3.0, 1.5), (.9, 1.7), (0, 1.7))
SOCKET = ((0, 0), (.8, 0), (.8, 1.2), (0, 1.2))
KNOB = ((0, 0), (.45, 0), (.5, .1), (.5, .5), (0, .5))


def _unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def _raw(positions, normals, triangles, color: str) -> dict:
    return {"p": np.asarray(positions, float), "n": np.asarray(normals, float),
            "t": [tuple(t) for t in triangles], "color": color}


def _turned(profile, color: str, origin, axes, *, closed: bool = False) -> dict:
    """Lathe about local z (inches), then map local x/y/z onto the world ``axes``."""
    mesh = turned_profile(profile, 1, 1, color, segments=SEG, closed=closed,
                          smooth=True)["mesh"]
    basis = np.asarray(axes, float)  # rows are the images of local x, y, z
    return _raw(np.asarray(origin, float) + np.asarray(mesh["positions"]) @ basis,
                np.asarray(mesh["normals"]) @ basis, mesh["triangles"], color)


def _sweep(path: np.ndarray, ref: np.ndarray, radius: float) -> dict:
    """Smooth round tube along ``path`` (rings perpendicular to it), capped at both ends."""
    tangent = np.gradient(path, axis=0)
    positions, normals = [], []
    for point, direction in zip(path, tangent, strict=True):
        direction = _unit(direction)
        u = _unit(np.cross(ref, direction))
        v = np.cross(direction, u)
        for i in range(TUBE_SEG):
            radial = math.cos(math.tau * i / TUBE_SEG) * u + math.sin(math.tau * i / TUBE_SEG) * v
            positions.append(point + radius * radial)
            normals.append(radial)
    triangles = []
    for ring in range(len(path) - 1):
        for i in range(TUBE_SEG):
            a, b = ring * TUBE_SEG + i, ring * TUBE_SEG + (i + 1) % TUBE_SEG
            triangles += [(a, a + TUBE_SEG, b), (b, a + TUBE_SEG, b + TUBE_SEG)]
    for end, sign in ((0, -1), (len(path) - 1, 1)):  # caps wound with the sides
        centre, first = len(positions), end * TUBE_SEG
        positions.append(path[end])
        normals.append(sign * _unit(tangent[end]))
        fan = [(centre, first + i, first + (i + 1) % TUBE_SEG) for i in range(TUBE_SEG)]
        triangles += fan if sign < 0 else [(a, c, b) for a, b, c in fan]
    return _raw(positions, normals, outward(positions, triangles), FINISH)


def _hull(points):
    points = sorted(set(points))

    def half(sequence):
        out: list = []
        for p in sequence:
            while len(out) > 1 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                    - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    return half(points)[:-1] + half(points[::-1])[:-1]


@cache
def _model(stem_rise: float):
    """Raw inch-frame parts and plan shapes for a vertical stem rising ``stem_rise``."""
    bend, tilt = math.radians(BEND_DEG), math.radians(AIM_DEG)
    arc = [(-BEND_R * (1 - math.cos(a)), stem_rise + BEND_R * math.sin(a))
           for a in (bend * i / 8 for i in range(9))]
    end = (arc[-1][0] - REACH * math.sin(bend), arc[-1][1] + REACH * math.cos(bend))
    stem = np.array([(0, 0, 1.6), *((0, y, z) for y, z in arc), (0, *end)], float)
    aim = np.array((0, -math.cos(tilt), -math.sin(tilt)))
    up = np.cross(aim, EX)
    axes = (EX, up, aim)  # the shade frame: x across, y up, z out of the mouth
    pivot = stem[-1] - YOKE_UP * up  # shade centre at the side pins
    back = pivot - PIVOT_A * aim
    rod, corner = SHADE_R * .94 + .12, 1.2  # yoke sides run just outside the body
    left = [(-rod, 0), (-rod, YOKE_UP - corner)]  # the bend starts at i=1, not repeating it
    left += [(-rod + corner - corner * math.cos(math.pi / 2 * i / 6),
              YOKE_UP - corner + corner * math.sin(math.pi / 2 * i / 6)) for i in range(1, 7)]
    yoke = np.array([pivot + x * EX + y * up for x, y in left + [(-x, y) for x, y in left[::-1]]])
    bulb = [(1.9 * math.sin(a), 1.2 + 1.9 * (1 - math.cos(a)))
            for a in np.linspace(.55, math.pi, 14)]
    globe = ((0.0, bulb[0][1]), *bulb[:-1], (0.0, bulb[-1][1]))  # neck and crown on the axis
    raw = [_turned(BASE, FINISH, (0, 0, 0), np.eye(3)),
           _sweep(stem, EX, TUBE_R), _sweep(yoke, aim, .12),
           _turned(SHADE, FINISH, back, axes, closed=True),
           _turned(SOCKET, FINISH, back + .1 * aim, axes),
           _turned(globe, "lamp", back + .1 * aim, axes),  # E26 opal globe
           _turned(KNOB, FINISH, pivot + rod * EX, ((0, 1, 0), (0, 0, 1), (1, 0, 0)))]

    def ring(axial: float, radius: float):
        return [tuple((back + axial * aim + radius * (math.cos(k) * EX + math.sin(k) * up))[:2])
                for k in (math.tau * i / 48 for i in range(48))]

    mouth = ring(6.5, SHADE_R)
    return raw, {"hull": _hull(mouth + ring(0, 4.2) + ring(3.4, 5.4)), "mouth": mouth,
                 "stem_end": tuple(float(v) for v in stem[-1][:2])}


def _envelope() -> tuple[float, tuple[float, ...]]:
    """Stem rise putting the highest point at 71 in, and the resulting box centre and size."""
    top = max(m["p"][:, 2].max() for m in _model(60.0)[0])
    rise = 60.0 + HEIGHT_IN - top
    raw = _model(rise)[0]
    low = np.min([m["p"].min(axis=0) for m in raw], axis=0)
    high = np.max([m["p"].max(axis=0) for m in raw], axis=0)
    return rise, (*((low + high) / 2)[:2], *(high - low))


_RISE, (_CX, _CY, WIDTH_IN, DEPTH_IN, _) = _envelope()
ENVELOPE_IN = (round(WIDTH_IN, 2), round(DEPTH_IN, 2), HEIGHT_IN)


def ikea_hektar_floor_lamp(width: float, depth: float, height: float) -> Geometry:
    """Fit the product to W x D x H; z=0 is the floor, the shade overhangs toward -y."""
    scale = np.array((width / WIDTH_IN, depth / DEPTH_IN, height / HEIGHT_IN))
    shift = np.array((_CX, _CY, 0.0))
    raw, plan = _model(_RISE)
    parts: list[Part] = []
    for item in raw:
        positions = (item["p"] - shift) * scale
        normals = item["n"] / scale
        normals = normals / np.linalg.norm(normals, axis=1)[:, None]
        low, high = positions.min(axis=0), positions.max(axis=0)
        parts.append({
            "center": tuple(((low + high) / 2).tolist()), "size": tuple((high - low).tolist()),
            "color": item["color"], "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(map(tuple, positions.tolist())),
                     "triangles": tuple(item["t"]),
                     "normals": tuple(map(tuple, normals.tolist()))}})

    def fit(points):
        return [((x - _CX) * scale[0], (y - _CY) * scale[1]) for x, y in points]

    base = ellipse(-_CX * scale[0], -_CY * scale[1], BASE_R * scale[0], BASE_R * scale[1])
    strokes = (base, polygon(fit(plan["hull"]), fill=FINISH),
               polygon(fit(plan["mouth"]), fill="lamp"),
               polygon(fit([(0.0, 0.0), plan["stem_end"]]), closed=False))
    return strokes, tuple(parts)
