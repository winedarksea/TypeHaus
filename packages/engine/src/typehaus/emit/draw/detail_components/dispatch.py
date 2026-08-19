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
from typehaus.emit.draw.detail_components.geometry import condition_opening, condition_walls
from typehaus.emit.draw.detail_components.opening import (
    concrete_opening_bucks,
    humid_liner_opening_return,
    sauna_liner_opening_return,
    window_head_jamb_sill,
)
from typehaus.emit.draw.detail_components.ridge import lvl_ridge_hanger
from typehaus.emit.draw.detail_components.sauna import sauna_components
from typehaus.emit.draw.detail_components.shower import shower_components
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


def _recipe_window_head_jamb_sill(model, context) -> list[IRNode]:
    """Framed weather-wall opening: head flashing + sill pan (also the garage door head)."""
    if context.opening is None:
        return []
    wall = next((w for w in context.walls if not w.is_foundation), None)
    if wall is None:
        return []
    return window_head_jamb_sill(model, wall, context.opening, context.crop,
                                 context.direction, context.station)


def _recipe_concrete_opening(model, context) -> list[IRNode]:
    """Opening cast into concrete (interior door, basement window): treated buck + sealant."""
    if context.opening is None:
        return []
    wall = next((w for w in context.walls if w.is_foundation), context.walls[0]
                if context.walls else None)
    if wall is None:
        return []
    return concrete_opening_bucks(model, wall, context.opening, context.crop,
                                  context.direction, context.station)


def _recipe_sauna_liner_opening(model, context) -> list[IRNode]:
    if context.opening is None or not context.walls:
        return []
    return sauna_liner_opening_return(model, context.walls[0], context.opening,
                                      context.crop, context.direction, context.station)


def _recipe_humid_liner_opening(model, context) -> list[IRNode]:
    if context.opening is None or not context.walls:
        return []
    return humid_liner_opening_return(model, context.walls[0], context.opening,
                                      context.crop, context.direction, context.station)


def _recipe_lvl_ridge_hanger(model, context) -> list[IRNode]:
    return lvl_ridge_hanger(model, context.roof, context.crop, context.direction,
                            context.station)


#: overlay id → recipe. Every id Catlin authors that has drawable vocabulary appears here.
OVERLAY_RECIPES = {
    "zero-overhang-eave": _recipe_zero_overhang_eave,
    "basement-framed-wall": _recipe_basement_framed_wall,
    "rim-band-air-seal": _recipe_rim_band_air_seal,
    "stack-width-shelf": _recipe_stack_width_shelf,
    "window-head-jamb-sill": _recipe_window_head_jamb_sill,
    "garage-opening": _recipe_window_head_jamb_sill,
    "concrete-opening": _recipe_concrete_opening,
    "foundation-window": _recipe_concrete_opening,
    "sauna-liner-opening": _recipe_sauna_liner_opening,
    "humid-liner-opening": _recipe_humid_liner_opening,
    "lvl-ridge-hanger": _recipe_lvl_ridge_hanger,
}


#: Authored overlay ids that deliberately draw nothing, and why. Recorded rather than
#: omitted so the gap is a decision on the record instead of an apparent oversight.
#: (Conditions that warrant no detail *sheet at all* — not just no applied vocabulary —
#: are handled upstream by ``Transition.suppress`` instead of an entry here.)
UNDRAWN_RECIPES = {
    "interior-opening": (
        "an interior door sheds no weather and controls no vapour, so there is no applied "
        "vocabulary (no flashing, no pan, no sealant) at its perimeter; the head and jamb "
        "casing that does exist is authored trim, and duplicating it here would double-draw"
    ),
    "bearing-partition-opening": (
        "the header carrying the bearing line over the opening is real framing the cut "
        "already draws; an interior bearing opening takes nothing applied beyond it, so "
        "any extra linework would describe a building that does not exist"
    ),
}


class _RecipeContext:
    """The resolved inputs every recipe reads: the crop, the cut, and what is in it."""

    __slots__ = ("crop", "direction", "station", "walls", "condition", "opening", "roof")

    def __init__(self, crop, direction, station, walls, condition, opening=None,
                 roof=None):
        self.crop = crop
        self.direction = direction
        self.station = station
        self.walls = walls
        self.condition = condition
        self.opening = opening
        self.roof = roof


def build_overlay_components(model, derived) -> list[IRNode]:
    """Dispatch this detail's overlay recipe, then the assembly/fixture-driven vocabulary.

    Sauna components are not keyed on an overlay id: the liner rides on whichever junction
    its wall happens to appear in (a foundation detail, a stack detail, an assembly change),
    so it is selected by the *assembly* in the cut rather than by the recipe. It self-gates on
    the sauna floor slab being in frame, so a wall-top crop gets nothing. Shower components
    gate the same way off the shower *fixture* being in the cut — a shower has no assembly
    of its own to key on.
    """
    transition = getattr(derived, "transition", None)
    crop_points = derived.view.crop
    if crop_points is None:
        return []
    crop = (crop_points[0].xy_m, crop_points[1].xy_m)
    walls = condition_walls(model, derived.condition)
    opening = condition_opening(model, derived.condition)
    roof = next((r for r in model.roofs if r.tag in derived.condition.element_tags), None)
    context = _RecipeContext(crop, derived.direction, derived.station, walls,
                             derived.condition, opening=opening, roof=roof)

    nodes: list[IRNode] = []
    overlay = getattr(transition, "overlay", None) if transition is not None else None
    recipe = OVERLAY_RECIPES.get(overlay) if overlay else None
    if recipe is not None:
        nodes += recipe(model, context)

    sauna_walls = [w for w in walls if "SAUNA" in (w.assembly or "")]
    if sauna_walls:
        nodes += sauna_components(model, sauna_walls, crop, derived.direction,
                                  derived.station)
    nodes += shower_components(model, crop, derived.direction, derived.station)
    return nodes
