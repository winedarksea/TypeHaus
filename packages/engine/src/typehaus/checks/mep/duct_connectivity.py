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
* **a register** at the end itself, but only one that already names this run in ``duct_ref``,
  and only within
  ``BOOT_REACH_M``. That is the boot: the flex tail and collar between the end of the hard
  duct and the grille in the ceiling. This house authors four of them at 24"-36"
  (``plan/mep_registers.py``), so they are the design, not a defect, and a check that called
  them orphans would be reporting the drawing rather than the building.

* **its own take-off**, when the end is the cap past the last boot on a served trunk. A trunk
  that feeds grilles along its length ends a few inches past the last one and is capped —
  that is a duct end that lands on nothing and is not a defect. Earned from ``duct_ref``: the
  run's *final segment* must carry a register naming it within ``BOOT_REACH_M``. Restricted
  to the final segment on purpose — "this run has a register somewhere" would excuse a riser
  dangling in a chase at the other end of the house.
And one exempts it: an end **outdoors**, which is a hood — the same
``clear_face`` probe ``mep.erv_outdoor_terminals`` and ``code.M1502_dryer_exhaust`` use, and
a fact about geometry rather than about the tag.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.mep_soffit import segment_meets_box

if TYPE_CHECKING:
    from typehaus.resolve.model import ResolvedDuct

#: How far apart two duct vertices may be in plan and still be one joint. A duct is drawn on
#: its centreline and authored to the inch, so this is fabrication slop, not a routing
#: allowance: 3" is under the radius of every trunk in this house, which means two runs this
#: close in plan are inside one another's section and a fitting genuinely joins them.
JOINT_TOLERANCE_M = inch(3).meters

#: How far a register may sit from the end of the run it names and still be its boot. The
#: flex tail from a hard-duct take-off to a ceiling grille is a real, ordinary piece of the
#: system — this house authors REG-S-HP-BED1/2/3 at 36" and REG-S-HP-STAIR at 24" and says so
#: in ``plan/mep_registers.py``. 36" is that authored maximum, not a round number: past it
#: the "boot" is a duct run that should be drawn as one.
BOOT_REACH_M = inch(36).meters


def _ends_outdoors(ctx: CheckContext, point: tuple[float, float]) -> bool:
    """Whether a plan point lands outside every resolved room's clear face."""
    from shapely.geometry import Point, Polygon

    probe = Point(point)
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3 and Polygon(room.clear_face).covers(probe):
            return False
    return True


def _plan_distance_to_segment(point: tuple[float, float], a: tuple[float, float],
                             b: tuple[float, float]) -> tuple[float, float]:
    """``(distance, t)`` from a plan point to the segment ``a``->``b``, ``t`` in [0, 1].

    A degenerate segment — the two ends of a riser, which share a plan point — returns the
    distance to that point at ``t = 0``, which is what a riser needs: its whole z span is
    the segment's, and ``t`` has nothing to say about where along it a branch lands.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0.0 else max(0.0, min(1.0, ((point[0] - a[0]) * dx
                                                        + (point[1] - a[1]) * dy) / length_sq))
    near = (a[0] + t * dx, a[1] + t * dy)
    return ((point[0] - near[0]) ** 2 + (point[1] - near[1]) ** 2) ** 0.5, t


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
        for index in range(len(other.path) - 1):
            span, _ = _plan_distance_to_segment(point, other.path[index], other.path[index + 1])
            if span > JOINT_TOLERANCE_M:
                continue
            if z is None or len(other.z_m) <= index + 1:
                return other.tag
            low = min(other.z_m[index], other.z_m[index + 1])
            high = max(other.z_m[index], other.z_m[index + 1])
            if low - JOINT_TOLERANCE_M <= z <= high + JOINT_TOLERANCE_M:
                return other.tag
    return None


def _case_height(ctx: CheckContext, type_ref: str | None) -> float | None:
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


def _meets_equipment(ctx: CheckContext, z: float | None,
                     point: tuple[float, float]) -> str | None:
    """Whether the end lands in a machine's footprint, at the height of its case.

    ``segment_meets_box`` is the same Liang-Barsky clip ``mep_soffit.connected`` runs, given
    a degenerate segment — the end point against itself — so "the end is inside the case" is
    asked with the identical arithmetic that decides a duct is plumbed into a machine. The
    elevation band is this check's own: a soffit clash is already confined to one box, and a
    duct end is not.
    """
    from shapely.geometry import Polygon

    for obj in ctx.model.canvas_objects:
        if not obj.footprint:
            continue
        x0, y0, x1, y1 = Polygon(obj.footprint).bounds
        box = ((x0 - JOINT_TOLERANCE_M, x1 + JOINT_TOLERANCE_M),
               (y0 - JOINT_TOLERANCE_M, y1 + JOINT_TOLERANCE_M))
        if not segment_meets_box(point, point, box):
            continue
        height = _case_height(ctx, obj.type_ref)
        if z is None or height is None:
            return obj.tag
        # ``z_m`` is the object's base — a ceiling-hung ERV at a 6'-0" mount resolves to the
        # bottom of its case and stands 21.6" up from there — so the band runs upward.
        if obj.z_m - JOINT_TOLERANCE_M <= z <= obj.z_m + height + JOINT_TOLERANCE_M:
            return obj.tag
    return None


def _takeoffs(ctx: CheckContext, duct: ResolvedDuct) -> list[tuple[str, tuple[float, float]]]:
    """``(tag, plan position)`` for every register naming this run in ``duct_ref``."""
    positions = {obj.tag: obj.position for obj in ctx.model.canvas_objects}
    out: list[tuple[str, tuple[float, float]]] = []
    for element in ctx.plan.all_elements():
        if element.element_kind != "Register" or element.duct_ref != duct.tag:
            continue
        at = positions.get(element.tag)
        if at is not None:
            out.append((element.tag, at))
    return out


def _boot(ctx: CheckContext, duct: ResolvedDuct,
          point: tuple[float, float]) -> str | None:
    """A register that names this run and is within a boot's reach of the end."""
    for tag, at in _takeoffs(ctx, duct):
        span = ((at[0] - point[0]) ** 2 + (at[1] - point[1]) ** 2) ** 0.5
        if span <= BOOT_REACH_M:
            return tag
    return None


def _capped_past_a_takeoff(ctx: CheckContext, duct: ResolvedDuct,
                           point: tuple[float, float]) -> str | None:
    """A cap on a served trunk: the run's final leg carries a boot, and then it stops.

    DU-S-HP-SUP is the case. It runs the hall soffit past REG-S-HP-BED1/2/3, each 36" east
    through the bedroom wall, and then ends — a capped trunk, which is how a trunk ends. The
    end itself lands on nothing and never will, so ``_boot`` cannot speak for it; what makes
    it a cap rather than an orphan is that the leg it ends is the leg a grille comes off.

    The leg, not the run: a register anywhere on a run would excuse both of its ends, and the
    ends this check exists to catch — a riser dangling in a chase — are at the far end of a
    run whose other end is squarely in a manifold.
    """
    if len(duct.path) < 2:
        return None
    leg = ((duct.path[-2], duct.path[-1]) if point == duct.path[-1]
           else (duct.path[0], duct.path[1]))
    for tag, at in _takeoffs(ctx, duct):
        span, _ = _plan_distance_to_segment(at, leg[0], leg[1])
        if span <= BOOT_REACH_M:
            return tag
    return None


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
        z_by_end = {"start": duct.z_m[0] if duct.z_m else None,
                    "end": duct.z_m[-1] if duct.z_m else None}
        for point, label in ((duct.path[0], "start"), (duct.path[-1], "end")):
            z = z_by_end[label]
            landed = (_meets_another_duct(ctx, duct, z, point)
                      or _meets_equipment(ctx, z, point)
                      or _boot(ctx, duct, point))
            if landed is not None:
                out.append(passed(
                    "mep.duct_connectivity",
                    f"duct {duct.tag} {label} lands on {landed}", (duct.tag,)))
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
                f"no register naming this run is within {BOOT_REACH_M / M_PER_IN:.0f}\" of it "
                "or of the leg it ends, and "
                "it is not outdoors", (duct.tag,)))
    return out
