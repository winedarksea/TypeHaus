"""Are there more branches on a distribution plenum than it was fabricated with ports?

This grades a sentence. ``houses/catlin/plan/mep_erv_l2.py`` has said in prose since the
level-2 layout was drawn that ``EQ-M-ERV-MAN-EXH`` is "full at 10 of 10", and every argument
about where a new terminal could go leans on it — the plant room's extract is where it is
because that manifold has no eleventh port. A comment is not a guard. Add a twelfth radial
and the prose goes on saying ten while the model says twelve, and nothing anywhere notices.

The census is earned rather than counted off a naming convention. A branch is a run whose
end lands *inside the plenum's case* — the same ``duct_connectivity.equipment_at_end`` test
that decides a duct is plumbed into a machine anywhere else in the engine — and on one of its
branch ports rather than its trunk collar (:func:`lands_on_branch_port`). That is what keeps
the trunk out of the count: a 6" riser landing in the same box is the inlet collar, not a
branch, and a census that counted it would report every plenum one over.

**A COUNT and a LAYOUT are two different verdicts, and the check gives whichever the type
earned.** A shared catalog plenum (``library/hvac.py``) states how many collars it has and
nothing about where: there is no shop drawing behind a commodity part, and inventing
positions for one would be the confident nonsense an UNKNOWN exists to avoid. A plenum
fabricated for THIS house can state the layout, and then the question stops being "are
there more pipes than holes" and becomes "does each pipe land on a hole of its own" — which
is the one a fabricator asks. Where collars are dimensioned each radial is assigned to its
nearest free collar, nearest pair first; a radial with no free collar within
:data:`COLLAR_REACH_M` FAILs by name, and so does a collar two radials both want.

**This one does FAIL, and blocks.** Unlike the static budget beside it, there is nothing
approximate here and nothing that depends on what the building needs: a box with six collars
cannot take seven pipes. It is an INTEGRITY finding for the same reason a duplicate tag is —
the model is asserting something that cannot be built.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind
from typehaus.resolve.duct_sizing import effective_diameter_m
from typehaus.resolve.mep_ports import PlacedPort, placed_ports

_M_PER_IN = 0.0254

#: How far from a dimensioned collar a radial's end may be and still be landing on it. One
#: inch: a quarter of a 4" collar, so a run drawn at the collar's own station passes and a
#: run drawn at the plenum's centre — which is how an undimensioned box is authored — does
#: not quietly claim the nearest hole.
COLLAR_REACH_M = 0.0254


@check(Tier.INTEGRITY, "mep.erv_manifold_ports")
def erv_manifold_ports(ctx: CheckContext) -> list[Finding]:
    """Branch count against the fabricated port count, per distribution plenum."""
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    cid = "mep.erv_manifold_ports"
    kinds = {element.tag: element.kind.value for element in ctx.plan.all_elements()
             if element.element_kind == "Equipment"}
    plenums = [obj for obj in ctx.model.canvas_objects
               if kinds.get(obj.tag) == EquipmentKind.DUCT_MANIFOLD.value]
    if not plenums:
        return [not_applicable(cid, "this plan holds no duct manifold, so there is no port "
                                    "census to take", ())]

    types = {row.tag: row for row in ctx.plan.library.equipment_types}
    stated = [obj for obj in plenums
              if getattr(types.get(obj.type_ref or ""), "duct_ports", None) is not None]
    if not stated:
        # Earned: every manifold in the plan was inspected and not one type states a port
        # count, so there is no number in this model to grade a census against. Distinct
        # from "a plenum is missing one", which is the UNKNOWN below.
        return [not_applicable(
            cid, f"none of the {len(plenums)} duct manifolds in this plan names a type "
                 "stating duct_ports, so no port census is expressible", ())]

    out: list[Finding] = []
    air_ports = plenum_air_ports(ctx.model)
    for obj in sorted(plenums, key=lambda item: item.tag):
        product = types.get(obj.type_ref or "")
        ports = getattr(product, "duct_ports", None)
        if ports is None:
            out.append(unknown(
                cid, f"{obj.tag} is a duct manifold but its type "
                     f"({obj.type_ref or 'none'}) states no duct_ports, so the runs landing "
                     "in it cannot be counted against anything", (obj.tag,)))
            continue
        port_diameter = getattr(product, "port_diameter", None)
        if port_diameter is None:
            out.append(unknown(
                cid, f"{obj.tag}'s type states {ports} ports but no port_diameter, so a "
                     "branch cannot be told from the trunk collar", (obj.tag,)))
            continue

        branches: list[str] = []
        trunks: list[str] = []
        ports_here = air_ports.get(obj.tag, ())
        for duct in ctx.model.ducts:
            if not duct.path or effective_diameter_m(duct) is None:
                continue
            for index in (0, -1):
                z = (duct.z_m[index]
                     if duct.z_m and len(duct.z_m) == len(duct.path) else None)
                if equipment_at_end(ctx, z, duct.path[index]) != obj.tag:
                    continue
                if lands_on_branch_port(product, ports_here, duct, (duct.path[index], z)):
                    branches.append(duct.tag)
                else:
                    trunks.append(duct.tag)
                break

        size = f"{port_diameter.meters / _M_PER_IN:.0f}\""
        collars = [port for port in ports_here if port.collar]
        if collars:
            out.extend(_graded_by_collar(cid, obj, collars, branches, ctx, size))
            continue
        if len(branches) > ports:
            out.append(failed(
                cid, f"{obj.tag} ({obj.type_ref}) is fabricated with {ports} x {size} ports "
                     f"and {len(branches)} runs land on them: "
                     f"{', '.join(sorted(branches))}",
                (obj.tag, *sorted(branches)),
                fix="add a port to the plenum's spec, split the load onto a second plenum, "
                    "or give one radial two heads at a grille plenum"))
        else:
            spare = ports - len(branches)
            out.append(passed(
                cid, f"{obj.tag} ({obj.type_ref}): {len(branches)} of {ports} x {size} "
                     f"ports used"
                     + (f", {spare} spare" if spare else ", full")
                     + (f"; trunk collar {', '.join(sorted(trunks))}" if trunks else ""),
                (obj.tag,)))
    return out


def plenum_air_ports(model) -> dict[str, list[PlacedPort]]:
    """``{equipment tag: its placed air ports}``, read once per check."""
    out: dict[str, list[PlacedPort]] = {}
    for port in placed_ports(model):
        if port.duct_system is not None:
            out.setdefault(port.equipment_tag, []).append(port)
    return out


def is_rect_collar(port) -> bool:
    """An EXACT port with a rectangular section (W != D): a collar for a flat trunk or neck.

    Round collars are ``EquipmentType.collars()`` (section == ``port_diameter``); this is the
    rectangular counterpart, read off the placed port.
    """
    section = port.section_m
    return bool(port.exact and section and abs(section[0] - section[1]) > 1e-9)


def lands_on_branch_port(product, ports, duct, end) -> bool:
    """Does this run, ending at ``end`` in this plenum, land on a BRANCH port?

    By role, not by an equal diameter: a 3" radial reduced onto a 4" collar is a branch.

    * larger than ``port_diameter``: the trunk collar, which no branch port can take;
    * equal, or smaller and within :data:`COLLAR_REACH_M` of a collar: a branch;
    * otherwise smaller: the trunk only on positive evidence — the type dimensions its
      collars, and the run's system is a non-collar port's and no collar's
      (``EQ-T-ERV-PLENUM-M-EXH``: a RETURN riser feed into a box whose one collar is
      EXHAUST). Service decides because trunk and riser stations are approximate. Anything
      else is a branch, so a reduced radial drawn off its collar FAILs the census by name.

    **A plenum with an EXACT rectangular port** (:func:`is_rect_collar`) takes a rectangle as
    its branch by that port alone, whatever its ``port_diameter``; a round run there is the
    trunk when its service is a non-collar port's and no collar's.
    """
    rect = [p for p in ports if is_rect_collar(p)]
    if rect:
        # A rectangular collar takes a rectangle; a round run is the trunk where its service
        # is a non-collar port's and no collar's, else a branch.
        if duct.diameter_m is None:
            return True
        return not (duct.system in {p.duct_system for p in ports if p not in rect}
                    and duct.system not in {p.duct_system for p in rect})
    port = getattr(product, "port_diameter", None)
    size = effective_diameter_m(duct)  # a rectangle is sized by its equivalent diameter
    if port is None or size is None or size > port.meters + 1e-6:
        return False
    collars = [p for p in ports if p.collar]
    if (abs(size - port.meters) <= 1e-6 or not collars
            or _reach(end, collars) <= COLLAR_REACH_M):
        return True
    trunk_systems = {p.duct_system for p in ports if not p.collar}
    return not (duct.system in trunk_systems
                and duct.system not in {p.duct_system for p in collars})


def _graded_by_collar(cid, obj, collars, branches, ctx, size) -> list[Finding]:
    """One verdict per plenum whose type dimensions its collars — see the module note.

    Greedy by distance over all (radial, collar) pairs: the closest pair is settled first
    and both drop out, which is the assignment a fitter makes with a tape. It is not a
    global optimum and does not need to be — the question is whether every radial has a
    hole of its own within an inch, and a layout where the answer depends on which optimum
    you take is a layout nobody should build.
    """
    ends = {}
    for duct in ctx.model.ducts:
        if duct.tag not in branches or not duct.path:
            continue
        z = duct.z_m if duct.z_m and len(duct.z_m) == len(duct.path) else None
        # The end that lands in this plenum: whichever of the two is nearer its case.
        pairs = [(duct.path[i], None if z is None else z[i]) for i in (0, -1)]
        ends[duct.tag] = min(pairs, key=lambda pair: _reach(pair, collars))

    scored = sorted(
        ((_gap(ends[tag], collar), tag, collar.port_tag)
         for tag in ends for collar in collars),
        key=lambda row: (row[0], row[1], row[2]))
    taken: dict[str, str] = {}      # collar tag -> run tag
    landed: dict[str, str] = {}     # run tag -> collar tag
    contested: dict[str, list[str]] = {}
    for gap, tag, collar_tag in scored:
        if gap > COLLAR_REACH_M:
            break
        if tag in landed:
            continue
        if collar_tag in taken:
            contested.setdefault(collar_tag, [taken[collar_tag]]).append(tag)
            continue
        taken[collar_tag] = tag
        landed[tag] = collar_tag

    stranded = sorted(set(ends) - set(landed))
    spare = sorted(collar.port_tag for collar in collars if collar.port_tag not in taken)
    if contested:
        worst = sorted(contested.items())[0]
        return [failed(
            cid, f"{obj.tag} ({obj.type_ref}): collar {worst[0]} is claimed by "
                 f"{len(worst[1])} runs — {', '.join(sorted(worst[1]))}. A collar is one "
                 "hole and takes one pipe",
            (obj.tag, *sorted(worst[1])),
            fix="move one radial's end onto a free collar, or add a collar to the plenum's "
                "type in plan/mep_erv_types.py")]
    if stranded:
        return [failed(
            cid, f"{obj.tag} ({obj.type_ref}) dimensions {len(collars)} x {size} collars "
                 f"and {len(stranded)} run(s) end more than "
                 f"{COLLAR_REACH_M / _M_PER_IN:.0f}\" from any free one: "
                 f"{', '.join(stranded)}"
                 + (f" (free: {', '.join(spare)})" if spare else " (none free)"),
            (obj.tag, *stranded),
            fix="move the run's end onto a collar's own station — `haus route --run <tag>` "
                "terminates on an exact port — or add a collar to the plenum's type")]
    return [passed(
        cid, f"{obj.tag} ({obj.type_ref}): {len(landed)} of {len(collars)} x {size} "
             "collars used, each by one run"
             + (f"; spare {', '.join(spare)}" if spare else ", full")
             + "; graded by POSITION, not by count — this type dimensions its layout",
        (obj.tag,))]


def _gap(end, collar) -> float:
    (point, z) = end
    plan = max(abs(collar.x_m - point[0]), abs(collar.y_m - point[1]))
    return plan if z is None else max(plan, abs(collar.z_m - z))


def _reach(end, collars) -> float:
    return min((_gap(end, collar) for collar in collars), default=float("inf"))
