"""A device box's drawn body (decision #93): its shape, raised cover or mud ring.

Built in the box's (tangent ``s``, normal ``n``, ``z``) frame, ``n`` = 0 on the host face
and positive into the room, ``z`` about the box centre, then placed at the bank's origin.
Every piece is a closed convex prism (``duct_mesh.prism``), so the mesh stays watertight
without booleans. A cover's device opening is a frame of four bars round the devices; the
device face fills it. The solid's ``outline``/``z0``/``z1`` stay the bounding prism.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.duct_mesh import prism
from typehaus.resolve.geometry_ir import GMesh

Point = tuple[float, float]
Opening = tuple[float, float, float, float]  # s0, s1, z0, z1 about the box centre

_ROUND_FACETS = 24
_CHAMFER_M = 0.125 * M_PER_IN  # the drawn/welded corner radius, as a chamfer
_SKIN_M = 0.0625 * M_PER_IN  # a cover's or ring's sheet: its flange under the plateau
_PLATEAU_INSET_M = 0.25 * M_PER_IN  # raised plateau inside the cover edge (representative)
_OPENING_MARGIN_M = 0.0625 * M_PER_IN  # the opening clears the device face all round
_RING_BORDER_M = 0.375 * M_PER_IN  # a 1-device mud ring's raised border round its opening
_FLAT_COVER_M = 0.125 * M_PER_IN  # a cover rise at or under this is a flat plate (RACO 753)


def box_mesh(origin: Point, tangent: Point, normal: Point, middle: float, *, width: float,
             height: float, depth: float, shape: str, mounting: str, cover_rise: float,
             openings: tuple[Opening, ...] = ()) -> GMesh:
    """The box body plus its surface cover (proud by ``depth + cover_rise``) or its
    ``flush_raceway`` ring (inside ``-depth..0``); a plain flush box is the body alone."""
    pieces: list[tuple[list[Point], float, float]] = []  # (s, z) ring, n0, n1
    body = (_round(width / 2) if shape == "round"
            else _chamfered(width / 2, height / 2, min(_CHAMFER_M, width / 4, height / 4)))
    if mounting == "surface":
        pieces.append((body, 0.0, depth))
        if cover_rise > 0:
            pieces += _cover(body, width, height, depth, cover_rise, openings)
    elif mounting == "flush_raceway" and 0 < cover_rise < depth:
        pieces.append((body, -depth, -cover_rise))
        pieces += _ring(body, width, height, cover_rise, openings)
    else:
        pieces.append((body, -depth, 0.0))

    def place(ring: list[Point], n: float) -> list[tuple[float, float, float]]:
        return [(origin[0] + tangent[0] * s + normal[0] * n,
                 origin[1] + tangent[1] * s + normal[1] * n, middle + z) for s, z in ring]

    return combine_meshes(*(prism(place(ring, n0), place(ring, n1)) for ring, n0, n1 in pieces))


def _cover(body: list[Point], width: float, height: float, depth: float, rise: float,
           openings: tuple[Opening, ...]) -> list[tuple[list[Point], float, float]]:
    if rise <= _FLAT_COVER_M:  # a flat cover: one plate, its centre KO not drawn
        return [(body, depth, depth + rise)]
    flange = [(body, depth, depth + _SKIN_M)]
    hw, hh = width / 2 - _PLATEAU_INSET_M, height / 2 - _PLATEAU_INSET_M
    return flange + _framed(hw, hh, _hole(openings, hw, hh), depth + _SKIN_M, depth + rise)


def _ring(body: list[Point], width: float, height: float, rise: float,
          openings: tuple[Opening, ...]) -> list[tuple[list[Point], float, float]]:
    """A mud ring: its flange on the box, its raised border round the device to the face."""
    flange = [(body, -rise, -rise + _SKIN_M)]
    hole = _hole(openings, width / 2 - _RING_BORDER_M, height / 2 - _PLATEAU_INSET_M)
    if hole is None:
        return flange
    s0, s1, z0, z1 = hole
    hw = min(width / 2, max(abs(s0), abs(s1)) + _RING_BORDER_M)
    hh = min(height / 2, max(abs(z0), abs(z1)) + _PLATEAU_INSET_M)
    return flange + _framed(hw, hh, hole, -rise + _SKIN_M, 0.0)


def _hole(openings: tuple[Opening, ...], hw: float, hh: float) -> Opening | None:
    """The devices' bounding opening, kept inside the plateau with a bar on every side."""
    if not openings:
        return None
    bar = _SKIN_M
    s0 = max(min(o[0] for o in openings) - _OPENING_MARGIN_M, -hw + bar)
    s1 = min(max(o[1] for o in openings) + _OPENING_MARGIN_M, hw - bar)
    z0 = max(min(o[2] for o in openings) - _OPENING_MARGIN_M, -hh + bar)
    z1 = min(max(o[3] for o in openings) + _OPENING_MARGIN_M, hh - bar)
    return (s0, s1, z0, z1) if s1 > s0 and z1 > z0 else None


def _framed(hw: float, hh: float, hole: Opening | None, n0: float,
            n1: float) -> list[tuple[list[Point], float, float]]:
    """A plateau ``2hw`` x ``2hh`` with ``hole`` cut out: four bars, or one block if blank."""
    if hole is None:
        return [(_rect(-hw, hw, -hh, hh), n0, n1)]
    s0, s1, z0, z1 = hole
    bars = (_rect(-hw, hw, z1, hh), _rect(-hw, hw, -hh, z0),
            _rect(-hw, s0, z0, z1), _rect(s1, hw, z0, z1))
    return [(bar, n0, n1) for bar in bars]


def _rect(s0: float, s1: float, z0: float, z1: float) -> list[Point]:
    return [(s0, z0), (s1, z0), (s1, z1), (s0, z1)]


def _chamfered(hw: float, hh: float, c: float) -> list[Point]:
    return [(-hw + c, -hh), (hw - c, -hh), (hw, -hh + c), (hw, hh - c),
            (hw - c, hh), (-hw + c, hh), (-hw, hh - c), (-hw, -hh + c)]


def _round(r: float) -> list[Point]:
    step = 2 * math.pi / _ROUND_FACETS
    return [(r * math.cos(i * step), r * math.sin(i * step)) for i in range(_ROUND_FACETS)]
