"""One builder per ``PlantType.form``, plus the espalier built off its trellis.

A form builder draws roughly unit-sized (height ~1, radius ~0.5) into a
:class:`~typehaus.resolve.plant_models.MeshBuilder`; ``build_prototype`` then normalises it
exactly. Triangle budgets (back faces counted) are asserted by ``tests/test_plant_models.py``.
"""

from __future__ import annotations

import math

from typehaus.resolve.plant_models import MeshBuilder

TRIANGLE_BUDGET = {"grass": 420, "perennial": 420, "groundcover": 420, "shrub": 500,
                   "tree": 620, "espalier": 1600}


def _polar(r: float, a: float, z: float) -> tuple[float, float, float]:
    return (r * math.cos(a), r * math.sin(a), z)


def grass(mesh: MeshBuilder, *, has_bloom: bool) -> None:
    """14-20 tapered blades arching out of a tight crown; seed wisps above when blooming."""
    rng = mesh.rng
    for _ in range(rng.randint(14, 17 if has_bloom else 20)):
        a = rng.uniform(0.0, 2.0 * math.pi)
        root = rng.uniform(0.0, 0.08)
        lean = rng.uniform(0.15, 0.45)
        tall = rng.uniform(0.6, 1.0)
        width = rng.uniform(0.035, 0.06)
        segments = rng.choice((3, 4))
        spine, widths = [], []
        for k in range(segments + 1):
            t = k / segments
            # Up fast, then over: the arch the bluestem holds and a sedge lets fall.
            r = root + lean * t * t
            z = tall * math.sin(t * math.pi / 2.0) * (1.0 - 0.25 * lean * t * t)
            spine.append(_polar(r, a, z))
            widths.append(width * (1.0 - t) if k < segments else 0.0)
        mesh.strip("foliage", spine, widths, (-math.sin(a), math.cos(a), 0.0))
    if has_bloom:
        for _ in range(rng.randint(5, 7)):
            a = rng.uniform(0.0, 2.0 * math.pi)
            r = rng.uniform(0.02, 0.18)
            spine = [_polar(r * 0.3, a, 0.55), _polar(r * 0.8, a, 0.85), _polar(r, a, 1.08)]
            mesh.strip("bloom", spine, [0.014, 0.009, 0.0], (-math.sin(a), math.cos(a), 0.0))


def _shell_leaves(mesh: MeshBuilder, count: int, *, dome: float, leaf: float,
                  flat: float = 1.0) -> None:
    """Leaf lozenges over a dome of height ``dome``, pointing out and up from the crown."""
    rng = mesh.rng
    for _ in range(count):
        a = rng.uniform(0.0, 2.0 * math.pi)
        s = math.sqrt(rng.uniform(0.0, 1.0))      # area-uniform over the dome
        r = 0.42 * s
        z = dome * math.sqrt(max(1.0 - s * s, 0.0)) * rng.uniform(0.75, 1.0) * flat
        tilt = rng.uniform(0.2, 0.9)
        along = (math.cos(a) * math.cos(tilt), math.sin(a) * math.cos(tilt), math.sin(tilt))
        across = (-math.sin(a), math.cos(a), 0.0)
        mesh.lozenge("foliage", _polar(r * 0.8, a, z * 0.85), along, across,
                     leaf * rng.uniform(0.8, 1.2), leaf * 0.45)


def perennial(mesh: MeshBuilder, *, has_bloom: bool) -> None:
    """A domed clump of leaf lozenges with florets scattered over its upper shell."""
    rng = mesh.rng
    _shell_leaves(mesh, rng.randint(46 if has_bloom else 60, 56 if has_bloom else 70),
                  dome=0.8, leaf=0.26)
    if has_bloom:
        for _ in range(rng.randint(12, 16)):
            a = rng.uniform(0.0, 2.0 * math.pi)
            s = rng.uniform(0.0, 0.8)
            z = 0.8 * math.sqrt(1.0 - s * s) + rng.uniform(0.05, 0.2)
            mesh.berry("bloom", _polar(0.4 * s, a, z), rng.uniform(0.035, 0.05))


def groundcover(mesh: MeshBuilder, *, has_bloom: bool) -> None:
    """A low mat of overlapping rosettes; normalised to its own height, so the type's short
    mature height is what makes it low."""
    rng = mesh.rng
    for _ in range(rng.randint(10, 13)):
        a = rng.uniform(0.0, 2.0 * math.pi)
        r = 0.36 * math.sqrt(rng.uniform(0.0, 1.0))
        cx, cy, _ = _polar(r, a, 0.0)
        cz = rng.uniform(0.2, 0.5)
        petals = 5
        for p in range(petals):
            b = a + 2.0 * math.pi * p / petals + rng.uniform(-0.2, 0.2)
            tilt = rng.uniform(0.25, 0.6)
            along = (math.cos(b) * math.cos(tilt), math.sin(b) * math.cos(tilt), math.sin(tilt))
            mesh.lozenge("foliage", (cx, cy, cz), along, (-math.sin(b), math.cos(b), 0.0),
                         0.16, 0.09)
        if has_bloom and rng.random() < 0.4:
            mesh.berry("bloom", (cx, cy, cz + 0.35), 0.04)


def shrub(mesh: MeshBuilder, *, has_bloom: bool) -> None:
    """4-5 lumpy foliage clusters on a few stems."""
    rng = mesh.rng
    count = rng.randint(4, 5)
    for n in range(count):
        a = 2.0 * math.pi * n / count + rng.uniform(-0.4, 0.4)
        r = rng.uniform(0.12, 0.26)
        z = rng.uniform(0.45, 0.7)
        centre = _polar(r, a, z)
        mesh.tube("stem", (0.0, 0.0, 0.0), (centre[0] * 0.7, centre[1] * 0.7, z * 0.6),
                  0.03, 0.015, sides=4)
        size = rng.uniform(0.2, 0.28)
        mesh.blob("foliage", centre, (size, size, size * 0.8))
    if has_bloom:
        for _ in range(6):
            a = rng.uniform(0.0, 2.0 * math.pi)
            mesh.berry("bloom", _polar(rng.uniform(0.0, 0.3), a, rng.uniform(0.85, 1.0)), 0.035)


def tree(mesh: MeshBuilder, *, has_bloom: bool) -> None:
    """A tapered trunk, 3-5 scaffold branches and blob canopy clusters."""
    rng = mesh.rng
    crown = 0.45
    mesh.tube("stem", (0.0, 0.0, 0.0), (0.0, 0.0, crown), 0.045, 0.032, sides=6)
    branches = rng.randint(3, 5)
    for n in range(branches):
        a = 2.0 * math.pi * n / branches + rng.uniform(-0.3, 0.3)
        tip = _polar(rng.uniform(0.2, 0.3), a, rng.uniform(0.62, 0.75))
        mesh.tube("stem", (0.0, 0.0, crown * rng.uniform(0.8, 1.0)), tip, 0.025, 0.012, sides=4)
        mesh.blob("foliage", tip, (0.2, 0.2, 0.17))
    mesh.blob("foliage", (0.0, 0.0, 0.85), (0.24, 0.24, 0.17))
    if has_bloom:
        for _ in range(10):
            a = rng.uniform(0.0, 2.0 * math.pi)
            mesh.berry("fruit", _polar(rng.uniform(0.15, 0.4), a, rng.uniform(0.55, 0.85)), 0.03)


FORM_BUILDERS = {"grass": grass, "perennial": perennial, "groundcover": groundcover,
                 "shrub": shrub, "tree": tree}


def espalier(mesh: MeshBuilder, *, spread: float, height: float, wires: tuple[float, ...],
             thickness: float, has_fruit: bool) -> None:
    """A trunk to the top wire and a pair of horizontal cordons on each wire, in metres.

    Local frame: x along the trellis, y across it, z up from the root. Cordons sit exactly
    at the wire heights; nothing leaves ``|x| <= spread/2``, ``|y| <= thickness/2`` or
    ``z <= height``.
    """
    rng = mesh.rng
    tiers = [w for w in wires if 0.0 < w <= height] or [height * 0.6]
    top = min(max(tiers) + 0.1, height)
    mesh.tube("stem", (0.0, 0.0, 0.0), (0.0, 0.0, top), 0.03, 0.018, sides=6)
    reach = spread / 2.0 * 0.95
    half_y = thickness / 2.0
    leaf = min(0.075, half_y * 0.9)
    for z in tiers:
        for side in (-1.0, 1.0):
            # Hold the cordon on the wire: a slight taper, no droop.
            mesh.tube("stem", (0.0, 0.0, z), (side * reach, 0.0, z), 0.016, 0.008, sides=4)
            stations = max(2, int(reach / 0.1))
            for s in range(1, stations + 1):
                x = side * reach * s / stations
                for _ in range(2):
                    b = rng.uniform(0.0, 2.0 * math.pi)
                    tilt = rng.uniform(0.3, 0.9)
                    along = (math.cos(b) * math.cos(tilt) * 0.5,
                             math.sin(b) * math.cos(tilt), math.sin(tilt))
                    norm = math.sqrt(sum(c * c for c in along))
                    along = (along[0] / norm, along[1] / norm, along[2] / norm)
                    # Keep the leaf inside the trellis plane's slab and under the top.
                    length = min(leaf, half_y / max(abs(along[1]), 1e-6) * 0.95,
                                 max(height - z, 0.01) / max(along[2], 1e-6) * 0.95)
                    mesh.lozenge("foliage", (x - side * 0.02, 0.0, z), along,
                                 (1.0, 0.0, 0.0), length, length * 0.5)
                if has_fruit and rng.random() < 0.18:
                    r = min(0.035, half_y * 0.9)
                    mesh.berry("fruit", (x, 0.0, max(z - r * 1.3, r)), r)
