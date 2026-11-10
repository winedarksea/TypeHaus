"""Grounding electrodes and bonding conductors on the plans (decision #123).

One module so the E-10x electrical plans and the C-101 site plan draw the same glyphs:
a driven rod is a circle with a cross (an LPS terminal rod, an X), the concrete-encased
electrode a square with an X at its stub, a bond a dashed ``E-GRND`` polyline lettered
``#6 CU GEC``. Glyphs are plain polylines, writer-agnostic, in model inches.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.annotation_requests import add_point_label
from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text
from typehaus.emit.draw.typography import MIN_PT
from typehaus.quantities import M_PER_IN

LAYER = "E-GRND"
_ROD_R_IN = 5.0
_ROLE_LABEL = {
    "gec": "GEC", "bonding_jumper": "BJ", "ibt": "IBT BOND", "water_bond": "WATER BOND",
    "counterpoise": "COUNTERPOISE", "down_lead": "PV DOWN-LEAD",
}


def _grounding(model):
    g = getattr(model, "grounding", None)
    return g if g is not None and (g.electrodes or g.bonds) else None


def _ft_in(metres: float) -> str:
    inches = round(metres / M_PER_IN)
    return f"{inches // 12}'-{inches % 12}\""


def bond_label(bond) -> str:
    metal = "AL" if bond.material == "aluminum" else "CU"
    skin = "" if bond.bare else " INSUL"
    return f"#{bond.size} {metal}{skin} {_ROLE_LABEL.get(bond.role, bond.role.upper())}"


def electrode_label(el) -> str:
    base = el.tag.removeprefix("GE-")
    if el.kind == "concrete_encased":
        bar = f"{_ft_in(el.length_m)} #{el.bar} BAR" if el.length_m else "NO QUALIFYING BAR"
        return f"{base} {bar}"
    if el.use == "lps_terminal":
        return f"{base} LPS TERMINAL"
    return f"{base} ROD {_ft_in(el.length_m)}"


def rod_glyph(b: SceneBuilder, xy_m, *, layer: str = LAYER, lps: bool = False,
              uid: str | None = None, tag: str | None = None, radius_in: float = _ROD_R_IN) -> None:
    """A circle with a cross; an LPS terminal rod takes the diagonal cross."""
    cx, cy = _in(xy_m)
    ring = tuple((cx + radius_in * math.cos(a), cy + radius_in * math.sin(a))
                 for a in (i * math.pi / 8 for i in range(16)))
    b.add(Polyline(points=ring, closed=True, layer=layer, uid=uid, tag=tag))
    reach = radius_in * 1.5
    arms = ((math.pi / 4, 5 * math.pi / 4), (3 * math.pi / 4, 7 * math.pi / 4)) if lps \
        else ((0.0, math.pi), (math.pi / 2, 3 * math.pi / 2))
    for a0, a1 in arms:
        b.add(Polyline(points=((cx + reach * math.cos(a0), cy + reach * math.sin(a0)),
                               (cx + reach * math.cos(a1), cy + reach * math.sin(a1))),
                       layer=layer))


def ufer_glyph(b: SceneBuilder, xy_m, *, layer: str = LAYER, uid: str | None = None,
               tag: str | None = None, half_in: float = _ROD_R_IN) -> None:
    """The concrete-encased electrode's stub: a square with an X."""
    cx, cy = _in(xy_m)
    h = half_in
    b.add(Polyline(points=((cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)),
                   closed=True, layer=layer, uid=uid, tag=tag))
    b.add(Polyline(points=((cx - h, cy - h), (cx + h, cy + h)), layer=layer))
    b.add(Polyline(points=((cx - h, cy + h), (cx + h, cy - h)), layer=layer))


def bond_polyline(b: SceneBuilder, bond, *, lineweight: float = 0.35) -> bool:
    pts = [(p[0], p[1]) for p in bond.path]
    if len({(round(x, 4), round(y, 4)) for x, y in pts}) < 2:
        return False
    b.add(Polyline(points=tuple(_in(p) for p in pts), layer=LAYER, lineweight=lineweight,
                   linetype="DASHED", uid=bond.uid, tag=bond.tag))
    return True


def emit_grounding(b: SceneBuilder, model, storey: str) -> None:
    """Electrodes and bonds authored on ``storey`` itself; nothing when the house has none."""
    g = _grounding(model)
    if g is None:
        return
    on = {storey}  # as the devices: a sibling structure's electrical has no sheet of its own
    for el in g.electrodes:
        if el.storey not in on:
            continue
        if el.kind == "concrete_encased":
            ufer_glyph(b, el.xy, uid=el.uid, tag=el.tag)
        else:
            rod_glyph(b, el.xy, lps=el.use == "lps_terminal", uid=el.uid, tag=el.tag)
        add_point_label(b, key=f"ground-{el.uid}", text=electrode_label(el), target=_in(el.xy),
                        layer=LAYER, height_pt=MIN_PT, priority=30, leader=False)
    for bond in g.bonds:
        if bond.storey not in on or not bond_polyline(b, bond):
            continue
        mid = bond.path[len(bond.path) // 2]
        add_point_label(b, key=f"bond-{bond.uid}", text=bond_label(bond),
                        target=_in((mid[0], mid[1])), layer=LAYER, height_pt=MIN_PT,
                        priority=25, leader=False)


def legend_rows(model, storey: str) -> list[str]:
    """Legend entries for the grounding glyphs present on ``storey``."""
    g = _grounding(model)
    if g is None:
        return []
    on = {storey}  # as the devices: a sibling structure's electrical has no sheet of its own
    here = [e for e in g.electrodes if e.storey in on]
    rows = []
    if any(e.kind != "concrete_encased" and e.use != "lps_terminal" for e in here):
        rows.append("rod")
    if any(e.use == "lps_terminal" for e in here):
        rows.append("lps")
    if any(e.kind == "concrete_encased" for e in here):
        rows.append("ufer")
    if any(bd.storey in on for bd in g.bonds):
        rows.append("bond")
    return rows


_LEGEND_TEXT = {
    "rod": "GROUND ROD", "lps": "LPS TERMINAL ROD", "ufer": "CONCRETE-ENCASED ELECTRODE",
    "bond": "BONDING CONDUCTOR (BARE UNLESS NOTED)",
}


def emit_legend(b: SceneBuilder, model, storey: str, origin_m, first_row: int,
                row_pitch_m: float = 0.6) -> None:
    """Append grounding rows to the electrical legend (origin in metres)."""
    for i, key in enumerate(legend_rows(model, storey)):
        y = origin_m[1] - (first_row + i + 1) * row_pitch_m
        if key == "bond":
            b.add(Polyline(points=(_in((origin_m[0] - 0.2, y)), _in((origin_m[0] + 0.2, y))),
                           layer=LAYER, linetype="DASHED", lineweight=PROFILE))
        elif key == "ufer":
            ufer_glyph(b, (origin_m[0], y), half_in=3.0)
        else:
            rod_glyph(b, (origin_m[0], y), lps=key == "lps", radius_in=3.0)
        b.add(Text(anchor=_in((origin_m[0] + 0.6, y)), content=_LEGEND_TEXT[key], height=2.5,
                   layer="A-ANNO-TEXT"))


def site_electrodes(model) -> Iterable:
    g = _grounding(model)
    return [] if g is None else [e for e in g.electrodes if e.kind != "concrete_encased"]


def site_bonds(model, roles: frozenset[str]) -> list:
    g = _grounding(model)
    return [] if g is None else [bd for bd in g.bonds if bd.role in roles]


def emit_site(b: SceneBuilder, model, *, layer: str = LAYER, text_pt: float = MIN_PT) -> None:
    """C-101: every rod, the counterpoise and the PV down-lead, lettered."""
    for el in site_electrodes(model):
        rod_glyph(b, el.xy, layer=layer, lps=el.use == "lps_terminal", uid=el.uid, tag=el.tag,
                  radius_in=_ROD_R_IN * 2)
        add_point_label(b, key=f"ground-{el.uid}", text=electrode_label(el), target=_in(el.xy),
                        layer=layer, height_pt=text_pt, priority=35)
    for bond in site_bonds(model, frozenset({"counterpoise", "down_lead"})):
        if bond_polyline(b, bond):
            mid = bond.path[len(bond.path) // 2]
            add_point_label(b, key=f"bond-{bond.uid}", text=bond_label(bond),
                            target=_in((mid[0], mid[1])), layer=layer, height_pt=text_pt,
                            priority=30)
