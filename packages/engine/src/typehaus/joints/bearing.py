"""Where members **bear** — the joints that sit on a support rather than hang in one.

The complement of :mod:`typehaus.joints.hung`: a hung end develops its depth *inside* a
carrier, a bearing end sits *on* one, and the two rules cannot both fire on the same end
because the elevation test that separates them is one-sided (see :func:`_bears_on`).

Two disciplines the whole module keeps:

* **Supports come from the element's own ``bearing_refs``**, never from a proximity search
  over every wall. A floor crosses walls it does not bear on; the model already states which
  ones carry it, so a joint is located against a declared bearing and nothing else.
* **An authored ``Connector`` wins.** A joint the plan already modelled by hand is not
  derived again — the same double-billing guard ``Material.exposed_fastener`` is for.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.config import FT_TO_M, UpliftTieRules
from typehaus.hardware.plan_geometry import (
    centerline_endpoints,
    distance_point_to_segment,
    segment_crossing,
)
from typehaus.joints.authored import (
    authored_connectors,
    authored_joints,
    tags_covered_by,
)
from typehaus.joints.hosts import member_storeys
from typehaus.joints.model import axis_of
from typehaus.model.enums import ConnectorKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sweep import interpolate_along, straight_sweep_band

_M_TO_FT = 3.280839895013123
#: How far below a support's top a member underside may read and still sit on it. A level
#: joist on a TILTED beam is seated ~1/64" under the interpolated top (catlin's balcony); a
#: hung end is a full carrier depth below, so 1/8" cannot admit one.
_SEAT_SLACK_M = 0.125 * M_PER_IN

@dataclass(frozen=True)
class BearingSupport:
    """A declared bearing line and the elevation a member seats on it at."""

    tag: str
    p0: tuple
    p1: tuple
    top_z_m: float
    #: Half the support's own width. A member end lands *on* a plate, not on its centreline,
    #: so the plan test has to admit half a wall — and a 15 1/2" foundation wall and a 6 3/4"
    #: partition do not get the same allowance.
    half_width_m: float
    #: The seat elevation at the FAR end (``p1``), for a support that is not level — a
    #: TILTED beam (``Beam.top_rise_end``). ``None`` is level and ``top_z_m`` answers for
    #: the whole run. The bounding box cannot: it reports the run's HIGH end, and a member
    #: seated at the low end then measures ~2" BELOW its own bearing and is dropped.
    top_z_end_m: float | None = None
    #: Is the wood this support presents to a tie preservative-treated? Decides the tie's
    #: COATING (see :func:`_exposure`), never its capacity. The support and not the member,
    #: because the support is the leg the model can answer for: a joist carries no material
    #: ref of its own, while a beam has an assembly and a wall has a layer stack.
    treated: bool = False
    #: A wall, not a beam. A floor joist on a wall plate is toe-nailed (IRC Table R602.3(1))
    #: and held down by the wall above it; only a joist on a beam takes a tie.
    wall: bool = False


@dataclass(frozen=True)
class BearingConnection:
    """One detected bearing: which member profile, on which support, in which storey."""

    support_tag: str
    storey: str
    #: The roof or floor whose member this is. Carried so a consumer can ask about ONE
    #: assembly: ``emit/draw/roofframingplan.py`` needs "is THIS roof restrained", and the
    #: load-path check needs each floor's own tie count rather than the total on a bearing
    #: wall it shares with the floor next door.
    assembly_tag: str
    member_profile: str
    member_category: str
    #: Plan location, snapped to ``coincident_bearing_tolerance_in``. Two joist segments that
    #: meet over an interior bearing wall are one joint and take one tie, not two.
    key_point: tuple
    #: Whether the support is preservative-treated wood — see ``takeoff/uplift._exposure``.
    #: Part of the connection and not of the row, because two joists of one profile can land
    #: on a dry plate and a treated beam and must then be two orders.
    support_treated: bool = False
    #: The *unsnapped* plan point, in project-frame metres. ``key_point`` above is grid
    #: indices and answers "is this the same joint as that one"; this answers "where is it",
    #: and a marker drawn on the snapped one would sit up to half a tolerance off its member.
    point_m: tuple = (0.0, 0.0)
    #: The seat elevation under this end — the support's top face, interpolated along a
    #: tilted support rather than read off its bounding box.
    z_m: float = 0.0
    #: The support line, snapped to ``"x"``/``"y"``. A tie straddles its plate, so the
    #: support's direction and not the member's is what orients it.
    axis: str = "x"


def _support(model: ResolvedModel, tag: str, fallback_half_width_m: float):
    """Resolve a ``bearing_ref`` tag to the line and the top face a member seats on.

    A wall bears at its ``plate_top_z_m`` when it has one and at ``z1_m`` when it does not
    (a foundation wall's sill plate is a construction return, not part of the wall solid).
    Either way ``_bears_on`` measures upward from this, so the plate's own thickness lands
    inside the seat tolerance rather than needing to be modelled here.
    """
    wall = model.wall(tag)
    if wall is not None:
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        return BearingSupport(tag=tag, p0=wall.axis[0], p1=wall.axis[1], top_z_m=top,
                              half_width_m=wall.thickness_m / 2.0,
                              treated=is_treated(model, wall.assembly), wall=True)
    for solid in model.solids:
        if solid.tag != tag or solid.category != "beam":
            continue
        treated = is_treated(model, solid.assembly, material_ref=solid.material)
        band = straight_sweep_band(solid)
        if band is not None:
            (start, end), depth, soffit0, soffit1 = band
            return BearingSupport(tag=tag, p0=start, p1=end, top_z_m=soffit0 + depth,
                                  half_width_m=fallback_half_width_m, treated=treated,
                                  top_z_end_m=soffit1 + depth)
        start, end = centerline_endpoints(list(solid.outline))
        return BearingSupport(tag=tag, p0=start, p1=end, top_z_m=solid.z1_m,
                              half_width_m=fallback_half_width_m, treated=treated)
    return None


def is_treated(model: ResolvedModel, assembly_tag: str | None,
                material_ref: str | None = None) -> bool:
    """Does this support present preservative-treated wood to a connector landing on it?

    Read off the catalog ``Material``, never off a tag spelling: ``BEAM_GLULAM_TREATED``
    happens to say so in its name and ``POST_KDAT`` does not, and a rule that grepped for
    "treated" would get one right by luck and the other wrong.
    """
    ref = material_ref or assembly_structure_material(model.plan, assembly_tag)
    if not ref:
        return False
    material = model.plan.library.material(ref)
    return bool(material is not None and material.preservative_treated)


def _bearing_line(model: ResolvedModel, declared: BearingSupport,
                  rules: UpliftTieRules) -> list:
    """``declared`` plus every wall collinear with it at the same bearing elevation.

    A house names a *wall* in ``bearing_refs``; what actually carries the floor is a bearing
    LINE, and the resolver splits that line into as many walls as the plan has nodes on it
    (catlin's west line is three segments, of which ``FS-S-WEST`` names one). Billing only
    the named segment would tie four of that floor's twenty-eight trusses and call the order
    complete.

    Two guards keep this from wandering: the candidate must be collinear with the declared
    wall *within half its thickness* — the same allowance the seat test uses — and its
    bearing top must match, which is what stops the foundation wall directly below a framed
    one from joining its own successor's line.
    """
    seat_m = rules.bearing_seat_tolerance_in * M_PER_IN
    (ax, ay), (bx, by) = declared.p0, declared.p1
    dx, dy = bx - ax, by - ay
    span = (dx * dx + dy * dy) ** 0.5
    if span < 1e-9:
        return [declared]
    line = [declared]
    for wall in model.walls:
        if wall.tag == declared.tag:
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        if abs(top - declared.top_z_m) > seat_m:
            continue
        offsets = [abs((px - ax) * dy - (py - ay) * dx) / span for px, py in wall.axis]
        if max(offsets) > max(declared.half_width_m, wall.thickness_m / 2.0):
            continue
        line.append(BearingSupport(tag=wall.tag, p0=wall.axis[0], p1=wall.axis[1],
                                   top_z_m=top, half_width_m=wall.thickness_m / 2.0,
                                   wall=True))
    return line


def _bears_on(point: tuple, bottom_z_m: float, support: BearingSupport,
              rules: UpliftTieRules) -> bool:
    """Does a member end sit on this support's top face?

    Deliberately **one-sided** in elevation: a bearing member's underside is at the support
    top or a plate's thickness above it, never below. That single sign is what keeps this
    rule off the ends ``hangers.py`` already bills — a joist hung in an 11 7/8" beam has its
    underside ~11 7/8" *below* the beam top, so it fails here no matter how loose the
    tolerance gets.
    """
    plan_tolerance_m = max(support.half_width_m,
                           rules.bearing_plan_tolerance_in * M_PER_IN)
    if distance_point_to_segment(point, support.p0, support.p1) > plan_tolerance_m:
        return False
    # A TILTED support's seat is at a different elevation at every station, so the member
    # end is measured against the seat directly under it rather than against the run's box.
    top_z_m = support.top_z_m
    if support.top_z_end_m is not None:
        top_z_m = interpolate_along((support.p0, support.p1), point,
                                    support.top_z_m, support.top_z_end_m)
    rise_m = bottom_z_m - top_z_m
    return -_SEAT_SLACK_M <= rise_m <= rules.bearing_seat_tolerance_in * M_PER_IN


def _seat_z(point: tuple, support: BearingSupport) -> float:
    """The support's top face directly under ``point``.

    A TILTED support's seat is at a different elevation at every station, so this
    interpolates rather than reading the run's bounding box — the same correction
    :func:`_bears_on` makes to decide the end bears at all.
    """
    if support.top_z_end_m is None:
        return support.top_z_m
    return interpolate_along((support.p0, support.p1), point,
                             support.top_z_m, support.top_z_end_m)


def _member_ends(member) -> list:
    """Both ends as ``(point, underside_z)``. A raked member carries its own end elevations,
    which is what tells a rafter's eave seat from its ridge end."""
    return [
        (member.p0, member.z0_m),
        (member.p1, member.z0_m if member.z0_end_m is None else member.z0_end_m),
    ]


def _crossing(member, support: BearingSupport):
    """Where a LEVEL member passes over a support between its ends, as ``(point, underside)``.

    A deck joist cantilevered past its outer beam has no END near that beam — the tip is 9"
    out on catlin's balcony, past the 8" plan tolerance — yet it bears there and needs a tie.
    Level members only: a rafter crosses its plate at a birdsmouth, which is its seat end
    already, and its raked underside is not a bearing plane.
    """
    if member.z0_end_m is not None:
        return None
    crossing = segment_crossing(member.p0, member.p1, support.p0, support.p1)
    return None if crossing is None else (crossing[0], member.z0_m)


def _tied_assemblies(model: ResolvedModel, elements_by_tag: dict, rules: UpliftTieRules):
    """``(assembly, bearing tags, member categories to tie, tie on walls?)`` per roof/floor.

    Roofs and floors are walked separately because each names its bearings on a different
    field — a ``Roof`` on ``bearing_refs``, a ``FloorSystem`` on ``joists.bearing_refs`` —
    and they tie different member categories. A rafter roof seats on its rafters; a truss
    roof seats on its heels, and its top chords pass a foot and a half over the plate on
    their way to the overhang, so tying those would be tying the wrong member.
    """
    for roof in model.roofs:
        element = elements_by_tag.get(roof.tag)
        refs = tuple(getattr(element, "bearing_refs", ()) or ())
        if refs:
            yield roof, refs, rules.tied_roof_categories, True
    for floor in model.floors:
        element = elements_by_tag.get(floor.tag)
        joists = getattr(element, "joists", None)
        refs = tuple(getattr(joists, "bearing_refs", ()) or ())
        if refs:
            yield floor, refs, rules.tied_floor_categories, rules.tie_floor_joists_on_walls


def bearing_line_tags(model: ResolvedModel, refs: tuple, rules: UpliftTieRules) -> set:
    """Every wall tag on the bearing lines ``refs`` names.

    Public because ``checks/structural/uplift_path.py`` has to count ties along the same
    lines this module ties along. A check that re-derived which walls carry a floor would
    drift from the take-off, and then the report and the order would disagree about the same
    house — so there is one answer and both callers read it.
    """
    fallback_m = rules.bearing_plan_tolerance_in * M_PER_IN
    tags: set = set()
    for ref in refs:
        declared = _support(model, ref, fallback_m)
        if declared is not None:
            tags.update(support.tag for support in _bearing_line(model, declared, rules))
    return tags


def bearing_connections(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """Every rafter/truss-heel/joist end that bears on a declared support."""
    found = {(c.support_tag, c.key_point): c
             for c, _support in _derive(model, rules, authored=False)}
    return sorted(found.values(), key=lambda c: (c.support_tag, c.key_point))


def authored_tie_gaps(model: ResolvedModel, rules: UpliftTieRules,
                      tolerance_in: float = 3.0) -> list:
    """Bearings of an assembly whose ties are AUTHORED that no authored tie sits at.

    A tie naming a roof or floor stands the derived rule down for the whole assembly, so the
    coverage has to be checked crossing by crossing: a derived bearing with no authored
    tie (naming that assembly) within ``tolerance_in`` along its support is a gap.
    """
    ties: dict = {}
    for element in authored_connectors(model):
        if element.kind in _SEATED_KINDS:
            for tag in element.connects:
                ties.setdefault(tag, []).append(element.position.xy_m)
    tol_m = tolerance_in * M_PER_IN
    gaps: dict = {}
    for connection, support in _derive(model, rules, authored=True):
        (ax, ay), (bx, by) = support.p0[:2], support.p1[:2]
        length = math.hypot(bx - ax, by - ay) or 1.0
        ux, uy = (bx - ax) / length, (by - ay) / length
        reach_m = max(support.half_width_m, rules.bearing_plan_tolerance_in * M_PER_IN)
        px, py = connection.point_m

        if not any(abs((tx - px) * ux + (ty - py) * uy) <= tol_m
                   and abs((tx - ax) * uy - (ty - ay) * ux) <= reach_m
                   for tx, ty in ties.get(connection.assembly_tag, ())):
            gaps[(connection.support_tag, connection.key_point)] = connection
    return sorted(gaps.values(), key=lambda c: (c.assembly_tag, c.support_tag, c.key_point))


_SEATED_KINDS = frozenset({ConnectorKind.HURRICANE_TIE, ConnectorKind.HOLD_DOWN})


def _derive(model: ResolvedModel, rules: UpliftTieRules, *, authored: bool):
    """``(connection, support)`` per seated end or crossing.

    ``authored=False`` is the take-off: assemblies an authored tie names are skipped, and so
    is a support named together with its assembly by one. ``authored=True`` derives ONLY
    those assemblies, ignoring the hand-off, so their ties can be checked point by point.
    """
    fallback_m = rules.bearing_plan_tolerance_in * M_PER_IN
    grid_m = max(rules.coincident_bearing_tolerance_in, 1e-6) * M_PER_IN
    # The ASSEMBLY hand-off is coarse: a tie naming a roof or a floor is the plan saying "I
    # own this deck's uplift"; ``authored_tie_gaps`` checks the claim tie by tie.
    covered = tags_covered_by(model, _SEATED_KINDS)
    # The SUPPORT hand-off is pairwise: a connector naming a support stands the rule down
    # only for the member bearing on it (``authored_joints``).
    joints = set() if authored else authored_joints(model, _SEATED_KINDS)
    elements_by_tag = {element.tag: element
                       for storey in model.plan.storeys
                       for element in model.plan.storey_elements(storey.tag)}

    for resolved, refs, categories, on_walls in _tied_assemblies(model, elements_by_tag, rules):
        if (resolved.tag in covered) is not authored:
            continue
        supports: list = []
        seen: set = set()
        for tag in refs:
            if frozenset({tag, resolved.tag}) in joints:
                continue
            declared = _support(model, tag, fallback_m)
            if declared is None:
                continue
            for support in _bearing_line(model, declared, rules):
                if (support.tag in seen
                        or frozenset({support.tag, resolved.tag}) in joints):
                    continue
                seen.add(support.tag)
                if on_walls or not support.wall:
                    supports.append(support)
        if not supports:
            continue
        for member in resolved.members:
            if member.category not in categories:
                continue
            ties: list = []  # (point, support)
            for point, bottom_z in _member_ends(member):
                for support in supports:
                    if _bears_on(point, bottom_z, support, rules):
                        ties.append((point, support))
                        break  # one tie per end, even where two declared bearings overlap
            # Every support an end bears on, not only the one the break above tied: a
            # collinear second segment is the same bearing, not a crossing.
            tied = {support.tag for point, bottom_z in _member_ends(member)
                    for support in supports if _bears_on(point, bottom_z, support, rules)}
            for support in supports:
                crossing = None if support.tag in tied else _crossing(member, support)
                if crossing is not None and _bears_on(*crossing, support, rules):
                    ties.append((crossing[0], support))
            for point, support in ties:
                key_point = (round(point[0] / grid_m), round(point[1] / grid_m))
                yield BearingConnection(
                    support_tag=support.tag, storey=resolved.storey,
                    assembly_tag=resolved.tag, member_profile=member.profile,
                    member_category=member.category, key_point=key_point,
                    support_treated=support.treated,
                    point_m=(point[0], point[1]), z_m=_seat_z(point, support),
                    axis=axis_of(support.p0, support.p1)), support


@dataclass(frozen=True)
class ContinuousBearing:
    """A member bedded on its support for its whole length, and the stations along it.

    ``bearing_connections`` above locates member ENDS, which is the right rule for every
    rafter, truss heel and joist in the house and the wrong one for a beam that never leaves
    its wall — catlin's ridge is the case, and nothing else in the load path covers it.
    """

    category: str
    profile: str
    storey: str
    length_m: float
    #: One station per tie, in metres from ``p0``. Ends included: a run is a fencepost count,
    #: not a division — which is why this is a list of places and not just a number.
    stations_m: tuple[float, ...]
    p0: tuple
    p1: tuple
    z_m: float


def continuous_bearing_members(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """Every continuously supported member, with its ties' stations.

    The pitch is the house's own; both it and the part are commodity choices recorded in
    ``houses/catlin/notes/ridge_beam_detail.md``, not an engineered uplift design. This
    derives a *schedule* — how many ties, where — and no part of it reads a wind field,
    computes a tributary uplift, or compares one against the tie's allowable.
    """
    pitch_m = max(rules.continuous_bearing_pitch_ft, 0.5) * FT_TO_M
    storeys = member_storeys(model)
    found = []
    for member in model.all_members():
        if not member.continuously_supported:
            continue
        count = int(math.floor(member.length_m / pitch_m + 1e-9)) + 1
        found.append(ContinuousBearing(
            category=member.category, profile=member.profile,
            storey=storeys.get(member.parent_uid, ""),
            length_m=member.length_m,
            stations_m=tuple(min(index * pitch_m, member.length_m) for index in range(count)),
            p0=member.p0, p1=member.p1, z_m=member.z0_m))
    return found
