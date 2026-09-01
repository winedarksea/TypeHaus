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

Three things legitimately terminate a run, and all three are earned from the model rather
than from a naming convention:

* **another duct**, meeting it in plan *and* in elevation. Plan alone is not enough and the
  first draft of this check proved it: a basement riser end "landed on" a second-storey run
  231" above it, because two runs on different floors share a plan point all the time. But
  the elevations must not be required to be *equal* either — a riser is a single plan point
  spanning a z range, and it joins a trunk somewhere along that span. So the test is that the
  end's elevation falls within the other run's own z extent at that vertex, widened by
  ``JOINT_TOLERANCE_M``.
* **a machine** — an air handler, a manifold, an ERV — whose footprint the end lands in.
* **a register**, but only one that already names this run in ``duct_ref``, and only within
  ``BOOT_REACH_M``. That is the boot: the flex tail and collar between the end of the hard
  duct and the grille in the ceiling. This house authors four of them at 24"-36"
  (``plan/mep_registers.py``), so they are the design, not a defect, and a check that called
  them orphans would be reporting the drawing rather than the building.

And one exempts it: an end **outdoors**, which is a hood — the same
``clear_face`` probe ``mep.erv_outdoor_terminals`` and ``code.M1502_dryer_exhaust`` use, and
a fact about geometry rather than about the tag.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.mep_soffit import segment_meets_box

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


def _meets_another_duct(ctx: CheckContext, duct, z: float | None,
                        point: tuple[float, float]) -> str | None:
    """Another run with a vertex at this plan point, at an elevation this end can reach.

    The z test is what separates a joint from a coincidence. Without it a basement end reads
    as connected to whatever second-storey run happens to cross the same plan point, which is
    how the ERV chase risers first passed this check while ending 231" below the run they
    were credited to. The comparison is against the other run's full z *extent* rather than
    the matched vertex alone, so a riser spanning a storey still meets the trunk it joins
    anywhere along its span.
    """
    for other in ctx.model.ducts:
        if other.tag == duct.tag:
            continue
        for vertex in other.path:
            if (abs(vertex[0] - point[0]) > JOINT_TOLERANCE_M
                    or abs(vertex[1] - point[1]) > JOINT_TOLERANCE_M):
                continue
            if z is None or not other.z_m:
                return other.tag
            low, high = min(other.z_m), max(other.z_m)
            if low - JOINT_TOLERANCE_M <= z <= high + JOINT_TOLERANCE_M:
                return other.tag
    return None


def _meets_equipment(ctx: CheckContext, point: tuple[float, float]) -> str | None:
    """Whether the end lands in a machine's footprint.

    ``segment_meets_box`` is the same Liang-Barsky clip ``mep_soffit.connected`` runs, given
    a degenerate segment — the end point against itself — so "the end is inside the case" is
    asked with the identical arithmetic that decides a duct is plumbed into a machine.
    """
    from shapely.geometry import Polygon

    for obj in ctx.model.canvas_objects:
        if not obj.footprint:
            continue
        x0, y0, x1, y1 = Polygon(obj.footprint).bounds
        box = ((x0 - JOINT_TOLERANCE_M, x1 + JOINT_TOLERANCE_M),
               (y0 - JOINT_TOLERANCE_M, y1 + JOINT_TOLERANCE_M))
        if segment_meets_box(point, point, box):
            return obj.tag
    return None


def _boot(ctx: CheckContext, duct, point: tuple[float, float]) -> str | None:
    """A register that names this run and is within a boot's reach of the end."""
    positions = {obj.tag: obj.position for obj in ctx.model.canvas_objects}
    for element in ctx.plan.all_elements():
        if element.element_kind != "Register" or element.duct_ref != duct.tag:
            continue
        at = positions.get(element.tag)
        if at is None:
            continue
        span = ((at[0] - point[0]) ** 2 + (at[1] - point[1]) ** 2) ** 0.5
        if span <= BOOT_REACH_M:
            return element.tag
    return None


@check(Tier.INTEGRITY, "mep.duct_connectivity")
def duct_connectivity(ctx: CheckContext) -> list[Finding]:
    """Every duct end lands on a duct, a machine, its own register's boot, or outdoors."""
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
                      or _meets_equipment(ctx, point)
                      or _boot(ctx, duct, point))
            if landed is not None:
                out.append(passed(
                    "mep.duct_connectivity",
                    f"duct {duct.tag} {label} lands on {landed}", (duct.tag,)))
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
                f"no register naming this run is within {BOOT_REACH_M / M_PER_IN:.0f}\", and "
                "it is not outdoors", (duct.tag,)))
    return out
