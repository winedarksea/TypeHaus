"""``structural.veneer_cavity_width`` — an anchored masonry veneer's tie reach and airspace.

**Subject.** Every anchored wythe (``veneer_ties.anchored_wythes``): masonry on its own air
gap with no ``lateral_support``. None anywhere is N/A, from every wall examined.

**The rule.** IRC R703.8.4 and Table R703.8.4(1), by the profile's ``irc_base``: the back
of the wythe stands at most the row's maximum off the backing (stud or concrete face), and
at least 1" nominal off the sheathing or foam. R703.8.4.1 sets the tie spacing a PASS
prints: 2.67 sf per tie (2 sf over 30 psf ASD wall pressure), 32" o.c. horizontally, 24"
vertically.

**Past every row the adopted edition publishes** the wythe is beyond the prescriptive path:
reported through ``veneer_anchor/<wythe>``, the dated dependency that names what has to
happen instead (decision 10: the ties are detailed to the 2024 IRC's W2.8 row, so the permit
application waits for Minnesota's 2024-based code, with an R104.11 request as the fallback).
Never a silent FAIL.

**Where the ties land** (``veneer_tie_layout``): on studs, never into a concrete stretch, each
within the 2.67 sf (or 2 sf) a tie carries and within 12" of an opening over 16" (R703.8.4.1.1).
**What they must take (owner, G8: a bond break at the base, an adjustable slotted tie):** the
wythe stands on flashing over the court's beam, so the court slides under it and each tie carries
only friction drag, mu x the wythe's weight / the tie count, in both directions of movement, with
wind (TN 3C's tributary method, 2.5 p At for the slotted tie's 3,000 lb/in) against TMS 402-22
Table 6's 200 lb. The friction is a stated upper bound of 1.0 (unverified) until one is sourced
(``veneer_ties.FRICTION_BRICK_ON_FLASHING``); FAIL with no bond break (the ties would take
stiffness x the court's closure).

Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6k, reproduced by
``tests/test_veneer_cavity.py``.
"""

from __future__ import annotations

from typing import Any

from typehaus import veneer_tie_layout, veneer_ties, wind
from typehaus.checks._authoring import engineered
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown

_ID = "structural.veneer_cavity_width"
_CODE = "IRC R703.8.4, R703.8.4.1, R703.8.4.1.1, Table R703.8.4(1)"
_TIE_AREA_FT2 = veneer_ties.TIE_AREA_SF


def _wall_pressure_psf(ctx: CheckContext) -> float | None:
    """ASD Zone 5 wall C&C suction at the mean roof height over one tie's area, or None."""
    basis = wind.wind_basis(ctx.plan.project.site)
    height = wind.mean_roof_height_ft(ctx.model)
    if basis is None or height is None:
        return None
    q_h = wind.velocity_pressure_psf(basis, height)
    return wind.cladding_pressure_asd_psf(q_h, _TIE_AREA_FT2, "5")[1]


def _spacing(pressure: float | None) -> str:
    area = veneer_ties.tie_area_sf(pressure)
    why = ("no design wind is authored, so the high-wind area" if pressure is None
           else f"ASD wall pressure {pressure:.1f} psf")
    return (f"one tie per {area:g} sf ({why}), at most {veneer_ties.TIE_SPACING_H_IN:g}\" "
            f"o.c. horizontally and {veneer_ties.TIE_SPACING_V_IN:g}\" vertically")


def _grade(ctx: CheckContext, wythe: Any, pressure: float | None) -> Finding:
    tags = (wythe.tag,)
    reach = veneer_ties.measure(ctx.model, wythe)
    if reach is None:
        return unknown(_ID, f"{wythe.tag} has no backing wall behind its cavity to measure "
                            f"the tie reach to", tags, code=_CODE)
    tags = (wythe.tag, reach.backing)
    head = (f"{wythe.tag}: back of wythe to {reach.backing}'s structure "
            f"{reach.to_structure_in:.3f}\", airspace {reach.airspace_in:.3f}\" "
            f"(backing {', '.join(reach.backings)})")
    if reach.unbacked_in > 0.5:
        return unknown(_ID, f"{head}; {reach.unbacked_in:.1f}\" of it has no backing",
                       tags, code=_CODE)
    if reach.airspace_in < veneer_ties.MIN_AIRSPACE_IN - 1.0 / 16.0:
        return failed(_ID, f"{head}: under R703.8.4's {veneer_ties.MIN_AIRSPACE_IN:g}\" "
                           f"nominal airspace", tags, code=_CODE,
                      fix="move the wythe off the backing, or thin the backing's foam")
    edition = ctx.profile.irc_base
    rows = veneer_ties.table_rows(edition)
    if rows is None:
        return unknown(_ID, f"{head}; Table R703.8.4(1) is not transcribed for "
                            f"{edition!r}", tags, code=_CODE)
    row = veneer_ties.covering_row(edition, reach.to_structure_in)
    if row is None:
        widest = rows[-1]
        detail = veneer_ties.covering_row(f"{veneer_ties.DETAIL_EDITION} IRC",
                                          reach.to_structure_in)
        return engineered(
            ctx, _ID, f"veneer_anchor/{wythe.tag}",
            f"{head}: past every row of Table R703.8.4(1) as adopted ({edition}; widest "
            f"{widest.tie}, {widest.max_to_backing_in:g}\"), so the ties are beyond the "
            f"prescriptive path. Detailed to the {veneer_ties.DETAIL_EDITION} IRC row "
            f"({detail.tie if detail else 'none covers it'}, {detail.max_to_backing_in:g}\" "
            f"max): the permit application waits for Minnesota's {veneer_ties.DETAIL_EDITION}"
            f"-based code, else an R104.11 request. {veneer_ties.TIE_DETAIL}",
            tags, code=_CODE)
    return passed(_ID, f"{head}: {row.tie}, at most {row.max_to_backing_in:g}\" to the "
                       f"backing ({edition} Table R703.8.4(1)); {_spacing(pressure)}",
                  tags, code=_CODE)


def _layout(ctx: CheckContext, wythe: Any, pressure: float | None) -> Finding | None:
    reach = veneer_ties.measure(ctx.model, wythe)
    if reach is None:
        return None
    lay = veneer_tie_layout.layout(ctx.model, wythe, reach, veneer_ties.tie_area_sf(pressure))
    tags = (wythe.tag, *reach.backings)
    if lay is None:
        return unknown(_ID, f"{wythe.tag}: no stud stands behind the wythe to take a tie",
                       tags, code=_CODE)
    strips = "; ".join(
        f"{s.length_in:.1f}\" in front of {s.wall} (concrete) is tied from the stud "
        f"{s.to_first_tie_in:.2f}\" in, none into the pour" for s in lay.strips)
    head = (f"{wythe.tag}: ties on {len(lay.stations_in)} stud stations over {lay.length_in:.1f}\""
            f", widest tributary {lay.widest_in:.2f}\" against the {lay.allowed_in:.2f}\" "
            f"one tie per {veneer_ties.tie_area_sf(pressure):g} sf on 24\" rows carries"
            + (f"; {strips}" if strips else ""))
    bad = [o for o in lay.openings if o.applies and not o.met]
    reach_in = veneer_tie_layout.OPENING_TIE_REACH_IN
    if lay.widest_in > lay.allowed_in + 1e-6 or bad or not lay.rows_met:
        why = []
        for o in bad:
            miss = [name for name, band in (("head", o.head), ("sill", o.sill))
                    if band is not None and not band.met]
            why.append(f"{o.tag} has no stud tie within {reach_in:g}\" of "
                       + (" and ".join(f"its {m}" for m in miss) if miss else "a jamb"))
        if lay.widest_in > lay.allowed_in + 1e-6:
            why.append(f"the station at {lay.widest_at_in:.1f}\" carries too wide a strip")
        if not lay.rows_met:
            why.append("a tie row is over 24\" from the next")
        return failed(_ID, f"{head}: {'; '.join(why)}", tags, code=_CODE,
                      fix="add a stud, or move the opening onto a stud bay, so every tie "
                          "is on a stud")
    parts = []
    for o in (o for o in lay.openings if o.applies):
        bands = [f"{name} {b.stations} stations, widest {b.max_gap_in:.1f}\" o.c., row "
                 f"{b.row_in:.2f}\" over the base"
                 for name, b in (("head", o.head), ("sill", o.sill)) if b is not None]
        parts.append(f"{o.tag}: jambs {min(g for g in o.near_in if g is not None):.2f}\"; "
                     + "; ".join(bands))
    rows = ", ".join(f"{r:g}" for r in lay.rows_in)
    return passed(_ID, f"{head}; openings over 16\" (R703.8.4.1.1) are tied around the whole "
                       f"perimeter, within {reach_in:g}\" and at most 36\" o.c. ({'; '.join(parts)}"
                       f"); bed-joint rows at {rows}\" over the base, none over 24\" apart",
                  tags, code=_CODE)


def _force(ctx: CheckContext, wythe: Any, pressure: float | None, lay: Any) -> Finding | None:
    """Each tie's drag + wind against Table 6, with the bond break the owner chose (G8)."""
    from typehaus.engineering.thermal_break_joint import NAME
    from typehaus.resolve.assembly_weight import dead_load_plf

    if lay is None or pressure is None:
        return None
    tags = (wythe.tag,)
    k, allow, design = veneer_ties.TIE_TABLE_6[veneer_ties.DETAIL_TIE_KIND]
    factor = (veneer_ties.TIE_FORCE_FACTOR_SOFT if k <= 2500.0
              else veneer_ties.TIE_FORCE_FACTOR_STIFF)
    closure = max((ls.demand for key in ctx.engineering
                   if key.startswith("thermal_break_transfer/")
                   for ls in ctx.engineering[key].limit_states if ls.name == NAME),
                  default=None)
    thermal = max((q.value for key in ctx.engineering
                   if key.startswith("thermal_break_transfer/")
                   for q in ctx.engineering[key].inputs if q.name == "joint_thermal"),
                  default=None)
    from typehaus.engineering.thermal_break_board import temps

    tbasis = temps(ctx)
    opening = (thermal * (tbasis.set_f - tbasis.min_f) / tbasis.closing
               if thermal is not None and tbasis is not None and tbasis.closing > 0 else None)
    runs, bare = veneer_ties.base_flashing(ctx.model, wythe)
    if closure is not None and (not runs or bare > 1.0):
        return failed(
            _ID, f"{wythe.tag}: no bond break and base flashing under {bare:.1f}\" of its first "
                 f"course (R703.8.5), so the brick follows the court and every tie takes "
                 f"{k:,.0f} lb/in x the closure {closure:.4f}\" = {k * closure:,.0f} lb against "
                 f"{allow:g} lb allowable", tags, code=_CODE,
            fix="author the flashing run on the beam top under the first course")
    plf = dead_load_plf(ctx, wythe, wythe.z1_m - wythe.z0_m)
    if plf is None:
        return unknown(_ID, f"{wythe.tag}: a density is not stated, so its weight is not known",
                       tags, code=_CODE)
    height_ft = (wythe.z1_m - wythe.z0_m) / 0.3048
    area_sf = lay.length_in * lay.height_in / 144.0 - sum(
        o.width_in * o.height_in / 144.0 for o in lay.openings)
    weight = plf / height_ft * area_sf
    ties = len(lay.stations_in) * len(lay.rows_in)
    at = veneer_ties.tie_area_sf(pressure)
    wind = factor * pressure * at
    per_mu = weight / ties
    sourced = veneer_ties.FRICTION_BRICK_ON_FLASHING
    mu = sourced if sourced is not None else veneer_ties.FRICTION_UPPER_BOUND
    basis = ("sourced" if sourced is not None else "a stated UPPER BOUND, unverified (no maker "
             "publishes it; McGinley and Borchelt, TMS J. 9(2), tested it and was not opened)")
    drag = mu * per_mu
    span = '' if tbasis is None else f'{tbasis.set_f:g} F set to {tbasis.min_f:g} F'
    total = wind + drag
    text = (f"{wythe.tag}: {veneer_ties.DETAIL_TIE_KIND.replace('_', ' ')} tie, a READING of "
            f"{veneer_ties.DETAIL_TIE_PRODUCT.split(',')[0]} (H&B's sheet does not use the word "
            f"slotted; its own test is over 200 lbf at the 1 1/4\" maximum offset); bond break "
            f"and flashing "
            f"{', '.join(runs)} under the first course; wythe {weight:,.0f} lb on {ties} ties "
            f"({len(lay.stations_in)} stations x {len(lay.rows_in)} rows) = {per_mu:.1f} lb of "
            f"drag per tie per unit friction; wind {factor:g} p At = {factor:g} x {pressure:.2f} "
            f"psf x {at:g} sf = {wind:.1f} lb (TN 3C Table 7, k {k:,.0f} lb/in); friction "
            f"{mu:g} is {basis}, in either direction: summer closing "
            f"{'' if closure is None else f'{closure:.4f}'}\", winter opening about "
            f"{'' if opening is None else f'{opening:.3f}'}\" (the court record's own thermal "
            f"basis, {span}): drag {drag:.1f} + wind {wind:.1f} = "
            f"{total:.1f} lb against {allow:g} lb allowable, {design:g} lb design (TMS 402-22 "
            f"Table 6 via BIA TN 3C), d/c {total / allow:.2f}")
    if total <= allow + 1e-6:
        return passed(_ID, text, tags, code=_CODE)
    return failed(_ID, text, tags, code=_CODE,
                  fix="tighter tie spacing, or a tie with a higher Table 6 row")


@check(Tier.CODE, _ID)
def veneer_cavity_width(ctx: CheckContext) -> list[Finding]:
    wythes = veneer_ties.anchored_wythes(ctx.model)
    if not wythes:
        return [not_applicable(_ID, f"no masonry wythe stands on an air gap, of "
                                    f"{len(ctx.model.walls)} walls examined", code=_CODE)]
    pressure = _wall_pressure_psf(ctx)
    out: list[Finding] = []
    for wythe in wythes:
        out.append(_grade(ctx, wythe, pressure))
        reach = veneer_ties.measure(ctx.model, wythe)
        lay = (veneer_tie_layout.layout(ctx.model, wythe, reach,
                                        veneer_ties.tie_area_sf(pressure))
               if reach is not None else None)
        out += [f for f in (_layout(ctx, wythe, pressure), _force(ctx, wythe, pressure, lay))
                if f]
    return out
