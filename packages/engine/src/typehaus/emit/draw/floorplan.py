"""Floorplan slice → drawing IR (→ 20 §Drawing IR, → 11b §Slices).

Every 2D view is a ``Slice``; a floorplan is the auto-scaffolded plan slice cut 4' above a
storey floor. This builder projects the *resolved* geometry — per-layer wall polygons, real
framing member sections, insulation hatch, openings, room labels — into the pure-data 2D IR.
It never redraws from scalar specs (the old failure mode) and never re-measures: all numbers
come from the ``ResolvedModel`` (→ 20 "the UI never re-measures" rule, applied engine-side).
"""

from __future__ import annotations

from typehaus.emit.draw.scene import (
    ArchDimension,
    FaceAnchor,
    Hatch,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.resolve.model import ResolvedModel, ResolvedWall

M_TO_IN = 39.37007874015748

# AIA CAD Layer Guidelines mapping per assembly-layer function (→ 20 §DXF conventions).
_FUNCTION_LAYER = {
    "structure": "A-WALL",
    "sheathing": "A-WALL",
    "cladding": "A-WALL",
    "finish": "A-WALL-FINI",
    "insulation": "A-WALL-INSU",
    "membrane": "A-WALL-PATT",
    "airgap": "A-WALL-PATT",
    "furring": "A-WALL",
}
_HATCH_PATTERN = {
    "insulation": "batt",
    "sheathing": "osb",
    "structure": "lumber",
}


def _in(p: tuple[float, float]) -> tuple[float, float]:
    return (p[0] * M_TO_IN, p[1] * M_TO_IN)


def build_floorplan(model: ResolvedModel, storey: str) -> Scene:
    """Build the plan-slice IR scene for one storey tag."""
    b = SceneBuilder(name=f"plan-{storey}", units="in")
    walls = [w for w in model.walls if w.storey == storey]

    for wall in walls:
        _emit_wall(b, wall)
    _emit_openings(b, model, {w.tag for w in walls})
    _emit_rooms(b, model, storey)
    _emit_dimension_chain(b, walls)
    return b.build()


def _emit_wall(b: SceneBuilder, wall: ResolvedWall) -> None:
    for layer in wall.layers:
        if len(layer.polygon) < 2:
            continue
        aia = _FUNCTION_LAYER.get(layer.function, "A-WALL")
        b.add(Polyline(
            points=tuple(_in(p) for p in layer.polygon),
            layer=aia, closed=True, lineweight=0.35 if aia == "A-WALL" else 0.18,
            uid=wall.uid, tag=wall.tag,
        ))
        pattern = _HATCH_PATTERN.get(layer.function)
        if pattern is not None and len(layer.polygon) >= 3:
            b.add(Hatch(
                boundary=tuple(_in(p) for p in layer.polygon),
                pattern=pattern, layer="A-WALL-PATT",
            ))
    # Real framing member sections on S-FRAM (the signature framed-floorplan look).
    for m in wall.members:
        b.add(Polyline(
            points=(_in(m.p0), _in(m.p1)),
            layer="S-FRAM", lineweight=0.5, uid=wall.uid, tag=m.child_key,
        ))


def _emit_openings(b: SceneBuilder, model: ResolvedModel, wall_tags: set[str]) -> None:
    for op in model.openings:
        if op.host_wall not in wall_tags:
            continue
        wall = model.wall(op.host_wall)
        if wall is None:
            continue
        (sx, sy), (ex, ey) = wall.axis
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
        t = op.center_along_m / length
        cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
        layer = "A-DOOR" if op.is_door else "A-GLAZ"
        b.add(Symbol(
            name="door-swing" if op.is_door else "window-mark",
            insert=_in((cx, cy)),
            rotation=_angle(sx, sy, ex, ey),
            scale=op.width_m * M_TO_IN,
            layer=layer,
            params={"width_in": op.width_m * M_TO_IN},
        ))


def _emit_rooms(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    for room in model.rooms:
        if room.storey != storey or not room.clear_face:
            continue
        cx = sum(p[0] for p in room.clear_face) / len(room.clear_face)
        cy = sum(p[1] for p in room.clear_face) / len(room.clear_face)
        area_sf = room.area_m2 * 10.7639
        b.add(Text(anchor=_in((cx, cy)), content=room.tag, height=4.0,
                   layer="A-AREA-IDEN", align="center"))
        b.add(Text(anchor=_in((cx, cy - 0.3)), content=f"{area_sf:.0f} SF", height=3.0,
                   layer="A-AREA-IDEN", align="center"))


def _emit_dimension_chain(b: SceneBuilder, walls: list[ResolvedWall]) -> None:
    """Overall bounding-box dimension chain below the plan (auto-dimensioner v1)."""
    pts = [p for w in walls for p in (w.axis[0], w.axis[1])]
    if not pts:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx, miny = min(xs), max(xs), min(ys)
    off = -18.0  # 18" below the plan
    b.add(ArchDimension(
        kind="linear",
        ends=(NamedPoint(xy=_in((minx, miny)), name="W"),
              NamedPoint(xy=_in((maxx, miny)), name="E")),
        p0=_in((minx, miny)), p1=_in((maxx, miny)), offset=off,
    ))
    b.add(ArchDimension(
        kind="linear",
        ends=(FaceAnchor(uid=walls[0].uid, face_role="start"),
              NamedPoint(xy=_in((min(xs), max(ys))), name="N")),
        p0=_in((minx, miny)), p1=_in((minx, max(ys))), offset=off,
    ))


def _angle(sx: float, sy: float, ex: float, ey: float) -> float:
    import math

    return math.degrees(math.atan2(ey - sy, ex - sx))
