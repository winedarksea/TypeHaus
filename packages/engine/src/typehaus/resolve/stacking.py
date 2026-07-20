"""Vertical stacking pass (#43): derive wall-line stacks + storey-stack conditions (→ 11)."""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ConditionKind
from typehaus.quantities import ft, inch
from typehaus.resolve.geometry import add, length, scale, sub, unit
from typehaus.resolve.model import BoundaryCondition, ResolvedModel, ResolvedWall, StackEdge

_TOL = inch(0.5).meters  # datum-face alignment tolerance
_MIN_OVERLAP = ft(2).meters


def _total_thickness(rw: ResolvedWall) -> float:
    return rw.thickness_m


def _axis_match(lower: ResolvedWall, upper: ResolvedWall) -> float:
    """Return overlap length in meters if the two wall axes are collinear, else 0."""
    (a0, a1), (b0, b1) = lower.axis, upper.axis
    da, db = unit(sub(a1, a0)), unit(sub(b1, b0))
    # parallel (allowing reversal)?
    cross = da[0] * db[1] - da[1] * db[0]
    if abs(cross) > 1e-3:
        return 0.0
    # perpendicular distance of b0 from line a
    n = (-da[1], da[0])
    dist = abs(sub(b0, a0)[0] * n[0] + sub(b0, a0)[1] * n[1])
    if dist > _TOL:
        return 0.0
    # project both walls onto axis a and measure overlap
    def proj(p: tuple[float, float]) -> float:
        v = sub(p, a0)
        return v[0] * da[0] + v[1] * da[1]

    la0, la1 = 0.0, length(sub(a1, a0))
    lb0, lb1 = sorted((proj(b0), proj(b1)))
    return max(0.0, min(la1, lb1) - max(la0, lb0))


def resolve_stacking(model: ResolvedModel) -> list[Finding]:
    """Derive stack edges between adjacent storeys and emit boundary conditions."""
    plan = model.plan
    ordered = sorted(plan.storeys, key=lambda s: s.elevation.meters)
    findings: list[Finding] = []
    walls_by_storey: dict[str, list[ResolvedWall]] = {}
    for rw in model.walls:
        walls_by_storey.setdefault(rw.storey, []).append(rw)

    # For each wall, stack against the first storey above that carries a collinear
    # wall. Interleaved storeys of *other* freestanding structures (the catlin garage
    # storey sits between main and second) must not break a structure's own stack.
    for index, lower_s in enumerate(ordered):
        lowers = walls_by_storey.get(lower_s.tag, [])
        for lw in lowers:
            candidates: list[tuple[ResolvedWall, float]] = []
            for upper_s in ordered[index + 1:]:
                uppers = walls_by_storey.get(upper_s.tag, [])
                candidates = [
                    (uw, ov) for uw in uppers
                    if (ov := _axis_match(lw, uw)) >= _MIN_OVERLAP
                ]
                if candidates:
                    break
            if not candidates:
                continue
            if len(candidates) > 1:
                # ambiguous only if authored tiebreaker absent
                authored = plan.by_tag(lw.tag)
                stacks_on = getattr(authored, "stacks_on", None)
                chosen = next((c for c in candidates
                               if getattr(plan.by_tag(c[0].tag), "stacks_on", None) == lw.tag),
                              None)
                if chosen is None and stacks_on is None:
                    findings.append(
                        Finding(
                            severity=Severity.ERROR,
                            check_id="integrity.stack_ambiguous",
                            message=f"ambiguous vertical stack over {lw.tag}",
                            element_tags=(lw.tag, *(c[0].tag for c in candidates)),
                            fix_hint="set Wall.stacks_on on the upper wall to disambiguate",
                            result=Result.FAIL,
                        )
                    )
                    continue
                candidates = [chosen] if chosen else candidates[:1]
            uw, ov = candidates[0]
            width_change = abs(_total_thickness(lw) - _total_thickness(uw)) > _TOL
            model.stack_edges.append(
                StackEdge(lower_wall=lw.tag, upper_wall=uw.tag, overlap_m=ov,
                          width_change=width_change)
            )
            asms = tuple(sorted({lw.assembly, uw.assembly}))
            model.conditions.append(
                BoundaryCondition(
                    kind=ConditionKind.STOREY_STACK, assemblies=asms, detail="rim",
                    element_tags=(lw.tag, uw.tag),
                    key=f"storey_stack:rim:{'|'.join(asms)}",
                )
            )
            if lw.is_foundation and not uw.is_foundation:
                model.conditions.append(
                    BoundaryCondition(
                        kind=ConditionKind.WALL_FOUNDATION, assemblies=asms,
                        detail="foundation-to-framed", element_tags=(lw.tag, uw.tag),
                        key=f"wall_foundation:{'|'.join(asms)}",
                    )
                )
            if width_change:
                model.conditions.append(
                    BoundaryCondition(
                        kind=ConditionKind.STACK_WIDTH_CHANGE, assemblies=asms,
                        detail="width-change", element_tags=(lw.tag, uw.tag),
                        key=f"stack_width_change:{'|'.join(asms)}",
                    )
                )
    return findings
