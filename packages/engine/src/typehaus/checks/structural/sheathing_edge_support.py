"""Every vertical sheathing joint lands on framing (decision #146).

IRC R602.10.4.4: "Vertical joints of panel sheathing shall occur over and be fastened to
common studs"; R602.3 fastens wall sheathing directly to framing members. A joint is backed
where members cover the house's ``min_edge_bearing`` on both sides of it
(``SheetLayoutStandard``, its ``source``), read off ``ResolvedModel.sheet_layouts``.

* FAIL: a vertical joint bare inside its wall's plate-to-plate height (the panel).
* UNKNOWN: bare only over a floor band (no rim, sill or deck edge is modelled behind it);
  a layer with no ``sheet_length``; a layer with no framing behind it.
* Horizontal joints are not graded here: R602.10.4.4 exception 1 lets a WSP panel omit
  their blocking at Table R602.10.3(2) item 8's factor, which ``bracing_eval`` applies.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.quantities import M_PER_IN
from typehaus.resolve.sheet_layout import sheet_layout_standard
from typehaus.resolve.sheet_stock import wall_sheathing

_ID = "structural.sheathing_edge_support"
_CODE = "IRC R602.10.4.4; IRC R602.3"
_PLATES = frozenset({"plate", "raked_plate"})
_TOL_M = 0.125 * M_PER_IN


def _panel_zone(wall) -> tuple[float, float]:
    plates = [m for m in wall.members if m.category in _PLATES]
    if not plates:
        return wall.z0_m, wall.z1_m
    return min(m.z0_m for m in plates), max(max(m.z1_m, m.z1_end_m or m.z1_m) for m in plates)


def _inside(spans, lo: float, hi: float) -> float:
    return sum(max(0.0, min(b, hi) - max(a, lo)) for a, b in spans)


def _where(layout, brk) -> str:
    member = f"{brk.backing} {brk.offset_m / M_PER_IN:+.2f} in" if brk.backing else "no member"
    return (f"{layout.wall_at(brk.at)} run station {brk.at / M_PER_IN:.2f} in ({member}, "
            f"{brk.unbacked_m / M_PER_IN:.1f} in bare)")


def _in_panel(model, layout, brk) -> bool:
    lo, hi = _panel_zone(model.wall(layout.wall_at(brk.at)))
    return _inside(brk.unbacked_spans, lo, hi) > _TOL_M


def _grade(model, layout, source: str) -> Finding:
    tags = layout.wall_tags
    what = f"{', '.join(tags)} {layout.layer_name}"
    if not layout.framed:
        return unknown(_ID, f"{what}: no framing stands behind the layer, so its joints "
                            f"are not graded", tags, code=_CODE)
    bare = [b for b in layout.vertical_breaks if not b.backed]
    in_panel = [b for b in bare if _in_panel(model, layout, b)]
    if in_panel:
        return failed(_ID, f"{what}: {len(in_panel)} vertical joint(s) off framing at "
                           f"{'; '.join(_where(layout, b) for b in in_panel)}{source}", tags,
                      code=_CODE, fix="move the joint onto a stud, or add a stud under it")
    if bare:
        return unknown(_ID, f"{what}: {len(bare)} vertical joint(s) bare only over the floor "
                            f"band, where no rim, sill or deck edge is modelled behind the "
                            f"sheathing: {'; '.join(_where(layout, b) for b in bare)}", tags,
                       code=_CODE, fix="model the floor's rim or blocking on this wall line")
    joints = len(layout.vertical_breaks)
    return passed(_ID, f"{what}: {joints} vertical joint(s), each on framing{source}", tags,
                  code=_CODE)


@check(Tier.STRUCTURAL, _ID)
def sheathing_edge_support(ctx: CheckContext) -> list[Finding]:
    """Each sheathing layer's vertical joints are over framing."""
    model = ctx.model
    plan = getattr(model, "plan", None)
    if plan is None:
        return []
    standard, _ = sheet_layout_standard(plan)
    source = (f" (edge bearing {standard.min_edge_bearing.inches:g} in: {standard.source})"
              if standard is not None and standard.source else "")
    out = [unknown(_ID, f"{wall.tag} {name}: the layer states no sheet_length, so no sheet "
                        f"layout is drawn", (wall.tag,), code=_CODE,
                   fix="state Layer.sheet_length on the assembly")
           for wall in model.walls for name, length in wall_sheathing(plan, wall)
           if length is None]
    out.extend(_grade(model, lay, source) for lay in model.sheet_layouts)
    if not out:
        return [not_applicable(_ID, "no wall carries a sheathing layer", code=_CODE)]
    return out
