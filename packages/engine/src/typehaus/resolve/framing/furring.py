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

from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import _wall_top_elevations, band_axis
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.intervals import subtract as _subtract_spans
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedOpening, ResolvedWall

#: Category every member here carries. Strapping is billed by ``(profile, category)`` like
#: all framing, so this string is what puts 1x4 battens on their own BOM row instead of
#: merging them into the wall's studs.
STRAPPING_CATEGORY = "strapping"

#: ``FramingSpec.direction`` values this module lays out. A FURRING spec that names neither
#: is framed vertically (the conventional rainscreen batten) *and* reported — silently
#: guessing would turn a typo into a wrong take-off nobody ever sees.
VERTICAL, HORIZONTAL = "vertical", "horizontal"


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
    for rw in model.walls:
        members, wall_findings = frame_wall_furring(plan, rw, by_host.get(rw.tag, []))
        findings.extend(wall_findings)
        # ``replace`` rather than a field-by-field rebuild, as in ``frame_model``: this pass
        # only appends members, and respelling the constructor drops fields added later.
        framed.append(replace(rw, members=rw.members + members) if members else rw)
    model.walls = framed
    return findings


def frame_wall_furring(
        plan: PlanModel, rw: ResolvedWall,
        openings: list[ResolvedOpening]) -> tuple[tuple[FramedMember, ...], list[Finding]]:
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
        layout = _layout_vertical if direction == VERTICAL else _layout_horizontal
        members.extend(layout(rw, resolved, spec, openings))
    return tuple(members), findings


def _layout_vertical(rw: ResolvedWall, layer, spec,
                     openings: list[ResolvedOpening]) -> list[FramedMember]:
    """Battens on centre along the wall axis, split around any opening they cross.

    Each station normally frames one member from the base to the framing top (raked or
    level); a station whose footprint crosses a window or door instead frames the
    below-sill and above-head pieces that survive, so a batten never runs across the
    glass or the RO it doesn't carry any load over anyway.
    """
    p0, direction, axis_len = _band_geometry(rw, layer)
    if axis_len <= 0.0:
        return []
    first, last = _band_extent(layer.polygon, p0, direction, axis_len)
    section = cross_section(spec.member)
    # A strip laid flat presents its *wide* face to the wall, so ``depth_m`` — not
    # ``width_m`` — is the run it occupies along the axis. That is the dimension the end
    # strips have to be held in by, and the one two strips have to clear each other by.
    face = section.depth_m
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    top_start, top_end = _wall_top_elevations(rw)

    stations = _module_stations(first + face / 2.0, last - face / 2.0, spacing, face)
    # ``orient`` is the member's *thickness* axis (profiles.py convention). A stud's
    # thickness runs along the wall; a furring strip is laid flat, so its 3/4" thickness
    # runs *through* the wall and its 3-1/2" face lies on it. Passing the wall direction
    # here — as a stud does — would stand every strip on edge, poking 1-3/4" out through
    # cladding that is nailed to it.
    through = normal(direction)
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
        cuts = [(rw.z0_m + op.sill_m, rw.z0_m + op.sill_m + op.height_m)
                for op in openings
                if _overlaps(station - face / 2.0, station + face / 2.0,
                            op.center_along_m - op.width_m / 2.0,
                            op.center_along_m + op.width_m / 2.0)]
        for bottom, z1 in _subtract_spans(rw.z0_m, top, cuts):
            if z1 - bottom <= face:
                continue
            out.append(FramedMember(
                rw.uid, f"strapping-{layer.name}-{index:03d}", STRAPPING_CATEGORY,
                spec.member, point, point, bottom, z1, z1 - bottom, orient=through))
            index += 1
    return out


def _layout_horizontal(rw: ResolvedWall, layer, spec,
                       openings: list[ResolvedOpening]) -> list[FramedMember]:
    """Batten courses at the spec's spacing up the wall, split around any opening they cross.

    A raked wall carries a course only where its top is above that course; the clipped
    sub-span is closed-form because the top varies linearly between the two endpoints. A
    course whose elevation band overlaps a window or door is further split around the
    opening's width, so it frames the piece(s) flanking it rather than the piece over it.
    """
    p0, direction, axis_len = _band_geometry(rw, layer)
    if axis_len <= 0.0:
        return []
    first, last = _band_extent(layer.polygon, p0, direction, axis_len)
    section = cross_section(spec.member)
    # Laid flat and running horizontally, the strip's wide face is its *height* on the
    # wall; its thickness is the band depth, which is what ``member_footprint`` bands a
    # p0 != p1 member by.
    face = section.depth_m
    # A course ends against whatever crosses its band at the corner — the neighbouring
    # wall's course, whose centreline runs half a board inside the mitre. The member IR
    # has no mitre and no butt cut, so hold each end back half a thickness and the two
    # courses abut there instead of lapping through each other.
    first, last = first + section.width_m / 2.0, last - section.width_m / 2.0
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    top_start, top_end = _wall_top_elevations(rw)
    top_low, top_high = min(top_start, top_end), max(top_start, top_end)

    elevations = _module_stations(rw.z0_m, top_low - face, spacing, face)
    # A course that clears the *lower* top is full length; above it only the raked part of
    # the wall is still there to nail to, so the courses thin out toward the high end.
    elevation = elevations[-1] + spacing if elevations else rw.z0_m
    while elevation + face <= top_high + 1e-9:
        elevations.append(elevation)
        elevation += spacing

    out: list[FramedMember] = []
    index = 0
    for z in elevations:
        lo, hi = _course_span(z + face, top_start, top_end, axis_len, first, last)
        if hi - lo <= face:
            continue
        cuts = [(op.center_along_m - op.width_m / 2.0, op.center_along_m + op.width_m / 2.0)
                for op in openings
                if _overlaps(z, z + face, rw.z0_m + op.sill_m,
                            rw.z0_m + op.sill_m + op.height_m)]
        for seg_lo, seg_hi in _subtract_spans(lo, hi, cuts):
            if seg_hi - seg_lo <= face:
                continue
            a = add(p0, scale(direction, seg_lo))
            b = add(p0, scale(direction, seg_hi))
            out.append(FramedMember(
                rw.uid, f"strapping-{layer.name}-{index:03d}", STRAPPING_CATEGORY,
                spec.member, a, b, z, z + face, length(sub(b, a))))
            index += 1
    return out


def _overlaps(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> bool:
    """Whether ``[a_lo, a_hi]`` and ``[b_lo, b_hi]`` share any interior, past a small epsilon."""
    return a_lo < b_hi - 1e-9 and b_lo < a_hi - 1e-9




def _band_geometry(rw: ResolvedWall, layer):
    """The furring band's centreline start, unit direction, and run length."""
    start, end = band_axis(rw.axis, layer.polygon)
    return start, unit(sub(end, start)), length(sub(end, start))


def _band_extent(polygon, p0, direction, axis_len: float) -> tuple[float, float]:
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


def _module_stations(first: float, last: float, spacing: float,
                     width: float) -> list[float]:
    """``first`` on centre to ``last``, with ``last`` always framed.

    Same rule the stud module follows: a strip at each end of the run whatever the
    spacing does, and no module strip so close to the end one that the two are the same
    piece of wood.
    """
    if last < first:
        return []
    stations = [first]
    index = 1
    while first + index * spacing < last - width + 1e-9:
        stations.append(first + index * spacing)
        index += 1
    if last - stations[-1] > width - 1e-9:
        stations.append(last)
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
