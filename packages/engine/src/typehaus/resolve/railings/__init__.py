"""Guard and handrail geometry: posts, rails and infill along an authored plan path.

Split by *part*, not by style: :mod:`.spans` owns what the walking surface does, :mod:`.parts`
owns what each part is made of and how big it is, :mod:`.frame` owns posts and rails,
:mod:`.terminations` owns the ends, and :mod:`.infill` owns what fills the bays.

The flat/raking fork is one line here and one object (:class:`~.spans.RailingSurface`)
everywhere else, so a new style is written once rather than twice.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.findings import Finding, element_error
from typehaus.model.enums import RailingKind
from typehaus.model.structure import Railing
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.railings.fascia_assembly import emit_fascia_assembly
from typehaus.resolve.railings.fascia_layout import fascia_deck
from typehaus.resolve.railings.frame import (
    MIN_POST_SPACING_M,
    emit_posts,
    emit_rails,
    railing_post_stations,
)
from typehaus.resolve.railings.guard_line import (
    guard_line,
    guard_line_offset_m,
    guard_post_stations,
    shared_post_ends,
)
from typehaus.resolve.railings.infill import emit_infill
from typehaus.resolve.railings.parts import railing_type, resolve_parts
from typehaus.resolve.railings.spans import deck_surface, flat_surface, raking_surface
from typehaus.resolve.railings.terminations import emit_terminations

__all__ = ["guard_line", "guard_post_stations", "railing_post_stations", "resolve_railing"]


def resolve_railing(model: ResolvedModel, el: Railing, storey: str) -> list[Finding]:
    """Frame one railing into ``model.solids``; returns WARN-tier geometry findings."""
    findings: list[Finding] = []
    if el.type_ref is not None and not any(
            product.tag == el.type_ref for product in model.plan.library.railing_types):
        findings.append(element_error(
            "integrity.unknown_railing_type",
            f"railing {el.tag} references missing type {el.type_ref!r}", el.tag))
    # Where the guard stands: the path, or outboard of it on a fascia (→ .guard_line).
    path = guard_line(model.plan.library, el)
    if len(path) < 2:
        return findings
    if el.kind is RailingKind.MASONRY:
        # A masonry guard is a wall — a layered stucco/CMU/air/brick stack standing at an
        # edge, whose grouted cores can carry a post base and whose volume bills in cubic
        # yards. None of that survives being reduced to posts and rails, so the model
        # authors it as a ``Wall``/``FoundationWall`` with ``guard=True`` and the checks and
        # take-off read it there. Framing a stick guard here would draw a second, wrong
        # guard on top of the real one.
        return findings

    stair = (next((s for s in model.stairs if s.tag == el.serves_stair), None)
             if el.serves_stair is not None else None)
    base = el.base_elevation.meters
    if stair is not None:
        surface = raking_surface(stair, base)
        # R311.7.8.1 measures a handrail above the *nosings*, which is not the datum
        # ``height`` uses (guard height above the deck); ``height`` stands in when the
        # element states no ``top_height``.
        rail_h = (el.top_height if el.top_height is not None else el.height).meters
    else:
        surface = flat_surface(base)
        rail_h = el.height.meters

    parts = resolve_parts(model, el)
    product = railing_type(model.plan.library, el)
    mount_spec = product.fascia_mount if product is not None and el.mount == "fascia" else None
    if el.fascia_ref is not None:
        deck = fascia_deck(model, el)
        if deck is None:
            return findings + [element_error("geometry.railing_fascia_host",
                f"{el.tag}: fascia_ref must identify a fascia with a resolved floor host", el.tag)]
        surface = deck_surface(deck, [p.xy_m for p in el.path],
                               guard_line_offset_m(model.plan.library, el))
    stations = railing_post_stations(path, max(el.post_spacing.meters, MIN_POST_SPACING_M))
    shared, shared_findings = shared_post_ends(model.plan, el, stations)
    findings += shared_findings
    first = len(model.solids)
    if mount_spec is not None:
        if el.fascia_face_offset is None or el.fascia_bracket_drop is None:
            return findings + [element_error("geometry.railing_fascia_dimensions",
                f"{el.tag}: detailed mounts need fascia_face_offset "
                "and fascia_bracket_drop", el.tag)]
        try:
            emit_fascia_assembly(model, el, storey, surface, parts, mount_spec, shared)
        except ValueError as exc:
            del model.solids[first:]
            return findings + [element_error("geometry.railing_fascia_layout", str(exc), el.tag)]
    else:
        findings += emit_posts(model, el, storey, stations, surface, parts, rail_h, shared)
    bottom_clearance = mount_spec.bottom_clearance.meters if mount_spec else 0.0
    emit_rails(model, el, storey, path, surface, parts, rail_h,
               bottom_clearance_m=bottom_clearance, face_height=mount_spec is not None)
    findings.extend(emit_terminations(model, el, storey, path, surface, parts, rail_h))
    findings += emit_infill(model, el, storey, stations, surface, parts, rail_h,
                            bottom_clearance_m=bottom_clearance,
                            face_height=mount_spec is not None)
    # Every part of the guard is addressable as the railing it belongs to.
    for i in range(first, len(model.solids)):
        model.solids[i] = replace(model.solids[i], host_ref=el.tag, group=el.tag)
    return findings
