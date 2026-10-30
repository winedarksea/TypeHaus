"""Which countertop edges a fabricator finishes, and the radius on every corner.

Each outline edge is probed by a thin strip just outside it, and split where what it meets
changes:

- ``wall``      a wall's layers stand there (the slab is scribed to it),
- ``seam``      another slab is there (a field joint),
- ``abutment``  a placeable rising well above the top stands there (a tall pantry, a fridge),
- ``finished``  open air: the eased, polished edge.

A slide-in range is not an abutment: it barely clears the top, and that edge is seen. A
run of one kind shorter than an inch joins its neighbour, and that edge is recorded in
``mixed_edges`` so the drawing never mislabels it silently
(``advisory.countertop_fabrication`` grades it).

Radii: a convex corner between two finished edges takes the authored ``corner_radius``; a
concave corner takes the inside stress-relief radius; any corner meeting a wall, seam or
abutment stays square, because it is scribed or butted.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.model.plan import PlanModel
from typehaus.resolve.fillet import vertex_is_convex
from typehaus.resolve.geometry_countertops import countertop_top_z
from typehaus.resolve.model import ResolvedCountertop, ResolvedModel, ResolvedWindowStool
from typehaus.resolve.overlay import union_all

EDGE_WALL, EDGE_SEAM, EDGE_ABUTMENT, EDGE_FINISHED = "wall", "seam", "abutment", "finished"
#: Probe precedence when one probe touches two things.
_PRECEDENCE = (EDGE_WALL, EDGE_SEAM, EDGE_ABUTMENT, EDGE_FINISHED)
_IN_M = 0.0254
#: Stone yards' stress-relief radius at an inside corner; a material may ask for more.
INSIDE_CORNER_RADIUS_IN = 0.375
#: The probe runs from just off the edge to 1/2" out.
_PROBE_NEAR_M, _PROBE_FAR_M = _IN_M / 16.0, _IN_M / 2.0
#: Shorter than this, a run of one kind is not an edge of its own (it joins a neighbour).
_MIN_SPAN_M = _IN_M
#: Under this, a sliver is where two faces meet at a corner, not a disagreement.
_NOISE_SPAN_M = _IN_M / 4.0
#: A neighbour rising more than this above the top abuts it; a range does not.
_ABUTMENT_RISE_M = 6.0 * _IN_M
_ABUTTING_KINDS = frozenset({"Furniture", "Fixture", "Appliance", "Equipment"})

#: ``window_stool_ring``'s fixed order: front, horn end, horn back, jamb side, back, jamb
#: side, horn back, horn end.
STOOL_EDGE_KINDS = (EDGE_FINISHED, EDGE_FINISHED, EDGE_WALL, EDGE_WALL, EDGE_WALL,
                    EDGE_WALL, EDGE_WALL, EDGE_FINISHED)
#: ``window_stool_ring``'s two shoulder-notch vertices.
_NOTCH_VERTICES = (3, 6)


def inside_radius_m(plan: PlanModel, material_ref: str) -> float:
    """The material's inside-corner radius (a solid-surface bulletin may ask for more)."""
    material = next((item for item in plan.library.materials if item.tag == material_ref),
                    None)
    inches = getattr(material, "inside_corner_radius_in", None) or INSIDE_CORNER_RADIUS_IN
    return inches * _IN_M


def stool_corner_radii(front_m: float, inside_m: float) -> tuple[float, ...]:
    """One radius per ``window_stool_ring`` vertex: front corners, then the shoulder notches.

    Square (empty) unless the stool authors a front radius: a milled wood stool keeps its
    shop's own notch, and only a fabricated stool is drawn by ``haus countertops``.
    """
    if front_m <= 0.0:
        return ()
    return (front_m, front_m, 0.0, inside_m, 0.0, 0.0, inside_m, 0.0)


def stool_wrapping_return(stool: ResolvedWindowStool, finish_m: float,
                          bead_radius_m: float) -> ResolvedWindowStool:
    """A fabricated stool is templated after the drywall returns: its shoulder notches wrap
    the finished board corner, and round to the corner bead's radius where that is larger,
    so the stone seats against a bullnose. Idempotent, so a re-resolve may repeat it."""
    radii = tuple(max(radius, bead_radius_m) if index in _NOTCH_VERTICES else radius
                  for index, radius in enumerate(stool.corner_radii_m))
    return replace(stool, notch_inset_m=finish_m, corner_radii_m=radii)


def classify_countertop_edges(model: ResolvedModel) -> None:
    """Split every slab's edges by kind and set its corner radii, in place.

    A vertex is inserted wherever one edge changes kind (the corner slab's south edge is
    open air, then the pantry), so each outline edge carries exactly one kind.
    """
    for index, top in enumerate(model.countertops):
        ring, kinds, mixed = _edge_kinds(model, top)
        radii = corner_radii(ring, kinds, top.corner_radius_m,
                             inside_radius_m(model.plan, top.material_ref))
        model.countertops[index] = replace(top, outline=ring, edge_kinds=kinds,
                                           corner_radii_m=radii, mixed_edges=mixed)


def corner_radii(ring, kinds, exposed_m: float, inside_m: float) -> tuple[float, ...]:
    """Per vertex i (between edge i-1 and edge i); all square unless a radius is authored."""
    if exposed_m <= 0.0:
        return (0.0,) * len(ring)
    radii = []
    for index in range(len(ring)):
        prev, here, nxt = ring[index - 1], ring[index], ring[(index + 1) % len(ring)]
        cross = ((here[0] - prev[0]) * (nxt[1] - here[1])
                 - (here[1] - prev[1]) * (nxt[0] - here[0]))
        if abs(cross) <= 1e-12:
            radii.append(0.0)  # a split along one straight edge
        elif not vertex_is_convex(ring, index):
            radii.append(inside_m)
        elif kinds[index - 1] == kinds[index] == EDGE_FINISHED:
            radii.append(exposed_m)
        else:
            radii.append(0.0)
    return tuple(radii)


def _edge_kinds(model: ResolvedModel, top: ResolvedCountertop):
    z_top = countertop_top_z(model, top)
    walls = union_all([Polygon(layer.polygon) for wall in model.walls
                       if wall.storey == top.storey
                       and (z_top is None or wall.z0_m < z_top < wall.z1_m)
                       for layer in wall.layers if len(layer.polygon) >= 3])
    seams = union_all([Polygon(other.outline) for other in model.countertops
                       if other.storey == top.storey and other.tag != top.tag])
    tall = union_all([Polygon(obj.footprint) for obj in model.canvas_objects
                      if obj.storey == top.storey and obj.kind in _ABUTTING_KINDS
                      and obj.tag not in top.hosts and len(obj.footprint) >= 3
                      and z_top is not None and obj.body_z0_m is not None
                      and obj.body_z1_m is not None and obj.body_z0_m < z_top
                      and obj.body_z1_m > z_top + _ABUTMENT_RISE_M])
    neighbours = ((EDGE_WALL, walls), (EDGE_SEAM, seams), (EDGE_ABUTMENT, tall))
    ring: list[tuple[float, float]] = []
    kinds: list[str] = []
    mixed: list[int] = []
    outline = top.outline
    for index, start in enumerate(outline):
        end = outline[(index + 1) % len(outline)]
        spans, absorbed = _edge_spans(start, end, neighbours)
        for t0, kind in spans:
            if absorbed:
                mixed.append(len(kinds))
            ring.append((start[0] + (end[0] - start[0]) * t0,
                         start[1] + (end[1] - start[1]) * t0))
            kinds.append(kind)
    return tuple(ring), tuple(kinds), tuple(mixed)


def _edge_spans(start, end, neighbours) -> tuple[list[tuple[float, str]], bool]:
    """``[(t_start, kind), ...]`` along one edge, and whether a sliver was absorbed.

    The probe is a strip 1/16"..1/2" outside the edge; what it meets is painted onto the
    edge's parameter by precedence. A span under ``_MIN_SPAN_M`` is not a fabricated edge
    of its own: it joins its longer neighbour and the edge is reported mixed.
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 1e-12:
        return [(0.0, EDGE_FINISHED)], False
    ux, uy = dx / length, dy / length
    nx, ny = uy, -ux  # outward on a counter-clockwise ring
    strip = Polygon([(start[0] + nx * _PROBE_NEAR_M, start[1] + ny * _PROBE_NEAR_M),
                     (end[0] + nx * _PROBE_NEAR_M, end[1] + ny * _PROBE_NEAR_M),
                     (end[0] + nx * _PROBE_FAR_M, end[1] + ny * _PROBE_FAR_M),
                     (start[0] + nx * _PROBE_FAR_M, start[1] + ny * _PROBE_FAR_M)])
    covers: dict[str, list[tuple[float, float]]] = {}
    for kind, geometry in neighbours:
        if geometry.is_empty:
            continue
        hit = strip.intersection(geometry)
        for part in getattr(hit, "geoms", [hit]):
            coords = list(getattr(part, "exterior", part).coords) if not part.is_empty else []
            ts = [((x - start[0]) * ux + (y - start[1]) * uy) / length for x, y in coords]
            if ts and max(ts) - min(ts) > 1e-9:
                covers.setdefault(kind, []).append((max(0.0, min(ts)), min(1.0, max(ts))))
    breaks = sorted({0.0, 1.0, *(t for spans in covers.values() for pair in spans
                                 for t in pair)})
    pieces: list[list] = []  # [t0, t1, kind]
    for a, b in zip(breaks, breaks[1:], strict=False):
        if b - a <= 1e-9:
            continue
        mid = (a + b) / 2.0
        kind = next((k for k in _PRECEDENCE[:-1]
                     if any(t0 <= mid <= t1 for t0, t1 in covers.get(k, ()))), EDGE_FINISHED)
        if pieces and pieces[-1][2] == kind:
            pieces[-1][1] = b
        else:
            pieces.append([a, b, kind])
    absorbed = False
    while len(pieces) > 1:
        short = min(range(len(pieces)), key=lambda i: pieces[i][1] - pieces[i][0])
        sliver = (pieces[short][1] - pieces[short][0]) * length
        if sliver >= _MIN_SPAN_M:
            break
        absorbed = absorbed or sliver >= _NOISE_SPAN_M
        left = pieces[short - 1] if short > 0 else None
        right = pieces[short + 1] if short + 1 < len(pieces) else None
        keep = left if right is None or (left is not None and (left[1] - left[0])
                                         >= (right[1] - right[0])) else right
        keep[0], keep[1] = min(keep[0], pieces[short][0]), max(keep[1], pieces[short][1])
        del pieces[short]
        merged: list[list] = []
        for piece in pieces:
            if merged and merged[-1][2] == piece[2]:
                merged[-1][1] = piece[1]
            else:
                merged.append(piece)
        pieces = merged
    return [(piece[0], piece[2]) for piece in pieces], absorbed
