"""Drywall accessories derived from the host faces (decision #103, the #85/#93 pattern).

The house's ``DrywallStandard`` names one bead per edge kind; this stage finds the edges:

* ``outside_corner`` — each reflex vertex of a room ring with gypsum on both faces, finished
  floor to ceiling less any tile band over it; and a gypsum soffit's free bottom edges;
* ``termination`` (J-bead) — where a gypsum arc meets a bare face along a ring (floor to
  ceiling), and along a banded gypsum layer whose edge stops over a bare face;
* ``tile_reveal``, ``door_l_bead``, ``window_corner`` / ``window_frame``, ``led_profile`` —
  ``resolve/drywall_trim_edges.py``.

Inside corners are paper tape and stay in the board's labour rate. Without a standard only
the window returns bill, on the library's generic beads.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient

from typehaus.findings import Finding
from typehaus.model.drywall import DrywallStandard
from typehaus.quantities import ft
from typehaus.resolve.drywall_led import drywall_standard, host_shadow_gap_runs
from typehaus.resolve.interior_trim_scope import face_function, face_is_gypsum, is_finish
from typehaus.resolve.model import ResolvedModel, ResolvedRoom
from typehaus.resolve.model_trim import ResolvedDrywallTrim
from typehaus.resolve.room_corners import (
    corner_kind,
    corners_only,
    point_and_outward,
    ring_vertices,
)
from typehaus.resolve.room_walls import _TOUCH_M, bounding_wall_arcs

# A corner probe stands this far along each face from the vertex: inside the board where
# it wraps a wall end, short of the next layer.
_CORNER_STEP_M = 0.003
# Mid-wall probe band above the finished floor, clear of base, tile and counters.
_WALL_PROBE = (1.2, 1.4)
# Arcs this close along the ring meet; a banded layer this far off the floor/ceiling stops.
_MEET_M = 0.05
_BAND_GAP_M = 0.025
_MIN_TRIM_M = 2 * 0.0254
_DEFAULT_STOCK_M = ft(10).meters
# A clear face carries ~1" mitre slivers where wall bodies meet; opened and closed by this
# they stop reading as reflex corners. Real returns (a 2 1/4" step) survive.
_SLIVER_M = 0.02
# A face is probed this far inside each band between layer edges.
_BAND_EPS_M = 1e-4


class TrimContext:
    """The standard, the material table and a wall-body cache for one pass."""

    def __init__(self, model: ResolvedModel, standard: DrywallStandard | None) -> None:
        self.model = model
        self.standard = standard
        self.materials = {m.tag: m for m in model.plan.library.materials}
        self.stock_m = standard.stock_length.meters if standard else _DEFAULT_STOCK_M
        products = {p.tag: p for p in model.plan.library.products}
        # A product's own stock length (an 8' LED profile) beats the standard's.
        self.stock_by_material = {
            tag: products[m.product_ref].stock_length.meters
            for tag, m in self.materials.items()
            if getattr(m, "product_ref", None) in products
            and products[m.product_ref].stock_length is not None}
        self.records: list[ResolvedDrywallTrim] = []
        self._bodies: dict[str, object] = {}

    def body(self, wall):
        from typehaus.resolve.wall_faces import wall_body

        if wall.tag not in self._bodies:
            self._bodies[wall.tag] = wall_body(wall, wall.z0_m, wall.z1_m)
        return self._bodies[wall.tag]

    def add(self, kind: str, room: str | None, storey: str, material: str, length_m: float,
            tags: tuple[str, ...]) -> None:
        if length_m < _MIN_TRIM_M:
            return
        stock = self.stock_by_material.get(material, self.stock_m)
        pieces = max(1, math.ceil(length_m / stock - 1e-9))
        self.records.append(ResolvedDrywallTrim(
            kind=kind, room=room, storey=storey, material_ref=material, length_m=length_m,
            pieces=pieces, tags=tuple(dict.fromkeys(tag for tag in tags if tag))))


def resolve_drywall_trims(plan, model: ResolvedModel) -> list[Finding]:
    from typehaus.resolve import drywall_trim_edges as edges

    standard, findings = drywall_standard(plan)
    findings.extend(host_shadow_gap_runs(model, standard))
    ctx = TrimContext(model, standard)
    edges.window_returns(ctx)
    if standard is not None:
        edges.led_profiles(ctx)
        for room in sorted(model.rooms, key=lambda r: r.uid):
            if len(room.clear_face) >= 3:
                _room_edges(ctx, room)
        edges.soffit_corners(ctx)
        edges.tile_reveals(ctx)
        edges.door_beads(ctx)
    model.drywall_trims = ctx.records
    return findings


def ceiling_z(model: ResolvedModel, room: ResolvedRoom, xy, fallback: float | None) -> float:
    """The room's ceiling face nearest ``xy``, else ``fallback`` (a sloped or open ceiling)."""
    point = Point(xy)
    best = min(((Polygon(c.outline).distance(point), c.z0_m) for c in model.ceilings
                if c.room_ref == room.tag and c.z0_m is not None and len(c.outline) >= 3),
               default=None)
    if best is not None:
        return best[1]
    return fallback if fallback is not None else room_floor(model, room) + 2.4


def room_floor(model: ResolvedModel, room: ResolvedRoom) -> float:
    from typehaus.resolve.room_floor import room_finished_floor_elevation

    return room_finished_floor_elevation(model, room)


def _clean_face(clear_face) -> Polygon:
    raw = Polygon(clear_face)
    joint = {"join_style": 2}
    clean = raw.buffer(-_SLIVER_M, **joint).buffer(_SLIVER_M, **joint)
    clean = clean.buffer(_SLIVER_M, **joint).buffer(-_SLIVER_M, **joint)
    return clean if clean.geom_type == "Polygon" and not clean.is_empty else raw


def top_at(model: ResolvedModel, room: ResolvedRoom, xy, walls) -> float:
    """The ceiling face at ``xy``, else the walls' body top there (a raked attic wall)."""
    from typehaus.resolve.geometry_walls import body_top_at

    tops = [body_top_at(wall, xy[0], xy[1]) for wall in walls if wall is not None]
    return ceiling_z(model, room, xy, min(tops) if tops else None)


def _room_edges(ctx: TrimContext, room: ResolvedRoom) -> None:
    model, standard = ctx.model, ctx.standard
    ring = corners_only(list(orient(_clean_face(room.clear_face), 1.0).exterior.coords)[:-1])
    perimeter = sum(math.dist(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))
    floor_z = room_floor(model, room)
    probe = (floor_z + _WALL_PROBE[0], floor_z + _WALL_PROBE[1])
    arcs = bounding_wall_arcs(model, room, ring, ctx.body)

    def wall_at(s: float):
        s %= perimeter
        hits = [(b - a, wall) for wall, (a, b) in arcs if a - 1e-9 <= s <= b + 1e-9]
        return max(hits, key=lambda hit: hit[0])[1] if hits else None

    def gypsum_at(s: float, z0: float, z1: float) -> bool:
        wall = wall_at(s)
        if wall is None:
            return False
        point, outward = point_and_outward(ring, s % perimeter)
        return face_is_gypsum(wall, point, outward, z0, z1, ctx.materials)

    # Outside corners: gypsum on both faces at the vertex.
    for s in ring_vertices(ring):
        if corner_kind(ring, s) != "outside":
            continue
        before, after = (s - _CORNER_STEP_M) % perimeter, s + _CORNER_STEP_M
        if not (gypsum_at(before, *probe) and gypsum_at(after, *probe)):
            continue
        vertex = ring[ring_vertices(ring).index(s)]
        walls = [w for w in (wall_at(before), wall_at(after)) if w is not None]
        top = top_at(model, room, vertex, walls)
        height = top - floor_z - _tile_cover(model, room, vertex, floor_z, top)
        ctx.add("outside_corner", room.tag, room.storey, standard.outside_corner_ref, height,
                (room.tag,))

    # Vertical J-bead where a gypsum arc meets a bare one.
    kinds = []
    for wall, (a, b) in arcs:
        a2, b2 = a + _TOUCH_M, b - _TOUCH_M
        if b2 - a2 < _MEET_M:  # nothing, or a ring-seam sliver of a wall reaching round
            continue
        point, outward = point_and_outward(ring, (a2 + b2) / 2.0)
        if _is_wall_end(wall, outward):
            continue  # a stub's end: the faces' board wraps it, two outside corners
        gyp = face_is_gypsum(wall, point, outward, *probe, ctx.materials)
        function = face_function(wall, point, outward, *probe)
        bare = function is not None and not is_finish(function)  # None: no wall up here
        kinds.append((a2, b2, "gypsum" if gyp else "bare" if bare else "other", wall))
        _banded_edges(ctx, room, wall, ring, (a2, b2), floor_z)
    for a, b, kind, wall in kinds:
        if kind != "gypsum":
            continue
        for end in (a, b):
            bare = next(((_inset(min((c, d), key=lambda e: _gap(end, e, perimeter)), c, d),
                          other_wall)
                         for c, d, other, other_wall in kinds
                         if other == "bare" and _meets(end, c, d, perimeter)), None)
            if bare is not None:
                height = _jbead_height(ctx, room, ring, perimeter, (_inset(end, a, b), wall),
                                       bare, floor_z)
                ctx.add("termination", room.tag, room.storey, standard.termination_ref,
                        height, (room.tag,))


def _jbead_height(ctx: TrimContext, room: ResolvedRoom, ring, perimeter: float, gypsum,
                  bare, floor_z: float) -> float:
    """The height over which ``gypsum``'s board meets ``bare``'s face, each ``(s, wall)``:
    open framing bays under a banded board end where the board begins."""
    (g_s, g_wall), (b_s, b_wall) = gypsum, bare
    g_xy, g_in = point_and_outward(ring, g_s % perimeter)
    b_xy, b_in = point_and_outward(ring, b_s % perimeter)
    top = top_at(ctx.model, room, g_xy, (g_wall,))
    # Faces change only at a layer band's edge, so one probe per interval between them.
    breaks = sorted({floor_z, top, *(z for wall in (g_wall, b_wall) for layer in wall.layers
                                     for z in layer.band(wall) if floor_z < z < top)})
    total = 0.0
    for lo, hi in zip(breaks, breaks[1:], strict=False):
        z0, z1 = lo + _BAND_EPS_M, hi - _BAND_EPS_M
        if z1 <= z0:
            continue
        function = face_function(b_wall, b_xy, b_in, z0, z1)
        if (function is not None and not is_finish(function)
                and face_is_gypsum(g_wall, g_xy, g_in, z0, z1, ctx.materials)):
            total += hi - lo
    return total


def _is_wall_end(wall, into_wall) -> bool:
    """Whether a face looking ``into_wall`` is the wall's end rather than one of its faces."""
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    return length > 1e-9 and abs((x1 - x0) * into_wall[0] + (y1 - y0) * into_wall[1]) > (
        0.9 * length)


def _inset(end: float, a: float, b: float) -> float:
    """A station just inside arc ``a..b`` from its ``end``: at the vertex itself the probe
    would look into the neighbouring wall."""
    step = min(_MEET_M, (b - a) / 2.0)
    return end + step if end == a else end - step


def _gap(s: float, e: float, perimeter: float) -> float:
    return min(abs(s - e), perimeter - abs(s - e))


def _meets(s: float, c: float, d: float, perimeter: float) -> bool:
    return any(_gap(s, e, perimeter) < _MEET_M for e in (c, d))


def _banded_edges(ctx: TrimContext, room: ResolvedRoom, wall, ring, span, floor_z: float):
    """Horizontal J-bead along a banded gypsum board whose edge stops over a bare face."""
    a, b = span
    point, outward = point_and_outward(ring, (a + b) / 2.0)
    top = top_at(ctx.model, room, point, (wall,))
    probe = Point(point[0] + outward[0] * 0.002, point[1] + outward[1] * 0.002)
    for layer in wall.layers:
        if (layer.is_cavity or layer.z0_m is None and layer.z1_m is None
                or getattr(ctx.materials.get(layer.material_ref), "gypsum_type", None) is None
                or len(layer.polygon) < 3 or Polygon(layer.polygon).distance(probe) > 0.01):
            continue
        z0, z1 = layer.band(wall)
        for edge, z_lo, z_hi in ((z0 > floor_z + _BAND_GAP_M, z0 - _MEET_M, z0 - 0.01),
                                 (z1 < top - _BAND_GAP_M, z1 + 0.01, z1 + _MEET_M)):
            if edge and not is_finish(face_function(wall, point, outward, z_lo, z_hi)):
                ctx.add("termination", room.tag, room.storey, ctx.standard.termination_ref,
                        b - a, (room.tag,))


def _tile_cover(model: ResolvedModel, room: ResolvedRoom, xy, floor_z: float,
                top: float) -> float:
    """Height of a finish-replacing band at ``xy`` (a tile surround wrapping the corner)."""
    spans = sorted((max(band.z0_m, floor_z), min(band.z1_m, top)) for band in model.panelings
                   if band.room == room.tag and band.replaces_wall_finish and band.outline
                   and band.z0_m is not None and band.z1_m is not None
                   and Polygon(band.outline).distance(Point(xy)) < _MEET_M)
    covered, reach = 0.0, floor_z
    for lo, hi in spans:
        lo = max(lo, reach)
        if hi > lo:
            covered += hi - lo
            reach = hi
    return covered


__all__ = ["TrimContext", "ceiling_z", "resolve_drywall_trims", "room_floor", "top_at"]
