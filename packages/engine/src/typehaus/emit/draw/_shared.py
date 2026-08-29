"""Shared plan-view helpers reused by floorplan/foundationplan/framingplan (→ 20).

Extracted from floorplan.py so the wall-emission and bbox-dimension-chain logic has one
authoritative implementation (the plan-view builders are otherwise a family, not one file
per → 20's original scope).
"""

from __future__ import annotations

from typehaus.emit.draw.annotate import DODGE_GAP_PT, LabelSpec, PlacedLabel, dodge, label_box
from typehaus.emit.draw.annotate import model_in_per_pt as annotate_model_in_per_pt
from typehaus.emit.draw.scene import (
    ArchDimension,
    FaceAnchor,
    Hatch,
    NamedPoint,
    Polyline,
    SceneBuilder,
    Text,
)
from typehaus.emit.draw.typography import DIM_TEXT_PT, LINE_SPACING, TEXT_PT
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import place_local
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.model import ResolvedModel, ResolvedWall

#: The scale a plan's annotation *reserves room at*, in ``typography``'s paper-inches-per-
#: model-foot form. Lettering is a printed size, so the model-space room a label needs is a
#: function of the scale the sheet ends up at — and a plan builder runs long before a sheet
#: is chosen (``render.py`` never chooses one at all, and ``sheet_writer.select_scale`` only
#: decides once the scene it is fitting already exists).
#:
#: 3/16" = 1'-0" is what a whole-storey plan of this house actually lands on: ``select_scale``
#: gives catlin's second storey exactly that on a ledger and its main storey 1/8", and the
#: frameless ``haus render`` raster fits the same drawing at an effective 3/16". Reserving
#: here is what makes a room block trim itself rather than run through two partitions, and
#: what makes a crowded dimension string step out onto its own tier — both of which fail
#: *toward* legibility when the sheet turns out bigger than this, and neither of which the
#: frameless ``annotate.LEGACY_IN_PER_PT`` convention (a 4x under-reservation at plan scale)
#: could ever trigger.
PLAN_RESERVATION_SCALE = 0.1875

#: Rows a staggered dimension string may use before it starts reusing them. Three is what
#: catlin's basement plan needs — its bbox spans the house, the freestanding garage and the
#: sunken garden, and the run of short segments where the three meet does not clear on two.
#: It also sets the vertical air a caller has to leave between two dimension tiers: three
#: rows is about 20 model inches at ``PLAN_RESERVATION_SCALE``.
STAGGER_ROWS = 3

#: Wall layer functions that make up the face a builder pulls a tape to. Cladding, furring
#: and finish stand outboard of it and move whenever the rainscreen does (catlin's face has
#: moved three times in a month); the sheathing plane is the one the house is dimensioned
#: from (houses/catlin/CLAUDE.md, "36'x36' at sheathing").
DIMENSION_FACE_FUNCTIONS = frozenset({"structure", "sheathing"})

# How far below a symbol's footprint its tag sits, so the label never covers the glyph.
_LABEL_GAP_M = 0.08

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
    return (p[0] / M_PER_IN, p[1] / M_PER_IN)


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


def emit_ghost_walls(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw a storey's walls as background context on a trade plan.

    Every MEP sheet opens the same way: the walls are there so the reader can locate a
    device, not to be read as architecture, so they print thin, unhatched and unframed on
    the below-line layer. Five plan builders spelled this loop out identically, which is
    how the line weight drifted between them.
    """
    for wall in model.walls:
        if wall.storey == storey:
            emit_wall(b, wall, layer_override="A-WALL-BELW", weight_override=0.15,
                      hatch=False, members=False)


def emit_fixtures(b: SceneBuilder, model: ResolvedModel, storey: str,
                  domains: frozenset[str] | None = None, *, labels: bool = True) -> None:
    """Draw resolved placeable polygons when detailed SVG cannot safely enter technical output.

    The drawing IR deliberately stays vector-primitive-only.  Using resolver geometry keeps
    rotation, wall attachment, custom footprint shapes, and imported products consistent
    with canvas/IFC without attempting to embed arbitrary third-party SVG into PDF or DXF.

    A type that names a ``plan_symbol`` also contributes its generated glyph, transformed by
    the same ``place_local`` every other consumer uses: the resolved footprint stays the heavy
    outline and the glyph is drawn lighter inside it.  Fills are ignored here — that is the
    one thing the technical output does not take from the symbol — and the label moves below
    the object now that the glyph, not the text, carries the meaning.  Everything arrives as
    plain polylines, so the PDF and DXF writers need no new branch.

    ``labels=False`` draws the glyph and drops the caption. A trade plan wants the caption —
    a plumber reading P-101 needs to know which of two identical rectangles is the lav — but
    the architectural plan does not. Every fixture and appliance is a row on the A-601
    schedule already, and the furniture that is not is furniture: a dining table reads as a
    dining table from its glyph, and ``FURN-DINING-8-CHAIR`` printed under each of eight of
    them is a field of type refs over the room plan rather than an annotation of it.
    """
    layers = {"furniture": "A-FURN", "plumbing": "A-FIXT", "appliance": "A-FIXT",
              "mechanical": "M-EQPT", "electrical": "E-POWR"}
    symbols = {item["tag"]: item.get("plan_strokes", ())
               for item in canvas_object_types(model.plan)}
    for item in model.canvas_objects:
        if item.storey != storey or (domains is not None and item.domain not in domains):
            continue
        if len(item.footprint) < 3:
            continue
        layer = layers.get(item.domain, "A-FIXT")
        b.add(Polyline(points=tuple(to_in(point) for point in item.footprint),
                       layer=layer, closed=True, lineweight=0.25,
                       uid=item.uid, tag=item.tag))
        strokes = symbols.get(item.type_ref or "", ())
        for stroke in strokes:
            placed = place_local(stroke["points"], item.position, item.rotation_degrees)
            b.add(Polyline(points=tuple(to_in(point) for point in placed), layer=layer,
                           closed=stroke["closed"], lineweight=stroke["weight"],
                           uid=item.uid, tag=item.tag))
        if not labels:
            continue
        label_y = min(point[1] for point in item.footprint) - _LABEL_GAP_M
        b.add(Text(anchor=to_in((item.position[0], label_y)) if strokes else to_in(item.position),
                   content=item.type_ref or item.tag, height_pt=DIM_TEXT_PT,
                   layer="A-ANNO-TEXT", align="center"))


def emit_floor_heat(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw a serpentine guide from the resolved zone, not a generic fixture icon.

    Lived on the architectural floor plan until it was moved here: an electric floor-heat
    mat is *mechanical*, and a serpentine that sweeps a whole bathroom floor buries the room
    it is drawn over. It has no home yet — ``hvacplan.build_hvac_plan`` is where it belongs
    and should call this — so it is a reusable function rather than a deletion. Nothing in
    the drawing set draws floor heat while that adoption is outstanding.
    """
    for zone in (item for item in model.floor_heat if item.storey == storey):
        xs, ys = [point[0] for point in zone.zone], [point[1] for point in zone.zone]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        lines = max(1, int((maxy - miny) / zone.spacing_m))
        points: list[tuple[float, float]] = []
        for index in range(lines + 1):
            y = min(maxy, miny + index * zone.spacing_m)
            points.extend(((minx, y), (maxx, y)) if index % 2 == 0 else ((maxx, y), (minx, y)))
        b.add(Polyline(points=tuple(to_in(point) for point in points), layer="A-FLR-HEAT",
                       lineweight=0.25, uid=zone.uid, tag=zone.tag))
        b.add(Text(anchor=to_in(((minx + maxx) / 2, (miny + maxy) / 2)),
                   content=f"{zone.tag} {zone.wire_length_m / 0.3048:.0f} LF",
                   height_pt=TEXT_PT, layer="A-ANNO-TEXT", align="center"))


def wall_face_bounds(walls: list[ResolvedWall]) -> tuple[float, float, float, float] | None:
    """``(minx, maxx, miny, maxy)`` of the walls' **sheathing faces**, meters.

    A builder pulls a tape to a face, not to a centreline, so an overall dimension struck
    off the wall axis is short by half a wall at each end — 6.77" across catlin's 36'-0".
    Falls back to the axis bbox for a wall with no resolved layer polygon at all (a plan
    that has not been framed), because half a wall is still better than no dimension.
    """
    xs: list[float] = []
    ys: list[float] = []
    for wall in walls:
        for layer in wall.layers:
            if layer.function not in DIMENSION_FACE_FUNCTIONS or len(layer.polygon) < 3:
                continue
            xs.extend(point[0] for point in layer.polygon)
            ys.extend(point[1] for point in layer.polygon)
    if not xs:
        xs = [p[0] for w in walls for p in (w.axis[0], w.axis[1])]
        ys = [p[1] for w in walls for p in (w.axis[0], w.axis[1])]
    if not xs:
        return None
    return min(xs), max(xs), min(ys), max(ys)


def dimension_offsets(spans: list[float], labels: list[str], base_offset: float,
                      height_pt: float = DIM_TEXT_PT,
                      scale: float = PLAN_RESERVATION_SCALE) -> list[float]:
    """Per-segment dimension-line offsets, staggered onto outer tiers where text collides.

    The writers centre a dimension string on the segment it measures, so a 6" segment in a
    chain is handed a 4'-3 1/2"-wide string and prints it straight through both neighbours —
    which is the overprinted mush the plan's two exterior tiers show today. The IR cannot
    move a string off its own dimension line, so the only lever left here is the *tier*: a
    segment too short to hold its own label steps out onto a second line, which is the
    staggered dimension string every hand-drafted plan uses for the same reason.

    Placement runs through ``annotate.dodge`` in a local (along-chain, outward) frame — the
    same one-pass, deterministic resolver the detail path uses — so the plan and the details
    settle collisions the same way instead of each growing its own. Returns offsets with
    ``base_offset``'s sign; ``spans`` are segment lengths and ``labels`` their strings, both
    in the chain's own order.

    ``dodge`` CASCADES and a dimension chain cannot afford to: it pushes each colliding box
    below every box already settled, so a run of six 6" segments marches six rows out and
    the tier below it has to be moved to make room for a chain that may or may not use it.
    The settled rows are therefore folded back onto ``STAGGER_ROWS`` lines — the ordinary
    staggered dimension string — which bounds the tier's depth and still separates every
    pair ``dodge`` found touching, because a segment three rows down the cascade is far
    enough along the chain that it never overlapped the one three rows above it.
    """
    sign = -1.0 if base_offset < 0 else 1.0
    magnitude = abs(base_offset)
    per_pt = annotate_model_in_per_pt(scale)
    row_pitch = (height_pt * LINE_SPACING + DODGE_GAP_PT) * per_pt
    placed: list[PlacedLabel] = []
    along = 0.0
    for span, label in zip(spans, labels, strict=True):
        # ``z`` runs INWARD in this frame, so ``dodge``'s downward push is outward on paper.
        at = (along + span / 2.0, 0.0)
        placed.append(PlacedLabel(spec=LabelSpec(text=label), at=at, align="center",
                                  height_pt=height_pt,
                                  box=label_box(at, label, height_pt, "center", scale)))
        along += span
    settled = dodge(placed, scale=scale)
    rows = [round(-item.at[1] / row_pitch) % STAGGER_ROWS for item in settled]
    return [sign * (magnitude + row * row_pitch) for row in rows]


def emit_bbox_dimension_chain(b: SceneBuilder, walls: list[ResolvedWall],
                              offset: float = -18.0, *,
                              reference: str = "axis") -> None:
    """Overall bounding-box dimension chain below the plan (auto-dimensioner v1).

    ``reference="face"`` measures the sheathing faces (:func:`wall_face_bounds`) instead of
    the wall axes — what the architectural plan wants, and what a framer can actually pull.
    The default stays ``"axis"`` because the structural plans (S-100/S-101) call this with a
    *bearing-wall* subset whose members are drawn on their centrelines: a face bbox there
    would dimension to a face nothing on that sheet draws.
    """
    pts = [p for w in walls for p in (w.axis[0], w.axis[1])]
    if not pts:
        return
    if reference == "face":
        bounds = wall_face_bounds(walls)
        if bounds is None:
            return
        minx, maxx, miny, maxy = bounds
        xs, ys = [minx, maxx], [miny, maxy]
    else:
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


def _dimension_label(span_in: float) -> str:
    """The string a writer will print for a span — what :func:`dimension_offsets` reserves.

    Mirrors ``pdf_writer._feet_inches``. Duplicated rather than imported: this module is a
    *scene builder* and must not depend on either writer, and what matters for reservation
    is the character count, which both writers agree on.
    """
    total = round(span_in)
    return f"{total // 12}'-{total % 12}\""


# Perpendicular walls / openings within this distance of a facade line count as *on* it.
_FACADE_TOL_M = 0.02
# Stations closer together than this collapse into one (degenerate segments read as noise).
_MIN_STATION_GAP_IN = 1.0


def _facade_stations(walls: list[ResolvedWall], model: ResolvedModel,
                     along: int, perp: int, coord: float,
                     lo: float, hi: float) -> list[float]:
    """Sorted, deduped station list (meters, along-axis) for one facade line.

    Stations: the two facade corners, every wall axis endpoint touching the facade line
    (a perpendicular exterior wall or a partition dying into the facade), and the
    centerline of every opening hosted in a wall that *lies on* the facade.
    """
    stations = [lo, hi]
    facade_wall_tags: set[str] = set()
    for w in walls:
        on0 = abs(w.axis[0][perp] - coord) <= _FACADE_TOL_M
        on1 = abs(w.axis[1][perp] - coord) <= _FACADE_TOL_M
        if on0 and on1:
            facade_wall_tags.add(w.tag)
            continue
        for touching, p in ((on0, w.axis[0]), (on1, w.axis[1])):
            if touching:
                stations.append(p[along])
    for op in model.openings:
        if op.host_wall not in facade_wall_tags:
            continue
        wall = model.wall(op.host_wall)
        if wall is None:
            continue
        center = opening_center(wall, op) or wall.axis[0]
        stations.append(center[along])
    stations.sort()
    min_gap_m = _MIN_STATION_GAP_IN * M_PER_IN
    deduped: list[float] = []
    for s in stations:
        if s < lo - _FACADE_TOL_M or s > hi + _FACADE_TOL_M:
            continue
        if deduped and s - deduped[-1] < min_gap_m:
            continue
        deduped.append(s)
    # Snap the last kept station onto the far corner so the chain always closes the
    # overall extent (a station within the gap of ``hi`` would otherwise swallow it).
    if deduped:
        deduped[0] = lo  # a touch-tolerance hit just outside the corner snaps onto it
        if abs(deduped[-1] - hi) > _FACADE_TOL_M:
            deduped.append(hi)
        else:
            deduped[-1] = hi
    return deduped


def emit_facade_dimension_strings(b: SceneBuilder, model: ResolvedModel,
                                  walls: list[ResolvedWall],
                                  offset: float = 14.0) -> None:
    """Per-facade second-tier dimension strings (auto-dimensioner v2).

    For each of the four facades (outer edges of the wall-axis bbox) emit a cumulative
    chain of ``ArchDimension`` segments between wall intersections and opening
    centerlines on that facade. The chain sits ``offset`` inches outside the facade —
    inside the overall bbox chain, which the caller stacks further out. A facade with
    no interior stations contributes nothing (the overall chain already covers it).

    The chain LINE stands on the sheathing face and its two end stations are the face
    corners (:func:`wall_face_bounds`), so it closes the same extent the overall chain
    states; the stations between them stay axis measurements, because an opening's
    centreline and a partition's centreline *are* centrelines and dimensioning them to a
    face would be a different number, not a better one. Crowded strings stagger onto an
    outer tier through :func:`dimension_offsets` rather than printing through each other.
    """
    pts = [p for w in walls for p in (w.axis[0], w.axis[1])]
    if not pts:
        return
    axis_xs = [p[0] for p in pts]
    axis_ys = [p[1] for p in pts]
    face = wall_face_bounds(walls)
    if face is None:
        return
    face_minx, face_maxx, face_miny, face_maxy = face
    minx, maxx, miny, maxy = min(axis_xs), max(axis_xs), min(axis_ys), max(axis_ys)
    # (name, along-axis index, perp-axis index, facade coordinate, lo, hi, offset sign)
    facades = (
        ("S", 0, 1, face_miny, face_minx, face_maxx, -1.0),
        ("N", 0, 1, face_maxy, face_minx, face_maxx, 1.0),
        ("W", 1, 0, face_minx, face_miny, face_maxy, -1.0),
        ("E", 1, 0, face_maxx, face_miny, face_maxy, 1.0),
    )
    # The stations are generated against the AXIS extent and only their two ends are then
    # moved out onto the face. Generating them against the face extent instead would leave
    # each corner wall's own axis endpoint standing 3 3/8" inside the face corner — a
    # half-wall sliver segment at both ends of all four chains, which is noise, not a
    # dimension.
    axis_extent = {"S": (miny, minx, maxx), "N": (maxy, minx, maxx),
                   "W": (minx, miny, maxy), "E": (maxx, miny, maxy)}
    for name, along, perp, coord, lo, hi, sign in facades:
        axis_coord, axis_lo, axis_hi = axis_extent[name]
        stations = _facade_stations(walls, model, along, perp, axis_coord, axis_lo, axis_hi)
        if len(stations) <= 2:
            continue  # only the corners — the overall chain already says this
        stations[0], stations[-1] = lo, hi
        spans = [(stations[i + 1] - stations[i]) / M_PER_IN
                 for i in range(len(stations) - 1)]
        offsets = dimension_offsets(spans, [_dimension_label(span) for span in spans],
                                    sign * offset)
        for index in range(len(stations) - 1):
            s0, s1 = stations[index], stations[index + 1]
            if along == 0:
                p0, p1 = (s0, coord), (s1, coord)
            else:
                p0, p1 = (coord, s0), (coord, s1)
            b.add(ArchDimension(
                kind="linear",
                ends=(NamedPoint(xy=to_in(p0), name=f"{name}{index}"),
                      NamedPoint(xy=to_in(p1), name=f"{name}{index + 1}")),
                p0=to_in(p0), p1=to_in(p1), offset=offsets[index],
            ))
