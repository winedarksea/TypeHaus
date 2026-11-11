"""The geometry and layer walk behind ``mep.supply_freeze_exposure``.

Two questions: how much of a supply run's centreline lies in an exterior wall's stud bay
(:func:`cavity_pieces`), and what temperature a steady-state walk from the room to the design
outdoor air puts on the pipe's outboard face there (:func:`pipe_plane_profile`).

The walk reads the RESOLVED layers at the pipe, not the assembly card, so a banded layer or a
cut-down wall is what it is on the wall. The bay is the CAVITY path: a framed layer
contributes no R of its own, only the ``is_cavity`` fill layers inside it do, and a bay with
no ``CavityFill`` is credited zero (``analysis._layer_rsi`` would bill it as solid wood).
Layers outboard of a back-vented rainscreen cavity are cut off by
``glaser.glaser_layers``, the same rule the condensation check applies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.checks.building_science.glaser import (
    EXTERIOR_SURFACE_R_US,
    INTERIOR_SURFACE_R_US,
    glaser_layers,
)
from typehaus.quantities import M_PER_IN

#: Lengths under this are a vertex clipping the ring, not pipe in the bay.
MIN_PIECE_M = 0.125 * M_PER_IN
_REACH_M = 3.0  # half-length of the through-thickness probe line
_Z_TOL_M = 1e-6


@dataclass(frozen=True)
class FreezeAdvisory:
    """House advisory constants. Judgement, not code: nothing here is a published limit."""

    #: Water freezes at 0 C. Physical, not a code number.
    freezing_f: float = 32.0
    #: Margin the pipe plane must clear above freezing. The walk is steady-state at the
    #: design hour and leaves out stud and fastener bridging, convection around the pipe,
    #: wind-driven infiltration and a thermostat setback. 10 F is a judgement.
    margin_f: float = 10.0

    @property
    def threshold_f(self) -> float:
        return self.freezing_f + self.margin_f


@dataclass(frozen=True)
class Piece:
    """A stretch of centreline inside one wall's bay and z band."""

    a: tuple[float, float]
    b: tuple[float, float]
    za: float
    zb: float

    @property
    def length_m(self) -> float:
        return math.hypot(math.dist(self.a, self.b), self.zb - self.za)


@dataclass(frozen=True)
class Profile:
    temperature_f: float
    inboard_r: float  # US R: room film + layers inboard of the pipe's outboard face
    outboard_r: float  # US R: layers outboard of it + outdoor film
    continuous_r: float  # the part of outboard_r a non-bay INSULATION layer carries
    continuous_note: str
    depth_in: float  # pipe's outboard face, measured from the room face
    unfilled: tuple[str, ...]  # framed layers at the pipe with no CavityFill
    missing: tuple[str, ...]  # layers whose material has no r_per_inch


def wall_frame(wall) -> tuple[tuple[float, float], Any] | None:
    """``(outward unit vector, structure ring)``; None when the wall has no framed bay."""
    from shapely.geometry import Polygon

    structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
    polys = [Polygon(ly.polygon) for ly in wall.layers
             if len(ly.polygon) >= 3 and ly.thickness_m > 0]
    if (structure is None or not structure.framed or len(structure.polygon) < 3
            or len(polys) < 2 or len(wall.axis) < 2):
        return None
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    run = math.hypot(bx - ax, by - ay)
    if run < 1e-9:
        return None
    normal = (-(by - ay) / run, (bx - ax) / run)
    first, last = polys[0].centroid, polys[-1].centroid
    sign = 1.0 if (last.x - first.x) * normal[0] + (last.y - first.y) * normal[1] >= 0 else -1.0
    ring = Polygon(structure.polygon)
    return ((normal[0] * sign, normal[1] * sign), ring) if ring.is_valid else None


def cavity_pieces(path, z, ring, z0: float, z1: float, cuts: list[tuple]) -> list[Piece]:
    """Centreline pieces inside ``ring`` and ``[z0, z1]``, less rough openings.

    ``cuts`` is ``[(footprint, low, high)]``; an opening is removed from a leg whose z range
    meets its band. A leg with no plan length (a riser) counts where its point is in the ring.
    """
    from shapely.geometry import LineString, Point

    out: list[Piece] = []
    for i in range(len(path) - 1):
        a, b, za, zb = tuple(path[i]), tuple(path[i + 1]), z[i], z[i + 1]
        if max(za, zb) < z0 - _Z_TOL_M or min(za, zb) > z1 + _Z_TOL_M:
            continue
        if a == b:
            if ring.covers(Point(a)):
                lo, hi = max(min(za, zb), z0), min(max(za, zb), z1)
                if hi - lo >= MIN_PIECE_M:
                    out.append(Piece(a, b, lo, hi))
            continue
        line = LineString([a, b])
        for footprint, low, high in cuts:
            if min(za, zb) < high and max(za, zb) > low:
                line = line.difference(footprint)
        inside = line.intersection(ring)
        for part in getattr(inside, "geoms", [inside]):
            if part.is_empty or part.geom_type != "LineString":
                continue
            (p, q) = part.coords[0], part.coords[-1]
            total = math.dist(a, b)
            ta, tb = (math.dist(a, p) / total, math.dist(a, q) / total)
            za_p, zb_p = za + (zb - za) * ta, za + (zb - za) * tb
            clipped = _clip_z(p, q, za_p, zb_p, z0, z1)
            if clipped is not None and clipped.length_m >= MIN_PIECE_M:
                out.append(clipped)
    return out


def _clip_z(p, q, za: float, zb: float, z0: float, z1: float) -> Piece | None:
    """The part of a sloped piece whose z lies in ``[z0, z1]``."""
    lo, hi = 0.0, 1.0
    if abs(zb - za) > 1e-12:
        t0, t1 = sorted(((z0 - za) / (zb - za), (z1 - za) / (zb - za)))
        lo, hi = max(lo, t0), min(hi, t1)
    elif not z0 - _Z_TOL_M <= za <= z1 + _Z_TOL_M:
        return None
    if hi <= lo:
        return None

    def at(t: float) -> tuple[float, float]:
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    return Piece(at(lo), at(hi), za + (zb - za) * lo, za + (zb - za) * hi)


def vent_trimmed(wall, assembly) -> list:
    """The wall's resolved layers up to the vent plane ``glaser_layers`` stops at."""
    kept = glaser_layers(list(assembly.default_lining) + list(assembly.layers))
    last = kept[-1].name if kept else None
    layers = list(wall.layers)
    stop = max((i for i, ly in enumerate(layers) if last in (ly.name, ly.cavity_host)),
               default=len(layers) - 1)
    return layers[:stop + 1]


def pipe_plane_profile(wall, layers, library, point, z: float, outward, radius_m: float,
                       indoor_f: float, outdoor_f: float) -> Profile:
    """Steady-state temperature on the outboard face of a pipe at ``point``, height ``z``."""
    from shapely.geometry import LineString, Polygon

    probe = LineString([(point[0] - outward[0] * _REACH_M, point[1] - outward[1] * _REACH_M),
                        (point[0] + outward[0] * _REACH_M, point[1] + outward[1] * _REACH_M)])

    def span(layer) -> tuple[float, float] | None:
        hit = probe.intersection(Polygon(layer.polygon))
        if hit.is_empty:
            return None
        ts = [(x - point[0]) * outward[0] + (y - point[1]) * outward[1]
              for part in getattr(hit, "geoms", [hit])
              for x, y in getattr(part, "coords", ())]
        return (min(ts), max(ts)) if ts else None

    face = radius_m  # outboard face of the pipe wall, outward of the centreline
    inboard = INTERIOR_SURFACE_R_US
    outboard = EXTERIOR_SURFACE_R_US
    continuous = 0.0
    note = ""
    unfilled, missing = [], []
    room_face = face
    for layer in layers:
        if len(layer.polygon) < 3 or layer.thickness_m <= 0:
            continue
        lo_z, hi_z = layer.band(wall)
        if not lo_z - _Z_TOL_M <= z <= hi_z + _Z_TOL_M:
            continue
        found = span(layer)
        if found is None:
            continue
        a, b = found
        room_face = min(room_face, a)
        if layer.framed and not layer.is_cavity:
            if not any(o.is_cavity and o.cavity_host == layer.name for o in layers):
                unfilled.append(layer.name)
            continue  # the bay path: only its fill layers carry R
        material = library.material(layer.material_ref)
        if material is None or material.r_per_inch is None:
            missing.append(layer.name)
            continue
        r_in = material.r_per_inch / M_PER_IN  # R per metre of depth
        inboard += r_in * max(0.0, min(b, face) - a)
        beyond = r_in * max(0.0, b - max(a, face))
        outboard += beyond
        if beyond > 0 and layer.function == "insulation" and not layer.is_cavity:
            continuous += beyond
            note += f"{beyond / r_in / M_PER_IN:.2g}\" {material.name}; "
    swing = indoor_f - outdoor_f
    temperature = indoor_f - swing * inboard / (inboard + outboard)
    return Profile(temperature, inboard, outboard, continuous, note.rstrip("; "),
                   (face - room_face) / M_PER_IN, tuple(unfilled), tuple(missing))
