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
        # A "band" is a buried single-purpose layer of the ground — an FPSF wing, a
        # capillary break — and has no structure by definition. Read off the assembly's own
        # ``role`` rather than inferred from the absence of the layer, which is the very
        # mistake this line exists to catch.
        if resolved.role == "enclosure" and resolved.structure_index() is None:
            out.append(_err("integrity.assembly_layers",
                            f"assembly {asm.tag} has no STRUCTURE layer", (asm.tag,)))
        if resolved.role == "band" and resolved.structure_index() is not None:
            out.append(_err("integrity.assembly_layers",
                            f"assembly {asm.tag} declares role=\"band\" but carries a "
                            "STRUCTURE layer; a band is a buried layer of the ground, not a "
                            "thing that holds anything up", (asm.tag,)))
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
    """The rough opening fits its host wall — and a pocket door's cavity fits too.

    The second half is not the same test. A pocket's framed extent is roughly twice its
    clear opening, and the cavity legitimately crosses a node into a colinear neighbour of
    the same assembly, so it is graded against that whole run rather than against the host
    alone (``framing/pockets.py``). Without this the wall body, the plan symbol and the
    framing would all happily draw a leaf sliding into a corner.
    """
    from typehaus.resolve.framing.pockets import pocket_segments
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
        if not op.pocket_run_m or ctx.plan is None:
            continue
        segments, shortfall = pocket_segments(ctx.plan, ctx.model, op)
        if shortfall > 1e-9:
            chain = " -> ".join(segment.wall_tag for segment in segments) or op.host_wall
            out.append(_err(
                "integrity.opening_fits",
                f"pocket door {op.tag} needs {op.pocket_run_m*39.37:.1f}\" of cavity past "
                f"its opening but runs out of colinear wall in {chain} — "
                f"{shortfall*39.37:.1f}\" short. A pocket may only continue into a wall "
                f"that shares the node, runs parallel and carries the same assembly.",
                (op.tag,)))
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


@check(Tier.INTEGRITY, "integrity.slab_thickness")
def slab_thickness_matches_assembly(ctx: CheckContext) -> list[Finding]:
    """A slab's authored ``thickness`` has to end on one of its assembly's layer boundaries.

    A wall has no such check because it needs none: a wall's thickness *is* its layer sum,
    derived. A :class:`~typehaus.model.floors.Slab` authors ``thickness`` independently of
    the assembly it names, because the two measure different things — ``CATLIN_SLAB_FLOOR``
    is a 3.5" pour over 3" of XPS that is *under* the slab, not part of it, and a deck
    assembly carries a gypsum thermal barrier hanging below its soffit. So the rule cannot
    be "thickness == sum of layers".

    What it can be, and what this asserts, is that the slab body stops at a layer boundary:
    reading the stack top-down, some prefix of it adds up to ``thickness`` exactly. Nothing
    is half in the pour and half out of it. That is what keeps a tuned build-up true —
    catlin's 12 5/8" EPS-formed deck is a 4 5/8" cap on an 8" form, and dropping the cap to
    4" without moving ``thickness`` would otherwise pass silently while the finished floor
    plane no longer met the wood bays beside it.
    """
    out: list[Finding] = []
    for el in ctx.plan.all_elements():
        if el.element_kind != "Slab" or getattr(el, "assembly", None) is None:
            continue
        resolved = ctx.plan.library.resolve_assembly(el.assembly)
        if resolved is None:
            continue  # integrity.slab_assembly territory; not this check's complaint
        thickness_in = el.thickness.inches
        prefixes: list[float] = []
        running = 0.0
        for layer in resolved.layers:
            running += layer.thickness.inches
            prefixes.append(running)
        if any(abs(prefix - thickness_in) < 1e-6 for prefix in prefixes):
            continue
        out.append(_err(
            "integrity.slab_thickness",
            f"slab {el.tag} is authored {thickness_in:g}\" thick but assembly "
            f"{el.assembly} has no layer boundary there — its stack reads "
            + ", ".join(f"{prefix:g}\"" for prefix in prefixes),
            (el.tag,),
            "move the slab thickness to a layer boundary, or restate the layer that moved",
        ))
    return out


# The finishes that are a treatment OF a concrete surface rather than a covering laid over
# whatever is underneath. Kept here beside the rule that needs it, the way
# ``takeoff/finishes.py::_WASTE`` keeps its own table: ``Material`` has no substrate field,
# and adding one would be a schema change carrying a fact only this check reads.
_CONCRETE_FINISHES = {"sealed-concrete", "polished-concrete"}

# How much of the finished area has to sit over a slab. Not 100%, and the slack is measured
# rather than guessed: RM-GARAGE is a legitimate sealed slab that covers only ~85%, because
# its clear face is taken at the wood-wall lining while SL-G-FLOOR is poured inside the ICF
# stem below it. Exact containment would report that as a defect. Half is the line between
# "this room is floored in concrete" and "this finish was left behind by a structure change".
_CONCRETE_FINISH_MIN_COVERAGE = 0.5


@check(Tier.INTEGRITY, "integrity.concrete_finish_needs_concrete_deck")
def concrete_finish_needs_concrete_deck(ctx: CheckContext) -> list[Finding]:
    """A sealed or polished floor needs concrete under it to seal or polish.

    This is drift, not a typo, and drift is what makes it worth a check. The catlin main
    floor was one 1,233 SF cast deck until the 2026-08-21 EPS/wood overhaul replaced most of
    it with I-joists and plywood. The rooms above kept their authored ``sealed-concrete``,
    which still resolved, still rendered, and still billed a sealer — over a wood deck that
    has no slab to seal. Nothing else notices: ``floor_finish`` is a free string joined to a
    library material, and the join was never wrong.

    Covers the room's FIELD finish and any AUTHORED zone. A DERIVED zone is exempt by
    construction — it exists only because a ``Slab`` with a ``floor_finish`` is under it,
    which is precisely what this measures.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    slabs_by_storey: dict[str, list[Polygon]] = {}
    for solid in ctx.model.solids:
        if solid.category != "slab" or len(solid.outline) < 3:
            continue
        footprint = Polygon(solid.outline)
        if not footprint.is_valid:
            footprint = footprint.buffer(0)
        slabs_by_storey.setdefault(solid.storey, []).append(footprint)
    concrete_by_storey = {storey: unary_union(parts)
                          for storey, parts in slabs_by_storey.items()}

    out: list[Finding] = []
    for room in ctx.model.rooms:
        if len(room.clear_face) < 3:
            continue
        face = Polygon(room.clear_face)
        if not face.is_valid:
            face = face.buffer(0)
        claims: list[tuple[str, str, Polygon]] = []
        if room.floor_finish in _CONCRETE_FINISHES:
            claims.append((room.floor_finish, "floor_finish", face))
        for zone in room.finish_zones:
            if zone.source_ref is not None or zone.material_ref not in _CONCRETE_FINISHES:
                continue
            zone_face = Polygon(zone.outline)
            if not zone_face.is_valid:
                zone_face = zone_face.buffer(0)
            claims.append((zone.material_ref, "finish zone", zone_face.intersection(face)))
        concrete = concrete_by_storey.get(room.storey)
        for finish, where, area in claims:
            if area.is_empty or area.area <= 0.0:
                continue
            covered = 0.0 if concrete is None else area.intersection(concrete).area
            fraction = covered / area.area
            if fraction >= _CONCRETE_FINISH_MIN_COVERAGE:
                continue
            out.append(_err(
                "integrity.concrete_finish_needs_concrete_deck",
                f"room {room.tag} {where} is {finish!r} but only {fraction * 100:.0f}% of "
                f"that area sits over a slab on storey {room.storey} — a sealer or a polish "
                "is a treatment of concrete, not a covering that can be laid over a deck",
                (room.tag,),
                "give the room a covering finish (vinyl-sheet, lvp, tile) if the concrete "
                "under it went away, or set floor_finish on the Slab that is actually there",
            ))
    return out
