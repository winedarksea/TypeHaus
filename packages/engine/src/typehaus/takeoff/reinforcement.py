"""Reinforcing steel, in pounds — the quantity that had only ever ridden inside a $/cy rate.

Rebar reached the estimate as an invisible component of the ``[concrete]`` and
``[wall_structure]`` cubic-yard rates: roughly five tons of it, ordered by nobody, checkable
against nothing. This bills it as its own line, one row per ``(bar, coating, scope)``.

**THE LOAD-BEARING RULE: the BOM bills only what a house AUTHORED, never what the engineering
suite designed.** ``engineering/`` sizes the steel and grades the authored schedule against
it; the house authors; this bills the authored spec. The alternative — billing the suite's
answer — would make a ``BASIS_VERSION`` bump move the estimate, which is exactly the failure
the engineering fingerprint exists to prevent, arriving through the money door. It is also
why this module imports ``model`` and never ``engineering``.

A pour that authors no reinforcement therefore contributes NOTHING here, and that is a
*hole* rather than a zero: ``checks/structural`` is where it gets reported, because a takeoff
row that silently reads 0 lb is indistinguishable from a pour that genuinely has no steel.

**Bars are not resolved as elements or solids.** Doing so would drag steel into IFC,
``emit/trades``, ``tasks`` and the framing-takeoff coverage gate — tripling the change for no
quantity gain. A bar is a quantity, not a thing the viewer draws.

**Lengths are NET.** Laps and splices ride in ``[waste]``, and chairs, bolsters and tie wire
ride inside the $/lb rate. Both are stated in the price file's basis note, because a quantity
that carries its own waste and a waste table that adds more is the double-count
``cli/price_file.py`` already raises a hard error over.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.enums import LayerFunction
from typehaus.model.rebar import BARS
from typehaus.resolve.concrete import concrete_spec_for
from typehaus.takeoff.envelope import wall_layer_net_area_m2, wall_net_areas_m2

_M2_TO_FT2 = 10.763910416709722
_M_TO_FT = 1.0 / 0.3048

#: Roles whose bars lie in the plane of a horizontal member (a footing mat, a slab mat).
_MAT_ROLES = ("top-x", "top-y", "bottom-x", "bottom-y")
#: Roles whose bars lie in the plane of a wall face.
_WALL_ROLES = ("vertical", "horizontal")


def reinforcement_takeoff(model: Any) -> list[dict[str, object]]:
    """One row per ``(bar, coating, scope)``, carrying length, weight, bar count and tags.

    ``scope`` is the member family — "foundation wall", "footing", "pad", "slab", "column" —
    and is part of the key rather than a label because a #5 in a footing mat and a #5 in a
    column cage are the same steel bought for two different operations, and an estimator
    prices the placing labour of the two differently even where the mill price is one number.
    """
    rows: dict[tuple[str, str, str], dict[str, object]] = {}
    plan = model.plan

    net_areas = wall_net_areas_m2(model)
    for wall in model.walls:
        element = plan.by_tag(wall.tag)
        spec = getattr(element, "reinforcement", None)
        if spec is None:
            continue
        area_m2 = _wall_structure_area_m2(model, wall, net_areas)
        if area_m2 <= 0.0:
            continue
        scope = "foundation wall" if wall.is_foundation else "wall"
        coating = _pour_coating(plan, element)
        for entry in spec.bars:
            _add(rows, entry, coating, scope, wall.tag,
                 _spaced_length_ft(entry, area_m2 * _M2_TO_FT2))

    for solid in model.solids:
        element = plan.by_tag(solid.tag)
        spec = getattr(element, "reinforcement", None) if element is not None else None
        if spec is None:
            continue
        coating = _pour_coating(plan, element)
        if solid.category == "column":
            for entry in spec.bars:
                _add(rows, entry, coating, "column", solid.tag,
                     _cage_length_ft(entry, spec, solid))
            continue
        area_ft2 = _plan_area_ft2(solid)
        for entry in spec.bars:
            _add(rows, entry, coating, solid.category, solid.tag,
                 _spaced_length_ft(entry, area_ft2))

    out: list[dict[str, object]] = []
    for key in sorted(rows):
        row = rows[key]
        length_ft = round(float(row["length_ft"]), 1)
        weight = BARS[int(str(key[0]).lstrip("#"))].weight_plf
        tags = row["tags"]
        assert isinstance(tags, list)
        out.append({**row, "length_ft": length_ft,
                    "weight_lb": round(length_ft * weight, 1),
                    "tags": sorted(set(tags))})
    return out


def _wall_structure_area_m2(model: Any, wall: Any, net_areas: dict[str, float]) -> float:
    """The net face area of the wall's monolithic STRUCTURE layers.

    Read through the same helper ``wall_structure`` and ``envelope_layers`` use, so the steel,
    the concrete it sits in and the coverings over it cannot disagree about how big the wall
    is. Net of openings, which is what "bill net" means here: a bar does not run through a
    window, and the trim bars that frame one are detailing this schema does not carry.
    """
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    if assembly is None:
        return 0.0
    authored = {layer.name: layer for layer in assembly.layers}
    total = 0.0
    for resolved in wall.layers:
        if resolved.function != LayerFunction.STRUCTURE.value:
            continue
        layer = authored.get(resolved.name)
        if layer is None or layer.concrete is None:
            continue
        total += max(0.0, wall_layer_net_area_m2(model, wall, resolved,
                                                 net_areas[wall.tag]))
    return total


def _plan_area_ft2(solid: Any) -> float:
    from typehaus.resolve.geometry import polygon_area

    net = abs(polygon_area(list(solid.outline))) - sum(
        abs(polygon_area(list(void))) for void in solid.voids)
    return max(0.0, net) * _M2_TO_FT2


def _spaced_length_ft(entry: Any, area_ft2: float) -> float:
    """``area / spacing``, which is the whole of it.

    A bar every ``s`` inches across a plane of area ``A`` is ``A/s`` of bar, whichever way it
    runs — the run length cancels. That is why one expression serves a wall's verticals, a
    wall's horizontals, a footing's transverse mat and a slab's mat alike, and why this
    module needs no per-role geometry beyond knowing which PLANE the bars lie in.

    ``dowels`` are deliberately not billed: a dowel's length is a lap into the pour below,
    and nothing in this model carries it. Billing it at the member's own height would be
    inventing a number.
    """
    if entry.role == "dowels" or entry.spacing is None:
        return 0.0
    if entry.role not in _MAT_ROLES and entry.role not in _WALL_ROLES:
        return 0.0
    spacing_ft = float(entry.spacing.inches) / 12.0
    if spacing_ft <= 0.0:
        return 0.0
    return area_ft2 / spacing_ft * max(1, entry.layers)


def _cage_length_ft(entry: Any, spec: Any, solid: Any) -> float:
    """A column cage: longitudinal bars run the height, ties wrap it at a spacing."""
    height_ft = max(0.0, solid.z1_m - solid.z0_m) * _M_TO_FT
    if entry.role == "vertical" and entry.count:
        return entry.count * height_ft * max(1, entry.layers)
    if entry.role == "ties" and entry.spacing is not None:
        spacing_ft = float(entry.spacing.inches) / 12.0
        if spacing_ft <= 0.0:
            return 0.0
        return math.ceil(height_ft / spacing_ft) * _tie_perimeter_ft(entry, spec, solid)
    return 0.0


def _tie_perimeter_ft(entry: Any, spec: Any, solid: Any) -> float:
    """One tie's length: the bar circle's circumference, cover taken off both faces.

    Read off the solid's plan bounding box rather than the ``Post.size`` string, because the
    resolver already had to decide what a ``"12 round"`` is and a second parse of the same
    text is a second answer waiting to differ. A round column resolves as a many-sided
    polygon whose bbox is its diameter either way.

    Hooks are not added. ACI 318-19 §25.7.2.3 asks for a seismic or a standard hook on every
    tie and that is real steel, but its length depends on a bend the model does not carry;
    it rides in ``[waste]`` with the laps, and the basis note says so.
    """
    xs = [p[0] for p in solid.outline]
    ys = [p[1] for p in solid.outline]
    side_in = min(max(xs) - min(xs), max(ys) - min(ys)) * _M_TO_FT * 12.0
    cover_in = float(spec.cover.inches) if spec.cover is not None else 1.5
    diameter_in = max(0.0, side_in - 2.0 * cover_in - BARS[entry.bar].diameter_in)
    return math.pi * diameter_in / 12.0


def _pour_coating(plan: Any, element: Any) -> str:
    """What the bar in this pour is coated with, from the pour's own ``ConcreteSpec``.

    The coating lives on the MIX, not on the schedule, because it is a property of the bar
    you buy for a pour and not of any one role in it — you do not order galvanized verticals
    and black ties for the same cage, and a house that tried would be specifying a corrosion
    cell. ``BarSpec.coating`` overrides it per role for the one case that is real: a dowel
    lapped into a black-bar pour below.
    """
    return getattr(concrete_spec_for(plan, element), "bar_coating", None) or ""


def _add(rows: dict[tuple[str, str, str], dict[str, object]], entry: Any, pour_coating: str,
         scope: str, tag: str, length_ft: float) -> None:
    if length_ft <= 0.0 or entry.bar not in BARS:
        return
    # "" rather than None where nothing states a coating, so ``cli/prices.candidate_keys``
    # TRUNCATES to the bare ``#6`` instead of building the key ``#6:None``, which is not a
    # key anybody would author.
    coating = entry.coating or pour_coating or ""
    key = (f"#{entry.bar}", coating, scope)
    row = rows.get(key)
    if row is None:
        row = rows[key] = {"bar": key[0], "coating": coating, "scope": scope,
                           "length_ft": 0.0, "count": 0, "tags": []}
    row["length_ft"] = float(row["length_ft"]) + length_ft
    row["count"] = int(row["count"]) + 1
    tags = row["tags"]
    assert isinstance(tags, list)
    tags.append(tag)
