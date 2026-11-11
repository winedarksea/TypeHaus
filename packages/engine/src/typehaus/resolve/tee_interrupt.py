"""Tee junctions: a branch frames to the through wall's framing; drywall goes on after.

At a supported T/X the branch's core (first..last STRUCTURE layer, plus cavity) runs past
the through wall's room-face layers to its framing (:func:`framing_envelope`); its face
layers still stop at the through wall's face. :func:`resolve_tee_interruptions` then cuts
those through-wall face layers, and their coatings, over the branch's stud band.

A face layer is cut only from the room face in to the first weather or sheathing layer:
a vapour retarder, WRB or sheathing runs on behind the branch.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import GeometryCollection, Polygon

from typehaus.model.layer_functions import values_where
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.layer_pockets import subtract_layer_region
from typehaus.resolve.overlay import union_all

_EPS = 1e-6
_UNCUT = values_where(weather=True) | {"structure"}
_CUT_NAME = "tee"


def _span(wall, ring) -> tuple[float, float]:
    origin, _tangent, normal, _ = wall_frame(wall)
    values = [(x - origin[0]) * normal[0] + (y - origin[1]) * normal[1] for x, y in ring]
    return min(values), max(values)


def _side(wall, direction) -> int:
    _o, _t, normal, _ = wall_frame(wall)
    return 1 if direction[0] * normal[0] + direction[1] * normal[1] > 0 else -1


def _solids(wall):
    return [ly for ly in wall.body_layers() if not ly.coating and len(ly.polygon) >= 3]


def cut_zone(wall, side: int) -> float | None:
    """Normal offset where the cuttable face zone on ``side`` begins, or ``None``.

    Everything wholly beyond it on that side is a room-face layer the branch passes.
    """
    if wall_frame(wall)[3] <= 0.0:
        return None
    spans = [(ly, _span(wall, ly.polygon)) for ly in _solids(wall)]
    structure = [s for ly, s in spans if ly.function == "structure"]
    if not structure:
        return None
    if side > 0:
        stop = max([hi for _lo, hi in structure]
                   + [hi for ly, (lo, hi) in spans if ly.function in _UNCUT
                      and lo >= max(h for _l, h in structure) - _EPS])
        cut = any(lo >= stop - _EPS and ly.function not in _UNCUT for ly, (lo, _h) in spans)
    else:
        stop = min([lo for lo, _hi in structure]
                   + [lo for ly, (lo, hi) in spans if ly.function in _UNCUT
                      and hi <= min(lo2 for lo2, _h in structure) + _EPS])
        cut = any(hi <= stop + _EPS and ly.function not in _UNCUT for ly, (_l, hi) in spans)
    return stop if cut else None


def _in_zone(wall, layer, side: int, stop: float) -> bool:
    if len(layer.polygon) < 2 or layer.is_cavity:
        return False
    lo, hi = _span(wall, layer.polygon)
    if layer.coating:  # strictly outside: a coating at ``stop`` is under the board
        return lo > stop + _EPS if side > 0 else hi < stop - _EPS
    if layer.function in _UNCUT:
        return False
    return lo >= stop - _EPS if side > 0 else hi <= stop + _EPS


def core_indices(wall) -> set[int]:
    """The branch's framing core: first..last STRUCTURE layer, plus its cavity fill."""
    structure = [i for i, ly in enumerate(wall.layers) if ly.function == "structure"
                 and not ly.is_cavity]
    if not structure:
        return set()
    core = set(range(structure[0], structure[-1] + 1))
    return core | {i for i, ly in enumerate(wall.layers) if ly.is_cavity}


def framing_envelope(walls: dict, through_tags, direction):
    """The through walls' bodies minus the face layers a branch from ``direction`` passes."""
    polygons = []
    for tag in through_tags:
        wall = walls[tag]
        side = _side(wall, direction)
        stop = cut_zone(wall, side)
        polygons.extend(Polygon(ly.polygon) for ly in _solids(wall)
                        if stop is None or not _in_zone(wall, ly, side, stop))
    return union_all(polygons) if polygons else GeometryCollection()


def _branch_cutter(branch, point, reach: float):
    """The branch's stud band as a plan strip, ``reach`` either side of the node."""
    structure = [ly for ly in _solids(branch) if ly.function == "structure"]
    if not structure:
        return None
    origin, tangent, normal, _ = wall_frame(branch)
    n0 = min(_span(branch, ly.polygon)[0] for ly in structure)
    n1 = max(_span(branch, ly.polygon)[1] for ly in structure)
    s = (point[0] - origin[0]) * tangent[0] + (point[1] - origin[1]) * tangent[1]

    def at(u, v):
        return (origin[0] + tangent[0] * u + normal[0] * v,
                origin[1] + tangent[1] * u + normal[1] * v)
    bands = [ly.band(branch) for ly in structure]
    return (Polygon([at(s - reach, n0), at(s + reach, n0), at(s + reach, n1), at(s - reach, n1)]),
            min(z0 for z0, _ in bands), max(z1 for _, z1 in bands))


def _split_coating(wall, layer, cutters):
    """Split a zero-width coating ring at each cutter's station span (``z`` ignored)."""
    origin, tangent, normal, _ = wall_frame(wall)

    def station(p):
        return (p[0] - origin[0]) * tangent[0] + (p[1] - origin[1]) * tangent[1]
    lo, hi = (f(station(p) for p in layer.polygon) for f in (min, max))
    offset = _span(wall, layer.polygon)[0]
    gaps = sorted((min(map(station, c.exterior.coords)), max(map(station, c.exterior.coords)))
                  for c in cutters)
    pieces, start = [], lo
    for g0, g1 in gaps:
        if g0 > start + _EPS:
            pieces.append((start, min(g0, hi)))
        start = max(start, g1)
    if hi > start + _EPS:
        pieces.append((start, hi))
    if pieces == [(lo, hi)]:
        return (layer,)

    def at(u):
        return (origin[0] + tangent[0] * u + normal[0] * offset,
                origin[1] + tangent[1] * u + normal[1] * offset)
    return tuple(replace(layer, name=f"{layer.name}-{_CUT_NAME}-{i}",
                         polygon=[at(a), at(b), at(b), at(a)], run_span_m=(a, b),
                         source_layer_name=layer.source_layer_name or layer.name,
                         band_spec=None, slot=layer.slot or f"service-region:{layer.name}")
                 for i, (a, b) in enumerate(pieces) if b - a > _EPS)


def resolve_tee_interruptions(plan, model) -> None:  # noqa: ARG001 — pipeline signature
    """Cut each through wall's branch-side face layers over the branch's stud band."""
    walls = {wall.tag: wall for wall in model.walls}
    cuts: dict[str, list] = {}
    for junction in model.junctions:
        if junction.kind not in {"t", "x"} or not junction.supported:
            continue
        for incident in junction.incidents:
            branch = walls.get(incident.wall_tag)
            if incident.wall_tag not in junction.branch_walls or branch is None:
                continue
            for tag in junction.through_walls:
                wall = walls.get(tag)
                if wall is None:
                    continue
                side = _side(wall, incident.direction)
                stop = cut_zone(wall, side)
                found = _branch_cutter(branch, junction.point, wall.thickness_m + 0.05)
                if stop is not None and found is not None:
                    cuts.setdefault(tag, []).append((side, stop, *found))
    for tag, items in cuts.items():
        wall = walls[tag]
        layers = list(wall.layers)
        groups: dict[tuple, list] = {}
        for side, stop, cutter, bottom, top in items:
            key = (side, round(stop, 6), round(bottom, 6), round(top, 6))
            groups.setdefault(key, []).append((side, stop, cutter, bottom, top))
        for key in sorted(groups):
            side, stop, _c, bottom, top = groups[key][0]
            cutters = [item[2] for item in groups[key]]
            cutter = union_all(cutters)
            layers = [piece for layer in layers for piece in (
                (_split_coating(wall, layer, cutters) if layer.coating
                 else subtract_layer_region(wall, layer, cutter, bottom, top, _CUT_NAME))
                if _in_zone(wall, layer, side, stop) else (layer,))]
        model.walls[model.walls.index(wall)] = replace(wall, layers=_renumbered(wall, layers))


def _renumbered(wall, layers) -> tuple:
    """Full-depth thickness (no float drift) and flat ``<source>-tee-<k>`` names."""
    thickness = {ly.name: ly.thickness_m for ly in wall.layers}
    count: dict[str, int] = {}
    out = []
    for layer in layers:
        source = layer.source_layer_name or layer.name
        if layer.name.startswith(f"{source}-{_CUT_NAME}-"):
            k = count[source] = count.get(source, -1) + 1
            layer = replace(layer, name=f"{source}-{_CUT_NAME}-{k}",
                            thickness_m=thickness.get(source, layer.thickness_m))
        out.append(layer)
    return tuple(out)
