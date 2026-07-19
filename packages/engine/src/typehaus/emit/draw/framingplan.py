"""Framing plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 1).

The first plan-view joist rendering — until now, framing members only appeared cut in
section (section.py:264). Ghosts the bearing storey's walls below and draws the resolved
joists, span direction, and floor openings for one ``ResolvedFloor``.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_bbox_dimension_chain, emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.model.floors import FloorSystem
from typehaus.resolve.model import ResolvedModel


def build_framing_plan(model: ResolvedModel, floor_tag: str) -> Scene:
    """Build the framing-plan IR scene for the ``ResolvedFloor`` with tag ``floor_tag``."""
    floor = next((f for f in model.floors if f.tag == floor_tag), None)
    b = SceneBuilder(name=f"framing-{floor_tag}", units="in")
    if floor is None:
        return b.build()

    system = model.plan.by_tag(floor_tag)
    if not isinstance(system, FloorSystem):
        return b.build()  # defensive; every ResolvedFloor is sourced from a FloorSystem
    bearing_walls = [w for tag in system.joists.bearing_refs if (w := model.wall(tag)) is not None]
    bearing_storey = bearing_walls[0].storey if bearing_walls else None
    bearing_tags = {w.tag for w in bearing_walls}

    if bearing_storey is not None:
        for wall in model.walls:
            if wall.storey != bearing_storey:
                continue
            if wall.tag in bearing_tags:
                emit_wall(b, wall, layer_override="S-WALL", weight_override=0.5, members=False)
            else:
                emit_wall(b, wall, layer_override="S-WALL-BELW", weight_override=0.13,
                         hatch=False, members=False)

    for member in floor.members:
        b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-FRAM",
                       lineweight=0.4, uid=floor.uid, tag=member.child_key))

    _emit_span_callout(b, model, floor, system)
    _emit_floor_openings(b, model, system)

    if bearing_walls:
        for wall in bearing_walls:
            cx = (wall.axis[0][0] + wall.axis[1][0]) / 2.0
            cy = (wall.axis[0][1] + wall.axis[1][1]) / 2.0
            b.add(Text(anchor=_in((cx, cy + 0.1)), content=f"BRG: {wall.tag}", height=2.0,
                       layer="A-ANNO-TEXT", align="center"))
        emit_bbox_dimension_chain(b, bearing_walls)
    return b.build()


def _emit_span_callout(b: SceneBuilder, model: ResolvedModel, floor, system) -> None:
    if not floor.members:
        return
    xs = [p[0] for m in floor.members for p in (m.p0, m.p1)]
    ys = [p[1] for m in floor.members for p in (m.p0, m.p1)]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    along_x = floor.direction == "x"
    rotation = 0.0 if along_x else 90.0
    b.add(Symbol(name="span-arrow", insert=_in((cx, cy)), rotation=rotation, scale=24.0,
                 layer="S-FRAM"))
    spacing_in = system.joists.spacing.inches if system.joists.spacing is not None else 16.0
    label = f'{system.joists.member.upper()} @ {spacing_in:.0f}" O.C.'
    b.add(Text(anchor=_in((cx, cy + 1.0)), content=label, height=3.0, layer="S-FRAM",
               align="center"))


def _emit_floor_openings(b: SceneBuilder, model: ResolvedModel, system) -> None:
    for tag in system.openings:
        opening = model.plan.by_tag(tag)
        if opening is None or len(opening.outline) < 3:
            continue
        outline = [pt.xy_m for pt in opening.outline]
        b.add(Polyline(points=tuple(_in(p) for p in outline), layer="S-FRAM-OPEN",
                       closed=True, lineweight=0.3, uid=opening.uid, tag=opening.tag))
        cx = sum(p[0] for p in outline) / len(outline)
        cy = sum(p[1] for p in outline) / len(outline)
        b.add(Text(anchor=_in((cx, cy)), content="HEADER/TRIMMER BY SUPPLIER", height=2.0,
                   layer="S-FRAM-OPEN", align="center"))
