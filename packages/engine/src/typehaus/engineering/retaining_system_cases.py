"""The court's case set: soil, water on both sides, uplift, two sliding planes (free body §15).

One drawing-backed set, each case naming its plane, the body that moves and what resists:

* **footing plane** (concrete on the stone bed, mu 0.35, IBC Table 1806.2 class 3): the cast
  loop with every spliced wall and the retaining heels' soil (``retaining_system_body``);
* **deep plane** (stone and native on native at the soakaway course's bottom, mu 0.25, class
  4): the same body plus the beds and the native core they enclose. No frontal resistance
  against the house is credited, and no passive.

Water: **perched** at H/2 over the footing top on the retained side, the drain column taken as
blocked and the bed still draining (no uplift; the water thrust unbalanced); **retained
side full height, court empty** (the same, to the terrace); **flooded court**, one level on
both sides at the court floor (the overflow failed), so the water forces close on themselves
and uplift remains; and for the deep plane the soakaway **full to its lip**.

A drained zone is credited only the pressure change its geometry gives: a vertical column
moves a perched head's force from pore pressure to seepage force and the same force reaches
the body, so the perched case takes it as blocked and nothing else is changed by it.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.retaining_basis import REQUIRED_FS
from typehaus.engineering.retaining_system_body import (
    DRY,
    STONE_PCF,
    Body,
    Member,
    Water,
    deep_plane_body,
    footing_plane_body,
)
from typehaus.engineering.retaining_system_restraint import house_side_weight

_M = 0.3048

#: Cases whose answer is an owner decision still open: under 1.50 they hold the record
#: INCOMPLETE (named) instead of OVER. Empty since the soil decision (2026-11-23).
PENDING_CASES: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Case:
    key: str
    label: str
    plane: str           # "footing" | "deep"
    graded: bool


#: Cases the owner has excluded by a stated basis: printed once, never graded.
OWNER_BASIS = {
    "perched snow": (
        "OWNER BASIS, stated: full ground snow on the terrace and perched water at H/2 (a "
        "blinded drain) are taken as NOT concurrent; each is graded alone. Combined they would "
        "read FS {fs:.2f} at {pcf:.0f} pcf, printed for transparency. NOT COVERED (owner): that "
        "combination; lateral frost thrust in the top 42\" of retained fill; seasonal thermal "
        "ratcheting under the sustained thrust."),
}

CASES = (
    Case("dry", "sliding, dry", "footing", True),
    Case("perched", "sliding, perched at H/2", "footing", True),
    Case("retained full", "sliding, retained water to the terrace, court empty", "footing",
         False),
    Case("snow", "sliding, ground snow on the terrace", "footing", True),
    Case("wind", "sliding, dry with the structure's wind on the court (D + H + 0.6W)",
         "footing", True),
    # Owner's stated basis (2026-11-23): full ground snow and perched water at H/2 are not
    # concurrent. The combination is printed once, never graded (free body §15k).
    Case("perched snow", "sliding, perched at H/2 under snowmelt", "footing", False),
    Case("flooded court", "sliding, court flooded to its lowest threshold", "footing", True),
    Case("deep dry", "deep plane, dry", "deep", False),
    Case("deep, soakaway full", "deep plane, soakaway full to its lip", "deep", True),
    Case("deep flooded", "deep plane, flooded court", "deep", False),
)


def members_for(ctx, walls: list, built: list, soil, soil_pcf: float) -> list[Member]:  # type: ignore[no-untyped-def]
    """``retaining_system._members`` output, as the body module reads it."""
    from typehaus.engineering.tier_surcharge import court_surcharges

    tiers, _ = court_surcharges(ctx, soil_pcf)
    by_tag = {w.tag: w for w in walls}
    out = []
    for m in built:
        resolved = next(w for w in ctx.model.walls if w.tag == m.tag)
        wall = by_tag[m.tag]
        out.append(Member(
            m.tag, m.push, tuple((a / _M, b / _M) for a, b in resolved.axis),
            soil.at_rest_efp_psf_per_ft,
            tiers[m.tag].surcharge.lateral_plf if m.tag in tiers else 0.0,
            (wall.bottom_elevation.meters + wall.unbalanced_fill.meters) / _M))
    return out


def _lip_ft(ctx, body: Body) -> float | None:  # type: ignore[no-untyped-def]
    """The soakaway's overflow lip: an authored ``overflow_invert`` on a bed in the loop."""
    from typehaus.model.structure import FootingBedding

    hosts = {p.label.split(":")[1] for p in body.prisms if ":" in p.label}
    lips = [b.overflow_invert.meters / _M for b in ctx.plan.all_elements()
            if isinstance(b, FootingBedding) and b.overflow_invert is not None
            and b.host_ref in hosts]
    return max(lips) if lips else None


def court_wind(ctx, body: Body) -> tuple[float, tuple[float, float]]:  # type: ignore[no-untyped-def]
    """``(lb, direction)``: the ASD (0.6W) E-W base shear of every cast column standing on
    the court (``pier_basis.cast_piers``, read, never copied), along the side walls' push
    axis. IBC §1807.2.3's FS 1.5 is a service check, so the wind enters at ASCE 7 §2.4.1's
    0.6W with the dead load whole; wet and snow cases are not taken concurrent with it."""
    from shapely.geometry import Point, Polygon

    from typehaus.engineering.pier_basis import cast_piers

    hull = Polygon([pt for p in body.prisms if p.label.startswith("footing:") and p.shape
                    is not None for pt in p.shape.exterior.coords]).convex_hull
    total = 0.0
    for pier in cast_piers(ctx):
        post = ctx.plan.by_tag(pier.tag)
        where = getattr(post, "position", None)
        if where is not None and hull.contains(Point(where.x.meters / _M, where.y.meters / _M)):
            total += pier.wind_ew_base_shear_lb
    opposed = [p.direction for p in body.pushes for o in body.pushes if o is not p
               and abs(p.direction[0] * o.direction[0] + p.direction[1] * o.direction[1]) > 0.99]
    return total, (opposed[0] if opposed else (1.0, 0.0))


def _threshold_ft(ctx, body: Body) -> float | None:  # type: ignore[no-untyped-def]
    """The lowest door threshold opening onto a floor inside the loop: where a flooded court
    overflows (into the house). None where no door opens onto it."""
    from shapely.geometry import Polygon

    loop = Polygon([pt for p in body.prisms if p.label.startswith("footing:") and p.shape
                    is not None for pt in p.shape.exterior.coords]).convex_hull
    decks = {s.tag for s in ctx.model.solids if s.category in ("slab", "slab_band")
             and Polygon([(x / _M, y / _M) for x, y in s.outline]).buffer(0).within(
                 loop.buffer(0.5))}
    crests = []
    for opening in ctx.model.openings:
        doorway = getattr(opening, "doorway", None)
        place = getattr(doorway, "exterior_placement", None)
        floors = {f.deck_tag for f in getattr(doorway, "adjacent_floors", ()) or () if f}
        crest = getattr(place, "threshold_crest_z_m", None)
        if crest is not None and floors & decks:
            crests.append(crest / _M)
    return min(crests) if crests else None


def waters(ctx, body: Body) -> tuple[dict[str, Water], list[str]]:  # type: ignore[no-untyped-def]
    floor = max(p.z1_ft for p in body.prisms if p.label.startswith("footing:"))
    top = max(p.top_ft for p in body.pushes)
    height = top - body.plane_ft
    site = getattr(getattr(ctx.plan, "project", None), "site", None)
    snow = getattr(site, "ground_snow_load_psf", None) or 0.0
    flood = _threshold_ft(ctx, body) or floor
    wind, wind_dir = court_wind(ctx, body)
    out = {"dry": DRY, "deep dry": DRY,
           "perched": Water("perched", floor + height / 2.0),
           "snow": Water("snow", snow_psf=snow),
           "wind": Water("wind", wind_lb=wind, wind_dir=wind_dir),
           "perched snow": Water("perched snow", floor + height / 2.0, snow_psf=snow),
           "retained full": Water("retained full", top),
           "flooded court": Water("flooded court", flood, both_sides=True),
           "deep flooded": Water("deep flooded", flood, both_sides=True)}
    lip = _lip_ft(ctx, body)
    if lip is None:
        return out, ["an overflow_invert on the court's soakaway bed — the lip the deep "
                     "plane's soakaway-full case fills to"]
    out["deep, soakaway full"] = Water("deep, soakaway full", lip, both_sides=True)
    return out, []


@dataclass(frozen=True)
class Graded:
    states: tuple[LimitState, ...]
    pending: tuple[tuple[str, str], ...]
    notes: tuple[str, ...]
    inputs: tuple[Quantity, ...]
    dry: dict[float, tuple[float, float]]
    #: ``{pcf: (friction mobilised once backfilled, before the apron; the most any graded
    #: service case mobilises)}`` — what the joint row's post-backfill movement reads.
    mobilised: dict[float, tuple[float, float]] = dataclasses.field(default_factory=dict)
    #: ``{pcf: (dry resultant, whole-body friction, house-side friction, how)}`` at the upper
    #: (restraint) bed friction that the court's contraction rows grade at.
    restraint: dict[float, tuple] = dataclasses.field(default_factory=dict)


def grade(ctx, ref: str, walls: list, built_by_pcf: dict, soil) -> tuple[Graded | None, list[str]]:  # type: ignore[no-untyped-def]
    """Every case at both ends of the band; each row reports its worse end."""
    bed_mu, native_mu, _state, _basis = design_friction(ctx, soil)
    fs: dict[str, list[tuple[float, float, Body, Water]]] = {c.key: [] for c in CASES}
    missing: list[str] = []
    dry: dict[float, tuple[float, float]] = {}
    mobilised: dict[float, tuple[float, float]] = {}
    restraint: dict[float, tuple] = {}
    upper = restraint_friction(ctx, soil)
    tables = []
    for pcf, built in built_by_pcf.items():
        members = members_for(ctx, walls, built, soil, pcf)
        body, gap = footing_plane_body(ctx, ref, walls, members, soil_pcf=pcf,
                                       friction=bed_mu)
        missing.extend(gap)
        if body is None:
            return None, missing
        deep, gap = deep_plane_body(ctx, body, friction=native_mu,
                                    native_pcf=pcf)
        missing.extend(gap)
        levels, gap = waters(ctx, body)
        missing.extend(gap)
        dry[pcf] = (body.resultant(), body.friction * body.weight())
        house, house_how = house_side_weight(ctx, ref, walls, members, body)
        restraint[pcf] = (body.resultant(), upper * body.weight(), upper * house,
                          f"mu {upper:.2f} x {house_how}")
        bare = dataclasses.replace(body, pushes=tuple(
            dataclasses.replace(p, lateral_plf=0.0) for p in body.pushes))
        service = [levels[k] for k in ("dry", "perched", "flooded court") if k in levels]
        mobilised[pcf] = (1.0 / bare.fs(DRY) if bare.fs(DRY) else 0.0,
                          max(1.0 / body.fs(w) for w in service))
        for case in CASES:
            on = body if case.plane == "footing" else deep
            water = levels.get(case.key)
            if on is None or water is None:
                continue
            fs[case.key].append((on.fs(water), pcf, on, water))
        tables.append(_table(pcf, body, deep, levels))
    if missing:
        return None, list(dict.fromkeys(missing))
    states, pending, notes = [], [], []
    for case in CASES:
        if not fs[case.key]:
            continue
        value, pcf, on, water = min(fs[case.key], key=lambda r: (r[0], r[1]))
        how = _how(case, on, water, pcf)
        if case.graded:
            states.append(LimitState(case.label, REQUIRED_FS, value, "", how,
                                     is_safety_factor=True))
            if value < REQUIRED_FS and case.key in PENDING_CASES:
                pending.append((case.label, (
                    f"a design answer for the court's {case.label} case, FS {value:.2f} "
                    f"against {REQUIRED_FS:.2f} at {pcf:.0f} pcf (more resistance, a key, or "
                    f"an owner-accepted basis)")))
        else:
            if case.key in OWNER_BASIS:
                notes.append(OWNER_BASIS[case.key].format(fs=value, pcf=pcf))
                continue
            notes.append(f"REPORTED, not graded — {case.label}: FS {value:.2f} at "
                         f"{pcf:.0f} pcf. {how}")
    body110 = fs["dry"][0][2]
    inputs = (Quantity("stone_unit_weight", STONE_PCF, "pcf", 1.0),
              Quantity("body_weight_110", body110.weight(), "lb", 1.0),
              Quantity("body_resultant_110", body110.resultant(), "lb", 1.0))
    return Graded(tuple(states), tuple(pending), tuple(notes + tables), inputs, dry,
                  mobilised, restraint), []


def _how(case: Case, body: Body, water: Water, pcf: float) -> str:
    where = "both sides, uplift" if water.both_sides else "retained side, bed draining"
    level = ("none" if water.level_ft is None else f"{water.level_ft * 12:.2f}\" ({where})")
    return (f"IRC R404.4 — {body.label} at {body.plane_ft * 12:.2f}\", mu {body.friction:.2f}"
            f": {body.friction:.2f} x N' {body.weight(water):,.0f} lb / H "
            f"{body.resultant(water):,.0f} lb at {pcf:.0f} pcf; water {level}"
            + (f"; the columns' ASD E-W base shear {water.wind_lb:,.0f} lb added the adverse "
               f"way (IBC §1807.2.3 at service, ASCE 7 §2.4.1 0.6W)" if water.wind_lb else ""))


def _table(pcf: float, body: Body, deep: Body | None, levels: dict[str, Water]) -> str:
    def row(b: Body, key: str) -> str:
        w = levels.get(key)
        return "-" if w is None or b is None else f"{key} {b.fs(w):.2f}"

    parts = "; ".join(f"{k} {v:,.0f}" for k, v in body.parts().items())
    widths = ", ".join(f"{p.tag} {p.width_ft:.2f}'" for p in body.pushes)
    deep_parts = "" if deep is None else "; ".join(
        f"{k} {v:,.0f}" for k, v in deep.parts().items())
    return (f"CASE SET at {pcf:.0f} pcf — footing-plane body (lb): {parts}; each push acts over "
            f"its projected width ({widths}). Deep body adds (lb): {deep_parts}. FS: "
            + ", ".join(row(body if c.plane == "footing" else deep, c.key) for c in CASES))


def design_friction(ctx, soil) -> tuple[float, float, str, str]:  # type: ignore[no-untyped-def]
    """``(bed mu, deep-plane mu, state, how)``: the report's confirmed values, else the
    specified ones the design is closed on, else IBC Table 1806.2 (class 3 on the washed
    stone, the site's class on the native). ``state`` is "confirmed", "specified" or
    "presumptive"."""
    import math

    from typehaus.engineering.soil import aggregate_bed

    site = getattr(getattr(ctx.plan, "project", None), "site", None)
    for state in ("confirmed", "specified"):
        params = getattr(site, f"{state}_soil", None)
        if params is not None:
            native = math.tan(math.radians(params.native_phi_deg))
            return params.bed_friction, native, state, (
                f"{state.upper()} soil parameters: bed friction {params.bed_friction:.2f}, "
                f"native phi' {params.native_phi_deg:g} deg (tan {native:.3f})"
                + (f" — {params.source}" if params.source else ""))
    return aggregate_bed().friction_coefficient, soil.friction_coefficient, "presumptive", (
        "PRESUMPTIVE IBC Table 1806.2: class 3 on the stone, the site's class on the native")


def restraint_friction(ctx, soil) -> float:  # type: ignore[no-untyped-def]
    """The bed friction an UNFAVOURABLE (restraint) row grades at: the confirmed report
    value, else the specified ``bed_friction_max``, else the design friction itself."""
    site = getattr(getattr(ctx.plan, "project", None), "site", None)
    confirmed = getattr(site, "confirmed_soil", None)
    if confirmed is not None:
        return confirmed.bed_friction
    specified = getattr(site, "specified_soil", None)
    if specified is not None and specified.bed_friction_max is not None:
        return specified.bed_friction_max
    return design_friction(ctx, soil)[0]
