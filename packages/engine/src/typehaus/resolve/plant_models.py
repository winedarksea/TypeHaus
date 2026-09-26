"""Procedural low-poly plant models: prototypes the viewer and the GLB both instance.

Each :class:`PlantType` gets ``VARIANTS`` seeded prototypes built by its ``form``
(``resolve/plant_forms.py``) in UNIT space — spread 1 (a circle of radius 0.5), height 1,
root at the origin, z up — which a plant scales to its own spread and height. An espaliered
plant is not a shared prototype: its model is built from its trellis, in metres.

Deterministic by construction: every random draw comes from ``random.Random(seed string)``,
which hashes a string the same way on every run (``hash()`` is salted and never used).
Coordinates round to ``QUANTUM`` (unit space: under 1 mm on any catalog plant) when a model
is built, so both renderers draw the same numbers. Normals are area-weighted vertex normals
over each part's own indexed triangles — what three.js ``computeVertexNormals`` produces —
so model.json ships no normals and the viewer derives the same ones the GLB carries.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

Vec3 = tuple[float, float, float]

VARIANTS = 3
QUANTUM = 1e-3
ROLES = ("foliage", "bloom", "stem", "fruit")
# Absent stem material: the foliage colour at this factor.
STEM_DARKEN = 0.55
_DEFAULT_FOLIAGE = "#6f8c4a"


@dataclass(frozen=True)
class PlantPart:
    """One role's triangles. ``two_sided`` marks thin surfaces (blades, leaves) that must
    read from behind: the viewer draws them double-sided, the GLB duplicates them reversed."""

    role: str
    positions: tuple[Vec3, ...]
    triangles: tuple[tuple[int, int, int], ...]
    two_sided: bool = False

    @property
    def normals(self) -> tuple[Vec3, ...]:
        return vertex_normals(self.positions, self.triangles)


@dataclass(frozen=True)
class PlantPrototype:
    ref: str
    parts: tuple[PlantPart, ...]
    form: str
    type_ref: str = ""
    # Unit prototypes are 1 tall; an espalier's is its own height in metres.
    height: float = 1.0

    @property
    def triangle_count(self) -> int:
        return sum(len(p.triangles) * (2 if p.two_sided else 1) for p in self.parts)

    def shade(self, part: PlantPart) -> tuple[float, ...]:
        """Base-to-tip gradient, 0 at the root and 1 at the top."""
        h = self.height or 1.0
        return tuple(min(max(z / h, 0.0), 1.0) for _, _, z in part.positions)


def vertex_normals(positions, triangles) -> tuple[Vec3, ...]:
    acc = [[0.0, 0.0, 0.0] for _ in positions]
    for a, b, c in triangles:
        pa, pb, pc = positions[a], positions[b], positions[c]
        ux, uy, uz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
        vx, vy, vz = pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2]
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        for i in (a, b, c):
            acc[i][0] += n[0]
            acc[i][1] += n[1]
            acc[i][2] += n[2]
    out = []
    for x, y, z in acc:
        length = math.sqrt(x * x + y * y + z * z)
        out.append((x / length, y / length, z / length) if length > 1e-12 else (0.0, 0.0, 1.0))
    return tuple(out)


@dataclass
class MeshBuilder:
    """Accumulates triangles per (role, two_sided) while a form builds."""

    rng: random.Random
    _parts: dict[tuple[str, bool], tuple[list[Vec3], list[tuple[int, int, int]]]] = field(
        default_factory=dict)

    def _bucket(self, role: str, two_sided: bool):
        return self._parts.setdefault((role, two_sided), ([], []))

    def add(self, role: str, points: list[Vec3], tris: list[tuple[int, int, int]],
            two_sided: bool = False) -> None:
        positions, triangles = self._bucket(role, two_sided)
        base = len(positions)
        positions.extend(points)
        triangles.extend((a + base, b + base, c + base) for a, b, c in tris)

    # --- primitives ------------------------------------------------------------------------
    def strip(self, role: str, spine: list[Vec3], widths: list[float], side: Vec3) -> None:
        """A tapered ribbon along ``spine``; a zero width at the tip closes it to a point."""
        points: list[Vec3] = []
        tris: list[tuple[int, int, int]] = []
        for k, ((x, y, z), w) in enumerate(zip(spine, widths, strict=True)):
            half = w / 2.0
            if half <= 0.0 and k == len(spine) - 1:
                points.append((x, y, z))
                i = len(points) - 1
                tris.append((i - 2, i - 1, i))
                break
            points.append((x - side[0] * half, y - side[1] * half, z - side[2] * half))
            points.append((x + side[0] * half, y + side[1] * half, z + side[2] * half))
            if k:
                i = len(points) - 4
                tris.extend(((i, i + 1, i + 3), (i, i + 3, i + 2)))
        self.add(role, points, tris, two_sided=True)

    def lozenge(self, role: str, base: Vec3, along: Vec3, across: Vec3, length: float,
                width: float) -> None:
        """A leaf: a diamond from ``base`` along ``along``, widest at 40% of its length."""
        bx, by, bz = base
        mid = 0.4 * length
        half = width / 2.0
        points = [
            base,
            (bx + along[0] * mid - across[0] * half, by + along[1] * mid - across[1] * half,
             bz + along[2] * mid - across[2] * half),
            (bx + along[0] * length, by + along[1] * length, bz + along[2] * length),
            (bx + along[0] * mid + across[0] * half, by + along[1] * mid + across[1] * half,
             bz + along[2] * mid + across[2] * half),
        ]
        self.add(role, points, [(0, 1, 2), (0, 2, 3)], two_sided=True)

    def blob(self, role: str, centre: Vec3, radii: Vec3, lumpiness: float = 0.15,
             subdivisions: int = 1) -> None:
        """A lumpy icosphere, closed and outward-wound."""
        points, tris = icosphere(subdivisions)
        cx, cy, cz = centre
        rx, ry, rz = radii
        placed = []
        for x, y, z in points:
            k = 1.0 + self.rng.uniform(-lumpiness, lumpiness)
            placed.append((cx + x * rx * k, cy + y * ry * k, cz + z * rz * k))
        self.add(role, placed, tris)

    def tube(self, role: str, p0: Vec3, p1: Vec3, r0: float, r1: float, sides: int = 5) -> None:
        """A tapered, uncapped prism from ``p0`` to ``p1``."""
        axis = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        u, v = _frame(axis)
        points: list[Vec3] = []
        for centre, r in ((p0, r0), (p1, r1)):
            for s in range(sides):
                a = 2.0 * math.pi * s / sides
                ca, sa = math.cos(a) * r, math.sin(a) * r
                points.append((centre[0] + u[0] * ca + v[0] * sa,
                               centre[1] + u[1] * ca + v[1] * sa,
                               centre[2] + u[2] * ca + v[2] * sa))
        tris: list[tuple[int, int, int]] = []
        for s in range(sides):
            t = (s + 1) % sides
            tris.extend(((s, t, sides + t), (s, sides + t, sides + s)))
        self.add(role, points, tris)

    def berry(self, role: str, centre: Vec3, r: float) -> None:
        """An octahedron: a floret or a fruit."""
        cx, cy, cz = centre
        points = [(cx + r, cy, cz), (cx - r, cy, cz), (cx, cy + r, cz), (cx, cy - r, cz),
                  (cx, cy, cz + r), (cx, cy, cz - r)]
        tris = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        self.add(role, points, tris)

    # --- output ----------------------------------------------------------------------------
    def normalise_unit(self) -> None:
        """Fit the whole model to spread 1 (radius 0.5) and height 1; nothing below 0."""
        everything = [p for positions, _ in self._parts.values() for p in positions]
        if not everything:
            return
        reach = max(math.hypot(x, y) for x, y, _ in everything) or 1.0
        top = max(z for _, _, z in everything) or 1.0
        for positions, _ in self._parts.values():
            positions[:] = [(x * 0.5 / reach, y * 0.5 / reach, max(z / top, 0.0))
                            for x, y, z in positions]

    def clamp(self, half_x: float, half_y: float, top: float) -> None:
        """Hold every vertex inside ``|x| <= half_x``, ``|y| <= half_y``, ``0 <= z <= top``."""
        for positions, _ in self._parts.values():
            positions[:] = [(min(max(x, -half_x), half_x), min(max(y, -half_y), half_y),
                             min(max(z, 0.0), top)) for x, y, z in positions]

    def parts(self, ndigits: int = 3) -> tuple[PlantPart, ...]:  # 3 == -log10(QUANTUM)
        out = []
        for role in ROLES:
            for two_sided in (True, False):
                bucket = self._parts.get((role, two_sided))
                if not bucket or not bucket[1]:
                    continue
                positions, triangles = bucket
                rounded = tuple(tuple(round(c, ndigits) + 0.0 for c in p) for p in positions)
                out.append(PlantPart(role=role, positions=rounded,  # type: ignore[arg-type]
                                     triangles=tuple(triangles), two_sided=two_sided))
        return tuple(out)


def _frame(axis: Vec3) -> tuple[Vec3, Vec3]:
    """Two unit vectors perpendicular to ``axis`` and to each other."""
    length = math.sqrt(sum(c * c for c in axis)) or 1.0
    a = (axis[0] / length, axis[1] / length, axis[2] / length)
    helper = (0.0, 0.0, 1.0) if abs(a[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _cross(helper, a)
    lu = math.sqrt(sum(c * c for c in u))
    u = (u[0] / lu, u[1] / lu, u[2] / lu)
    return u, _cross(a, u)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def icosphere(subdivisions: int) -> tuple[list[Vec3], list[tuple[int, int, int]]]:
    t = (1.0 + math.sqrt(5.0)) / 2.0
    raw = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
           (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    points = [_unit(p) for p in raw]
    tris = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
            (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8),
            (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(subdivisions):
        cache: dict[tuple[int, int], int] = {}

        def mid(i: int, j: int, cache=cache) -> int:
            key = (min(i, j), max(i, j))
            if key not in cache:
                a, b = points[i], points[j]
                points.append(_unit(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)))
                cache[key] = len(points) - 1
            return cache[key]

        tris = [t for a, b, c in tris
                for t in ((a, mid(a, b), mid(c, a)), (b, mid(b, c), mid(a, b)),
                          (c, mid(c, a), mid(b, c)), (mid(a, b), mid(b, c), mid(c, a)))]
    return points, tris


def _unit(p) -> Vec3:
    length = math.sqrt(sum(c * c for c in p))
    return (p[0] / length, p[1] / length, p[2] / length)


# --- the catalog's colours --------------------------------------------------------------------
def _darken(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")[:6]
    r, g, b = (int(h[k:k + 2], 16) for k in (0, 2, 4))
    return "#" + "".join(f"{round(c * factor):02x}" for c in (r, g, b))


def role_materials(ptype) -> dict[str, str]:
    """Material tag per role; an absent role falls back to the foliage material."""
    return {"foliage": ptype.foliage_material,
            "bloom": ptype.bloom_material or ptype.foliage_material,
            "stem": ptype.stem_material or ptype.foliage_material,
            "fruit": ptype.fruit_material or ptype.bloom_material or ptype.foliage_material}


def role_colors(ptype, materials_by_tag: dict) -> dict[str, str]:
    """Render hex per role, read off ``Material.color``; a fallen-back stem is darkened."""
    def color(tag: str) -> str:
        material = materials_by_tag.get(tag)
        value = getattr(material, "color", None) or _DEFAULT_FOLIAGE
        return value if value.startswith("#") else "#" + value

    out = {role: color(tag) for role, tag in role_materials(ptype).items()}
    if not ptype.stem_material:
        out["stem"] = _darken(out["foliage"], STEM_DARKEN)
    return out


# --- entry points -----------------------------------------------------------------------------
def prototype_ref(type_tag: str, k: int) -> str:
    return f"{type_tag}#{k}"


def build_prototype(ptype, k: int) -> PlantPrototype:
    from typehaus.resolve.plant_forms import FORM_BUILDERS

    mesh = MeshBuilder(rng=random.Random(f"{ptype.tag}#{k}"))
    # A tree's or a vegetable's "bloom" worth drawing is its fruit.
    flag = (ptype.fruit_material if ptype.form in ("tree", "vegetable")
            else ptype.bloom_material)
    FORM_BUILDERS[ptype.form](mesh, has_bloom=bool(flag))
    mesh.normalise_unit()
    return PlantPrototype(ref=prototype_ref(ptype.tag, k), parts=mesh.parts(), form=ptype.form,
                          type_ref=ptype.tag)


def pick_variant(uid: str) -> tuple[int, float, float, float]:
    """``(variant, rotation, spread factor, height factor)`` seeded by the plant's uid.

    The factors only ever shrink, so a drawn plant stays inside its bounding solid.
    """
    rng = random.Random(f"plant:{uid}")
    return (rng.randrange(VARIANTS), rng.uniform(0.0, 2.0 * math.pi),
            rng.uniform(0.9, 1.0), rng.uniform(0.85, 1.0))


def build_espalier(uid: str, type_ref: str, *, spread_m: float, height_m: float,
                   wire_heights_m, thickness_m, has_fruit: bool) -> PlantPrototype:
    from typehaus.resolve.plant_forms import espalier

    mesh = MeshBuilder(rng=random.Random(f"espalier:{uid}"))
    espalier(mesh, spread=spread_m, height=height_m, wires=tuple(wire_heights_m),
             thickness=thickness_m, has_fruit=has_fruit)
    mesh.clamp(spread_m / 2.0, thickness_m / 2.0, height_m)
    return PlantPrototype(ref=f"espalier:{uid}", parts=mesh.parts(), form="espalier",
                          type_ref=type_ref, height=height_m)
