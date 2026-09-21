"""An upper segmental wall's bearing, delivered to a parallel lower wall as a lateral surcharge.

The raised-garden apron (``tiered_retaining/W-RG-*``) is founded on its levelling pad inside
the soil the court walls retain — the court wall's active wedge crosses the pad
(``notes/raised_garden_srw.md`` §6). IBC 2018 §1610.1 adds surcharge pressure to the earth
pressure; this module turns the apron's weight into that surcharge and hands it to
``retaining_basis.Surcharge``, which ``retaining_wall`` and ``retaining_system`` both read.

**Method: a strip load in an elastic half-space, rigid-wall form** — Terzaghi's (1954)
doubling of the Boussinesq strip solution, ``sigma_h = (2q/pi)(beta - sin(beta) cos(2 alpha))``
(NAVFAC DM 7.02 Fig. 7-11; AASHTO LRFD Eq. 3.11.6.2-5). The doubling is the unyielding-wall
image, which is the condition the court is graded at (at-rest, ``retaining_system``); a
1'-0" strip is not an infinite surcharge, so ``K q`` over the full height would overstate it
several-fold.

**q is NET of the soil the unit displaces.** The court's Rankine free body already carries a
level backfill up to its retained surface, so the ground the block stands in is counted
there; adding the whole block weight would count that column twice. What the pad carries
beyond the level-backfill model is ``W/B - gamma h``. Not credited, and conservative: the
yard beyond the apron is below the retained surface the free body assumes, and the strip's
vertical stress spreading onto the heel.

The pressure is integrated on two planes: the heel's **virtual back** (stability — sliding,
overturning, bearing, the loop) and the **stem face** (stem flexure).

Oracle: ``notes/sunken_garden_court_free_body.md`` §4c (closed form, by hand), reproduced by
``tests/test_retaining_court.py``; the apron's reading is ``segmental_wall.reading``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.item import Quantity, item_id
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import Surcharge, _geometry
from typehaus.engineering.segmental_wall import KIND as TIER_KIND
from typehaus.engineering.segmental_wall import lower_tiers, reading, segmental_walls

_M_PER_FT = 0.3048
_SIMPSON_PANELS = 400


def strip_load(q_psf: float, a_ft: float, b_ft: float, h_ft: float) -> tuple[float, float]:
    """``(P plf, height of P above the plane's base ft)`` on a wall plane ``h`` deep under a
    strip ``b`` wide starting ``a`` behind it, by integrating the pressure (Simpson)."""
    if q_psf <= 0.0 or b_ft <= 0.0 or h_ft <= 0.0:
        return 0.0, 0.0

    def sigma(z: float) -> float:
        if z <= 0.0:
            z = 1e-9
        a1, a2 = math.atan(a_ft / z), math.atan((a_ft + b_ft) / z)
        beta = a2 - a1
        return 2.0 * q_psf / math.pi * (beta - math.sin(beta) * math.cos(a1 + a2))

    n = _SIMPSON_PANELS
    dz = h_ft / n
    force = moment = 0.0
    for i in range(n + 1):
        z = i * dz
        weight = 1.0 if i in (0, n) else (4.0 if i % 2 else 2.0)
        s = sigma(z)
        force += weight * s
        moment += weight * s * (h_ft - z)
    force *= dz / 3.0
    moment *= dz / 3.0
    return force, (moment / force if force else 0.0)


@dataclass(frozen=True)
class TierLoad:
    """The surcharge on one lower wall, and what its record prints and fingerprints."""

    surcharge: Surcharge
    notes: tuple[str, ...]
    inputs: tuple[Quantity, ...]


def _projections(polygon, origin, normal) -> list[float]:  # type: ignore[no-untyped-def]
    return [(x - origin[0]) * normal[0] + (y - origin[1]) * normal[1] for x, y in polygon]


def _structure(resolved):  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    return next((layer for layer in resolved.layers
                 if layer.function == LayerFunction.STRUCTURE.value), None)


def _one(ctx: EngineeringContext, apron, court, soil_pcf: float
         ) -> tuple[TierLoad | None, str | None]:  # type: ignore[no-untyped-def]
    source = item_id(TIER_KIND, apron.tag)
    read, missing = reading(ctx, apron)
    if read is None:
        return None, f"{source}'s weight on its pad ({'; '.join(missing)})"
    geometry, _ = _geometry(ctx, court)
    if geometry is None:
        return None, None      # the court record already names what it lacks
    resolved = {w.tag: w for w in ctx.model.walls}
    mine, theirs = resolved.get(court.tag), resolved.get(apron.tag)
    court_face, apron_face = (_structure(mine) if mine else None,
                              _structure(theirs) if theirs else None)
    if court_face is None or apron_face is None:
        return None, f"resolved STRUCTURE layers on {court.tag} and {apron.tag}"

    (x0, y0), (x1, y1) = mine.axis
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    normal = (-(y1 - y0) / length, (x1 - x0) / length)
    theirs_p = _projections(apron_face.polygon, (x0, y0), normal)
    side = 1.0 if sum(theirs_p) >= 0.0 else -1.0
    face = max(side * p for p in _projections(court_face.polygon, (x0, y0), normal))
    near, far = min(side * p for p in theirs_p), max(side * p for p in theirs_p)
    near, far, face = near / _M_PER_FT, far / _M_PER_FT, face / _M_PER_FT
    if near < face - 1e-6:
        return None, f"{apron.tag} on the retained side of {court.tag}, not through it"
    heel_edge = face + geometry.heel_ft

    surface = court.bottom_elevation.meters + court.unbalanced_fill.meters
    drop_ft = max(surface - apron.bottom_elevation.meters, 0.0) / _M_PER_FT
    displaced_ft = max(min(apron.top_elevation.meters, surface)
                       - apron.bottom_elevation.meters, 0.0) / _M_PER_FT
    width = read.section.unit_depth_ft
    gross = read.weight_plf / width
    net = gross - soil_pcf * displaced_ft

    back_a = max(near - heel_edge, 0.0)
    back_b = far - max(near, heel_edge)
    back_h = geometry.retained_height_ft - drop_ft
    lateral, arm = strip_load(net, back_a, back_b, back_h)
    gross_lateral = strip_load(gross, back_a, back_b, back_h)[0]
    stem_h = geometry.retained_height_ft - geometry.footing_depth_ft - drop_ft
    stem_p, stem_arm = strip_load(net, near - face, far - near, stem_h)

    surcharge = Surcharge(axial_plf=0.0, moment_plf=0.0, arm_ft=0.0, source=source,
                          lateral_plf=lateral, lateral_arm_ft=arm,
                          stem_moment_plf=stem_p * stem_arm)
    note = (
        f"APRON SURCHARGE via {source}: {read.weight_plf:,.0f} plf of SRW unit on a "
        f"{width * 12:.0f}\" pad {drop_ft:.2f}' below this wall's retained surface, "
        f"{back_a:.2f}' behind the heel's virtual back — {gross:,.0f} psf gross, "
        f"{net:,.0f} psf NET of the {displaced_ft:.2f}' of {soil_pcf:.0f} pcf soil the "
        f"level-backfill free body already carries. As a rigid-wall Boussinesq strip "
        f"(IBC 2018 §1610.1; Terzaghi 1954, NAVFAC DM 7.02 Fig. 7-11): {lateral:,.0f} plf at "
        f"{arm:.2f}' above the footing underside, into sliding and overturning; "
        f"{stem_p * stem_arm:,.0f} ft-lb/ft at the stem base. At the GROSS {gross:,.0f} psf the "
        f"thrust term would be {gross_lateral:,.0f} plf — the sensitivity, not the graded "
        f"case. Not credited: the yard below the retained surface beyond the apron, and the "
        f"strip's stress spreading onto the heel.",)
    if net <= 0.0:
        note += (f"The unit is lighter than the soil it displaces at {soil_pcf:.0f} pcf, so "
                 "the net surcharge is a relief and is not credited.",)
    tag = apron.tag
    inputs = (Quantity(f"surcharge_{tag}_q_net", net, "psf", 1.0),
              Quantity(f"surcharge_{tag}_lateral", lateral, "plf", 1.0),
              Quantity(f"surcharge_{tag}_arm", arm, "ft", 0.01))
    return TierLoad(surcharge, note, inputs), None


def _combine(first: TierLoad, second: TierLoad) -> TierLoad:
    a, b = first.surcharge, second.surcharge
    lateral = a.lateral_plf + b.lateral_plf
    arm = ((a.lateral_plf * a.lateral_arm_ft + b.lateral_plf * b.lateral_arm_ft) / lateral
           if lateral else 0.0)
    return TierLoad(
        Surcharge(axial_plf=0.0, moment_plf=0.0, arm_ft=0.0,
                  source=f"{a.source}, {b.source}", lateral_plf=lateral, lateral_arm_ft=arm,
                  stem_moment_plf=a.stem_moment_plf + b.stem_moment_plf),
        first.notes + second.notes, first.inputs + second.inputs)


def court_surcharges(ctx: EngineeringContext, soil_pcf: float
                     ) -> tuple[dict[str, TierLoad], dict[str, list[str]]]:
    """``({lower wall tag: TierLoad}, {lower wall tag: [what could not be read]})`` for every
    parallel tier ``segmental_wall.lower_tiers`` finds. A perpendicular return meets the lower
    wall end-on and loads no length of it, so it carries nothing here."""
    loads: dict[str, TierLoad] = {}
    missing: dict[str, list[str]] = {}
    for apron in segmental_walls(ctx):
        for tier in lower_tiers(ctx, apron):
            if not tier.parallel:
                continue
            court = ctx.plan.by_tag(tier.tag)
            load, gap = _one(ctx, apron, court, soil_pcf)
            if gap is not None:
                missing.setdefault(tier.tag, []).append(gap)
            if load is None:
                continue
            loads[tier.tag] = _combine(loads[tier.tag], load) if tier.tag in loads else load
    return loads, missing
