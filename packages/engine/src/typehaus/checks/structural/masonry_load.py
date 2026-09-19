"""What a masonry wall weighs, and what is under it — the reading two checks share.

Extracted from ``checks/structural/guards.py``, which asked both questions of a parapet, the
moment ``checks/structural/through_deck.py`` needed the same two of a wall standing in a
floor deck. The question is the same either way and there must be one answer to it: a guard
and a fireplace pier that disagreed about what "bears on wood" means would be two rules
wearing one number.

The load is derived from the wall's *own* assembly — every layer's thickness times its
material's density, times the wall's height — rather than from a magic number, so a lighter
wall prices itself out of a finding automatically and a heavier one prices itself in. Air
gaps carry nothing and are skipped; a solid layer whose material states no ``density`` makes
the whole answer ``None``, because a load computed from a partial stack is not a load.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.enums import LayerFunction

#: kg/m -> lb/ft. 1 kg = 2.20462 lb over 1 m = 3.280840 ft.
KG_PER_M_TO_PLF = 2.2046226218 / 3.2808398950

#: A support's top is "under" the wall when the two are this close in Z. Same slop the rest
#: of the stacking logic uses — a storey's walls land exactly on the one below.
BEARING_Z_TOL_M = 0.05
#: How far off a support's own axis the wall's line may sit and still bear on it. Half the
#: support's thickness plus this: a wall is aligned to a face, not to a centreline.
BEARING_PLAN_TOL_M = 0.10
#: Wood fraction of a framed layer that states no cavity fill to read one off. The field
#: default elsewhere in the engine for 16" o.c. studs with plates, corners and jamb packs.
_DEFAULT_FRAMING_FACTOR = 0.23

#: Material hatch families that carry masonry without further thought. ``concrete`` is the
#: catalog's family for both poured concrete and masonry units (cmu, brick all hatch
#: concrete), which is the distinction that matters here — they are all hard bearing.
_HARD_SUPPORT_HATCHES = frozenset({"concrete", "masonry", "metal"})


def dead_load_plf(ctx: Any, wall: Any, height_m: float) -> float | None:
    """``Σ(layer thickness × material density) × height``, in pounds per lineal foot.

    Air gaps are skipped rather than treated as missing data — a cavity is not a layer whose
    density nobody stated, it is a layer with no material in it. ``None`` where any solid
    layer's material states neither a density nor an areal density.
    """
    mass_per_area = 0.0
    materials = {material.tag: material for material in ctx.plan.library.materials}
    # ``ResolvedLayer`` carries no ``framing``: the stud layout is a property of the AUTHORED
    # layer, and a cavity fill resolves as its own layer rather than as a field on its host.
    # So the framing factor is read back off the assembly, by layer name.
    assembly = next((a for a in getattr(ctx.plan.library, "assemblies", ())
                     if a.tag == getattr(wall, "assembly", None)), None)
    authored = {getattr(layer, "name", ""): layer
                for layer in (getattr(assembly, "layers", ()) if assembly else ())}
    for layer in wall.depth_layers():
        if layer.function in (LayerFunction.AIRGAP.value, "air_gap"):
            continue
        # A FRAMED layer is mostly cavity. Weighing a 2x4 stud layer as 3 1/2" of solid wood
        # over the whole wall face is the same overstatement a profiled sheet makes, and in
        # the same direction: it read a 31 plf screen panel at 67 and sent it looking for a
        # masonry bearing line. The framing factor is the cavity fill's own where one is
        # stated (it is the number that layer already uses for its R-value), and the 16" o.c.
        # field default otherwise. The fill itself is added at full area, because a batt or a
        # foam does occupy the whole cavity.
        source = authored.get(getattr(layer, "name", "") or "")
        if source is not None and getattr(source, "framing", None) is not None:
            fills = getattr(source, "cavity_fills", ()) or ()
            factor = next((f.framing_factor for f in fills
                           if getattr(f, "framing_factor", None) is not None),
                          _DEFAULT_FRAMING_FACTOR)
            material = materials.get(layer.material_ref or "")
            density = getattr(material, "density", None)
            if density is None:
                return None
            mass_per_area += layer.thickness_m * density * factor
            for fill in fills:
                fill_material = materials.get(getattr(fill, "material_ref", "") or "")
                fill_density = getattr(fill_material, "density", None)
                if fill_density is None:
                    return None
                thickness = getattr(fill, "thickness", None)
                mass_per_area += ((thickness.meters if thickness is not None
                                   else layer.thickness_m) * fill_density * (1.0 - factor))
            continue
        material = materials.get(layer.material_ref or "")
        # A profiled sheet states its own kg/m2 and that wins: its `thickness` is the depth
        # it occupies in the wall, not a depth of material (→ Material.areal_density_kg_m2).
        areal = getattr(material, "areal_density_kg_m2", None)
        if areal is not None:
            mass_per_area += areal
            continue
        density = getattr(material, "density", None)
        if density is None:
            return None
        mass_per_area += layer.thickness_m * density
    return mass_per_area * height_m * KG_PER_M_TO_PLF


def support_at(ctx: Any, wall: Any, point: tuple[float, float]) -> tuple[str | None, str | None]:
    """``(kind, name)`` under one station of ``wall``'s run, at its base elevation.

    ``kind`` is ``"hard"`` (concrete, masonry, steel, a footing), ``"wood"`` (a framed floor
    deck), or ``None`` where nothing is modeled under that station.
    """
    from shapely.geometry import LineString, Point, Polygon

    base = wall.z0_m
    probe = Point(point)
    for other in ctx.model.walls:
        if other.tag == wall.tag or abs(other.z1_m - base) > BEARING_Z_TOL_M:
            continue
        reach = other.thickness_m / 2.0 + BEARING_PLAN_TOL_M
        if LineString(other.axis).distance(probe) > reach:
            continue
        return (wall_support_kind(ctx, other), other.tag)
    for solid in ctx.model.solids:
        if solid.category not in ("footing", "pad", "slab"):
            continue
        if abs(solid.z1_m - base) > BEARING_Z_TOL_M or len(solid.outline) < 3:
            continue
        if Polygon(solid.outline).covers(probe):
            return ("hard", solid.tag)
    for floor in ctx.model.floors:
        if not floor.deck_outline or abs(floor.deck_z1_m - base) > BEARING_Z_TOL_M:
            continue
        if Polygon(floor.deck_outline).covers(probe):
            return ("wood", floor.tag)
    return (None, None)


def wall_support_kind(ctx: Any, wall: Any) -> str:
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
