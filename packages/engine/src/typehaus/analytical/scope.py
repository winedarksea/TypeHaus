"""What the analytical model covers: the engineered items, and their load path.

Owner decision, 2026-09-12. Not the whole building — a graph of 15,000 framed members is
not a thing a PE loads into RISA — and not the graded element alone either, because a
column with no beam over it and no footing under it is not a structure. So the scope is
every element an :class:`EngineeringRecord` names, plus the load path DOWN from it to
something that carries it to the ground, plus the path UP to what stands on it.

The walk **terminates at a wall or a footing**, which become support nodes rather than
members: a beam bearing in a foundation wall is a pinned support, a post on its bell is a
support, and a wall is not a curve member. Where an item is a wall or a panel —
``retaining_system``, ``girt_screw`` — the whole item is a gap, named in
words in :attr:`AnalyticalModel.gaps` rather than silently absent.

``retaining_wall`` is the exception and no longer reaches :func:`gap_line`:
:mod:`~typehaus.analytical.shells` meshes it as plates on soil springs, or says in its own
words why it cannot. It stays in :data:`SURFACE_KINDS` because that set is about the WALK —
a wall is still a terminal and never a member — and the shell stage speaks for it after.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Items whose element is a surface, not a curve member — so the walk terminates there.
#: ``retaining_wall`` is meshed by ``shells.py``; the rest are gaps in words.
SURFACE_KINDS = frozenset({"girt_screw", "retaining_wall", "retaining_system"})

#: How deep a bearing_refs chain may be walked. Four levels is past any real framing chain
#: and is the same guard ``engineering/pier_basis._delivered_to_posts`` uses.
_MAX_DEPTH = 8


@dataclass
class Scope:
    """The elements in the model, by kind, plus which items grade each of them."""

    item_ids: tuple[str, ...] = ()
    #: Post tags, sorted — every one becomes a column member.
    posts: tuple[str, ...] = ()
    #: Standalone Beam tags, sorted.
    beams: tuple[str, ...] = ()
    #: FloorSystem tags whose load this model carries, sorted.
    decks: tuple[str, ...] = ()
    #: Wall / Footing / Pad tags the walk terminated on — supports, never members.
    terminals: tuple[str, ...] = ()
    #: element tag -> the item ids that grade it, sorted.
    items_by_tag: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def items_for(self, *tags: str) -> tuple[str, ...]:
        out: set[str] = set()
        for tag in tags:
            out.update(self.items_by_tag.get(tag, ()))
        return tuple(sorted(out))


def gap_line(item_id: str, kind: str) -> str:
    """The words an item that reaches no member is listed under."""
    if kind in SURFACE_KINDS:
        return (f"{item_id}: no analytical representation in v1: surface members are a "
                f"follow-on")
    return (f"{item_id}: the elements it grades resolve to no curve member, so nothing in "
            f"this graph carries its demand")


def build_scope(ctx: Any) -> Scope:
    """Every element the records name, and everything on the load path through it."""
    plan = ctx.plan
    item_ids = tuple(sorted(ctx.engineering))
    items_by_tag: dict[str, set[str]] = {}
    seeds: set[str] = set()
    for item in item_ids:
        record = ctx.engineering[item]
        for tag in record.element_tags:
            items_by_tag.setdefault(tag, set()).add(item)
            if record.kind not in SURFACE_KINDS:
                seeds.add(tag)

    posts: set[str] = set()
    beams: set[str] = set()
    decks: set[str] = set()
    terminals: set[str] = set()
    for tag in sorted(seeds):
        _absorb(plan, tag, posts, beams, decks, terminals, 0)

    # UP: anything standing on what is already in scope. Iterated to a fixed point because a
    # deck lands on a beam that lands on a beam — one pass finds the first and misses the
    # second, and which one it misses depends on authoring order.
    while _walk_up(plan, posts, beams, decks, terminals):
        pass

    # A deck is only carried where a beam under it is in scope. A floor bearing entirely on
    # walls has no member here to hang its load on, and claiming it does would be a load
    # path this graph cannot show.
    decks = {tag for tag in decks
             if any(ref in beams for ref in _deck_bearings(plan, tag))}
    return Scope(
        item_ids=item_ids, posts=tuple(sorted(posts)), beams=tuple(sorted(beams)),
        decks=tuple(sorted(decks)), terminals=tuple(sorted(terminals)),
        items_by_tag={tag: tuple(sorted(items)) for tag, items in sorted(items_by_tag.items())},
    )


def _deck_bearings(plan: Any, tag: str) -> tuple[str, ...]:
    from typehaus.model.floors import FloorSystem

    deck = plan.by_tag(tag)
    if not isinstance(deck, FloorSystem):
        return ()
    return tuple(deck.joists.bearing_refs or ())


def _absorb(plan: Any, tag: str, posts: set[str], beams: set[str], decks: set[str],
            terminals: set[str], depth: int) -> None:
    """Put one element in scope and walk DOWN from it to whatever carries it."""
    from typehaus.model.elements import Wall
    from typehaus.model.floors import FloorSystem
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Footing, Pad, Post

    if depth > _MAX_DEPTH:
        return
    element = plan.by_tag(tag)
    if isinstance(element, Post):
        if tag in posts:
            return
        posts.add(tag)
        # Two ways a post reaches the ground and both are real: an authored
        # ``supported_by``, and a ``Footing`` that names the post in ``under`` (the
        # augered-and-belled case, where the post authors no support at all).
        for below in (element.supported_by, _footing_under(plan, tag)):
            if below:
                _absorb(plan, below, posts, beams, decks, terminals, depth + 1)
        return
    if isinstance(element, Beam) and element.ledger_on:
        terminals.add(tag)  # a ledger is a line support on its wall, not a member
        return
    if isinstance(element, Beam):
        if tag in beams:
            return
        beams.add(tag)
        for ref in element.bearing_refs or ():
            _absorb(plan, ref, posts, beams, decks, terminals, depth + 1)
        return
    if isinstance(element, FloorSystem):
        if tag in decks:
            return
        decks.add(tag)
        for ref in element.joists.bearing_refs or ():
            _absorb(plan, ref, posts, beams, decks, terminals, depth + 1)
        return
    if isinstance(element, Roof):
        # A roof is not a member. What carries it is, and that is what the record's demand
        # travels down.
        for ref in element.bearing_refs or ():
            _absorb(plan, ref, posts, beams, decks, terminals, depth + 1)
        return
    if isinstance(element, Wall | Footing | Pad):
        terminals.add(tag)


def _footing_under(plan: Any, tag: str) -> str | None:
    from typehaus.model.structure import Footing

    for element in plan.all_elements():
        if isinstance(element, Footing) and element.under == tag:
            return element.tag
    return None


def _walk_up(plan: Any, posts: set[str], beams: set[str], decks: set[str],
             terminals: set[str]) -> bool:
    """Add everything that bears on something already in scope. True if anything moved."""
    from typehaus.model.floors import FloorSystem
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post

    carried = posts | beams
    added = False
    for element in sorted(plan.all_elements(), key=lambda e: getattr(e, "tag", "") or ""):
        tag = getattr(element, "tag", None)
        if not tag:
            continue
        if isinstance(element, Roof) and any(ref in carried
                                             for ref in element.bearing_refs or ()):
            # A roof standing partly on scope pulls the REST of its bearing line in: half a
            # roof's load path is not a load path.
            for ref in element.bearing_refs or ():
                before = len(posts) + len(beams)
                _absorb(plan, ref, posts, beams, decks, terminals, 0)
                added = added or (len(posts) + len(beams)) != before
            continue
        if isinstance(element, Post):
            wants = tag not in posts and element.supported_by in carried
        elif isinstance(element, Beam) and element.ledger_on:
            continue
        elif isinstance(element, Beam):
            wants = tag not in beams and any(ref in carried
                                             for ref in element.bearing_refs or ())
        elif isinstance(element, FloorSystem):
            wants = tag not in decks and any(ref in beams
                                             for ref in element.joists.bearing_refs or ())
        else:
            continue
        if wants:
            _absorb(plan, tag, posts, beams, decks, terminals, 0)
            added = True
    return added
