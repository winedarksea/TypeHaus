"""A concealed-fastener metal wall panel over open girts, read off its maker's load table.

Two checks, one scope. A wall is in scope when its outermost skin declares ``skin_family``
(one of the building's metal skins), does NOT declare ``exposed_fastener`` (so no
face-fastened span table reaches it — PBR and the garage corrugated stay out), and stands
on a block-standoff girt band with a spacing (``truss_girt_bands``, the one reading
``engineering/girt_screw.py`` shares).

* ``structural.cladding_wind`` — **the prescriptive read.** ASCE 7-16 C&C wall pressure
  (``typehaus.wind``), zone 5, at 0.6W, graded in BOTH directions against the
  ``PublishedCladdingLoad`` on the panel's Material: outward suction against the outward
  allowable, inward push against the inward one. Either may govern. Mints no engineering
  item: this is what took ``wall_panel/W-A-N1`` out of the register on 2026-09-22.
* ``structural.cladding_fastener`` — **an advisory, never an item.** The maker's table
  excludes fasteners by its own footnote, so the NDS 2018 §12.2 withdrawal and AISI S100
  head pull-through the retired item graded are kept as arithmetic a reviewer can read.
  FAIL at WARN severity when either exceeds 1.

One finding set per (material, girt spacing) group, keyed by the lowest wall tag and
naming every member wall — twenty walls in one product over one girt course are one read.

**Oracle.** ``houses/catlin/notes/board_batten_girt_span.md`` §2-§6.2 and §5b;
``tests/test_cladding_read.py`` reproduces it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import wind
from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.cladding_fastener import (
    SHEET_FLANGE_IN,
    fastener_demand_lb,
    pull_through_allowable_lb,
    withdrawal_allowable_lb,
)
from typehaus.checks.structural.published import graded_against_published_cladding
from typehaus.findings import Finding, Result, not_applicable
from typehaus.resolve.framing.truss_girts import truss_girt_bands

_WIND = "structural.cladding_wind"
_FASTENER = "structural.cladding_fastener"
_CODE = "IRC R703.1.2 / ASCE 7-16 §30.3"


@dataclass(frozen=True)
class _Panel:
    wall_tag: str
    material: object
    spacing_in: float
    support_ref: str
    support_thickness_in: float
    support_sg: float | None


def _panels(ctx: CheckContext) -> list[_Panel]:
    catalog = {material.tag: material for material in ctx.plan.library.materials}
    out: list[_Panel] = []
    for wall in ctx.model.walls:
        body = wall.body_layers()
        if len(body) < 2:
            continue
        material = catalog.get(body[-1].material_ref or "")
        if material is None or getattr(material, "skin_family", None) is None:
            continue
        if getattr(material, "exposed_fastener", False):
            continue
        bands = truss_girt_bands(ctx.plan, wall.assembly)
        if bands is None:
            continue
        outer = bands[1]
        spacing = getattr(outer.framing, "spacing", None) if outer.framing else None
        if spacing is None:
            continue
        # The RESOLVED girt layer: a ``layer_materials`` override swaps its material.
        girt = next((layer for layer in body if layer.name == outer.name), None)
        support_ref = (girt.material_ref if girt is not None else outer.material_ref) or ""
        thickness = (girt.thickness_m / 0.0254 if girt is not None
                     else float(outer.thickness.inches))
        out.append(_Panel(
            wall_tag=wall.tag, material=material, spacing_in=float(spacing.inches),
            support_ref=support_ref, support_thickness_in=thickness,
            support_sg=getattr(catalog.get(support_ref), "specific_gravity", None)))
    return out


def _groups(ctx: CheckContext) -> dict[str, list[_Panel]]:
    """One design per ``(material, girt spacing)``, keyed by its lowest wall tag."""
    buckets: dict[tuple[str, float], list[_Panel]] = {}
    for panel in _panels(ctx):
        buckets.setdefault((panel.material.tag, panel.spacing_in), []).append(panel)
    return {min(p.wall_tag for p in members): sorted(members, key=lambda p: p.wall_tag)
            for members in buckets.values()}


@dataclass(frozen=True)
class _Demand:
    q_h: float
    area_ft2: float
    outward_strength: float
    outward_asd: float
    inward_strength: float
    inward_asd: float


def _demand(ctx: CheckContext, spacing_in: float) -> _Demand | str:
    """Zone-5 ASD pressure both ways, or the sentence naming what is missing."""
    basis = wind.wind_basis(ctx.plan.project.site)
    height = wind.mean_roof_height_ft(ctx.model)
    if basis is None:
        return ("the site declares no complete design wind basis (design_wind_speed_mph, "
                "wind_exposure, risk_category)")
    if not height:
        return "no resolved roof gives a mean roof height for q_h"
    q_h = wind.velocity_pressure_psf(basis, height)
    area = wind.effective_wind_area_ft2(spacing_in)
    out_s, out_a = wind.cladding_pressure_asd_psf(q_h, area, "5", sign="negative")
    in_s, in_a = wind.cladding_pressure_asd_psf(q_h, area, "5", sign="positive")
    return _Demand(q_h, area, out_s, out_a, in_s, in_a)


def _subject(key: str, members: list[_Panel]) -> str:
    more = f" and {len(members) - 1} more wall(s)" if len(members) > 1 else ""
    return (f"{key}{more} clad in {members[0].material.tag} over "
            f"{members[0].spacing_in:g}\" open girts")


def _none_in_scope(ctx: CheckContext, cid: str) -> list[Finding]:
    """N/A is earned only from walls actually examined; a wall-less model says nothing."""
    if not ctx.model.walls:
        return []
    return [not_applicable(
        cid, "no wall's outermost skin is a concealed-fastener metal panel over open "
             "girts, the only covering this rule reads a published load row for", (),
        code=_CODE)]


@check(Tier.STRUCTURAL, _WIND)
def cladding_wind(ctx: CheckContext) -> list[Finding]:
    groups = _groups(ctx)
    if not groups:
        return _none_in_scope(ctx, _WIND)
    site = ctx.plan.project.site
    out: list[Finding] = []
    for key, members in sorted(groups.items()):
        panel, tags, subject = members[0], tuple(p.wall_tag for p in members), _subject(
            key, members)
        material = panel.material
        demand = _demand(ctx, panel.spacing_in)
        if isinstance(demand, str):
            out.append(structural_advisory(
                _WIND, f"{subject}: the wind demand cannot be computed — {demand}", tags,
                Result.UNKNOWN, code=_CODE))
            continue
        if not getattr(material, "open_framing_source", None):
            out.append(structural_advisory(
                _WIND, f"{subject}: {material.tag} quotes no maker's permission to span "
                       f"open framing (Material.open_framing_source); a panel nobody's "
                       f"literature puts on girts is the wrong product, not a table to read",
                tags, Result.UNKNOWN, code=_CODE))
            continue
        for direction, asd in (("outward", demand.outward_asd), ("inward", demand.inward_asd)):
            out.append(graded_against_published_cladding(
                _WIND, f"{subject}, zone 5", tags, asd, direction,
                getattr(material, "published_cladding", None),
                material_name=material.name, fastener_spacing_in=panel.spacing_in,
                coverage_in=getattr(material, "fastener_coverage_in", None),
                panel_fastener=getattr(material, "panel_fastener", None),
                support_is_wood=panel.support_sg is not None,
                support_thickness_in=panel.support_thickness_in,
                governing_demand_psf=max(demand.outward_asd, demand.inward_asd),
                wind_speed_mph=getattr(site, "design_wind_speed_mph", None),
                exposure=getattr(site, "wind_exposure", None)))
    return out


@check(Tier.STRUCTURAL, _FASTENER)
def cladding_fastener(ctx: CheckContext) -> list[Finding]:
    groups = _groups(ctx)
    if not groups:
        return _none_in_scope(ctx, _FASTENER)
    return [_fastener(ctx, key, members) for key, members in sorted(groups.items())]


def _fastener(ctx: CheckContext, key: str, members: list[_Panel]) -> Finding:
    panel, tags, subject = members[0], tuple(p.wall_tag for p in members), _subject(
        key, members)
    material = panel.material
    demand = _demand(ctx, panel.spacing_in)
    if isinstance(demand, str):
        return structural_advisory(_FASTENER, f"{subject}: {demand}", tags, Result.UNKNOWN,
                                   code=_CODE)
    need = {
        "Material.specific_gravity on the support " + (panel.support_ref or "(unnamed)"):
            panel.support_sg,
        f"Material.panel_fastener_diameter_in on {material.tag}":
            getattr(material, "panel_fastener_diameter_in", None),
        f"Material.panel_fastener_length_in on {material.tag}":
            getattr(material, "panel_fastener_length_in", None),
        f"Material.fastener_coverage_in on {material.tag}":
            getattr(material, "fastener_coverage_in", None),
        f"Material.panel_fastener_head_dia_in on {material.tag}":
            getattr(material, "panel_fastener_head_dia_in", None),
    }
    missing = [name for name, value in need.items() if value is None]
    if missing:
        return structural_advisory(
            _FASTENER, f"{subject}: the concealed-leg screw cannot be graded without "
                       f"{'; '.join(missing)}", tags, Result.UNKNOWN, code=_CODE)
    sg, dia, length, coverage, head = (float(v) for v in need.values())
    withdrawal = withdrawal_allowable_lb(sg, dia, length, panel.support_thickness_in,
                                         SHEET_FLANGE_IN)
    load = fastener_demand_lb(demand.outward_asd, panel.spacing_in, coverage)
    if withdrawal.reason is not None:
        return structural_advisory(_FASTENER, f"{subject}: {withdrawal.reason}", tags,
                                   Result.FAIL, code=_CODE)
    pull = pull_through_allowable_lb(head)
    w_ratio, p_ratio = load / withdrawal.capacity_lb, load / pull
    ladder = "; ".join(
        f"{rung:g}\" -> {alt.thread_penetration_in:.3f}\" pen, {alt.capacity_lb:.0f} lb"
        for rung in _rungs(length)
        for alt in (withdrawal_allowable_lb(sg, dia, rung, panel.support_thickness_in,
                                            SHEET_FLANGE_IN),))
    over = w_ratio > 1.0 or p_ratio > 1.0
    return structural_advisory(
        _FASTENER,
        f"{subject}: {load:.1f} lb per screw ({demand.outward_asd:.2f} psf ASD suction x "
        f"{panel.spacing_in:g}\" x {coverage:g}\"). Withdrawal, NDS 2018 §12.2 at G {sg:g}, "
        f"C_D 1.6, C_M 0.7, {withdrawal.thread_penetration_in:.3f}\" thread in the girt: "
        f"{withdrawal.capacity_lb:.1f} lb, d/c {w_ratio:.3f}. Head pull-through, AISI S100 "
        f"Pnov = 1.5 t d'w Fu at t {SHEET_FLANGE_IN:g}\", d'w {head:g}\", Omega 3: "
        f"{pull:.1f} lb, d/c {p_ratio:.3f}. Screw ladder: {ladder}. An advisory: the maker's "
        f"table excludes fasteners and names this screw; the arithmetic is kept so a "
        f"reviewer can see the screw is not the weak link",
        tags, Result.FAIL if over else Result.PASS, code="AWC NDS 2018 §12.2 / AISI S100",
        fix_hint="a longer screw or a tighter girt course" if over else None)


def _rungs(authored: float) -> list[float]:
    """The stock lengths plus the authored one, de-duplicated in order."""
    rungs: list[float] = []
    for rung in (1.0, 1.5, 2.0, authored):
        if rung > 0.0 and not any(abs(rung - seen) < 1e-6 for seen in rungs):
            rungs.append(rung)
    return rungs
