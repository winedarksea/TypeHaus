"""The court's sliding bodies, read off the resolved solids, and the earth and water on them.

``retaining_system`` grades one court on two planes (free body §15, decisions 1 and 2):

* the **footing plane** — concrete on the stone bed. The body is the cast loop (every footing
  and stem in placements 1-2, the strut, and the walls spliced to them) plus the retained soil
  standing on the retaining footings' heels, corner squares included;
* the **deep plane** — the bed's stone on native, at the bottom of the soakaway course. The
  body adds the beds and the native core the beds enclose.

**Why a body and not unit sections.** The old free body took each wall as a unit section x
its axis length. FT-SG-S runs out to out (25'-0") and carries soil on its two corner squares,
so the retained soil pushes on 25'-0" of south face, not on 18'-0" of axis. Counting the
corners' weight without their thrust would be the unsafe half of the same correction.
The net thrust acts over the body's projected width; favourable soil pressure on its
north-facing soil faces (the side heels' north ends) is not credited, like passive.

Water (``Water``): a perched or high head on the retained side only, with the bed draining
(no uplift, the water thrust unbalanced); or one level on both sides, where the horizontal
water forces close on themselves and what is left is uplift on every prism below it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon

from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF, SOIL_UNIT_WEIGHT_BAND_PCF
from typehaus.resolve.overlay import union_all

_M = 0.3048
WATER_PCF = 62.4
#: The saturated unit weight the THRUST takes below water, at both ends of the band: the
#: band's top, so K0·(γsat − γw) + γw is the largest the band allows. Weights below water
#: take the band's own γ less γw, the smallest. Neither is a code value (soil.py).
SATURATED_PCF_FOR_THRUST = SOIL_UNIT_WEIGHT_BAND_PCF[1]
#: Washed #57 stone in the beds and drain columns: the library's #57 density (1,600 kg/m3),
#: which the beds' authored void ratio 0.40 reproduces at Gs 2.65: 0.60 x 2.65 x 62.4 = 99.2.
STONE_PCF = 100.0


@dataclass(frozen=True)
class Prism:
    """A vertical prism of one material in the body; elevations in feet."""

    label: str
    area_sf: float
    z0_ft: float
    z1_ft: float
    pcf: float
    #: Plan footprint (ft), for apportioning the prism to the footing under it.
    shape: object = field(default=None, compare=False, repr=False)

    def weight(self, water_ft: float | None = None) -> float:
        """Effective weight: buoyant below ``water_ft`` (None = no water under the body)."""
        height = max(0.0, self.z1_ft - self.z0_ft)
        sub = 0.0 if water_ft is None else min(height, max(0.0, water_ft - self.z0_ft))
        return self.area_sf * (self.pcf * height - WATER_PCF * sub)


@dataclass(frozen=True)
class Water:
    """One water state. ``level_ft`` None is dry."""

    label: str
    level_ft: float | None = None
    #: True: the same level both sides, uplift on the body. False: retained side only, the
    #: bed under the footings draining (no uplift).
    both_sides: bool = False
    #: Ground snow on the retained terrace, psf, carried as a K0 surcharge.
    snow_psf: float = 0.0
    #: A lateral load delivered INTO the body (a structure standing on it), lb, along
    #: ``wind_dir``; added the adverse way to the soil's resultant.
    wind_lb: float = 0.0
    wind_dir: tuple[float, float] = (1.0, 0.0)
    #: The same structure's other-axis wind, lb, added along the soil's own resultant.
    wind_along_lb: float = 0.0


DRY = Water("dry")


@dataclass(frozen=True)
class Push:
    """One retaining member's push on the body: per-foot terms and the width it acts on."""

    tag: str
    direction: tuple[float, float]
    width_ft: float
    top_ft: float
    efp: float
    lateral_plf: float = 0.0


@dataclass(frozen=True)
class Body:
    """A rigid body sliding on one plane."""

    label: str
    plane_ft: float
    friction: float
    prisms: tuple[Prism, ...]
    pushes: tuple[Push, ...]
    soil_pcf: float
    #: Tags of the spliced walls and their footings: in the body by their concrete only.
    spliced: frozenset[str] = frozenset()

    def weight(self, water: Water = DRY) -> float:
        level = water.level_ft if water.both_sides else None
        return sum(p.weight(level) for p in self.prisms)

    def thrust_per_ft(self, push: Push, water: Water = DRY) -> float:
        """At-rest earth on the push's face, top to plane, plus its lateral surcharge."""
        earth, unbalanced_water, snow, lateral = self.thrust_terms(push, water)
        return earth + unbalanced_water + snow + lateral

    def thrust_terms(self, push: Push, water: Water = DRY
                     ) -> tuple[float, float, float, float]:
        """``(earth, unbalanced water, snow, lateral surcharge)`` plf: the terms of the thrust."""
        k0 = push.efp / self.soil_pcf
        sub = SATURATED_PCF_FOR_THRUST - WATER_PCF
        depth = push.top_ft - self.plane_ft
        level = water.level_ft
        hw = 0.0 if level is None else min(depth, max(0.0, level - self.plane_ft))
        dry = depth - hw
        earth = 0.5 * k0 * self.soil_pcf * dry * dry
        earth += k0 * (self.soil_pcf * dry * hw + 0.5 * sub * hw * hw)
        unbalanced_water = 0.0 if water.both_sides else 0.5 * WATER_PCF * hw * hw
        snow = k0 * water.snow_psf * depth
        return earth, unbalanced_water, snow, push.lateral_plf

    def resultant_vector(self, water: Water = DRY) -> tuple[float, float]:
        rx = sum(self.thrust_per_ft(p, water) * p.width_ft * p.direction[0] for p in self.pushes)
        ry = sum(self.thrust_per_ft(p, water) * p.width_ft * p.direction[1] for p in self.pushes)
        if water.wind_lb:
            dx, dy = water.wind_dir
            sign = 1.0 if rx * dx + ry * dy >= 0.0 else -1.0
            rx, ry = rx + sign * water.wind_lb * dx, ry + sign * water.wind_lb * dy
        if water.wind_along_lb:
            norm = (rx * rx + ry * ry) ** 0.5 or 1.0
            rx, ry = rx * (1 + water.wind_along_lb / norm), ry * (1 + water.wind_along_lb / norm)
        return rx, ry

    def resultant(self, water: Water = DRY) -> float:
        rx, ry = self.resultant_vector(water)
        return (rx * rx + ry * ry) ** 0.5

    def fs(self, water: Water = DRY) -> float:
        demand = self.resultant(water)
        return self.friction * self.weight(water) / demand if demand else float("inf")

    def weight_on(self, footprint, water: Water = DRY) -> float:  # type: ignore[no-untyped-def]
        """The share of the body's weight standing on ``footprint`` (plan, ft)."""
        level = water.level_ft if water.both_sides else None
        return sum(p.weight(level) * p.shape.intersection(footprint).area / p.shape.area
                   for p in self.prisms if p.shape is not None and p.shape.area)

    def parts(self, water: Water = DRY) -> dict[str, float]:
        level = water.level_ft if water.both_sides else None
        out: dict[str, float] = {}
        for p in self.prisms:
            key = p.label.split(":")[0]
            out[key] = out.get(key, 0.0) + p.weight(level)
        return out


def _poly(ring) -> Polygon:  # type: ignore[no-untyped-def]
    return Polygon([(x / _M, y / _M) for x, y in ring]).buffer(0)


def _solid(ctx, tag: str, category: str):  # type: ignore[no-untyped-def]
    return next((s for s in ctx.model.solids if s.tag == tag and s.category == category), None)


def _footing_of(ctx, wall_tag: str):  # type: ignore[no-untyped-def]
    from typehaus.model.structure import Footing

    return next((f for f in ctx.plan.all_elements()
                 if isinstance(f, Footing) and f.under == wall_tag), None)


def spliced_walls(ctx, members: list) -> list:  # type: ignore[no-untyped-def]
    """Walls not in the loop whose footing a member footing's bars run into
    (``BarSpec.continues_into``): cast with it and tied to it, so they slide with it.
    Their own thrusts are carried by their own braces and add nothing to the resultant."""
    from typehaus.model.structure import FoundationWall

    into: set[str] = set()
    for wall in members:
        footing = _footing_of(ctx, wall.tag)
        spec = getattr(footing, "reinforcement", None)
        for bar in getattr(spec, "bars", ()) or ():
            into.update(bar.continues_into or ())
    tags = {w.tag for w in members}
    return sorted((w for w in ctx.plan.all_elements()
                   if isinstance(w, FoundationWall) and w.tag not in tags
                   and (f := _footing_of(ctx, w.tag)) is not None and f.tag in into),
                  key=lambda w: w.tag)


def _stem(ctx, wall, ends: set[str]):  # type: ignore[no-untyped-def]
    """The stem's footprint (ft), lengthened by half its thickness at a loop corner."""
    from typehaus.engineering.retaining_basis import _structure_thickness_in

    resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
    thickness = (_structure_thickness_in(ctx, wall.assembly) or 0.0) / 12.0
    if resolved is None or not thickness:
        return None, thickness
    (x0, y0), (x1, y1) = ((a / _M, b / _M) for a, b in resolved.axis)
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    h = thickness / 2.0
    s = h if wall.start_node in ends else 0.0
    e = h if wall.end_node in ends else 0.0
    a = (x0 - ux * s, y0 - uy * s)
    b = (x1 + ux * e, y1 + uy * e)
    nx, ny = -uy * h, ux * h
    return Polygon([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                    (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]), thickness


def _exterior(member, stem_ft: float):  # type: ignore[no-untyped-def]
    """The half-plane beyond ``member``'s retained face, as a large polygon (ft)."""
    (x0, y0), (x1, y1) = member.axis_ft
    dx, dy = member.push
    far = 1000.0
    ox, oy = x0 - dx * stem_ft / 2.0, y0 - dy * stem_ft / 2.0
    ux, uy = x1 - x0, y1 - y0
    norm = (ux * ux + uy * uy) ** 0.5
    ux, uy = ux / norm * far, uy / norm * far
    return Polygon([(ox - ux, oy - uy), (ox + ux, oy + uy),
                    (ox + ux - dx * far, oy + uy - dy * far),
                    (ox - ux - dx * far, oy - uy - dy * far)])


@dataclass(frozen=True)
class Member:
    """What the body needs of one retaining wall (``retaining_system._members`` gives it)."""

    tag: str
    push: tuple[float, float]
    axis_ft: tuple[tuple[float, float], tuple[float, float]]
    efp: float
    lateral_plf: float
    top_ft: float


def footing_plane_body(ctx, cross_tag: str, walls: list, members: list[Member], *,  # type: ignore[no-untyped-def]
                       soil_pcf: float, friction: float) -> tuple[Body | None, list[str]]:
    """The loop, its spliced walls and the retaining heels' soil, on the footing plane."""
    missing: list[str] = []
    extra = spliced_walls(ctx, walls)
    loop_walls = [*walls, *extra]
    nodes = [n for w in loop_walls for n in (w.start_node, w.end_node)]
    corners = {n for n in nodes if nodes.count(n) > 1}
    prisms: list[Prism] = []
    footprints = []
    footing_polys = {}
    for wall in loop_walls:
        footing = _footing_of(ctx, wall.tag)
        solid = _solid(ctx, footing.tag, "footing") if footing else None
        if solid is None:
            missing.append(f"a resolved footing under {wall.tag}")
            continue
        poly = _poly(solid.outline).difference(union_all(footprints)) if footprints \
            else _poly(solid.outline)
        footprints.append(poly)
        footing_polys[wall.tag] = poly
        prisms.append(Prism(f"footing:{footing.tag}", poly.area, solid.z0_m / _M,
                            solid.z1_m / _M, CONCRETE_UNIT_WEIGHT_PCF, poly))
    cross = _solid(ctx, cross_tag, "beam")
    if cross is not None:
        poly = _poly(cross.outline).difference(union_all(footprints))
        prisms.append(Prism(f"strut:{cross_tag}", poly.area, cross.z0_m / _M,
                            cross.z1_m / _M, CONCRETE_UNIT_WEIGHT_PCF))
    if missing:
        return None, missing
    plane = min(p.z0_ft for p in prisms)
    stems = []
    stem_ft = 1.0
    for wall in loop_walls:
        poly, thickness = _stem(ctx, wall, corners)
        if poly is None:
            missing.append(f"a resolved stem section on {wall.tag}")
            continue
        stem_ft = thickness if wall in walls else stem_ft
        part = poly.difference(union_all(stems)) if stems else poly
        stems.append(poly)
        prisms.append(Prism(f"stem:{wall.tag}", part.area, wall.bottom_elevation.meters / _M,
                            wall.top_elevation.meters / _M, CONCRETE_UNIT_WEIGHT_PCF, part))
    heels = union_all([footing_polys[w.tag] for w in walls if w.tag in footing_polys])
    outside = union_all([_exterior(m, stem_ft) for m in members])
    soil = heels.intersection(outside).difference(union_all(stems))
    footing_top = max(p.z1_ft for p in prisms if p.label.startswith("footing:"))
    top = max(m.top_ft for m in members)
    columns = [s for s in ctx.model.solids if s.category == "drain_column"]
    stone = union_all([_poly(s.outline) for s in columns]).intersection(soil) \
        if columns else Polygon()
    col_top = max((s.z1_m / _M for s in columns
                   if not _poly(s.outline).intersection(soil).is_empty), default=footing_top)
    prisms.append(Prism("heel soil", soil.area, footing_top, top, soil_pcf, soil))
    if not stone.is_empty:
        # The drain column is stone, not soil, up to its own top.
        prisms.append(Prism("heel soil:drain column", stone.area, footing_top, col_top,
                            STONE_PCF - soil_pcf, stone))
    extent = union_all(list(footing_polys[w.tag] for w in walls if w.tag in footing_polys))
    pushes = tuple(Push(m.tag, m.push, _width(extent, m.axis_ft), m.top_ft, m.efp,
                        m.lateral_plf) for m in members)
    spliced = frozenset({w.tag for w in extra}
                        | {f.tag for w in extra if (f := _footing_of(ctx, w.tag))})
    return Body("footing plane", plane, friction, tuple(prisms), pushes, soil_pcf,
                spliced), missing


def _width(poly, axis) -> float:  # type: ignore[no-untyped-def]
    """The extent of ``poly`` along ``axis`` — the width a member's push acts over."""
    (x0, y0), (x1, y1) = axis
    norm = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    ux, uy = (x1 - x0) / norm, (y1 - y0) / norm
    proj = [x * ux + y * uy for x, y in poly.convex_hull.exterior.coords]
    return max(proj) - min(proj)


def deep_plane_body(ctx, body: Body, *, friction: float, native_pcf: float  # type: ignore[no-untyped-def]
                    ) -> tuple[Body | None, list[str]]:
    """``body`` plus the beds under it and the native core they enclose, on the deep plane.

    The plane is the deepest bed bottom under the loop (the soakaway course). Everything
    above it inside the loop's hull moves: the enclosed court core must, and the porch core is
    credited only its base shear, never a frontal resistance against the house."""
    footing_tags = {p.label.split(":")[1] for p in body.prisms if p.label.startswith(
        ("footing:", "strut:"))}
    beds = [b for b in ctx.model.footing_beddings if b.host in footing_tags]
    if not beds:
        return None, ["a FootingBedding under the loop's footings (the deep plane's stone)"]
    plane = min((b.soakaway_z0_m if b.soakaway_z0_m is not None else b.z0_m) / _M
                for b in beds)
    loop = union_all([_poly(s.outline) for s in ctx.model.solids
                        if s.tag in footing_tags and s.category in ("footing", "beam")])
    hull = loop.convex_hull
    floor = max(p.z1_ft for p in body.prisms if p.label.startswith("footing:"))
    prisms = list(body.prisms)
    counted = []
    for bed in ctx.model.footing_beddings:
        poly = _poly(bed.outline).intersection(hull)
        if poly.is_empty:
            continue
        part = poly.difference(union_all(counted)) if counted else poly
        counted.append(poly)
        bottom = (bed.soakaway_z0_m if bed.soakaway_z0_m is not None else bed.z0_m) / _M
        prisms.append(Prism(f"bed stone:{bed.tag}", part.area, bottom, bed.z1_m / _M, STONE_PCF))
        prisms.append(Prism(f"native under beds:{bed.tag}", part.area, plane, bottom,
                            native_pcf))
        above = part.difference(loop)
        if above.area > 1e-6 and bed.z1_m / _M < floor:
            prisms.append(Prism(f"native core:{bed.tag}", above.area, bed.z1_m / _M, floor,
                                native_pcf))
    beds_poly = union_all(counted)
    core = hull.difference(loop).difference(beds_poly)
    bands = [s for s in ctx.model.solids
             if s.category == "slab_band" and _poly(s.outline).within(hull.buffer(0.01))]
    field = union_all([_poly(s.outline) for s in bands])
    gravel = core.intersection(field) if bands else Polygon()
    field_z0 = min((s.z0_m / _M for s in bands), default=floor)
    prisms.append(Prism("native core", core.area, plane, floor, native_pcf))
    if not gravel.is_empty:
        prisms.append(Prism("native core:field gravel", gravel.area, field_z0, floor,
                            STONE_PCF - native_pcf))
    under = loop.difference(beds_poly)
    if under.area > 1e-6:
        prisms.append(Prism("native under beds:unbedded", under.area, plane,
                            min(p.z0_ft for p in body.prisms), native_pcf))
    pushes = tuple(Push(p.tag, p.direction, _width(hull, _axis_of(p.direction)), p.top_ft,
                        p.efp, p.lateral_plf) for p in body.pushes)
    return Body("deep plane", plane, friction, tuple(prisms), pushes, native_pcf,
                body.spliced), []


def _axis_of(direction: tuple[float, float]):  # type: ignore[no-untyped-def]
    dx, dy = direction
    return ((0.0, 0.0), (-dy, dx))

