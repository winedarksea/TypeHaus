"""``_EdgeRun.host_ref`` names the thing the run trims — and nothing ever read it.

A fascia, a gutter, a drip edge and a cap flashing each carry a ``host_ref``: the deck,
roof, beam or fascia the run is fixed to. ``resolve/accessories.py`` builds every one of
them from its own ``path`` and ``top_elevation`` and never opens the field. So the tag can
name a retired element, or an element on the other side of the building, and the run still
draws, still bills, and still passes — the same decorative-reference failure
``integrity.reveal_alignment`` exists for, one element family over.

**Subject — a run that names a host.** Nine of catlin's 29 edge runs name none (the four
corner flashings, the five garage stem-zone strips) and are out of subject, not a gap: a
run with no host claims nothing to check.

**The obvious rule — "the run sits on its host's top" — FAILS three legitimate families,**
so it is not the rule:

* **A tilted beam.** ``BM-SG-BLW``/``BLC``/``BLE`` carry ``top_rise_end``, so their solids
  are swept, not prismatic, and the bounding box's ``z1_m`` is the HIGH end. A cap at
  its low end (``TR-SG-CAP-BLW``, removed 2026-09-16) sat 2.42" under the box top — a false
  FAIL against the box on a cap exactly where it belongs.
  An ``_EdgeRun`` has a single ``top_elevation`` and **cannot be raked**, so a cap on a
  tilted beam is a flat run against a sloping top and lands somewhere in that range by
  construction. Graded against the swept range, derived from the box top and the path's own
  z travel so no assumption is made about how the profile is oriented.
* **A roof host.** ``RF-HOUSE`` resolves to **no solid at all** — only a footprint and its
  eave/ridge elevations. And the runs on it are deliberately at different heights: the
  gutter hangs below the drip edge, which hangs below the eave. Plan only.
* **Another edge run.** ``TR-SG-GUTTER`` names ``TR-SG-FASCIA`` and is authored 3" below it
  ON PURPOSE — that is what a gutter does. Plan only, for the same reason.

**A ``FloorSystem`` host is UNKNOWN, and reporting it is the point.** ``FS-SG-DECK`` and
``FS-SG-PORCH`` resolve to no solid *and* to a zero-point outline, so there is nothing to
compare a run against in either plan or elevation. Silently skipping those three runs would
make this check quietly narrower than it reads; the honest answer is that the model cannot
say, and that is a real finding about the model either way.

**Plan tolerance is generous on purpose.** A gutter legitimately hangs 3.33" outboard of
the roof footprint and a drip edge 1.04", because that is where those parts go. The error
this catches is a run pointed at the wrong element, which is feet away, not inches.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CHECK_ID = "integrity.edge_run_host"

#: Every ``_EdgeRun`` subclass. Named rather than discovered so a new trim family is a
#: deliberate decision to cover; ``test_edge_run_host`` lints the list against the model
#: registry.
_RUN_KINDS = ("Fascia", "EaveSoffit", "Gutter", "Flashing", "GlazingTrim")

#: How far off its host's plan a run may sit. A gutter hangs 3.33" outboard of the roof it
#: drains and that is correct; a run naming the wrong element is not inches away.
_PLAN_TOLERANCE_M = 12.0 * M_PER_IN

#: Drafting slop on an elevation, far below the smallest real misattachment.
_Z_TOLERANCE_M = 1.0 * M_PER_IN


def _top_range(solid) -> tuple[float, float]:
    """The host's top surface, low end to high end.

    Derived from the bounding top and the sweep path's own z travel rather than from the
    profile: a swept solid's ``z1_m`` is its HIGH top, and the low top is that less however
    far the path climbs. A prismatic solid (no sweep, or a level one) collapses to a single
    value, so this stays a tight test where the host really is flat — it only opens up by
    exactly the amount the host is out of level.
    """
    sweep = getattr(solid, "sweep", None)
    path = getattr(sweep, "path", None) if sweep is not None else None
    if not path:
        return (solid.z1_m, solid.z1_m)
    zs = [point[2] for point in path if len(point) > 2]
    if not zs:
        return (solid.z1_m, solid.z1_m)
    return (solid.z1_m - (max(zs) - min(zs)), solid.z1_m)


def _plan_gap(path, boundary) -> float | None:
    """Furthest any vertex of ``path`` lies outside ``boundary``, or ``None`` if unusable."""
    if boundary is None or len(boundary) < 3:
        return None
    # Plain shapely, deliberately. ``resolve/overlay.py`` exists because GEOS 3.12 needs a
    # grid_size on UNION/DIFFERENCE/INTERSECTION; constructing a ring and measuring a
    # distance is neither, so there is no overlay predicate here to snap.
    shape = Polygon([(point[0], point[1]) for point in boundary])
    if shape.is_empty or not shape.is_valid:
        return None
    return max(Point(point.xy_m).distance(shape) for point in path)


@check(Tier.INTEGRITY, _CHECK_ID)
def edge_run_host(ctx: CheckContext) -> list[Finding]:
    model = ctx.model
    runs = [element
            for kind in _RUN_KINDS
            for element in model.plan.elements_of_kind(kind)
            if getattr(element, "host_ref", None)]
    if not runs:
        return [not_applicable(_CHECK_ID,
                               "no trim run in this building names a host, so there is no "
                               "reference here to have gone stale")]

    solids = {solid.tag: solid for solid in model.solids}
    roofs = {roof.tag: roof for roof in model.roofs}
    run_paths = {element.tag: element
                 for kind in _RUN_KINDS
                 for element in model.plan.elements_of_kind(kind)}

    findings: list[Finding] = []
    graded = 0
    for run in sorted(runs, key=lambda element: element.tag):
        host_tag = run.host_ref
        host = model.plan.by_tag(host_tag)
        if host is None:
            findings.append(failed(
                _CHECK_ID,
                f"{run.tag} is hosted on {host_tag}, which is not in this plan — the run "
                f"trims an element that does not exist",
                tags=(run.tag,),
                fix="point host_ref at a live tag, or drop it if the run trims nothing"))
            continue

        solid = solids.get(host_tag)
        if solid is not None:
            gap = _plan_gap(run.path, getattr(solid, "outline", None))
            low, high = _top_range(solid)
            top = run.top_elevation.meters
            if gap is not None and gap > _PLAN_TOLERANCE_M:
                findings.append(failed(
                    _CHECK_ID,
                    f"{run.tag} runs {gap / M_PER_IN:.1f}\" clear of {host_tag} in plan, "
                    f"the element it says it trims",
                    tags=(run.tag, host_tag),
                    fix="host_ref is read by nothing else, so it drifts silently — "
                        "re-point it at the element the path actually follows"))
                continue
            if not (low - _Z_TOLERANCE_M <= top <= high + _Z_TOLERANCE_M):
                where = (f"{low / M_PER_IN:.2f}\"" if low == high
                         else f"{low / M_PER_IN:.2f}\"-{high / M_PER_IN:.2f}\" "
                              f"(it is out of level)")
                findings.append(failed(
                    _CHECK_ID,
                    f"{run.tag} tops out at {top / M_PER_IN:.2f}\" but {host_tag}'s top "
                    f"is {where} — the run is not on the element it trims",
                    tags=(run.tag, host_tag),
                    fix="check top_elevation against the host's own top; an _EdgeRun has "
                        "one elevation and cannot be raked, so on a sloping host it must "
                        "land within the host's range"))
                continue
            graded += 1
            continue

        roof = roofs.get(host_tag)
        if roof is not None:
            # Plan only: a roof resolves to no solid, and the runs on it sit at three
            # deliberate heights below the eave.
            gap = _plan_gap(run.path, getattr(roof, "footprint", None))
            if gap is not None and gap > _PLAN_TOLERANCE_M:
                findings.append(failed(
                    _CHECK_ID,
                    f"{run.tag} runs {gap / M_PER_IN:.1f}\" clear of {host_tag}'s "
                    f"footprint, the roof it says it trims",
                    tags=(run.tag, host_tag),
                    fix="re-point host_ref at the roof the path actually follows"))
                continue
            graded += 1
            continue

        other = run_paths.get(host_tag)
        if other is not None and other.tag != run.tag:
            # Plan only, and for a stated reason: a gutter is authored below the fascia it
            # hangs on, so their elevations differ by design.
            near = min(
                min(abs(p.xy_m[0] - q.xy_m[0]) + abs(p.xy_m[1] - q.xy_m[1])
                    for q in other.path)
                for p in run.path)
            if near > _PLAN_TOLERANCE_M:
                findings.append(failed(
                    _CHECK_ID,
                    f"{run.tag} runs {near / M_PER_IN:.1f}\" clear of {host_tag}, the run "
                    f"it says it hangs on",
                    tags=(run.tag, host_tag),
                    fix="re-point host_ref at the run the path actually follows"))
                continue
            graded += 1
            continue

        findings.append(unknown(
            _CHECK_ID,
            f"{run.tag} is hosted on {host_tag}, which resolves to no solid and no plan "
            f"outline — there is nothing to compare the run against in either plan or "
            f"elevation, so the model cannot say whether the reference is still true",
            tags=(run.tag, host_tag),
            fix=("a FloorSystem carries no geometry of its own; give the host a resolved "
                 "outline, or host the run on the beam or deck edge it really follows")))

    if not findings:
        return [passed(_CHECK_ID,
                       f"every one of {graded} hosted trim run(s) follows the element it "
                       f"names, in plan and where the host has a top to compare against")]
    return findings
