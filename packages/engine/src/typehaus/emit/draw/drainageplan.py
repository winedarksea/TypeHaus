"""Drainage plan → drawing IR (→ 20 §Drawing IR).

One sheet per storey that owns stormwater content: the resolved drainage solids on that
storey — authored gutters/leaders, drain tile, french drains, sumps and drywells — plus the
channels a roof *derives* along its own eaves, which are members rather than solids and
would otherwise appear on no drawing at all. The trade already has a real IFC system
(``emit/ifc/mep.py::_emit_stormwater_system``) and a real BOM section
(``takeoff/drainage.py``); this is the sheet an installer hangs it from.

Same skeleton as :mod:`typehaus.emit.draw.plumbingplan`: ghost walls for orientation, one
polyline per run/pit on a stormwater layer, buried work dashed, and a tag on everything an
inspector would ask about.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_ghost_walls
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.emit.trades import DRAINAGE_CATEGORIES
from typehaus.resolve.model import ResolvedModel

#: Solid category → (layer, linetype). Buried work (tile, trench, soakaway) is dashed;
#: hung and surface work draws solid. All four layers are styled in both writers
#: (→ test_writer_layer_coverage).
_CATEGORY_STYLE = {
    "gutter": ("P-STRM-GUTR", "CONTINUOUS"),
    "downspout": ("P-STRM-LEDR", "CONTINUOUS"),
    "drain_tile": ("P-STRM-TILE", "DASHED"),
    "french_drain": ("P-STRM-TILE", "DASHED"),
    "sump": ("P-STRM-PIT", "CONTINUOUS"),
    "drywell": ("P-STRM-PIT", "DASHED"),
}


def _storey_solids(model: ResolvedModel, storey_tag: str) -> list:
    return [solid for solid in model.solids
            if solid.storey == storey_tag
            and (solid.category or "").lower() in DRAINAGE_CATEGORIES]


def _derived_gutter_members(model: ResolvedModel, storey_tag: str) -> list[tuple]:
    """(roof, member) for each derived eave-gutter band on this storey's roofs.

    Only the ``bottom`` band draws — the channel is three bands of one open U, and three
    parallel polylines a half-inch apart read as three gutters.
    """
    out = []
    for roof in model.roofs:
        if roof.storey != storey_tag:
            continue
        for member in roof.members:
            if member.category == "gutter" and member.child_key.endswith("-bottom"):
                out.append((roof, member))
    return out


def has_drainage_content(model: ResolvedModel, storey_tag: str) -> bool:
    return bool(_storey_solids(model, storey_tag)
                or _derived_gutter_members(model, storey_tag))



def build_drainage_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name=f"drainage-{storey}", units="in")
    emit_ghost_walls(b, model, storey)

    # One label per element tag, at the first solid drawn for it: a banded gutter or a
    # multi-segment tile run is many solids and must not become a picket of labels.
    labelled: set[str] = set()
    for solid in sorted(_storey_solids(model, storey), key=lambda s: s.uid):
        layer, linetype = _CATEGORY_STYLE[(solid.category or "").lower()]
        points = tuple(_in(p) for p in solid.outline)
        if len(points) < 2:
            continue
        b.add(Polyline(points=points, closed=True, layer=layer, lineweight=0.35,
                       linetype=linetype, uid=solid.uid, tag=solid.tag))
        base = (solid.tag or "").rstrip("0123456789").rstrip("-")
        if base and base not in labelled:
            labelled.add(base)
            x = sum(p[0] for p in points) / len(points)
            y = max(p[1] for p in points)
            b.add(Text(anchor=(x, y + 0.5), content=base, height=2.0,
                       layer="A-ANNO-TEXT", align="center"))

    for roof, member in _derived_gutter_members(model, storey):
        b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="P-STRM-GUTR",
                       lineweight=0.35, uid=f"{roof.uid}-{member.child_key}",
                       tag=f"{roof.tag}:{member.child_key}"))
        mid = ((member.p0[0] + member.p1[0]) / 2.0, (member.p0[1] + member.p1[1]) / 2.0)
        b.add(Text(anchor=_in((mid[0], mid[1])), content=f"{roof.tag} EAVE GUTTER",
                   height=2.0, layer="A-ANNO-TEXT", align="center"))
    return b.build()
