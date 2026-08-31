"""A closed loop of retaining walls, summed as ONE free body.

``retaining_system/<the cross-member's tag>``. The item exists because the per-wall free
body is the wrong one for a court: ``retaining_wall`` grades each wall as an isolated free
cantilever resisting by base friction alone, and what is built at the sunken garden is a
19'-0" x 28'-0" court whose walls are cast into a closed loop. ``W-SG-W2`` (axis x = 8'-0")
and ``W-SG-E2`` (axis x = 28'-0") face each other across it, same height, same length, and
**their thrusts cancel through the concrete between them.** Only the south wall is unopposed.

**Do not pair opposing walls.** The sum below is over the whole group as one rigid body and
the cancellation falls out of equilibrium, which is both simpler and more honest than
matching walls up: it needs no special case for "the unopposed one", and it answers what
happens to a wall whose restraint reaches nothing — its thrust simply lands in the
resultant and nothing cancels it.

**What earns the cancellation is a real load path, and it is a limit state here rather than
a claim.** ``strut compression`` puts a number on the axial force the cross-member carries
across the court, so a reviewer has something to disagree with instead of a sentence.

**Oracle.** ``houses/catlin/notes/sunken_garden_court_free_body.md``, worked by hand in a
separate pass; ``tests/test_retaining_court.py`` reproduces it, and separately breaks each
condition in :func:`_verify` in turn to confirm the answer is INCOMPLETE and never OK. A
calculation that only agrees with itself is not verified, and a *verification* that has
never been shown to fail is not a verification.

**At-rest governs here, and that is the price of the restraint** (see
:data:`AT_REST_IS_THE_GRADED_CASE`). ``retaining_wall``'s free-cantilever branch grades at
active; this one does not, and the two docstrings say which they use so a reader comparing
records is not comparing load cases.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.retaining_basis import (
    BASIS,
    EARTH_PRESSURE_LOAD_FACTOR,
    PRESUMPTIVE_FC_PSI,
    REQUIRED_FS,
    _base_interface,
    _geometry,
    _structure_thickness_in,
    analyse,
)
from typehaus.engineering.soil import SOIL_UNIT_WEIGHT_BAND_PCF, presumptive

KIND = "retaining_system"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"

#: **The graded case is at-rest, not active, and that is a consequence of the restraint and
#: not a preference.** You cannot cite a permanent base restraint in the resistance term and
#: simultaneously claim the walls are free enough to shed to the active wedge in the demand
#: term; crediting one concedes the other. Worked in the note: a base-restrained, top-free
#: 12" stem deflects about 0.16" at the head, roughly 0.0013H, which is at the very bottom
#: of the 0.001H-0.004H a granular backfill needs to mobilise the active state. Active is
#: *arguable*. At-rest is *defensible*, and a screening should be the second thing.
AT_REST_IS_THE_GRADED_CASE = True

#: ACI 318-19 §14.5.4 (§22.6.5.2 in 318-11): a structural plain concrete wall's axial
#: strength is ``Pn = 0.45 f'c Ag [1 - (lc/32h)^2]``. **§14.5.6 is BEARING and is the wrong
#: section** — a mis-citation worth naming, because 14.5.6's coefficient is 0.85 and using it
#: here would nearly double the allowable.
#:
#: The slenderness bracket is dropped, which is conservative: it can only reduce the
#: capacity, and this strut is buried on all four faces with the ground bracing it against
#: the buckling that term describes. Claiming that bracing would be the unsafe direction, so
#: the term is discarded rather than credited.
#:
#: Plain concrete IS in scope here, unlike the stem: R22.6.3 excludes only walls free to
#: translate at top and bottom, and a strut cast into a closed loop is the opposite case.
STRUT_STRESS_COEFFICIENT = 0.45

_M_PER_FT = 0.3048


@dataclass(frozen=True)
class _Member:
    """One wall in the loop, with the vector its thrust acts along."""

    tag: str
    length_ft: float
    thrust_plf: float
    weight_plf: float
    friction: float
    #: Unit vector the retained soil pushes this wall along, in plan. The exterior face is
    #: at ``+outward_sign * normal(start->end)`` (``resolve/orientation``), so the soil
    #: pushes the other way.
    push: tuple[float, float]

    @property
    def demand_lb(self) -> float:
        return self.thrust_plf * self.length_ft

    @property
    def capacity_lb(self) -> float:
        return self.friction * self.weight_plf * self.length_ft


def _foundation_walls(ctx: EngineeringContext) -> list:
    from typehaus.model.structure import FoundationWall

    return [w for w in ctx.plan.all_elements() if isinstance(w, FoundationWall)]


def _loops(ctx: EngineeringContext) -> dict[str, list]:
    """Groups of walls that name the same ``base_restraint_ref``, keyed by that ref.

    The key is the **cross-member's tag** and not an invented group name. That is what makes
    the item id ``retaining_system/W-SG-ARCH`` name a thing the model actually contains — the
    element whose presence closes the loop and whose removal breaks it, which is exactly the
    edit that should stale the seal. ``retaining_system/SG-COURT`` would name nothing, and
    ``EngineeringRecord``'s identity rule is that an item is per element.
    """
    groups: dict[str, list] = {}
    for wall in _foundation_walls(ctx):
        ref = getattr(wall, "base_restraint_ref", None)
        if ref and getattr(wall, "lateral_support", None) == "base":
            groups.setdefault(ref, []).append(wall)
    return {ref: sorted(walls, key=lambda w: w.tag) for ref, walls in groups.items()}


def _bridges(edges: list[tuple[str, str, str]]) -> set[str]:
    """Tags of the edges that lie on **no** cycle, by Hopcroft-Tarjan lowlink.

    An edge on no cycle is a bridge, and a bridge is precisely a wall whose removal opens
    the loop. Two edges lie on a common cycle exactly when they survive here and land in the
    same component of the bridge-free graph, which is what :func:`_verify` tests.
    """
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for tag, a, b in edges:
        adjacency.setdefault(a, []).append((b, tag))
        adjacency.setdefault(b, []).append((a, tag))

    order: dict[str, int] = {}
    low: dict[str, int] = {}
    bridges: set[str] = set()
    counter = 0

    for root in sorted(adjacency):
        if root in order:
            continue
        # Iterative DFS: a house is small, but a recursive one is a latent stack limit and
        # this runs over every foundation wall on a storey.
        stack: list[tuple[str, str | None, int]] = [(root, None, 0)]
        order[root] = low[root] = counter
        counter += 1
        while stack:
            node, via, index = stack[-1]
            if index < len(adjacency[node]):
                stack[-1] = (node, via, index + 1)
                nxt, tag = adjacency[node][index]
                if tag == via:
                    continue
                if nxt in order:
                    low[node] = min(low[node], order[nxt])
                else:
                    order[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append((nxt, tag, 0))
            else:
                stack.pop()
                if stack:
                    parent = stack[-1][0]
                    low[parent] = min(low[parent], low[node])
                    if low[node] > order[parent] and via is not None:
                        bridges.add(via)
    return bridges


def _cycle_components(edges: list[tuple[str, str, str]]) -> dict[str, int]:
    """Edge tag -> the 2-edge-connected component it sits in; bridges are dropped.

    Every edge left here is on a cycle, and two edges sharing a component are on a *common*
    cycle. That is the whole geometric content of "closes the loop".
    """
    bridges = _bridges(edges)
    kept = [(tag, a, b) for tag, a, b in edges if tag not in bridges]
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for _tag, a, b in kept:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    labels: dict[str, int] = {}
    index: dict[str, int] = {}
    for tag, a, _b in kept:
        root = find(a)
        labels[tag] = index.setdefault(root, len(index))
    return labels



def _cross_span(ctx: EngineeringContext, cross) -> float:
    """The cross-member's own clear span, in feet — what its slenderness is measured on."""
    resolved = next((w for w in ctx.model.walls if w.tag == cross.tag), None)
    if resolved is None:
        return 0.0
    (x0, y0), (x1, y1) = resolved.axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / _M_PER_FT


def _verify(ctx: EngineeringContext, ref: str, members: list) -> list[str]:
    """The conditions that have to hold for the restraint to be real. Names what does not.

    Every one of these is **derived from the model rather than asserted by the author**,
    which is the difference between a restraint and a free pass. Authoring
    ``base_restraint_ref`` states an intention; this function goes and checks it.
    """
    from typehaus.model.enums import LayerFunction
    from typehaus.model.structure import FoundationWall

    missing: list[str] = []
    cross = ctx.plan.by_tag(ref)
    if not isinstance(cross, FoundationWall):
        return [f"a FoundationWall tagged {ref} — {len(members)} wall(s) name it as the "
                f"element restraining their base and the model has no such wall"]

    walls = _foundation_walls(ctx)
    edges = [(w.tag, w.start_node, w.end_node) for w in walls
             if w.start_node and w.end_node and w.start_node != w.end_node]
    components = _cycle_components(edges)

    if ref not in components:
        return [f"a closed structural loop through {ref} — it lies on no cycle of walls, so "
                f"it is a bridge and restrains nothing. An open U does not restrain its own "
                f"ends"]
    loop = components[ref]
    for member in members:
        if components.get(member.tag) != loop:
            missing.append(
                f"a closed structural loop through {ref} — {member.tag}'s base is not "
                f"restrained by it, because the two lie on no common cycle")

    # Continuity: a loop of cast concrete, or it is a diagram rather than a load path.
    for wall in [cross, *members]:
        if _structure_thickness_in(ctx, wall.assembly) is None:
            missing.append(f"a concrete STRUCTURE layer on {wall.tag} (assembly "
                           f"{wall.assembly}) — the loop has to be cast, not framed")
            continue
        assembly = next((a for a in ctx.plan.library.assemblies
                         if a.tag == wall.assembly), None)
        if assembly is not None and not any(
                layer.function is LayerFunction.STRUCTURE
                and "concrete" in (layer.material_ref or "")
                for layer in assembly.layers):
            missing.append(f"a cast-concrete STRUCTURE layer on {wall.tag} — its structure "
                           f"layer is not concrete, so the corners cannot be cast continuous")
    return missing


def _members(ctx: EngineeringContext, walls: list, *, soil, soil_pcf: float
             ) -> tuple[list[_Member], list[str]]:
    """Each wall's thrust, weight and push direction, on one soil unit weight."""
    from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign

    out: list[_Member] = []
    missing: list[str] = []
    for wall in walls:
        geometry, geometry_missing = _geometry(ctx, wall)
        if geometry is None:
            missing.extend(geometry_missing)
            continue
        base = _base_interface(ctx, wall) or soil
        case = analyse(geometry, soil, at_rest=AT_REST_IS_THE_GRADED_CASE,
                       soil_pcf=soil_pcf, base=base)
        resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
        if resolved is None:
            missing.append(f"a resolved {wall.tag} to take its length and direction from")
            continue
        (x0, y0), (x1, y1) = resolved.axis
        dx, dy = x1 - x0, y1 - y0
        length_m = (dx * dx + dy * dy) ** 0.5
        if not length_m:
            missing.append(f"a non-zero length on {wall.tag}")
            continue
        windings = resolve_storey_windings(ctx.plan, resolved.storey)
        sign = wall_outward_sign(ctx.plan, wall, resolved.storey,
                                 windings.sign_for_wall(wall))
        # Left-hand normal of start->end, per ``resolve/geometry.normal``. The exterior face
        # is at +sign along it, so the retained soil pushes along -sign.
        nx, ny = -dy / length_m, dx / length_m
        out.append(_Member(
            tag=wall.tag, length_ft=length_m / _M_PER_FT, thrust_plf=case.thrust_plf,
            weight_plf=case.weight_plf, friction=base.friction_coefficient,
            push=(-sign * nx, -sign * ny)))
    return out, missing


def _free_body(members: list[_Member]) -> tuple[float, float, float]:
    """``(demand_lb, capacity_lb, cancelled_lb)`` for the group as one rigid body.

    The demand is the **2-D resultant** of the members' thrusts, not their scalar sum: two
    walls facing each other across a court push in opposite directions and equilibrium is
    where the cancellation belongs. Friction is isotropic, so every member's base resists
    the resultant whichever way it points.
    """
    rx = sum(m.demand_lb * m.push[0] for m in members)
    ry = sum(m.demand_lb * m.push[1] for m in members)
    demand = (rx * rx + ry * ry) ** 0.5
    scalar = sum(m.demand_lb for m in members)
    return demand, sum(m.capacity_lb for m in members), scalar - demand


def _strut(ctx: EngineeringContext, cross, members: list[_Member],
           span_ft: float) -> tuple[float, float, str]:
    """``(Pu, phi_Pn, how)`` in the cross-member, pounds. ACI 318-19 §14.5.4.

    The force taken is **half the largest member's whole thrust**, with no friction credit.
    A wall tied at both ends delivers about half its thrust to each; refusing to net the base
    friction off first is deliberate, because that friction is already spent in the sliding
    row above and spending it twice is how a load path stops being one. Taking the LARGEST
    member rather than the ones the strut actually ties is conservative by about 9% here, and
    is what keeps this row from having to know which walls face each other.

    Strength design, unlike every row above it and for the same reason ``stem flexure`` is:
    ``0.45 f'c Ag [1 - (lc/32h)^2]`` is a nominal strength, so comparing a service force to
    it would spend the whole load factor. ``Pu = 1.6 P``, ``phi = 0.60`` (Table 21.2.1).

    The slenderness bracket IS applied here, on the full clear span and on the member's
    thinnest dimension. Buried in compacted stone on both faces the strut is braced far
    better than that, so this is the conservative end of a range whose other end is 1.0 —
    and it is applied rather than argued away because a claim about bracing is exactly the
    kind of claim this module exists to refuse.
    """
    thickness_in = _structure_thickness_in(ctx, cross.assembly) or 0.0
    height_in = 0.0
    if cross.top_elevation is not None and cross.bottom_elevation is not None:
        height_in = cross.top_elevation.inches - cross.bottom_elevation.inches
    area_in2 = thickness_in * height_in
    force_lb = 0.5 * max((m.demand_lb for m in members), default=0.0)
    demand = EARTH_PRESSURE_LOAD_FACTOR * force_lb
    if not area_in2 or not thickness_in:
        return demand, 0.0, "no resolvable section on the cross-member"
    slenderness = 1.0 - (span_ft * 12.0 / (32.0 * thickness_in)) ** 2
    capacity = (0.60 * STRUT_STRESS_COEFFICIENT * PRESUMPTIVE_FC_PSI * area_in2
                * max(slenderness, 0.0))
    return demand, capacity, (f"{force_lb:,.0f} lb service on {thickness_in:.0f}\" x "
                              f"{height_in:.1f}\" ({area_in2:,.0f} in2), {span_ft:.1f}' clear, "
                              f"slenderness factor {max(slenderness, 0.0):.2f}")


@keys(KIND)
def enumerate_systems(ctx: EngineeringContext) -> list[str]:
    return sorted(_loops(ctx))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, ref, members) for ref, members in sorted(_loops(ctx).items())]


def system_factors(ctx: EngineeringContext, ref: str, members: list
                   ) -> dict[str, tuple[float, float]] | None:
    """``{soil_pcf: (demand_lb, capacity_lb)}`` — the numbers a per-wall record quotes back.

    Exposed so ``retaining_wall`` can put ``system_demand``/``system_capacity`` in each
    member's fingerprint, which is what makes moving the cross-member, or moving one wall,
    stale all of the group's seals together.
    """
    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None or _verify(ctx, ref, members):
        return None
    out: dict[str, tuple[float, float]] = {}
    for pcf in SOIL_UNIT_WEIGHT_BAND_PCF:
        built, missing = _members(ctx, members, soil=soil, soil_pcf=pcf)
        if missing:
            return None
        demand, capacity, _ = _free_body(built)
        out[f"{pcf:.0f}"] = (demand, capacity)
    return out


def _one(ctx: EngineeringContext, ref: str, members: list) -> EngineeringRecord:
    tags = tuple(sorted({ref, *(w.tag for w in members)}))
    soil = presumptive(getattr(ctx, "soil_class", None))
    missing: list[str] = []
    if soil is None:
        missing.append("a declared soil class (Site/profile soil_class)")
    missing.extend(_verify(ctx, ref, members))

    built_by_pcf: dict[float, list[_Member]] = {}
    if soil is not None and not missing:
        for pcf in SOIL_UNIT_WEIGHT_BAND_PCF:
            built, member_missing = _members(ctx, members, soil=soil, soil_pcf=pcf)
            missing.extend(member_missing)
            built_by_pcf[pcf] = built

    if missing:
        return EngineeringRecord(
            item_id=item_id(KIND, ref), kind=KIND, key=ref,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=(f"{ref}: the court's base restraint could not be verified, so the "
                     f"walls it is claimed to restrain have no closed free body"),
            missing=tuple(dict.fromkeys(missing)), element_tags=tags)

    cross = ctx.plan.by_tag(ref)
    low, high = SOIL_UNIT_WEIGHT_BAND_PCF
    states_by_pcf = {}
    for pcf, built in built_by_pcf.items():
        demand, capacity, cancelled = _free_body(built)
        strut_demand, strut_capacity, how = _strut(ctx, cross, built, _cross_span(ctx, cross))
        states_by_pcf[pcf] = (
            (LimitState("sliding", REQUIRED_FS,
                        capacity / demand if demand else float("inf"), "",
                        "IRC R404.4", is_safety_factor=True),
             LimitState("strut compression", strut_demand, strut_capacity, "lb",
                        f"ACI 318 §14.5.4, phi 0.60 at 1.6H — {how}")),
            demand, capacity, cancelled)

    over_low = any(not state.ok for state in states_by_pcf[low][0])
    over_high = any(not state.ok for state in states_by_pcf[high][0])
    states, demand, capacity, cancelled = states_by_pcf[low]

    inputs = tuple(
        item for member in built_by_pcf[low] for item in (
            Quantity(f"thrust_{member.tag}", member.thrust_plf, "plf", 1.0),
            Quantity(f"weight_{member.tag}", member.weight_plf, "plf", 1.0),
            Quantity(f"length_{member.tag}", member.length_ft, "ft", 0.01),
            Quantity(f"friction_{member.tag}", member.friction, "", 0.01),
        )
    ) + (
        Quantity("cross_thickness",
                 _structure_thickness_in(ctx, cross.assembly) or 0.0, "in", 0.5),
        Quantity("cross_height",
                 (cross.top_elevation.inches - cross.bottom_elevation.inches)
                 if cross.top_elevation is not None and cross.bottom_elevation is not None
                 else 0.0, "in", 0.01),
    )
    notes = (
        f"ONE free body, not {len(members)}: the members are cast into a closed loop through "
        f"{ref}, so their thrusts are summed as a 2-D resultant and opposed walls cancel in "
        f"equilibrium rather than by being paired up.",
        f"{cancelled:,.0f} lb of the {sum(m.demand_lb for m in built_by_pcf[low]):,.0f} lb "
        f"of total thrust cancels across the court; {demand:,.0f} lb reaches the ground.",
        "GRADED AT AT-REST (60 psf/ft). A permanent base restraint and an active wedge are "
        "not both available: crediting the restraint concedes that the wall does not move "
        "enough to shed to active. See the module docstring.",
        "SCREENING on presumptive code values, not a design. The cancellation depends on "
        "the loop being CAST — corner bar development is ordinary practice and is not "
        "something this engine has looked at.",
        "Sequence is the objection this answers: the cross-member is cast WITH the walls, "
        "so the loop is closed before any backfill goes in. A floor slab strut would not be.",
    )

    if over_low != over_high:
        return EngineeringRecord(
            item_id=item_id(KIND, ref), kind=KIND, key=ref,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=(f"{ref}: the court's verdict turns on the soil unit weight — it checks "
                     f"at {high:.0f} pcf and does not at {low:.0f} pcf"),
            inputs=inputs, limit_states=states,
            missing=("a measured soil unit weight (no code table publishes one, and this "
                     "court's answer depends on it)",),
            notes=notes, element_tags=tags)

    governing = max(states, key=lambda state: state.ratio)
    return EngineeringRecord(
        item_id=item_id(KIND, ref), kind=KIND, key=ref,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over_low else Status.OK,
        summary=(f"{ref} closes a {len(members)}-wall court: {demand:,.0f} lb of resultant "
                 f"thrust against {capacity:,.0f} lb of base friction, "
                 f"FS {capacity / demand:.2f} against the 1.50 IRC R404.4 requires"),
        inputs=inputs, limit_states=states, notes=notes, element_tags=tags)
