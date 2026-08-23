"""The guard's frame: post stations, posts (or wall brackets), and the rails between them."""

from __future__ import annotations

import math

from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.geometry import Vec, length, rect_between, square, sub
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.railings.parts import (
    RAILING_CATEGORY,
    RAILING_FACETS,
    RailingParts,
)
from typehaus.resolve.railings.spans import RailingSurface
from typehaus.resolve.round_solids import round_run_bands

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


def railing_post_stations(path: list[Vec], spacing: float) -> list[Vec]:
    """Posts at every segment start plus interior stations; the final vertex closes.

    Each segment's loop restarts at its own start vertex, so every authored path vertex is
    itself a station and two consecutive stations never straddle a corner. That is the
    property the infill relies on: one walk of this list yields the bays, and a bay is
    always straight.

    Bays are **evenly divided**, at ``ceil(segment / spacing)`` of them. The old
    ``int(seg // spacing)`` left the whole remainder in the last bay, which could take it to
    nearly twice the authored spacing — RL-A-STAIR came out with bays of 5'-0" and 9'-3" on
    a guard authored at 5'-0" o.c. Balusters absorbed that invisibly, because they re-space
    to whatever bay they are handed; a glass lite became an unmanufacturable 9'-3" panel,
    which is why :func:`~typehaus.resolve.railings.infill.emit_infill` warns on one.
    Dividing evenly rather than laying out at exactly ``spacing`` from the start is both
    what a builder does and what avoids the other failure of a bare ``ceil``: a segment a
    millimetre over a whole number of bays would otherwise end in a millimetre-wide bay.
    ``spacing`` is a maximum, and no bay now exceeds it.
    """
    placed: list[Vec] = []
    for a, b in zip(path[:-1], path[1:]):
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
    """``rail_count`` evenly spaced horizontal runs, top rail at the guard height.

    Banded per *path segment*, and within a segment by what the surface under it does: a
    flat run is one band, a raking one is a ladder of bands each climbing no more than the
    bar's own section, so consecutive pieces abut rather than leaving air between them
    (→ :mod:`.spans`). Rails are the guard line a plan reader looks for, so a flat run stays
    one solid per segment rather than being chopped into bays.

    A rail whose product profile names a *round* section is drawn as one — faceted through
    :func:`~typehaus.resolve.round_solids.round_run_bands`, the same machinery the pipe
    sweeps use, at a smaller facet budget. Take-off is unaffected either way: railings bill
    per element off their path length (``takeoff/railings.py``), never off these solids.
    """
    levels = el.rail_count if el.rail_count > 0 else 1
    radius = parts.rail_round_radius_m
    section = 2.0 * radius if radius is not None else parts.rail_section_m
    half = section / 2.0
    index = 0
    for a, b in zip(path[:-1], path[1:]):
        for pa, pb, za, zb in surface.rail_bands(a, b, section):
            for level in range(levels):
                frac = 1.0 - (level / max(levels - 1, 1)) if levels > 1 else 1.0
                ra, rb = za + rail_h * frac, zb + rail_h * frac
                if radius is not None:
                    pieces = round_run_bands(pa, pb, radius, (ra + rb) / 2.0,
                                             sweep_bands=RAILING_FACETS // 2)
                    # The band's own fall, opened out from the section's mid-height so the
                    # faceted stack spans the slope instead of sitting level across it.
                    fall = abs(rb - ra) / 2.0
                    pieces = [(outline, z0 - fall, z1 + fall) for outline, z0, z1 in pieces]
                else:
                    pieces = [(rect_between(pa, pb, -half, half),
                               min(ra, rb) - half, max(ra, rb) + half)]
                for outline, z0, z1 in pieces:
                    model.solids.append(ResolvedSolid(
                        uid=f"{el.uid}-r{index:02d}", tag=f"{el.tag}-RAIL{index + 1}",
                        storey=storey, category=RAILING_CATEGORY, outline=outline,
                        z0_m=z0, z1_m=z1, assembly=el.assembly,
                        material=parts.rail_material,
                    ))
                    index += 1
