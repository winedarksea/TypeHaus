"""What a guard weighs, and whether the thing under it can carry that.

A guard does not have to be a stick railing. A masonry parapet standing at a porch edge is
the same fixture in code terms — R312.1's guard — and it is authored here as a ``Wall`` with
``guard=True`` rather than as a ``Railing``, because reducing it to posts and rails would
strip its four-layer stucco/CMU/air/brick stack, orphan the post bases grouted into its
cores, and drop its masonry volume out of the cubic-yard take-off.

What that costs is a load path nobody was asking about. A 42" grouted-CMU-and-brick parapet
runs about 420 plf; a wood deck rim designed to R507's 40 psf live + 10 psf dead cannot
carry that, and the model had no rule that would ever say so.

The load is derived from the guard's *own* assembly — every layer's thickness times its
material's density, times the guard's height — rather than from a magic number, so a lighter
guard prices itself out of the finding automatically and a heavier one prices itself in.
Air gaps carry nothing and are skipped; a solid layer whose material states no ``density``
makes the whole answer UNKNOWN, because a load computed from a partial stack is not a load.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import not_applicable as _not_applicable
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.elements import Wall
from typehaus.model.enums import LayerFunction

_CHECK_ID = "structural.masonry_guard_bearing"

#: kg/m -> lb/ft. 1 kg = 2.20462 lb over 1 m = 3.280840 ft.
_KG_PER_M_TO_PLF = 2.2046226218 / 3.2808398950

#: A support's top is "under" the guard when the two are this close in Z. Same slop the
#: rest of the stacking logic uses — a storey's walls land exactly on the one below.
_BEARING_Z_TOL_M = 0.05
#: How far off a support's own axis the guard's line may sit and still bear on it. Half the
#: support's thickness plus this: a guard is aligned to a face, not to a centreline.
_BEARING_PLAN_TOL_M = 0.10
#: Stations along the guard's run, so a guard that starts on a wall and ends over a deck is
#: read as what it is rather than as whichever support happened to be found first.
_STATION_STEP_M = 0.25

#: Material hatch families that carry a masonry guard without further thought. ``concrete``
#: is the catalog's family for both poured concrete and masonry units (cmu, brick all hatch
#: concrete), which is the distinction that matters here — they are all hard bearing.
_HARD_SUPPORT_HATCHES = frozenset({"concrete", "masonry", "metal"})


@check(Tier.STRUCTURAL, _CHECK_ID)
def masonry_guard_bearing(ctx: CheckContext) -> list[Finding]:
    """A guard wall's dead load lands on something that can carry it.

    One finding per ``guard=True`` wall. PASS where every station of its run stands on
    concrete, masonry, steel or a footing, or where the derived load is under the house's
    ``max_guard_dead_load_on_wood_plf`` allowance whatever it stands on. FAIL where a heavy
    guard stands on wood framing. UNKNOWN — never PASS — where a layer states no density or
    no support can be identified under some part of the run.
    """
    guards = [element for element in ctx.plan.all_elements()
              if isinstance(element, Wall) and element.guard]
    if not guards:
        # N/A, not UNKNOWN: the plan was read and states positively that no wall is a
        # guard. There is no missing input here and nothing for anyone to author.
        return [_not_applicable(_CHECK_ID, "no wall in the plan is marked as a guard "
                                "(Wall.guard); a stick guard is graded by "
                                "structural.deck_guard and code.R312_1_guard_height "
                                "instead")]
    allowance = ctx.preferences.structural.max_guard_dead_load_on_wood_plf
    out: list[Finding] = []
    for element in guards:
        wall = next((w for w in ctx.model.walls if w.tag == element.tag), None)
        if wall is None:
            out.append(_unknown(_CHECK_ID, f"guard wall {element.tag} resolved no geometry, "
                                "so neither its weight nor its support can be read",
                                (element.tag,)))
            continue
        out.append(_grade(ctx, element.tag, wall, allowance))
    return out


def _grade(ctx: CheckContext, tag: str, wall, allowance_plf: float) -> Finding:
    height_m = wall.z1_m - wall.z0_m
    load_plf = _dead_load_plf(ctx, wall, height_m)
    if load_plf is None:
        return _unknown(_CHECK_ID, f"guard wall {tag} has a solid layer whose material "
                        "states no density, so its dead load cannot be derived", (tag,))
    supports = _supports_along(ctx, wall)
    named = sorted({name for _kind, name in supports if name})
    if any(kind is None for kind, _name in supports):
        return _unknown(_CHECK_ID, f"guard wall {tag} carries {load_plf:.0f} plf but part "
                        "of its run has nothing modeled under it at its base elevation, so "
                        "what it bears on cannot be identified", (tag,))
    if load_plf <= allowance_plf + 1e-9:
        return _advisory(_CHECK_ID, f"guard wall {tag} weighs {load_plf:.0f} plf, at or "
                         f"under the {allowance_plf:.0f} plf ordinary wood framing carries; "
                         "its support does not have to be hard", (tag,), Result.PASS)
    soft = sorted({name for kind, name in supports if kind == "wood"})
    if soft:
        return _advisory(
            _CHECK_ID,
            f"guard wall {tag} puts {load_plf:.0f} plf of dead load on wood framing "
            f"({', '.join(soft)}), over the {allowance_plf:.0f} plf allowance",
            (tag, *soft), Result.FAIL,
            fix_hint=("carry the guard on a concrete or masonry bearing line, or author a "
                      "lighter guard (a stick Railing rather than a masonry parapet)"))
    return _advisory(
        _CHECK_ID,
        f"guard wall {tag} weighs {load_plf:.0f} plf and bears on "
        f"{', '.join(named) or 'hard support'} the length of its run",
        (tag, *named), Result.PASS)


def _dead_load_plf(ctx: CheckContext, wall, height_m: float) -> float | None:
    """``Σ(layer thickness × material density) × height``, in pounds per lineal foot.

    Air gaps are skipped rather than treated as missing data — a cavity is not a layer whose
    density nobody stated, it is a layer with no material in it.
    """
    mass_per_area = 0.0
    materials = {material.tag: material for material in ctx.plan.library.materials}
    for layer in wall.depth_layers():
        if layer.function in (LayerFunction.AIRGAP.value, "air_gap"):
            continue
        material = materials.get(layer.material_ref or "")
        density = getattr(material, "density", None)
        if density is None:
            return None
        mass_per_area += layer.thickness_m * density
    return mass_per_area * height_m * _KG_PER_M_TO_PLF


def _supports_along(ctx: CheckContext, wall) -> list[tuple[str | None, str | None]]:
    """``(kind, name)`` under each station of the guard's run, walked base to tip.

    ``kind`` is ``"hard"`` (concrete, masonry, steel, a footing), ``"wood"`` (a framed floor
    deck), or ``None`` where nothing is modeled under that station.
    """
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0)
    steps = max(int(math.ceil(run / _STATION_STEP_M)), 1)
    out: list[tuple[str | None, str | None]] = []
    for index in range(steps + 1):
        t = index / steps
        out.append(_support_at(ctx, wall, (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)))
    return out


def _support_at(ctx: CheckContext, wall, point) -> tuple[str | None, str | None]:
    from shapely.geometry import LineString, Point, Polygon

    base = wall.z0_m
    probe = Point(point)
    for other in ctx.model.walls:
        if other.tag == wall.tag or abs(other.z1_m - base) > _BEARING_Z_TOL_M:
            continue
        reach = other.thickness_m / 2.0 + _BEARING_PLAN_TOL_M
        if LineString(other.axis).distance(probe) > reach:
            continue
        return (_wall_support_kind(ctx, other), other.tag)
    for solid in ctx.model.solids:
        if solid.category not in ("footing", "pad", "slab"):
            continue
        if abs(solid.z1_m - base) > _BEARING_Z_TOL_M or len(solid.outline) < 3:
            continue
        if Polygon(solid.outline).covers(probe):
            return ("hard", solid.tag)
    for floor in ctx.model.floors:
        if not floor.deck_outline or abs(floor.deck_z1_m - base) > _BEARING_Z_TOL_M:
            continue
        if Polygon(floor.deck_outline).covers(probe):
            return ("wood", floor.tag)
    return (None, None)


def _wall_support_kind(ctx: CheckContext, wall) -> str:
    """A supporting wall's bearing class, read off its structure layer's material hatch.

    The hatch family is the catalog's own answer to "what is this made of", and it is the
    one that separates hard bearing from framing: every masonry unit and every pour hatches
    ``concrete``, steel hatches ``metal``, and a stud wall's structure layer is lumber.
    """
    materials = {material.tag: material for material in ctx.plan.library.materials}
    for layer in wall.depth_layers():
        if layer.function != LayerFunction.STRUCTURE.value:
            continue
        hatch = getattr(materials.get(layer.material_ref or ""), "hatch", None)
        return "hard" if hatch in _HARD_SUPPORT_HATCHES else "wood"
    return "wood"
