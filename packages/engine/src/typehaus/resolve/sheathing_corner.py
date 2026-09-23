"""Sheathing at an L corner: panels meet edge to face, never overlapping.

Every other layer at an L mitres on the angular bisector (``topology._clip_l_corner``). A
structural panel is not cut on a mitre: one wall's sheathing runs through to the far face
of its neighbour's sheathing, covering that panel's edge, and the other's edge butts the
through panel's back. The pair's plan area is unchanged; what moves is which wall owns the
corner square, and so which wall is billed and drawn for it.

``ResolvedJunction.sheathing_through`` names the through wall. It defaults to the junction's
``framing_owner`` — the wall whose studs already run through the corner carries its panel
through too — so the choice is deterministic and needs no authoring. No authored override
exists: a ``Node`` carries no junction rules today.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from shapely import intersection as _boundary_meet
from shapely.geometry import Polygon

from typehaus.resolve.model import ResolvedJunction, ResolvedLayer, ResolvedWall, Ring
from typehaus.resolve.overlay import difference, intersection, union_all

_SHEATHING = "sheathing"
_SHARED_EDGE_M = 1e-4  # two clipped bands that meet on the mitre share an edge this long
_TOUCH_M = 1e-6


def _sheathing(wall: ResolvedWall) -> list[tuple[int, ResolvedLayer]]:
    return [(index, layer) for index, layer in enumerate(wall.layers)
            if layer.function == _SHEATHING and not layer.is_cavity
            and len(layer.polygon) >= 3]


def _share_mitre(a: Polygon, b: Polygon) -> bool:
    # Within a micron: the two halves of one mitre are cut separately and need not agree
    # to the last bit, so an exact boundary intersection can come back as two points.
    return bool(_boundary_meet(b.boundary, a.buffer(_TOUCH_M)).length > _SHARED_EDGE_M)


def butt_sheathing(walls: dict[str, ResolvedWall], junction: ResolvedJunction,
                  unclipped: dict[str, dict[int, Ring]],
                  normalize: Callable[[Any, Ring], Ring]) -> None:
    """Re-cut the mitred sheathing pair(s) at one L so ``junction.sheathing_through`` runs through.

    ``unclipped`` holds each wall's layer rings before the mitre — bands already extended
    past the node, so a band intersected with the pair's union runs to the neighbour's far
    face. ``normalize`` is topology's ring normaliser, passed in to keep one ring convention.
    """
    through = junction.sheathing_through
    others = [item.wall_tag for item in junction.incidents if item.wall_tag != through]
    if through not in walls or len(others) != 1 or others[0] not in walls:
        return
    butting = others[0]
    run_wall, butt_wall = walls[through], walls[butting]
    run_rings: dict[int, Ring] = {}
    butt_rings: dict[int, Ring] = {}
    for run_index, run_layer in _sheathing(run_wall):
        strip_ring = unclipped.get(through, {}).get(run_index)
        if not strip_ring or len(strip_ring) < 3:
            continue
        run_poly = Polygon(run_layer.polygon)
        for butt_index, butt_layer in _sheathing(butt_wall):
            butt_poly = Polygon(butt_rings.get(butt_index, butt_layer.polygon))
            if not _share_mitre(run_poly, butt_poly):
                continue
            pair = union_all((run_poly, butt_poly))
            ran = intersection(pair, Polygon(strip_ring))
            # simplify(0) drops the collinear vertex the old mitre leaves on each face;
            # readers that average a band's vertices would otherwise drift toward it.
            new_run = normalize(ran.simplify(0), run_layer.polygon)
            new_butt = normalize(difference(butt_poly, ran).simplify(0), butt_layer.polygon)
            if not new_run or not new_butt:
                continue  # never erase a panel; leave the mitre
            run_poly = Polygon(new_run)
            run_rings[run_index] = new_run
            butt_rings[butt_index] = new_butt
    for tag, rings in ((through, run_rings), (butting, butt_rings)):
        if rings:
            layers = list(walls[tag].layers)
            for index, ring in rings.items():
                layers[index] = replace(layers[index], polygon=ring)
            walls[tag] = replace(walls[tag], layers=tuple(layers))


def layer_run_m(layer: ResolvedLayer, axis_run_m: float) -> float:
    """A layer's run along its wall, read off its resolved plan polygon (area / thickness).

    This is the length the drawn solid has — a through panel's extra reach, a mitre's mean
    face, a butting branch's shortened end — rather than the node-to-node axis. Falls back
    to the axis when the layer has no usable polygon.
    """
    if layer.thickness_m <= 0.0 or len(layer.polygon) < 3:
        return axis_run_m
    return float(abs(Polygon(layer.polygon).area)) / layer.thickness_m
