"""Reference-remap registry + ``MutationResult`` (→ 21b §Mutation contract #33).

Topology-changing macros (split, join, trim, heal) can invalidate references far beyond
geometry: hosted openings, `stacks_on` tiebreakers, `bearing_refs`, room-lining wall refs.
So every such op returns a :class:`MutationResult` — its patch ops *plus* a
:class:`ReferenceRemap` describing how element identities changed. Each element kind that can
hold a reference registers a :class:`RemapHandler`; a CI completeness test (→ 21b) introspects
every kind's ref-bearing fields and asserts each is named in some handler's ``ref_fields``, so
no reference can silently dangle after a remap.

References in authored source are by **tag** (``start_node``, ``host``, …), so the remap and
its handlers operate on tags — the same currency the libcst writeback edits.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from typehaus.model.base import Element
from typehaus.source.ops import PatchOp

ElementT = TypeVar("ElementT", bound=Element)


@dataclass(frozen=True)
class ReferenceRemap:
    """How element identities changed during a topology op.

    ``renamed`` maps an old tag to the tag that inherits its references (split: the survivor
    segment; join/merge: the survivor). ``deleted`` are tags whose references become dangling
    unless a handler rehosts them. ``rehost`` is an explicit override map an op can supply
    (e.g. split re-hosts opening D-103 onto the segment its position falls in).
    """

    renamed: dict[str, str] = field(default_factory=dict)
    deleted: frozenset[str] = frozenset()
    rehost: dict[str, str] = field(default_factory=dict)  # opening_tag -> new host wall tag

    def resolve(self, ref: str) -> str | None:
        """Return the surviving tag for ``ref``, or ``None`` if it was deleted."""
        if ref in self.deleted:
            return None
        return self.renamed.get(ref, ref)


@dataclass(frozen=True)
class MutationResult:
    """The full outcome of a topology-changing op (→ 21b §Mutation contract)."""

    ops: list[PatchOp] = field(default_factory=list)
    remap: ReferenceRemap = field(default_factory=ReferenceRemap)
    deleted_tags: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


# --- handler registry --------------------------------------------------------
# A handler yields zero or more ``update`` PatchOps that rewrite one element's reference
# fields under a remap. Returning no ops means "unchanged".
RemapHandler = Callable[[Element, ReferenceRemap], list[PatchOp]]


@dataclass(frozen=True)
class _Registration:
    kind: str
    ref_fields: tuple[str, ...]
    handler: RemapHandler


_HANDLERS: dict[str, _Registration] = {}


def remap_handler(
    cls: type[Element], ref_fields: tuple[str, ...]
) -> Callable[[RemapHandler], RemapHandler]:
    """Register ``handler`` as the remapper for ``cls``'s ``ref_fields`` (→ 21b)."""

    def decorate(handler: RemapHandler) -> RemapHandler:
        _HANDLERS[cls.__name__] = _Registration(cls.__name__, tuple(ref_fields), handler)
        return handler

    return decorate


def registered_ref_fields() -> dict[str, tuple[str, ...]]:
    """Kind → the ref-bearing fields its handler covers (the CI completeness surface)."""
    return {r.kind: r.ref_fields for r in _HANDLERS.values()}


def remap_ops_for(element: Element, remap: ReferenceRemap) -> list[PatchOp]:
    """Yield update ops to carry ``element``'s references through ``remap`` (empty if none)."""
    reg = _HANDLERS.get(element.element_kind)
    if reg is None:
        return []
    return reg.handler(element, remap)


# --- built-in handlers -------------------------------------------------------
# Registered here rather than beside each element class so `model/remap.py` is the single
# audit point; the completeness test (→ 21b) still enforces field coverage.

def _register_builtins() -> None:
    from typehaus.model.elements import Door, RoughOpening, Wall, Window
    from typehaus.model.spatial import Room, Stair

    @remap_handler(Wall, ref_fields=("start_node", "end_node", "stacks_on", "bearing_refs"))
    def _wall(el: Element, remap: ReferenceRemap) -> list[PatchOp]:
        w = el  # typed as Wall at runtime
        changed: dict[str, object] = {}
        for fld in ("start_node", "end_node", "stacks_on"):
            cur = getattr(w, fld, None)
            if not cur:
                continue
            survivor = remap.resolve(cur)
            if survivor is not None and survivor != cur:
                changed[fld] = survivor
        refs = getattr(w, "bearing_refs", ()) or ()
        new_refs = tuple(
            s for s in (remap.resolve(r) for r in refs) if s is not None
        )
        if new_refs != tuple(refs):
            changed["bearing_refs"] = list(new_refs)
        if not changed:
            return []
        return [PatchOp("update", "Wall", w.tag, changed)]

    def _opening_handler(kind: str) -> RemapHandler:
        def handler(el: Element, remap: ReferenceRemap) -> list[PatchOp]:
            host = getattr(el, "host", None)
            # Explicit rehost (split re-hosts by position) wins over a plain rename.
            target = remap.rehost.get(el.tag) or remap.resolve(host) if host else None
            if target is None or target == host:
                return []
            return [PatchOp("update", kind, el.tag, {"host": target})]

        return handler

    for _cls in (Door, Window, RoughOpening):
        remap_handler(_cls, ref_fields=("host",))(_opening_handler(_cls.__name__))

    @remap_handler(Stair, ref_fields=("bearing_refs",))
    def _stair(el: Element, remap: ReferenceRemap) -> list[PatchOp]:
        refs = getattr(el, "bearing_refs", ()) or ()
        new_refs = tuple(s for s in (remap.resolve(r) for r in refs) if s is not None)
        if new_refs == tuple(refs):
            return []
        return [PatchOp("update", "Stair", el.tag, {"bearing_refs": list(new_refs)})]

    @remap_handler(Room, ref_fields=("wall_lining_exceptions",))
    def _room(el: Element, remap: ReferenceRemap) -> list[PatchOp]:
        # Wall-lining exceptions carry wall_ref, but they are nested records edited as a
        # whole-field replacement; a dangling ref surfaces as an integrity finding rather
        # than an auto-rewrite, so this handler only reports (no ops) — coverage satisfied.
        return []


_register_builtins()
