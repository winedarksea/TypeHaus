"""One horizontal cut, every structure it crosses.

A ``Storey`` is a datum *within one building*, so five of catlin's structures hold a storey
at ``0'-0"``: the house's main floor, the garage deck, the porch, the north entry and the
yard pads. Every drawing in ``emit/draw`` filters ``element.storey == storey`` — 43 sites
across 17 modules — which made each of those five its own sheet, and left the main floor
plan with no porch on it. Nine plumbing plans is not a drawing set; it is a reader's problem.

Rather than teach 43 comparisons about datums (several of which compare two *elements* to
each other, and would break), this re-labels at the boundary: every element standing on the
level's datum is handed to the drawing code wearing the level's own storey tag. The existing
comparisons then do the right thing untouched.

**What the re-label loses, and why a drawing does not care.** The swapped tag carries two
other facts: the element's *building*, and its *datum*. A level may cross datums where a
storey authors ``level=`` (the garage bears its walls a foot below the house's deck and is
still the same floor plan), so a consumer that reads an elevation back off the tag would be
wrong by that foot. Verified: nothing in ``emit/draw`` does — the plan builders derive no
elevation from a storey tag, and ``sheets._storey_elevation`` is only ever asked about the
unrelabelled model. Geometry is already absolute by this stage, so nothing drawn moves.

The *building* is lost outright, so this must not be used where one matters: ``code.R302_5``
narrows its room list by building precisely to keep a garage wall reaching over the house
footprint from raising a fire-separation finding across four feet of outdoor air. Drawings
have no such question — a plan draws what the cut crosses — and ``checks/`` never calls this.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.emit.draw.scene import Scene
    from typehaus.resolve.model import ResolvedModel

T = TypeVar("T")


def model_at_level(model: ResolvedModel, primary: str) -> ResolvedModel:
    """``model`` with every element on ``primary``'s datum re-labelled to ``primary``.

    Returns the model itself when the level holds one storey, which is every storey of a
    one-building house — so a plan that never authored a second structure pays nothing and
    cannot be perturbed by this.
    """
    siblings = set(model.plan.level_of(primary)) - {primary}
    if not siblings:
        return model

    def relabel(item: Any) -> Any:
        if getattr(item, "storey", None) in siblings:
            item = dataclasses.replace(item, storey=primary)
        # A stair's far end is the same claim about the same plane.
        if getattr(item, "to_storey", None) in siblings:
            item = dataclasses.replace(item, to_storey=primary)
        return item

    changes: dict[str, Any] = {}
    for field in dataclasses.fields(model):
        collection = getattr(model, field.name, None)
        if not isinstance(collection, list) or not collection:
            continue
        if not dataclasses.is_dataclass(collection[0]):
            continue
        names = {f.name for f in dataclasses.fields(collection[0])}
        if "storey" not in names and "to_storey" not in names:
            continue
        changes[field.name] = [relabel(item) for item in collection]
    # ``copy.copy`` then assign: ResolvedModel is a mutable dataclass with fields that
    # ``replace()`` would demand as arguments (and a ``_tag_index`` it rebuilds itself).
    import copy

    out = copy.copy(model)
    for name, value in changes.items():
        setattr(out, name, value)
    # The index maps tag -> element *object*, and re-labelling made new objects. Left alone
    # it would hand ``by_tag`` the original, so a drawing would read one storey off the
    # element it filtered and another off the element it looked up.
    out.index_by_tag()
    return out


def at_level(build: Any, primary: str, **kwargs: Any) -> Any:
    """A ``SceneFn`` that draws ``primary``'s whole level rather than its storey alone.

    Carries ``func``/``keywords`` the way the ``functools.partial`` it replaces did, so that
    "which builder does this sheet use" stays an answerable question — the one thing
    ``test_sheet_index`` asserts to keep S-100 and S-101 from quietly aliasing the floorplan.
    """

    def scene(model: ResolvedModel) -> Scene:
        return build(model_at_level(model, primary), storey=primary, **kwargs)

    scene.func = build          # type: ignore[attr-defined]
    scene.keywords = {"storey": primary, **kwargs}  # type: ignore[attr-defined]
    return scene
