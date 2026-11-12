"""Which runs land in a ventilator's plenums, and which are its distribution network.

Split out of ``erv_static.py`` for size. Membership and topology only: the friction physics is
``resolve/duct_sizing.py`` and the per-run drop is ``erv_static._duct_drop``.
"""

from __future__ import annotations

import math
from collections import deque

from typehaus.checks.mep.erv_network import connected_distribution, rectangular_chain
from typehaus.checks.mep.erv_static_terms import type_for
from typehaus.checks.registry import CheckContext
from typehaus.model.enums import EquipmentKind
from typehaus.resolve.duct_sizing import effective_diameter_m


def equipment_kinds(ctx: CheckContext) -> dict[str, str]:
    """``{tag: EquipmentKind value}`` from the authored elements.

    ``ResolvedCanvasObject.kind`` is the ELEMENT kind ("Equipment"), not the equipment
    kind — the resolved object carries geometry and the authored one carries what the
    machine is — so the two have to be joined by tag.
    """
    return {element.tag: element.kind.value
            for element in ctx.plan.all_elements()
            if element.element_kind == "Equipment"}


def manifolds(ctx: CheckContext) -> dict[str, object]:
    """Distribution plenums by tag — a ``DUCT_MANIFOLD`` that actually distributes.

    **Two ports or more, and the exterior hoods are why.** A hood carries ``DUCT_MANIFOLD``
    because the enum has no HOOD kind, and it states one 6" port so the port census can
    grade it. One port does not distribute anything: counted here, the exhaust hood would
    make ``DU-ERV-EA`` — a 6" trunk carrying the whole house's stale air — read as a radial
    off it, and the worst path would be a trunk landing on a hood rather than the branch it
    actually is. ``mep.erv_manifold_ports`` still grades every one of them.

    **Or ONE port and a dimensioned collar** (2026-09-19). A trunk-and-branch plenum has a
    single branch port — the trunk — and is a distribution box in every sense that matters
    here: catlin's ``EQ-M-ERV-MAN-EXH`` feeds ten terminals through it. The port count
    cannot tell it from a hood, and a dimensioned collar (round, or an EXACT rectangular
    port) can: declaring WHERE a collar is
    is a positive statement that this box hands air to a named branch, and no hood in the
    catalog declares one (``library/hvac.py`` states counts and no layouts on purpose).
    Without this the level-2 trunk-and-branch tree left the static budget silently, ten
    runs at a time, which is the failure mode this whole module is written against.
    """
    out: dict[str, object] = {}
    kinds = equipment_kinds(ctx)
    for obj in ctx.model.canvas_objects:
        if kinds.get(obj.tag) != EquipmentKind.DUCT_MANIFOLD.value:
            continue
        product = type_for(ctx, obj.type_ref, "equipment_types")
        if product is None:
            continue
        reader = getattr(product, "collars", None)
        dimensioned = bool(reader()) if callable(reader) else False
        # An EXACT rectangular port is the same positive statement for a flat trunk or neck.
        dimensioned = dimensioned or any(
            port.is_exact() and port.width is not None and port.depth is not None
            and port.width != port.depth for port in getattr(product, "ports", ()))
        if (getattr(product, "duct_ports", None) or 0) >= 2 or dimensioned:
            out[obj.tag] = product
    return out


def _end_host(ctx: CheckContext, duct, index: int) -> tuple[str | None, tuple]:
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
    return equipment_at_end(ctx, z, duct.path[index]), (duct.path[index], z)


def radial_landings(ctx: CheckContext) -> dict[str, str]:
    """``{run tag: manifold tag}`` for every run that lands in a fabricated plenum.

    A run is a *radial* when one of its ends is inside a ``DUCT_MANIFOLD``'s case and on
    one of its branch ports rather than its trunk collar — by ROLE, the census's own
    ``lands_on_branch_port``, so a 3" radial reduced onto a 4" collar is a radial, not a
    trunk summed into the whole side. A rectangular run is sized by its equivalent diameter.

    "Lands in" is ``duct_connectivity.equipment_at_end``, the one definition of it in the
    engine, rather than a second footprint test that could drift from the first.

    A rectangle chained end-to-end to a landed rectangle (the trunk beyond a neck) lands on
    the same plenum: the branches tee off it, and it is the run they hop through.
    """
    from typehaus.checks.mep.erv_manifold_ports import lands_on_branch_port, plenum_air_ports

    plenums, ports = manifolds(ctx), plenum_air_ports(ctx.model)
    out: dict[str, str] = {}
    for duct in ctx.model.ducts:
        if not duct.path or effective_diameter_m(duct) is None:
            continue
        if duct.diameter_m is None and duct.material is None:
            continue
        for index in (0, -1):
            host, end = _end_host(ctx, duct, index)
            if host in plenums and lands_on_branch_port(
                    plenums[host], ports.get(host, ()), duct, end):
                out[duct.tag] = host
                break
    rect = {tag: host for tag, host in out.items()
            if next(d for d in ctx.model.ducts if d.tag == tag).diameter_m is None}
    out.update(rectangular_chain(ctx.model.ducts, rect))
    return _through_trunks(ctx, out)


def _diameter(ctx: CheckContext, tag: str) -> float:
    return next((effective_diameter_m(d) or 0.0 for d in ctx.model.ducts if d.tag == tag), 0.0)


def _cfm(ctx: CheckContext, tag: str) -> float | None:
    return next((d.design_cfm for d in ctx.model.ducts if d.tag == tag), None)


def direct_landings(ctx: CheckContext, landings: dict[str, str]) -> set[str]:
    """The landings whose own end is in the plenum: a branch off a trunk (or off another
    radial, whatever its size) is not one, so its flow is never added to the box twice."""
    ancestors = landing_ancestors(ctx, landings)
    return {tag for tag in landings if tag not in ancestors}


def landing_ancestors(ctx: CheckContext, landings: dict[str, str]) -> dict[str, list[str]]:
    """``{landing: [landings between it and its plenum, nearest first]}``.

    Breadth-first from the landings whose own end is in the plenum over joints within one
    plenum's landings, so a branch's path carries the trunk (and neck) its air also crosses.
    """
    from typehaus.resolve.mep_soffit import ducts_are_joined

    by_host: dict[str, list[str]] = {}
    for tag, host in sorted(landings.items()):
        by_host.setdefault(host, []).append(tag)
    ducts = {d.tag: d for d in ctx.model.ducts}
    out: dict[str, list[str]] = {}
    for host, tags in by_host.items():
        anchored = [t for t in tags if any(_end_host(ctx, ducts[t], i)[0] == host
                                           for i in (0, -1))]
        parent: dict[str, str | None] = dict.fromkeys(anchored)
        queue = deque(anchored)
        while queue:
            current = queue.popleft()
            for tag in tags:
                if tag not in parent and ducts_are_joined(ctx.model, current, tag):
                    parent[tag] = current
                    queue.append(tag)
        for tag in parent:
            chain, up = [], parent[tag]
            while up is not None:
                chain.append(up)
                up = parent[up]
            if chain:
                out[tag] = chain
    return out


def _through_trunks(ctx: CheckContext, landings: dict[str, str]) -> dict[str, str]:
    """Branches that reach a plenum THROUGH a trunk, not by landing in its case.

    **A plenum does not have to be a manifold.** Catlin's level 2 went trunk-and-branch on
    2026-09-19 — thirteen home-run lanes will not leave one closet through an open-web
    truss field — so what leaves ``EQ-M-ERV-MAN-EXH`` is one trunk and the ten branches
    are tee'd off it out in the floor. Every one of them was silently outside this check:
    ``radial_landings`` asked whether a run ends INSIDE a plenum's case, and they end on a
    duct. Ten runs left the static budget and nothing said so, which is the failure mode
    this whole module is written against.

    Hops repeat to a fixed point since 2026-11-11, when shared legs made a branch off a
    branch real (SAUNA-SUP off GYM, BED1 off BED2, RET3 off LAUNDRY). A run reached this way
    is graded exactly as a radial is — its own flow against its own product — plus the trunk
    it crosses (:func:`landing_ancestors`). Only a ROUND run hops: a rectangle never joins by
    contact with a round one, and a trunk's size is its equivalent diameter when rectangular.
    """
    from typehaus.resolve.mep_soffit import ducts_are_joined

    sizes = {duct.tag: effective_diameter_m(duct) for duct in ctx.model.ducts
             if effective_diameter_m(duct) is not None}
    ducts = {duct.tag: duct for duct in ctx.model.ducts}
    out = dict(landings)
    # To a fixed point: a branch off a branch (catlin's RET3 off LAUNDRY) hops too.
    changed = True
    while changed:
        changed = False
        for duct in ctx.model.ducts:
            if duct.tag in out or not duct.path or duct.diameter_m is None:
                continue
            for trunk_tag, host in sorted(out.items()):
                if trunk_tag == duct.tag:
                    continue
                # **A branch leaves its parent, and the test is DIRECTION.** Its first vertex
                # sits on the parent away from the parent's plenum end. Without it the hop
                # runs backwards: catlin's 6" basement trunk is joined to radials that land
                # in their plenum, and inheriting the plenum would add its 210 cfm to the
                # box's own 60. A strictly smaller run joined to the parent still hops, as
                # before 2026-11-11.
                smaller = duct.diameter_m < sizes.get(trunk_tag, 0.0) - 1e-9
                if (_leaves(ctx, duct, ducts[trunk_tag], host, out)
                        or (smaller and ducts_are_joined(ctx.model, duct.tag, trunk_tag))):
                    out[duct.tag] = host
                    changed = True
                    break
    return out


def _on_run(point, z, duct, tolerance: float) -> bool:
    from typehaus.checks.mep.erv_routes import distance_to_run

    return distance_to_run(point, z, duct) <= tolerance


def _end_point(duct, index: int) -> tuple[tuple[float, float], float | None]:
    z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
    return duct.path[index], z


def _leaves(ctx: CheckContext, duct, parent, host: str, landings: dict[str, str]) -> bool:
    """Whether ``duct``'s first vertex is on ``parent``, away from the parent's plenum end.

    The parent's plenum end is the end in ``host``'s case, else the end lying on another
    run of the same plenum (a branch's own tee), else its first vertex.
    """
    from typehaus.resolve.mep_envelopes import joint_tolerance_m

    tolerance = joint_tolerance_m()
    start, z = _end_point(duct, 0)
    if not _on_run(start, z, parent, tolerance):
        return False
    others = [d for d in ctx.model.ducts
              if d.tag != parent.tag and landings.get(d.tag) == host]
    plenum_end = 0
    for index in (0, -1):
        point, pz = _end_point(parent, index)
        if _end_host(ctx, parent, index)[0] == host or any(
                _on_run(point, pz, other, tolerance) for other in others):
            plenum_end = index
            break
    point, pz = _end_point(parent, plenum_end)
    gap = math.dist(start, point)
    if z is not None and pz is not None:
        gap = math.hypot(gap, z - pz)
    return gap > tolerance


def network(ctx: CheckContext, machine_tag: str, landings: dict[str, str]) -> list[object]:
    """The runs that belong to this ventilator's own distribution, and nothing else.

    Seed from radials and equipment landings, then follow compatible physical duct joints.
    Remote pieces of a split header contribute even when neither end touches equipment.

    **A run that states no ``material`` is not in it.** A round run that DOES state one but
    matches no ``DuctProductType`` stays in, reported as a gap by its own pair — a house that
    forgot to author a row.

    **A rectangular run is in only when anchored on one of the distributing plenums** (an end
    inside its case), or chained end-to-end to such a run (a neck and its trunk). It is never
    anchored by a MIXING_BOX or PLENUM and never pulled by a joint from a round run: Catlin's
    System 1 shares the mixing box with this machine and its trunks are fabricated rectangular
    sheet metal, which this budget has no business grading. Round runs joined to an included
    rectangle (the takeoffs off a flat trunk) come in as usual.
    """
    kinds = equipment_kinds(ctx)
    plenums = manifolds(ctx)
    anchors = {machine_tag, *landings.values()}
    anchors |= {tag for tag, kind in kinds.items()
                if kind in (EquipmentKind.MIXING_BOX.value, EquipmentKind.PLENUM.value)}
    seeds: set[str] = set()
    rect_seeds: dict[str, str] = {}
    for duct in ctx.model.ducts:
        if duct.material is None or not duct.path:
            continue
        rectangular = duct.diameter_m is None
        if effective_diameter_m(duct) is None:
            continue
        if not rectangular and duct.tag in landings:
            seeds.add(duct.tag)
            continue
        hosts = {_end_host(ctx, duct, index)[0] for index in (0, -1)}
        if rectangular and (duct.tag in landings or hosts & plenums.keys()):
            rect_seeds[duct.tag] = duct.tag
        elif not rectangular and hosts & anchors:
            seeds.add(duct.tag)
    seeds |= rectangular_chain(ctx.model.ducts, rect_seeds).keys()
    return connected_distribution(ctx.model.ducts, seeds)
