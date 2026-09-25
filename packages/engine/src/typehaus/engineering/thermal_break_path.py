"""The house's real lateral path for a break's thrust — free body §11i (basis 6).

The thrust enters the house's near footing line. What the stems' floor line does not take
goes into the basement slab as a compression strut, through its perimeter break, to the far
footing line. It is resisted by friction under the WHOLE house and by the far wall's soil.
Every link is graded on every break item, because every board's thrust feeds it:

* slab-edge bearing on the slab's ``perimeter_thermal_break`` at its AUTHORED rating (grade
  unstated → the lowest ASTM C578 type of its material, as the house foam is graded), the
  near line's own friction not credited; and the sheet's sustained-load rule (a fraction of
  that rating) graded beside it (§11k — the "imposed deformation" exemption is retired);
* slab strut compression, plain concrete — **buckling of a slab on grade is not credible**
  (braced continuously by its subgrade), so no slenderness row;
* global sliding at FS 1.5: μ × the house's dead load (a stated lower bound) plus the
  at-rest soil the far wall carries in excess of the near face's, passive not credited;
* the far wall's soil: its at-rest load plus what friction does not take, against IBC Table
  1806.2 lateral bearing.
"""

from __future__ import annotations

from typehaus.engineering.item import LimitState
from typehaus.engineering.thermal_break_board import CONCRETE_PCF, rated
from typehaus.resolve.solid_categories import in_slab_family, is_pour_slab

REQUIRED_FS = 1.5
#: ACI 318-19 Table 21.2.1, plain concrete; §14.5.6 bearing 0.85 f'c.
PHI_PLAIN = 0.60
#: ASCE 7-16 Table C3.1-1a, "wood or steel studs, 1/2-in. gypsum board each side" — the
#: lightest framed-wall row with gypsum, applied to every framed wall: a lower bound.
FRAMED_WALL_PSF = 8.0
#: How far past the slab's outline the take-down reaches for footings and walls, in.
FOOTPRINT_REACH_IN = 12.0
_IN = 1.0 / 0.0254


def _poly(outline):
    from shapely.geometry import Polygon

    return Polygon([(x * _IN, y * _IN) for x, y in outline])


def house_slab(ctx, footings: list[str]):
    """The slab on grade the near footing line bears on: top within 1" of a footing top and
    its outline within ``FOOTPRINT_REACH_IN`` of that footing. ``(element, solid)``."""
    from typehaus.model.floors import Slab

    tops, near = [], []
    for s in ctx.model.solids:
        if s.tag in footings and s.category == "footing":
            tops.append(s.z1_m * _IN)
            near.append(_poly(s.outline))
    best = None
    for s in ctx.model.solids:
        el = ctx.plan.by_tag(s.tag)
        if not is_pour_slab(s.category) or not isinstance(el, Slab):
            continue
        poly = _poly(s.outline)
        touches = any(abs(s.z1_m * _IN - t) < 1.0 for t in tops) and any(
            poly.distance(n) <= FOOTPRINT_REACH_IN for n in near)
        if touches and (best is None or poly.area > _poly(best[1].outline).area):
            best = (el, s)
    return best


def take_down(ctx, slab_solid) -> tuple[float, str]:
    """``(lb, basis)`` — every Footing and Slab solid and every concrete wall's STRUCTURE
    layer inside the slab's outline + reach at 150 pcf, every other wall at
    ``FRAMED_WALL_PSF``. Floors, roof, finishes and contents are left off."""
    from shapely.geometry import LineString

    from typehaus.model.floors import Slab
    from typehaus.model.structure import Footing

    zone = _poly(slab_solid.outline).buffer(FOOTPRINT_REACH_IN, join_style=2)
    parts = {"footings": 0.0, "slabs": 0.0, "concrete walls": 0.0, "framed walls": 0.0}
    for s in ctx.model.solids:
        el = ctx.plan.by_tag(s.tag)
        kind = ("footings" if isinstance(el, Footing) and s.category == "footing" else
                "slabs" if isinstance(el, Slab) and in_slab_family(s.category) else None)
        if kind and zone.contains(p := _poly(s.outline)):
            parts[kind] += p.area * (s.z1_m - s.z0_m) * _IN * CONCRETE_PCF / 1728.0
    for w in ctx.model.walls:
        axis = LineString([(x * _IN, y * _IN) for x, y in w.axis])
        if not zone.contains(axis):
            continue
        height = (w.z1_m - w.z0_m) * _IN
        core = next((ly for ly in w.depth_layers() if ly.function == "structure"), None)
        if core is not None and core.material_ref == "concrete":
            parts["concrete walls"] += (_poly(core.polygon).area * height * CONCRETE_PCF
                                        / 1728.0)
        elif core is None or core.material_ref not in ("brick",):
            parts["framed walls"] += axis.length * height / 144.0 * FRAMED_WALL_PSF
    basis = "; ".join(f"{k} {v:,.0f}" for k, v in parts.items())
    return sum(parts.values()), (f"{basis} lb (concrete at {CONCRETE_PCF:.0f} pcf, framed walls "
                                 f"at {FRAMED_WALL_PSF:.0f} psf, ASCE 7-16 Table C3.1-1a; "
                                 f"floors, roof and contents left off — a lower bound)")


def _span(outline, ax: int) -> tuple[float, float]:
    vals = [p[ax] * _IN for p in outline]
    return min(vals), max(vals)


def court_opening_in(ctx, boards) -> float:
    """The court's width along the joint, outer face to outer face — the stretch of the
    house's near face that retains no soil."""
    ax = 1 - boards[0].ax
    tags = set().union(*(b.structure for b in boards))
    spans = [_span(ly.polygon, ax) for w in ctx.model.walls if w.tag in tags
             for ly in w.depth_layers() if ly.function == "structure"]
    return max(s[1] for s in spans) - min(s[0] for s in spans) if spans else 0.0


def _slab_edge(slab, total_lb, floor_line_lb, edge_len, t, states, missing) -> None:
    brk = slab.perimeter_thermal_break
    grade = rated(brk.material_ref, brk.psi, brk.source)
    if grade is None:
        missing.append(f"a compressive rating for {slab.tag}'s perimeter break "
                       f"({brk.material_ref})")
        return
    psi, how = grade
    depth = brk.depth.inches if brk.depth is not None else t
    area, line = depth * edge_len, total_lb - floor_line_lb
    modulus = ""
    if brk.modulus_psi is not None and brk.psi is not None:
        modulus = f", E {brk.modulus_psi:,.0f} " + (
            "ESTIMATED" if brk.modulus_estimated else "published")
    states.append(LimitState(
        "house slab-edge bearing", line, psi * area, "lb",
        f"{total_lb:,.0f} lb of thrust less the floor line's {floor_line_lb:,.0f} into "
        f"{slab.tag}'s {brk.thickness.inches:g}\" {brk.material_ref} perimeter break, "
        f"{depth:.2f}\" x {edge_len:.0f}\"; {how}{modulus}; the near line's own friction not "
        f"credited"))
    frac = brk.sustained_load_fraction
    if frac and brk.psi is not None:
        states.append(LimitState(
            "house slab-edge sustained load", line, frac * brk.psi * area, "lb",
            f"the same {line:,.0f} lb against the sheet's sustained-load rule, "
            f"{frac:.3g} x {brk.psi:.0f} = {frac * brk.psi:.1f} psi over {depth:.2f}\" x "
            f"{edge_len:.0f}\" (free body §11k: graded as a dead load; no creep-relaxation "
            f"credit for an imposed deformation)"))


def path_rows(ctx, boards, total_lb: float, floor_line_lb: float, states, missing,
              notes=None, inputs=None) -> None:
    """The four lateral-path links, graded for the whole thrust ``total_lb``."""
    notes = [] if notes is None else notes
    inputs = [] if inputs is None else inputs
    from typehaus.engineering.item import Quantity as _Quantity
    from typehaus.engineering.soil import (
        presumptive,
        soil_is_presumed,
        soil_provenance_note,
    )
    from typehaus.engineering.thermal_break_geometry import facing_footings
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
    footings = sorted({t for b in boards for t in facing_footings(ctx, b)})
    found = house_slab(ctx, footings) if footings else None
    if soil is None or found is None:
        missing.append("a soil class and the house slab on grade the near footing line bears "
                       "on — the house's lateral path")
        return
    # Three of the four links below are read off the site's soil class — friction, at-rest
    # and lateral bearing — so this record carries its provenance like every other one that
    # reads a code table row for the ground.
    inputs.append(_Quantity("soil_presumed", 1.0 if soil_is_presumed(soil) else 0.0, "-", 0.5))
    notes.append(soil_provenance_note(soil))
    slab, solid = found
    ax = boards[0].ax
    lo, hi = _span(solid.outline, 1 - ax)
    edge_len, t = hi - lo, slab.thickness.inches
    line = total_lb - floor_line_lb
    if slab.perimeter_thermal_break is not None:
        _slab_edge(slab, total_lb, floor_line_lb, edge_len, t, states, missing)
    fc = fc_psi(concrete_spec_for(ctx.plan, slab))
    if fc is None:
        missing.append(f"{slab.tag}'s mix f'c — the slab strut")
    else:
        # In the fingerprint because the strut's capacity is 0.85 f'c: a mix change has to
        # stale a seal pinned over this record.
        inputs.append(_Quantity("slab_fc", fc, "psi", 1.0))
        states.append(LimitState(
            "house slab strut compression", line / (t * edge_len), PHI_PLAIN * 0.85 * fc, "psi",
            f"{line:,.0f} lb over {t:.2f}\" x {edge_len:.0f}\" of {slab.tag}; phi 0.60 x 0.85 "
            f"f'c (plain, ACI 318-19 Table 21.2.1, §14.5.6). Buckling not credible: a slab on "
            f"grade is braced continuously by its subgrade"))
    dead, basis = take_down(ctx, solid)
    bottom = min(s.z0_m * _IN for s in ctx.model.solids
                 if s.tag in footings and s.category == "footing")
    depth_ft = (ctx.plan.project.site.grade.inches - bottom) / 12.0
    at_rest = 0.5 * soil.at_rest_efp_psf_per_ft * depth_ft ** 2
    near = max(0.0, edge_len - court_opening_in(ctx, boards))
    net = at_rest * (edge_len - near) / 12.0
    friction = soil.friction_coefficient * dead
    fs = (friction + net) / total_lb if total_lb else float("inf")
    states.append(LimitState(
        "house global sliding", REQUIRED_FS, fs, "",
        f"(mu {soil.friction_coefficient} x D {dead:,.0f} + net at-rest {net:,.0f}) / H "
        f"{total_lb:,.0f} lb. D: {basis}. At rest {soil.at_rest_efp_psf_per_ft:.0f} psf/ft "
        f"over {depth_ft:.3f}' ({at_rest:,.1f} plf) on the far wall's {edge_len / 12:.2f}' less "
        f"the near face's {near / 12:.2f}' (the court retains nothing); passive not credited",
        is_safety_factor=True))
    far = at_rest * edge_len / 12.0 + max(0.0, total_lb - friction)
    cap = 0.5 * soil.lateral_bearing_psf_per_ft * depth_ft ** 2 * edge_len / 12.0
    states.append(LimitState(
        "house far-wall soil bearing", far, cap, "lb",
        f"at rest {at_rest * edge_len / 12:,.0f} + what friction does not take "
        f"{max(0.0, total_lb - friction):,.0f} lb; vs IBC Table 1806.2 lateral bearing "
        f"{soil.lateral_bearing_psf_per_ft:.0f} psf/ft over {depth_ft:.3f}' x "
        f"{edge_len / 12:.2f}'"))
