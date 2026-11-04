"""``structural.veneer_cavity_width`` — an anchored masonry veneer's tie reach and airspace.

**Subject.** Every anchored wythe (``veneer_ties.anchored_wythes``): masonry on its own air
gap with no ``lateral_support``. None anywhere is N/A, from every wall examined.

**The rule.** IRC R703.8.4 and Table R703.8.4(1), by the profile's ``irc_base``: the back
of the wythe stands at most the row's maximum off the backing (stud or concrete face), and
at least 1" nominal off the sheathing or foam. R703.8.4.1 sets the tie spacing a PASS
prints: 2.67 sf per tie (2 sf over 30 psf ASD wall pressure), 32" o.c. horizontally, 24"
vertically.

**Past every row the adopted edition publishes** the wythe is beyond the prescriptive path:
reported through ``veneer_anchor/<wythe>``, the engineered item that names what has to be
produced instead. Never a silent FAIL.

Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6k, reproduced by
``tests/test_veneer_cavity.py``.
"""

from __future__ import annotations

from typing import Any

from typehaus import veneer_ties, wind
from typehaus.checks._authoring import engineered
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown

_ID = "structural.veneer_cavity_width"
_CODE = "IRC R703.8.4, R703.8.4.1, Table R703.8.4(1)"
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
        return engineered(
            ctx, _ID, f"veneer_anchor/{wythe.tag}",
            f"{head}: past every row of Table R703.8.4(1) as adopted ({edition}; widest "
            f"{widest.tie}, {widest.max_to_backing_in:g}\"), so the ties are beyond the "
            f"prescriptive path",
            tags, code=_CODE)
    return passed(_ID, f"{head}: {row.tie}, at most {row.max_to_backing_in:g}\" to the "
                       f"backing ({edition} Table R703.8.4(1)); {_spacing(pressure)}",
                  tags, code=_CODE)


@check(Tier.CODE, _ID)
def veneer_cavity_width(ctx: CheckContext) -> list[Finding]:
    wythes = veneer_ties.anchored_wythes(ctx.model)
    if not wythes:
        return [not_applicable(_ID, f"no masonry wythe stands on an air gap, of "
                                    f"{len(ctx.model.walls)} walls examined", code=_CODE)]
    pressure = _wall_pressure_psf(ctx)
    return [_grade(ctx, wythe, pressure) for wythe in wythes]
