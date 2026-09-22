"""End anchorage of a veneer beam's longitudinal rows — ACI 318-19 §25.4.

Split from ``veneer_beam.py`` for size. Each corner bar is torsion steel and must develop fy
at the support face (no §25.4.10.1 reduction). A row either hooks into the supporting WALL
(§25.4.3.1, ψr 1.0 on 6 db spacing or on authored ``BarSpec.hook_ties`` per Table 25.4.3.2
and §25.4.3.3), or — where it sits below the wall, inside the footing poured a placement
earlier — is carried by the beam's authored ``dowels``, cast STRAIGHT in that footing
(§25.4.2.4). Nothing is assumed: a missing hook, tie or dowel is a named missing input.

Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6e.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typehaus.engineering.item import LimitState
from typehaus.model.rebar import BARS

_M_PER_IN = 0.0254
#: ACI 318-19 Table 25.4.3.2: the Ath credit reaches #11 and smaller only.
_MAX_TIE_CREDIT_BAR = 11
_ATH_FRACTION = 0.4
_TOL_IN = 1e-6


def hooked_anchorage(*, bar: int, count: int, width_in: float, cover_in: float,
                     hoop_diameter_in: float, side_cover_in: float, fc_psi: float,
                     epoxy: bool = False, tie_area_in2: float = 0.0,
                     ) -> tuple[float, float, bool, bool]:
    """``(ldh, row spacing, ψr 1.0?, ψo 1.0?)`` for one hooked row, ACI 318-19 §25.4.3.1.

    ψr is 1.0 when the hooked bars sit ≥ 6 db apart OR ``tie_area_in2`` (a §25.4.3.3-valid
    Ath) reaches 0.4 Ahs, Table 25.4.3.2. ψo is 1.0 when side cover normal to the hook's
    plane is ≥ 6 db.
    """
    from typehaus.resolve.rebar.detailing import hooked_development_in

    db = BARS[bar].diameter_in
    inset = cover_in + hoop_diameter_in + db / 2.0
    spacing = (width_in - 2.0 * inset) / (count - 1) if count > 1 else float("inf")
    ahs = count * BARS[bar].area_in2
    tied = bar <= _MAX_TIE_CREDIT_BAR and tie_area_in2 >= _ATH_FRACTION * ahs - _TOL_IN
    psi_r_one, covered = spacing >= 6.0 * db or tied, side_cover_in >= 6.0 * db
    ldh = hooked_development_in(bar, fc_psi, confined_spacing=psi_r_one,
                                side_cover_ok=covered, epoxy=epoxy)
    return ldh, spacing, psi_r_one, covered


def confining_tie_area(conf: Any, *, hooked_bar: int, ldh_in: float) -> tuple[float, list[str]]:
    """``(Ath, why it does not count)`` for authored hook ties, ACI 318-19 §25.4.3.3.

    ``ldh_in`` is the ψr-1.0 length the ties must be distributed along. Ath is 0 whenever a
    reason is returned — a tie arrangement the section does not count is not partly counted.
    """
    if conf is None:
        return 0.0, ["no `BarSpec.hook_ties` authored"]
    db, tie = BARS[hooked_bar].diameter_in, BARS.get(conf.bar)
    spacing = float(conf.spacing.inches)
    why = []
    if tie is None:
        why.append(f"#{conf.bar} is not a bar size this engine knows")
    if conf.count < 2:
        why.append(f"{conf.count} tie(s) per end; §25.4.3.3 wants two or more")
    if spacing > 8.0 * db + _TOL_IN:
        why.append(f"ties {spacing:.2f}\" apart against 8db {8.0 * db:.2f}\"")
    if conf.orientation == "perpendicular" and (conf.count - 1) * spacing > ldh_in + _TOL_IN:
        why.append(f"{conf.count} ties at {spacing:.2f}\" span {(conf.count - 1) * spacing:.2f}\""
                   f", beyond ℓdh {ldh_in:.2f}\"")
    if why or tie is None:
        return 0.0, why
    return conf.count * conf.legs * tie.area_in2, []


@dataclass
class Anchorage:
    """What the anchorage pass adds to the record."""

    states: list[LimitState] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _footing_at(ctx: Any, origin: Any, u: Any, n: Any, sup: Any, own: Any, z_m: float) -> Any:
    """The resolved footing/pad solid under support ``sup`` containing the row at ``z_m``."""
    su, sn = (sup.u0 + sup.u1) / 2.0, (own.n0 + own.n1) / 2.0
    x, y = origin[0] + u[0] * su + n[0] * sn, origin[1] + u[1] * su + n[1] * sn
    for solid in sorted(getattr(ctx.model, "solids", ()), key=lambda s: s.tag):
        if solid.category not in ("footing", "pad") or not solid.z0_m <= z_m <= solid.z1_m:
            continue
        xs, ys = [p[0] for p in solid.outline], [p[1] for p in solid.outline]
        if xs and min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys):
            return solid
    return None


def _u_extent(solid: Any, origin: Any, u: Any) -> tuple[float, float]:
    us = [((p[0] - origin[0]) * u[0] + (p[1] - origin[1]) * u[1]) / _M_PER_IN
          for p in solid.outline]
    return min(us), max(us)


def _dowel_state(ctx: Any, beam: Any, spec: Any, role: str, row: tuple[int, int, int],
                 sup: Any, starts: bool, solid: Any, frame: tuple[Any, Any, Any],
                 z_in: float, epoxy: bool, out: Anchorage) -> None:
    """A row below the wall, carried by dowels cast STRAIGHT in the footing (§25.4.2.4)."""
    from typehaus.resolve.concrete import concrete_spec_for, cover_for, fc_psi
    from typehaus.resolve.rebar.detailing import development_length_in, tension_lap_in

    dowel = next((b for b in getattr(spec, "bars", ()) if b.role == "dowels"), None)
    if dowel is None or dowel.embedment is None or not dowel.count:
        out.missing.append(
            f"`dowels` (a COUNT and an `embedment`) on {beam.tag}'s ReinforcementSpec for its "
            f"{role} row at {sup.tag}: the row is at z {z_in:.2f}\", below the wall, inside "
            f"{solid.tag} — cast dowels in that footing, or raise the beam bottom")
        return
    element = ctx.plan.by_tag(solid.tag)
    ftg_fc = fc_psi(concrete_spec_for(ctx.plan, element))
    ftg_cover, _ = cover_for(ctx.plan, element)
    if ftg_fc is None or ftg_cover is None:
        out.missing.append(f"f'c and cover on {solid.tag} to develop {beam.tag}'s dowels in it")
        return
    lo, hi = _u_extent(solid, frame[0], frame[1])
    face = sup.u1 / _M_PER_IN if starts else sup.u0 / _M_PER_IN
    joint = hi if starts else lo                                  # the footing's span face
    offset = max(0.0, (joint - face) if starts else (face - joint))
    geometric = (face - lo if starts else hi - face) - ftg_cover
    embedded = float(dowel.embedment.inches)
    available = max(0.0, min(embedded - offset, geometric))
    below = z_in - solid.z0_m / _M_PER_IN
    ld = development_length_in(dowel.bar, ftg_fc, top_cast=below > 12.0, epoxy=epoxy)
    lap = tension_lap_in(dowel.bar, ftg_fc, spec.lap_class)
    out.states.append(LimitState(
        f"dowel development of {role} into {solid.tag}", ld, available, "in",
        f"ACI 318-19 §25.4.2.4 straight ℓd of #{dowel.bar} at {solid.tag}'s f'c "
        f"{ftg_fc:,.0f}, ψt {'1.3' if below > 12.0 else '1.0'} ({below:.2f}\" cast below); past "
        f"the {sup.tag} face: min({embedded:g}\" embedment − {offset:.2f}\" face-to-joint, "
        f"{geometric:.2f}\" to the far face less {ftg_cover:g}\" cover)"))
    bar, count, _layers = row
    out.states.append(LimitState(
        f"dowel steel against {role} at {solid.tag}", count * BARS[bar].area_in2,
        dowel.count * BARS[dowel.bar].area_in2, "in2",
        f"{dowel.count} #{dowel.bar} dowels carry the {count} #{bar} row across the joint",
        is_detailing=True))
    if dowel.projection is None:
        out.notes.append(f"DOWEL LAP at {solid.tag}: class {spec.lap_class or 'B'} "
                         f"{lap:.2f}\" past the joint (§25.5.2.1), laid and billed by the "
                         f"rebar layout; not graded (no authored `BarSpec.projection`).")
        return
    out.states.append(LimitState(
        f"dowel lap of {role} past the {solid.tag} joint", lap,
        float(dowel.projection.inches), "in",
        f"ACI 318-19 §25.5.2.1 class {spec.lap_class or 'B'} lap on ℓd {ld:.2f}\"; authored "
        f"`projection` past the joint into {beam.tag}", is_detailing=True))


def _hook_state(ctx: Any, beam: Any, entry: Any, role: str, row: tuple[int, int, int],
                sup: Any, own: Any, section: tuple[float, float, float], epoxy: bool,
                out: Anchorage) -> None:
    """A row hooked into the supporting WALL, §25.4.3.1."""
    from typehaus.resolve.concrete import concrete_spec_for, cover_for, fc_psi

    width, cover, hoop_d = section
    bar, count, _layers = row
    db = BARS[bar].diameter_in
    element = ctx.plan.by_tag(sup.tag)
    sup_fc = fc_psi(concrete_spec_for(ctx.plan, element))
    sup_cover, _ = cover_for(ctx.plan, element)
    if sup_fc is None or sup_cover is None:
        out.missing.append(f"f'c and cover on {sup.tag} to develop {role} into it")
        return
    available = (sup.u1 - sup.u0) / _M_PER_IN - sup_cover
    side_cover = min(own.n0 - sup.n0, sup.n1 - own.n1) / _M_PER_IN + cover + hoop_d
    common: dict[str, Any] = dict(bar=bar, count=count, width_in=width, cover_in=cover,
                                  hoop_diameter_in=hoop_d, side_cover_in=side_cover,
                                  fc_psi=sup_fc, epoxy=epoxy)
    ldh_one = hooked_anchorage(**common, tie_area_in2=float("inf"))[0]
    ath, refused = confining_tie_area(entry.hook_ties, hooked_bar=bar, ldh_in=ldh_one)
    ldh, spacing, psi_r_one, covered = hooked_anchorage(**common, tie_area_in2=ath)
    ahs = count * BARS[bar].area_in2
    ties = (f"Ath {ath:.3f} in² vs 0.4 Ahs {_ATH_FRACTION * ahs:.3f}" if not refused
            else "no Ath credited: " + "; ".join(refused))
    how = (f"ψr {'1.0' if psi_r_one else '1.6'} (bars {spacing:.2f}\" apart vs 6db "
           f"{6 * db:.2f}\"; {ties}), ψo {'1.0' if covered else '1.25'}, {available:.2f}\" = "
           f"{sup.tag} {(sup.u1 - sup.u0) / _M_PER_IN:.2f}\" less {sup_cover:.2f}\" far-face cover")
    if not entry.hooks:
        out.missing.append(f"`BarSpec.hooks` on {beam.tag}'s {role} row (anchorage into "
                           f"{sup.tag}); a straight #{bar} needs far more than the wall")
        out.notes.append(f"IF {role} WERE HOOKED into {sup.tag}: ℓdh {ldh:.2f}\" against "
                         f"{available:.2f}\" (d/c {ldh / available:.2f}); {how}")
        return
    out.states.append(LimitState(
        f"hooked development of {role} into {sup.tag}", ldh, available, "in",
        f"ACI 318-19 §25.4.3.1 at fy (torsion corner bar, no §25.4.10.1 reduction); {how}; "
        f"ψr per Table 25.4.3.2 and §25.4.3.3"))


#: ACI 318-19 §25.7.1.3/§25.7.1.6 — a closed hoop resisting torsion is closed with 135°
#: seismic-style hooks; 90° is permitted only where torsion is not resisted and the bar end
#: is restrained by a slab. This beam's hoops are its torsion steel (note §4a), so 135° is
#: the requirement and an unstated angle is a missing input, never a 90° assumption.
TORSION_HOOP_HOOK_DEGREES = 135


def tie_hook_row(beam: Any, spec: Any, out: Anchorage) -> None:
    """The closed hoops' hook angle, graded — ``BarSpec.tie_hook_degrees`` on ``ties``."""
    entry = next((b for b in getattr(spec, "bars", ()) if b.role in ("ties", "stirrups")), None)
    if entry is None:
        return
    if entry.tie_hook_degrees is None:
        out.missing.append(
            f"`BarSpec.tie_hook_degrees` on {beam.tag}'s {entry.role}: the hoops ARE the "
            f"torsion steel, so ACI 318-19 §25.7.1.3/§25.7.1.6 want {TORSION_HOOP_HOOK_DEGREES}"
            f"° and an unstated angle is not a 90° claim either way")
        return
    out.states.append(LimitState(
        "closed hoop hook angle", TORSION_HOOP_HOOK_DEGREES, float(entry.tie_hook_degrees),
        "deg", f"ACI 318-19 §25.7.1.3 and §25.7.1.6 — a hoop resisting torsion is closed with "
        f"a {TORSION_HOOP_HOOK_DEGREES}° bend; authored {entry.tie_hook_degrees}°",
        is_detailing=True))


def anchor_rows(ctx: Any, beam: Any, spec: Any, rows: dict[str, tuple[int, int, int]],
                supports: tuple[Any, Any], own: Any, frame: tuple[Any, Any, Any],
                section: tuple[float, float, float], epoxy: bool) -> Anchorage:
    """Every longitudinal row into each end. ``rows`` maps role -> ``(bar, count, layers)``,
    ``supports`` is ``(start, end)``, ``section`` is ``(width, cover, hoop diameter)``, in."""
    out = Anchorage()
    _width, cover, hoop_d = section
    for role, row in rows.items():
        entry = next(b for b in getattr(spec, "bars", ()) if b.role == role)
        db = BARS[row[0]].diameter_in
        inset = cover + hoop_d + db / 2.0
        z = (own.z1 / _M_PER_IN - inset) if role == "top-y" else (own.z0 / _M_PER_IN + inset)
        for starts, sup in zip((True, False), supports, strict=True):
            if sup.z0 / _M_PER_IN + db / 2.0 <= z <= sup.z1 / _M_PER_IN - db / 2.0:
                _hook_state(ctx, beam, entry, role, row, sup, own, section, epoxy, out)
                continue
            solid = _footing_at(ctx, *frame, sup, own, z * _M_PER_IN)
            if solid is None:
                out.missing.append(
                    f"a wall or footing for {beam.tag}'s {role} row to anchor in at {sup.tag}: "
                    f"the row is at z {z:.2f}\" and {sup.tag} spans {sup.z0 / _M_PER_IN:.2f}\".."
                    f"{sup.z1 / _M_PER_IN:.2f}\" — raise the beam bottom or detail the end")
                continue
            _dowel_state(ctx, beam, spec, role, row, sup, starts, solid, frame, z, epoxy, out)
    tie_hook_row(beam, spec, out)
    return out
