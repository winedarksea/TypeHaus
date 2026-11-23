"""The weight on the house side of the court's cross-member: what restrains the side runs in
winter (free body §15j).

Contracting, the court is held by base friction toward each end of a section, and the
tension at a section through the side lines is the SMALLER of the two sides' friction
(rigid-plastic): ``min(mu W_house, mu W_far − 0.6 T)`` over the lines it crosses. The house
side of the strut is the governing one, and it is taken as an upper bound:

* the body's own footings and stems there (the spliced braced walls);
* their heel soil to the STEM TOP, not to grade, at the band's top — the excess over
  grade stands in for the porch, balcony and veneer dead those walls carry;
* any other cast wall bedded there and cast with them (the veneer beam), concrete only.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.engineering.retaining_system_body import (
    Body,
    _exterior,
    _poly,
    _stem,
    spliced_walls,
)
from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF, SOIL_UNIT_WEIGHT_BAND_PCF
from typehaus.resolve.overlay import union_all

_M = 0.3048


def _house_side(ctx, cross_tag: str, walls: list):  # type: ignore[no-untyped-def]
    """A large polygon on the far side of the cross-member's axis from the loop members."""
    from typehaus.engineering.retaining_system_rows import cross_axis

    axis = cross_axis(ctx, ctx.plan.by_tag(cross_tag))
    if axis is None:
        return None
    (x0, y0), (x1, y1) = ((a / _M, b / _M) for a, b in axis)
    ux, uy = x1 - x0, y1 - y0
    norm = (ux * ux + uy * uy) ** 0.5
    nx, ny = -uy / norm, ux / norm
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    members = union_all([_stem(ctx, w, set())[0] for w in walls])
    cx, cy = members.centroid.x, members.centroid.y
    if (cx - mx) * nx + (cy - my) * ny > 0:
        nx, ny = -nx, -ny
    far = 1000.0
    return Polygon([(mx - ux / norm * far, my - uy / norm * far),
                    (mx + ux / norm * far, my + uy / norm * far),
                    (mx + ux / norm * far + nx * far, my + uy / norm * far + ny * far),
                    (mx - ux / norm * far + nx * far, my - uy / norm * far + ny * far)])


def house_side_weight(ctx, cross_tag: str, walls: list, members, body: Body  # type: ignore[no-untyped-def]
                      ) -> tuple[float, str]:
    """``(upper-bound weight on the house side lb, how)``."""
    from typehaus.model.structure import FoundationWall

    region = _house_side(ctx, cross_tag, walls)
    if region is None:
        return 0.0, "no resolvable cross-member axis"
    concrete = sum(p.weight() * p.shape.intersection(region).area / p.shape.area
                   for p in body.prisms if p.shape is not None and p.shape.area
                   and p.label.startswith(("footing:", "stem:")))
    pcf = SOIL_UNIT_WEIGHT_BAND_PCF[1]
    stem_ft = 1.0
    outside = union_all([_exterior(m, stem_ft) for m in members])
    soil = 0.0
    for wall in spliced_walls(ctx, walls):
        footing = next((s for s in ctx.model.solids
                        if s.category == "footing" and getattr(
                            ctx.plan.by_tag(s.tag), "under", None) == wall.tag), None)
        stem, _t = _stem(ctx, wall, set())
        if footing is None or stem is None:
            continue
        heel = _poly(footing.outline).intersection(outside).difference(stem)
        height = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M
        soil += heel.intersection(region).area * height * pcf
    loop = {w.tag for w in walls} | body.spliced
    beds = {b.host for b in ctx.model.footing_beddings}
    braced = union_all([_stem(ctx, w, set())[0] for w in spliced_walls(ctx, walls)])
    extra = 0.0
    for wall in ctx.plan.all_elements():
        if (isinstance(wall, FoundationWall) and wall.tag not in loop and wall.tag in beds
                and wall.top_elevation is not None and wall.bottom_elevation is not None):
            poly, _t = _stem(ctx, wall, set())
            # Cast with the braced walls: concrete, and it runs into them.
            if poly is not None and _cast(ctx, wall) and poly.distance(braced) < 0.1 \
                    and poly.intersection(region).area > 0.5 * poly.area:
                height = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M
                extra += poly.area * height * CONCRETE_UNIT_WEIGHT_PCF
    total = concrete + soil + extra
    return total, (f"house side of {cross_tag}: concrete {concrete:,.0f} + heel soil to the "
                   f"stem tops at {pcf:.0f} pcf {soil:,.0f} + bedded cast walls {extra:,.0f} "
                   f"= {total:,.0f} lb")


def _cast(ctx, wall) -> bool:  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    assembly = ctx.plan.library.resolve_assembly(wall.assembly)
    return assembly is not None and any(
        layer.function is LayerFunction.STRUCTURE and layer.material_ref == "concrete"
        for layer in assembly.layers)
