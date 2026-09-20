"""A spread — or COMBINED — base under axial load and a moment, as a rigid body on soil.

``column_base`` grades a cast column's base fixity against IBC 1807.3.2.1's embedded-pole
formula, and carried a second mechanism as PROSE for as long as it existed: "taken as a rigid
spread base with no help from the buried shaft, the resultant sits 1.65' off centre against a
kern of 0.25'". True, useful, and not a limit state — no demand, no capacity, no ratio, and
nothing a seal could cover. This module is that paragraph turned into arithmetic.

** THE TWO MECHANISMS ARE ALTERNATIVE AND THE CHOICE IS AUTHORED. ** A shaft that turns in
soil sheds its moment into lateral bearing along its buried length; a pad resists by bearing
precisely because the shaft above it does not. Adding them counts one moment twice. Which one
a base actually has is a soil-structure stiffness problem nothing here solves, so
``Pad.resists_base_moment`` decides it — never this module, and never "whichever passes".

** THE UNION IS CREDITED ONLY UNDER THAT CLAIM, AND ONLY FOR CONCRETE. ** Where the pad names
``cast_with`` pours, the footprint is their union: one pour, ACI 318-19 §13.3.4's combined
footing. Two guards, and both have fired on a real house. A named pour that resolves to a
DIFFERENT MATERIAL — catlin's garage strip footings became consolidated crushed stone under
IRC R403.5 in 2026-09-15, four days after three pads declared they were cast with them — is
refused by name, because stone is not cast with anything. And a union that comes back as more
than one piece is refused too: a combined footing is one body, and two pours that do not
touch cannot share a section modulus.

** A CONTINUOUS STRIP FOOTING NAMED IN ``cast_with`` IS CREDITED IN FULL, AND THAT IS THE
TRAP TO WATCH. ** The union takes each named pour's whole plan solid. For a neighbouring pad
that is exactly right. For a forty-foot strip footing under a basement wall it is not: how
much of a continuous strip belongs to one column's combined footing is a DESIGN decision —
the length over which the two loads are taken to act together — and no geometry answers it.
Nothing here can tell those two cases apart, so a house claiming ``resists_base_moment`` on a
pad lapped into a long strip is claiming something this module will happily compute and a
reviewer should refuse. That is the one place on this page where the arithmetic is not the
whole answer, and it is why the claim is authored rather than derived.

** §13.3.4.3 FORBIDS A UNIFORM PRESSURE, SO NONE IS ASSUMED. ** The distribution here is the
rigid-body LINEAR one — ``p = W/A ± M_c c / I`` on the union's own area, centroid and second
moment, computed from the polygon rather than from a width and a length. Where the resultant
leaves the kern the section lifts at one edge, the linear form stops describing anything, and
this refuses to publish a pressure rather than extrapolating a trapezoid past its validity.
That refusal is itself the answer a small pad under a big moment deserves.

**Oracle.** ``houses/catlin/notes/entry_column_base_fixity.md`` §8, hand-worked in a separate
pass; ``tests/test_column_base_calcs.py`` reproduces it.
"""

from __future__ import annotations

from dataclasses import dataclass

_M_PER_FT = 0.3048

#: Normal-weight concrete, lb/ft3 — the same figure ``engineering/soil`` uses.
CONCRETE_PCF = 150.0

#: IRC R404.4's factor of safety against overturning, applied here for the same reason it is
#: applied to a retaining wall: it is the only published stability factor this engine holds,
#: and a canopy column's base is no less a stability question than a stem wall's.
REQUIRED_FS_OVERTURNING = 1.5


@dataclass(frozen=True)
class Pour:
    """One body in a combined footing: its plan polygon in FEET and its thickness."""

    tag: str
    outline_ft: tuple[tuple[float, float], ...]
    thickness_ft: float
    #: False for anything that is not cast concrete — a crushed-stone footing, say.
    castable: bool = True


@dataclass(frozen=True)
class Footprint:
    """The union's plan properties along ONE axis, plus what it weighs."""

    tags: tuple[str, ...]
    area_ft2: float
    #: Centroid station along the moment's own axis, feet in plan coordinates.
    centroid_ft: float
    #: Second moment of area about that centroid, ft^4.
    inertia_ft4: float
    #: The union's two edges along the axis.
    low_ft: float
    high_ft: float
    weight_lb: float
    #: Station of the resultant of the pours' own weight.
    weight_station_ft: float


def polygon_area_centroid(outline: tuple[tuple[float, float], ...],
                          ) -> tuple[float, float, float]:
    """``(signed area, x centroid, y centroid)`` by the shoelace formulas."""
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(outline)
    for i in range(n):
        x0, y0 = outline[i]
        x1, y1 = outline[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        return 0.0, 0.0, 0.0
    return area, cx / (6.0 * area), cy / (6.0 * area)


def polygon_second_moment(outline: tuple[tuple[float, float], ...], axis: str) -> float:
    """Second moment of area about the centroidal axis NORMAL to ``axis``, ft^4.

    ``axis`` names the direction the bearing pressure varies in — "x" for a moment that
    tips the base east-west. Green's theorem on the polygon, then the parallel-axis shift
    back to the centroid, so a shape that is not a rectangle is not approximated by one.
    """
    area, cx, cy = polygon_area_centroid(outline)
    if area == 0.0:
        return 0.0
    total = 0.0
    n = len(outline)
    for i in range(n):
        x0, y0 = outline[i]
        x1, y1 = outline[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        if axis == "x":
            total += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        else:
            total += (y0 * y0 + y0 * y1 + y1 * y1) * cross
    about_origin = total / 12.0
    centre = cx if axis == "x" else cy
    return abs(about_origin) - abs(area) * centre ** 2


def union_footprint(pours: list[Pour], axis: str) -> Footprint | None:
    """The combined footprint of every pour, or ``None`` where it is not one body.

    Refuses rather than returns a partial answer in three cases, and each one is a real
    modelling condition rather than a defensive crouch: a pour that is not castable (nothing
    is cast monolithically with crushed stone), a union that comes back as more than one
    piece (two bodies cannot share a section modulus), and a degenerate outline.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    if not pours or any(not pour.castable for pour in pours):
        return None
    shapes = []
    for pour in pours:
        if len(pour.outline_ft) < 3:
            return None
        shapes.append(Polygon(pour.outline_ft))
    merged = union_all(shapes)
    if merged.is_empty or merged.geom_type != "Polygon":
        return None
    outline = tuple((float(x), float(y)) for x, y in merged.exterior.coords[:-1])
    area, cx, cy = polygon_area_centroid(outline)
    if abs(area) < 1e-9:
        return None
    inertia = polygon_second_moment(outline, axis)
    stations = [p[0] if axis == "x" else p[1] for p in outline]
    weight = sum(abs(polygon_area_centroid(pour.outline_ft)[0]) * pour.thickness_ft
                 * CONCRETE_PCF for pour in pours)
    moment = 0.0
    for pour in pours:
        pour_area, pcx, pcy = polygon_area_centroid(pour.outline_ft)
        moment += (abs(pour_area) * pour.thickness_ft * CONCRETE_PCF
                   * (pcx if axis == "x" else pcy))
    return Footprint(
        tags=tuple(pour.tag for pour in pours), area_ft2=abs(area),
        centroid_ft=(cx if axis == "x" else cy), inertia_ft4=inertia,
        low_ft=min(stations), high_ft=max(stations), weight_lb=weight,
        weight_station_ft=(moment / weight if weight else 0.0))


@dataclass(frozen=True)
class SpreadResult:
    """What the rigid-body analysis found, in the units a limit state wants."""

    #: Eccentricity of the total resultant from the footprint's centroid, ft.
    eccentricity_ft: float
    #: The kern distance on the side the resultant moved toward, ft (``S/A``).
    kern_ft: float
    #: Peak bearing pressure, psf — ``None`` where the resultant left the kern and the
    #: linear distribution no longer describes the contact.
    bearing_psf: float | None
    #: Factor of safety against overturning about the nearer edge.
    fs_overturning: float
    #: Which edge it would tip about, for the record's prose.
    tipping_edge: str
    total_vertical_lb: float


def analyse(footprint: Footprint, axial_lb: float, axial_station_ft: float,
            moment_lb_ft: float, axis: str) -> SpreadResult | None:
    """One base, one moment axis, as a rigid body.

    ``axial_station_ft`` is where the COLUMN stands, which on a combined footing is nowhere
    near the union's centroid — that offset is most of what a combined footing is for, and
    taking the load at the centroid would quietly delete it.
    """
    del axis
    total = axial_lb + footprint.weight_lb
    if total <= 0.0 or footprint.area_ft2 <= 0.0 or footprint.inertia_ft4 <= 0.0:
        return None
    # Everything about the AREA centroid: the applied moment, plus the moment the vertical
    # loads already make by not standing over it.
    offset = ((axial_lb * axial_station_ft + footprint.weight_lb
               * footprint.weight_station_ft) / total) - footprint.centroid_ft
    net_moment = moment_lb_ft + total * offset
    eccentricity = net_moment / total
    toward_high = eccentricity >= 0.0
    c = ((footprint.high_ft - footprint.centroid_ft) if toward_high
         else (footprint.centroid_ft - footprint.low_ft))
    if c <= 0.0:
        return None
    kern = footprint.inertia_ft4 / (c * footprint.area_ft2)
    bearing = None
    if abs(eccentricity) <= kern + 1e-9:
        bearing = total / footprint.area_ft2 + abs(net_moment) * c / footprint.inertia_ft4
    # Overturning about the edge the resultant is moving toward: the vertical loads resist
    # on their own levers to that edge, the applied moment drives it.
    edge = footprint.high_ft if toward_high else footprint.low_ft
    resisting = (axial_lb * abs(edge - axial_station_ft)
                 + footprint.weight_lb * abs(edge - footprint.weight_station_ft))
    fs = resisting / abs(moment_lb_ft) if abs(moment_lb_ft) > 1e-9 else float("inf")
    return SpreadResult(
        eccentricity_ft=abs(eccentricity), kern_ft=kern, bearing_psf=bearing,
        fs_overturning=fs,
        tipping_edge=f"the {'high' if toward_high else 'low'} edge at {edge:+.2f}'",
        total_vertical_lb=total)


def pours_for(ctx, pad) -> list[Pour] | None:  # type: ignore[no-untyped-def]
    """This base and everything it says it was cast with, as plan polygons in FEET.

    ``None`` where any of them is missing from the resolved model or is not concrete. A
    crushed-stone footing is the case that made this a guard rather than a filter: catlin
    retyped nine garage strip footings to IRC R403.5 stone four days after three pier pads
    declared they were cast monolithically with them, and silently dropping those from the
    union would have credited a smaller footprint without saying so.
    """
    tag = getattr(pad, "tag", None)
    if tag is None:
        return None
    wanted = [tag, *(getattr(pad, "cast_with", ()) or ())]
    solids = {s.tag: s for s in ctx.model.solids if s.tag in set(wanted)}
    out: list[Pour] = []
    for name in wanted:
        solid = solids.get(name)
        outline = getattr(solid, "outline", None) if solid is not None else None
        if not outline:
            return None
        element = ctx.plan.by_tag(name)
        material = getattr(element, "material", None)
        thickness = (solid.z1_m - solid.z0_m) / 0.3048
        out.append(Pour(
            tag=name,
            outline_ft=tuple((p[0] / 0.3048, p[1] / 0.3048) for p in outline),
            thickness_ft=thickness,
            castable=material in (None, "concrete")))
    return out
