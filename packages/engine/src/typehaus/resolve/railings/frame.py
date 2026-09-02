"""The guard's frame: post stations, posts (or wall brackets), and the rails between them."""

from __future__ import annotations

import math

from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.geometry import Vec, length, rect_between, square, sub
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, SolidSweep, Vec3
from typehaus.resolve.railings.parts import (
    RAILING_CATEGORY,
    RAILING_FACETS,
    RailingParts,
)
from typehaus.resolve.railings.spans import RAIL_BAND_STEP_M, RailingSurface
from typehaus.resolve.sweep import (
    rect_profile,
    round_profile,
    simplify_path,
    sweep_plan_silhouette,
    sweep_z_extent,
)

#: A post cannot be closer than this o.c. — a zero or negative authored spacing would
#: otherwise walk a segment forever.
MIN_POST_SPACING_M = 0.3

#: ``mount`` values that mean "carried by the wall beside it", not "standing on the floor".
#: ``Railing.mount``'s docstring named only "fascia" and "surface", but every handrail in
#: the reference house authors ``mount="wall"`` — and ``grep -rn 'mount ==' src/typehaus``
#: returned *nothing*, so the field was read by no one. A 36" floor post therefore stood at
#: every station of every wall-mounted rail, marching up the flight beside a rail that is
#: actually screwed to the wall.
_WALL_MOUNTS = frozenset({"wall"})
#: How far from a station a wall may be and still be the thing the bracket lands on.
_BRACKET_REACH_M = inch(9).meters
#: Bracket stock: the drop from the rail centreline to the arm, and the arm's section.
_BRACKET_DROP_M = inch(2.5).meters
_BRACKET_SECTION_M = inch(1.0).meters

#: How far a sampled rail station may sit off the chord between the stations either side of
#: it before the run keeps it as a real vertex. A straight flight's samples are collinear to
#: well inside a sixteenth, so a 13-ft bar collapses back to the two points a carpenter cuts
#: it at; a winder, whose nosing line genuinely curves, keeps as many as it needs.
_RAIL_SIMPLIFY_TOL_M = inch(1.0 / 16.0).meters


def railing_post_stations(path: list[Vec], spacing: float) -> list[Vec]:
    """Posts at every segment start plus interior stations; the final vertex closes.

    Each segment's loop restarts at its own start vertex, so every authored path vertex is
    itself a station and two consecutive stations never straddle a corner. That is the
    property the infill relies on: one walk of this list yields the bays, and a bay is
    always straight.

    Bays are **evenly divided**, at ``ceil(segment / spacing)`` of them, so no bay exceeds
    ``spacing`` and none ends up a millimetre wide from rounding. An oversize bay is a
    manufacturing problem for a sheet product — see
    :func:`~typehaus.resolve.railings.infill.emit_infill`'s bay-oversize warning.
    """
    placed: list[Vec] = []
    for a, b in zip(path[:-1], path[1:], strict=True):
        seg = length(sub(b, a))
        bays = max(int(math.ceil(seg / spacing - 1e-9)), 1) if seg > 1e-9 else 1
        for k in range(bays):
            t = k / bays
            placed.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    placed.append(path[-1])
    return placed


def emit_posts(model: ResolvedModel, el: Railing, storey: str, stations: list[Vec],
               surface: RailingSurface, parts: RailingParts, rail_h: float) -> None:
    """One prism per station, standing on the walking surface under it.

    Unless the rail is carried by a wall, in which case it stands on nothing at all and
    gets brackets instead — see :func:`emit_brackets`.
    """
    if el.mount in _WALL_MOUNTS:
        emit_brackets(model, el, storey, stations, surface, parts, rail_h)
        return
    half = parts.post_section_m / 2.0
    for index, (px, py) in enumerate(stations):
        z0 = surface.height_at((px, py))
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-p{index:02d}", tag=f"{el.tag}-POST{index + 1}", storey=storey,
            category=RAILING_CATEGORY, outline=square(px, py, half, half),
            z0_m=z0, z1_m=z0 + rail_h, assembly=el.assembly, material=parts.post_material,
        ))


def emit_brackets(model: ResolvedModel, el: Railing, storey: str, stations: list[Vec],
                  surface: RailingSurface, parts: RailingParts, rail_h: float) -> None:
    """A short arm at each station, from the wall face out to the rail centreline.

    The wall is found rather than authored: the nearest wall face on the railing's storey
    within :data:`_BRACKET_REACH_M` of the station gives both the direction the arm runs and
    how far it reaches. A station with no wall that close gets a stub dropped under the rail
    instead — which side to project toward is not knowable there, and a cleat under the bar
    is at least never on the wrong one. Neither is a 36" post standing on the flight.
    """
    half = _BRACKET_SECTION_M / 2.0
    for index, station in enumerate(stations):
        rail_z = surface.height_at(station) + rail_h
        arm_z = rail_z - _BRACKET_DROP_M
        anchor = _nearest_wall_face(model, el, storey, station)
        outline = (rect_between(anchor, station, -half, half) if anchor is not None
                   else square(station[0], station[1], half, half))
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-b{index:02d}", tag=f"{el.tag}-BRACKET{index + 1}", storey=storey,
            category=RAILING_CATEGORY, outline=outline,
            z0_m=arm_z - half, z1_m=rail_z, assembly=el.assembly,
            material=parts.post_material,
        ))


def _nearest_wall_face(model: ResolvedModel, el: Railing, storey: str,
                       station: Vec) -> Vec | None:
    """The point on the nearest wall's *face* a bracket at ``station`` would land on."""
    best: tuple[float, Vec] | None = None
    for wall in model.walls:
        if wall.storey != storey:
            continue
        (x0, y0), (x1, y1) = wall.axis
        dx, dy = x1 - x0, y1 - y0
        run2 = dx * dx + dy * dy
        if run2 < 1e-18:
            continue
        t = max(0.0, min(1.0, ((station[0] - x0) * dx + (station[1] - y0) * dy) / run2))
        foot = (x0 + dx * t, y0 + dy * t)
        gap = math.hypot(station[0] - foot[0], station[1] - foot[1])
        # The axis is the wall's centreline; the bracket lands on the face nearer the rail.
        reach = max(0.0, gap - wall.thickness_m / 2.0)
        if reach > _BRACKET_REACH_M or gap < 1e-9:
            continue
        face = (station[0] + (foot[0] - station[0]) * reach / gap,
                station[1] + (foot[1] - station[1]) * reach / gap)
        if best is None or reach < best[0]:
            best = (reach, face)
    return None if best is None else best[1]


def emit_rails(model: ResolvedModel, el: Railing, storey: str, path: list[Vec],
               surface: RailingSurface, parts: RailingParts, rail_h: float) -> None:
    """``rail_count`` evenly spaced runs, top rail at the guard height — **one solid each**.

    A rail is one bar. It is cut once, ordered once and installed once, so it is one solid
    carrying its own 3D polyline (:class:`~typehaus.resolve.model.SolidSweep`) rather than a
    stack of level bands faking a rake. The polyline is *sampled* off the walking surface
    under it — the same ``height_at`` the posts stand on, every
    :data:`~typehaus.resolve.railings.spans.RAIL_BAND_STEP_M` along the authored path — and
    then simplified, so a straight flight comes back as the two points it really has and a
    winder keeps its curve.

    A rail whose product profile names a *round* section gets a faceted circle; anything else
    gets its square stock section, whose flat face stays level on a rake because of the
    sweep's frame convention (→ :mod:`typehaus.resolve.sweep`). Take-off is unaffected either
    way — railings bill per element (``takeoff/railings.py``), and the one quantity that does
    come off this geometry, the top rail's developed length, now reads the sweep's own path.

    Posts, brackets and infill are untouched: those are genuinely discrete pieces.
    """
    levels = el.rail_count if el.rail_count > 0 else 1
    radius = parts.rail_round_radius_m
    profile = (round_profile(radius, RAILING_FACETS) if radius is not None
               else rect_profile(parts.rail_section_m, parts.rail_section_m))
    for level in range(levels):
        frac = 1.0 - (level / max(levels - 1, 1)) if levels > 1 else 1.0
        sweep = SolidSweep(path=_rail_path(path, surface, rail_h * frac), profile=profile)
        if len(sweep.path) < 2:
            continue
        z0, z1 = sweep_z_extent(sweep)
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-r{level:02d}", tag=f"{el.tag}-RAIL{level + 1}",
            storey=storey, category=RAILING_CATEGORY,
            outline=sweep_plan_silhouette(sweep), z0_m=z0, z1_m=z1,
            assembly=el.assembly, material=parts.rail_material, sweep=sweep,
        ))


def _rail_path(path: list[Vec], surface: RailingSurface, rise_m: float) -> tuple[Vec3, ...]:
    """The rail's own 3D polyline: the authored plan path lifted onto the walking surface.

    Sampled rather than taken at the vertices because the surface under a stair guard is a
    ramp the authored path knows nothing about — every authored vertex is still a sample, so
    a corner can never be rounded off, and the sampling in between is what makes the bar
    follow the flight. ``rise_m`` is this level's height above that surface.
    """
    points: list[Vec3] = []
    for a, b in zip(path[:-1], path[1:], strict=True):
        run = length(sub(b, a))
        steps = max(int(math.ceil(run / RAIL_BAND_STEP_M)), 1)
        for k in range(steps):
            t = k / steps
            station = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            points.append((station[0], station[1], surface.height_at(station) + rise_m))
    end = path[-1]
    points.append((end[0], end[1], surface.height_at(end) + rise_m))
    return simplify_path(points, _RAIL_SIMPLIFY_TOL_M, _RAIL_SIMPLIFY_TOL_M)
