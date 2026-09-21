"""What a wall LINE weighs, per lineal foot — the one reading a check and a calc share.

``dead_load_plf`` moved here from ``checks/structural/masonry_load.py`` on 2026-09-20, and
the move is the point: ``engineering/pier_basis`` needs the same number to turn a wall
standing on a beam into a line load on the posts under it, and ``engineering`` may not
import ``checks`` (``tests/test_package_leaves.py`` walks the AST for exactly that, function
-local imports included). ``resolve`` is where a router, a check and a calculation may all
reach the same reading — the same argument ``resolve/mep_envelopes.py`` carries for what a
pipe occupies. A check that weighed a different wall from the one the pier calc loaded would
make the two impossible to reconcile, and `haus check` was already printing "guard wall
W-BW-SCREEN weighs 31 plf" in the same run that called that wall's load unknown.

**The load is derived from the assembly, never from a constant.** Every layer's thickness
times its material's density, times the height; a framed layer at its cavity fill's own
framing factor; a profiled sheet at its published ``areal_density_kg_m2``. A solid layer
whose material states neither makes the whole answer ``None``, because a load computed from
a partial stack is not a load — and ``None`` is the honest verdict a record then reports,
not a zero.

**And what STANDS on the line counts too.** :func:`wall_line_plf` adds what bears on the
wall through ``supported_by`` — catlin's ``SC-BW-WEST``, a slat clerestory on
``W-BW-SCREEN``'s top plate, is a third of that line's weight. An element standing there
that nothing here knows how to weigh returns ``None`` naming it, for the same reason a
material with no density does.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.enums import LayerFunction

#: kg/m -> lb/ft. 1 kg = 2.20462 lb over 1 m = 3.280840 ft.
KG_PER_M_TO_PLF = 2.2046226218 / 3.2808398950

#: Wood fraction of a framed layer that states no cavity fill to read one off. The field
#: default elsewhere in the engine for 16" o.c. studs with plates, corners and jamb packs.
_DEFAULT_FRAMING_FACTOR = 0.23
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




def wall_line_plf(ctx: Any, wall: Any) -> tuple[float | None, str]:
    """``(plf, basis)`` for a resolved wall's line — its own stack plus what stands on it.

    ``basis`` is prose for the record that consumes this, and it is written for both
    outcomes: where the answer is a number it says which assemblies it came from, and where
    it is ``None`` it names the thing that could not be weighed. A calculation reporting
    INCOMPLETE has to be able to say what is missing, and "the wall load is unknown" is not
    an answer anyone can act on.

    ** A LINE, NOT A WALL, AND THAT IS WHAT THE CONSUMER ACTUALLY WANTS. ** A beam under a
    wall carries everything above that wall too. catlin's ``BM-BW-SCSILL`` sits under
    ``W-BW-SCREEN``, and ``SC-BW-WEST`` — a 2'-4 3/4" slat clerestory — stands on that wall's
    top plate through ``supported_by``. Weighing the wall alone understates the sill's load
    by 30%, which is the same partial-stack failure ``dead_load_plf`` refuses one layer down.
    """
    height_m = wall.z1_m - wall.z0_m
    own = dead_load_plf(ctx, wall, height_m)
    if own is None:
        return None, (f"{wall.tag} states no weight: a layer in its assembly names a "
                      f"material with neither a density nor an areal density, and a load "
                      f"computed from a partial stack is not a load")
    parts = [f"{wall.tag} {own:.2f} plf over its {height_m / 0.3048:.2f}' height"]
    total = own
    for tag, plf, why in _standing_on(ctx, wall.tag):
        if plf is None:
            return None, f"{tag} stands on {wall.tag} and {why}"
        total += plf
        parts.append(f"{tag} {plf:.2f} plf ({why})")
    return total, "; ".join(parts)


def _standing_on(ctx: Any, wall_tag: str) -> list[tuple[str, float | None, str]]:
    """``(tag, plf, why)`` for every element bearing on this wall line, in tag order.

    Only the element families that are LINES on this line: another wall stacked on it, and a
    slat screen standing on its plate. Anything else that names this wall in ``supported_by``
    is reported unweighed — a point load standing on a wall is a different question from a
    line load and inventing a plf for it would be a fabricated demand.
    """
    from typehaus.model.elements import Wall
    from typehaus.model.screens import SlatScreen

    resolved = {w.tag: w for w in ctx.model.walls}
    out: list[tuple[str, float | None, str]] = []
    for element in sorted(ctx.plan.all_elements(), key=lambda e: getattr(e, "tag", "")):
        if getattr(element, "supported_by", None) != wall_tag:
            continue
        if isinstance(element, Wall):
            above = resolved.get(element.tag)
            if above is None:
                out.append((element.tag, None, "resolves to no wall this can weigh"))
                continue
            height_m = above.z1_m - above.z0_m
            plf = dead_load_plf(ctx, above, height_m)
            out.append((element.tag, plf,
                        f"stacked wall over {height_m / 0.3048:.2f}'"
                        if plf is not None else "names a material with no density"))
        elif isinstance(element, SlatScreen):
            out.append(_slat_screen_plf(ctx, element))
        else:
            out.append((getattr(element, "tag", "?"), None,
                        f"is a {type(element).__name__} this module cannot weigh as a line "
                        f"load; a plf invented for it would be a fabricated demand"))
    return out


def _slat_screen_plf(ctx: Any, screen: Any) -> tuple[str, float | None, str]:
    """One slat clerestory's weight per foot of the line it stands on.

    ** THE COUNT IS ``resolve/screens.py``'s OWN, IMPORTED. ** The slats it draws are the
    slats there are, and a second count rule here would be a second answer — the margin and
    the pitch are not obvious enough to restate. The section is ``slat_face x slat_depth``
    over ``height``, and the material is the assembly's structure layer, exactly as the
    solids the resolver appends are coloured and hatched.
    """
    import math

    from typehaus.resolve.assembly_material import assembly_structure_material
    from typehaus.resolve.screens import slat_count

    x0, y0 = screen.start.xy_m
    x1, y1 = screen.end.xy_m
    length_m = math.hypot(x1 - x0, y1 - y0)
    count = slat_count(screen)
    if length_m <= 0.0 or count <= 0:
        return screen.tag, None, "resolves to no slats"
    materials = {m.tag: m for m in ctx.plan.library.materials}
    ref = assembly_structure_material(ctx.plan, getattr(screen, "assembly", None))
    density = getattr(materials.get(ref or ""), "density", None)
    if density is None:
        return (screen.tag, None,
                f"is built of `{ref or 'an unnamed material'}`, which states no density")
    volume_m3 = (count * screen.slat_face.meters * screen.slat_depth.meters
                 * screen.height.meters)
    plf = volume_m3 * density / length_m * KG_PER_M_TO_PLF
    return (screen.tag, plf,
            f"{count} slats of {screen.slat_face.inches:.2f}\" x "
            f"{screen.slat_depth.inches:.2f}\" x {screen.height.meters / 0.3048:.2f}' in "
            f"{ref} at {density:.0f} kg/m3, over {length_m / 0.3048:.2f}'")
