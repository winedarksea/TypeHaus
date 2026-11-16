"""Does every duct run actually land on something at both ends?

A duct that stops in mid-air is the one HVAC defect a plan reader cannot see. Every other
duct property is visible — a run is too long, too small, in the wrong bay, over the roof —
but a run whose end coincides with nothing draws exactly like a run whose end coincides with
a trunk. On a plan sheet the two are the same line.

The predicate this needs already existed, and was being used the other way round.
``resolve/mep_soffit.py`` asks "is this duct plumbed into that machine?" in order to
*suppress* a soffit clash: two things overlapping in one box are fine when one runs into the
other. That is this same question with the sign flipped — here a connection is what must be
present, there it is what excuses an overlap — so the geometry is imported rather than
re-derived (``connected`` / ``segment_meets_box``), and the two can never drift apart about
what "connected" means.

Four things legitimately terminate a run, and all four are earned from the model rather
than from a naming convention:

* **another duct**, meeting it in plan *and* in elevation. Plan alone is not enough and the
  first draft of this check proved it: a basement riser end "landed on" a second-storey run
  231" above it, because two runs on different floors share a plan point all the time. But
  the elevations must not be required to be *equal* either — a riser is a single plan point
  spanning a z range, and it joins a trunk somewhere along that span. So the test is that the
  end's elevation falls within the z range of the other run's *segment* it lands on, widened
  by ``JOINT_TOLERANCE_M``. Segment and not vertex: a branch tees into the side of a trunk,
  which is a point along a leg and almost never one of its corners. DU-S-HP-SUITE is that
  tee — it leaves DU-S-HP-SUP 118" from either end of the trunk's only segment — and a
  vertex-only test called it an orphan while crediting it to a register 39" away.
* **a machine** — an air handler, a manifold, an ERV — whose footprint the end lands in *and*
  whose case the end is inside vertically. The same elevation argument as above, and the same
  failure without it: with a plan-only footprint test DU-ERV-RISER-SUP's basement end "landed
  on" EQ-M-ERV-HOOD-OA 67" above it and DU-S-HP-SUP's capped end "landed on" the fridge, 220"
  below. The case runs from the object's resolved ``z_m`` (its base) up by its type's
  ``height``; a type that states no height falls back to the plan test alone.
* **a register** whose boot ENDS this run (``resolve/terminal_joints``, decision #136):
  a straight or 90 end boot behind the grille, read in 3D from the face the register
  resolves. No plan reach: a run that passes through a grille, or stops short of it,
  earns nothing here (``mep.register_reach`` FAILs the register). A round run's ceiling
  COLLAR earns no reach either: the run must end on its top, arriving from above
  (``resolve/terminal_drops``), and a collar no run end reaches is mid-run.

* **a cap**, when the end is the stub past the last take-off on a served trunk: a side
  boot (a grille on the trunk's flank) or a branch taking off the end leg near the end
  (``resolve/duct_terminations.capped_by``). A trunk ends a few inches past its last grille
  and is capped; that end lands on nothing and is not a defect. Restricted to the end leg
  on purpose: "this run has a register somewhere" would excuse a riser dangling in a chase
  at the other end of the house.
And one exempts it: an end **outdoors**, which is a hood — the same
axis-cell probe ``mep.erv_outdoor_terminals`` and ``code.M1502_dryer_exhaust`` use, and
a fact about geometry rather than about the tag.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check, shared
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_soffit import (
    DUCT_JOINT_TOLERANCE_M,
    end_joins,
    segment_meets_box,
)
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

if TYPE_CHECKING:
    from typehaus.resolve.model import ResolvedDuct

#: The joint tolerance, owned by ``resolve/mep_soffit`` so that the check that *requires* a
#: joint and the occupancy checks that *excuse* one share a single definition of it. Kept
#: under the local name every message in this module formats.
JOINT_TOLERANCE_M = DUCT_JOINT_TOLERANCE_M

def _ends_outdoors(ctx: CheckContext, point: tuple[float, float]) -> bool:
    """Whether a plan point lands outside every resolved room's clear face."""
    from shapely.geometry import Point

    probe = Point(point)
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3 and axis_polygon(room).covers(probe):
            return False
    return True


def _meets_another_duct(ctx: CheckContext, duct: ResolvedDuct, z: float | None,
                        point: tuple[float, float]) -> str | None:
    """Another run passing this plan point, at an elevation this end can reach.

    The z test is what separates a joint from a coincidence. Without it a basement end reads
    as connected to whatever second-storey run happens to cross the same plan point, which is
    how the ERV chase risers first passed this check while ending 231" below the run they
    were credited to. The comparison is against the matched *segment's* z range rather than
    one vertex's elevation, so a riser spanning a storey still meets the trunk it joins
    anywhere along its span.
    """
    for other in ctx.model.ducts:
        if other.tag == duct.tag or len(other.path) < 2:
            continue
        if end_joins(duct, point, z, other):
            return other.tag
    return None


def case_height(ctx: CheckContext, type_ref: str | None) -> float | None:
    """The height of a placeable's type, in metres, across every type collection.

    ``FurnitureType.height`` is required, so this is None only for an object that names no
    type at all — and there the check has nothing to say about elevation and falls back to
    the plan test, rather than inventing a case depth and failing a real joint on it.
    """
    if not type_ref:
        return None
    library = ctx.plan.library
    for collection in ("equipment_types", "register_types", "appliance_types",
                       "fixture_types", "furniture_types", "electrical_device_types"):
        for candidate in getattr(library, collection, ()):
            if candidate.tag == type_ref:
                height = getattr(candidate, "height", None)
                return None if height is None else height.meters
    return None


def equipment_at_end(ctx: CheckContext, z: float | None,
                     point: tuple[float, float]) -> str | None:
    """Whether the end lands in a machine's footprint, at the height of its case.

    ``segment_meets_box`` is the same Liang-Barsky clip ``mep_soffit.connected`` runs, given
    a degenerate segment — the end point against itself — so "the end is inside the case" is
    asked with the identical arithmetic that decides a duct is plumbed into a machine. The
    elevation band is this check's own: a soffit clash is already confined to one box, and a
    duct end is not.

    Public — and named for what it *returns*, the machine's tag, rather than for the boolean
    the connectivity walk uses it as — because ``mep.erv_static_budget`` and
    ``mep.erv_manifold_ports`` both need to know which plenum a run lands in, and a second
    implementation of "lands in" would be a second answer to a question this module settles.
    """
    from shapely.geometry import Polygon

    # Filled lazily, so the first hit still returns early; kept for one check run.
    bounds: dict = shared(ctx, "duct_connectivity.footprint_bounds", dict)
    for obj in ctx.model.canvas_objects:
        if not obj.footprint:
            continue
        if id(obj) not in bounds:
            bounds[id(obj)] = Polygon(obj.footprint).bounds
        x0, y0, x1, y1 = bounds[id(obj)]
        box = ((x0 - JOINT_TOLERANCE_M, x1 + JOINT_TOLERANCE_M),
               (y0 - JOINT_TOLERANCE_M, y1 + JOINT_TOLERANCE_M))
        if not segment_meets_box(point, point, box):
            continue
        height = case_height(ctx, obj.type_ref)
        if z is None or height is None:
            return obj.tag
        # ``z_m`` is the object's base — a ceiling-hung ERV at a 6'-0" mount resolves to the
        # bottom of its case and stands 21.6" up from there — so the band runs upward.
        if obj.z_m - JOINT_TOLERANCE_M <= z <= obj.z_m + height + JOINT_TOLERANCE_M:
            return obj.tag
    return None


def _end_index(duct: ResolvedDuct, point: tuple[float, float]) -> int:
    return 0 if tuple(point) == tuple(duct.path[0]) else len(duct.path) - 1


def _boot(ctx: CheckContext, duct: ResolvedDuct,
          point: tuple[float, float]) -> str | None:
    """A register whose end boot (straight or 90) terminates this run at ``point``."""
    from typehaus.checks.mep.register_reach import joints
    from typehaus.resolve.terminal_joints import END

    index = _end_index(duct, point)
    for tag, joint in joints(ctx).items():
        if joint.run == duct.tag and joint.kind == END and joint.end_index == index:
            return tag
    return None


def _capped_past_a_takeoff(ctx: CheckContext, duct: ResolvedDuct,
                           point: tuple[float, float]) -> str | None:
    """A cap on a served trunk: a side boot or a branch on the end leg, then it stops.

    The leg, not the run: a register anywhere on a run would excuse both of its ends, and the
    ends this check exists to catch (a riser dangling in a chase) are at the far end of a
    run whose other end is squarely in a manifold.
    """
    from typehaus.checks.mep.register_reach import joints
    from typehaus.resolve.duct_terminations import capped_by

    caps = shared(ctx, "duct_connectivity.capped_by",
                  lambda: capped_by(ctx.model, joints(ctx)))
    return caps.get((duct.tag, _end_index(duct, point)))


def _collars(ctx: CheckContext, duct: ResolvedDuct) -> list:
    """The ceiling necks naming this run; each takes a run end from above."""
    from typehaus.resolve.terminal_drops import collars_by_run, engaged

    return engaged(duct, shared(ctx, "duct_connectivity.collars",
                                lambda: collars_by_run(ctx.model)).get(duct.tag, []))


def _collar_tags(ctx: CheckContext, duct: ResolvedDuct) -> set[str]:
    return {tag for tag, _ in _collars(ctx, duct)}


def _collar_end(ctx: CheckContext, duct: ResolvedDuct,
                at_end: bool) -> tuple[str, str | None] | None:
    """``(register, problem or None)`` for the ceiling collar whose drop joint is this end."""
    from typehaus.checks.mep.register_reach import joints
    from typehaus.resolve.terminal_joints import DROP

    index = len(duct.path) - 1 if at_end else 0
    for tag, joint in joints(ctx).items():
        if joint.run == duct.tag and joint.kind == DROP and joint.end_index == index:
            return tag, joint.problem
    return None


def _mid_run_collars(ctx: CheckContext, duct: ResolvedDuct,
                     graded: set[str]) -> list[Finding]:
    """A ceiling collar no end of its run was graded against (none near, the near end joins
    a duct, or another collar is nearer it): the collar cannot tee off a trunk."""
    out = []
    for tag, _ in _collars(ctx, duct):
        if tag not in graded:
            out.append(failed("mep.duct_connectivity",
                              f"{tag} is mid-run on {duct.tag}; a ceiling collar takes a run "
                              "end or a tee branch", (duct.tag, tag)))
    return out


@check(Tier.INTEGRITY, "mep.duct_connectivity")
def duct_connectivity(ctx: CheckContext) -> list[Finding]:
    """Every end lands on a duct, a machine, a boot, a cap past its own take-off, or outdoors."""
    runs = [duct for duct in ctx.model.ducts if len(duct.path) >= 2]
    if not runs:
        # Earned, not assumed: a house with no resolved duct runs has no ends to orphan.
        return [not_applicable(
            "mep.duct_connectivity",
            "no duct runs resolve in this model, so no run can end on nothing", ())]

    out: list[Finding] = []
    for duct in runs:
        graded: set[str] = set()
        z_by_end = {"start": duct.z_m[0] if duct.z_m else None,
                    "end": duct.z_m[-1] if duct.z_m else None}
        for point, label in ((duct.path[0], "start"), (duct.path[-1], "end")):
            z = z_by_end[label]
            authored = ctx.plan.by_tag(duct.tag)
            terminal_ref = getattr(authored, "end_terminal_ref", None)
            if label == "end" and terminal_ref is not None:
                from typehaus.resolve.terminal_connections import inlet_connection_error

                problem = inlet_connection_error(ctx.model, terminal_ref)
                if problem:
                    out.append(failed("mep.duct_connectivity",
                                      f"duct {duct.tag} end: {problem}", (duct.tag, terminal_ref)))
                else:
                    out.append(passed("mep.duct_connectivity",
                                      f"duct {duct.tag} end matches "
                                      f"{terminal_ref}'s dimensioned inlet",
                                      (duct.tag, terminal_ref)))
                continue
            joined = _meets_another_duct(ctx, duct, z, point)
            # Before the case test: a collar's own face is a "case" an inch deep.
            collar = None if joined else _collar_end(ctx, duct, label == "end")
            if collar is not None:
                tag, problem = collar
                graded.add(tag)
                out.append(failed("mep.duct_connectivity", f"duct {duct.tag} {label} {problem}",
                                  (duct.tag, tag)) if problem else passed(
                    "mep.duct_connectivity",
                    f"duct {duct.tag} {label} drops onto {tag}'s ceiling collar", (duct.tag,)))
                continue
            landed = joined or equipment_at_end(ctx, z, point) or _boot(ctx, duct, point)
            mismatch = _collar_mismatch(ctx, duct, landed) if landed is not None else None
            if mismatch is not None:
                out.append(failed("mep.duct_connectivity", f"duct {duct.tag} {label} lands "
                                  f"on {landed}, {mismatch}", (duct.tag, landed),
                                  fix="match the run to the collar, or author the "
                                      "transition as its own run"))
                continue
            if landed is not None:
                out.append(passed(
                    "mep.duct_connectivity",
                    f"duct {duct.tag} {label} lands on {landed}"
                    + _port_note(ctx, duct, point, z, landed), (duct.tag,)))
                continue
            capped = _capped_past_a_takeoff(ctx, duct, point)
            if capped is not None:
                out.append(passed(
                    "mep.duct_connectivity",
                    f"duct {duct.tag} {label} is the cap past {capped}'s take-off — a served "
                    "trunk ends, it does not land", (duct.tag,)))
                continue
            if _ends_outdoors(ctx, point):
                out.append(passed(
                    "mep.duct_connectivity",
                    f"duct {duct.tag} {label} terminates outdoors — a hood, not an orphan",
                    (duct.tag,)))
                continue
            out.append(failed(
                "mep.duct_connectivity",
                f"duct {duct.tag} {label} at "
                f"({point[0] / M_PER_IN / 12:.2f}', {point[1] / M_PER_IN / 12:.2f}') lands on "
                "nothing: no duct meets it within "
                f"{JOINT_TOLERANCE_M / M_PER_IN:.0f}\", no equipment footprint contains it, "
                "no register boot ends it, no side boot or branch caps its end leg, and "
                "it is not outdoors", (duct.tag,)))
        out.extend(_mid_run_collars(ctx, duct, graded))
    return out


def _collar_mismatch(ctx: CheckContext, duct: ResolvedDuct, landed: str) -> str | None:
    """Why a round run cannot fit a ONE-collar machine (a hood), or None.

    A single-collar type states its spigot in ``port_diameter``; an 8" leg on a 6" hood
    collar connects to nothing an installer can buy. Multi-port plenums take a larger trunk
    collar beside their branch collars, so only the one-collar case is graded here.
    """
    if duct.diameter_m is None:
        return None
    obj = next((o for o in ctx.model.canvas_objects if o.tag == landed), None)
    if obj is None or not obj.type_ref:
        return None
    product = next((t for t in getattr(ctx.plan.library, "equipment_types", ())
                    if t.tag == obj.type_ref), None)
    port = getattr(product, "port_diameter", None)
    # A dimensioned collar marks a trunk-and-branch plenum, whose inlet is another size.
    if product is None or product.duct_ports != 1 or port is None or product.collars():
        return None
    if abs(port.meters - duct.diameter_m) <= 1e-4:
        return None
    return (f"a {duct.diameter_m / M_PER_IN:.0f}\" run on its "
            f"{port.meters / M_PER_IN:.0f}\" collar")


def _port_note(ctx: CheckContext, duct: ResolvedDuct, point: tuple[float, float],
               z: float | None, landed: str) -> str:
    """How exact this landing is, when the machine states a DIMENSIONED port.

    **Reporting, not a second verdict.** ``mep.equipment_port_service`` already FAILs a
    dimensioned port with nothing on it, and a duplicate FAIL here would be the same defect
    counted twice. What this adds is the distinction that check is organised the other way
    round to see: *this duct end*, landing on the spigot or merely inside the case. An end
    a foot from the collar passes connectivity either way — it is connected to that machine
    — and an installer still has to know which of the two it is.

    Silent where the machine states no exact port, which today is every machine in catlin:
    a datasheet that gives a face has nothing to be near or far from.
    """
    from typehaus.resolve.mep_ports import placed_ports

    system = duct.system.value if hasattr(duct.system, "value") else str(duct.system)
    exact = [p for p in placed_ports(ctx.model)
             if p.exact and p.equipment_tag == landed
             and p.duct_system in (None, system)]
    if not exact:
        return ""
    near = min(exact, key=lambda p: max(abs(p.x_m - point[0]), abs(p.y_m - point[1]))
               + (0.0 if z is None else abs(p.z_m - z)))
    off = max(abs(near.x_m - point[0]), abs(near.y_m - point[1]),
              0.0 if z is None else abs(near.z_m - z))
    if off <= JOINT_TOLERANCE_M:
        return f" — on its dimensioned port {near.port_tag}, an exact connection"
    return (f" — but {off / M_PER_IN:.1f}\" off its dimensioned port {near.port_tag}: "
            "connected to the machine, not to the spigot")
