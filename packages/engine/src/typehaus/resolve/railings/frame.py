"""The guard's frame: post stations, posts (or wall brackets), and the rails between them."""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.geometry import Vec, length, rect_between, square, sub
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, SolidSweep, Vec3
from typehaus.resolve.railings.parts import (
    RAILING_CATEGORY,
    RAILING_FACETS,
    RailingParts,
    railing_type,
)
from typehaus.resolve.railings.spans import RAIL_BAND_STEP_M, RailingSurface
from typehaus.resolve.railings.wall_contact import mounting_wall_face
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
#: Bracket stock: the drop from the rail centreline to the arm, and the arm's section.
_BRACKET_DROP_M = inch(2.5).meters
_BRACKET_SECTION_M = inch(1.0).meters

#: How far a sampled rail station may sit off the chord between the stations either side of
#: it before the run keeps it as a real vertex. A straight flight's samples are collinear to
#: well inside a sixteenth, so a 13-ft bar collapses back to the two points a carpenter cuts
#: it at; a winder, whose nosing line genuinely curves, keeps as many as it needs.
_RAIL_SIMPLIFY_TOL_M = inch(1.0 / 16.0).meters
#: Bound refinement at abrupt surface transitions without hiding a level lead-in's end.
_MAX_RAIL_SAMPLE_SUBDIVISIONS = 12


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
               surface: RailingSurface, parts: RailingParts, rail_h: float) -> list[Finding]:
    """One prism per station, standing on the walking surface under it.

    Unless the rail is carried by a wall, in which case it stands on nothing at all and
    gets brackets instead — see :func:`emit_brackets`.
    """
    if el.mount in _WALL_MOUNTS:
        return emit_brackets(model, el, storey, stations, surface, parts, rail_h)
    half = parts.post_section_m / 2.0
    if el.mount == "fascia":
        _emit_fascia_brackets(model, el, storey, stations, surface, parts)
    for index, (px, py) in enumerate(stations):
        z0 = surface.height_at((px, py))
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-p{index:02d}", tag=f"{el.tag}-POST{index + 1}", storey=storey,
            category=RAILING_CATEGORY, outline=square(px, py, half, half),
            z0_m=z0, z1_m=z0 + rail_h, assembly=el.assembly, material=parts.post_material,
        ))
    return []


def _emit_fascia_brackets(model: ResolvedModel, el: Railing, storey: str,
                          stations: list[Vec], surface: RailingSurface,
                          parts: RailingParts) -> None:
    """A plate on the fascia's outer face at each post, so it shows what it displaces.

    Drawn only where the product states its height and the guard states where its fascia
    face and bracket top are; the right-hand normal of the path is outboard.
    """
    product = railing_type(model.plan.library, el)
    if (product is None or product.fascia_bracket_height is None
            or product.fascia_bracket_width is None
            or product.fascia_bracket_projection is None
            or el.fascia_face_offset is None or el.fascia_bracket_drop is None):
        return
    half_w = product.fascia_bracket_width.meters / 2.0
    projection = product.fascia_bracket_projection.meters
    for index, station in enumerate(stations):
        dirs = _directions_at(stations, index)
        # Corner stations take the segment that arrives; the first station the one leaving.
        dx, dy = dirs[0]
        n = math.hypot(dx, dy)
        if n < 1e-9:
            continue
        ux, uy = dx / n, dy / n
        out = (uy, -ux)
        face = el.fascia_face_offset.meters
        a = (station[0] + out[0] * face, station[1] + out[1] * face)
        b = (a[0] + out[0] * projection, a[1] + out[1] * projection)
        top = surface.height_at(station) - el.fascia_bracket_drop.meters
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-f{index:02d}", tag=f"{el.tag}-FASCIA-BRACKET{index + 1}",
            storey=storey, category=RAILING_CATEGORY,
            outline=rect_between(a, b, -half_w, half_w),
            z0_m=top - product.fascia_bracket_height.meters, z1_m=top,
            assembly=el.assembly, material=parts.post_material,
        ))


def emit_brackets(model: ResolvedModel, el: Railing, storey: str, stations: list[Vec],
                  surface: RailingSurface, parts: RailingParts, rail_h: float) -> list[Finding]:
    """A short arm at each station, from the wall face out to the rail centreline.

    Only a solid face supporting the full arm footprint can carry a bracket. An end
    carried by a wall return (:mod:`.terminations`) gets no bracket.
    """
    half = _BRACKET_SECTION_M / 2.0
    findings: list[Finding] = []
    bracket_drops = dict(el.bracket_drop_overrides)
    last = len(stations) - 1
    for index, station in enumerate(stations):
        if (index == 0 and el.start_termination == "wall_return") or (
                index == last and el.end_termination == "wall_return"):
            continue
        rail_z = surface.height_at(station) + rail_h
        custom_drop = bracket_drops.get(index + 1)
        arm_z = rail_z - (_BRACKET_DROP_M if custom_drop is None else custom_drop.meters)
        contact, obstructing_tags = mounting_wall_face(
            model, station, rail_z if custom_drop is None else arm_z,
            along=_directions_at(stations, index), half_width_m=half,
            z0_m=arm_z - half, z1_m=rail_z if custom_drop is None else arm_z + half)
        if contact is None or contact.distance_m < 1e-4:
            findings.append(Finding(
                severity=Severity.WARN, check_id="geometry.railing_bracket_unanchored",
                message=(f"railing {el.tag} bracket {index + 1} has no solid wall face "
                         "supporting its full footprint within reach; no bracket drawn"),
                element_tags=(el.tag, *obstructing_tags), result=Result.FAIL))
            continue
        outline = rect_between(contact.face_point, station, -half, half)
        sweep = None
        z0, z1 = arm_z - half, rail_z
        if custom_drop is not None:
            # The wall carries only the lower horizontal arm. The upright is outboard,
            # beside the rail, so it can pass the floor band without inventing wall there.
            sweep = SolidSweep(
                path=((*contact.face_point, arm_z), (*station, arm_z), (*station, rail_z)),
                profile=rect_profile(_BRACKET_SECTION_M, _BRACKET_SECTION_M))
            outline = sweep_plan_silhouette(sweep)
            z0, z1 = sweep_z_extent(sweep)
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-b{index:02d}", tag=f"{el.tag}-BRACKET{index + 1}", storey=storey,
            category=RAILING_CATEGORY, outline=outline,
            z0_m=z0, z1_m=z1, assembly=el.assembly,
            material=parts.post_material, sweep=sweep,
        ))
    return findings


def _directions_at(stations: list[Vec], index: int) -> tuple[Vec, ...]:
    """The rail's plan direction(s) either side of station ``index``."""
    out: list[Vec] = []
    for a, b in ((index - 1, index), (index, index + 1)):
        if a >= 0 and b < len(stations):
            out.append(sub(stations[b], stations[a]))
    return tuple(out)


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
    starting_z = surface.height_at(path[0]) + rise_m
    leading_level = True

    def append_band(a: Vec3, b: Vec3, depth: int = 0) -> None:
        midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        midpoint_z = surface.height_at(midpoint) + rise_m
        if (depth < _MAX_RAIL_SAMPLE_SUBDIVISIONS and
                abs(midpoint_z - (a[2] + b[2]) / 2) > _RAIL_SIMPLIFY_TOL_M / 2):
            middle = (*midpoint, midpoint_z)
            append_band(a, middle, depth + 1)
            append_band(middle, b, depth + 1)
        else:
            points.append(a)

    for a, b in zip(path[:-1], path[1:], strict=True):
        run = length(sub(b, a))
        steps = max(int(math.ceil(run / RAIL_BAND_STEP_M)), 1)
        for k in range(steps):
            t = k / steps
            station = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            next_t = (k + 1) / steps
            following = (a[0] + (b[0] - a[0]) * next_t, a[1] + (b[1] - a[1]) * next_t)
            current = (*station, surface.height_at(station) + rise_m)
            next_point = (*following, surface.height_at(following) + rise_m)
            if leading_level and abs(next_point[2] - starting_z) > 1e-9:
                # Resolve the end of a level lead-in without changing the established
                # sampling policy for the rest of a flight or its arrival landing.
                if points:
                    append_band(current, next_point)
                else:
                    points.append(current)
                leading_level = False
            else:
                points.append(current)
    end = path[-1]
    points.append((end[0], end[1], surface.height_at(end) + rise_m))
    return simplify_path(points, _RAIL_SIMPLIFY_TOL_M, _RAIL_SIMPLIFY_TOL_M)
