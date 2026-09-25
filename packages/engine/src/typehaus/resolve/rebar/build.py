"""``resolve_rebar``: every authored ``ReinforcementSpec`` laid out as pieces (decision #75).

Runs as the ``"rebar"`` pipeline stage, after every host it reads has resolved and before
``"geometry"``. Bars land in ``ResolvedModel.rebar`` and nowhere else — not in any member
list — so framing takeoff, member checks, sections and the geometry IR never see them.

Defaults, where a pour states nothing: cover 1 1/2", f'c 3,000 psi, 40'-0" stock, class B
laps. Walls lay first, then ``junctions.py`` carries their horizontals across each node; mats
lay largest pour first and a later mat stops where an earlier pour's concrete already is, so
an overlap is reinforced (and billed) once. ``integrity.reinforcement_layout`` is where an
unplaceable role is reported.
"""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.model.rebar import BARS
from typehaus.resolve.assembly_material import is_cast_beam
from typehaus.resolve.concrete import concrete_spec_for
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.beams import BEAM_ROLES, frame_of_ring, lay_beam
from typehaus.resolve.rebar.cages import lay_column, lay_dowels
from typehaus.resolve.rebar.junctions import lay_junction_bars
from typehaus.resolve.rebar.mats import lay_mat
from typehaus.resolve.rebar.records import ResolvedRebarSet
from typehaus.resolve.rebar.stock import Sink
from typehaus.resolve.rebar.walls import WallBase, lay_wall, structure_layer, wall_frame
from typehaus.resolve.solid_categories import in_slab_family

_IN = 0.0254
DEFAULT_COVER_IN = 1.5
DEFAULT_FC_PSI = 3000.0
_SOLID_SCOPES = {"footing", "pad", "column", "beam"}


def cover_m(plan, element, spec=None) -> float:
    """The element's cover: its spec's, else its pour's mix, else 1 1/2"."""
    mix = concrete_spec_for(plan, element)
    own = getattr(spec, "cover", None)
    cover_in = (own.inches if own is not None
                else mix.cover.inches if mix is not None and mix.cover is not None
                else DEFAULT_COVER_IN)
    return cover_in * _IN


def _sink(plan, element, spec, *, wall: bool = False) -> tuple[Sink, float]:
    mix = concrete_spec_for(plan, element)
    stock = spec.stock_length.meters if spec.stock_length else det.DEFAULT_STOCK_IN * _IN
    sink = Sink(element.tag, (mix.bar_coating if mix is not None else None) or "",
                mix.fc_psi if mix is not None else DEFAULT_FC_PSI, spec.lap_class, stock,
                wall=wall)
    return sink, cover_m(plan, element, spec)


def resolve_rebar(model) -> list[ResolvedRebarSet]:
    plan = model.plan
    out: list[ResolvedRebarSet] = []
    openings: dict[str, list] = {}
    for o in model.openings:
        openings.setdefault(o.host_wall, []).append(o)

    steel, sinks, laid_walls = {}, {}, []
    for wall in model.walls:
        element = plan.by_tag(wall.tag)
        spec = getattr(element, "reinforcement", None)
        if spec is None or structure_layer(wall) is None:
            continue
        sink, cover = _sink(plan, element, spec, wall=True)
        footing = _footing_under(model, wall)
        base = _base_of(model, footing) if footing is not None else None
        beam = base is None and any(e.role in BEAM_ROLES for e in spec.bars)
        joints = _beam_joints(model, spec, wall, cover) if beam else None
        ends = _beam_row_ends(model, wall, joints) if beam else None
        ws = lay_wall(sink, spec, wall, cover, openings.get(wall.tag, ()), base, ends)
        if base is not None:
            _wall_dowels(sink, spec, wall, base)
        elif joints:
            _beam_end_dowels(sink, spec, wall, cover, joints)
        sinks[wall.tag] = sink
        if ws is not None:
            steel[wall.tag] = ws
        laid_walls.append((wall, element, sink))
    lay_junction_bars(model.junctions, steel, sinks)
    for wall, element, sink in laid_walls:
        out.append(ResolvedRebarSet(wall.uid, wall.tag, element.element_kind, wall.storey,
                                    "foundation wall" if wall.is_foundation else "wall",
                                    tuple(sink.bars)))

    laid_mats: list = []
    # The larger pour keeps an overlap's mat; ties by tag. Columns and beams are unaffected.
    for solid in sorted(model.solids, key=lambda s: (-_plan_area(s.outline), s.tag)):
        if solid.derived or not (solid.category in _SOLID_SCOPES
                                  or in_slab_family(solid.category)):
            continue
        element = plan.by_tag(solid.tag)
        spec = getattr(element, "reinforcement", None) if element is not None else None
        if spec is None:
            continue
        if solid.category == "beam" and not is_cast_beam(plan, element):
            continue
        sink, cover = _sink(plan, element, spec)
        if solid.category == "column":
            feet = lay_column(sink, spec, solid, cover)
            _post_dowels(model, sink, spec, element, feet)
        elif solid.category == "beam":
            lay_beam(sink, spec.bars, frame_of_ring(solid.outline, solid.z0_m, solid.z1_m), cover)
        else:
            earlier = [m.outline for m in laid_mats
                       if m.z0_m < solid.z1_m and solid.z0_m < m.z1_m]
            lay_mat(sink, spec, solid, cover, ey=_strip_axis(model, element),
                    cap_thickness=_cap_thickness(plan, element), earlier=earlier)
            laid_mats.append(solid)
        out.append(ResolvedRebarSet(solid.uid, solid.tag, element.element_kind, solid.storey,
                                    solid.category, tuple(sink.bars)))
    return out


def _strip_axis(model, element) -> tuple[float, float]:
    """A strip footing's ``y``: its wall's axis. Anything else is plan Y."""
    if element.element_kind != "Footing":
        return (0.0, 1.0)
    wall = model.wall(getattr(element, "under", ""))
    if wall is None:
        return (0.0, 1.0)
    (ax, ay), (bx, by) = wall.axis
    d = math.hypot(bx - ax, by - ay) or 1.0
    return ((bx - ax) / d, (by - ay) / d)


def _cap_thickness(plan, element) -> float | None:
    assembly = plan.library.resolve_assembly(getattr(element, "assembly", None) or "")
    if assembly is None:
        return None
    layer = next((ly for ly in assembly.layers if ly.function == LayerFunction.STRUCTURE), None)
    return layer.thickness.meters if layer is not None else None


def _plan_area(ring) -> float:
    pts = list(ring)
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                   for i in range(len(pts)))) / 2.0


def _footing_under(model, wall):
    return next((s for s in model.solids if s.category == "footing" and not s.derived
                 and getattr(model.plan.by_tag(s.tag), "under", None) == wall.tag), None)


def _bottom_mat_m(spec) -> float:
    """How thick the bottom mat stands: what a foot set on it rests on."""
    if spec is None:
        return 0.0
    return sum(BARS[e.bar].diameter_in * _IN * max(1, e.layers) for e in spec.bars
               if e.role.startswith("bottom-") and e.spacing is not None)


def _base_of(model, solid) -> WallBase:
    element = model.plan.by_tag(solid.tag)
    spec = getattr(element, "reinforcement", None)
    return WallBase(solid.z1_m, solid.z0_m + cover_m(model.plan, element, spec)
                    + _bottom_mat_m(spec))


def _anchor(sink: Sink, top: float, points, outline, dirs):
    """``(entry, z_foot, db) -> (embedment, ldh)`` for L dowels at ``points``."""
    def fn(entry, z_foot, db):
        gaps = [math.dist(p, q) for i, p in enumerate(points) for q in points[i + 1:]]
        spaced = not gaps or min(gaps) >= 6 * db
        side_ok = all(_side_cover(p, d, outline) >= 6 * db
                      for p, d in zip(points, dirs, strict=True))
        need = det.hooked_development_in(entry.bar, sink.fc_psi, confined_spacing=spaced,
                                         side_cover_ok=side_ok) * _IN
        return top - (z_foot - db / 2), need
    return fn


def _side_cover(p, d, outline) -> float:
    """Cover normal to a hook's plane: distance to the edge across the foot's direction."""
    if outline is None:
        return math.inf
    from shapely.geometry import LineString, Point, Polygon

    poly = Polygon(outline)
    n = (-d[1], d[0])
    reach = []
    for k in (1.0, -1.0):
        ray = LineString([p, (p[0] + n[0] * k * 50, p[1] + n[1] * k * 50)])
        hit = poly.exterior.intersection(ray)
        reach.append(hit.distance(Point(p)) if not hit.is_empty else 0.0)
    return min(reach)


def _outward_dirs(points, centre, axes, outline, cover: float, leg: float):
    """Each foot turns AWAY from the cage along whichever axis leaves it the most room."""
    from shapely.geometry import LineString, Point, Polygon

    inner = Polygon(outline).buffer(-cover) if outline is not None else None
    dirs = []
    for x, y in points:
        best, best_room = None, -math.inf
        for ax in axes:
            k = 1.0 if (x - centre[0]) * ax[0] + (y - centre[1]) * ax[1] >= 0 else -1.0
            d = (ax[0] * k, ax[1] * k)
            if inner is None or inner.is_empty:
                room = leg
            else:
                ray = LineString([(x, y), (x + d[0] * 50, y + d[1] * 50)])
                hit = inner.exterior.intersection(ray)
                room = hit.distance(Point(x, y)) if not hit.is_empty else 0.0
            if room > best_room + 1e-6:
                best, best_room = d, room
        dirs.append(best)
    return dirs


def _wall_dowels(sink: Sink, spec, wall, base: WallBase) -> None:
    entries = [e for e in spec.bars if e.role == "dowels"]
    vert = next((e for e in spec.bars if e.role == "vertical"), None)
    if not entries or vert is None:
        return
    frame, ext = wall_frame(wall, structure_layer(wall))
    lows = [min(b.path, key=lambda p: p[2]) for b in sink.bars
            if b.role == "vertical" and b.piece == 1]
    if not lows:
        return
    lap_top = min(p[2] for p in lows)
    foot = (-frame.n[0] * ext, -frame.n[1] * ext)
    for entry in entries:
        shift = (BARS[vert.bar].diameter_in + BARS[entry.bar].diameter_in) / 2 * _IN
        pts = [(x + frame.u[0] * shift, y + frame.u[1] * shift) for x, y, _ in lows]
        anchor = _anchor(sink, base.top, pts, None, [foot] * len(pts))
        lay_dowels(sink, entry, pts, base.top, base.rest, lap_top, [foot] * len(pts),
                   anchorage=anchor)


def _beam_z(spec, frame, cover: float) -> tuple[float, float]:
    """``(inner, z)``: the bottom row's inset from the face and its centreline elevation."""
    bottom = next((e for e in spec.bars if e.role == "bottom-y" and e.count), None)
    hoop = next((e for e in spec.bars if e.role in ("ties", "stirrups")), None)
    inner = cover + (BARS[hoop.bar].diameter_in * _IN if hoop else 0.0)
    return inner, frame.z0 + inner + (BARS[bottom.bar].diameter_in * _IN / 2 if bottom else 0.0)


def _beam_joints(model, spec, wall, cover: float):
    """Per end of a wall acting as a beam, ``(joint_s, far_limit_s, inward)`` where its bottom
    row meets a footing poured a placement first, else ``None``. The row stops at that face
    and the footing's ``dowels`` take over (``notes/sunken_garden_veneer_beam.md`` §6e)."""
    if not any(e.role == "dowels" and e.count and e.embedment for e in spec.bars) or not any(
            e.role == "bottom-y" and e.count for e in spec.bars):
        return None
    frame, _ext = wall_frame(wall, structure_layer(wall))
    _inner, z = _beam_z(spec, frame, cover)
    out = []
    for s_end, inward in ((frame.s0 + cover, 1.0), (frame.s1 - cover, -1.0)):
        x, y, _ = frame.world(s_end, (frame.t0 + frame.t1) / 2, z)
        footing = next((s for s in model.solids if s.category == "footing"
                        and not s.derived and s.z0_m <= z <= s.z1_m
                        and _contains(s.outline, x, y)), None)
        if footing is None:
            out.append(None)
            continue
        ss = [(p[0] - frame.origin[0]) * frame.u[0] + (p[1] - frame.origin[1]) * frame.u[1]
              for p in footing.outline]
        joint, far = (max(ss), min(ss)) if inward > 0 else (min(ss), max(ss))
        element = model.plan.by_tag(footing.tag)
        limit = far + inward * cover_m(model.plan, element, getattr(element, "reinforcement", None))
        out.append((joint, limit, inward))
    return tuple(out) if any(out) else None


def _beam_row_ends(model, wall, joints) -> dict:
    """Where a wall-beam's rows stop: ``bottom-y`` at each dowelled cold joint; ``top-y`` in
    the support wall its end frames into, at that wall's far face less its cover — the ℓdh
    ``notes/sunken_garden_veneer_beam.md`` §6e credits (12" − 3" = 9.00")."""
    frame, _ext = wall_frame(wall, structure_layer(wall))
    top: list[float | None] = []
    for s_end, sign in ((frame.s0, -1.0), (frame.s1, 1.0)):
        x, y, _ = frame.world(s_end, (frame.t0 + frame.t1) / 2, frame.z1)
        reach = None
        for other in model.walls:
            layer = structure_layer(other) if other.tag != wall.tag else None
            if layer is None or not (other.z0_m < frame.z1 and frame.z0 < other.z1_m):
                continue
            ring = list(layer.polygon)
            if not _contains(ring, x, y):
                continue
            ss = [(p[0] - frame.origin[0]) * frame.u[0] + (p[1] - frame.origin[1]) * frame.u[1]
                  for p in ring]
            element = model.plan.by_tag(other.tag)
            c = cover_m(model.plan, element, getattr(element, "reinforcement", None))
            reach = (max(ss) - c) if sign > 0 else (min(ss) + c)
            break
        top.append(reach)
    ends = {"top-y": (top[0], top[1])}
    if joints:
        ends["bottom-y"] = tuple(j[0] if j else None for j in joints)
    return ends


def _beam_end_dowels(sink: Sink, spec, wall, cover: float, joints) -> None:
    """Each ``dowels`` bar is cast STRAIGHT in the footing, ``embedment`` back from its span
    face (the cold joint), and projects a class-B lap into the beam. Oracle:
    ``notes/sunken_garden_veneer_beam.md`` §6e."""
    entries = [e for e in spec.bars if e.role == "dowels" and e.count and e.embedment]
    frame, _ext = wall_frame(wall, structure_layer(wall))
    inner, z = _beam_z(spec, frame, cover)
    for entry in entries:
        db = BARS[entry.bar].diameter_in * _IN
        t0, t1 = frame.t0 + inner + db / 2, frame.t1 - inner - db / 2
        ts = ([t0 + (t1 - t0) * i / (entry.count - 1) for i in range(entry.count)]
              if entry.count > 1 else [(t0 + t1) / 2])
        lap = det.tension_lap_in(entry.bar, sink.fc_psi, sink.lap_class) * _IN
        for joint, limit, inward in (j for j in joints if j is not None):
            start = joint - inward * entry.embedment.meters
            start = max(start, limit) if inward > 0 else min(start, limit)
            for t in ts:
                sink.polyline(entry, [frame.world(start, t, z),
                                      frame.world(joint + inward * lap, t, z)],
                              placed_m=abs(joint - start), lap_m=lap, hook_m=0.0,
                              hook_kinds=())


def _contains(outline, x: float, y: float) -> bool:
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    return bool(xs) and min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys)


def _post_dowels(model, sink: Sink, spec, element, feet) -> None:
    entries = [e for e in spec.bars if e.role == "dowels"]
    vert = next((e for e in spec.bars if e.role == "vertical"), None)
    base_tag = getattr(element, "supported_by", None)
    if not entries or not base_tag or not feet or vert is None:
        return
    centre = (sum(f[0] for f in feet) / len(feet), sum(f[1] for f in feet) / len(feet))
    lap_top = min(f[2] for f in feet)
    base = next((s for s in model.solids if s.tag == base_tag and not s.derived), None)
    if base is not None:
        wb = _base_of(model, base)
        base_el = model.plan.by_tag(base_tag)
        cover = cover_m(model.plan, base_el, getattr(base_el, "reinforcement", None))
        outline, axes = list(base.outline), [(1.0, 0.0), (0.0, 1.0)]
    else:
        wall = model.wall(base_tag)
        if wall is None:
            return
        # A column on a wall: the dowel develops straight down from the wall top, then turns
        # along the wall, the only way a 90° leg stays inside its thickness.
        cover = cover_m(model.plan, model.plan.by_tag(base_tag),
                        getattr(model.plan.by_tag(base_tag), "reinforcement", None))
        # An authored `BarSpec.embedment` is the drawing's length; ld is the fallback.
        ld = max(e.embedment.inches if e.embedment is not None
                 else det.development_length_in(e.bar, sink.fc_psi) for e in entries) * _IN
        wb = WallBase(wall.z1_m, max(wall.z0_m + cover, wall.z1_m - ld))
        (ax, ay), (bx, by) = wall.axis
        d = math.hypot(bx - ax, by - ay) or 1.0
        outline, axes = None, [((bx - ax) / d, (by - ay) / d)]
    for entry in entries:
        shift = (BARS[vert.bar].diameter_in + BARS[entry.bar].diameter_in) / 2 * _IN
        pts = []
        for x, y, _ in feet:
            r = math.hypot(x - centre[0], y - centre[1]) or 1.0
            pts.append((x - (x - centre[0]) / r * shift, y - (y - centre[1]) / r * shift))
        galv = sink.galvanized(entry)
        _, bend, ext = det.hook_geometry_in(entry.bar, "std90", galvanized=galv)
        leg = (bend / 2 + BARS[entry.bar].diameter_in + ext) * _IN
        dirs = _outward_dirs(pts, centre, axes, outline, cover, leg)
        lay_dowels(sink, entry, pts, wb.top, wb.rest, lap_top, dirs,
                   anchorage=_anchor(sink, wb.top, pts, outline, dirs))
