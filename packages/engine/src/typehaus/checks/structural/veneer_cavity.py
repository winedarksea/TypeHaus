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
**What they must take:** the court's closure on the veneer's own ties (the thermal-break
record's joint row) against the travel a tie publishes (UNKNOWN while none is published).

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
#: Max movement between an adjustable tie's pintle and eye (TMS 402-16 as summarised in
#: Heckmann's 2018 catalog p.70); no maker publishes travel normal to the wall.
_TIE_PLAY_IN = 1.0 / 16.0
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
    if lay.widest_in > lay.allowed_in + 1e-6 or bad:
        why = ([f"{o.tag} has no stud tie within {reach_in:g}\" of a jamb" for o in bad]
               or [f"the station at {lay.widest_at_in:.1f}\" carries too wide a strip"])
        return failed(_ID, f"{head}: {'; '.join(why)}", tags, code=_CODE,
                      fix="add a stud, or move the opening onto a stud bay, so every tie "
                          "is on a stud")
    near = ", ".join(f"{o.tag} {min(g for g in o.near_in if g is not None):.2f}\""
                     for o in lay.openings if o.applies)
    return passed(_ID, f"{head}; openings over 16\" (R703.8.4.1.1) have a stud tie within "
                       f"{reach_in:g}\" of each jamb ({near})", tags, code=_CODE)


def _travel(ctx: CheckContext, wythe: Any) -> Finding | None:
    """The veneer ties take the court-to-house closure the thermal-break record bounds."""
    from typehaus.engineering.thermal_break_joint import NAME

    closure = [ls.demand for key in ctx.engineering if key.startswith("thermal_break_transfer/")
               for ls in ctx.engineering[key].limit_states if ls.name == NAME]
    if not closure:
        return None
    moved = max(closure)
    return unknown(
        _ID, f"{wythe.tag}: the ties go in with the boards and take the court's {moved:.4f}\" "
             f"of closure; an adjustable tie's pintle and eye fit to at most {_TIE_PLAY_IN:g}\" "
             f"({moved / _TIE_PLAY_IN:.2f}x) and no tie maker publishes travel normal to the wall",
        (wythe.tag,), code=_CODE,
        fix="a tie with published wall-normal travel of at least the closure, or the "
            "owner's choice among the options (the joint's width, the tie rows' heights)")


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
        out += [f for f in (_layout(ctx, wythe, pressure), _travel(ctx, wythe)) if f]
    return out
