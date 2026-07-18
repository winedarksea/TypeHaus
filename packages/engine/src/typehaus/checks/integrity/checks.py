"""Integrity checks — the main focus (→ 12 §Checks). Deep model-truth guarantees."""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity


def _err(check_id: str, msg: str, tags: tuple[str, ...] = (), hint: str | None = None,
         result: Result = Result.FAIL) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=check_id, message=msg,
                   element_tags=tags, fix_hint=hint, result=result)


def _warn(check_id: str, msg: str, tags: tuple[str, ...] = (),
          result: Result = Result.FAIL) -> Finding:
    return Finding(severity=Severity.WARN, check_id=check_id, message=msg,
                   element_tags=tags, result=result)


@check(Tier.INTEGRITY, "integrity.tag_unique")
def tag_unique(ctx: CheckContext) -> list[Finding]:
    seen: dict[str, int] = {}
    for el in ctx.plan.all_elements():
        seen[el.tag] = seen.get(el.tag, 0) + 1
    return [
        _err("integrity.tag_unique", f"tag {tag!r} used {n} times", (tag,),
             "tags must be unique per plan")
        for tag, n in sorted(seen.items()) if n > 1
    ]


@check(Tier.INTEGRITY, "integrity.uid_unique")
def uid_unique(ctx: CheckContext) -> list[Finding]:
    seen: dict[str, int] = {}
    for el in ctx.plan.all_elements():
        if el.uid:
            seen[el.uid] = seen.get(el.uid, 0) + 1
    return [
        _err("integrity.uid_unique", f"uid {uid!r} collision (regenerate)", (uid,))
        for uid, n in sorted(seen.items()) if n > 1
    ]


@check(Tier.INTEGRITY, "integrity.wall_assembly")
def wall_assembly_resolves(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for el in ctx.plan.all_elements():
        if el.element_kind not in ("Wall", "FoundationWall"):
            continue
        if ctx.plan.library.resolve_assembly(el.assembly) is None:
            out.append(_err("integrity.wall_assembly",
                            f"wall {el.tag} references unknown assembly {el.assembly!r}",
                            (el.tag,), "define the assembly or fix the reference"))
    return out


@check(Tier.INTEGRITY, "integrity.assembly_layers")
def assembly_layer_sanity(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for asm in ctx.plan.library.assemblies:
        resolved = ctx.plan.library.resolve_assembly(asm.tag)
        if resolved is None:
            continue
        for layer in resolved.layers:
            if layer.thickness.meters <= 0:
                out.append(_err("integrity.assembly_layers",
                                f"assembly {asm.tag} layer {layer.name} has thickness <= 0",
                                (asm.tag,)))
        if resolved.structure_index() is None:
            out.append(_err("integrity.assembly_layers",
                            f"assembly {asm.tag} has no STRUCTURE layer", (asm.tag,)))
    return out


@check(Tier.INTEGRITY, "integrity.opening_fits")
def opening_fits_host(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.geometry import length, sub

    out: list[Finding] = []
    min_edge = 0.05  # meters
    for op in ctx.model.openings:
        rw = ctx.model.wall(op.host_wall)
        if rw is None:
            continue
        axis_len = length(sub(rw.axis[1], rw.axis[0]))
        left = op.center_along_m - op.width_m / 2
        right = op.center_along_m + op.width_m / 2
        if left < min_edge or right > axis_len - min_edge:
            out.append(_err("integrity.opening_fits",
                            f"opening {op.tag} does not fit host {op.host_wall} "
                            f"(needs >= {min_edge*39.37:.1f}\" edge distance)", (op.tag,)))
    return out


@check(Tier.INTEGRITY, "integrity.space_zero_gap")
def space_zero_gap(ctx: CheckContext) -> list[Finding]:
    """Every Room's clear-face polygon must be a real closed polygon (#41)."""
    out: list[Finding] = []
    for room in ctx.model.rooms:
        if len(room.clear_face) < 3 or room.area_m2 <= 0:
            out.append(_err("integrity.space_zero_gap",
                            f"room {room.tag} has no valid clear-face polygon", (room.tag,)))
    return out


@check(Tier.INTEGRITY, "integrity.condition_coverage")
def condition_coverage(ctx: CheckContext) -> list[Finding]:
    """Every derived boundary condition should be bound to a Transition or warn-flagged
    (warn-tier during design; hard-gated only in /permit-check, → 11b risk 8)."""
    out: list[Finding] = []
    transitions = ctx.plan.library.transitions
    for cond in ctx.model.conditions:
        covered = any(_matches(t.condition_pattern, cond.key) for t in transitions)
        if not covered:
            out.append(_warn("integrity.condition_coverage",
                             f"boundary condition {cond.key} has no Transition binding",
                             cond.element_tags))
    return out


def _matches(pattern: str, key: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(key, pattern)
