"""The applicability sheet of a segmental wall's published gravity-chart row.

A maker's chart (Allan Block Table 1.3) is true for a SECTION, not a height. Each
:class:`Condition` is one thing the row assumes, set beside what the model draws; any False
is a FAIL of ``structural.srw_gravity_chart``, any unanswerable one UNKNOWN. Row values are
authored on ``SegmentalWallSpec.chart``/``published`` with their page; none ships here.

Facing and 2H: the tier row is a TERRACE rule (same-facing upper wall, AB manual p.60), so a
back-to-back pair does not trip it; an unknown facing still refuses.

Oracle: ``notes/raised_garden_srw.md`` §10 (the sheet, by hand per leg).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.soil import SOIL_UNIT_WEIGHT_BAND_PCF
from typehaus.engineering.srw_gravity import phi_from_efp
from typehaus.engineering.srw_scope import R404_4_FILL_LIMIT_FT
from typehaus.engineering.srw_tiers import TIER_FACTOR, Tier, _direction, _footprint

_M_PER_FT = 0.3048
#: House clearance (NOT a maker's number): concentrated gutter water must land at least this far
#: off a wall's toe, on an erosion-protected pad (AB Table 2.1, p.16: "When moisture is present,
#: extra precautions may be required" - the pad is that precaution), within ``TOE_ZONE_FT``.
#: The reviewer's 3'-0" (A2-F8) was not AB's either; the owner relaxed it 2026-11-24.
TOE_CLEAR_FT = 1.5
TOE_ZONE_FT = 10.0
#: A ground-level object no more than this proud (m, 4") counts as the splash pad.
PAD_MAX_PROUD_M = 0.1016
#: How far a free-ended gutter's water travels past its lip before it lands. Not modelled: a
#: stated assumption, by hand (notes/raised_garden_srw.md §10): 17 gpm design in the 4" x 3"
#: channel at 1/4 in/ft (Manning n 0.012) runs 0.645" deep at 2.11 ft/s and falls ~28" (channel
#: floor to the basin dish): 0.38 s, 0.80 ft out.
THROW_FT = 0.8
#: A trim run whose underside is within this of a wall's top is seated on it.
_SEAT_TOL_M = 0.15


@dataclass(frozen=True)
class Condition:
    name: str
    row: str          # what the chart row assumes
    drawn: str        # what the model draws
    ok: bool | None   # None: the model cannot answer


def drainage_layers(ctx: EngineeringContext, wall) -> list[str]:  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    assembly = ctx.plan.library.resolve_assembly(wall.assembly)
    return [layer.name for layer in (assembly.layers if assembly is not None else ())
            if layer.function is LayerFunction.DRAINAGE]


def published_refusal(ctx: EngineeringContext, wall, tiers: list[Tier]) -> str | None:  # type: ignore[no-untyped-def]
    """Why the authored chart row cannot describe this wall, or ``None``."""
    from typehaus.engineering.segmental_wall import reading

    spec = getattr(wall, "srw", None)
    row = getattr(spec, "published", None)
    if row is None:
        return None
    if not drainage_layers(ctx, wall) and spec.drainage_zone is None:
        return (f"assembly {wall.assembly} declares no DRAINAGE layer and the spec no "
                "drainage_zone behind the unit")
    if spec.batter_deg is None:
        return "no batter is stated on the SegmentalWallSpec"
    if not spec.cap:
        return "no cap unit is modelled"
    # Same-facing terrace walls only: a perpendicular or back-to-back one is not this rule's.
    near = [t for t in tiers if t.parallel and t.back_to_back is False
            and t.clear_ft < TIER_FACTOR * t.lower_height_ft]
    if near:
        return (f"{near[0].tag} ({near[0].lower_height_ft:.2f}' retained) faces the same way "
                f"and stands {near[0].clear_ft:.2f}' away, inside 2H = "
                f"{TIER_FACTOR * near[0].lower_height_ft:.2f}'")
    unknown = [t for t in tiers if t.parallel and t.back_to_back is None
               and t.clear_ft < TIER_FACTOR * t.lower_height_ft]
    if unknown:
        return f"{unknown[0].tag}'s facing is not established ({unknown[0].facing_basis})"
    read, _ = reading(ctx, wall)
    if read is not None:
        exposed = read.wall_ft - read.yard_ft
        if row.span.feet + 1e-6 < exposed:
            return f"the row publishes {row.span.feet:.2f}' and the wall stands {exposed:.2f}'"
    return None


def _seated_runs(ctx: EngineeringContext, shape, top_m: float):  # type: ignore[no-untyped-def]
    """Gutters whose underside is on the wall top and whose path crosses its footprint."""
    from shapely.geometry import LineString

    from typehaus.model.trim import Gutter

    out = []
    for el in ctx.plan.all_elements():
        if not isinstance(el, Gutter) or len(el.path) < 2:
            continue
        under = el.top_elevation.meters - el.depth.meters
        if abs(under - top_m) <= _SEAT_TOL_M and shape.intersects(
                LineString([p.xy_m for p in el.path])):
            out.append(el)
    return out


def _face_side(ctx: EngineeringContext, here):  # type: ignore[no-untyped-def]
    """Unit normal pointing at the yard (the face side), off the grade station the wall's
    embedment is read to, or None."""
    from shapely.geometry import Point

    from typehaus.engineering.srw_tiers import _station_xy
    from typehaus.resolve.site_earth import nearest_grade_station

    (ax, ay), (bx, by) = here.axis
    mid = ((ax + bx) / 2.0, (ay + by) / 2.0)
    station = nearest_grade_station(ctx.model, Point(mid))
    sx, sy = _station_xy(ctx, station[0]) if station is not None else (None, None)
    if sx is None:
        return None
    ux, uy = _direction(here.axis)
    return (-uy, ux) if (sx - mid[0]) * -uy + (sy - mid[1]) * ux > 0 else (uy, -ux)


def _toe_discharges(ctx: EngineeringContext, shape, here, face):  # type: ignore[no-untyped-def]
    """What is wrong with where yard-side water lands, as sentences: a free-ended gutter's lip plus
    ``THROW_FT`` along its last leg, or a leader's foot, inside ``TOE_ZONE_FT`` of the toe. It
    must land >= TOE_CLEAR_FT off the wall AND on a flat ground-level pad."""
    from shapely.geometry import Point, Polygon

    from typehaus.model.trim import Downspout, Gutter

    (ax, ay), _ = here.axis
    pads = [(o.tag, Polygon(o.footprint)) for o in ctx.model.canvas_objects
            if len(o.footprint) >= 3 and o.body_z1_m is not None and o.body_z0_m is not None
            and o.body_z1_m - o.body_z0_m <= PAD_MAX_PROUD_M]
    problems: list[str] = []
    for el in ctx.plan.all_elements():
        if isinstance(el, Gutter) and len(el.path) >= 2:
            if el.downspout_ref is not None:    # it lets go at a leader, tested below
                continue
            (px, py), (qx, qy) = el.path[-2].xy_m, el.path[-1].xy_m
            run = math.hypot(qx - px, qy - py) or 1.0
            throw = THROW_FT * _M_PER_FT
            xy = (qx + (qx - px) / run * throw, qy + (qy - py) / run * throw)
        elif isinstance(el, Downspout):
            xy = el.position.xy_m
        else:
            continue
        if (xy[0] - ax) * face[0] + (xy[1] - ay) * face[1] <= 0.0:
            continue                            # on the retained side
        off = shape.distance(Point(xy)) / _M_PER_FT
        if off > TOE_ZONE_FT:
            continue
        if off < TOE_CLEAR_FT:
            problems.append(f"{el.tag} lands {off:.1f}' off the toe")
        elif not any(poly.contains(Point(xy)) for _tag, poly in pads):
            problems.append(f"{el.tag} lands {off:.1f}' off the toe on no splash pad")
    return problems


def _surcharge(ctx: EngineeringContext, wall, here, face, height_ft: float):  # type: ignore[no-untyped-def]
    """Slabs and stairs in the retained strip, one exposed height behind the wall."""
    from shapely.geometry import Polygon

    from typehaus.model.slabs import Slab

    (ax, ay), (bx, by) = here.axis
    back = (-face[0], -face[1])
    half = 0.5 * wall.srw.unit_depth.meters if wall.srw.unit_depth is not None else 0.15
    reach = half + height_ft * _M_PER_FT
    zone = Polygon([(ax, ay), (bx, by), (bx + back[0] * reach, by + back[1] * reach),
                    (ax + back[0] * reach, ay + back[1] * reach)])
    hits = [s.tag for s in ctx.plan.all_elements()
            if isinstance(s, Slab) and len(s.outline) >= 3
            and Polygon([p.xy_m for p in s.outline]).intersects(zone)]
    hits += [s.tag for s in ctx.model.stairs if len(s.outline) >= 3
             and Polygon(s.outline).intersects(zone)]
    return hits


def applicability(ctx: EngineeringContext, wall, tiers: list[Tier]) -> list[Condition]:  # type: ignore[no-untyped-def]
    """Every condition of the wall's chart row against the model. Needs ``spec.chart``."""
    from typehaus.engineering.segmental_wall import reading
    from typehaus.model.structure import FootingBedding

    spec, chart, row = wall.srw, wall.srw.chart, wall.srw.published
    read, missing = reading(ctx, wall)
    if read is None:
        return [Condition("reading", "the wall's own section", "; ".join(missing), None)]
    sect, fill_ft = read.section, wall.unbalanced_fill.feet
    exposed = max(read.wall_ft - read.yard_ft, fill_ft)
    resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
    shape = _footprint(resolved) if resolved is not None else None
    top_m = wall.top_elevation.meters
    out: list[Condition] = []

    out.append(Condition(
        "R404.4 scope", f"unbalanced fill <= {R404_4_FILL_LIMIT_FT * 12:.0f}\"; no added "
        "lateral load (below)", f"{fill_ft * 12:.0f}\" retained",
        fill_ft <= R404_4_FILL_LIMIT_FT + 1e-9))
    layer = _unit_size(ctx, wall)
    out.append(Condition(
        "unit and setback", f"{row.member}, {chart.batter_deg:g} deg",
        f"{layer or 'no unit named'}, {sect.batter_deg:g} deg",
        None if layer is None else (row.member.split(",")[0].strip() in layer
                                    and sect.batter_deg + 1e-9 >= chart.batter_deg)))
    out.append(Condition(
        "exposed height, cap included", f"<= {row.span.feet * 12:.0f}\"",
        f"{exposed * 12:.1f}\" ({read.grade_from})", exposed <= row.span.feet + 1e-6))
    cap_ft, course = chart.cap_height.feet, sect.course_ft
    whole = (read.wall_ft - cap_ft) / course if course else 0.0
    seated = _seated_runs(ctx, shape, top_m) if shape is not None else []
    out.append(Condition(
        "cap on the top course", "a cap block on every course line",
        f"{spec.cap or 'none'} {cap_ft * 12:.0f}\" on {whole:.2f} courses"
        + (f"; {', '.join(g.tag for g in seated)} seated on the cap" if seated else ""),
        bool(spec.cap) and cap_ft > 0 and abs(whole - round(whole)) < 0.02))
    out.append(Condition(
        "buried base course", f">= {chart.min_buried.inches:g}\"",
        f"{read.yard_ft * 12:.1f}\" to {read.grade_from}",
        read.yard_ft + 1e-6 >= chart.min_buried.feet))
    zone = spec.drainage_zone
    out.append(Condition(
        "wall rock", f">= {chart.min_wall_rock.inches:g}\" behind the unit",
        f"{zone.width.inches:g}\"" if zone is not None else "none",
        zone is not None and zone.width.feet + 1e-6 >= chart.min_wall_rock.feet))
    phis = [phi_from_efp(read.soil.active_efp_psf_per_ft, pcf)
            for pcf in SOIL_UNIT_WEIGHT_BAND_PCF]
    out.append(Condition(
        "soil friction", f">= {chart.soil_phi_deg:g} deg (the row's floor)",
        f"{min(phis):.1f}-{max(phis):.1f} deg, " + ("PRESUMED" if read.soil is not None
                                                  and ctx.soil_basis is not None
                                                  and ctx.soil_basis.provenance == "presumed"
                                                  else "stated"),
        min(phis) + 1e-6 >= chart.soil_phi_deg))
    out.append(_drain(ctx, chart, FootingBedding))
    out.append(Condition(
        "founding fill", "compacted (Standard Proctor), placed in lifts",
        f"{chart.founding_compaction_pct:g}% Standard Proctor, {chart.lift.inches:g}\" lifts",
        chart.founding_compaction_pct >= 95.0 and chart.lift.inches <= 8.0))
    face = _face_side(ctx, resolved) if resolved is not None else None
    hits = _surcharge(ctx, wall, resolved, face, exposed) if face is not None else None
    out.append(Condition(
        "level bed, no surcharge", "level, nothing but soil retained",
        "unknown retained side" if hits is None else
        (f"{', '.join(hits)} in the retained strip" if hits else "planting terrace only"),
        None if hits is None else not hits))
    wet = _toe_discharges(ctx, shape, resolved, face) if face is not None else None
    out.append(Condition(
        "water landed clear of the toe", f"lands >= {TOE_CLEAR_FT * 12:g}\" off the toe on an "
        f"erosion-protected pad (a gutter's water lands {THROW_FT:g}' past its lip)",
        "yard side not established" if wet is None else (", ".join(wet) if wet else
                                                          "none lands on the yard side"),
        None if wet is None else not wet))
    refusal = published_refusal(ctx, wall, tiers)
    out.append(Condition("tier independence (2H)", "no same-facing taller wall within 2H",
                         refusal or "answered", refusal is None))
    return out


def _unit_size(ctx: EngineeringContext, wall) -> str | None:  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    assembly = ctx.plan.library.resolve_assembly(wall.assembly)
    for layer in (assembly.layers if assembly is not None else ()):
        if layer.function is LayerFunction.STRUCTURE and layer.masonry is not None:
            return layer.masonry.unit_size
    return None


def _drain(ctx: EngineeringContext, chart, bedding_type) -> Condition:  # type: ignore[no-untyped-def]
    d = chart.drain
    if d is None:
        return Condition("drain pipe and outlet", "a drain, vented to daylight or an "
                         "underground drainage system", "none authored", False)
    bed = next((b for b in ctx.plan.all_elements()
                if isinstance(b, bedding_type) and b.tag == d.outlet_ref), None)
    ok = bed is not None and bed.wall_column is not None
    return Condition(
        "drain pipe and outlet", "a drain, vented to daylight or an underground drainage system",
        f"{d.pipe} into {d.outlet_ref}'s wall column" if ok else
        f"{d.pipe}; outlet {d.outlet_ref} has no wall column", ok)


__all__ = ["Condition", "applicability", "drainage_layers", "published_refusal"]
