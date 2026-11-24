"""``structural.veneer_bed_bearing`` — a beam on a stone bed, carrying a wythe off its centre.

**Subject.** Every ``FoundationWall`` a ``FootingBedding`` hosts (founded on the bed itself)
that carries another wall's masonry on its top: catlin's ``W-SG-BRKBM`` under ``W-B-BRICK``.
None is N/A, from every bedded wall examined.

**What it grades**, at each interface it actually has (F-04):

* the wythe's weight and the beam's own, per foot, taken from the assemblies' densities and
  heights, acting at their centroids across the beam, plus **the veneer's wind base shear** at
  the beam's top, 17.75" over the bed: the strip between the flashing (a pin) and the first tie
  row takes half of p x its height at the base, p the ties' own ASD pressure, and the moment
  that shear makes is the worst sign added to the eccentricity;
* the resultant's offset from the contact's centre against the kern (B/6). Outside the kern
  the contact is partial, the far edge lifts and the peak is 2P / (3a) over 3a, ``a = B/2 - e``;
  at or past the edge there is no contact at all, which FAILs;
* that peak against the site's presumptive bearing (IRC Table R401.4.1, the footing checks'
  value), and the soil under the bed at the beam's average pressure on its width, no spread
  through the stone credited.

**Why widening the stone is no fix.** The contact is the beam's own bottom, ``min(beam,
bed)``: stone south of the beam neither widens it nor moves the resultant onto it, and a
one-sided bed moves the bed's centroid off the beam's. The fix is to grade the contact as it is.

**Not graded:** the tilt a one-sided peak settles into (the beam is cast with the court walls'
toes, which hold it), and the wythe's own bearing on the beam top. Oracle:
``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6l, ``tests/test_veneer_bed.py``.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Polygon

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.soil import site_soil_bearing_psf
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.model.structure import FootingBedding
from typehaus.resolve.assembly_weight import KG_PER_M_TO_PLF, dead_load_plf

_ID = "structural.veneer_bed_bearing"
_CODE = "IRC R401.4.1, R403.1.1"
_IN = 0.0254
_Z_TOL_M = 0.05


def _structure(wall: Any) -> Any:
    return next(ly for ly in wall.layers if ly.function == "structure" and ly.polygon)


def _band_in(layer: Any, normal: tuple[float, float], origin: tuple[float, float]):
    offs = [((x - origin[0]) * normal[0] + (y - origin[1]) * normal[1]) / _IN
            for x, y in layer.polygon]
    return min(offs), max(offs)


def _beam_plf(ctx: CheckContext, beam: Any) -> float | None:
    layer = _structure(beam)
    density = next((m.density for m in ctx.plan.library.materials
                    if m.tag == layer.material_ref and m.density), None)
    if density is None:
        return None
    return layer.thickness_m * (beam.z1_m - beam.z0_m) * density * KG_PER_M_TO_PLF


def _wind_base_shear_plf(ctx: CheckContext, wythe: Any) -> float:
    """Half of p x the height below the first tie row, per foot of wythe, or 0 if unknown."""
    from typehaus import veneer_tie_layout, veneer_ties
    from typehaus.checks.structural.veneer_cavity import _wall_pressure_psf

    pressure = _wall_pressure_psf(ctx)
    reach = veneer_ties.measure(ctx.model, wythe) if veneer_ties.is_anchored_wythe(
        ctx.model, wythe) else None
    lay = (veneer_tie_layout.layout(ctx.model, wythe, reach, veneer_ties.tie_area_sf(pressure))
           if reach is not None else None)
    if pressure is None or lay is None or not lay.rows_in:
        return 0.0
    return pressure * (lay.rows_in[0] / 12.0) / 2.0


@check(Tier.STRUCTURAL, _ID)
def veneer_bed_bearing(ctx: CheckContext) -> list[Finding]:
    beds = {e.host_ref: e for e in ctx.plan.all_elements() if isinstance(e, FootingBedding)}
    out: list[Finding] = []
    examined = 0
    for beam in ctx.model.walls:
        bed = beds.get(beam.tag)
        if bed is None:
            continue
        examined += 1
        slab = Polygon(_structure(beam).polygon)
        carried = [w for w in ctx.model.walls if w.tag != beam.tag
                   and abs(w.z0_m - beam.z1_m) <= _Z_TOL_M
                   and Polygon(_structure(w).polygon).intersection(slab).area > 1e-6]
        if not carried:
            continue
        (ax, ay), (bx, by) = beam.axis
        length = math.hypot(bx - ax, by - ay)
        normal = (-(by - ay) / length, (bx - ax) / length)
        origin = (ax, ay)
        lo, hi = _band_in(_structure(beam), normal, origin)
        width_in = hi - lo
        contact = min(width_in, bed.width.inches) if bed.width is not None else width_in
        centre = (lo + hi) / 2.0
        tags = (beam.tag, bed.tag, *(w.tag for w in carried))
        loads = [(w.tag, dead_load_plf(ctx, w, w.z1_m - w.z0_m),
                  sum(_band_in(_structure(w), normal, origin)) / 2.0) for w in carried]
        own = _beam_plf(ctx, beam)
        soil = site_soil_bearing_psf(ctx.plan, ctx.profile)
        if own is None or soil is None or any(plf is None for _t, plf, _y in loads):
            out.append(unknown(_ID, f"{beam.tag} on {bed.tag}: a density or the site's "
                                    f"presumptive bearing is not stated", tags, code=_CODE))
            continue
        total = own + sum(plf for _t, plf, _y in loads)
        resultant = (own * centre + sum(plf * y for _t, plf, y in loads)) / total
        ecc_dead = abs(resultant - centre)
        shear = _wind_base_shear_plf(ctx, carried[0])
        arm_in = (beam.z1_m - beam.z0_m) / _IN
        ecc = ecc_dead + (shear * arm_in / total if shear else 0.0)
        kern = contact / 6.0
        sides = ", ".join(f"{t} {plf:.1f}" for t, plf, _y in loads)
        wind = (f", wind base shear {shear:.1f} plf x {arm_in:.2f}\" = "
                f"{shear * arm_in:.0f} lb-in/ft moves it {shear * arm_in / total:.2f}\" "
                f"(worst sign)" if shear else "")
        head = (f"{beam.tag} on {bed.tag}: {sides} + beam {own:.1f} = {total:.1f} plf, resultant "
                f"{ecc_dead:.2f}\"{wind} = {ecc:.2f}\" off the {contact:g}\" contact's centre "
                f"(kern {kern:.2f}\")")
        if ecc >= contact / 2.0:
            out.append(failed(_ID, f"{head}: past the contact's edge, the beam does not sit on "
                                   f"its bed", tags, code=_CODE,
                              fix="widen the beam under the load, not the stone beside it"))
            continue
        peak_psf = total / (contact / 12.0) if ecc <= kern else \
            2.0 * total / (3.0 * (contact / 2.0 - ecc) / 12.0)
        avg_psf = total / (width_in / 12.0)
        how = ("inside the middle third, full contact" if ecc <= kern else
               f"outside the middle third: partial contact over {3 * (contact / 2 - ecc):.2f}\" "
               f"of {contact:g}\", the far edge lifts")
        text = (f"{head}, {how}; peak {peak_psf:,.0f} psf of the site's {soil:,.0f} psf "
                f"({peak_psf / soil:.2f}); soil under the {bed.undercut.inches:g}\" stone at "
                f"{avg_psf:,.0f} psf with no spread credited ({avg_psf / soil:.2f})")
        if peak_psf <= soil:
            out.append(passed(_ID, text, tags, code=_CODE))
        else:
            out.append(failed(_ID, text, tags, code=_CODE,
                              fix="widen the beam's bottom to bring the resultant inside "
                                  "the kern"))
    return out or [not_applicable(
        _ID, f"no bedded wall carries masonry on its top, of {examined} bedded walls examined",
        code=_CODE)]
