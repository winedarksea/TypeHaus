"""IKEA TERTIAL work lamp (dark gray, art. 203.554.34) with its table clamp, posed on a desk.

Published: 7" (17 cm) shade diameter, 4'11" cord, clamp opens to 2 1/4" (60 mm), steel arm and
head, ABS clamp. IKEA publishes NO assembled height, arm length or reach; its 21 3/4" x 6 3/4" x
4 1/2" figure is the box. Estimated from the shade in IKEA's assembly drawing: lower arm 11 1/2"
and upper arm 13 1/2" (pivot to pivot), shade 4 1/3" deep, clamp flange 2 3/4" x 2 3/8", the bar
and plate sections, springs and knobs. Not fabrication geometry; the clamp jaw below the desk
top is omitted so every part stays at z >= 0.
Pose: lower arm 85 deg from horizontal leaning 5 deg back, upper arm rising 10 deg forward,
shade tilted 25 deg forward-down. Local frame: clamp at +y (desk edge), shade reaches toward -y.
The true envelope is measured off this pose and the geometry scales into any declared W x D x H.
Sources: https://www.ikea.com/us/en/p/tertial-work-lamp-dark-gray-20355434/ and
https://www.ikea.com/us/en/assembly_instructions/tertial-work-lamp-dark-gray__AA-2202950-4-100.pdf
"""

from __future__ import annotations

import math
from functools import lru_cache

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, box, polygon
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._turned_profile import turned_profile

Vec = tuple[float, float, float]  # (x, s, z) in cm; s runs forward from the clamp's back edge
Pt = tuple[float, float]
Raw = tuple  # ("box", x0, x1, s0, s1, z0, z1, color) | ("mesh", positions, tris, normals, color)

BODY, SPRING, KNOB, LAMP = "luminaire-housing", "metal", "metal-black", "lamp"
SHADE_D, SHADE_H, CAP_R, WALL = 17.0, 11.0, 3.0, 0.2  # only the 17 is published
LOWER_LEN, UPPER_LEN = 29.0, 34.0
LOWER_DEG, UPPER_DEG, TILT_DEG = 85.0, 10.0, 25.0
FLANGE_W, FLANGE_D, FLANGE_T, BLOCK_W, BLOCK_H = 7.0, 6.0, 0.7, 4.0, 3.2
PIVOT_S = FLANGE_D / 2
BAR_X, BAR_GAP = 0.6, 1.0  # bar half-width across x; each bar's in-plane offset from the axis
PLATE_X = ((0.65, 0.9), (-0.9, -0.65))
SHADE_OFFSET, CAP_TOP = 3.4, 0.6  # shade axis forward of its pivot; cap top above the pivot
SIDES, SHADE_SEGMENTS = 10, 40
CIRCLE = tuple((math.cos(math.tau * i / SIDES), math.sin(math.tau * i / SIDES))
               for i in range(SIDES))
RECT = ((1, 1), (-1, 1), (-1, -1), (1, -1))


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(v: Vec) -> Vec:
    n = math.sqrt(sum(c * c for c in v))
    return (v[0] / n, v[1] / n, v[2] / n)


def _at(origin: Vec, direction: Vec, t: float) -> Vec:
    return tuple(o + d * t for o, d in zip(origin, direction, strict=True))  # type: ignore[return-value]


def _tube(a: Vec, b: Vec, rx: float, ry: float, color: str, *, ring=CIRCLE,
          ribs: int = 0) -> Raw:
    """A closed straight tube a->b; ``ribs`` alternates the radius so it reads as a coil."""
    axis = _unit(tuple(q - p for p, q in zip(a, b, strict=True)))  # type: ignore[arg-type]
    ref = (1.0, 0.0, 0.0) if abs(axis[0]) < .9 else (0.0, 1.0, 0.0)
    dot = sum(r * c for r, c in zip(ref, axis, strict=True))
    e1 = _unit(tuple(r - c * dot for r, c in zip(ref, axis, strict=True)))  # type: ignore[arg-type]
    e2 = _cross(axis, e1)
    stations = [k / (2 * ribs) for k in range(2 * ribs + 1)] if ribs else [0.0, 1.0]
    n, positions, triangles = len(ring), [], []
    for k, t in enumerate(stations):
        centre, grow = _at(a, tuple(q - p for p, q in zip(a, b, strict=True)), t), \
            (.7 if ribs and k % 2 else 1.0)  # type: ignore[arg-type]
        positions += [tuple(centre[i] + (e1[i] * u * rx + e2[i] * v * ry) * grow
                            for i in range(3)) for u, v in ring]
    for k in range(len(stations) - 1):
        for i in range(n):
            p, q = k * n + i, k * n + (i + 1) % n
            triangles += [(p, q, p + n), (q, q + n, p + n)]
    for k, flip in ((0, True), (len(stations) - 1, False)):  # caps wound with the sides
        positions.append(tuple(sum(positions[k * n + i][c] for i in range(n)) / n
                               for c in range(3)))
        fan = [(len(positions) - 1, k * n + i, k * n + (i + 1) % n) for i in range(n)]
        triangles += [(a, c, b) for a, b, c in fan] if flip else fan
    return ("mesh", positions, triangles, None, color)


def _plate(poly: list[Pt], x0: float, x1: float, color: str) -> Raw:
    """A convex (s, z) outline extruded from x0 to x1."""
    n = len(poly)
    positions = [(x, s, z) for x in (x0, x1) for s, z in poly]
    triangles = [(n, n + i, n + i + 1) for i in range(1, n - 1)]
    triangles += [(0, i + 1, i) for i in range(1, n - 1)]
    for i in range(n):
        j = (i + 1) % n
        triangles += [(i, j, n + j), (i, n + j, n + i)]
    return ("mesh", positions, triangles, None, color)


def _tilt(s: float, z: float) -> Pt:
    """Rotate (s, z) so a downward vector swings toward +s (forward) by TILT_DEG."""
    c, sn = math.cos(math.radians(TILT_DEG)), math.sin(math.radians(TILT_DEG))
    return s * c - z * sn, s * sn + z * c


def _shade(pivot: Vec) -> list[Raw]:
    """Bell shade (vented-cap neck, thin wall) and its emitting disc, tilted about the pivot."""
    def bell(k: int, inset: float = 0.0) -> Pt:
        tau = k / 8
        return (CAP_R + (SHADE_D / 2 - CAP_R) * (1 - (1 - tau) ** 2) - inset,
                CAP_R + (SHADE_H - CAP_R) * tau)
    shell = [(0, 0), (CAP_R - .4, 0), (CAP_R, .4), (CAP_R, CAP_R), *(bell(k) for k in range(1, 9)),
             *(bell(k, WALL) for k in range(8, 0, -1)),
             (CAP_R - WALL, CAP_R), (CAP_R - WALL, .6), (0, .6)]
    u0, radius = SHADE_H - 1.8, 3.4  # a bulb-sized glow, nearer the rim than the cap
    disc = [(radius, u0 + .25), (0, u0 + .25), (0, u0), (radius, u0)]
    parts: list[Raw] = []
    for profile, color in ((shell, BODY), (disc, LAMP)):
        src = turned_profile(tuple(profile), 1.0, 1.0, color, segments=SHADE_SEGMENTS,
                             closed=True, smooth=color == BODY)["mesh"]
        positions, normals = [], []
        for (px, py, u), (nx, ny, nu) in zip(src["positions"], src["normals"], strict=True):
            s, z = _tilt(SHADE_OFFSET + py, CAP_TOP - u)
            ns, nz = _tilt(ny, -nu)
            positions.append((px, pivot[1] + s, pivot[2] + z))
            normals.append((nx, ns, nz))
        parts.append(("mesh", positions, src["triangles"], normals, color))
    return parts


@lru_cache(maxsize=1)
def _pose() -> tuple[tuple[Raw, ...], list[Pt], tuple[tuple[Vec, Vec], ...]]:
    """Every part in the product pose (cm), the shade's plan points, and the arm centrelines."""
    lo, up = math.radians(LOWER_DEG), math.radians(UPPER_DEG)
    d1, d2 = (0.0, -math.cos(lo), math.sin(lo)), (0.0, math.cos(up), math.sin(up))
    n1, n2 = (0.0, -d1[2], d1[1]), (0.0, -d2[2], d2[1])  # n1 points back, n2 up
    top = FLANGE_T + BLOCK_H
    p0 = (0.0, PIVOT_S, top + 2.3)
    elbow = _at(p0, d1, LOWER_LEN)
    head = _at(elbow, d2, UPPER_LEN)
    parts: list[Raw] = [
        ("box", -FLANGE_W / 2, FLANGE_W / 2, 0, FLANGE_D, 0, FLANGE_T, BODY),
        ("box", -BLOCK_W / 2, BLOCK_W / 2, PIVOT_S - BLOCK_W / 2, PIVOT_S + BLOCK_W / 2,
         FLANGE_T, top, BODY)]

    def plates(poly: list[Pt]) -> None:
        parts.extend(_plate(poly, x0, x1, BODY) for x0, x1 in PLATE_X)

    plates([(PIVOT_S - 1.5, top), (PIVOT_S + 1.5, top), (PIVOT_S + 1.0, p0[2] + 1.0),
            (PIVOT_S - 1.0, p0[2] + 1.0)])
    plates([(elbow[1] - 3.2 * d1[1], elbow[2] - 3.2 * d1[2]),
            (elbow[1] + 3.2 * d2[1], elbow[2] + 3.2 * d2[2]),
            (elbow[1] - 1.4 * d2[1] + 1.6 * n2[1], elbow[2] - 1.4 * d2[2] + 1.6 * n2[2])])
    for start, end, normal in ((p0, elbow, n1), (elbow, head, n2)):
        for sign in (-1, 1):  # the parallelogram's two bars, offset in the arm's plane
            shift = (0.0, sign * BAR_GAP * normal[1], sign * BAR_GAP * normal[2])
            parts.append(_tube(_at(start, shift, 1), _at(end, shift, 1), BAR_X, .35, BODY,
                               ring=RECT))
    for sign in (-1, 1):  # two coil springs forward of the lower arm
        a, b = _at(_at(p0, d1, 2.5), n1, -1.9), _at(_at(p0, d1, 25.0), n1, -1.9)
        parts.append(_tube((sign * 1.6, a[1], a[2]), (sign * 1.6, b[1], b[2]), .45, .45,
                           SPRING, ribs=13))
    parts.append(_tube(_at(_at(elbow, d2, 3.0), n2, 1.9), _at(_at(elbow, d2, 22.0), n2, 1.9),
                       .4, .4, SPRING, ribs=10))
    for point, radius, half, color in ((p0, .45, 1.4, SPRING), (elbow, .45, 1.4, SPRING),
                                       (head, 1.0, 2.2, KNOB)):
        parts.append(_tube((-half, point[1], point[2]), (half, point[1], point[2]),
                           radius, radius, color))
    shade = _shade(head)
    return (*parts, *shade), [(x, s) for x, s, _ in shade[0][1]], ((p0, elbow), (elbow, head))


def _extent(parts: tuple[Raw, ...]) -> tuple[float, float, float, float]:
    """Half-width, back s, front s and top z of the pose, in cm."""
    xs, ss, zs = [], [], []
    for part in parts:
        if part[0] == "box":
            xs += part[1:3]
            ss += part[3:5]
            zs += part[5:7]
        else:
            xs += [p[0] for p in part[1]]
            ss += [p[1] for p in part[1]]
            zs += [p[2] for p in part[1]]
    return max(abs(x) for x in xs), min(ss), max(ss), max(zs)


def envelope_cm() -> tuple[float, float, float]:
    """The pose's true width, depth (clamp to shade rim) and height, in cm."""
    half, s0, s1, top = _extent(_pose()[0])
    return 2 * half, s1 - s0, top


def ikea_tertial_work_lamp(width: float, depth: float, height: float) -> Geometry:
    """Scale the posed lamp into W x D x H: clamp at +y, shade toward -y, z=0 the desk top."""
    parts, shade_points, arms = _pose()
    half, s_min, s_max, top = _extent(parts)
    kx, ky, kz = width / 2 / half, depth / (s_max - s_min), height / top

    def plan(x: float, s: float) -> Pt:
        return x * kx, depth / 2 - (s - s_min) * ky

    out: list[Part] = []
    for part in parts:
        if part[0] == "box":
            _, x0, x1, s0, s1, z0, z1, color = part
            cx, cy = plan((x0 + x1) / 2, (s0 + s1) / 2)
            out.append(box(cx, cy, z0 * kz, z1 * kz, (x1 - x0) * kx, (s1 - s0) * ky, color))
            continue
        _, positions, triangles, normals, color = part
        scaled = [(*plan(x, s), z * kz) for x, s, z in positions]
        triangles = outward(scaled, triangles)  # wound here: the s -> -y mirror inverts a mesh
        if normals is None:
            out.append(mesh_part(scaled, triangles, color))
            continue
        # Normals take the inverse scale, so the shade stays smooth after the stretch.
        shaded = []
        for nx, ns, nz in normals:
            v = (nx / kx, -ns / ky, nz / kz)  # +s is -y
            m = math.sqrt(sum(c * c for c in v))
            shaded.append((v[0] / m, v[1] / m, v[2] / m))
        low = [min(p[i] for p in scaled) for i in range(3)]
        high = [max(p[i] for p in scaled) for i in range(3)]
        out.append({"center": tuple((a + b) / 2 for a, b in zip(low, high, strict=True)),
                    "size": tuple(b - a for a, b in zip(low, high, strict=True)),
                    "color": color, "points": (), "shape": "mesh",
                    "mesh": {"positions": tuple(scaled), "normals": tuple(shaded),
                             "triangles": tuple(map(tuple, triangles))}})

    def rectangle(x0: float, x1: float, s0: float, s1: float) -> list[Pt]:
        return [plan(x0, s0), plan(x1, s0), plan(x1, s1), plan(x0, s1)]

    strokes = [polygon(rectangle(-FLANGE_W / 2, FLANGE_W / 2, 0, FLANGE_D), fill=BODY)]
    strokes += [polygon(rectangle(-1.0, 1.0, a[1], b[1]), fill=BODY) for a, b in arms]
    hull = _hull(shade_points)
    strokes.append(polygon([plan(x, s) for x, s in hull], fill=BODY))
    return tuple(strokes), tuple(out)


def _hull(points: list[Pt]) -> list[Pt]:
    """Convex hull of a point set (monotone chain), counter-clockwise."""
    def half(seq: list[Pt]) -> list[Pt]:
        out: list[Pt] = []
        for p in seq:
            while len(out) > 1 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                    - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    pts = sorted(set(points))
    return half(pts) + half(pts[::-1])
