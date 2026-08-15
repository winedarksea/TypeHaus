"""HVAC plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 3).

One sheet per storey owning duct content. Ducts draw as a double-line plan rectangle
(``rect_between`` — the same wall-band helper the resolver's geometry module uses);
bearing-line crossings get a Leader calling out fire blocking per R302.11.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_ghost_walls
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Leader, NamedPoint, Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel

_SUPPLY_LAYER = "M-HVAC-SDFF"
_RETURN_LAYER = "M-HVAC-RDFF"
_EXHAUST_LAYER = "M-HVAC-EXHS"
_SYSTEM_LAYERS = {"supply": _SUPPLY_LAYER, "return": _RETURN_LAYER, "exhaust": _EXHAUST_LAYER}


def _system_layer(system: str) -> str:
    return _SYSTEM_LAYERS.get(system, _RETURN_LAYER)


def has_hvac_content(model: ResolvedModel, storey_tag: str) -> bool:
    return any(duct.storey == storey_tag for duct in model.ducts)


def build_hvac_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name=f"hvac-{storey}", units="in")
    emit_ghost_walls(b, model, storey)

    occupied_floors = {duct.floor_ref for duct in model.ducts
                       if duct.storey == storey and duct.floor_ref is not None}
    for floor in model.floors:
        if floor.tag in occupied_floors:
            for member in floor.members:
                b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-FRAM",
                               lineweight=0.13, uid=floor.uid, tag=member.child_key))

    for duct in model.ducts:
        if duct.storey != storey:
            continue
        layer = _system_layer(duct.system)
        for i in range(len(duct.path) - 1):
            outline = rect_between(duct.path[i], duct.path[i + 1],
                                   -duct.width_m / 2, duct.width_m / 2)
            b.add(Polyline(points=tuple(_in(p) for p in outline), layer=layer, closed=True,
                           lineweight=0.35, uid=duct.uid, tag=f"{duct.tag}-seg{i}"))
        mid = duct.path[len(duct.path) // 2]
        label = (f'{duct.width_m / M_PER_IN:.0f}×{duct.depth_m / M_PER_IN:.0f} '
                f'{duct.system.upper()}')
        b.add(Text(anchor=_in((mid[0], mid[1] + duct.width_m / 2 + 0.05)), content=label,
                   height=3.0, layer=layer))
        for x, y in duct.crossings:
            b.add(Leader(
                anchor=NamedPoint(xy=_in((x, y)), name=duct.tag), at=_in((x, y)),
                to=_in((x + 1.0, y + 1.0)),
                text=(f'{duct.width_m / M_PER_IN:.0f}×{duct.depth_m / M_PER_IN:.0f} '
                     f'{duct.system.upper()} IN JOIST BAY — CROSSES BRG WALL BETWEEN '
                     'JOISTS, FIRE BLOCKING REQ\'D'),
                layer=layer,
            ))

    _emit_registers(b, model, storey)
    _emit_equipment(b, model, storey)
    return b.build()


def _emit_registers(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    for element in model.plan.storey_elements(storey):
        if element.element_kind != "Register":
            continue
        layer = _system_layer(element.kind.value)
        b.add(Symbol(name=f"register-{element.kind.value}", insert=_in(element.position.xy_m),
                     layer=layer))


def _emit_equipment(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    for element in model.plan.storey_elements(storey):
        if element.element_kind != "Equipment":
            continue
        width, depth = (dim.meters for dim in element.footprint)
        x, y = element.position.xy_m
        outline = ((x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
                   (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2))
        b.add(Polyline(points=tuple(_in(p) for p in outline), layer="M-HVAC-EQPM",
                       closed=True, lineweight=0.4, uid=element.uid, tag=element.tag))
        b.add(Text(anchor=_in((x, y)), content=element.kind.value.upper(), height=2.5,
                   layer="M-HVAC-EQPM", align="center"))
