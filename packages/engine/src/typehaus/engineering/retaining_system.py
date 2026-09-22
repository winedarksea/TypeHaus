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
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import (
    EngineeringContext,
    calc,
    keys,
    oracled_by,
)
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
from typehaus.engineering.tier_surcharge import court_surcharges

KIND = "retaining_system"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
#: ``"2"``: the strut force stopped being ``0.5 * max(member thrust)`` and became a derived
#: reaction projected onto the cross-member's own axis (2026-09-14). Every seal on this kind
#: stales, which is correct — the graded demand moved.
#: ``"3"``: the raised-garden apron's bearing enters each member's thrust as a lateral
#: strip surcharge (``tier_surcharge``, 2026-09-20). The resultant and the strut force moved.
BASIS_VERSION = "3"

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
    #: The stem's own section, feet — what the wall has to pass in-plane shear THROUGH when
    #: its base cannot hold its own thrust. Zero where the model does not say, which
    #: :func:`_corner_transfer` reports rather than defaults around.
    stem_thickness_ft: float = 0.0
    stem_height_ft: float = 0.0

    @property
    def demand_lb(self) -> float:
        return self.thrust_plf * self.length_ft

    @property
    def capacity_lb(self) -> float:
        return self.friction * self.weight_plf * self.length_ft

    @property
    def unassisted_shortfall_lb(self) -> float:
        """What this member's OWN base cannot hold of its OWN thrust.

        **The quantity R2 said nothing was checked against.** The group free body sums
        isotropic friction against one resultant, which is the right rigid-body statement
        for a verified cast loop — but it says nothing about any individual footing, and on
        this court no individual footing holds its own wall: the south wall alone wants
        61,446 lb against 37,993 lb of its own friction. The 23,453 lb difference does not
        vanish because the resultant is smaller than the sum; it travels through the corners
        as in-plane shear, and until 2026-09-14 nothing named it, let alone graded it.
        """
        return max(0.0, self.demand_lb - self.capacity_lb)


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



def _cast_beams(ctx: EngineeringContext) -> list:
    from typehaus.resolve.assembly_material import is_cast_beam

    return [e for e in ctx.plan.all_elements() if is_cast_beam(ctx.plan, e)]


def _cross_axis(ctx: EngineeringContext, cross
                ) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """The cross-member's plan axis, metres: a wall's resolved axis, or a cast beam's
    centreline read off its resolved solid."""
    resolved = next((w for w in ctx.model.walls if w.tag == cross.tag), None)
    if resolved is not None:
        return resolved.axis
    solid = next((s for s in ctx.model.solids
                  if s.tag == cross.tag and s.category == "beam"), None)
    if solid is None or len(solid.outline) != 4:
        return None
    a, b, c, d = solid.outline
    return (((a[0] + d[0]) / 2, (a[1] + d[1]) / 2), ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2))


def _cross_section_in(ctx: EngineeringContext, cross) -> tuple[float, float]:
    """``(thickness, height)`` of the cross-member, inches; zero where unstated."""
    from typehaus.model.structure import Beam
    from typehaus.resolve.framing.profiles import cross_section

    if isinstance(cross, Beam):
        cs = cross_section(cross.size)
        return cs.width_m / _M_PER_FT * 12.0, cs.depth_m / _M_PER_FT * 12.0
    thickness_in = _structure_thickness_in(ctx, cross.assembly) or 0.0
    height_in = 0.0
    if cross.top_elevation is not None and cross.bottom_elevation is not None:
        height_in = cross.top_elevation.inches - cross.bottom_elevation.inches
    return thickness_in, height_in


def _cross_span(ctx: EngineeringContext, cross) -> float:
    """The cross-member's own clear span, in feet — what its slenderness is measured on."""
    axis = _cross_axis(ctx, cross)
    if axis is None:
        return 0.0
    (x0, y0), (x1, y1) = axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / _M_PER_FT


def _verify(ctx: EngineeringContext, ref: str, members: list) -> list[str]:
    """The conditions that have to hold for the restraint to be real. Names what does not.

    Every one of these is **derived from the model rather than asserted by the author**,
    which is the difference between a restraint and a free pass. Authoring
    ``base_restraint_ref`` states an intention; this function goes and checks it.
    """
    from typehaus.model.enums import LayerFunction
    from typehaus.model.structure import FoundationWall
    from typehaus.resolve.assembly_material import is_cast_beam

    missing: list[str] = []
    cross = ctx.plan.by_tag(ref)
    if not (isinstance(cross, FoundationWall) or is_cast_beam(ctx.plan, cross)):
        return [f"a FoundationWall or concrete Beam tagged {ref} — {len(members)} wall(s) name "
                f"it as the element restraining their base and the model has no such member"]

    edges = [(w.tag, w.start_node, w.end_node) for w in [*_foundation_walls(ctx),
                                                          *_cast_beams(ctx)]
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
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
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
    # The apron founded in the retained soil pushes too (``tier_surcharge``), and the loop
    # carries that thrust as it carries the earth's.
    tiers, tier_missing = court_surcharges(ctx, soil_pcf)
    for wall in walls:
        geometry, geometry_missing = _geometry(ctx, wall)
        if geometry is None:
            missing.extend(geometry_missing)
            continue
        missing.extend(tier_missing.get(wall.tag, ()))
        base = _base_interface(ctx, wall) or soil
        tier = tiers.get(wall.tag)
        case = analyse(geometry, soil, at_rest=AT_REST_IS_THE_GRADED_CASE,
                       soil_pcf=soil_pcf, base=base,
                       surcharge=tier.surcharge if tier is not None else None)
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
            push=(-sign * nx, -sign * ny),
            stem_thickness_ft=geometry.stem_thickness_ft,
            stem_height_ft=geometry.stem_height_ft))
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


#: The share of a propped member's thrust that arrives at the **prop**, for the two ends of
#: the corner-fixity family. A retaining leg spans IN PLAN between the monolithic corner at
#: one end and the cross-member at the other, carrying its own base shear as a uniform load:
#:
#: * corner **fully fixed** — propped cantilever, prop reaction ``3wL/8`` -> 0.375
#: * corner **pinned** — simple span, each end ``wL/2`` -> 0.500
#:
#: The real corner is a cast concrete L that is neither. A *softer* corner pushes more into
#: the strut, so the pinned end is the conservative one and is what the record grades; the
#: fixed end is published beside it so a reviewer can see the whole family rather than one
#: number. Nothing here needs a soil spring, which is the point: the coupled model
#: (``analytical/sunken_garden_coupled.py``) is INCOMPLETE without a geotechnical report,
#: and this row must not be.
STRUT_PROP_SHARE = (0.375, 0.500)


def _strut_axis(ctx: EngineeringContext, cross) -> tuple[float, float] | None:
    """The cross-member's unit vector in plan, or ``None`` where it does not resolve."""
    resolved = _cross_axis(ctx, cross)
    if resolved is None:
        return None
    (x0, y0), (x1, y1) = resolved
    dx, dy = x1 - x0, y1 - y0
    length = (dx * dx + dy * dy) ** 0.5
    if not length:
        return None
    return dx / length, dy / length


def strut_reaction_lb(axis: tuple[float, float], members: list[_Member],
                      share: float) -> tuple[float, str]:
    """The compression the cross-member carries, and the member that sets it.

    **This replaced an assertion on 2026-09-14.** The force used to be
    ``0.5 * max(m.demand_lb for m in members)`` — half the largest thrust in the loop,
    whichever wall that was and whichever way it pointed. It bounded nothing in particular:
    on the catlin court the largest member is the SOUTH wall, whose thrust runs
    perpendicular to the strut and cannot compress it at all, so the number graded was a
    wall's load applied to a member it does not push.

    What is computed instead is a reaction. Each member's thrust resultant is projected onto
    the strut's own axis — a wall pushing across the strut contributes nothing, and falls
    out by geometry rather than by being excluded by name — and that along-axis thrust is
    shared between the member's two in-plan supports by ``share`` (see
    :data:`STRUT_PROP_SHARE`).

    The strut is a **compression member between two opposing legs**, so the governing value
    is the LARGER single reaction and not the sum: the two legs push toward each other and
    the strut carries the force that passes through it, once. Where they differ, the
    difference is net base shear on the group and the ``sliding`` row above is where it is
    answered.

    Base friction is still **not** netted off first, for the reason it never was: it is
    already spent in the sliding row, and spending it twice is how a load path stops being
    one.
    """
    best, source = 0.0, ""
    for member in members:
        along = abs(member.push[0] * axis[0] + member.push[1] * axis[1])
        reaction = share * member.demand_lb * along
        if reaction > best:
            best, source = reaction, member.tag
    return best, source


#: ACI 318-19 Table 21.2.1 — the strength reduction factor for shear.
_PHI_SHEAR = 0.75

#: ACI 318-19 §11.5.4.3: for a wall, the effective depth in the direction of shear may be
#: taken as ``0.8 * lw`` — 0.8 of the length of the wall in the plane the shear acts in.
#: In-plane shear on a court wall acts in its VERTICAL plane, so ``lw`` here is the stem
#: height and the section is (stem thickness) x 0.8 (stem height).
_WALL_SHEAR_DEPTH_FACTOR = 0.8


def _corner_transfer(members: list[_Member], fc_psi: float
                     ) -> tuple[float, float, str]:
    """``(Vu, phi_Vn, how)`` — the in-plane shear the cancellation is bought with.

    **R2, and the honest form of it.** The review's complaint was that ``_free_body`` sums
    isotropic friction against a resultant magnitude while each footing's own thrust is
    assumed to cancel through concrete, and that "no footing is checked against its own
    resultant". Half of that is a misreading and half of it is a real gap, and they are
    worth separating because the fix follows from which is which:

    * **Summing friction against the group resultant is correct** for a loop whose closure
      :func:`_verify` has actually established. A rigid body on a uniform interface has one
      capacity disc, and the cancelled component is carried by concrete precisely so that
      none of that disc is spent on it. Apportioning the resultant back to the footings by
      their own capacity and re-checking each is algebraically the same inequality — it
      would add a row and no information.
    * **What is genuinely unchecked is the delivery.** Cancellation is not free: a wall
      whose base friction cannot hold its own thrust has to pass the difference through its
      corners as in-plane shear, and this module's own note has always said corner bar
      development "is not something this engine has looked at". Naming the force is the
      first half of looking.

    So each member's shortfall against its OWN friction is computed, the largest governs,
    and it is graded as one-way shear on that wall's vertical section — ACI 318-19 §22.5.5.1
    ``Vc = 2 lambda sqrt(f'c) b d``, phi 0.60... no: phi 0.75 (Table 21.2.1), with
    ``d = 0.8 lw`` per §11.5.4.3. Concrete alone, no horizontal steel credited, because the
    corner reinforcement is exactly what the model does not carry.

    ``Vu = 1.6 V`` for the same reason the strut row factors: this is a strength check
    against a nominal capacity, and IBC §1605.2's factor on lateral earth pressure applies.
    """
    governing = max(members, key=lambda m: m.unassisted_shortfall_lb, default=None)
    if governing is None or governing.unassisted_shortfall_lb <= 0.0:
        return 0.0, 0.0, ("every member's own base friction holds its own thrust; no "
                          "in-plane transfer is demanded of the corners")
    service = governing.unassisted_shortfall_lb
    demand = EARTH_PRESSURE_LOAD_FACTOR * service
    width_in = governing.stem_thickness_ft * 12.0
    depth_in = _WALL_SHEAR_DEPTH_FACTOR * governing.stem_height_ft * 12.0
    basis = (f"{service:,.0f} lb from {governing.tag} — its own thrust "
             f"{governing.demand_lb:,.0f} lb less its own friction "
             f"{governing.capacity_lb:,.0f} lb")
    if width_in <= 0.0 or depth_in <= 0.0:
        return demand, 0.0, f"no resolvable stem section on {governing.tag} — {basis}"
    capacity = _PHI_SHEAR * 2.0 * (fc_psi ** 0.5) * width_in * depth_in
    return demand, capacity, (
        f"{basis}, through {width_in:.0f}\" x {depth_in:.1f}\" (0.8 lw) of plain section")


def _strut(ctx: EngineeringContext, cross, members: list[_Member],
           span_ft: float) -> tuple[float, float, str]:
    """``(Pu, phi_Pn, how)`` in the cross-member, pounds. ACI 318-19 §14.5.4.

    The force is a **derived reaction**, not an assertion — see :func:`strut_reaction_lb`
    for what moved and why. Graded at the conservative end of the corner-fixity family; the
    other end is reported in ``how`` so the record carries the range a reviewer needs.

    **One cross-member per loop is all this data model can express**, because ``_loops``
    keys a group by the single ``base_restraint_ref`` its walls name. That is not a
    simplification of the catlin court, it is the court: ``W-SG-BRKBM`` restrains
    ``W-SG-W1``/``W-SG-E1``, which are braced top and bottom, name no base restraint and are
    not members of this loop — its own authoring says in as many words that it "reinforces
    nothing". If a future court is ever strutted twice at the same level, the two would
    share this reaction by ``EA/L`` and that is the change to make here.

    Strength design, unlike every row above it and for the same reason ``stem flexure`` is:
    ``0.45 f'c Ag [1 - (lc/32h)^2]`` is a nominal strength, so comparing a service force to
    it would spend the whole load factor. ``Pu = 1.6 P``, ``phi = 0.60`` (Table 21.2.1).

    The slenderness bracket IS applied here, on the full clear span and on the member's
    thinnest dimension. Buried in compacted stone on both faces the strut is braced far
    better than that, so this is the conservative end of a range whose other end is 1.0 —
    and it is applied rather than argued away because a claim about bracing is exactly the
    kind of claim this module exists to refuse.
    """
    thickness_in, height_in = _cross_section_in(ctx, cross)
    area_in2 = thickness_in * height_in

    axis = _strut_axis(ctx, cross)
    if axis is None:
        return 0.0, 0.0, f"no resolved plan axis on {cross.tag} to project thrusts onto"
    fixed_share, pinned_share = STRUT_PROP_SHARE
    force_lb, source = strut_reaction_lb(axis, members, pinned_share)
    lower_lb, _ = strut_reaction_lb(axis, members, fixed_share)
    demand = EARTH_PRESSURE_LOAD_FACTOR * force_lb
    basis = (f"{force_lb:,.0f} lb service reaction from {source or 'no member'} at a pinned "
             f"corner ({lower_lb:,.0f} lb if the corner is fully fixed)")
    if not area_in2 or not thickness_in:
        return demand, 0.0, f"no resolvable section on the cross-member — {basis}"
    slenderness = 1.0 - (span_ft * 12.0 / (32.0 * thickness_in)) ** 2
    capacity = (0.60 * STRUT_STRESS_COEFFICIENT * PRESUMPTIVE_FC_PSI * area_in2
                * max(slenderness, 0.0))
    return demand, capacity, (f"{basis} on {thickness_in:.0f}\" x "
                              f"{height_in:.1f}\" ({area_in2:,.0f} in2), {span_ft:.1f}' clear, "
                              f"slenderness factor {max(slenderness, 0.0):.2f}")


#: The independent hand pass this module is checked against — see ``Oracle``.
#: The closed-loop court free body is hand-worked start to finish in the first note; the
#: isolated free cantilever the loop is compared against is §4 of the second.
oracled_by(
    KIND,
    Oracle(note="sunken_garden_court_free_body.md", test="tests/test_retaining_court.py"),
    Oracle(note="sunken_garden_retaining_screening.md", section="§4",
           test="tests/test_retaining_wall_calc.py"),
)


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


def loop_free_bodies(ctx: EngineeringContext) -> dict[str, dict[str, tuple[float, float]]]:
    """``{loop ref: {soil_pcf: (soil resultant lb, base friction lb)}}`` for every verified
    loop — what ``thermal_break`` pushes the court against."""
    out = {}
    for ref, members in _loops(ctx).items():
        factors = system_factors(ctx, ref, members)
        if factors:
            out[ref] = factors
    return out


def footing_shortfalls(ctx: EngineeringContext
                       ) -> dict[str, dict[float, dict[str, float]]]:
    """``{loop ref: {soil_pcf: {member tag: shortfall lb}}}`` — each member's own thrust
    less its own base friction, the PER FOOTING figures ``_one`` prints. A loop that does
    not verify is omitted; ``thermal_break`` reads its reserve demand here."""
    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None:
        return {}
    out: dict[str, dict[float, dict[str, float]]] = {}
    for ref, members in _loops(ctx).items():
        if _verify(ctx, ref, members):
            continue
        by_pcf: dict[float, dict[str, float]] = {}
        for pcf in SOIL_UNIT_WEIGHT_BAND_PCF:
            built, missing = _members(ctx, members, soil=soil, soil_pcf=pcf)
            if missing:
                break
            by_pcf[pcf] = {m.tag: m.unassisted_shortfall_lb for m in built}
        else:
            out[ref] = by_pcf
    return out


def _surcharge_notes(ctx: EngineeringContext, built: list[_Member], pcf: float
                     ) -> tuple[str, ...]:
    """Name each apron surcharge the members' thrusts now carry, by its source item."""
    tiers, _ = court_surcharges(ctx, pcf)
    parts = [f"{m.tag} +{tiers[m.tag].surcharge.lateral_plf:,.0f} plf via "
             f"{tiers[m.tag].surcharge.source}" for m in built if m.tag in tiers]
    if not parts:
        return ()
    return (f"APRON SURCHARGE, in every thrust above at {pcf:.0f} pcf: " + "; ".join(parts)
            + ". The raised-garden SRW apron stands on its pad inside the retained soil; its "
            "net bearing is a rigid-wall Boussinesq strip load (IBC 2018 §1610.1), worked on "
            "each wall's retaining_wall record. Equal aprons on the two side walls still "
            "cancel; the south wall's does not, so it reaches the resultant whole. Deep-seated "
            "slip under the court and the apron together stays the geotechnical engineer's.",)


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
        corner_demand, corner_capacity, corner_how = _corner_transfer(
            built, PRESUMPTIVE_FC_PSI)
        states_by_pcf[pcf] = (
            (LimitState("sliding", REQUIRED_FS,
                        capacity / demand if demand else float("inf"), "",
                        "IRC R404.4", is_safety_factor=True),
             LimitState("strut compression", strut_demand, strut_capacity, "lb",
                        f"ACI 318 §14.5.4, phi 0.60 at 1.6H — {how}"),
             LimitState("corner shear transfer", corner_demand, corner_capacity, "lb",
                        f"ACI 318 §22.5.5.1 / §11.5.4.3, phi 0.75 at 1.6H — {corner_how}")),
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
        Quantity("cross_thickness", _cross_section_in(ctx, cross)[0], "in", 0.5),
        Quantity("cross_height", _cross_section_in(ctx, cross)[1], "in", 0.01),
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
        "something this engine has looked at, though `corner shear transfer` now puts a "
        "force on what it would have to develop.",
        "PER FOOTING, against its OWN thrust and its OWN friction — the check the group "
        "resultant does not make: " + "; ".join(
            f"{m.tag} {m.demand_lb:,.0f} lb vs {m.capacity_lb:,.0f} lb"
            + (f" (short {m.unassisted_shortfall_lb:,.0f})"
               if m.unassisted_shortfall_lb else " (holds its own)")
            for m in built_by_pcf[low]) + ". A shortfall is not a failure — it is the force "
        "that has to reach the loop, and the `corner shear transfer` row is where it is "
        "graded.",
        "Sequence is the objection this answers: the cross-member is cast WITH the walls, "
        "so the loop is closed before any backfill goes in. A floor slab strut would not be.",
    ) + _surcharge_notes(ctx, built_by_pcf[low], low)

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

    # Named in the summary rather than left for the reader to find, because which row governs
    # is the whole reading of the record: sliding governing says the answer is at the ground,
    # and `strut compression` governing would say the cross-member is the thing to look at.
    governing = max(states, key=lambda state: state.ratio)
    return EngineeringRecord(
        item_id=item_id(KIND, ref), kind=KIND, key=ref,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over_low else Status.OK,
        summary=(f"{ref} closes a {len(members)}-wall court: {demand:,.0f} lb of resultant "
                 f"thrust against {capacity:,.0f} lb of base friction, "
                 f"FS {capacity / demand:.2f} against the 1.50 IRC R404.4 requires "
                 f"({governing.name} governs)"),
        inputs=inputs, limit_states=states, notes=notes, element_tags=tags)
