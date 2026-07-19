"""Foundation plan → drawing IR (→ 20 §Drawing IR, Permit-ready plan set Phase 1).

Draws the storey holding the foundation walls/footings/pads/slab (the deck-below storey,
e.g. catlin's ``basement``) — never a re-render of the storey above it. Every geometric
input (wall layers, footing/pad/slab outlines, post positions) already exists in the
``ResolvedModel``; this builder only projects it into 2D IR (→ 20 "the UI never re-measures").
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_bbox_dimension_chain, emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.plumbingplan import storey_above
from typehaus.emit.draw.scene import (
    ArchDimension,
    FaceAnchor,
    Leader,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.resolve.model import ResolvedModel, ResolvedWall


def has_foundation_content(model: ResolvedModel) -> bool:
    """Whether S-100 has anything real to show (starter has none — sheet omitted)."""
    return (
        any(wall.is_foundation for wall in model.walls)
        or any(solid.category in {"footing", "pad", "slab"} for solid in model.solids)
    )


def _foundation_storey(model: ResolvedModel) -> str | None:
    storeys = {wall.storey for wall in model.walls if wall.is_foundation}
    if not storeys:
        return None
    elevation = {s.tag: s.elevation.meters for s in model.plan.storeys}
    return min(storeys, key=lambda tag: elevation.get(tag, 0.0))


def build_foundation_plan(model: ResolvedModel) -> Scene:
    """Build the foundation-plan IR scene: the lowest storey carrying foundation content."""
    b = SceneBuilder(name="foundation-plan", units="in")
    storey = _foundation_storey(model)
    walls = [w for w in model.walls if w.is_foundation and w.storey == storey] if storey else []

    for wall in walls:
        emit_wall(b, wall, layer_override="S-FNDN")
    _emit_footings_and_pads(b, model, storey)
    _emit_slabs(b, model, storey)
    _emit_posts(b, model, storey)
    _emit_elevation_notes(b, walls)
    _emit_sleeve_pour_dimensions(b, model, walls, storey)
    if walls:
        emit_bbox_dimension_chain(b, walls)
    return b.build()


def _emit_sleeve_pour_dimensions(b: SceneBuilder, model: ResolvedModel,
                                 walls: list[ResolvedWall], storey: str | None) -> None:
    """Dimension each sleeve above from the nearest two perpendicular foundation-wall
    faces — the pour layout the concrete crew works from (Phase 2 hook)."""
    if storey is None:
        return
    above = storey_above(model, storey)
    sleeves = [s for s in model.sleeves if s.storey == above]
    if not sleeves or not walls:
        return
    horizontal = [w for w in walls if _is_horizontal(w)]
    vertical = [w for w in walls if not _is_horizontal(w)]
    for sleeve in sleeves:
        cx, cy = sleeve.center
        nearest_h = min(horizontal, key=lambda w: abs(_axis_y(w) - cy), default=None)
        nearest_v = min(vertical, key=lambda w: abs(_axis_x(w) - cx), default=None)
        if nearest_h is not None:
            wy = _axis_y(nearest_h)
            b.add(ArchDimension(
                kind="linear",
                ends=(FaceAnchor(uid=nearest_h.uid, face_role="start"),
                      NamedPoint(xy=_in((cx, cy)), name=sleeve.tag)),
                p0=_in((cx, wy)), p1=_in((cx, cy)), offset=6.0,
            ))
        if nearest_v is not None:
            wx = _axis_x(nearest_v)
            b.add(ArchDimension(
                kind="linear",
                ends=(FaceAnchor(uid=nearest_v.uid, face_role="start"),
                      NamedPoint(xy=_in((cx, cy)), name=sleeve.tag)),
                p0=_in((wx, cy)), p1=_in((cx, cy)), offset=6.0,
            ))


def _is_horizontal(wall: ResolvedWall) -> bool:
    (x0, y0), (x1, y1) = wall.axis
    return abs(y1 - y0) < abs(x1 - x0)


def _axis_y(wall: ResolvedWall) -> float:
    return (wall.axis[0][1] + wall.axis[1][1]) / 2.0


def _axis_x(wall: ResolvedWall) -> float:
    return (wall.axis[0][0] + wall.axis[1][0]) / 2.0


def _emit_footings_and_pads(b: SceneBuilder, model: ResolvedModel, storey: str | None) -> None:
    footings = {el.tag: el for el in (model.plan.storey_elements(storey) if storey else ())
                if el.element_kind == "Footing"}
    seen_sizes: set[tuple[float, float]] = set()
    for solid in model.solids:
        if solid.category not in {"footing", "pad"} or solid.storey != storey:
            continue
        b.add(Polyline(
            points=tuple(_in(p) for p in solid.outline), layer="S-FNDN-FTNG",
            closed=True, lineweight=0.25, linetype="HIDDEN2",
            uid=solid.uid, tag=solid.tag,
        ))
        footing = footings.get(solid.tag)
        if footing is None:
            continue  # isolated pads: outline alone is the pour layout
        size = (footing.width.inches, footing.depth.inches)
        key = (round(size[0], 1), round(size[1], 1))
        if key in seen_sizes:
            continue
        seen_sizes.add(key)
        cx, cy = _outline_center(solid.outline)
        b.add(Leader(
            anchor=NamedPoint(xy=_in((cx, cy)), name=solid.tag),
            at=_in((cx, cy)), to=_in((cx, cy - 1.0)),
            text=f"{size[0]:.0f}\" × {size[1]:.0f}\" CONT. FTG.", layer="S-FNDN-FTNG",
        ))


def _emit_slabs(b: SceneBuilder, model: ResolvedModel, storey: str | None) -> None:
    for solid in model.solids:
        if solid.category != "slab" or solid.storey != storey:
            continue
        b.add(Polyline(
            points=tuple(_in(p) for p in solid.outline), layer="A-SLAB",
            closed=True, lineweight=0.3, uid=solid.uid, tag=solid.tag,
        ))
        cx, cy = _outline_center(solid.outline)
        thickness_in = (solid.z1_m - solid.z0_m) * 39.37007874015748
        b.add(Text(anchor=_in((cx, cy)), content=f"{solid.tag} — {thickness_in:.1f}\" CONC. SLAB",
                   height=3.0, layer="A-SLAB", align="center"))


def _emit_posts(b: SceneBuilder, model: ResolvedModel, storey: str | None) -> None:
    for element in model.plan.storey_elements(storey) if storey else ():
        if element.element_kind == "Post":
            x, y = element.position.xy_m
            half = 0.5 * 0.0254  # nominal ~6x6 post half-width placeholder in meters
            outline = ((x - half, y - half), (x + half, y - half),
                       (x + half, y + half), (x - half, y + half))
            b.add(Polyline(points=tuple(_in(p) for p in outline), layer="S-COLS",
                           closed=True, lineweight=0.4, uid=element.uid, tag=element.tag))
            b.add(Symbol(name="post", insert=_in((x, y)), layer="S-COLS"))
        elif element.element_kind == "Beam":
            wall_nodes = {n.tag: n for n in model.plan.storey_elements(storey)
                         if n.element_kind == "Node"}
            start, end = wall_nodes.get(element.start_node), wall_nodes.get(element.end_node)
            if start is None or end is None:
                continue
            b.add(Polyline(points=(_in(start.position.xy_m), _in(end.position.xy_m)),
                           layer="S-BEAM", lineweight=0.5, uid=element.uid, tag=element.tag))


def _emit_elevation_notes(b: SceneBuilder, walls: list) -> None:
    for wall in walls:
        top_ft = wall.z1_m * 3.280839895
        cx, cy = _outline_center([wall.axis[0], wall.axis[1]])
        b.add(Text(anchor=_in((cx, cy + 0.15)), content=f"T.O. WALL EL. {top_ft:.2f}'",
                   height=2.0, layer="A-ANNO-TEXT", align="center"))
    if walls:
        b.add(Text(anchor=_in((walls[0].axis[0][0], walls[0].axis[0][1] - 0.6)),
                   content="FROST DEPTH: 42\" MIN BELOW GRADE (MN 2024 RES CODE)",
                   height=2.5, layer="A-ANNO-TEXT"))


def _outline_center(outline) -> tuple[float, float]:
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return sum(xs) / len(xs), sum(ys) / len(ys)
