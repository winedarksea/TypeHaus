"""Electrical plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 3).

Symbols-only E-101 (decision 1): device positions + a legend. No circuit numbering —
``ElectricalDevice.circuit`` is a schema hook for a future panel schedule, unused here.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.resolve.model import ResolvedModel

_DEVICE_LAYER = {
    "receptacle": "E-POWR-DEVC", "gfci": "E-POWR-DEVC", "receptacle_240": "E-POWR-DEVC",
    "switch": "E-LITE", "light": "E-LITE", "panel": "E-POWR-DEVC",
    "junction_box": "E-POWR-DEVC", "meter": "E-POWR-DEVC", "disconnect": "E-POWR-DEVC",
}
_LEGEND = (
    ("receptacle", "DUPLEX RECEPTACLE"), ("gfci", "GFCI RECEPTACLE"),
    ("receptacle_240", "240V RECEPTACLE"), ("switch", "SWITCH"), ("light", "LIGHT"),
    ("panel", "ELECTRICAL PANEL"), ("junction_box", "JUNCTION BOX"),
    ("meter", "UTILITY METER"), ("disconnect", "DISCONNECT"),
)


def has_electrical_content(model: ResolvedModel, storey_tag: str) -> bool:
    return any(element.element_kind == "ElectricalDevice"
              for element in model.plan.storey_elements(storey_tag))


def build_electrical_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name=f"electrical-{storey}", units="in")
    for wall in model.walls:
        if wall.storey == storey:
            emit_wall(b, wall, layer_override="A-WALL-BELW", weight_override=0.15,
                     hatch=False, members=False)

    for element in model.plan.storey_elements(storey):
        if element.element_kind != "ElectricalDevice":
            continue
        layer = _DEVICE_LAYER.get(element.kind.value, "E-POWR-DEVC")
        b.add(Symbol(name=element.kind.value, insert=_in(element.position.xy_m), layer=layer))
        b.add(Text(anchor=_in((element.position.xy_m[0] + 0.1, element.position.xy_m[1] + 0.1)),
                   content=element.tag.removeprefix("ED-"), height=1.5, layer="A-ANNO-TEXT"))

    # Conduit trunks: dashed homerun polylines on their own raceway layer. The label sits
    # at the polyline's middle vertex — every trunk shares the panel as its first point,
    # so a first-vertex anchor stacks all the labels on one spot.
    for run in model.conduits:
        if run.storey != storey:
            continue
        b.add(Polyline(points=tuple(_in(p) for p in run.path), layer="E-POWR-CNDT",
                       linetype="DASHED", uid=run.uid, tag=run.tag))
        mid = run.path[len(run.path) // 2]
        b.add(Text(anchor=_in((mid[0] + 0.1, mid[1] + 0.25)),
                   content=f"{run.tag.removeprefix('CD-')} {run.trade_size_m * 39.3701:.3g}\"",
                   height=1.5, layer="A-ANNO-TEXT"))

    _emit_legend(b, model, storey)
    return b.build()


def _emit_legend(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    present = {element.kind.value for element in model.plan.storey_elements(storey)
              if element.element_kind == "ElectricalDevice"}
    if not present:
        return
    xs = [wall.axis[0][0] for wall in model.walls if wall.storey == storey]
    ys = [wall.axis[0][1] for wall in model.walls if wall.storey == storey]
    origin = (max(xs, default=0.0) + 2.0, min(ys, default=0.0))
    b.add(Text(anchor=_in(origin), content="LEGEND", height=3.5, layer="A-ANNO-TEXT"))
    for row, (kind, label) in enumerate(k for k in _LEGEND if k[0] in present):
        y = origin[1] - (row + 1) * 0.6
        b.add(Symbol(name=kind, insert=_in((origin[0], y)), layer=_DEVICE_LAYER[kind]))
        b.add(Text(anchor=_in((origin[0] + 0.6, y)), content=label, height=2.5,
                   layer="A-ANNO-TEXT"))
