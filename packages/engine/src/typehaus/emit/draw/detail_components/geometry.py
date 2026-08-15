"""Shared primitives every detail component is built from.

Two groups:

* **Emitters** (``closed_region``, ``flashing_nodes``) — turn a boundary into ordinary
  ``Polyline``/``Hatch`` IR nodes carrying a ``detail-component:<name>`` tag. Deliberately
  *not* new ``Symbol`` names: the writers already render polylines and hatches correctly and
  keep them hit-testable, whereas an unknown ``Symbol`` degrades to a bare circle in
  ``DetailCanvas.tsx`` and to a marker glyph in ``pdf_writer.py``.
* **Resolvers** (``wall_faces``, ``layer_intervals``, ``outboard_is_high``,
  ``slab_at_junction``) — read the live cut and the resolved planes around it. Components
  derive their geometry from these rather than freezing authored coordinates, so a geometry
  edit moves the flashing with the face it laps.

Section coordinates throughout: ``u`` is the in-section axis, ``z`` is world z. Resolvers
return **inches** unless their name says ``_m``; the cutter itself works in metres.
"""

from __future__ import annotations

import math

from typehaus.emit.draw.detail_components.config import LAYER
from typehaus.emit.draw.scene import Hatch, IRNode, Polyline
from typehaus.quantities import M_PER_IN


def closed_region(points, tag: str, material: str | None, pattern: str | None,
                  lineweight: float = 0.18) -> list[IRNode]:
    """A closed region as an optional hatch fill plus its tagged outline."""
    pts = tuple(points)
    nodes: list[IRNode] = []
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer=LAYER, material=material))
    nodes.append(Polyline(points=pts, layer=LAYER, closed=True, lineweight=lineweight,
                          tag=f"detail-component:{tag}"))
    return nodes


def rect_points(u0: float, z0: float, u1: float, z1: float):
    return ((u0, z0), (u1, z0), (u1, z1), (u0, z1))


def rect_region(u0: float, z0: float, u1: float, z1: float, tag: str,
                material: str | None, pattern: str | None,
                lineweight: float = 0.18) -> list[IRNode]:
    """``closed_region`` over a rectangle given in any corner order."""
    return closed_region(rect_points(min(u0, u1), min(z0, z1), max(u0, u1), max(z0, z1)),
                         tag, material, pattern, lineweight)


def path_from_steps(start_uz, steps) -> list[tuple[float, float]]:
    """Polyline from a start point plus a list of ``(du, dz)`` steps.

    Flashing profiles are naturally written as a sequence of legs — "up 2.4, out to the
    cladding face, down 4.2" — and reading them that way is what makes a profile reviewable
    against the reference drawing. Ported from the reference ``detail_utils._path_from_steps``.
    """
    u, z = float(start_uz[0]), float(start_uz[1])
    pts = [(u, z)]
    for du, dz in steps:
        u += float(du)
        z += float(dz)
        pts.append((u, z))
    return pts


def thicken_polyline(points, thickness: float,
                     miter_min_dot: float = 0.25) -> list[tuple[float, float]]:
    """Thicken a centreline into a closed constant-width polygon (pure-Python port).

    ``miter_min_dot`` clamps the miter at sharp corners so right-angle flashing profiles keep
    constant thickness without spiking to infinity at a 180° reversal.
    """
    pts = [(float(u), float(z)) for (u, z) in points]
    if len(pts) < 2:
        raise ValueError("need at least 2 points")

    seg_norms: list[tuple[float, float]] = []
    for (u0, z0), (u1, z1) in zip(pts, pts[1:]):
        nx, nz = -(z1 - z0), (u1 - u0)
        mag = math.hypot(nx, nz) or 1e-9
        seg_norms.append((nx / mag, nz / mag))

    vnorms: list[tuple[float, float]] = [(0.0, 0.0)] * len(pts)
    vnorms[0] = seg_norms[0]
    vnorms[-1] = seg_norms[-1]
    for i in range(1, len(pts) - 1):
        n0, n1 = seg_norms[i - 1], seg_norms[i]
        mx, mz = n0[0] + n1[0], n0[1] + n1[1]
        mag = math.hypot(mx, mz)
        if mag < 1e-6:
            vnorms[i] = n1
            continue
        mx, mz = mx / mag, mz / mag
        denom = max(mx * n1[0] + mz * n1[1], miter_min_dot)
        vnorms[i] = (mx / denom, mz / denom)

    half = thickness / 2.0
    outer = [(u + half * nx, z + half * nz) for (u, z), (nx, nz) in zip(pts, vnorms)]
    inner = [(u - half * nx, z - half * nz) for (u, z), (nx, nz) in zip(pts, vnorms)]
    return outer + inner[::-1]


def flashing_nodes(centerline, thickness: float | None = None, *,
                   material: str = "metal", tag: str = "flashing",
                   lineweight: float = 0.45) -> list[IRNode]:
    """Sheet-metal flashing as a thickened polyline: metal fill plus a closed outline."""
    from typehaus.emit.draw.detail_components.config import SHEET_METAL

    if len(centerline) < 2:
        return []
    thick = SHEET_METAL.thickness_in if thickness is None else thickness
    poly = tuple(thicken_polyline(centerline, thick))
    return [
        Hatch(boundary=poly, pattern="metal", layer=LAYER, material=material),
        Polyline(points=poly, layer=LAYER, closed=True, lineweight=lineweight,
                 tag=f"detail-component:{tag}"),
    ]


# --- resolvers over the live cut ----------------------------------------------

def condition_opening(model, cond):
    """The ``ResolvedOpening`` a condition is about, or None.

    ``opening_perimeter`` conditions carry the *opening's* tag in ``element_tags`` — not a
    wall tag — so every consumer that wants "the walls of this condition" has to go through
    the opening's ``host_wall`` to find one.
    """
    for tag in cond.element_tags:
        opening = next((o for o in model.openings if o.tag == tag), None)
        if opening is not None:
            return opening
    return None


def condition_walls(model, cond) -> list:
    """Every resolved wall a condition names — directly, or via its opening's host."""
    walls = [w for w in (model.wall(tag) for tag in cond.element_tags) if w is not None]
    if not walls:
        opening = condition_opening(model, cond)
        if opening is not None:
            host = model.wall(opening.host_wall)
            if host is not None:
                walls = [host]
    return walls


def _cut_intervals(ring, direction: str, station: float):
    from typehaus.emit.draw.section import _ring_cut_intervals

    return _ring_cut_intervals(ring, direction, station)


def wall_cut_bounds_m(wall, direction: str, station: float):
    """``(u_lo, u_hi)`` in **metres** across every layer the cut crosses, or ``(None, None)``."""
    bounds: list[float] = []
    for layer in wall.layers:
        for (a, b) in _cut_intervals(layer.polygon, direction, station):
            bounds.extend((a, b))
    if not bounds:
        return None, None
    return min(bounds), max(bounds)


def outboard_is_high(wall, direction: str, station: float) -> bool | None:
    """True when the wall's outermost layer sits at the high end of the section axis.

    Read from the assembly, not from the drawing: layers are ordered interior→exterior, so
    the last layer sits on the outboard face. Inferring the outdoor side from the crop
    instead would just reflect the crop's own asymmetry back at us.
    """
    depth = wall.depth_layers()
    if len(depth) < 2:
        return None
    first = _cut_intervals(depth[0].polygon, direction, station)
    last = _cut_intervals(depth[-1].polygon, direction, station)
    if not first or not last:
        return None
    return sum(last[0]) > sum(first[0])


def layer_intervals(wall, direction: str, station: float) -> dict:
    """``{layer.name: (u_lo_in, u_hi_in, function)}`` for every layer the cut crosses.

    Cavity fills are skipped: they share their host STRUCTURE layer's polygon, so
    including them double-reports that band — most visibly as bay batts counted into
    the "continuous insulation" total.
    """
    out: dict = {}
    for layer in wall.layers:
        if getattr(layer, "is_cavity", False):
            continue
        ivs = _cut_intervals(layer.polygon, direction, station)
        if ivs:
            lo = min(min(iv) for iv in ivs)
            hi = max(max(iv) for iv in ivs)
            out[layer.name] = (lo / M_PER_IN, hi / M_PER_IN, layer.function)
    return out


def face_of(interval, is_outboard_high: bool, *, outer: bool) -> float:
    """The outer (or inner) face position of one layer interval."""
    lo, hi = interval[0], interval[1]
    if outer:
        return hi if is_outboard_high else lo
    return lo if is_outboard_high else hi


def outermost_with_function(intervals: dict, function: str):
    """Outermost interval carrying ``function`` (furring / cladding / insulation …)."""
    hits = [iv for iv in intervals.values() if iv[2] == function]
    return hits[-1] if hits else None


def wall_in_frame(wall, direction: str, station: float, crop) -> bool:
    """Whether the cut crosses ``wall`` and its cut interval overlaps the crop's u-window."""
    lo, hi = wall_cut_bounds_m(wall, direction, station)
    if lo is None:
        return False
    (cu0, _), (cu1, _) = crop
    return lo <= max(cu0, cu1) and hi >= min(cu0, cu1)


#: How far a slab edge may sit from a wall face and still count as meeting it (metres, ~6").
_SLAB_EDGE_TOLERANCE_M = 0.15


def slab_at_junction(model, crop, direction, station, face_u_m):
    """The floor slab whose cut edge meets a wall face inside the crop, or None.

    Only a slab *below the crop midpoint* qualifies: the detail is about the floor a wall
    bears on, so a suspended deck sitting at the junction plane itself (the main-floor deck
    at a rim junction) is not the slab edge a thermal break or a liner base belongs to.
    Picks the highest qualifying slab so a stacked structure resolves to the one bearing here.
    """
    (_cu0, cz0), (_cu1, cz1) = crop
    lo_z, hi_z = min(cz0, cz1), max(cz0, cz1)
    mid_z = (lo_z + hi_z) / 2.0
    best = None
    for solid in model.solids:
        if solid.category != "slab" or not (lo_z <= solid.z1_m < mid_z):
            continue
        for (a, b) in _cut_intervals(solid.outline, direction, station):
            lo, hi = min(a, b), max(a, b)
            if lo - _SLAB_EDGE_TOLERANCE_M <= face_u_m <= hi + _SLAB_EDGE_TOLERANCE_M:
                if best is None or solid.z1_m > best.z1_m:
                    best = solid
                break
    return best


#: How far the junction plane may sit outside a floor band and still belong to it (metres).
_BAND_STRADDLE_TOLERANCE_M = 0.05


def floor_band_at(model, junction_z_m):
    """``(z0_m, z1_m)`` of the framed floor band the junction plane passes through, or None.

    The rim band's depth is the joist depth — a property of the floor structure, not of either
    wall — so it is read off the members rather than assumed. The junction plane may be the
    band's top (platform framing: the subfloor is the plane the wall above starts from) or its
    bottom (the joists bear on the plate below), so the test is straddling, not equality.
    """
    band = None
    for floor in model.floors:
        for member in floor.members:
            if member.category not in ("joist", "rim"):
                continue
            low, high = min(member.z0_m, member.z1_m), max(member.z0_m, member.z1_m)
            if not (low - _BAND_STRADDLE_TOLERANCE_M <= junction_z_m
                    <= high + _BAND_STRADDLE_TOLERANCE_M):
                continue
            if band is None or (high - low) > (band[1] - band[0]):
                band = (low, high)
    return band


def is_weather_exposed(wall) -> bool:
    """Whether this wall presents a weather face — i.e. carries cladding over its structure.

    An interior partition has no rain to shed, so the drawing must not flash its junctions:
    a Z-flashing on a bedroom partition is linework that describes a building that does not
    exist. Read from the assembly (a cladding layer outboard of the structure), never from
    the tag or the storey.
    """
    return any(layer.function == "cladding" and not layer.is_cavity
               for layer in wall.layers)
