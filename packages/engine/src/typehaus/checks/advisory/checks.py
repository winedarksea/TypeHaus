"""Advisory checks — design intelligence, warn-only, reasoning shown (→ 12 §checks/advisory).

Opinions with arithmetic behind them, never authority. Each finding states *why* and is
individually suppressible in preferences.toml.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity


def _warn(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


@check(Tier.ADVISORY, "advisory.habitable_window")
def habitable_room_window(ctx: CheckContext) -> list[Finding]:
    """Habitable rooms should have an exterior window (natural light, R303)."""
    from typehaus.model.enums import Occupancy

    habitable = {Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.KITCHEN,
                 Occupancy.DINING, Occupancy.OFFICE}
    out: list[Finding] = []
    has_window = any(not op.is_door for op in ctx.model.openings)
    for room in (e for e in ctx.plan.all_elements() if e.element_kind == "Room"):
        if room.occupancy in habitable and not has_window:
            out.append(_warn("advisory.habitable_window",
                             f"habitable room {room.tag} appears to have no window — "
                             "consider natural light/ventilation", (room.tag,)))
    return out


@check(Tier.ADVISORY, "advisory.window_size_variety")
def window_size_variety(ctx: CheckContext) -> list[Finding]:
    """Fewer unique window sizes = cheaper ordering (reported as a fact with a histogram)."""
    sizes: dict[tuple[float, float], int] = {}
    for op in ctx.model.openings:
        if not op.is_door:
            key = (round(op.width_m, 3), round(op.height_m, 3))
            sizes[key] = sizes.get(key, 0) + 1
    if len(sizes) <= 1:
        return []
    hist = ", ".join(f"{w*39.37:.0f}x{h*39.37:.0f}\"×{n}" for (w, h), n in sizes.items())
    return [_warn("advisory.window_size_variety",
                  f"{len(sizes)} unique window sizes — fewer eases ordering ({hist})")]


@check(Tier.ADVISORY, "advisory.control_continuity")
def control_layer_continuity(ctx: CheckContext) -> list[Finding]:
    """Warn where a tagged control layer dead-ends at a condition whose transition does
    not declare continuity (walks junctions and stack edges, → 11b)."""
    out: list[Finding] = []
    transitions = ctx.plan.library.transitions
    for cond in ctx.model.conditions:
        if cond.kind.value not in ("storey_stack", "assembly_change"):
            continue
        declared = any(
            _matches(t.condition_pattern, cond.key) and t.continuity for t in transitions
        )
        if not declared:
            out.append(_warn("advisory.control_continuity",
                             f"control-layer continuity not declared across {cond.key}",
                             cond.element_tags))
    return out


def _matches(pattern: str, key: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(key, pattern)
