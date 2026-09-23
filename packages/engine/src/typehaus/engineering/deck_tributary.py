"""THE deck tributary rule: the strip of deck each beam carries, and what reaches each post.

One copy, five readers: ``glulam_beam`` (the beam's line load), ``post_bearing`` (the beam's
reactions), ``pier_basis`` (a post's tributary area), ``analytical/loads`` (the graph's line
loads) and ``checks/structural/deck`` (R507 footings and posts, via ``_engineering``). Until
2026-09-23 only ``glulam_beam`` used the half-bay rule; the rest gave every beam the WHOLE
joist span, which double-counts the deck wherever two beams share it.

A beam carries half of each adjacent joist bay plus the joists' overhang on whichever side
it is the outermost bearing. Its share of the deck is that width times its node-to-node
length, divided among ALL its supports and kept where a support is (or leads down to) a Post.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md`` §1 (the balcony posts) and
``north_entry_piers.md`` (the breezeway landing), both hand-worked in a separate pass.
"""

from __future__ import annotations

import math
from typing import Any

_M_PER_FT = 0.3048
#: Two bearing lines closer than 3" are one bearing, however many ways it was found.
_SAME_LINE_M = 0.0762


def _joists(ctx: Any, deck: Any) -> list[Any]:
    resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
    return [m for m in resolved.members if m.category == "joist"] if resolved else []


def _cantilevers_m(deck: Any) -> tuple[float, float]:
    spec = deck.joists
    base = spec.cantilever.meters if spec.cantilever is not None else 0.0
    start = spec.cantilever_start.meters if spec.cantilever_start is not None else base
    end = spec.cantilever_end.meters if spec.cantilever_end is not None else base
    return start, end


def joist_span_ft(ctx: Any, deck: Any) -> float | None:
    """The deck's joist SPAN, from the resolved joists — bearing line to bearing line.

    A joist's drawn length includes its cantilevers; ``resolve/floors.py`` adds them to the
    outer bays only, so a member carries one exactly when its tip sits on the field's extent.
    Restated by ``checks/structural/deck.py::_Deck.joist_span_ft``, which reads R507 tables.
    """
    joists = _joists(ctx, deck)
    if not joists:
        return None
    axis = 0 if (deck.joists.direction or "x") == "x" else 1
    start_ft, end_ft = (c / _M_PER_FT for c in _cantilevers_m(deck))
    ends = [sorted((m.p0[axis], m.p1[axis])) for m in joists]
    low = min(a for a, _ in ends)
    high = max(b for _, b in ends)
    spans = []
    for (a, b), member in zip(ends, joists, strict=True):
        span_ft = member.length_m / _M_PER_FT
        if abs(a - low) < 1e-6:
            span_ft -= start_ft
        if abs(b - high) < 1e-6:
            span_ft -= end_ft
        spans.append(span_ft)
    return max(spans)


def beam_tributary_ft(ctx: Any, deck: Any, beam: Any) -> float | None:
    """Width of deck ``beam`` carries: half of each adjacent bay, plus the overhang on
    whichever side it is the outermost bearing.

    Bearing lines are the deck's ``bearing_refs`` at their nodes' coordinate along the joist
    axis, plus the joist field's two outer bearings (its extent less the cantilevers).
    ``None`` when the beam or the joist field does not place.
    """
    joists = _joists(ctx, deck)
    if not joists:
        return None
    axis = 0 if (deck.joists.direction or "x") == "x" else 1

    def line_of(element: Any) -> float | None:
        nodes = [ctx.plan.by_tag(getattr(element, name, None) or "")
                 for name in ("start_node", "end_node")]
        if any(n is None or getattr(n, "position", None) is None for n in nodes):
            return None
        return sum(n.position.xy_m[axis] for n in nodes) / 2.0

    here = line_of(beam)
    if here is None:
        return None
    start, end = _cantilevers_m(deck)
    low = min(min(m.p0[axis], m.p1[axis]) for m in joists)
    high = max(max(m.p0[axis], m.p1[axis]) for m in joists)
    lines = [low + start, high - end]
    for ref in deck.joists.bearing_refs or ():
        element = ctx.plan.by_tag(ref)
        if element is not None and (c := line_of(element)) is not None:
            lines.append(c)
    merged: list[float] = []
    for c in sorted(lines):
        if not merged or c - merged[-1] > _SAME_LINE_M:
            merged.append(c)
    i = min(range(len(merged)), key=lambda k: abs(merged[k] - here))
    width = (merged[i] - merged[i - 1]) / 2.0 if i > 0 else start
    width += (merged[i + 1] - merged[i]) / 2.0 if i < len(merged) - 1 else end
    return width / _M_PER_FT


def delivered_to_posts(ctx: Any, supports: Any, depth: int = 0) -> dict[str, float]:
    """``post tag -> fraction of one beam's load`` that reaches a Post, down the beam chain.

    The north entry's joists bear on floor beams, those on SEAT beams, and only the seats on
    piers, so a support that is itself a Beam passes its share on to ITS supports. A wall or
    a pier direct keeps its share and falls out: the fractions need not sum to 1. ``depth``
    guards a ``bearing_refs`` cycle.
    """
    from typehaus.model.structure import Beam, Post

    out: dict[str, float] = {}
    supports = tuple(supports)
    if not supports or depth > 4:
        return out
    each = 1.0 / len(supports)
    for tag in supports:
        element = ctx.plan.by_tag(tag)
        if isinstance(element, Post):
            out[tag] = out.get(tag, 0.0) + each
        elif isinstance(element, Beam):
            for post, fraction in delivered_to_posts(
                    ctx, element.bearing_refs or (), depth + 1).items():
                out[post] = out.get(post, 0.0) + each * fraction
    return out


def deck_beams(ctx: Any, deck: Any) -> list[Any]:
    """The Beams a deck's joists bear on, in ``bearing_refs`` order."""
    from typehaus.model.structure import Beam

    return [b for ref in deck.joists.bearing_refs or ()
            if isinstance(b := ctx.plan.by_tag(ref), Beam)]


def deck_posts(ctx: Any, deck: Any) -> list[str]:
    """Post tags under a deck, down the whole beam chain, de-duplicated in walk order."""
    out: list[str] = []
    for beam in deck_beams(ctx, deck):
        for tag in delivered_to_posts(ctx, beam.bearing_refs or ()):
            if tag not in out:
                out.append(tag)
    return out


def _outline_ft2(deck: Any) -> float | None:
    ring = [p.xy_m for p in deck.outline]
    if len(ring) < 3:
        return None
    area = 0.5 * sum(x0 * y1 - x1 * y0
                     for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1], strict=True))
    return abs(area) / (_M_PER_FT ** 2)


def deck_post_tributaries(ctx: Any, deck: Any) -> dict[str, float] | None:
    """``post tag -> tributary ft2`` for one deck, by each beam's own strip.

    ``beam_tributary_ft x beam length``, divided among the beam's supports (a bearing WALL
    keeps its half) and kept where a support reaches a post. Where a strip or a beam length
    will not resolve, the outline area split evenly among the posts stands in. ``None``
    when no post carries the deck, or when neither answer resolves.
    """
    posts = deck_posts(ctx, deck)
    if not posts:
        return None
    area = _outline_ft2(deck)
    fallback = {tag: area / len(posts) for tag in posts} if area is not None else None
    nodes = {e.tag: e.position.xy_m for e in ctx.plan.all_elements()
             if e.element_kind == "Node" and getattr(e, "position", None) is not None}
    out = dict.fromkeys(posts, 0.0)
    for beam in deck_beams(ctx, deck):
        width_ft = beam_tributary_ft(ctx, deck, beam)
        p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
        supports = tuple(beam.bearing_refs or ())
        if width_ft is None or p0 is None or p1 is None or not supports:
            return fallback
        share = width_ft * math.dist(p0, p1) / _M_PER_FT
        for tag, fraction in delivered_to_posts(ctx, supports).items():
            out[tag] = out.get(tag, 0.0) + share * fraction
    return out
