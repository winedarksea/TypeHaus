"""Furring/strapping: the battens a FURRING layer's ``FramingSpec`` names (→ 11 §Framing).

A ``FramingSpec`` on a FURRING layer is an authored statement that the layer is *sticks of
lumber on a grid* — 1x4 strapping over the sheathing of a rainscreen wall, horizontal
battens the sauna's T&G liner nails to — and until this module existed it framed nothing at
all. That is a billing hole, not a drawing one: ``takeoff/envelope.py`` deliberately skips
FURRING because it is lineal-foot stock rather than area, and the framing cut list only
carries what the solver resolves. Between the two, every furring strip in the house reached
no order. W-B-CS (``SAUNA_LINER_ON_CONCRETE``) is the case that made it undeniable — a
concrete core frames no members at all, so its liner strapping had nowhere to hide.

So this pass runs for *every* wall with such a layer, framed or monolithic. It is
deliberately a separate pass from ``solver.frame_wall`` rather than a branch inside it:
``frame_wall`` returns early for a monolithic wall by design (``frames_as_members``), and
strapping is not structure — it is a nailer grid fastened *over* whatever the wall is made
of, laid out in its own layer band, on its own spacing, in its own direction.

The members land in the FURRING layer's own resolved polygon, never the structure layer's.
On a catlin exterior wall that band sits 4.5" outboard of the studs behind two inches of
polyiso; framing it on the structure centreline would put strapping inside the insulation
and inside the stud bays it is supposed to hold cladding off of.

Battens and courses are also cut around ``model.openings``: a rainscreen strip is not
structural, but it still has to stop at a rough opening rather than run across the glass —
``layer_solids`` (``geometry_walls.py``) already notches this same layer's *solid* the same
way, and this pass mirrors that, not the padded jamb-pack exclusion zones ``framing/openings.py``
uses for load-bearing studs.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import (
    _wall_top_elevations,
    band_axis,
    continuation_roles,
)
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.intervals import subtract as _subtract_spans
from typehaus.resolve.layout_lines import layout_phase, lines_by_wall
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedOpening, ResolvedWall

#: Category every member here carries. Strapping is billed by ``(profile, category,
#: material)`` like all framing, so this string is what puts 1x4 battens on their own BOM row
#: instead of merging them into the wall's studs. The layer's own ``material_ref`` rides
#: along on each member for the same reason one step finer: a truss wall's outriggers are
#: KDAT and the studs behind them are SPF, and "2x4" alone cannot say which was bought.
STRAPPING_CATEGORY = "strapping"

#: ``FramingSpec.direction`` values this module lays out. A FURRING spec that names neither
#: is framed vertically (the conventional rainscreen batten) *and* reported — silently
#: guessing would turn a typo into a wrong take-off nobody ever sees.
VERTICAL, HORIZONTAL = "vertical", "horizontal"

#: ``FramingSpec.laid`` value that stands a strip up in its band. Named here so
#: ``framing/truss_wall.py`` — which exists only because of it — tests the same string.
EDGE = "edge"


def frame_furring(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Attach strapping members to every wall whose assembly furs out on a spec'd grid."""
    # Keyed by host wall, same grouping ``frame_model`` builds in ``solver.py`` — but kept as
    # plain ``ResolvedOpening`` records rather than translated into that pass's ``WallOpening``,
    # since furring never needs the door-operation/header-spec fields that translation exists
    # to carry.
    by_host: dict[str, list[ResolvedOpening]] = {}
    for op in model.openings:
        by_host.setdefault(op.host_wall, []).append(op)

    findings: list[Finding] = []
    framed: list[ResolvedWall] = []
    # A wall's layout line, so a batten grid that phase-locks to the studs follows them onto
    # the line when the assembly opts in (``FramingSpec.layout_origin``).
    lines_for_wall = lines_by_wall(model.layout_lines)
    # A batten band splits at a tee exactly as the studs behind it do, and until now each
    # half framed an end strip there: two outriggers 1-1/2" apart straddling a seam the
    # storey above put somewhere else. On this wall that band is what the standing seam
    # clips into, so those pairs are the visible vertical lines of the facade — the reason
    # this pass needs the same continuation reading ``solver.frame_model`` takes, per
    # furring layer, since it is that layer's own module that has to run through.
    roles_by_layer: dict[str, dict[tuple[str, str], str]] = {}
    resolved_by_tag = {wall.tag: wall for wall in model.walls}

    def roles_for(layer_name: str) -> dict[tuple[str, str], str]:
        if layer_name not in roles_by_layer:
            roles_by_layer[layer_name] = continuation_roles(
                model, lambda tag: _furring_module_signature(
                    plan, resolved_by_tag.get(tag), lines_for_wall.get(tag), layer_name))
        return roles_by_layer[layer_name]

    for rw in model.walls:
        members, wall_findings = frame_wall_furring(plan, rw, by_host.get(rw.tag, []),
                                                    lines_for_wall.get(rw.tag), roles_for)
        findings.extend(wall_findings)
        # ``replace`` rather than a field-by-field rebuild, as in ``frame_model``: this pass
        # only appends members, and respelling the constructor drops fields added later.
        framed.append(replace(rw, members=rw.members + members) if members else rw)
    model.walls = framed
    return findings


def _furring_module_signature(plan: PlanModel, rw: ResolvedWall | None, line: object | None,
                              layer_name: str) -> tuple[Any, ...] | None:
    """What has to match for two walls' ``layer_name`` batten grids to be provably one grid.

    Deliberately stricter than the stud signature ``solver`` uses: the *same layer name*, and
    the same member laid the same way, because a band that changes stick or turns from flat
    to on edge does not continue — it starts again, and its end strip is a real end strip.
    """
    if rw is None or line is None:
        return None
    assembly = plan.library.resolve_assembly(rw.assembly)
    if assembly is None:
        return None
    spec = next((layer.framing for layer in assembly.layers
                 if layer.name == layer_name
                 and layer.function is LayerFunction.FURRING
                 and layer.framing is not None), None)
    if spec is None or getattr(spec, "layout_origin", "wall-start") != "line":
        return None
    # ``direction`` is part of the signature rather than a filter, and that is the whole of
    # what lets a HORIZONTAL band continue. Two collinear segments of one facade carry the
    # same courses at the same elevations, and a course that stops half a board short of the
    # seam on each side leaves a 3" notch in a girt that is one continuous stick on the job —
    # exactly the pair of end studs ``continuation_roles`` exists to collapse, turned on its
    # side. A band that changes direction across a seam does not continue: the two grids are
    # not the same grid in any sense, so the mismatch has to be visible in the tuple.
    return (getattr(line, "tag", None), (spec.spacing or DEFAULT_SPACING).meters,
            spec.member, spec.laid,
            (spec.direction or VERTICAL).strip().lower())


def frame_wall_furring(
        plan: PlanModel, rw: ResolvedWall, openings: list[ResolvedOpening],
        line: object | None = None,
        roles_for: Callable[[str], dict[tuple[str, str], str]] | None = None,
        ) -> tuple[tuple[FramedMember, ...], list[Finding]]:
    """Strapping for one wall: every FURRING layer that carries a ``FramingSpec``.

    Returns ``(members, findings)`` — the shape ``framing/soffit.py`` uses, for the same
    reason: the layout is pure, and the only thing that can go wrong is authoring.
    """
    assembly = plan.library.resolve_assembly(rw.assembly)
    if assembly is None:
        return (), []
    # Keyed by layer *name* because that is the identity the resolver preserves: the
    # authored layer carries the FramingSpec, the resolved one carries the mitred band.
    specs = {layer.name: layer.framing for layer in assembly.layers
             if layer.function is LayerFunction.FURRING and layer.framing is not None}
    if not specs:
        return (), []

    members: list[FramedMember] = []
    findings: list[Finding] = []
    for resolved in rw.layers:
        spec = specs.get(resolved.name)
        if (spec is None or resolved.function != LayerFunction.FURRING.value
                or not resolved.polygon):
            continue
        direction = (spec.direction or VERTICAL).strip().lower()
        if direction not in (VERTICAL, HORIZONTAL):
            findings.append(_direction_finding(rw, resolved.name, spec.direction))
            direction = VERTICAL
        roles = roles_for(resolved.name) if roles_for is not None else {}
        continuations = (roles.get((rw.tag, "start")), roles.get((rw.tag, "end")))
        if direction == VERTICAL:
            members.extend(_layout_vertical(
                rw, resolved, spec, openings, line, continuations))
        else:
            members.extend(_layout_horizontal(
                rw, resolved, spec, openings, line, continuations))
    return tuple(members), findings


def _layout_vertical(rw: ResolvedWall, layer, spec, openings: list[ResolvedOpening],
                     line: object | None = None,
                     continuations: tuple[str | None, str | None] = (None, None),
                     ) -> list[FramedMember]:
    """Battens on centre along the wall axis, split around any opening they cross.

    Each station normally frames one member from the base to the framing top (raked or
    level); a station whose footprint crosses a window or door instead frames the
    below-sill and above-head pieces that survive, so a batten never runs across the
    glass or the RO it doesn't carry any load over anyway.
    """
    p0, direction, axis_len = _band_geometry(rw, layer)
    if axis_len <= 0.0:
        return []
    first, last = band_extent(layer.polygon, p0, direction, axis_len)
    section = cross_section(spec.member)
    # A strip laid flat presents its *wide* face to the wall, so ``depth_m`` — not
    # ``width_m`` — is the run it occupies along the axis. That is the dimension the end
    # strips have to be held in by, and the one two strips have to clear each other by.
    # Stood on edge (a truss wall's outrigger) the two swap: 1-1/2" on the wall, 3-1/2"
    # out through the band.
    on_edge = spec.laid == EDGE
    face = section.width_m if on_edge else section.depth_m
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    top_start, top_end = _wall_top_elevations(rw)

    stations = _module_stations(first + face / 2.0, last - face / 2.0, spacing, face,
                                module=True,
                                phase=layout_phase(spec, line, rw.tag, spacing),
                                continuations=continuations,
                                seams=(0.0, axis_len))
    # ``orient`` is the member's *thickness* axis (profiles.py convention). A stud's
    # thickness runs along the wall; a furring strip is laid flat, so its 3/4" thickness
    # runs *through* the wall and its 3-1/2" face lies on it. Passing the wall direction
    # here — as a stud does — would stand every strip on edge, poking 1-3/4" out through
    # cladding that is nailed to it.
    # An on-edge strip turns 90 degrees about its own long axis: the thickness face it
    # presents to the wall run is the 1-1/2" one, so ``orient`` — the thickness axis —
    # becomes the wall direction, exactly as a stud's does, and the 3-1/2" depth then
    # runs out through the band.
    through = direction if on_edge else normal(direction)
    out: list[FramedMember] = []
    index = 0
    for station in stations:
        point = add(p0, scale(direction, station))
        fraction = station / axis_len if axis_len else 0.0
        top = top_start + (top_end - top_start) * fraction
        # An opening's straight-run ``height_m`` already includes any arch rise (a semi-
        # circular head is a rectangle plus a curve above it), so cutting a plain rectangle
        # to ``sill_m + height_m`` never lets the batten intrude into the opening — it only
        # gives up a few conservative inches in an arch's spandrel corners, which
        # ``layer_solids`` draws precisely because *that* solid is what a viewer sees.
        cuts = [(rw.base_ref_z_m + op.sill_m,
                 rw.base_ref_z_m + op.sill_m + op.height_m)
                for op in openings
                if _overlaps(station - face / 2.0, station + face / 2.0,
                            op.center_along_m - op.width_m / 2.0,
                            op.center_along_m + op.width_m / 2.0)]
        for bottom, z1 in _subtract_spans(rw.z0_m, top, cuts):
            if z1 - bottom <= face:
                continue
            out.append(FramedMember(
                rw.uid, f"strapping-{layer.name}-{index:03d}", STRAPPING_CATEGORY,
                spec.member, point, point, bottom, z1, z1 - bottom, orient=through,
                material=layer.material_ref))
            index += 1
    return out


#: How far a girt band's field courses stand clear of a rough opening, along the wall and
#: in elevation alike. It is the width of the jamb POST — a 3-1/2" flat 2x4 whose inner face
#: is on the RO edge — and equally the height of the head and sill COURSES the girt frame
#: sets on it (``framing/truss_girts.py``). Those three pieces are the window's bearing, and
#: a field course that ran to the RO edge would land in exactly their plan: the head course
#: sits at ``z_head .. z_head + 3-1/2"``, which is where the field course above a low window
#: often wants to be. Holding the field back by one piece width in both axes leaves the
#: opening's own frame the room it is built in, and the courses resume beyond it.
#:
#: Zero for every furring band that is not a girt band, so a rainscreen batten course still
#: stops exactly at the RO the way ``layer_solids`` notches the band's solid.
OPENING_MARGIN_IN = 3.5


def opening_margin(spec: Any) -> float:
    """The clearance :data:`OPENING_MARGIN_IN` names, in metres, or 0.0 for a plain band."""
    if getattr(spec, "standoff", "none") != "block":
        return 0.0
    return OPENING_MARGIN_IN * 0.0254


def course_elevations(rw: ResolvedWall, spec: Any, face: float) -> list[float]:
    """The BOTTOM elevation of every course of a horizontal band on one wall.

    One list, computed once, because two different passes need to agree about it exactly.
    ``_layout_horizontal`` frames the courses; ``framing/truss_girts.py`` puts a block under
    each of them and pairs the inner band's course with the outer band's at the same
    elevation. A block half an inch below the girt it carries is not a tolerance, it is a
    block bearing on nothing, so the two readings cannot be allowed to be two readings.

    A raked wall carries a course only where its top is above it, and the courses thin out
    toward the high end: below the *lower* of the two tops every course is full length, and
    above it only the raked part of the wall is still there to nail to.
    """
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    top_start, top_end = _wall_top_elevations(rw)
    top_low, top_high = min(top_start, top_end), max(top_start, top_end)
    elevations = _module_stations(rw.z0_m, top_low - face, spacing, face)
    elevation = elevations[-1] + spacing if elevations else rw.z0_m
    while elevation + face <= top_high + 1e-9:
        elevations.append(elevation)
        elevation += spacing
    return elevations


def _layout_horizontal(rw: ResolvedWall, layer, spec, openings: list[ResolvedOpening],
                       _line: object | None = None,
                       continuations: tuple[str | None, str | None] = (None, None),
                       ) -> list[FramedMember]:
    """Batten courses at the spec's spacing up the wall, split around any opening they cross.

    A raked wall carries a course only where its top is above that course; the clipped
    sub-span is closed-form because the top varies linearly between the two endpoints. A
    course whose elevation band overlaps a window or door is further split around the
    opening's width, so it frames the piece(s) flanking it rather than the piece over it.

    ``continuations`` is the same reading ``_layout_vertical`` takes, and it does the same
    job one axis over: an end that is not an end runs to the seam and butts its neighbour's
    course rather than being held half a board back from it. Two collinear segments of one
    facade otherwise leave a 3" notch in every course at every tee — a girt is one stick on
    the job, and the seam is a modelling artifact of where the partitions land inside.
    """
    p0, direction, axis_len = _band_geometry(rw, layer)
    if axis_len <= 0.0:
        return []
    first, last = band_extent(layer.polygon, p0, direction, axis_len)
    section = cross_section(spec.member)
    # Laid flat and running horizontally, the strip's wide face is its *height* on the
    # wall; its thickness is the band depth, which is what ``member_footprint`` bands a
    # p0 != p1 member by. On edge the two swap, and nothing downstream needs telling:
    # ``profiles.plan_cross_section_m`` reads which way a horizontal member was laid off
    # its own z-extent, so a 1-1/2"-tall course automatically bands 3-1/2" deep.
    on_edge = spec.laid == EDGE
    face = section.width_m if on_edge else section.depth_m
    # A course ends against whatever crosses its band at the corner — the neighbouring
    # wall's course, whose centreline runs half a board inside the mitre. The member IR
    # has no mitre and no butt cut, so hold each end back half a thickness and the two
    # courses abut there instead of lapping through each other. A CONTINUED end has no
    # such neighbour to lap: the course on the far side of the seam is this same course.
    plan_face = section.depth_m if on_edge else section.width_m
    start_cont, end_cont = continuations
    if not start_cont:
        first = first + plan_face / 2.0
    if not end_cont:
        last = last - plan_face / 2.0
    top_start, top_end = _wall_top_elevations(rw)
    margin = opening_margin(spec)

    out: list[FramedMember] = []
    index = 0
    for z in course_elevations(rw, spec, face):
        lo, hi = _course_span(z + face, top_start, top_end, axis_len, first, last)
        if hi - lo <= face:
            continue
        # ``margin`` widens the void to the opening's own FRAME — the jamb posts beside the
        # RO and the head and sill courses above and below it — for a girt band, and is zero
        # for every other, which leaves a rainscreen batten stopping exactly at the RO.
        cuts = [(op.center_along_m - op.width_m / 2.0 - margin,
                 op.center_along_m + op.width_m / 2.0 + margin)
                for op in openings
                if _overlaps(z, z + face, rw.base_ref_z_m + op.sill_m - margin,
                            rw.base_ref_z_m + op.sill_m + op.height_m + margin)]
        for seg_lo, seg_hi in _subtract_spans(lo, hi, cuts):
            if seg_hi - seg_lo <= face:
                continue
            a = add(p0, scale(direction, seg_lo))
            b = add(p0, scale(direction, seg_hi))
            out.append(FramedMember(
                rw.uid, f"strapping-{layer.name}-{index:03d}", STRAPPING_CATEGORY,
                spec.member, a, b, z, z + face, length(sub(b, a)),
                material=layer.material_ref))
            index += 1
    return out


def _overlaps(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> bool:
    """Whether ``[a_lo, a_hi]`` and ``[b_lo, b_hi]`` share any interior, past a small epsilon."""
    return a_lo < b_hi - 1e-9 and b_lo < a_hi - 1e-9




def _band_geometry(rw: ResolvedWall, layer):
    """The furring band's centreline start, unit direction, and run length."""
    start, end = band_axis(rw.axis, layer.polygon)
    return start, unit(sub(end, start)), length(sub(end, start))


def band_extent(polygon, p0, direction, axis_len: float) -> tuple[float, float]:
    """The band's first/last station *on its own centreline*, clamped to the wall.

    The resolved layer polygon is mitred at every junction, so this is where corner
    interference is actually resolved: the strapping stops where its band stops. On W-B-CS
    the liner band gives up its last foot to the wall it tees into, and the battens stop
    there rather than running through the neighbour's liner.

    Measured by clipping the centreline against the polygon rather than by projecting its
    vertices, because a mitre's far tip is a *corner* of the band, not a station the
    centreline ever reaches. Projecting vertices ran the sauna's two liner courses a
    half-board past each other, straight through the mitre they are cut to. A polygon the
    centreline somehow misses falls back to the projection — a short band is better than
    none.
    """
    across = normal(direction)
    offsets = [(x - p0[0]) * across[0] + (y - p0[1]) * across[1] for x, y in polygon]
    stations = [(x - p0[0]) * direction[0] + (y - p0[1]) * direction[1]
                for x, y in polygon]
    crossings: list[float] = []
    for i, offset in enumerate(offsets):
        j = (i + 1) % len(offsets)
        if abs(offset) < 1e-12:
            crossings.append(stations[i])
        elif offset * offsets[j] < 0.0:
            fraction = offset / (offset - offsets[j])
            crossings.append(stations[i] + (stations[j] - stations[i]) * fraction)
    if len(crossings) < 2:
        crossings = stations
    return max(0.0, min(crossings)), min(axis_len, max(crossings))


def _module_stations(first: float, last: float, spacing: float, width: float,
                     module: bool = False, phase: float = 0.0,
                     continuations: tuple[str | None, str | None] = (None, None),
                     seams: tuple[float, float] = (0.0, 0.0)) -> list[float]:
    """``first`` on centre to ``last``, with ``last`` always framed.

    Same rule the stud module follows: a strip at each end of the run whatever the
    spacing does, and no module strip so close to the end one that the two are the same
    piece of wood.

    ``module=True`` additionally **phase-locks the run to the wall's own framing module** —
    stations at whole multiples of ``spacing`` from axis station 0, which is where
    ``solver._module_stations`` puts the studs. Without it the grid starts at
    ``first + width / 2`` and inherits that offset for the whole wall, so a strip lands
    half a stick off every stud line: a 3-1/2" batten laid flat came out 1-3/4" off, and a
    truss wall's 1-1/2"-wide outrigger 3/4" off, which is what put 806 of catlin's 1,285
    truss blocks half-lapped on their studs and 74 of them on bare sheathing.

    A vertical strip on an exterior wall is screwed *into the studs*, so its grid is the
    stud grid; only the end strips are off-module, exactly as the end studs are. Courses
    running horizontally are a different question — they climb their own elevation module
    and have no stud line to find — so they do not pass this.

    ``phase`` is the same shift ``solver._module_stations`` takes, and it has to be, because
    the promise this makes is *"sit on the studs"*: a wall laying out from its layout line
    moves its studs, and a batten grid still counting from the wall's own station 0 would be
    keeping the old promise to nothing. ``band_axis`` only ever translates the axis
    perpendicular, never along it, so the band's station 0 and the wall's are the same
    station and one phase serves both.

    ``continuations`` marks an end that is not an end — the band runs on into a collinear
    neighbour whose grid is this grid (``solver.continuation_roles``). There the mandatory end
    strip is dropped and the module is let out to the seam itself (``seams``, the wall-local
    station of each), because the strip that would have been held a full face clear of an end
    strip has no end strip to clear. A seam landing *on* the grid is framed by the ``"owner"``
    half alone, so it carries one strip rather than two in the same 1-1/2".
    """
    if last < first:
        return []
    start_cont, end_cont = continuations
    seam_start, seam_end = seams
    stations = [] if start_cont else [first]
    low = seam_start if start_cont else first + width
    high = seam_end if end_cont else last - width
    if module and spacing > 0.0:
        index = math.ceil((low - phase) / spacing)
        station = phase + index * spacing
        while station < high + 1e-9:
            contested = ((start_cont == "follower" and abs(station - seam_start) < 1e-9)
                         or (end_cont == "follower" and abs(station - seam_end) < 1e-9))
            if not contested:
                stations.append(station)
            index += 1
            station = phase + index * spacing
    else:
        index = 1
        while first + index * spacing < high + 1e-9:
            stations.append(first + index * spacing)
            index += 1
    if not end_cont and (not stations or last - stations[-1] > width - 1e-9):
        stations.append(last)
    if not stations:
        stations = [first] if last - first < width - 1e-9 else [first, last]
    return stations


def _course_span(top_needed: float, top_start: float, top_end: float, axis_len: float,
                 first: float, last: float) -> tuple[float, float]:
    """The sub-span of ``[first, last]`` whose wall top clears ``top_needed``."""
    rise = top_end - top_start
    if abs(rise) < 1e-9:
        return (first, last) if top_start >= top_needed - 1e-9 else (0.0, 0.0)
    crossing = (top_needed - top_start) / rise * axis_len
    return (max(first, crossing), last) if rise > 0 else (first, min(last, crossing))


def _direction_finding(rw: ResolvedWall, layer_name: str, direction) -> Finding:
    return Finding(
        severity=Severity.WARN,
        check_id="structural.furring_direction",
        message=(f"{rw.tag}: FURRING layer {layer_name!r} names direction "
                 f"{direction!r}; framed vertically"),
        element_tags=(rw.tag,),
        fix_hint=f'set FramingSpec.direction to "{VERTICAL}" or "{HORIZONTAL}"',
        result=Result.UNKNOWN,
    )
