"""``structural.footing_size`` — each plain concrete wall strip against IRC Table R403.1(1).

R403.1.1 sizes a light-frame house's strip footings off Tables R403.1(1)-(3) and the soil's
R401.4.1 value. Every PLAIN concrete ``Footing`` hosted under a wall (``Footing.under``) is
read against :mod:`footing_tables`, at:

* **stories** — the building's storeys above the footing's storey, a storey sharing a
  ``level`` counted once. A habitable attic that is a storey in the model counts: the
  table's attic basis is half a storage attic, not a living floor, and it may not be
  extrapolated. More than three is outside the table (UNKNOWN).
* **foundation** — a footing under storeys is read on "plus basement", the heaviest
  foundation row, so a crawl space is graded conservatively; with none above, "slab on
  grade" at one story.
* **snow** — ``Site.ground_snow_load_psf``; **soil** — ``checks/soil.site_soil_bearing_psf``;
  **house width** — the short side of the footing storey's wall axes (footnote b).

Out of scope: a reinforced strip (a designed footing, as in ``bearing_wall_footing``'s
projection leg) and a crushed-stone one (R403.4's own table). The footing must meet both W
and T; R403.1.1's 2" <= P <= T is graded by ``structural.bearing_wall_footing``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.soil import site_soil_bearing_psf
from typehaus.checks.structural.footing_tables import (
    SNOW_BANDS_PSF,
    SOIL_COLUMNS_PSF,
    required_footing_in,
)
from typehaus.findings import Finding

_CID = "structural.footing_size"
_CODE = "IRC R403.1.1, Table R403.1(1)"
_IN = 0.0254
_FT = 0.3048
_TOL_IN = 1e-6


def _stories_above(plan, storey_tag: str) -> int | None:
    storeys = {s.tag: s for s in plan.storeys}
    base = storeys.get(storey_tag)
    if base is None:
        return None
    above = {s.level or s.tag for s in storeys.values()
             if s.building == base.building and s.tag != base.tag
             and s.elevation.meters > base.elevation.meters + 1e-6}
    return len(above)


def _house_width_ft(model, storey_tag: str) -> float | None:
    from shapely.geometry import MultiPoint

    points = [p for w in model.walls if w.storey == storey_tag for p in w.axis]
    hull = MultiPoint(points).convex_hull if len(points) >= 3 else None
    if hull is None or hull.geom_type != "Polygon":
        return None
    # The least-area rectangle has a side on a hull edge (rotating calipers); shapely's own
    # oriented envelope warns on a plain rectangle.
    ring = list(hull.exterior.coords)
    best: tuple[float, float] | None = None
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if run <= 1e-9:
            continue
        ux, uy = (x1 - x0) / run, (y1 - y0) / run
        along = [x * ux + y * uy for x, y in ring]
        across = [y * ux - x * uy for x, y in ring]
        sides = (max(along) - min(along), max(across) - min(across))
        if best is None or sides[0] * sides[1] < best[0] * best[1]:
            best = sides
    return min(best) / _FT if best else None


@check(Tier.STRUCTURAL, _CID)
def footing_size(ctx: CheckContext) -> list[Finding]:
    """Grade each plain concrete wall strip's W x T against Table R403.1(1)."""
    if ctx.plan is None:
        return []
    from typehaus.model.structure import Footing
    from typehaus.resolve.construction_sills import _is_concrete_ref

    solids = {s.tag: s for s in ctx.model.solids if s.category == "footing"}
    strips = []
    for footing in ctx.plan.all_elements():
        if not isinstance(footing, Footing) or footing.reinforcement is not None:
            continue
        wall, solid = ctx.model.wall(footing.under), solids.get(footing.tag)
        if wall is None or solid is None or not _is_concrete_ref(ctx.model, footing.assembly):
            continue
        strips.append((footing, wall, solid))
    if not strips:
        return [not_applicable(_CID, "no plain cast-in-place concrete strip stands under a "
                               "wall; reinforced and crushed-stone footings are sized "
                               "elsewhere", code=_CODE)]

    site = ctx.plan.project.site
    snow = site.ground_snow_load_psf if site is not None else None
    soil = site_soil_bearing_psf(ctx.plan, ctx.profile)
    out: list[Finding] = []
    for footing, wall, solid in sorted(strips, key=lambda s: s[0].tag):
        tags = (footing.tag, wall.tag)
        stories = _stories_above(ctx.plan, wall.storey)
        width_ft = _house_width_ft(ctx.model, wall.storey)
        why = ("no ground snow load is stated" if snow is None else
               "no soil class or bearing value is stated" if soil is None else
               f"{snow:g} psf ground snow is past the table's last band"
               if snow > SNOW_BANDS_PSF[-1] else
               f"{soil:,.0f} psf soil is under the table's first column (R401.4.1 asks "
               "for a soils investigation)" if soil < SOIL_COLUMNS_PSF[0] else
               f"storey {wall.storey} is not in the plan" if stories is None else
               f"{stories} stories stand over it, past the table's three"
               if stories > 3 else
               "the storey's walls give no house width" if width_ft is None else None)
        if why:
            out.append(unknown(_CID, f"{footing.tag}: {why}, so Table R403.1(1) cannot be "
                               "read", tags, code=_CODE))
            continue
        row = (stories, "basement") if stories else (1, "slab")
        need_w, need_t = required_footing_in(*row, snow, soil, width_ft)
        have_w = footing.width.inches if footing.width is not None else None
        have_t = (solid.z1_m - solid.z0_m) / _IN
        if have_w is None:
            out.append(unknown(_CID, f"{footing.tag} authors no width", tags, code=_CODE))
            continue
        read = (f"{row[0]} story{' plus basement' if row[1] == 'basement' else ', slab'}, "
                f"{snow:g} psf snow, {soil:,.0f} psf soil, {width_ft:.1f}' house "
                f"(footnote b)")
        said = f"{footing.tag} is {have_w:.2f}\" x {have_t:.2f}\" against {need_w:.1f}\" x " \
               f"{need_t:.1f}\" ({read})"
        if have_w + _TOL_IN < need_w or have_t + _TOL_IN < need_t:
            out.append(failed(_CID, said, tags, code=_CODE,
                              fix="widen the strip (Footing.width) and deepen it "
                                  "(Footing.depth) to the table, or engineer it"))
        else:
            out.append(passed(_CID, said, tags, code=_CODE))
    return out
