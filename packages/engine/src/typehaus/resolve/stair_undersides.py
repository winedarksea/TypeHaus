"""A stair's gypsum underside, derived from ``Stair.underside_material`` (late stage).

After rooms and ceilings: a board above the room's finished ceiling is concealed and cut
away, and the coat is the owning room's ceiling coat (``resolve/room_paint.py``), unless
``underside_unpainted``. Each board is a ``stair_soffit`` member on the stair (drawn and
exported like a skirt) and a ``StairUnderside`` record (billed, and read overhead by
``resolve/overhead.py``). Winder turns, box and cast carriages take none. Geometry:
``resolve/stair_underside_boards.py``.
"""

from __future__ import annotations

import math
from dataclasses import replace

from shapely.geometry import Polygon, box

from typehaus.model.assembly import Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Stair
from typehaus.resolve import stair_underside_boards as geo
from typehaus.resolve.coatings import coating_tags
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedStair, StairUnderside
from typehaus.resolve.overlay import intersection, union_all
from typehaus.resolve.room_lookup import room_owning
from typehaus.resolve.room_paint import (
    DEFAULT_PAINT,
    paint_room,
    paint_stack_end,
    paint_standard,
    unroomed_coat,
)
from typehaus.resolve.soffits import wall_footprint

CATEGORY = "stair_soffit"
_IN = 0.0254


def resolve_stair_undersides(plan, model: ResolvedModel) -> None:
    walls = None
    for index, stair in enumerate(model.stairs):
        authored = plan.by_tag(stair.tag)
        if (not isinstance(authored, Stair) or authored.underside_material is None
                or authored.carriage != "stringer"):
            continue
        if walls is None:
            walls = [(wall, wall_footprint(wall)) for wall in model.walls if wall.layers]
        boards = _boards(plan, model, stair, authored, walls)
        material = authored.underside_material
        members = tuple(_member(stair, board, material) for board in boards)
        records = tuple(_record(plan, model, stair, authored, board) for board in boards)
        model.stairs[index] = replace(
            stair, members=(*(m for m in stair.members if m.category != CATEGORY), *members),
            undersides=records)


def _boards(plan, model, stair: ResolvedStair, authored: Stair, walls) -> list[geo.Board]:
    t = authored.underside_thickness.meters
    ceilings = [c for c in model.ceilings if c.storey == stair.storey
                and c.z0_m is not None and len(c.outline) >= 3]
    railings = [el for el in plan.all_elements() if getattr(el, "element_kind", "") == "Railing"
                and getattr(el, "mount", None) == "panel"]
    lands = geo.merged_landings(geo.landings(stair.members))
    out: list[geo.Board] = []
    for flight in geo.flights(stair.members):
        out.extend(_flight_boards(flight, t, walls, ceilings, railings, lands))
    for landing in lands:
        out.extend(_landing_board(landing, t, ceilings))
    out.extend(_steps(lands, t))
    return out


def _flight_boards(flight: geo.Flight, t: float, walls, ceilings, railings,
                   lands: list[geo.Landing]) -> list[geo.Board]:
    frame = flight.frame
    shape, depth, slope = geo.band(flight, t)
    s0, z0, s1, z1 = shape.bounds
    c_lo, c_hi = flight.c_lo, flight.c_hi
    free: dict[int, float] = {}
    for outward, c_face in ((-1, flight.c_lo), (1, flight.c_hi)):
        face = geo.wall_face(walls, frame, c_face, outward, s0, s1, z0, z1)
        if face is None:
            free[outward] = c_face
        elif outward < 0:
            c_lo = face
        else:
            c_hi = face
    footprint = frame.rect(s0, s1, c_lo, c_hi)
    clips = geo.ceiling_clips(ceilings, footprint, frame)
    spans = {side: geo.panel_spans(railings, frame, c) for side, c in free.items()}
    width = c_hi - c_lo
    c_mid = (c_lo + c_hi) / 2.0
    secant = math.sqrt(1.0 + slope * slope)
    (sa, za), _ = flight.rake

    def rake_z(s: float) -> float:
        return za + (s - sa) * slope - depth

    out = []
    for i, part in enumerate(geo.clip(shape, clips)):
        ps0, _, ps1, _ = part.bounds
        raked = part.area / depth * secant
        edges = tuple(e for side, c in free.items()
                      for e in geo.bottom_edges(flight, part, depth, c, spans[side]))
        out.append(_raked(f"soffit-{flight.name}" + (f"-{i}" if i else ""), "flight", frame,
                          part, ps0, ps1, c_mid, width, t, raked * width,
                          (rake_z(ps0), rake_z(ps1)), edges, raked))
    # Plumb returns at each end: onto a landing, or the head cut under the stairhead header.
    for end, (s_e, z_r) in (("foot", flight.rake[0]), ("head", flight.rake[1])):
        reach = frame.rect(s_e - geo.LANDING_MEETS_M, s_e + geo.LANDING_MEETS_M, c_lo, c_hi)
        landing = max((land for land in lands if land.polygon.intersects(reach)),
                      key=lambda land: land.polygon.intersection(reach).area, default=None)
        if landing is not None and abs(landing.underside_m - z_r) > 1e-3:
            lo = min(z_r - depth, landing.underside_m - t)
            hi = max(z_r, landing.underside_m)
            bead = min(z_r - depth, landing.underside_m - t)
        elif landing is None and end == "head" and flight.head_top is not None:
            lo, hi, bead = z_r - depth, flight.head_top, z_r - depth
        else:
            continue
        out.extend(_plumb(f"soffit-{flight.name}-{end}", frame.at(s_e, c_lo),
                          frame.at(s_e, c_hi), lo, hi, bead, t, ceilings))
    # Face boards over an unwalled outer stringer, short of what a panel covers.
    for outward, c_face in free.items():
        face = union_all([Polygon(flight.profile), shape])
        c_board = c_face + outward * t / 2.0
        side = "left" if outward > 0 else "right"
        strip = frame.rect(s0, s1, c_face, c_face + outward * t)
        face_clips = geo.ceiling_clips(ceilings, strip, frame)
        for i, part in enumerate(geo.clip(face, face_clips, spans=spans[outward])):
            ps0, _, ps1, _ = part.bounds
            out.append(_raked(f"soffit-{flight.name}-face-{side}" + (f"-{i}" if i else ""),
                              "face", frame, part, ps0, ps1, c_board, t, part.bounds[3]
                              - part.bounds[1], part.area, (part.bounds[1],) * 2, ()))
    return out


def _raked(key, role, frame: geo.Frame, part: Polygon, s0: float, s1: float, c: float,
           width: float, depth: float, area: float, zs, edges, raked=None) -> geo.Board:
    ring = tuple((s - s0, z) for s, z in tuple(part.exterior.coords)[:-1])
    p0, p1 = frame.at(s0, c), frame.at(s1, c)
    outline = tuple(frame.rect(s0, s1, c - width / 2.0, c + width / 2.0).exterior.coords)[:-1]
    return geo.Board(key, role, p0, p1, ring, width, depth, area, outline, (p0, p1),
                     zs[0], zs[1], edges, raked)


def _plumb(key, a, b, lo: float, hi: float, bead: float, t: float, ceilings) -> list[geo.Board]:
    """A plumb board across ``a``-``b`` (its run), ``t`` thick, from ``lo`` up to ``hi``."""
    width = math.dist(a, b)
    if width < 1e-3 or hi - lo < 1e-3:
        return []
    ux, uy = (b[0] - a[0]) / width, (b[1] - a[1]) / width
    frame = geo.Frame(a, (ux, uy), (-uy, ux))
    # Widened: a ceiling butting the board's open face conceals what stands above it.
    footprint = frame.rect(0.0, width, -t / 2.0, t / 2.0).buffer(geo.LANDING_MEETS_M)
    out = []
    for i, part in enumerate(geo.clip(box(0.0, lo, width, hi),
                                      geo.ceiling_clips(ceilings, footprint))):
        ps0, z0, ps1, z1 = part.bounds
        edges = (((*frame.at(ps0, 0.0), bead), (*frame.at(ps1, 0.0), bead)),) \
            if z0 <= bead + 1e-6 else ()
        out.append(_raked(key + (f"-{i}" if i else ""), "return", frame, part, ps0, ps1, 0.0,
                          t, z1 - z0, (ps1 - ps0) * (z1 - z0), (z0, z0), edges))
    return out


def _landing_board(landing: geo.Landing, t: float, ceilings) -> list[geo.Board]:
    u = landing.underside_m
    if any(z < u for _, _, z in geo.ceiling_clips(ceilings, landing.polygon)):
        return []  # concealed above the room's ceiling
    a, b, c, d = tuple(geo.aligned_rect(landing.polygon, landing.polygon).exterior.coords)[:4]
    p0 = ((a[0] + d[0]) / 2.0, (a[1] + d[1]) / 2.0)
    p1 = ((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0)
    length, width = math.dist(p0, p1), math.dist(a, d)
    ring = ((0.0, u - t), (length, u - t), (length, u), (0.0, u))
    return [geo.Board(f"soffit-landing-{landing.name}", "landing", p0, p1, ring, width, t,
                      length * width, (a, b, c, d), (p0, p1), u - t, u - t)]


def _steps(lands: list[geo.Landing], t: float) -> list[geo.Board]:
    """The riser between two half landings, where their footprints meet."""
    out = []
    for i, low in enumerate(lands):
        for high in lands[i + 1:]:
            if abs(low.underside_m - high.underside_m) < 1e-3:
                continue
            meet = intersection(low.polygon.exterior, high.polygon.buffer(0.002))
            segments = [(a, b) for line in getattr(meet, "geoms", [meet])
                        for a, b in zip(line.coords, line.coords[1:], strict=False)]
            if not segments:
                continue
            start, end = max(segments, key=lambda pair: math.dist(*pair))
            z_lo = min(low.underside_m, high.underside_m)
            out.extend(_plumb(f"soffit-step-{low.name}-{high.name}", start, end, z_lo - t,
                              max(low.underside_m, high.underside_m), z_lo - t, t, ()))
    return out


def _member(stair: ResolvedStair, board: geo.Board, material: str) -> FramedMember:
    zs = [z for _, z in board.ring]
    return FramedMember(
        stair.uid, board.key, CATEGORY,
        f"{board.plan_width_m / _IN:.3f}x{board.depth_m / _IN:.3f}",
        board.p0, board.p1, min(zs), max(zs), math.dist(board.p0, board.p1),
        material=material, plan_width_m=board.plan_width_m, elevation_profile=board.ring,
        cut_length_m=board.raked_length_m)


def _record(plan, model, stair: ResolvedStair, authored: Stair,
            board: geo.Board) -> StairUnderside:
    centre = Polygon(board.outline).centroid
    room = room_owning(model, stair.storey, (centre.x, centre.y))
    return StairUnderside(
        key=board.key, role=board.role, material_ref=authored.underside_material,
        thickness_m=authored.underside_thickness.meters, area_m2=board.area_m2,
        outline=tuple(board.outline), run_axis=board.run_axis, z_start_m=board.z_start_m,
        z_end_m=board.z_end_m, coating=None if authored.underside_unpainted
        else _coat(plan, room, authored), room=room.tag if room is not None else None,
        free_edges=board.free_edges)


def _coat(plan, room, authored: Stair) -> str | None:
    """The owning room's ceiling coat on this board, as ``resolve/ceilings.py`` paints one."""
    standard = paint_standard(plan)[0]
    if room is None:
        return unroomed_coat(standard, DEFAULT_PAINT, "ceilings")
    board = Layer(name="stair-underside", material_ref=authored.underside_material,
                  thickness=authored.underside_thickness,
                  function=LayerFunction.FINISH)
    painter = paint_room(plan.by_tag(room.tag), Polygon(room.clear_face), 0.0, 0.0, standard,
                         "ceilings")
    stack = paint_stack_end([board], 0, [painter], plan.library, envelope=False)[0]
    return stack[0].material_ref if stack[0].material_ref in coating_tags(plan.library) else None
