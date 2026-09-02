"""Guard and handrail geometry: posts, rails and infill along an authored plan path.

Split by *part*, not by style: :mod:`.spans` owns what the walking surface does, :mod:`.parts`
owns what each part is made of and how big it is, :mod:`.frame` owns posts and rails, and
:mod:`.infill` owns what fills the bays.

The flat/raking fork is one line here and one object (:class:`~.spans.RailingSurface`)
everywhere else, so a new style is written once rather than twice.
"""

from __future__ import annotations

from typehaus.findings import Finding
from typehaus.model.enums import RailingKind
from typehaus.model.structure import Railing
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.railings.frame import (
    MIN_POST_SPACING_M,
    emit_posts,
    emit_rails,
    railing_post_stations,
)
from typehaus.resolve.railings.infill import emit_infill
from typehaus.resolve.railings.parts import resolve_parts
from typehaus.resolve.railings.spans import flat_surface, raking_surface

__all__ = ["railing_post_stations", "resolve_railing"]


def resolve_railing(model: ResolvedModel, el: Railing, storey: str) -> list[Finding]:
    """Frame one railing into ``model.solids``; returns WARN-tier geometry findings."""
    path = [p.xy_m for p in el.path]
    if len(path) < 2:
        return []
    if el.kind is RailingKind.MASONRY:
        # A masonry guard is a wall — a layered stucco/CMU/air/brick stack standing at an
        # edge, whose grouted cores can carry a post base and whose volume bills in cubic
        # yards. None of that survives being reduced to posts and rails, so the model
        # authors it as a ``Wall``/``FoundationWall`` with ``guard=True`` and the checks and
        # take-off read it there. Framing a stick guard here would draw a second, wrong
        # guard on top of the real one.
        return []

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
    stations = railing_post_stations(path, max(el.post_spacing.meters, MIN_POST_SPACING_M))
    emit_posts(model, el, storey, stations, surface, parts, rail_h)
    emit_rails(model, el, storey, path, surface, parts, rail_h)
    return emit_infill(model, el, storey, stations, surface, parts, rail_h)
