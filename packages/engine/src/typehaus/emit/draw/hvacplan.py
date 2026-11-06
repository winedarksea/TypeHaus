"""HVAC plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 3).

One sheet per storey owning duct or floor-heat content. Ducts draw as a double-line plan
rectangle (``rect_between`` — the same wall-band helper the resolver's geometry module
uses); bearing-line crossings are marked and explained once in the sheet notes.

Electric floor heat lives here rather than on the architectural plan. It is mechanical, and
a serpentine sweeping a whole bathroom floor buries the room it is drawn over — see
``_shared.emit_floor_heat``, which this sheet is the intended home for. A storey can own
floor heat and no duct at all, so ``has_hvac_content`` tests both, or the sheet that would
have carried the mat never gets composed.
"""

from __future__ import annotations

import math

from typehaus.emit.draw._shared import emit_floor_heat, emit_ghost_walls
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.annotation_requests import add_point_label
from typehaus.emit.draw.lineweights import FAINT, PROFILE
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.placeables import placed_xy

_SUPPLY_LAYER = "M-HVAC-SDFF"
_RETURN_LAYER = "M-HVAC-RDFF"
_EXHAUST_LAYER = "M-HVAC-EXHS"
_SYSTEM_LAYERS = {"supply": _SUPPLY_LAYER, "return": _RETURN_LAYER, "exhaust": _EXHAUST_LAYER}


def _system_layer(system: str) -> str:
    return _SYSTEM_LAYERS.get(system, _RETURN_LAYER)


def duct_storeys(model: ResolvedModel) -> dict[str, str]:
    """duct uid -> the plan it prints on, where that is not its filing storey (M1-108).

    A duct prints on the storey whose band (its datum up to the next) holds most of its
    horizontal run: the ERV's OA/EA legs and risers are filed on ``main`` and lie in the
    basement ceiling, where they meet the ERV. Vertical legs carry no plan length.
    """
    ladder = sorted(((primary.elevation.meters, primary.tag)
                     for primary, _here in model.plan.levels()))
    out: dict[str, str] = {}
    for duct in model.ducts:
        if len(duct.z_m) != len(duct.path):
            continue
        run: dict[str, float] = {}
        for (a, c), (za, zc) in zip(zip(duct.path, duct.path[1:], strict=False),
                                    zip(duct.z_m, duct.z_m[1:], strict=False), strict=False):
            z = (za + zc) / 2.0
            band = next((tag for elevation, tag in reversed(ladder) if z >= elevation - 1e-6),
                        ladder[0][1] if ladder else duct.storey)
            run[band] = run.get(band, 0.0) + math.dist(a, c)
        if run:
            band = max(run, key=lambda tag: run[tag])
            if band != duct.storey and run[band] > 1e-6:
                out[duct.uid] = band
    return out


def _ducts_on(model: ResolvedModel, storey: str) -> list:
    drawn_on = duct_storeys(model)
    return [duct for duct in model.ducts if drawn_on.get(duct.uid, duct.storey) == storey]


def has_hvac_content(model: ResolvedModel, storey_tag: str) -> bool:
    return (bool(_ducts_on(model, storey_tag))
            or any(zone.storey == storey_tag for zone in model.floor_heat))


def duct_label(duct) -> str:
    """``6" RD SUPPLY``; a wrapped round adds the OD it occupies (M1-002: 8" read as 8")."""
    size = (f'{duct.diameter_m / M_PER_IN:.0f}" RD' if duct.diameter_m is not None
            else f'{duct.width_m / M_PER_IN:.0f}×{duct.depth_m / M_PER_IN:.0f}')
    text = f'{size} {duct.system.replace("_", " ").upper()}'
    wrap = _wrap_m(duct)
    if wrap:
        text += (f', {wrap / M_PER_IN:g}" WRAP = '
                 f'{(duct.diameter_m + 2 * wrap) / M_PER_IN:g}" OD')
    return text


def _wrap_m(duct) -> float | None:
    """The wrap thickness ``duct.insulation`` states, on a round duct only."""
    from typehaus.resolve.mep_envelopes import insulation_thickness_m

    if duct.diameter_m is None or not duct.insulation:
        return None
    return insulation_thickness_m(duct.insulation) or None


def build_hvac_plan(model: ResolvedModel, storey: str) -> Scene:
    b = SceneBuilder(name=f"hvac-{storey}", units="in")
    emit_ghost_walls(b, model, storey)

    ducts = _ducts_on(model, storey)
    occupied_floors = {duct.floor_ref for duct in ducts if duct.floor_ref is not None}
    for floor in model.floors:
        if floor.tag in occupied_floors:
            for member in floor.members:
                b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-FRAM",
                               lineweight=FAINT, uid=floor.uid, tag=member.child_key))

    for duct in ducts:
        layer = _system_layer(duct.system)
        wrap = _wrap_m(duct)
        for i in range(len(duct.path) - 1):
            outline = rect_between(duct.path[i], duct.path[i + 1],
                                   -duct.width_m / 2, duct.width_m / 2)
            b.add(Polyline(points=tuple(_in(p) for p in outline), layer=layer, closed=True,
                           lineweight=PROFILE, uid=duct.uid, tag=f"{duct.tag}-seg{i}"))
            if wrap:  # the wrap's outside face, light: what the run occupies
                half = duct.width_m / 2 + wrap
                outline = rect_between(duct.path[i], duct.path[i + 1], -half, half)
                b.add(Polyline(points=tuple(_in(p) for p in outline), layer=layer,
                               closed=True, lineweight=FAINT, linetype="DASHED",
                               uid=duct.uid, tag=f"{duct.tag}-wrap{i}"))
        mid = duct.path[len(duct.path) // 2]
        add_point_label(b, key=f"duct-{duct.uid}", text=duct_label(duct), target=_in(mid),
                        layer=layer, height_pt=TEXT_PT, priority=50, leader=True,
                        preferred_direction=(0.0, 1.0), avoid_obstacles=False)
        for x, y in duct.crossings:
            cx, cy = _in((x, y))
            mark = 1.5
            b.add(Polyline(points=((cx - mark, cy - mark), (cx + mark, cy + mark)),
                           layer=layer, lineweight=PROFILE))
            b.add(Polyline(points=((cx - mark, cy + mark), (cx + mark, cy - mark)),
                           layer=layer, lineweight=PROFILE))

    _emit_registers(b, model, storey)
    _emit_equipment(b, model, storey)
    _emit_erv_ports(b, model, storey)
    emit_floor_heat(b, model, storey)
    scene = b.build()
    if any(duct.crossings for duct in ducts):
        scene = scene.model_copy(update={"notes": (
            "DUCTS IN JOIST BAYS: X marks bearing-wall crossings requiring fire blocking. "
            "Provide fire blocking at every marked crossing.",
            "Duct labels: width × depth in inches (round: diameter, RD) and air system. "
            "Leaders identify the associated duct run.",
        )})
    return scene


def _emit_registers(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    for element in model.plan.storey_elements(storey):
        if element.element_kind != "Register":
            continue
        layer = _system_layer(element.kind.value)
        b.add(Symbol(name=f"register-{element.kind.value}", insert=_in(placed_xy(model, element)),
                     layer=layer))


def _emit_equipment(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    canvas = {obj.uid: obj for obj in model.canvas_objects}
    for element in model.plan.storey_elements(storey):
        if element.element_kind != "Equipment":
            continue
        width, depth = (dim.meters for dim in element.footprint)
        x, y = placed_xy(model, element)
        # The resolved ring carries the rotation (M2-103: the N-S HW header drew E-W).
        placed = canvas.get(element.uid)
        outline = (tuple(placed.footprint) if placed is not None and placed.footprint else
                   ((x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
                    (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2)))
        b.add(Polyline(points=tuple(_in(p) for p in outline), layer="M-HVAC-EQPM",
                       closed=True, lineweight=PROFILE, uid=element.uid, tag=element.tag))
        # Placed at frame time with the duct labels: at the mech room the plenums, ERV
        # and water heater stand inches apart (C7-E8, M1-009).
        # A plenum prints its tag: "DUCT MANIFOLD" six times says nothing (M1-009).
        text = (element.tag if element.kind.value == "duct_manifold"
                else element.kind.value.replace("_", " ").upper())
        add_point_label(b, key=f"equipment-{element.uid}", text=text,
                        target=_in((x, y)), layer="M-HVAC-EQPM", height_pt=TEXT_PT,
                        priority=60, leader=True, avoid_obstacles=False)


def _emit_erv_ports(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Tag each air port of an ERV by the product's own port tag and section (M1-009)."""
    from typehaus.resolve.mep_ports import placed_ports

    ervs = {element.tag for element in model.plan.storey_elements(storey)
            if element.element_kind == "Equipment" and element.kind.value == "erv"}
    for port in placed_ports(model):
        if port.equipment_tag not in ervs or port.duct_system is None:
            continue
        size = ("" if port.section_m is None
                else f' {port.section_m[0] / M_PER_IN:g}" RD' if
                abs(port.section_m[0] - port.section_m[1]) < 1e-9
                else f" {port.section_m[0] / M_PER_IN:g}x{port.section_m[1] / M_PER_IN:g}")
        add_point_label(b, key=f"port-{port.equipment_tag}-{port.port_tag}",
                        text=f"{port.port_tag.upper()}{size}", target=_in((port.x_m, port.y_m)),
                        layer="M-HVAC-EQPM", height_pt=TEXT_PT, priority=55, leader=True,
                        avoid_obstacles=False)
