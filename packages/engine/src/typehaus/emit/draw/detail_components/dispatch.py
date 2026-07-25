"""``Transition.overlay`` recipe id → detail component vocabulary.

An overlay id (``zero-overhang-eave``, ``basement-framed-wall``, ``rim-band-air-seal``,
``stack-width-shelf`` …) is authored on a ``Transition`` in the house's plan source. This
module is where those ids stop being inert strings printed in a title block and start
selecting what gets drawn: it is the single dispatch point for the whole per-detail
vocabulary, and every recipe below hangs off it.

Two rules keep the registry honest:

* **A recipe is read-only.** It receives the resolved model and the derived detail and
  returns IR nodes. It never touches construction geometry, so an overlay id can never
  change the building — only what the drawing says about it.
* **An id with no honest vocabulary gets no entry.** ``UNDRAWN_RECIPES`` records those, with
  the reason, rather than leaving a silent gap that reads as an oversight. Inventing linework
  for a junction the cut plane does not actually contain would be a drawing that lies.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.eave import zero_overhang_eave
from typehaus.emit.draw.detail_components.sauna import sauna_components
from typehaus.emit.draw.detail_components.stack import rim_band_air_seal, stack_width_shelf
from typehaus.emit.draw.detail_components.wall_base import basement_framed_wall
from typehaus.emit.draw.scene import IRNode


def _recipe_zero_overhang_eave(model, context) -> list[IRNode]:
    """Eave: prefer the framed wall carrying the roof; a foundation wall never has an eave."""
    wall = next((w for w in context.walls if not w.is_foundation), None)
    if wall is None:
        return []
    return zero_overhang_eave(model, wall, context.crop, context.direction, context.station)


def _recipe_basement_framed_wall(model, context) -> list[IRNode]:
    framed = next((w for w in context.walls if not w.is_foundation), None)
    concrete = next((w for w in context.walls if w.is_foundation), None)
    if framed is None:
        return []
    return basement_framed_wall(model, framed, concrete, context.crop, context.direction,
                                context.station)


def _recipe_rim_band_air_seal(model, context) -> list[IRNode]:
    return rim_band_air_seal(model, context.walls, context.crop, context.direction,
                             context.station)


def _recipe_stack_width_shelf(model, context) -> list[IRNode]:
    return stack_width_shelf(model, context.walls, context.crop, context.direction,
                             context.station)


#: overlay id → recipe. Every id Catlin authors that has drawable vocabulary appears here.
OVERLAY_RECIPES = {
    "zero-overhang-eave": _recipe_zero_overhang_eave,
    "basement-framed-wall": _recipe_basement_framed_wall,
    "rim-band-air-seal": _recipe_rim_band_air_seal,
    "stack-width-shelf": _recipe_stack_width_shelf,
}


#: Authored overlay ids that deliberately draw nothing, and why. Recorded rather than
#: omitted so the gap is a decision on the record instead of an apparent oversight.
UNDRAWN_RECIPES = {
    "assembly-change-jog": (
        "the jog happens *along* the wall run, while the derived detail cuts perpendicular "
        "to the wall at its midpoint — the change of assembly is simply not in this cut "
        "plane, so any linework here would describe a junction the drawing does not show"
    ),
    "window-head-jamb-sill": (
        "opening_perimeter conditions derive no detail slice (details.derive_detail_slices "
        "requires a host wall and a junction elevation); until an opening detail is "
        "scaffolded there is no crop for head/jamb/sill vocabulary to land in"
    ),
    "concrete-opening": "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "foundation-window": "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "concrete-arch": "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "garage-opening": "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "interior-opening": "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "bearing-partition-opening":
        "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "sauna-liner-opening":
        "see window-head-jamb-sill — no opening detail is scaffolded yet",
    "lvl-ridge-hanger": (
        "roof_ridge conditions carry no wall, so no detail slice is derived; the ridge is "
        "documented by the authored SL-D-RIDGE slice instead"
    ),
}


class _RecipeContext:
    """The resolved inputs every recipe reads: the crop, the cut, and the walls in it."""

    __slots__ = ("crop", "direction", "station", "walls", "condition")

    def __init__(self, crop, direction, station, walls, condition):
        self.crop = crop
        self.direction = direction
        self.station = station
        self.walls = walls
        self.condition = condition


def build_overlay_components(model, derived) -> list[IRNode]:
    """Dispatch this detail's overlay recipe, then the assembly-driven sauna vocabulary.

    Sauna components are not keyed on an overlay id: the liner rides on whichever junction
    its wall happens to appear in (a foundation detail, a stack detail, an assembly change),
    so it is selected by the *assembly* in the cut rather than by the recipe. It self-gates on
    the sauna floor slab being in frame, so a wall-top crop gets nothing.
    """
    transition = getattr(derived, "transition", None)
    crop_points = derived.view.crop
    if crop_points is None:
        return []
    crop = (crop_points[0].xy_m, crop_points[1].xy_m)
    walls = [w for w in (model.wall(t) for t in derived.condition.element_tags)
             if w is not None]
    context = _RecipeContext(crop, derived.direction, derived.station, walls,
                             derived.condition)

    nodes: list[IRNode] = []
    overlay = getattr(transition, "overlay", None) if transition is not None else None
    recipe = OVERLAY_RECIPES.get(overlay) if overlay else None
    if recipe is not None:
        nodes += recipe(model, context)

    sauna_walls = [w for w in walls if "SAUNA" in (w.assembly or "")]
    if sauna_walls:
        nodes += sauna_components(model, sauna_walls, crop, derived.direction,
                                  derived.station)
    return nodes
