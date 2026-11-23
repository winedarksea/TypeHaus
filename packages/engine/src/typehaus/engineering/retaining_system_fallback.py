"""The printed fallback for the court's sliding rows: a buried lean wall (free body §15h).

The design is closed on specified soil parameters a site report must confirm. If the report
comes in short, or the bed bottom is seen to be clay or silt at excavation, the drawing's
fallback is built: a plain lean-concrete wall, :data:`WIDTH_IN` wide, standing on the native
at the bed bottom and rising through the stone to the unopposed footing's underside, along
that footing. It is formed in the open dig before any stone goes in and the footing is cast
on it. These rows pre-check it on the IBC Table 1806.2 presumptions it would be built under.

Its credit is the lesser of two things. One is the stone's class-3 lateral bearing on the
wall's face, measured from the court floor (IBC §1806.3.1 lets it combine with friction;
x 0.6 with the stone submerged). The other is what the plain wall carries as a
cantilever from the footing: phi Mn = 0.60 x 5 sqrt(f'c) S (ACI 318-19 §14.5.2.1) over the
passive's centroid.
"""

from __future__ import annotations

from typehaus.engineering.item import LimitState
from typehaus.engineering.retaining_basis import REQUIRED_FS
from typehaus.engineering.soil import SOIL_UNIT_WEIGHT_BAND_PCF

_LOW_PCF = SOIL_UNIT_WEIGHT_BAND_PCF[0]

WIDTH_IN = 12.0
#: Lean-concrete strength the fallback specifies.
FALLBACK_FC_PSI = 2500.0
#: ACI 318-19 Table 21.2.1, plain concrete.
_PHI_PLAIN = 0.60
#: Submerged stone carries about its buoyant share of the dry lateral bearing.
SUBMERGED_FACTOR = 0.6


def _wall(ctx, body):  # type: ignore[no-untyped-def]
    """``(length ft, top depth ft, bottom depth ft, footing tag)`` below the court floor for
    the unopposed member's footing, or None."""
    from typehaus.engineering.retaining_system_body import _footing_of

    opposed = {p.tag for p in body.pushes for o in body.pushes
               if o is not p and abs(p.direction[0] * o.direction[0]
                                     + p.direction[1] * o.direction[1]) > 0.99}
    lone = [p for p in body.pushes if p.tag not in opposed]
    if not lone:
        return None
    footing = _footing_of(ctx, lone[0].tag)
    bed = next((b for b in ctx.model.footing_beddings if footing and b.host == footing.tag),
               None)
    if bed is None:
        return None
    floor = max(p.z1_ft for p in body.prisms if p.label.startswith("footing:"))
    bottom = (bed.soakaway_z0_m if bed.soakaway_z0_m is not None else bed.z0_m) / 0.3048
    return (lone[0].width_ft, floor - bed.z1_m / 0.3048, floor - bottom, footing.tag,
            lone[0].direction)


def fallback_rows(ctx, body, members, cases_levels, staged_fn, lateral_psf_per_ft: float):  # type: ignore[no-untyped-def]
    """Rows for the fallback on a presumptive ``body`` (bed friction 0.35). The wall resists
    along the unopposed member's push only, so each FS is the directional root."""
    from typehaus.engineering.retaining_system_staged import directional_fs

    wall = _wall(ctx, body)
    if wall is None:
        return []
    length, z1, z2, tag, along = wall
    passive = 0.5 * lateral_psf_per_ft * (z2 * z2 - z1 * z1)
    section = 12.0 * WIDTH_IN ** 2 / 6.0
    phi_mn = _PHI_PLAIN * 5.0 * FALLBACK_FC_PSI ** 0.5 * section / 12.0
    arm = (2.0 / 3.0) * (z2 ** 3 - z1 ** 3) / (z2 ** 2 - z1 ** 2) - z1
    cap = phi_mn / arm
    rows = []
    for key, label in (("perched", "perched at H/2"), ("flooded court", "flooded court")):
        water = cases_levels[key]
        credit = min(passive * (SUBMERGED_FACTOR if water.both_sides else 1.0), cap) * length
        fs = directional_fs(body.resultant_vector(water), body.friction * body.weight(water),
                            credit, along)
        rows.append(_row(f"fallback lean wall under {tag}: sliding, {label}", fs, credit,
                         passive, cap, length, z1, z2))
    credit = min(passive, cap) * length
    fs = staged_fn(body, (credit, along))
    rows.append(_row(f"fallback lean wall under {tag}: staged backfill", fs, credit,
                     passive, cap, length, z1, z2))
    return rows


def _row(name, fs, credit, passive, cap, length, z1, z2) -> LimitState:  # type: ignore[no-untyped-def]
    return LimitState(
        name, REQUIRED_FS, fs, "",
        f"IRC R404.4 on IBC Table 1806.2 presumptions (bed friction 0.35) + the wall's "
        f"{credit:,.0f} lb: the lesser of class-3 lateral bearing {passive:,.0f} plf "
        f"({z1:.2f}'-{z2:.2f}' below the court floor, IBC §1806.3.1) and the plain "
        f"{WIDTH_IN:.0f}\" wall's cantilever {cap:,.0f} plf (0.60 x 5 sqrt({FALLBACK_FC_PSI:,.0f}"
        f") S over the passive centroid), over {length:.2f}'", is_safety_factor=True)


def fallback_states(ctx, ref: str, walls: list, members, floor_ft: float, stem_ft: float  # type: ignore[no-untyped-def]
                    ) -> list[LimitState]:
    """The fallback's rows at 110 pcf on the presumptive bed (what it is built under)."""
    from typehaus.engineering import retaining_system_staged as staged
    from typehaus.engineering.retaining_system_body import footing_plane_body
    from typehaus.engineering.retaining_system_cases import waters
    from typehaus.engineering.soil import aggregate_bed

    bed = aggregate_bed()
    body, missing = footing_plane_body(ctx, ref, walls, members,
                                       soil_pcf=_LOW_PCF,
                                       friction=bed.friction_coefficient)
    if body is None or missing:
        return []
    levels, _ = waters(ctx, body)
    return fallback_rows(ctx, body, members, levels,
                         lambda b, key: staged.staged(b, members, floor_ft, stem_ft, key)[0],
                         bed.lateral_bearing_psf_per_ft)

