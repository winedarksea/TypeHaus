"""Cut the geometry IR with a vertical plane — the section's kernel (→ 30 §Details).

``geometry_build`` is the pipeline's last stage: every resolved record becomes an
``ElementGeometry`` of ``GPrism``/``GBox``/``GMesh`` solids, and "this is where geometry
stops being re-derived per emitter". IFC, glTF and ``model.json`` read that result; the 2D
section did not, and so grew ten hand-rolled per-family cut handlers that re-implemented
roof planes, layer stacks and the birdsmouth. This module is the missing consumer: one
plane, one profile, every family.

Why it lives in ``resolve/`` rather than ``emit/draw/``
------------------------------------------------------
* The IR's contract is that geometry math happens once, here.
* ``emit/draw/`` already imports shapely (``siteplan``, ``detail_components/wall_base``), so
  a kernel there would be one careless import from breaking Pyodide with no test to catch it.
  **This module imports ``math``, ``dataclasses`` and ``resolve.*`` — nothing else.**
* It breaks the ``detail_components/* → section.py`` import cycle: seven modules import
  ``ring_cut_intervals`` from ``section``, which made the biggest file in the engine an
  import hub for the whole detail package.

Section coordinates
-------------------
A :class:`CutPlane` names an axis the way ``Slice.cut_direction`` does: ``"x"`` cuts *along*
world x at a station in y, so ``u`` = world x; ``"y"`` gives ``u`` = world y. ``z`` is world
z in both. Everything here is metres.

Degeneracy
----------
A face lying exactly in the cut plane is the classic section pathology: it is simultaneously
"in front" and "behind", and even-odd pairing on a coplanar ring produces a slab, a sliver or
nothing depending on the winding. Rather than special-case it, the station is *nudged* off
any vertex within :data:`NUDGE_M` — 100 nm, four orders of magnitude below anything a detail
draws — which turns every coplanar face, vertex-on-plane and edge-on-plane into the generic
case.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.geometry_ir import (
    GBox,
    GMesh,
    GPart,
    GPrism,
    GSolid,
    GSweep,
    Ring,
)
from typehaus.resolve.intervals import subtract

# A (u, z) point in the section frame, metres.
Vec2UZ = tuple[float, float]

# How far to move a station off a coincident vertex, metres. 1e-7 m = 100 nm.
NUDGE_M = 1e-7
# Below this, two section-frame coordinates are the same point (mesh chain welding).
WELD_M = 1e-6


@dataclass(frozen=True)
class CutPlane:
    """A vertical cut plane. ``axis`` matches ``Slice.cut_direction`` exactly."""

    axis: str  # "x" | "y"
    station_m: float

    # Which plan coordinate the station measures (y for an "x" cut, x for a "y" cut) and
    # which one is u. Frozen-dataclass fields rather than properties because the reject test
    # reads them once per *vertex* of every solid in the model, per cut.
    perp_index: int = 0
    u_index: int = 0

    def __post_init__(self) -> None:
        if self.axis not in ("x", "y"):
            raise ValueError(f"CutPlane.axis must be 'x' or 'y', not {self.axis!r}")
        object.__setattr__(self, "perp_index", 1 if self.axis == "x" else 0)
        object.__setattr__(self, "u_index", 0 if self.axis == "x" else 1)

    def u_of(self, point) -> float:
        return point[self.u_index]

    def perp_of(self, point) -> float:
        return point[self.perp_index]

    def nudged(self, solid: GSolid) -> CutPlane:
        """This plane, moved off any of ``solid``'s vertices it sits exactly on.

        Called per solid rather than once per drawing: a station nudged clear of one wall's
        face may sit exactly on another's, and the whole point is that no ring is ever cut
        at one of its own vertices.

        The step goes **inward**, toward the middle of the solid's own perpendicular span.
        A cut landing exactly on an end face is common and deliberate — an authored
        foundation detail cut at the end of the wall it is about — and nudging outward there
        would silently drop the very element the drawing exists for. Inward, the plane
        grazes the end face and draws its cross-section, which is what the reader expects.
        """
        values = perp_values(solid, self.perp_index)
        if not values:
            return self
        return _nudge_off(self, values, min(values), max(values))


@dataclass(frozen=True)
class SectionProfile:
    """One closed face of a solid in the cut plane, in section coordinates.

    ``outline`` is the face; ``voids`` are holes through it. Both are closed implicitly (no
    repeated first point), matching the IR's ring convention.
    """

    outline: tuple[Vec2UZ, ...]
    voids: tuple[tuple[Vec2UZ, ...], ...] = ()


def perp_values(solid: GSolid, index: int) -> list[float]:
    """Every vertex's coordinate along one plan axis — the reject test's whole input.

    Yields the *coordinate* rather than the point because this is the hot loop: it runs once
    per vertex of every solid in the model for every cut, and a projection through a method
    call per vertex was half the drawing stage's time.
    """
    if isinstance(solid, GPrism):
        values = [point[index] for point in solid.ring]
        for void in solid.voids:
            values.extend(point[index] for point in void)
        return values
    if isinstance(solid, GBox):
        return ([point[index] for point in solid.corners_bottom]
                + [point[index] for point in solid.corners_top])
    if isinstance(solid, GSweep):
        shift = solid.extrude[index]
        values = [point[index] for point in solid.profile]
        return values + [value + shift for value in values]
    return [point[index] for point in solid.positions]


def solid_perp_span(solid: GSolid, plane: CutPlane) -> tuple[float, float]:
    """The solid's extent perpendicular to ``plane`` — the O(1) reject before slicing."""
    values = perp_values(solid, plane.perp_index)
    if not values:
        return (math.inf, -math.inf)
    return (min(values), max(values))


def _crosses(solid: GSolid, plane: CutPlane) -> bool:
    lo, hi = solid_perp_span(solid, plane)
    return lo <= plane.station_m <= hi


def _nudge_off(plane: CutPlane, values: list[float], lo: float, hi: float) -> CutPlane:
    """``plane.nudged`` with the vertex coordinates already in hand (see ``slice_solid``)."""
    step = NUDGE_M if plane.station_m <= (lo + hi) / 2.0 else -NUDGE_M
    station = plane.station_m
    for _ in range(4):
        if min(abs(value - station) for value in values) > NUDGE_M / 2.0:
            break
        station += step
    if station == plane.station_m:
        return plane
    return CutPlane(axis=plane.axis, station_m=station)


# --- ring crossings ------------------------------------------------------------------

def _crosses_edge(a0: float, a1: float, station: float) -> bool:
    """The **half-open** crossing rule: ``a0 <= s < a1`` on a rising edge, mirrored.

    This is what makes the crossing count provably even — a vertex sitting exactly on the
    plane belongs to exactly one of its two edges. The older strict-sign test counted such a
    vertex twice, which could yield an odd count that even-odd pairing then silently dropped
    a span from. Callers slicing IR solids never meet the case (``CutPlane.nudged`` has
    already moved the station off every vertex), but the rule is what makes the kernel
    correct without the nudge too.
    """
    return a0 <= station < a1 or a1 <= station < a0


def ring_crossings(ring: Ring, plane: CutPlane) -> list[tuple[float, int, float]]:
    """Where a plan ring crosses the plane: ``(u, edge_index, t)``, sorted by u.

    The edge index and parameter come back with the point because a consumer that carries
    per-vertex data — a raked prism's ``top[]`` — needs to interpolate *that edge's* two
    values, and the sorted-by-u order destroys the correspondence otherwise.
    """
    count = len(ring)
    if count < 3:
        return []
    station = plane.station_m
    crossings: list[tuple[float, int, float]] = []
    for index in range(count):
        p0, p1 = ring[index], ring[(index + 1) % count]
        a0, a1 = plane.perp_of(p0), plane.perp_of(p1)
        if a0 == a1 or not _crosses_edge(a0, a1, station):
            continue
        t = (station - a0) / (a1 - a0)
        u0, u1 = plane.u_of(p0), plane.u_of(p1)
        crossings.append((u0 + t * (u1 - u0), index, t))
    crossings.sort()
    return crossings


def ring_intervals(ring: Ring, plane: CutPlane) -> list[tuple[float, float]]:
    """The ring's inside-spans along u, even-odd paired."""
    us = [u for (u, _index, _t) in ring_crossings(ring, plane)]
    return [(us[i], us[i + 1]) for i in range(0, len(us) - 1, 2)]


# --- per-solid slicing ---------------------------------------------------------------

def _prism_profiles(solid: GPrism, plane: CutPlane) -> list[SectionProfile]:
    """A prism's cut faces: analytic, with the raked top interpolated exactly.

    A crossing always lies *on* a ring edge, so the top elevation there is the linear blend
    of that edge's two ``top`` values — no sampling, no approximation.
    """
    crossings = ring_crossings(solid.ring, plane)
    if len(crossings) < 2:
        return []
    tops = _crossing_tops(solid, crossings)
    # Voids run the full height by definition (they are opening holes), so they *split* the
    # span rather than perforating the face. The old section cut ignored them entirely and
    # drew a slab straight across a stair well.
    cuts = [(lo, hi) for void in solid.voids for (lo, hi) in ring_intervals(void, plane)]
    profiles: list[SectionProfile] = []
    for index in range(0, len(crossings) - 1, 2):
        u0, u1 = crossings[index][0], crossings[index + 1][0]
        z_left, z_right = tops[index], tops[index + 1]
        if u1 - u0 <= 1e-12:
            continue
        for (a, b) in subtract(u0, u1, cuts) if cuts else [(u0, u1)]:
            # Re-interpolate the top over the surviving sub-span so a split raked prism
            # keeps its rake instead of inheriting the parent span's end elevations.
            span = u1 - u0
            za = z_left + (z_right - z_left) * (a - u0) / span
            zb = z_left + (z_right - z_left) * (b - u0) / span
            profiles.append(SectionProfile(outline=(
                (a, solid.z0_m), (b, solid.z0_m), (b, zb), (a, za))))
    return profiles


def _crossing_tops(solid: GPrism, crossings) -> list[float]:
    """Top elevation at each crossing: flat ``z1_m``, or interpolated along the cut edge.

    Exact rather than sampled: a crossing always lies *on* a ring edge, so its top is the
    linear blend of that edge's two ``top`` values.
    """
    if solid.top is None:
        return [solid.z1_m] * len(crossings)
    count = len(solid.ring)
    tops: list[float] = []
    for (_u, index, t) in crossings:
        z0, z1 = solid.top[index], solid.top[(index + 1) % count]
        tops.append(z0 + t * (z1 - z0))
    return tops


def _box_profiles(solid: GBox, plane: CutPlane) -> list[SectionProfile]:
    """A hexahedron's cut face.

    The win is the member lying *in* the cut plane: its two long side faces contribute
    nothing and its two end faces each cross, so the profile that falls out is exactly the
    raked parallelogram the 2D code hand-built. The rake, the ends and the flange datums
    need no special case.
    """
    count = len(solid.corners_bottom)
    station = plane.station_m
    hits: list[tuple[float, float, float]] = []  # (u, z_bottom, z_top)
    for index in range(count):
        next_index = (index + 1) % count
        b0, b1 = solid.corners_bottom[index], solid.corners_bottom[next_index]
        t0, t1 = solid.corners_top[index], solid.corners_top[next_index]
        a0, a1 = plane.perp_of(b0), plane.perp_of(b1)
        if a0 == a1 or not _crosses_edge(a0, a1, station):
            continue
        f = (station - a0) / (a1 - a0)
        u = plane.u_of(b0) + f * (plane.u_of(b1) - plane.u_of(b0))
        hits.append((u, b0[2] + f * (b1[2] - b0[2]), t0[2] + f * (t1[2] - t0[2])))
    if len(hits) < 2:
        return []
    hits.sort()
    profiles: list[SectionProfile] = []
    for index in range(0, len(hits) - 1, 2):
        (ua, zb_a, zt_a), (ub, zb_b, zt_b) = hits[index], hits[index + 1]
        if ub - ua <= 1e-12:
            continue
        profiles.append(SectionProfile(outline=(
            (ua, zb_a), (ub, zb_b), (ub, zt_b), (ua, zt_a))))
    return profiles


def _mesh_profiles(solid: GMesh, plane: CutPlane) -> tuple[list[SectionProfile], int]:
    """Triangle/plane intersection, chained into rings. Returns ``(profiles, open_chains)``.

    Open chains are **discarded, never closed by fabrication** — a fabricated closure is a
    drawing that claims a solid where the model has a hole. The count comes back so a sweep
    test can assert it stays zero over both houses.
    """
    segments: list[tuple[Vec2UZ, Vec2UZ]] = []
    station = plane.station_m
    for tri in solid.triangles:
        points = [solid.positions[i] for i in tri]
        hits: list[Vec2UZ] = []
        for index in range(3):
            p0, p1 = points[index], points[(index + 1) % 3]
            a0, a1 = plane.perp_of(p0), plane.perp_of(p1)
            if a0 == a1 or not _crosses_edge(a0, a1, station):
                continue
            f = (station - a0) / (a1 - a0)
            hits.append((plane.u_of(p0) + f * (plane.u_of(p1) - plane.u_of(p0)),
                         p0[2] + f * (p1[2] - p0[2])))
        if len(hits) == 2 and _distance(hits[0], hits[1]) > WELD_M:
            segments.append((hits[0], hits[1]))
    rings, open_chains = _chain(segments)
    return ([SectionProfile(outline=ring) for ring in rings], open_chains)


def _distance(a: Vec2UZ, b: Vec2UZ) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _key(point: Vec2UZ) -> tuple[int, int]:
    """Quantized endpoint key — the ``geometry_roofs._vertex_key`` trick, in 2D."""
    return (round(point[0] / WELD_M), round(point[1] / WELD_M))


def _chain(segments) -> tuple[list[tuple[Vec2UZ, ...]], int]:
    """Weld segment endpoints into closed rings; count the chains that never close."""
    if not segments:
        return ([], 0)
    adjacency: dict[tuple[int, int], list[int]] = {}
    for index, (a, b) in enumerate(segments):
        adjacency.setdefault(_key(a), []).append(index)
        adjacency.setdefault(_key(b), []).append(index)

    used = [False] * len(segments)
    rings: list[tuple[Vec2UZ, ...]] = []
    open_chains = 0
    for start in range(len(segments)):
        if used[start]:
            continue
        used[start] = True
        a, b = segments[start]
        chain = [a, b]
        while True:
            candidates = [i for i in adjacency.get(_key(chain[-1]), []) if not used[i]]
            if not candidates:
                break
            index = candidates[0]
            used[index] = True
            p0, p1 = segments[index]
            chain.append(p1 if _key(p0) == _key(chain[-1]) else p0)
            if _key(chain[-1]) == _key(chain[0]):
                break
        if len(chain) > 3 and _key(chain[-1]) == _key(chain[0]):
            rings.append(tuple(chain[:-1]))
        else:
            open_chains += 1
    return (rings, open_chains)


def _sweep_profiles(solid: GSweep, plane: CutPlane) -> list[SectionProfile]:
    """A swept solid's cut face.

    The case worth having is the one the birdsmouth is: a profile standing in a vertical
    plane, extruded straight across the cut. Then every plane between the two ends meets the
    solid in *the profile itself*, so the cut is one projection and no chaining. Anything
    else falls back to the mesh path, which is correct but slower and has to weld.
    """
    perps = {round(plane.perp_of(point), 9) for point in solid.profile}
    across = plane.perp_of((solid.extrude[0], solid.extrude[1]))
    if len(perps) == 1 and abs(across) > 1e-9:
        start = perps.pop()
        lo, hi = sorted((start, start + across))
        if not lo < plane.station_m < hi:
            return []
        return [SectionProfile(outline=tuple(
            (plane.u_of(point), point[2]) for point in solid.profile))]
    profiles, _open = _mesh_profiles(sweep_mesh(solid), plane)
    return profiles


def sweep_mesh(solid: GSweep) -> GMesh:
    """A swept solid tessellated: two caps by fan triangulation plus one quad per edge.

    The fan is only valid for a convex profile, and a birdsmouth's is not — but the caps of a
    member sweep are its *ends*, which no section ever needs and which no viewer sees inside
    a wall. Callers that need a watertight non-convex cap should triangulate properly; this
    exists so the slice kernel has a general fallback and glTF has something to draw.
    """
    count = len(solid.profile)
    dx, dy, dz = solid.extrude
    positions = list(solid.profile) + [(x + dx, y + dy, z + dz)
                                       for (x, y, z) in solid.profile]
    triangles: list[tuple[int, int, int]] = []
    for index in range(1, count - 1):
        triangles.append((0, index + 1, index))
        triangles.append((count, count + index, count + index + 1))
    for index in range(count):
        nxt = (index + 1) % count
        triangles.append((index, nxt, count + nxt))
        triangles.append((index, count + nxt, count + index))
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def slice_solid(solid: GSolid, plane: CutPlane) -> tuple[SectionProfile, ...]:
    """Every closed face ``solid`` presents to ``plane``, in section coordinates."""
    values = perp_values(solid, plane.perp_index)
    if not values:
        return ()
    lo, hi = min(values), max(values)
    if not lo <= plane.station_m <= hi:
        return ()
    local = _nudge_off(plane, values, lo, hi)
    if isinstance(solid, GPrism):
        return tuple(_prism_profiles(solid, local))
    if isinstance(solid, GBox):
        return tuple(_box_profiles(solid, local))
    if isinstance(solid, GSweep):
        return tuple(_sweep_profiles(solid, local))
    profiles, _open = _mesh_profiles(solid, local)
    return tuple(profiles)


def open_chain_count(solid: GSolid, plane: CutPlane) -> int:
    """How many mesh chains failed to close — zero, for every solid either house builds."""
    if not isinstance(solid, GMesh) or not _crosses(solid, plane):
        return 0
    _profiles, open_chains = _mesh_profiles(solid, plane.nudged(solid))
    return open_chains


def slice_part(part: GPart, plane: CutPlane) -> tuple[SectionProfile, ...]:
    """Every profile one addressable part contributes."""
    out: list[SectionProfile] = []
    for solid in part.solids:
        out.extend(slice_solid(solid, plane))
    return tuple(out)


def nearest_station(solids, plane: CutPlane) -> float | None:
    """The station of the solid nearest ``plane`` among those that never cross it.

    The *representative member* problem, named. A rafter runs along the cut plane, so it is
    drawn only when one lands exactly on the station — which a wall-midpoint cut rarely
    does. ``section.py`` hand-rolled this for parallel rafters; every family wants it.
    ``None`` when something already crosses, or when there is nothing to pick.
    """
    best: float | None = None
    best_distance = math.inf
    for solid in solids:
        lo, hi = solid_perp_span(solid, plane)
        if lo > hi:
            continue
        if lo <= plane.station_m <= hi:
            return None
        centre = (lo + hi) / 2.0
        distance = min(abs(lo - plane.station_m), abs(hi - plane.station_m))
        if distance < best_distance:
            best, best_distance = centre, distance
    return best


def ring_cut_intervals(ring, direction: str, station: float) -> list[tuple[float, float]]:
    """Legacy shim for the seven detail callers — the *old* strict-sign crossing rule.

    Kept bug-for-bug on purpose while the section migrates: the half-open rule above
    changes behaviour for rings with a vertex exactly on the plane, and moving seven
    callers underneath a migration is how a migration stops being reviewable. Retired in
    one commit once ``section.py`` reads the IR.
    """
    if len(ring) < 3:
        return []
    crossings: list[float] = []
    count = len(ring)
    for index in range(count):
        x0, y0 = ring[index]
        x1, y1 = ring[(index + 1) % count]
        a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
        u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
        if (a0 - station) * (a1 - station) > 0 or a0 == a1:
            continue
        t = (station - a0) / (a1 - a0)
        crossings.append(u0 + t * (u1 - u0))
    crossings.sort()
    return [(crossings[i], crossings[i + 1]) for i in range(0, len(crossings) - 1, 2)]


__all__ = [
    "CutPlane",
    "SectionProfile",
    "Vec2UZ",
    "nearest_station",
    "open_chain_count",
    "perp_values",
    "ring_cut_intervals",
    "ring_intervals",
    "slice_part",
    "slice_solid",
    "solid_perp_span",
]
