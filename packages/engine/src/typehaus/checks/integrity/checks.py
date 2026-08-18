"""Integrity checks — the main focus (→ 12 §Checks). Deep model-truth guarantees."""

from __future__ import annotations

from collections.abc import Sequence

from typehaus.checks._authoring import advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Layer, LayerExtent
from typehaus.model.enums import LayerDatum
from typehaus.model.patterns import matches as _matches


def _err(check_id: str, msg: str, tags: tuple[str, ...] = (), hint: str | None = None,
         result: Result = Result.FAIL) -> Finding:
    return advisory(check_id, msg, tags, result, fix=hint, severity=Severity.ERROR)


def _warn(check_id: str, msg: str, tags: tuple[str, ...] = (),
          result: Result = Result.FAIL) -> Finding:
    return advisory(check_id, msg, tags, result, severity=Severity.WARN)


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
            out.extend(_layer_extent_findings(asm.tag, layer))
        out.extend(_overlapping_band_findings(asm.tag, resolved.layers))
        if resolved.structure_index() is None:
            out.append(_err("integrity.assembly_layers",
                            f"assembly {asm.tag} has no STRUCTURE layer", (asm.tag,)))
    return out


def _layer_extent_findings(assembly_tag: str, layer: Layer) -> list[Finding]:
    """A banded layer must describe a band that can exist.

    Only bounds sharing a datum are comparable without a wall: ``GRADE`` against
    ``WALL_TOP`` is a different answer on every wall the assembly is used by, which is the
    whole reason the extent is stated against datums instead of elevations. Where the two
    ends *are* comparable, an inverted band is an authoring error and nothing else — it
    resolves to a layer of zero height that silently disappears from the model, the
    drawings and the order.
    """
    extent = getattr(layer, "extent", None)
    if extent is None or extent.bottom is None or extent.top is None:
        return []
    if extent.bottom.datum is not extent.top.datum:
        return []
    if extent.bottom.offset.meters < extent.top.offset.meters - 1e-9:
        return []
    return [_err("integrity.assembly_layers",
                 f"assembly {assembly_tag} layer {layer.name} has an extent whose bottom "
                 f"({extent.bottom.offset.inches:+.1f}\") is at or above its top "
                 f"({extent.top.offset.inches:+.1f}\") off the same "
                 f"{extent.bottom.datum.value} datum", (assembly_tag,),
                 "put the lower elevation in `bottom`")]


def _overlapping_band_findings(assembly_tag: str,
                               layers: Sequence[Layer]) -> list[Finding]:
    """Two banded layers of the same material must not claim the same elevations.

    This is the split-row case — a parge coat below grade and a protection panel above it,
    the two regions of one row of the stack. Regions of a split row are exclusive by
    definition; two that overlap are one wall wearing two coats of the same thing over the
    same band, which is a bill for stuff nobody applies. Only bands stated off the same
    datum are compared, for the reason ``_layer_extent_findings`` gives.
    """
    banded = [layer for layer in layers if getattr(layer, "extent", None) is not None]
    out: list[Finding] = []
    for index, first in enumerate(banded):
        for second in banded[index + 1:]:
            if first.material_ref != second.material_ref:
                continue
            span_a = _comparable_span(first.extent)
            span_b = _comparable_span(second.extent)
            if span_a is None or span_b is None or span_a[0] is not span_b[0]:
                continue
            _datum, a0, a1 = span_a
            _datum, b0, b1 = span_b
            if min(a1, b1) - max(a0, b0) > 1e-9:
                out.append(_err(
                    "integrity.assembly_layers",
                    f"assembly {assembly_tag} layers {first.name} and {second.name} are the "
                    f"same material over overlapping bands of the {_datum.value} datum",
                    (assembly_tag,),
                    "split rows of one layer must not overlap — move one band's end"))
    return out


def _comparable_span(extent: LayerExtent | None) -> tuple[LayerDatum, float, float] | None:
    """``(datum, bottom_offset_m, top_offset_m)`` when both ends share one datum."""
    if extent is None or extent.bottom is None or extent.top is None:
        return None
    if extent.bottom.datum is not extent.top.datum:
        return None
    return (extent.bottom.datum, extent.bottom.offset.meters, extent.top.offset.meters)


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


@check(Tier.INTEGRITY, "integrity.condition_star_override")
def condition_star_override(ctx: CheckContext) -> list[Finding]:
    """Per-condition star overrides must name condition keys that still exist (→ 11b).

    ``Transition.starred_conditions``/``unstarred_conditions`` address conditions by their
    exact derived key, and those keys are spelled out of assembly tags — rename an assembly
    and every override naming it silently stops applying, quietly re-curating the primary
    drawing set. An override that matches nothing is either a typo or a rename that never
    got followed through, so it warns rather than degrading in silence.
    """
    out: list[Finding] = []
    derived = {cond.key for cond in ctx.model.conditions}
    for tr in ctx.plan.library.transitions:
        for field in ("starred_conditions", "unstarred_conditions"):
            for key in getattr(tr, field, ()):
                if key not in derived:
                    out.append(_warn("integrity.condition_star_override",
                                     f"transition {tr.tag} {field} names {key!r}, which no "
                                     f"longer derives to any boundary condition",
                                     (tr.tag,)))
                elif not _matches(tr.condition_pattern, key):
                    # The key is real, but this transition never binds it — the override is
                    # inert, and the detail is curated by whichever transition does bind it.
                    out.append(_warn("integrity.condition_star_override",
                                     f"transition {tr.tag} {field} names {key!r}, which its "
                                     f"pattern {tr.condition_pattern!r} does not match",
                                     (tr.tag,)))
    return out
