"""S-001's truss criteria schedule — what every truss ORDER is written against (decision 20).

Roof trusses and floor trusses alike are ordered off a supplier's sealed drawing, which does
not exist yet. This block is the order's criteria, derived from the model so no number is typed
twice: loads, the drift on each truss, bearings, the chord force, deflection limits, maximum
uplift and maximum reactions by member and bearing, and the applied loads of a floor order.

Two statuses print per subject and never merge. **Supporting structure** is graded now, against
the specified reactions (the heel tie's catalog allowable, a floor reaction against the maker's
published maximum). **Component** is the supplier's design checked against this block, and is
OPEN until a reaction schedule is quoted into the model.
"""

from __future__ import annotations

import statistics
from typing import Any

from typehaus.emit.draw.structural_common import (
    feet_inches,
    flat_roof_snow_psf,
    roof_snow_thermal_factor,
    truss_heel_note,
)
from typehaus.resolve.model import ResolvedModel
from typehaus.wind import wind_basis

_FT = 0.3048
NOT_STATED = "not stated"
_cache: dict[str, Any] = {}


def truss_criteria_block(model: ResolvedModel, preferences: object) -> list[str]:
    """The block's lines; empty when the model has no trussed roof and no floor truss order."""
    lines: list[str] = []
    ctx = _context(model, preferences)
    for roof in sorted(model.roofs, key=lambda r: r.tag):
        if any(m.category == "rafter" for m in roof.members) or not any(
                m.category == "roof_truss" for m in roof.members):
            continue
        lines += _roof(ctx, model, roof, preferences)
    for floor in sorted(model.plan.elements_of_kind("FloorSystem"), key=lambda f: f.tag):
        if getattr(floor, "truss_order", None) is not None:
            lines += _floor(model, floor)
    return lines


def _context(model: ResolvedModel, preferences: object) -> Any:
    from typehaus.engineering.registry import EngineeringContext

    return EngineeringContext(plan=model.plan, model=model, preferences=preferences)


def _drifted_sources(ctx: Any) -> list[Any]:
    from typehaus.engineering.roof_beam import compute

    tags = {t for record in compute(ctx) for t in record.element_tags}
    return [r for r in sorted(ctx.model.roofs, key=lambda r: r.tag) if r.tag in tags]


def _chord_force(ctx: Any, tag: str) -> float | None:
    """``chord_force_y`` off the roof's lateral record, computed once per model."""
    from typehaus.engineering import lateral_system

    key = f"chord:{id(ctx.model)}"
    if key not in _cache:
        _cache.clear()
        _cache[key] = {r.key: r for r in lateral_system.compute(ctx)}
    record = _cache[key].get(tag)
    return next((q.value for q in getattr(record, "inputs", ()) if q.name == "chord_force_y"),
                None)


def _runs(items: list[tuple[str, float]]) -> str:
    """``truss-000 1,464 lb; truss-001..truss-003 2,000 lb`` — equal neighbours collapse."""
    out: list[list] = []
    for key, value in items:
        if out and round(out[-1][2]) == round(value):
            out[-1][1] = key
        else:
            out.append([key, key, value])
    return "; ".join(f"{a} {v:,.0f} lb" if a == b else f"{a}..{b} {v:,.0f} lb"
                     for a, b, v in out)


def _roof(ctx: Any, model: ResolvedModel, roof: Any, preferences: object) -> list[str]:
    from typehaus.engineering.truss_on_beam import drift_triangle, half_span_ft, truss_widths
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.resolve.roof_geometry import roof_structure_framing

    element = model.plan.by_tag(roof.tag)
    specified = tuple(getattr(element, "specified_reactions", ()) or ())
    structural = getattr(preferences, "structural", None)
    site = getattr(model.plan.project, "site", None)
    ground = getattr(site, "ground_snow_load_psf", None)
    tcdl = float(getattr(structural, "roof_beam_dead_psf", None) or 0.0)
    bcdl = max((r.bottom_chord_dead_psf or 0.0 for r in specified), default=0.0)
    trusses = [m for m in roof.members if m.category == "roof_truss"]
    along = 1 - (1 if roof.ridge_direction == "x" else 0)
    stations = sorted({round(m.p0[along], 4) for m in trusses})
    gaps = [b - a for a, b in zip(stations, stations[1:], strict=False)]
    spacing = f'{statistics.median(gaps) / 0.0254:.0f} IN O.C.' if gaps else NOT_STATED
    first = trusses[0]
    span = ((first.p1[0] - first.p0[0]) ** 2 + (first.p1[1] - first.p0[1]) ** 2) ** 0.5
    spec = roof_structure_framing(model, roof)
    heel = (truss_heel_note(spec) if spec is not None else None) or NOT_STATED
    if heel == "STANDARD HEEL":
        heel += " AT THE OUTSIDE FACE OF BEARING"
    out = [f"{roof.tag}: {len(trusses)} TRUSSES AT {spacing}, "
           f"{element.pitch.rise:g}:{element.pitch.run:g}, SPAN {feet_inches(span)} OUT TO "
           f"OUT, {heel}; BEARS ON {', '.join(element.bearing_refs)}"]
    out.append(f"  DEAD LOAD  TCDL {tcdl:.1f} PSF"
               + (f", BCDL {bcdl:.1f} PSF (CEILING; THE ORDER STATES IT)" if bcdl
                  else ", BCDL 0 (NO CEILING)"))
    flat = (flat_roof_snow_psf(float(ground), roof_snow_thermal_factor(model, roof))
            if ground else None)
    out.append("  SNOW       " + (f"GROUND {ground:g} PSF, FLAT-ROOF {flat:.0f} PSF; " if flat
                                  else f"{NOT_STATED}; ")
               + "UNBALANCED NOT COMPUTED HERE: SUPPLIER APPLIES ASCE 7-16 7.6.1 AT THESE "
                 "C_T / C_E / I_S")
    drifts = [t for src in _drifted_sources(ctx) if (t := drift_triangle(ctx, src)) is not None
              and (src.tag == roof.tag or _abuts(src, roof))]
    surcharge = {m.child_key: max((t.surcharge_psf(m.p0[along]) for t in drifts), default=0.0)
                 for m in trusses}
    if drifts and any(v > 0.0 for v in surcharge.values()):
        out.append("  DRIFT      ASCE 7-16 7.7 STEP DRIFT ADDED TO FLAT-ROOF SNOW, "
                   f"{drifts[0].peak_psf:.1f} PSF PEAK AT THE HOUSE WALL; AT THE TRUSSES: "
                   + ", ".join(f"{k} {v:.1f}" for k, v in surcharge.items() if v > 0.0) + " PSF")
    basis = wind_basis(site) if site is not None else None
    enclosure = ("OPEN FREE ROOF, NO WALL UNDER IT" if all(
        getattr(model.plan.by_tag(t), "element_kind", "") == "Beam"
        for t in element.bearing_refs) else "ENCLOSED, ON WALLS")
    out.append("  WIND       " + (f"V_ULT {basis.speed_mph:.0f} MPH, EXPOSURE {basis.exposure}, "
                                  f"RISK CATEGORY {basis.risk_category}; " if basis
                                  else f"{NOT_STATED}; ") + enclosure)
    half = half_span_ft(ctx, roof)
    rows = [(m.child_key, (flat or 0.0) + surcharge[m.child_key] + tcdl + bcdl, w)
            for m, w in truss_widths(ctx, roof)]
    gravity = [(k, p * w * half) for k, p, w in rows]
    out.append("  MAX GRAVITY REACTION AT EACH BEARING: " + _runs(gravity))
    grouped: dict[tuple, list[str]] = {}
    for row in specified:
        grouped.setdefault((row.member, row.uplift_lb, row.connector, row.basis, row.truss_species,
                            row.capacity_lb, row.reduced_capacity_lb, row.design_uplift_lb),
                           []).append(row.bearing)
    for key, bearings in grouped.items():
        member, uplift, connector, basis, species, full, reduced, design = key
        allowable = allowable_for_model(connector or "")
        nails = (allowable.fasteners.split(" — ")[0].split(" (")[0] if allowable else "")
        tie = (f"{connector}, {species or 'SPECIES NOT STATED'} COLUMN {full:,.0f} LB WITH ALL "
               f"TRUSS NAILS LANDING ({uplift / full:.2f}); FASTENERS {nails}" if full
               else f"{connector or 'no connector'}: no row stated")
        out.append(f"  MAX NET UPLIFT {uplift:,.0f} LB PER HEEL AT {', '.join(bearings)}, "
                   f"{'EVERY TRUSS' if member == '*' else member.upper()} ({basis}); "
                   f"HEEL TIE {tie}")
        if reduced and design:
            out.append(f"    DESIGN UPLIFT {design:,.0f} LB AGAINST THE THREE-NAIL 2x4 CHORD ROW "
                       f"{reduced:,.0f} LB (SIMPSON C-C-2021 P.277 FN. 14): "
                       + ("CLOSED EITHER WAY" if design <= reduced else
                          f"{design / reduced:.2f}, SO THE HEEL STANDS ONLY WITH ALL FIVE TRUSS "
                          "NAILS LANDING"))
    conditions = sorted({r.heel_condition for r in specified if r.heel_condition})
    out.extend(f"  HEEL CONDITION (ORDER): {c.upper()}" for c in conditions)
    out += _chord_bearing(ctx, model, roof, element, tcdl + bcdl, flat, surcharge)
    chord = _chord_force(ctx, roof.tag) if getattr(
        getattr(element, "diaphragm", None), "delivers_to", None) is not None else None
    if chord:
        out.append(f"  DIAPHRAGM CHORD  N-S {chord:,.0f} LB AXIAL IN THE FIRST AND LAST "
                   "TRUSS'S TOP CHORD, ON EVERY TRUSS, WITH THE PEAK SPLICE IN TENSION; "
                   "ADDED TO GRAVITY. NO SPLICE-SLIP VALUE IS ASKED FOR")
    deflection = next((r.deflection for r in specified if r.deflection), ())
    out.append("  DEFLECTION  " + (", ".join(deflection) if deflection else NOT_STATED))
    closed = bool(specified) and all(
        r.design_uplift_lb is not None and r.reduced_capacity_lb is not None
        and r.design_uplift_lb <= r.reduced_capacity_lb for r in specified)
    conditional = bool(specified) and all(
        r.design_uplift_lb is not None and r.capacity_lb is not None
        and r.design_uplift_lb <= r.capacity_lb for r in specified)
    out.append("  SUPPORTING STRUCTURE: "
               + ("CLOSED ON THESE REACTIONS" if closed else
                  "CLOSED ONLY IF THE HEEL CONDITION ABOVE IS CONFIRMED" if conditional
                  else "NOT CLOSED") + " (HEEL TIES; BEARING ON THE SUPPORT GRADED IN THE CALCS)")
    supplied = bool(getattr(element, "published_reactions", ()))
    out.append("  COMPONENT: " + ("SUPPLIER'S SCHEDULE QUOTED; structural.truss_reactions CHECKS "
                                  "IT AGAINST THESE" if supplied else
                                  "OPEN UNTIL THE SUPPLIER'S SEALED DESIGN IS CHECKED AGAINST "
                                  "THESE CRITERIA"))
    return out


def _chord_bearing(ctx: Any, model: ResolvedModel, roof: Any, element: Any, dead: float,
                   flat: float | None, surcharge: dict[str, float]) -> list[str]:
    """The truss's own bottom-chord bearing on its support: the supplier's check, said aloud."""
    from typehaus.engineering.truss_on_beam import beam_bearing, half_span_ft, truss_widths

    half = half_span_ft(ctx, roof)
    peak = max(((flat or 0.0) + surcharge[m.child_key] + dead) * w * half
               for m, w in truss_widths(ctx, roof))
    out = []
    for tag in element.bearing_refs:
        support = model.plan.by_tag(tag)
        if getattr(support, "element_kind", "") == "Beam":
            found = beam_bearing(ctx, roof, support)
            width = (f"{found[0]:g} IN CHORD ON {found[1]:.1f} IN OF BEARING = "
                     f"{peak / (found[0] * found[1]):.0f} PSI" if found else "")
            out.append(f"  CHORD BEARING ON {tag}: THE SUPPLIER CHECKS THE TRUSS CHORD'S OWN "
                       f"FC-PERP (SPF) AT MAX {peak:,.0f} LB, {width}; NOT GRADED HERE "
                       "(THE GLULAM'S OWN BEARING IS)")
        else:
            out.append(f"  CHORD BEARING ON {tag}: THE SUPPLIER CHECKS THE TRUSS CHORD'S OWN "
                       f"FC-PERP (SPF) AT MAX {peak:,.0f} LB ON THE PLATE; NOT GRADED HERE")
    return out


def _abuts(first: Any, second: Any) -> bool:
    from typehaus.engineering.snow_drift import abutting

    return abutting(first.footprint, second.footprint) is not None


def _floor(model: ResolvedModel, floor: Any) -> list[str]:
    order = floor.truss_order
    joists = floor.joists
    resolved = next((f for f in model.floors if f.tag == floor.tag), None)
    west, east = (b.inches for b in order.bearings)
    span_in = east - west
    spacing = joists.spacing.inches if joists.spacing is not None else None
    lines_at = sorted({round(m.p0[1] / 0.0254 if joists.direction == "x" else m.p0[0] / 0.0254, 2)
                       for m in (resolved.members if resolved else ())
                       if m.category == "joist"})
    out = [f"{floor.tag}: {joists.member}, {len(lines_at)} TRUSS LINES"
           + (f" AT {spacing:g} IN O.C." if spacing else "")
           + f", BEARING CENTRES {west:g} IN AND {east:g} IN, SPAN {feet_inches(span_in * 0.0254)}"]
    out.append(f"  LOADS      {order.live_psf:g} PSF LIVE + {order.dead_psf:g} PSF DEAD"
               + (f"; {', '.join(order.deflection)}" if order.deflection else ""))
    uniform = None
    if spacing:
        uniform = (order.live_psf + order.dead_psf) * spacing / 12.0 * span_in / 12.0 / 2.0
        out.append(f"  UNIFORM    {uniform:,.0f} LB PER TRUSS AT EACH BEARING")
    by_line: dict[float, list[Any]] = {}
    for load in order.loads:
        by_line.setdefault(load.line.inches, []).append(load)
    peak = uniform or 0.0
    for line, loads in sorted(by_line.items()):
        plies = max(load.plies for load in loads)
        r_west = r_east = 0.0
        parts = []
        for load in loads:
            x0, x1 = load.x0.inches, load.x1.inches
            centre = (x0 + x1) / 2.0
            each = load.load_lb / load.plies
            r_west += each * (east - centre) / span_in
            r_east += each * (centre - west) / span_in
            parts.append(f"{load.load_lb:,.0f} LB OVER x {x0:g}..{x1:g} IN")
        peak = max(peak, (uniform or 0.0) + max(r_west, r_east))
        out.append(f"  LINE {line:g}  {plies} PLY, " + "; ".join(parts)
                   + f": PER PLY ADDS {r_west:,.0f} LB WEST, {r_east:,.0f} LB EAST"
                   + (f"; MAX {(uniform or 0.0) + r_west:,.0f} / {(uniform or 0.0) + r_east:,.0f}"
                      " LB" if uniform else ""))
    out.extend(f"  ORDER: {text}" for text in order.requests)
    if order.max_reaction_lb:
        verdict = "CLOSED" if peak <= order.max_reaction_lb else "NOT CLOSED"
        out.append(f"  SUPPORTING STRUCTURE: {verdict} - MAX {peak:,.0f} LB AGAINST THE "
                   f"MAKER'S PUBLISHED {order.max_reaction_lb:,.0f} LB AT THIS BEARING")
    else:
        out.append("  SUPPORTING STRUCTURE: the maker publishes no maximum reaction here; the "
                   "bearing and seat are graded in the calcs")
    out.append("  COMPONENT: OPEN UNTIL THE SUPPLIER'S DRAWING CARRIES THESE LOADS AT THESE "
               "LINES AND CONFIRMS EVERY DOUBLED PAIR")
    return out
