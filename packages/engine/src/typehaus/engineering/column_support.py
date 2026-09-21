"""A fixed-base cast column's joint onto a foundation-wall top — ``column_support/<wall tag>``.

Until 2026-09-20 this was a ``deferred.py`` kind: ``deck_post`` computes each column's base
moment ON THE COLUMN, and the concrete that receives it — a basement wall answered by IRC
Table R404.1.2(8), which publishes no surcharge column — was graded by nobody. One record
per wall, four states per column standing on it, each an envelope over ASCE 7-16 §2.3.1 at
the same (Pu, magnified Mu) pairs ``deck_post`` grades the column on:

* **bearing on the wall top**, ACI 318-19 §22.8.3, on the COMPRESSION BLOCK. The base sits
  far outside the kern (e = Mu/Pu against D/8 for a circle), so the load arrives on a
  circular segment, not the gross section. The block is ``deck_post._pm_point``'s at that
  Pu; the force on it is the dowel couple's compression. ``√(A2/A1)`` is read off the wall's
  own width and is 1.0 where the round is as wide as the stem.
* **dowel tension across the joint**, per bar, φ 0.90.
* **shear friction across the cold joint**, §22.9, μ from the authored
  ``BarSpec.joint_surface``; the tension the couple spends is deducted from Avf.
* **dowel development into the stem**, ``deck_post._dowel_anchorage`` — the same state the
  column's own record prints, against the authored ``BarSpec.embedment``.

**Oracle.** ``houses/catlin/notes/balcony_moment_columns.md`` §11, hand-worked in a separate
pass; ``tests/test_column_support_calc.py`` reproduces it.
"""

from __future__ import annotations

import dataclasses
import math

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Scope,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import _Pier, cast_piers
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_basis import _BAR, PRESUMPTIVE_FC_PSI, REINFORCEMENT_FY_PSI
from typehaus.wind import ASD_WIND_FACTOR

KIND = "column_support"
BASIS_VERSION = "1"
BASIS = "ACI 318-19 §22.8.3 (bearing), §22.9 (shear friction), §25.4.2.4 (development)"

#: ACI 318-19 Table 21.2.2: bearing 0.65, shear 0.75, tension-controlled 0.90.
PHI_BEARING = 0.65
PHI_SHEAR = 0.75
PHI_TENSION = 0.90
#: IRC R301.5 / Table R301.5 note f — the guard's concentrated load, lb.
GUARD_LOAD_LB = 200.0
#: ACI 318-19 Table 22.9.4.2, normalweight (λ 1.0).
MU_ROUGHENED = 1.0
MU_NOT_ROUGHENED = 0.6

oracled_by(KIND, Oracle(note="balcony_moment_columns.md", section="§11",
                        test="tests/test_column_support_calc.py"))


@keys(KIND)
def column_support_keys(ctx: EngineeringContext) -> list[str]:
    """Every wall with a cast, fixed-base column standing on its top.

    Read off ``cast_piers``' own ``shared_wall_footing`` flag — set exactly when a concrete
    post inherits a concrete wall as its base — and scoped to a column with a base moment:
    a leaning column hands its wall a vertical load and nothing else.
    """
    return sorted({pier_wall(ctx, pier) for pier in _moment_columns(ctx)} - {None})


def pier_wall(ctx: EngineeringContext, pier: _Pier) -> str | None:
    return getattr(ctx.plan.by_tag(pier.tag), "supported_by", None)


def _moment_columns(ctx: EngineeringContext) -> list[_Pier]:
    return [p for p in cast_piers(ctx) if p.shared_wall_footing and p.lateral_system]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    by_wall: dict[str, list[_Pier]] = {}
    for pier in _moment_columns(ctx):
        wall = pier_wall(ctx, pier)
        if wall:
            by_wall.setdefault(wall, []).append(pier)
    return [_one(ctx, wall, sorted(piers, key=lambda p: p.tag))
            for wall, piers in sorted(by_wall.items())]


def _clear_side_in(ctx: EngineeringContext, pier: _Pier, wall_tag: str) -> float | None:
    """The least distance from the column centre to either face of the wall's structure
    layer, inches — the radius of the largest concentric circle on the wall top (A2)."""
    from typehaus.resolve.rebar.walls import structure_layer

    wall = ctx.model.wall(wall_tag)
    post = ctx.plan.by_tag(pier.tag)
    layer = structure_layer(wall) if wall is not None else None
    if layer is None or post is None:
        return None
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay) or 1.0
    nx, ny = -(by - ay) / length, (bx - ax) / length
    ts = [(x - ax) * nx + (y - ay) * ny for x, y in layer.polygon]
    tc = (post.position.x.meters - ax) * nx + (post.position.y.meters - ay) * ny
    return round(min(max(ts) - tc, tc - min(ts)) / 0.0254, 3)  # 1/1000" — a flush round reads 6.000


def _shear_asd_lb(pier: _Pier) -> tuple[float, float]:
    """``(wind, guard)`` ASD base shear, lb. The deck path builds the wind moment as
    ``V x column height`` (``pier_basis._base_moments``), so that factorisation is exact; a
    roof-borne column records its own shear and arm, which is read instead."""
    from typehaus.engineering.roof_moment import base_shear_of

    guard = GUARD_LOAD_LB if pier.guard_base_moment_lb_ft > 0.0 else 0.0
    recorded = base_shear_of(pier.tag)
    if not guard and recorded is not None:
        return recorded[0], 0.0
    height_ft = pier.height_in / 12.0
    return (pier.wind_base_moment_lb_ft / height_ft if height_ft else 0.0), guard


def _couple(mu_lb_in: float, pu_lb: float, ybar_in: float,
            offsets: tuple[float, ...]) -> tuple[float, float, int]:
    """``(C, T, bars in tension)``: the compression on the block and the dowel tension that
    balance (Pu, Mu), T at the centroid of the dowels below the centre. Compression dowels
    are not credited, which puts every pound of compression on the concrete. Where no tension
    is needed, C = Pu, still on the block (conservative)."""
    tension = [-o for o in offsets if o < -1e-9]
    lever = sum(tension) / len(tension)
    compression = (mu_lb_in + pu_lb * lever) / (ybar_in + lever)
    pull = compression - pu_lb
    if pull <= 0.0:
        return pu_lb, 0.0, len(tension)
    return compression, pull, len(tension)


def _column_states(ctx: EngineeringContext, pier: _Pier, wall_tag: str,
                   missing: list[str], inputs: list[Quantity]) -> list[LimitState]:
    from typehaus.engineering import deck_post as dp

    cage = dp.cage_for(pier)
    dowel = dp.dowel_entry(pier)
    if cage is None or dowel is None or dowel.bar not in _BAR:
        missing.append(f"{pier.tag}: a structured cage with a `dowels` BarSpec row")
        return []
    col_fc = dp._fc_psi(pier)
    wall_fc = pier.base_fc_psi or PRESUMPTIVE_FC_PSI
    cover = dp._cover_in(pier)
    radius = pier.diameter_in / 2.0
    dowel_db, dowel_area = _BAR[dowel.bar][1], _BAR[dowel.bar][0]
    # Dowels sit one bar inside the verticals (resolve/rebar's contact lap), one per vertical.
    ring = (radius - cover - cage.tie_diameter_in - cage.bar_diameter_in / 2.0
            - (cage.bar_diameter_in + dowel_db) / 2.0)
    count = cage.count
    layouts = tuple(tuple(ring * math.cos(start + 2.0 * math.pi * i / count)
                          for i in range(count)) for start in (0.0, math.pi / count))

    clear = _clear_side_in(ctx, pier, wall_tag)
    if clear is None:
        missing.append(f"{pier.tag}: {wall_tag}'s resolved structure layer")
        return []
    root_a2_a1 = min(2.0, max(1.0, clear / radius))
    rough = dowel.joint_surface == "roughened"
    mu = MU_ROUGHENED if rough else MU_NOT_ROUGHENED
    fc_sf = min(col_fc, wall_fc)
    area = math.pi * radius ** 2
    vn_max = (min(0.2 * fc_sf, 480.0 + 0.08 * fc_sf, 1600.0) if rough
              else min(0.2 * fc_sf, 800.0)) * area
    wind_v, guard_v = _shear_asd_lb(pier)
    wind_mu = pier.wind_base_moment_lb_ft * dp.STRENGTH_FROM_ASD_WIND
    guard_mu = pier.guard_base_moment_lb_ft * dp.GUARD_LOAD_FACTOR

    worst: dict[str, tuple[float, float, float, object, str]] = {}
    for case in dp._combinations(pier, wind_mu, guard_mu):
        _slender, delta = dp._sway_magnifier(pier, case.axial_lb)
        mu_in = case.moment_lb_ft * delta * 12.0
        _phi_mn, _phi, c = dp._pm_point(pier, cage, cover, case.axial_lb)
        block, ybar = dp._segment(radius, min(dp._beta_1(col_fc) * c, 2.0 * radius))
        couples = [_couple(mu_in, case.axial_lb, ybar, offs) for offs in layouts]
        comp = max(k[0] for k in couples)
        pull = max(k[1] for k in couples)
        per_bar = max(k[1] / k[2] for k in couples)
        factors = dict(case.factors)
        vu = factors.get("W", 0.0) / ASD_WIND_FACTOR * wind_v + factors.get("L", 0.0) * guard_v
        bearing_cap = PHI_BEARING * 0.85 * wall_fc * block * root_a2_a1
        sf_cap = min(mu * (PHI_SHEAR * count * dowel_area * REINFORCEMENT_FY_PSI - pull),
                     PHI_SHEAR * vn_max)
        how = (f"Pu {case.axial_lb:,.0f} lb, Mu {mu_in / 12.0:,.0f} lb-ft (δ {delta:.3f}), "
               f"e {mu_in / case.axial_lb if case.axial_lb else 0.0:.1f}\"")
        for name, demand, capacity in (
                ("bearing", comp, bearing_cap),
                ("tension", per_bar, PHI_TENSION * dowel_area * REINFORCEMENT_FY_PSI),
                ("shear", vu, sf_cap)):
            ratio = demand / capacity if capacity > 0 else math.inf
            if name not in worst or ratio > worst[name][0]:
                worst[name] = (ratio, demand, capacity, case,
                               how + (f", c {c:.3f}\", block {block:.2f} in2 at "
                                      f"{ybar:.3f}\"" if name == "bearing" else ""))

    def graded(key: str, label: str, unit: str, citation: str) -> LimitState:
        _r, demand, capacity, case, how = worst[key]
        return LimitState(f"{pier.tag}: {label}", demand, capacity, unit,
                          f"{citation} — governed by ASCE 7-16 §2.3.1 {case.label}: {how}",
                          combination=f"ASCE 7-16 §2.3.1 {case.label}",
                          combination_factors=case.factors)

    states = [
        graded("bearing", "bearing on the wall top", "lb",
               f"ACI 318-19 §22.8.3.2 φ {PHI_BEARING:.2f} × 0.85 f'c {wall_fc:,.0f} psi × the "
               f"compression block × √(A2/A1) {root_a2_a1:.2f} (the wall top clears "
               f"{clear:.2f}\" each side of a {radius:.2f}\" radius); C from the dowel couple, "
               f"compression dowels not credited"),
        graded("tension", "dowel tension across the joint", "lb",
               f"φ {PHI_TENSION:.2f} As fy per #{dowel.bar} dowel, the worse of the two "
               f"orientations of a {count}-bar ring of radius {ring:.3f}\""),
        graded("shear", "shear friction across the cold joint", "lb",
               f"ACI 318-19 §22.9.4.2 φ {PHI_SHEAR:.2f} μ {mu:.1f}λ "
               f"({'the authored 1/4-in. roughening' if rough else 'not intentionally roughened'})"
               f" × (Avf fy less the couple's tension), capped by §22.9.4.4 at "
               f"{PHI_SHEAR * vn_max:,.0f} lb; wind at 1.0W plus the {guard_v:.0f} lb guard "
               f"load, compression not credited"),
    ]
    anchorage = dp._dowel_anchorage(pier, cage, col_fc)
    if anchorage is None:
        missing.append(f"{pier.tag}: `BarSpec.embedment` on its `dowels` row")
    else:
        states.append(dataclasses.replace(anchorage,
                                          name=f"{pier.tag}: dowel development into the stem"))
    states.append(LimitState(f"{pier.tag}: footprint on the wall top", radius, clear, "in",
                             "the column's radius against the clear wall top each side of "
                             "its centre — a round wider than the stem overhangs its face",
                             is_detailing=True))
    inputs += [
        Quantity(f"{pier.tag}.sqrt_A2_A1", root_a2_a1, "", 0.01),
        Quantity(f"{pier.tag}.shear_friction_mu", mu, "", None),
        Quantity(f"{pier.tag}.dowel_embedment",
                 float(dowel.embedment.inches) if dowel.embedment else 0.0, "in", 0.125),
        Quantity(f"{pier.tag}.wall_fc", wall_fc, "psi", 1.0),
        Quantity(f"{pier.tag}.column_fc", col_fc, "psi", 1.0),
        Quantity(f"{pier.tag}.column_cover", cover, "in", 0.125),
        Quantity(f"{pier.tag}.wall_cover", pier.base_cover_in or 0.0, "in", 0.125),
        Quantity(f"{pier.tag}.stem_height", pier.base_thickness_in, "in", 0.125),
        Quantity(f"{pier.tag}.dowel_bar", float(dowel.bar), "", None),
        Quantity(f"{pier.tag}.dowel_count", float(count), "", None),
        Quantity(f"{pier.tag}.wind_base_moment", pier.wind_base_moment_lb_ft, "lb-ft", 1.0),
        Quantity(f"{pier.tag}.guard_base_moment", pier.guard_base_moment_lb_ft, "lb-ft", 1.0),
        Quantity(f"{pier.tag}.factored_axial", pier.factored_lb, "lb", 1.0),
    ]
    return states


def _one(ctx: EngineeringContext, wall_tag: str, piers: list[_Pier]) -> EngineeringRecord:
    missing: list[str] = []
    inputs: list[Quantity] = []
    states: list[LimitState] = []
    for pier in piers:
        states += _column_states(ctx, pier, wall_tag, missing, inputs)
    tags = ", ".join(p.tag for p in piers)
    notes = (
        f"{wall_tag} is a basement wall graded prescriptively by IRC Table R404.1.2(8), "
        f"which publishes no surcharge column; this record grades the JOINT each of "
        f"{tags} makes with its top, at the same §2.3.1 (Pu, magnified Mu) pairs "
        f"`deck_post/<column>` grades the column on.",
        "BEARING is graded on the compression block, not the gross section: the base is far "
        "outside the kern (D/8 on a circle), so the round bears on a circular segment. The "
        "block is the column's own at each Pu (`deck_post._pm_point`); the force on it is "
        "the compression of the couple the dowels close. √(A2/A1) is taken off the wall's "
        "width and is 1.0 where the round is as wide as the stem — ACI's confinement "
        "credit needs concrete beside the column, and there is none.",
        "DOWELS: one per vertical, one bar inside the cage (contact lap). Both orientations "
        "of the ring are run — a bar on the tension axis loads one dowel on a longer lever, "
        "two straddling it share a shorter one — and each state takes the worse.",
        "SHEAR FRICTION: μ 1.0λ only where the dowel row authors "
        "`joint_surface=\"roughened\"` (ACI's intentional 1/4-in. amplitude); otherwise "
        "0.6λ. The couple's dowel tension is deducted from Avf, and no clamping from the "
        "axial load is credited.",
        "NOT GRADED here, and each is real: (1) ROTATIONAL RESTRAINT — the foundation "
        "stiffness the fixed base assumes is graded as `base_rotation/<column>` for "
        f"{tags}, one question and one item; (2) the stem's own flexure, out of plane and "
        "along its length, under the base moment it receives — whether a PILASTER or a "
        "LOCAL THICKENING is needed; (3) the strip footing's bearing under the column "
        "points, which `spread_footing` scopes off a shared wall footing; (4) torsion "
        "through the joint. The retired deferral's deliverable — \"a wall-top connection "
        "detail carrying the column's axial and base moment — dowel size, embedment and "
        "development into the stem, any pilaster or local thickening, and the bearing "
        "pressure under the point\" — is answered above except for the pilaster question, "
        "which stays with the structural engineer of record.",
    )
    over = any(not state.ok for state in states)
    status = Status.INCOMPLETE if missing else (Status.OVER if over else Status.OK)
    governing = max((s for s in states if not s.is_detailing), key=lambda s: s.ratio,
                    default=None)
    summary = (f"{wall_tag}: the wall-top joint under {tags}"
               + (f", d/c {governing.ratio:.2f} on {governing.name}" if governing else ""))
    return EngineeringRecord(
        item_id=item_id(KIND, wall_tag), kind=KIND, key=wall_tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=status, summary=summary,
        inputs=tuple(inputs), limit_states=tuple(states), missing=tuple(missing),
        notes=notes, element_tags=(wall_tag, *(p.tag for p in piers)),
        scope=Scope.SCREENING)
