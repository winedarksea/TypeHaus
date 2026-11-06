"""Which detail key each boundary condition derives under.

``emit/draw/detail_derive`` scaffolds one detail per key, and the transition-binding checks
grade the same keys, so both read them here.
"""

from __future__ import annotations

from typehaus.resolve.model import BoundaryCondition, ResolvedModel


def _condition_opening(model: ResolvedModel, cond: BoundaryCondition):
    """The opening an ``opening_perimeter`` condition names (its tag is the opening's)."""
    tags = set(cond.element_tags)
    return next((o for o in model.openings if o.tag in tags), None)


def _opening_class(model: ResolvedModel, cond: BoundaryCondition) -> str | None:
    """``"window"`` or ``"door"`` for an opening condition; ``None`` for a bare rough opening."""
    opening = _condition_opening(model, cond)
    if opening is None:
        return None
    if opening.kind == "window":
        return "window"
    return "door" if opening.is_door else None


def opening_kind_key(key: str, kind: str) -> str:
    """The detail key of an opening key's minority kind: ``opening_perimeter:door:EXT_2X6``.

    Qualified the way a storey stack is (``storey_stack:rim:A|B``), so the title still
    reads the assembly after the last colon and a note can scope ``{*:door:*}``."""
    prefix, _, bound = key.partition(":")
    return f"{prefix}:{kind}:{bound}"


def detail_keys(model: ResolvedModel) -> list[tuple[BoundaryCondition, str, str | None]]:
    """Each condition with its detail key and split kind, typical kind first.

    An opening key that holds both windows and doors yields a detail per kind (O4-103,
    O5-103): the TYPICAL kind keeps the plain key, and the other is qualified
    (``opening_kind_key``), so the B&B entry door and the garage windows each get a sheet
    and a note set of their own. Windows are typical only where they outnumber the rest;
    a bare rough opening rides with the typical kind. The split kind (``"window"`` /
    ``"door"``) is set on both halves of a split key, so both sheet titles name it.
    """
    classes: dict[int, str | None] = {}
    by_key: dict[str, list[str | None]] = {}
    for index, cond in enumerate(model.conditions):
        if cond.kind.value == "opening_perimeter":
            classes[index] = _opening_class(model, cond)
            by_key.setdefault(cond.key, []).append(classes[index])
    typical = {key: "window" if 2 * flags.count("window") > len(flags) else "door"
               for key, flags in by_key.items()}
    mixed = {key for key, flags in by_key.items() if {"window", "door"} <= set(flags)}

    def key_of(index: int, cond: BoundaryCondition) -> tuple[BoundaryCondition, str, str | None]:
        if cond.key not in mixed:
            return cond, cond.key, None
        kind = classes.get(index) or typical[cond.key]
        if kind != typical[cond.key]:
            return cond, opening_kind_key(cond.key, kind), kind
        return cond, cond.key, kind

    # The first condition of a key is the opening its detail draws: a typical window first,
    # then any unit before a bare rough opening (A-520 drew a leafless passage, O1-104).
    order = sorted(range(len(model.conditions)), key=lambda i: (not (
        classes.get(i) == "window" and typical.get(model.conditions[i].key) == "window"),
        model.conditions[i].kind.value == "opening_perimeter" and classes.get(i) is None))
    return [key_of(i, model.conditions[i]) for i in order]
