"""IRC R324.6 — roof access for rooftop PV, as the 2020 Minnesota Residential Code has it.

Source: MN DLI "Solar photovoltaic systems and the 2020 MN Residential Code" (rev. 2022-02,
dli.mn.gov/sites/default/files/pdf/fs_res_solar.pdf) over the adopted 2018 IRC R324.6:

* R324.6.1 pathways: at least two 36" pathways on separate roof planes, lowest edge to
  ridge, one on the street/driveway side; each array plane has one on its own plane, an
  adjacent plane, or straddling both.
* R324.6.2 ridge setback, each side of the ridge: 18" when the array is <= 33% of the plan
  view total roof area, 36" above that. (The 66% sprinklered alternative is not graded: the
  house is unsprinklered.)
* Exceptions: slope <= 2:12 (N/A here, earned from the pitch); a code-official waiver (a
  human decision, never graded). Pathways, setbacks and areas are plan-view measures.

Modelled: gable roofs, modules' plan hull (so the standoff lean toward the ridge counts),
ridge-parallel setback, free eave-to-ridge corridors between module along-ridge extents, the
street side from ``Site.streets``. Not modelled: pathway live load, obstructions (vents,
conduit), the emergency-escape-opening rule, hip/valley layouts (UNKNOWN).
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

CID = "code.R324_rooftop_pv_access"
_PATHWAY_MIN_IN = 36.0
_SETBACK_LOW_IN, _SETBACK_HIGH_IN = 18.0, 36.0
_COVERAGE_SPLIT = 0.33
_EXEMPT_SLOPE = 2.0 / 12.0  # R324.6 exception: 2:12 or flatter
_TOL_IN = 0.01
_BUTT_TOL_M = 0.005  # modules butted edge to edge leave no pathway


@dataclass(frozen=True)
class _Module:
    tag: str
    side: int  # -1 / +1 about the ridge
    along: tuple[float, float]  # plan hull along the ridge, m
    near_cross_m: float  # |hull cross distance| to the ridge, nearest corner
    area_m2: float


def _shoelace(ring) -> float:
    n = len(ring)
    return abs(sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1]
                   for i in range(n))) / 2.0


def _inches(m: float) -> str:
    return f"{m / M_PER_IN:.1f}\""


def _modules(roof, panels, a: int, c: int, ridge_c: float) -> list[_Module]:
    out = []
    for p in panels:
        pts = [*p.corners_bottom, *p.corners_top]
        along = [q[a] for q in pts]
        cross = [q[c] - ridge_c for q in pts]
        side = 1 if sum(cross) > 0 else -1
        out.append(_Module(p.tag, side, (min(along), max(along)),
                           min(abs(x) for x in cross),
                           _shoelace([(q[0], q[1]) for q in p.corners_top[:4]])))
    return out


def _corridors(mods: list[_Module], lo: float, hi: float) -> list[tuple[float, float]]:
    """Free along-ridge intervals of the plane, ``lo``..``hi`` less the modules' extents."""
    free, cursor = [], lo
    for m in sorted(mods, key=lambda m: m.along[0]):
        if m.along[0] - cursor > _BUTT_TOL_M:
            free.append((cursor, m.along[0]))
        cursor = max(cursor, m.along[1])
    if hi - cursor > _BUTT_TOL_M:
        free.append((cursor, hi))
    return free


def _street_side(ctx: CheckContext, roof_xy: tuple[float, float], along_axis: int):
    """``("along"|"cross", sign)``: which side of the roof the street is on, or None."""
    site = ctx.plan.project.site
    parcel = [p.xy_m for p in site.parcel]
    if not site.streets or len(parcel) < 3:
        return None
    e = site.streets[0].edge % len(parcel)
    (x0, y0), (x1, y1) = parcel[e], parcel[(e + 1) % len(parcel)]
    d = ((x0 + x1) / 2 - roof_xy[0], (y0 + y1) / 2 - roof_xy[1])
    d_along, d_cross = d[along_axis], d[1 - along_axis]
    return ("along", 1 if d_along > 0 else -1) if abs(d_along) >= abs(d_cross) \
        else ("cross", 1 if d_cross > 0 else -1)


@check(Tier.CODE, CID)
def rooftop_pv_access(ctx: CheckContext) -> list[Finding]:
    """R324.6 — pathways, ridge setback and coverage of each roof carrying PV."""
    panels = list(ctx.model.solar_panels)
    if not panels:
        return [_na(CID, "no rooftop PV modules are placed, so R324.6 has no array to "
                         "leave access around", (), "IRC R324.6")]
    out: list[Finding] = []
    for roof in ctx.model.roofs:
        mine = [p for p in panels if p.roof_ref == roof.tag]
        if mine:
            out.extend(_grade_roof(ctx, roof, mine))
    orphans = {p.roof_ref for p in panels} - {r.tag for r in ctx.model.roofs}
    out.extend(_unknown(CID, f"modules reference unresolved roof {tag}", (tag,), "IRC R324.6")
               for tag in sorted(orphans))
    return out


def _grade_roof(ctx: CheckContext, roof, panels) -> list[Finding]:
    tags = (roof.tag, *(p.tag for p in panels))
    xs, ys = [p[0] for p in roof.footprint], [p[1] for p in roof.footprint]
    if roof.form != "gable":
        return [_unknown(CID, f"{roof.tag} is a {roof.form} roof; pathway and ridge geometry "
                              "is graded for gables only", tags, "IRC R324.6")]
    c = 0 if roof.ridge_direction == "y" else 1  # cross-ridge axis index
    a = 1 - c
    cross_all = [p[c] for p in roof.footprint]
    ridge_c = (min(cross_all) + max(cross_all)) / 2.0
    half_span = (max(cross_all) - min(cross_all)) / 2.0
    slope = (roof.ridge_z_m - roof.eave_z_m) / half_span
    if slope <= _EXEMPT_SLOPE:
        return [_na(CID, f"{roof.tag} slopes {slope * 12:.1f}:12, at or under the 2:12 "
                         "R324.6 exception", tags, "IRC R324.6")]
    along_all = [p[a] for p in roof.footprint]
    lo, hi = min(along_all), max(along_all)
    mods = _modules(roof, panels, a, c, ridge_c)
    out: list[Finding] = []

    # R324.6.2 — setback by coverage (plan view over plan view).
    coverage = sum(m.area_m2 for m in mods) / _shoelace(roof.footprint)
    need_in = _SETBACK_LOW_IN if coverage <= _COVERAGE_SPLIT else _SETBACK_HIGH_IN
    basis = (f"array {coverage * 100:.1f}% of the plan-view roof "
             f"({'<=' if coverage <= _COVERAGE_SPLIT else '>'} 33%)")
    for side, name in ((-1, "low-side"), (1, "high-side")):
        row = [m for m in mods if m.side == side]
        if not row:
            continue
        near = min(m.near_cross_m for m in row) / M_PER_IN
        msg = (f"{roof.tag} {name} plane: ridge setback {near:.1f}\" against {need_in:.0f}\" "
               f"required; {basis}")
        out.append(_pass(CID, msg, "IRC R324.6.2") if near >= need_in - _TOL_IN else
                   _fail(CID, msg, tuple(m.tag for m in row), "IRC R324.6.2"))

    # R324.6.1 — a 36" eave-to-ridge corridor on each of two planes.
    best: dict[int, float] = {}
    corridors: dict[int, list[tuple[float, float]]] = {}
    for side in (-1, 1):
        corridors[side] = _corridors([m for m in mods if m.side == side], lo, hi)
        best[side] = max((e - s for s, e in corridors[side]), default=0.0) / M_PER_IN
    ok_planes = [s for s in (-1, 1) if best[s] >= _PATHWAY_MIN_IN - _TOL_IN]
    msg = (f"{roof.tag}: widest free eave-to-ridge pathway {best[-1]:.1f}\" on the low-side "
           f"plane, {best[1]:.1f}\" on the high-side plane; two planes need "
           f"{_PATHWAY_MIN_IN:.0f}\"")
    out.append(_pass(CID, msg, "IRC R324.6.1") if len(ok_planes) == 2 else
               _fail(CID, msg, tags, "IRC R324.6.1"))

    # R324.6.1 — one of them on the street/driveway side.
    street = _street_side(ctx, (sum(xs) / len(xs), sum(ys) / len(ys)), a)
    if street is None:
        out.append(_unknown(CID, "no street frontage or parcel is declared, so the "
                                 "street-side pathway cannot be placed", tags, "IRC R324.6.1"))
        return out
    kind, sign = street
    mid = (lo + hi) / 2.0
    if kind == "cross":  # street faces a roof plane: that plane carries the pathway
        hit = sign in ok_planes
    else:  # street at a gable end: a corridor centred in that half of the roof
        hit = any((e - s) / M_PER_IN >= _PATHWAY_MIN_IN - _TOL_IN
                  and sign * ((s + e) / 2 - mid) > 0
                  for side in (-1, 1) for s, e in corridors[side])
    where = "its facing plane" if kind == "cross" else "the street-end half of the ridge"
    msg = f"{roof.tag}: street-side pathway of {_PATHWAY_MIN_IN:.0f}\" on {where}"
    out.append(_pass(CID, f"{msg} found", "IRC R324.6.1") if hit else
               _fail(CID, f"{msg} missing", tags, "IRC R324.6.1"))
    return out
