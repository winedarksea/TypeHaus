"""Exposed metal wall tops and the closures that terminate them at the roof."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import lru_cache

from typehaus.library.trim.metal_sales import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.runs import cladding_face, subtract_spans
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.geometry_ir import GBox, GMesh
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.geometry_slice_box import _box_mesh
from typehaus.resolve.geometry_walls import body_top_at
from typehaus.resolve.metal_skin_profiles import (
    CORRUGATED_PROFILE,
    PANEL_PROFILES,
    PBR_PROFILE,
    SHEET_24_GA_M,
)
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.panel_support import panel_support_clearance_m
from typehaus.resolve.roof_edge_geometry import footprint_test
from typehaus.resolve.roof_geometry import (
    roof_height_at,
    roof_plane_z,
    roof_slope_coordinate,
    roof_slope_factor,
)
from typehaus.resolve.roof_image_ii_eave import (
    HEAD_CLEARANCE_M,
    LAP_GAP_M,
    wrapped_eave_deck_cut,
    wrapped_eave_head_cap_w,
)

_FACE_ALIGNMENT_TOLERANCE_M = 0.5 * M_PER_IN
_TOP_ALIGNMENT_TOLERANCE_M = M_PER_IN
_ROOF_REACH_TOLERANCE_M = 4 * M_PER_IN
_CLOSURE_HEIGHT_M = 0.75 * M_PER_IN
#: Half a lap gap: an edge reaching within this of a skin's outer face runs through it.
_CORNER_TOLERANCE_M = LAP_GAP_M / 2


@dataclass(frozen=True)
class WallTopEdge:
    wall: object
    roof: object
    face: object
    product: str
    condition: TrimCondition
    start: float
    end: float
    z_start: float
    z_end: float
    #: Its place in the unclipped inventory, so a corner that drops an edge renames no other.
    ordinal: int = 0

    @property
    def length_m(self):
        return math.hypot(self.end - self.start, self.z_end - self.z_start)


def _soffit_elevation(roof, face, start, end):
    """Find the underside of the soffit whose inside edge meets this cladding face."""
    outside = face.back + face.layer.thickness_m
    found = []
    for member in roof.members:
        if member.category != "soffit" or not member.child_key.startswith("eave"):
            continue
        box = member_box(member)
        if box is None:
            continue
        points = box.corners_bottom
        offsets = [x*face.n[0] + y*face.n[1] for x, y, _ in points]
        stations = [x*face.d[0] + y*face.d[1] for x, y, _ in points]
        error = min(abs(min(offsets)-outside), abs(max(offsets)-outside))
        if (error < _FACE_ALIGNMENT_TOLERANCE_M
                and min(max(stations), end)-max(min(stations), start) > M_PER_IN):
            found.append((error, member.z0_m))
    return min(found)[1] if found else None


def exposed_wall_top_edges(model):
    """Find roof-terminated skin edges and remove coincident stacked wall extensions."""
    walls = {wall.uid: wall for wall in model.walls}
    materials = {material.tag: material for material in model.plan.library.materials}
    candidates = []
    for roof in model.roofs:
        for member in roof.members:
            if member.connection != "roof:wall-top-closure" or member.category != "cladding":
                continue
            wall = walls.get(member.parent_uid)
            material = materials.get(member.material)
            if (wall is None or material is None
                    or material.finish not in {"ribbed-panel", "board-and-batten", "corrugated"}):
                continue
            layer = next((layer for layer in wall.layers if layer.function == "cladding"
                          and layer.material_ref == member.material), None)
            face = cladding_face(wall, layer) if layer and layer.polygon else None
            if face is None:
                continue
            z0 = member.z1_m
            z1 = member.z1_m if member.z1_end_m is None else member.z1_end_m
            condition = TrimCondition.RAKE_TOP if abs(z1-z0) > 1e-6 else TrimCondition.EAVE_TOP
            product = material.trim_kit.get(condition, "")
            start = sum(a*b for a, b in zip(member.p0, face.d, strict=True))
            end = sum(a*b for a, b in zip(member.p1, face.d, strict=True))
            if end < start:
                start, end, z0, z1 = end, start, z1, z0
            if end - start > 1e-6:
                if product == "CORRUGATED_SILL_TO_SOFFIT":
                    soffit = _soffit_elevation(roof, face, start, end)
                    candidates.append(WallTopEdge(wall, roof, face,
                                                  "corrugated-outside-closure", condition,
                                                  start, end, z0, z1))
                    candidates.append(WallTopEdge(wall, roof, face, product if soffit is not None
                                                  else "", condition, start, end,
                                                  soffit if soffit is not None else z0,
                                                  soffit if soffit is not None else z1))
                else:
                    candidates.append(WallTopEdge(wall, roof, face, product, condition,
                                                  start, end, z0, z1))
    # A wall that already reaches its roof has no roof-generated extension. Its own
    # cladding top is still an edge and must enter the same coverage inventory.
    for wall in model.walls:
        for layer in wall.layers:
            material = materials.get(layer.material_ref)
            if (layer.function != "cladding" or not material or not layer.polygon
                    or material.finish not in {"ribbed-panel", "board-and-batten", "corrugated"}):
                continue
            face = cladding_face(wall, layer)
            if face is None:
                continue
            points = (face.xy(face.lo), face.xy(face.hi))
            tops = tuple(min(layer.band(wall)[1], body_top_at(wall, *point)) for point in points)
            condition = (TrimCondition.RAKE_TOP if abs(tops[1]-tops[0]) > 1e-6
                         else TrimCondition.EAVE_TOP)
            product = material.trim_kit.get(condition, "")
            possible = [roof for roof in model.roofs if footprint_test(roof)(wall)
                        and all(abs(roof_height_at(roof, point)-top) < _ROOF_REACH_TOLERANCE_M
                                for point, top in zip(points, tops, strict=True))]
            if not possible:
                continue
            roof = min(possible, key=lambda item: sum(
                abs(roof_height_at(item, point)-top)
                for point, top in zip(points, tops, strict=True)))
            cuts = [(edge.start, edge.end) for edge in candidates
                    if edge.wall.tag == wall.tag and edge.roof.tag == roof.tag
                    and edge.condition == condition]
            for upper in model.walls:
                if upper is wall or abs(upper.z0_m-max(tops)) > _TOP_ALIGNMENT_TOLERANCE_M:
                    continue
                for upper_layer in upper.layers:
                    if upper_layer.material_ref != layer.material_ref or not upper_layer.polygon:
                        continue
                    upper_face = cladding_face(upper, upper_layer)
                    if upper_face is None or abs(sum(a*b for a, b in zip(
                            face.d, upper_face.d, strict=True))) < 1-1e-6:
                        continue
                    endpoints = [upper_face.xy(upper_face.lo), upper_face.xy(upper_face.hi)]
                    if max(abs(x*face.n[0]+y*face.n[1]-face.back)
                           for x, y in endpoints) > _TOP_ALIGNMENT_TOLERANCE_M:
                        continue
                    cuts.append(tuple(sorted(x*face.d[0]+y*face.d[1] for x, y in endpoints)))
            for a, b in subtract_spans(face.lo, face.hi, cuts):
                f0, f1 = (a-face.lo)/(face.hi-face.lo), (b-face.lo)/(face.hi-face.lo)
                candidates.append(WallTopEdge(wall, roof, face, product, condition, a, b,
                                              tops[0]+f0*(tops[1]-tops[0]),
                                              tops[0]+f1*(tops[1]-tops[0])))
    # A wall-top member can be emitted both for the attic panel and the panel below it.
    # Prefer the upper wall and subtract only coincident spans at the same elevation.
    candidates.sort(key=lambda edge: (-edge.wall.z0_m, edge.wall.tag, edge.start))
    accepted = []
    for edge in candidates:
        cuts = []
        for old in accepted:
            if edge.product != old.product or edge.roof.tag != old.roof.tag:
                continue
            if abs(sum(a*b for a, b in zip(edge.face.d, old.face.d, strict=True))) < 1-1e-6:
                continue
            old_points = [old.face.xy(old.start), old.face.xy(old.end)]
            distances = [abs(x*edge.face.n[0] + y*edge.face.n[1] - edge.face.back)
                         for x, y in old_points]
            if max(distances) > _FACE_ALIGNMENT_TOLERANCE_M:
                continue
            a, b = sorted(x*edge.face.d[0] + y*edge.face.d[1] for x, y in old_points)
            middle = (max(a, edge.start) + min(b, edge.end)) / 2
            if middle < max(a, edge.start) or middle > min(b, edge.end):
                continue
            def elevation(item, station):
                return (item.z_start + (item.z_end-item.z_start) * (station-item.start)
                        / (item.end-item.start))
            old_station = sum(a*b for a, b in zip(edge.face.xy(middle), old.face.d, strict=True))
            height_difference = abs(elevation(edge, middle) - elevation(old, old_station))
            if height_difference < _TOP_ALIGNMENT_TOLERANCE_M:
                cuts.append((a, b))
        for a, b in subtract_spans(edge.start, edge.end, cuts):
            f0 = (a-edge.start)/(edge.end-edge.start)
            f1 = (b-edge.start)/(edge.end-edge.start)
            accepted.append(WallTopEdge(edge.wall, edge.roof, edge.face, edge.product,
                                        edge.condition, a, b,
                                        edge.z_start + f0*(edge.z_end-edge.z_start),
                                        edge.z_start + f1*(edge.z_end-edge.z_start)))
    accepted = [replace(edge, ordinal=number) for number, edge in enumerate(accepted)]
    return tuple(edge for edge in (_clip_at_corners(edge, accepted) for edge in accepted)
                 if edge is not None)


def _clip_at_corners(edge, edges):
    """``edge`` stopped at the back plane of a perpendicular skin it ends inside, as its panel
    does: the skin whose edge runs through to the other's outer face owns the corner.
    ``None`` when nothing of it is left."""
    start, end = edge.start, edge.end
    mid = edge.face.layer.thickness_m / 2
    for other in edges:
        g = other.face
        k = sum(a*b for a, b in zip(edge.face.d, g.n, strict=True))
        if other is edge or other.roof.tag != edge.roof.tag or abs(abs(k) - 1) > 1e-6:
            continue
        x, y = edge.face.xy(start, mid)
        along = x*g.d[0] + y*g.d[1]
        if not other.start - _CORNER_TOLERANCE_M <= along <= other.end + _CORNER_TOLERANCE_M:
            continue
        # Depth into the other skin is linear along this edge, ``k`` per meter.
        depth0 = x*g.n[0] + y*g.n[1] - g.back
        tip = end if k > 0 else start
        depth = depth0 + k*(tip - start)
        if not _CORNER_TOLERANCE_M < depth < g.layer.thickness_m - _CORNER_TOLERANCE_M:
            continue
        station = start + (-depth0) / k
        if abs(_z_at(edge, station) - _z_at(other, along)) > _ROOF_REACH_TOLERANCE_M:
            continue
        start, end = (start, min(end, station)) if k > 0 else (max(start, station), end)
    if end - start < 1e-6:
        return None
    if (start, end) == (edge.start, edge.end):
        return edge
    return replace(edge, start=start, end=end, z_start=_z_at(edge, start),
                   z_end=_z_at(edge, end))


def _z_at(edge, station):
    span = edge.end - edge.start
    return edge.z_start + (edge.z_end - edge.z_start) * (station - edge.start) / span


def _finish(model, material_ref):
    material = next((m for m in model.plan.library.materials if m.tag == material_ref), None)
    return material.finish if material else None


def _append(model, edge, tag, product, mesh, length, stock=None):
    xs, ys, zs = zip(*mesh.positions, strict=True)
    model.solids.append(ResolvedSolid(
        uid=f"{edge.wall.uid}-{tag.lower()}", tag=tag, storey=edge.wall.storey,
        category="cladding_trim", material=(edge.face.layer.material_ref if stock else "rubber"),
        product=product,
        host_ref=edge.wall.tag, derived=True, body_mesh=mesh,
        outline=((min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)),
                 (min(xs), max(ys))), z0_m=min(zs), z1_m=max(zs),
        trim_length_m=length, trim_stock_length_in=stock))


def _head_limits(model, edge) -> tuple[tuple[float, float], ...]:
    """(z at the back plane, fall per meter outboard) lines a level wall-top closure under a
    wrapped Image II eave stays under: clear of the eave's lowest sheet, and of the deck's
    square-cut end that oversails the panel's back. None elsewhere."""
    if edge.condition is not TrimCondition.EAVE_TOP:
        return ()
    point = edge.face.xy((edge.start + edge.end) / 2)
    cap_w = wrapped_eave_head_cap_w(model, edge.roof, point)
    if cap_w is None:
        return ()
    plane = roof_plane_z(edge.roof, roof_slope_coordinate(edge.roof, point))
    factor = roof_slope_factor(edge.roof)
    limits = [(plane + cap_w * factor, math.sqrt(factor * factor - 1.0))]
    deck = wrapped_eave_deck_cut(model, edge.roof, point)
    if deck is not None:
        limits.append((deck[0] - HEAD_CLEARANCE_M, -deck[1]))
    return tuple(limits)


def _polygon_span(polygon, d, n, offset):
    """(lo, hi) stations along ``d`` where the line ``n . p = offset`` is inside ``polygon``."""
    found = []
    for (ax, ay), (bx, by) in zip(polygon, (*polygon[1:], polygon[0]), strict=True):
        ea, eb = ax*n[0] + ay*n[1] - offset, bx*n[0] + by*n[1] - offset
        if (ea > 1e-9 and eb > 1e-9) or (ea < -1e-9 and eb < -1e-9):
            continue
        sa, sb = ax*d[0] + ay*d[1], bx*d[0] + by*d[1]
        found.extend((sa, sb) if abs(ea - eb) < 1e-12 else (sa + (sb - sa) * ea / (ea - eb),))
    return (min(found), max(found)) if found else (math.inf, -math.inf)


def _top_z(z, depth, limits):
    return min([z, *(line - fall * depth for line, fall in limits)])


def _profile_closure_mesh(model, edge, profile, outside=False):
    """Fill the panel rib voids using its actual repeating skin profile and layout line:
    behind the sheet, or ``outside`` it between the ribs (where the skin draws it). Under a
    wrapped eave, or outside the sheet, it stays inside the skin's own mitred polygon."""
    line = next((line for line in model.layout_lines
                 if any(member.wall_tag == edge.wall.tag for member in line.members)), None)
    origin = line.origin if line else edge.wall.axis[0]
    phase = origin[0]*edge.face.d[0] + origin[1]*edge.face.d[1]
    section = profile.section_points_m
    limits = _head_limits(model, edge)
    if outside:
        # The skin's own relief over concealed laps (board_batten.profile_mesh).
        relief = profile.depth_m - profile.sheet_thickness_m
        clearance = panel_support_clearance_m(model, edge.wall, edge.face.layer)
        section = tuple((s, depth + clearance * (profile.depth_m - depth) / relief)
                        for s, depth in section)
    return _closure_mesh(phase, edge.start, edge.end, edge.z_start, edge.z_end,
                         edge.face.d, edge.face.n, edge.face.back,
                         section, profile.pitch_m,
                         limits, profile.depth_m if outside else None,
                         tuple(edge.face.layer.polygon) if outside or limits else ())


@lru_cache(maxsize=128)
def _closure_mesh(phase, start, end, z_start, z_end, d, n, back, section, pitch_m,
                  limits=(), outer=None, polygon=()) -> GMesh:
    """The rib fill, a pure function of numbers (→ board_batten._fold), under every
    ``_head_limits`` line and inside ``polygon``. Inside the skin (back plane to sheet) by
    default; with ``outer``, outside it (sheet to the ``outer`` depth, between the ribs)."""

    def xy(station):  # CladdingFace.xy at depth 0
        return (station * d[0] + back * n[0], station * d[1] + back * n[1])

    first = math.floor((start-phase-pitch_m/2)/pitch_m)
    last = math.ceil((end-phase+pitch_m/2)/pitch_m)
    positions, triangles = [], []
    for number in range(first, last+1):
        center = phase + number*pitch_m
        for (a, da), (b, db) in zip(section, section[1:], strict=False):
            lo, hi = max(start, center+a), min(end, center+b)
            if hi-lo < 1e-9:
                continue
            d0 = da + (db-da)*(lo-center-a)/(b-a)
            d1 = da + (db-da)*(hi-center-a)/(b-a)
            if outer is not None and outer - max(d0, d1) < 1e-6:
                continue
            depths = (0.0, 0.0, d1, d0) if outer is None else (d0, d1, outer, outer)
            corners = []
            for station, depth in zip((lo, hi, hi, lo), depths, strict=True):
                if polygon:  # stay inside the skin's own (mitred) layer polygon
                    span_lo, span_hi = _polygon_span(polygon, d, n, back + depth)
                    station = min(max(station, span_lo), span_hi)
                x, y = xy(station)
                z = z_start + (z_end-z_start)*(station-start)/(end-start)
                corners.append((x+n[0]*depth, y+n[1]*depth, z))
            bottom = tuple((x, y, z-_CLOSURE_HEIGHT_M) for x, y, z in corners)
            top = tuple((x, y, _top_z(z, depth, limits))
                        for (x, y, z), depth in zip(corners, depths, strict=True))
            if (abs(corners[1][0]-corners[0][0]) + abs(corners[1][1]-corners[0][1]) < 1e-9
                    and abs(corners[2][0]-corners[3][0]) + abs(corners[2][1]-corners[3][1])
                    < 1e-9):
                continue
            if any(t[2] - b[2] < 1e-6 for t, b in zip(top, bottom, strict=True)):
                continue
            mesh = _box_mesh(GBox(bottom, top))
            offset = len(positions)
            positions.extend(mesh.positions)
            triangles.extend(tuple(index+offset for index in tri) for tri in mesh.triangles)
    return GMesh(tuple(positions), tuple(triangles))


def resolve_wall_top_closures(model):
    for edge in exposed_wall_top_edges(model):
        if not edge.product:
            continue
        span = edge.end-edge.start
        tag = f"TRIM-{edge.wall.tag}-{edge.condition.value.upper()}-{edge.ordinal+1}"
        if edge.product in PROFILES:
            profile = PROFILES[edge.product]
            section = tuple((-x*M_PER_IN, y*M_PER_IN) for x, y in profile.section_in)
            for index, (start, end, stock) in enumerate(split_stock_run(
                    edge.length_m, tuple(x*M_PER_IN for x in profile.stock_lengths_in),
                    profile.min_lap_in*M_PER_IN)):
                f0, f1 = start/edge.length_m, end/edge.length_m
                x, y = edge.face.xy(edge.start + span*f0,
                                    profile.receiver_throat_in * M_PER_IN)
                delta_z = (edge.z_end-edge.z_start)*(f1-f0)
                run = (edge.face.d[0]*span*(f1-f0), edge.face.d[1]*span*(f1-f0), delta_z)
                # The second section axis is perpendicular to the inclined run.
                axis = (-edge.face.d[0]*delta_z/(end-start),
                        -edge.face.d[1]*delta_z/(end-start), span*(f1-f0)/(end-start))
                origin = (x, y, edge.z_start + f0*(edge.z_end-edge.z_start))
                mesh = folded_section_mesh(section, origin,
                                           (*edge.face.n, 0.0), axis, run, SHEET_24_GA_M)
                _append(model, edge, f"{tag}-{index+1}", edge.product, mesh, end-start,
                        round(stock/M_PER_IN, 6))
        else:
            if edge.product in {"6460800", "corrugated-outside-closure"}:
                profile = PBR_PROFILE if edge.product == "6460800" else CORRUGATED_PROFILE
                mesh = _profile_closure_mesh(model, edge, profile)
                _append(model, edge, tag, edge.product, mesh, edge.length_m)
                continue
            # Universal foam compresses against the cut BBD75 ribs, outside the sheet.
            skin = PANEL_PROFILES.get(_finish(model, edge.face.layer.material_ref))
            if skin is not None:
                mesh = _profile_closure_mesh(model, edge, skin, outside=True)
                _append(model, edge, tag, edge.product, mesh, edge.length_m)
                continue
            x0, y0 = edge.face.xy(edge.start)
            x1, y1 = edge.face.xy(edge.end)
            n = edge.face.n
            width = edge.face.layer.thickness_m
            height = _CLOSURE_HEIGHT_M
            limits = _head_limits(model, edge)
            bottom = ((x0,y0,edge.z_start-height), (x1,y1,edge.z_end-height),
                      (x1+n[0]*width,y1+n[1]*width,edge.z_end-height),
                      (x0+n[0]*width,y0+n[1]*width,edge.z_start-height))
            top = tuple((x, y, _top_z(z+height, depth, limits)) for (x, y, z), depth
                        in zip(bottom, (0.0, 0.0, width, width), strict=True))
            _append(model, edge, tag, edge.product, _box_mesh(GBox(bottom,top)), edge.length_m)
