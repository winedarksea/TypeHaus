"""Shared plan-view helpers reused by floorplan/foundationplan/framingplan (→ 20).

Extracted from floorplan.py so the wall-emission and bbox-dimension-chain logic has one
authoritative implementation (the plan-view builders are otherwise a family, not one file
per → 20's original scope).
"""

from __future__ import annotations

from typehaus.emit.draw.scene import (
    ArchDimension,
    FaceAnchor,
    Hatch,
    NamedPoint,
    Polyline,
    SceneBuilder,
    Text,
)
from typehaus.resolve.model import ResolvedModel, ResolvedWall

M_TO_IN = 39.37007874015748

# AIA CAD Layer Guidelines mapping per assembly-layer function (→ 20 §DXF conventions).
FUNCTION_LAYER = {
    "structure": "A-WALL",
    "sheathing": "A-WALL",
    "cladding": "A-WALL",
    "finish": "A-WALL-FINI",
    "insulation": "A-WALL-INSU",
    "membrane": "A-WALL-PATT",
    "airgap": "A-WALL-PATT",
    "furring": "A-WALL",
}
HATCH_PATTERN = {
    "insulation": "batt",
    "sheathing": "osb",
    "structure": "lumber",
}


def to_in(p: tuple[float, float]) -> tuple[float, float]:
    return (p[0] * M_TO_IN, p[1] * M_TO_IN)


def emit_wall(
    b: SceneBuilder,
    wall: ResolvedWall,
    *,
    layer_override: str | None = None,
    weight_override: float | None = None,
    hatch: bool = True,
    members: bool = True,
) -> None:
    """Draw one wall's per-layer polygons (+ optional hatch + framing members).

    ``layer_override``/``weight_override`` let framing/foundation plans reuse the same
    per-layer geometry under a different AIA layer (e.g. ``S-WALL-BELW`` ghosting) without
    duplicating the polygon-walk.
    """
    for layer in wall.layers:
        if len(layer.polygon) < 2:
            continue
        aia = layer_override or FUNCTION_LAYER.get(layer.function, "A-WALL")
        weight = weight_override if weight_override is not None else (
            0.35 if aia == "A-WALL" else 0.18
        )
        b.add(Polyline(
            points=tuple(to_in(p) for p in layer.polygon),
            layer=aia, closed=True, lineweight=weight,
            uid=wall.uid, tag=wall.tag,
        ))
        if hatch and layer_override is None:
            pattern = HATCH_PATTERN.get(layer.function)
            if pattern is not None and len(layer.polygon) >= 3:
                b.add(Hatch(
                    boundary=tuple(to_in(p) for p in layer.polygon),
                    pattern=pattern, layer="A-WALL-PATT",
                ))
    if members:
        for m in wall.members:
            b.add(Polyline(
                points=(to_in(m.p0), to_in(m.p1)),
                layer="S-FRAM", lineweight=0.5, uid=wall.uid, tag=m.child_key,
            ))


def emit_fixtures(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw typed fixture footprints; the schedule and service data share type refs."""
    fixture_types = {item.tag: item for item in model.plan.library.fixture_types}
    for fixture in (element for element in model.plan.storey_elements(storey)
                    if element.element_kind == "Fixture"):
        fixture_type = fixture_types.get(fixture.type_ref)
        if fixture_type is None:
            continue
        width, depth = (dimension.meters for dimension in fixture_type.footprint)
        x, y = fixture.position.xy_m
        outline = ((x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
                   (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2))
        b.add(Polyline(points=tuple(to_in(point) for point in outline), layer="A-FIXT",
                       closed=True, lineweight=0.25, uid=fixture.uid, tag=fixture.tag))
        b.add(Text(anchor=to_in((x, y)), content=fixture.type_ref.removeprefix("FX-"),
                   height=2.0, layer="A-ANNO-TEXT", align="center"))


def emit_bbox_dimension_chain(b: SceneBuilder, walls: list[ResolvedWall],
                              offset: float = -18.0) -> None:
    """Overall bounding-box dimension chain below the plan (auto-dimensioner v1)."""
    pts = [p for w in walls for p in (w.axis[0], w.axis[1])]
    if not pts:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx, miny = min(xs), max(xs), min(ys)
    b.add(ArchDimension(
        kind="linear",
        ends=(NamedPoint(xy=to_in((minx, miny)), name="W"),
              NamedPoint(xy=to_in((maxx, miny)), name="E")),
        p0=to_in((minx, miny)), p1=to_in((maxx, miny)), offset=offset,
    ))
    b.add(ArchDimension(
        kind="linear",
        ends=(FaceAnchor(uid=walls[0].uid, face_role="start"),
              NamedPoint(xy=to_in((min(xs), max(ys))), name="N")),
        p0=to_in((minx, miny)), p1=to_in((minx, max(ys))), offset=offset,
    ))
