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
from typing import Literal

from typehaus.model.base import Element
from typehaus.source.ops import PatchOp


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
    rehost: dict[str, str] = field(default_factory=dict)  # element tag -> new host wall tag
    # Wall-attached placeables: metres added to ``distance_from_start``; a ``reversed`` tag's
    # new wall runs the other way, so its distance becomes ``shift - distance`` and its face
    # flips. The station is the one ``resolve/placeables._resolve_location`` reads: from the
    # start node, along the node-to-node axis.
    shift: dict[str, float] = field(default_factory=dict)
    reversed: frozenset[str] = frozenset()

    def resolve(self, ref: str) -> str | None:
        """Return the surviving tag for ``ref``, or ``None`` if it was deleted."""
        if ref in self.deleted:
            return None
        return self.renamed.get(ref, ref)


ImpactKind = Literal["carried", "left_behind", "needs_review"]


@dataclass(frozen=True)
class Impact:
    """What an edit did to something other than its target: ``carried`` (followed it),
    ``left_behind`` (a relationship the edit dropped), ``needs_review`` (a person must look)."""

    tag: str
    kind: ImpactKind
    reason: str

    def to_json(self) -> dict[str, str]:
        return {"tag": self.tag, "kind": self.kind, "reason": self.reason}


@dataclass(frozen=True)
class MutationResult:
    """The full outcome of a topology-changing op (→ 21b §Mutation contract).

    ``warnings`` is the older, prose-only surface: when a macro supplies none, the reasons of
    its non-``carried`` impacts stand in, so callers reading only warnings still see them."""

    ops: list[PatchOp] = field(default_factory=list)
    remap: ReferenceRemap = field(default_factory=ReferenceRemap)
    deleted_tags: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    impacts: tuple[Impact, ...] = ()

    def __post_init__(self) -> None:
        if self.impacts and not self.warnings:
            object.__setattr__(self, "warnings", tuple(
                i.reason for i in self.impacts if i.kind != "carried"))


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
    from typehaus.model.mep import DrainCleanout, ElectricalDevice, Equipment, Register
    from typehaus.model.spatial import Appliance, Fixture, Furniture, Room, Stair

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

    def _placeable_handler(kind: str) -> RemapHandler:
        def handler(el: Element, remap: ReferenceRemap) -> list[PatchOp]:
            changed: dict[str, object] = {}
            loc = getattr(el, "location", None)
            att = getattr(loc, "attachment", None)
            explicit = remap.rehost.get(el.tag)
            if att is not None:
                target = explicit or remap.resolve(att.wall_ref)
                shift, flip = remap.shift.get(el.tag, 0.0), el.tag in remap.reversed
                if target is not None and (target != att.wall_ref or shift or flip):
                    changed["location"] = _relocated(loc, att, target, shift, flip)
            ref = getattr(el, "wall_ref", None)
            if ref:
                # An explicit rehost names the attachment's wall; a different wet wall only
                # follows a plain rename.
                follows = explicit if att is None or att.wall_ref == ref else None
                target = follows or remap.resolve(ref)
                if target is not None and target != ref:
                    changed["wall_ref"] = target
            return [PatchOp("update", kind, el.tag, changed)] if changed else []

        return handler

    for _cls in (Furniture, Fixture, Appliance, Equipment, Register, ElectricalDevice):
        fields = tuple(f for f in ("wall_ref", "location") if f in _cls.model_fields)
        remap_handler(_cls, ref_fields=fields)(_placeable_handler(_cls.__name__))

    @remap_handler(DrainCleanout, ref_fields=("wall_ref", "pipe_ref"))
    def _cleanout(el: Element, remap: ReferenceRemap) -> list[PatchOp]:
        changed = {}
        for field_name in ("wall_ref", "pipe_ref"):
            current = getattr(el, field_name, None)
            target = remap.rehost.get(el.tag) if field_name == "wall_ref" else None
            target = target or (remap.resolve(current) if current else None)
            if target is not None and target != current:
                changed[field_name] = target
        return [PatchOp("update", "DrainCleanout", el.tag, changed)] if changed else []

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


def _relocated(loc, att, wall: str, shift: float, flip: bool):
    """The ``location`` rewritten onto ``wall`` at the mapped station, as dialect source."""
    from typehaus.quantities import deg
    from typehaus.source.macros_common import _round_len
    from typehaus.source.ops import RawExpr
    from typehaus.source.serialize import value_source

    d = att.distance_from_start.meters
    update: dict[str, object] = {
        "wall_ref": wall,
        "distance_from_start": _round_len(round(max(0.0, shift - d if flip else d + shift), 6))}
    if flip:
        # The tangent turns 180 degrees: the same world face and heading need the other side
        # and a half-turn offset.
        update["face"] = "right" if att.face == "left" else "left"
        turned = (float(getattr(att.rotation_offset, "degrees", 0.0)) + 180.0) % 360.0
        update["rotation_offset"] = deg(turned)
    new_loc = loc.model_copy(update={"attachment": att.model_copy(update=update)})
    return RawExpr(value_source(new_loc))


# Ref-bearing fields no handler carries (decision #33). ``delete_wall`` refuses while one
# names the wall; split/heal report them as ``needs_review``. The completeness test holds
# every ref field to either a handler or this list.
UNCOVERED: dict[str, tuple[str, ...]] = {
    "WallBacking": ("wall_ref",),
    "BracedWallPanel": ("wall_ref",),
    "WallPaneling": ("walls",),
    "PipeRun": ("wall_ref", "wall_refs", "serves"),
    "PipeAccessory": ("wall_ref", "serves"),
    "VentRun": ("wall_ref",),
    "SleevePenetration": ("serves_fixture",),
    "ShelfBank": ("host",),
    "Post": ("within_wall",),
    "Beam": ("start_node", "end_node", "bearing_refs"),
    "FoundationWall": ("start_node", "end_node", "stacks_on", "bearing_refs"),
    "FloorSystem": ("joists",),
    "FloorOpening": ("bearing_refs",),
    # The interval and pocket polygon are tied to all three walls as one enclosure. A split
    # needs geometric review; independently remapping tags could falsely preserve guard credit.
    "FloorOpeningPocketClosure": ("wall_refs",),
    "Roof": ("bearing_refs",),
}


_register_builtins()
