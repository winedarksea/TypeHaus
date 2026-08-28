"""Uplift hardware along the continuous load path, derived from the resolved framing.

The rest of the load path was already derived — MASA anchors and STHD holdowns off the sill
runs, SP ties off the studs, CS16 coil strap across the stacked wall lines (all
``takeoff/anchors.py``), and LUS/LSSR/HUCQ hangers off the *hung* member ends
(``takeoff/hangers.py``). This module bills the joints none of those can see: the ends that
**bear** rather than hang, and the post/beam connections.

Four rules, one condition each:

* **Bearing ties.** A rafter, truss heel or floor joist whose underside lands on the top of a
  support its own element names as a ``bearing_ref``. This is the exact complement of
  ``hangers.hung_connections`` — a hung end develops its depth *inside* a carrier, a bearing
  end sits *on* one — and the two rules cannot both fire on the same end because the
  elevation test that separates them is one-sided (see ``_bears_on``).
* **Post bases.** Every wood post whose section the catalog stocks a base for.
* **Post/beam straps.** Every beam end that lands on such a post.
* **Lateral tie plates.** The bottom plate of every framed wall standing on a floor band.

Two disciplines the whole module keeps:

* **Supports come from the element's own ``bearing_refs``**, never from a proximity search
  over every wall. A floor crosses walls it does not bear on; the model already states which
  ones carry it, so a tie is billed against a declared bearing and nothing else.
* **An authored ``Connector`` wins.** Every rule skips a joint a plan already modelled by
  hand — the same double-billing guard ``Material.exposed_fastener`` is for. The sunken
  garden and the breezeway author twenty connectors between them, and without this each of
  them would be bought twice.

A joint this module cannot bill is not silently dropped: ``checks/structural/uplift_path.py``
reports every link of the path that no hardware covers, which is where a concrete column, a
post with no declared bearing, or an unstocked section shows up.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Beam, Connector, Post
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_HURRICANE_TIE,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_POST_BASE,
    hardware_for_role,
    hardware_for_role_and_nominal,
    hardware_row,
    structural_hardware_catalog,
)
from typehaus.takeoff.hardware_config import FT_TO_M, UpliftTieRules
from typehaus.takeoff.plan_geometry import centerline_endpoints, distance_point_to_segment

_M_TO_FT = 3.280839895013123


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
                              half_width_m=wall.thickness_m / 2.0)
    for solid in model.solids:
        if solid.tag != tag or solid.category != "beam":
            continue
        start, end = centerline_endpoints(list(solid.outline))
        return BearingSupport(tag=tag, p0=start, p1=end, top_z_m=solid.z1_m,
                              half_width_m=fallback_half_width_m)
    return None


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
                                   top_z_m=top, half_width_m=wall.thickness_m / 2.0))
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
    rise_m = bottom_z_m - support.top_z_m
    return -1e-9 <= rise_m <= rules.bearing_seat_tolerance_in * M_PER_IN


def _member_ends(member) -> list:
    """Both ends as ``(point, underside_z)``. A raked member carries its own end elevations,
    which is what tells a rafter's eave seat from its ridge end."""
    return [
        (member.p0, member.z0_m),
        (member.p1, member.z0_m if member.z0_end_m is None else member.z0_end_m),
    ]


# --- the authored-connector guard ----------------------------------------------------


def _authored_connectors(model: ResolvedModel) -> list:
    return [element for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if isinstance(element, Connector)]


def tags_covered_by(model: ResolvedModel, kinds: frozenset) -> set:
    """Every element tag an authored connector of one of ``kinds`` already names.

    Tag-based rather than geometric on purpose: ``Connector.connects`` is the plan's own
    statement of which members the hardware joins, it is what
    ``emit/draw/roofframingplan.py`` reads for the tie schedule, and it survives a member
    being re-resolved at a slightly different coordinate.
    """
    covered: set = set()
    for element in _authored_connectors(model):
        if element.kind in kinds:
            covered.update(element.connects)
    return covered


# --- rule 1: bearing ties ------------------------------------------------------------


def _tied_assemblies(model: ResolvedModel, elements_by_tag: dict, rules: UpliftTieRules):
    """``(resolved assembly, declared bearing tags, member categories to tie)`` triples.

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
            yield roof, refs, rules.tied_roof_categories
    for floor in model.floors:
        element = elements_by_tag.get(floor.tag)
        joists = getattr(element, "joists", None)
        refs = tuple(getattr(joists, "bearing_refs", ()) or ())
        if refs:
            yield floor, refs, rules.tied_floor_categories


def authored_joints(model: ResolvedModel, kinds: frozenset) -> set:
    """Every PAIR of tags one authored connector of ``kinds`` names together.

    The coarser :func:`tags_covered_by` answers "is this element mentioned at all", which is
    the right question for a post base (a post has exactly one) and the wrong one for a
    beam/post joint (a post carries several beams, and they are not all strapped).
    """
    joints: set = set()
    for element in _authored_connectors(model):
        if element.kind not in kinds:
            continue
        tags = list(element.connects)
        for index, left in enumerate(tags):
            for right in tags[index + 1:]:
                joints.add(frozenset({left, right}))
    return joints


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
    fallback_m = rules.bearing_plan_tolerance_in * M_PER_IN
    grid_m = max(rules.coincident_bearing_tolerance_in, 1e-6) * M_PER_IN
    covered = tags_covered_by(model, frozenset({ConnectorKind.HURRICANE_TIE,
                                                ConnectorKind.HOLD_DOWN}))
    elements_by_tag = {element.tag: element
                       for storey in model.plan.storeys
                       for element in model.plan.storey_elements(storey.tag)}

    found: dict = {}
    for resolved, refs, categories in _tied_assemblies(model, elements_by_tag, rules):
        if resolved.tag in covered:
            continue
        supports: list = []
        seen: set = set()
        for tag in refs:
            if tag in covered:
                continue
            declared = _support(model, tag, fallback_m)
            if declared is None:
                continue
            for support in _bearing_line(model, declared, rules):
                if support.tag in seen or support.tag in covered:
                    continue
                seen.add(support.tag)
                supports.append(support)
        if not supports:
            continue
        for member in resolved.members:
            if member.category not in categories:
                continue
            for point, bottom_z in _member_ends(member):
                for support in supports:
                    if not _bears_on(point, bottom_z, support, rules):
                        continue
                    key_point = (round(point[0] / grid_m), round(point[1] / grid_m))
                    found[(support.tag, key_point)] = BearingConnection(
                        support_tag=support.tag, storey=resolved.storey,
                        assembly_tag=resolved.tag, member_profile=member.profile,
                        member_category=member.category, key_point=key_point)
                    break  # one tie per end, even where two declared bearings overlap
    return sorted(found.values(), key=lambda c: (c.support_tag, c.key_point))


def bearing_uplift_tie_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """One tie per bearing joint, grouped by what bears where.

    Grouped on ``(member category, profile)`` rather than per support: a framer buys a box of
    H2.5A, and the support tag belongs in the basis where it can be audited rather than in a
    row that splits one order across thirty walls.
    """
    connections = bearing_connections(model, rules)
    if not connections:
        return []
    item = hardware_for_role(ROLE_HURRICANE_TIE)
    groups: dict = {}
    for connection in connections:
        entry = groups.setdefault((connection.member_category, connection.member_profile),
                                  {"by_storey": Counter(), "supports": Counter()})
        entry["by_storey"][connection.storey] += rules.ties_per_bearing
        entry["supports"][connection.support_tag] += 1

    rows = []
    for (category, profile), entry in sorted(groups.items()):
        by_storey, supports = entry["by_storey"], entry["supports"]
        rows.append(hardware_row(
            item, scope=f"{category.replace('_', ' ')} bearing", size=profile,
            count=int(sum(by_storey.values())), by_storey=dict(sorted(by_storey.items())),
            basis=(f"{rules.ties_per_bearing} per bearing joint x {sum(supports.values())} "
                   f"{profile} {category} ends seated on the declared bearings "
                   + ", ".join(f"{tag} x{n}" for tag, n in sorted(supports.items())))))
    return rows


# --- rule 2: post bases --------------------------------------------------------------


def catalogued_post_sizes() -> set:
    return {nominal for item in structural_hardware_catalog()
            if item.role == ROLE_POST_BASE for nominal in item.fits_nominal}


def _posts(model: ResolvedModel) -> list:
    return [(storey.tag, element) for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if isinstance(element, Post)]


def post_base_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """A standoff base under every wood post that declares what it bears on.

    Three conditions are deliberately out of reach of this rule, and each is a real one
    rather than a rounding decision:

    * a post inside a wall (``within_wall``) is developed by the wall's own plates and studs,
      which the SP tie already bills — a base under it would be a second connection at a
      joint that already has one;
    * a post with no ``supported_by`` has nothing declared to fasten a base to;
    * a concrete column is not a section this catalog stocks a wood base for.

    All three are reported by ``structural.uplift_load_path`` rather than being quietly
    absent from the order.
    """
    stocked = catalogued_post_sizes()
    covered = tags_covered_by(model, frozenset({ConnectorKind.POST_BASE}))
    by_size: dict = {}
    for storey, post in _posts(model):
        if post.tag in covered or post.within_wall or not post.supported_by:
            continue
        if post.size not in stocked:
            continue
        entry = by_size.setdefault(post.size, {"by_storey": Counter(), "tags": []})
        entry["by_storey"][storey] += 1
        entry["tags"].append(post.tag)

    rows = []
    for size in sorted(by_size):
        entry = by_size[size]
        item = hardware_for_role_and_nominal(ROLE_POST_BASE, size)
        by_storey = entry["by_storey"]
        rows.append(hardware_row(
            item, scope="post base", count=int(sum(by_storey.values())), size=size,
            by_storey=dict(sorted(by_storey.items())),
            basis=(f"one per {size} post that declares what it bears on: "
                   + ", ".join(sorted(entry["tags"])))))
    return rows


# --- rule 3: post/beam straps --------------------------------------------------------


def post_beam_strap_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """A strap at every beam end that lands on a wood post.

    ``Beam.bearing_refs`` already names the post, so this counts declarations rather than
    searching for coincident geometry. One strap per beam end by default, not the matched
    pair: a pair only fits where the beam *stops* at the post, and a beam that runs past its
    post has one reachable face — the same lesson ``KneeBraceRules`` learned when a pair rule
    billed twelve unbuildable braces. A joint that wants two authors the second by hand.
    """
    stocked = catalogued_post_sizes()
    posts = {post.tag: post for _storey, post in _posts(model)}
    # A joint is covered only when one authored connector names BOTH its members. Matching
    # on either alone credits the wrong joint: the breezeway straps its two ROOF beams to
    # PT-BW-1..4, and a post-only test would hand those straps to the two FLOOR beams landing
    # on the same four posts, which carry nothing at all.
    covered = authored_joints(model, frozenset({ConnectorKind.HOLD_DOWN,
                                                ConnectorKind.POST_CAP,
                                                ConnectorKind.HURRICANE_TIE}))
    by_storey: Counter = Counter()
    joints: list = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Beam):
                continue
            for ref in element.bearing_refs:
                post = posts.get(ref)
                if post is None or post.size not in stocked:
                    continue
                if frozenset({element.tag, post.tag}) in covered:
                    continue
                by_storey[storey.tag] += rules.straps_per_post_beam_joint
                joints.append(f"{element.tag}->{post.tag}")
    if not joints:
        return []
    item = hardware_for_role(ROLE_BEAM_HOLD_DOWN)
    return [hardware_row(
        item, scope="beam on post", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())),
        basis=(f"{rules.straps_per_post_beam_joint} per beam end landing on a wood post "
               f"({len(joints)} joints: " + ", ".join(sorted(joints)) + ")"))]


# --- rule 4: lateral tie plates ------------------------------------------------------


def lateral_tie_plate_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """LTP4s along the bottom plate of every framed wall that stands on a floor band.

    The sill-on-concrete case is already anchored (MASA, ``anchors.mudsill_anchor_rows``);
    this is the joint above it, where a wall's bottom plate meets the rim and band of the
    floor it stands on and nothing but the nailing holds the two together laterally. The
    walls are exactly the upper halves of the resolved stack edges, so the rule follows the
    model's own account of what stands on what.
    """
    foundations = {wall.tag for wall in model.walls if wall.is_foundation}
    # Only the framed-on-framed stack edges. A wall standing on concrete is a sill, and its
    # plate is already anchored through to the pour by ``anchors.mudsill_anchor_rows`` — a
    # tie plate there would be a second connection at a joint that has one, which is exactly
    # the double-billing ``Material.exposed_fastener`` exists to prevent elsewhere.
    stacked_above = {edge.upper_wall for edge in model.stack_edges
                     if edge.lower_wall not in foundations}
    pitch_m = rules.tie_plate_pitch_ft * FT_TO_M
    by_storey: Counter = Counter()
    total_length_m, walls = 0.0, 0
    for wall in model.walls:
        if wall.tag not in stacked_above or wall.is_foundation:
            continue
        if not any(member.category == "stud" for member in wall.members):
            continue
        (x0, y0), (x1, y1) = wall.axis
        length_m = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        by_storey[wall.storey] += max(rules.minimum_tie_plates_per_wall,
                                      int(length_m / pitch_m) + 1)
        total_length_m += length_m
        walls += 1
    if not walls:
        return []
    item = hardware_for_role(ROLE_LATERAL_TIE_PLATE)
    return [hardware_row(
        item, scope="wall on floor band", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())), length_ft=total_length_m * _M_TO_FT,
        basis=(f"{rules.tie_plate_pitch_ft:g} ft o.c. (min "
               f"{rules.minimum_tie_plates_per_wall} per wall) along the bottom plate of "
               f"{walls} framed walls standing on a framed floor band (a wall on concrete "
               f"is a sill and is anchored by its mudsill anchors instead), "
               f"{total_length_m * _M_TO_FT:.1f} LF"))]


def uplift_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """Every uplift line, in the order the load path runs: roof down to the band."""
    return [
        *bearing_uplift_tie_rows(model, rules),
        *post_base_rows(model, rules),
        *post_beam_strap_rows(model, rules),
        *lateral_tie_plate_rows(model, rules),
    ]
