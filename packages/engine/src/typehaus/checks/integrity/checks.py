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
        out.extend(_slot_findings(asm.tag, resolved.layers))
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


def _slot_findings(assembly_tag: str, layers: Sequence[Layer]) -> list[Finding]:
    """The regions of one ``Layer.slot`` must together describe one depth position.

    A slot is the split-row spelling: its members share a single strip of the stack
    (``resolve/topology.py::_slot_host``), which only means anything if they agree about how
    deep that strip is and take turns occupying it. Three ways to get it wrong, all silent
    without this:

    * **Disagreeing thicknesses.** The first member is the one that pays, so a second member
      authored thicker simply gets clipped to the first's depth — a 6" plinth under a 4"
      field renders and bills as 4" and nothing says so.
    * **A member with no extent.** It claims the whole wall, and every sibling then draws
      inside a region it also covers. Two bricks in the same place is not a wall.
    * **Overlapping bands.** Same, over part of the height rather than all of it. This is
      the case :func:`_overlapping_band_findings` already refuses for two layers of the
      *same* material; inside a slot it is wrong for any two, because differing materials is
      the entire point of splitting the row.

    A *gap* between two regions is legal and deliberate — those elevations are simply not
    built, which is how a reveal or a recessed course is spelled.
    """
    slots: dict[str, list[Layer]] = {}
    for layer in layers:
        slot = getattr(layer, "slot", None)
        if slot is not None:
            slots.setdefault(slot, []).append(layer)
    out: list[Finding] = []
    for slot, members in slots.items():
        depth = members[0].thickness.meters
        for member in members[1:]:
            if abs(member.thickness.meters - depth) > 1e-9:
                out.append(_err(
                    "integrity.assembly_layers",
                    f"assembly {assembly_tag} slot {slot!r} layer {member.name} is "
                    f"{member.thickness.inches:.3f}\" but the slot is {members[0].name}'s "
                    f"{members[0].thickness.inches:.3f}\" — one row has one depth",
                    (assembly_tag,),
                    "give every layer of a slot the same thickness, "
                    "or take this one out of the slot"))
        for member in members:
            if getattr(member, "extent", None) is None:
                out.append(_err(
                    "integrity.assembly_layers",
                    f"assembly {assembly_tag} slot {slot!r} layer {member.name} has no "
                    f"extent, so it claims the whole wall and hides its siblings",
                    (assembly_tag,),
                    "band every region of a split row"))
        for index, first in enumerate(members):
            for second in members[index + 1:]:
                span_a = _slot_span(first.extent)
                span_b = _slot_span(second.extent)
                if span_a is None or span_b is None or span_a[0] is not span_b[0]:
                    continue
                _datum, a0, a1 = span_a
                _datum, b0, b1 = span_b
                if min(a1, b1) - max(a0, b0) > 1e-9:
                    out.append(_err(
                        "integrity.assembly_layers",
                        f"assembly {assembly_tag} slot {slot!r} layers {first.name} and "
                        f"{second.name} claim overlapping bands of the {_datum.value} datum",
                        (assembly_tag,),
                        "regions of one row are exclusive — move one band's end"))
    return out


def _slot_span(extent: LayerExtent | None) -> tuple[LayerDatum, float, float] | None:
    """``(datum, bottom_offset_m, top_offset_m)`` for one region of a split row.

    Looser than :func:`_comparable_span` on purpose. The top region of a row is naturally
    authored with an open top — ``top=None`` means "the wall's own top", which is the only
    way to say it without writing a wall's height into an assembly that many walls share —
    and ``_comparable_span`` would give up on it, letting exactly the overlap this is meant
    to catch through. An open end is instead read as the infinity it is, so a region running
    to the wall top still refuses to overlap the region below it. Two regions are comparable
    when their *authored* ends agree about the datum; a region with no authored end at all
    (both open) is the whole wall, which the no-extent rule above has already reported.
    """
    if extent is None:
        return None
    datum = (extent.bottom.datum if extent.bottom is not None
             else extent.top.datum if extent.top is not None else None)
    if datum is None:
        return None
    for bound in (extent.bottom, extent.top):
        if bound is not None and bound.datum is not datum:
            return None
    bottom = extent.bottom.offset.meters if extent.bottom is not None else float("-inf")
    top = extent.top.offset.meters if extent.top is not None else float("inf")
    return (datum, bottom, top)


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
