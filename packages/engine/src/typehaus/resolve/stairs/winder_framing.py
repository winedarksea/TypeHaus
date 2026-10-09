"""Nested platform boxes with plywood decks, fitted rims, and bearing-line blocking."""

from __future__ import annotations

import math

from shapely.geometry import LineString, Polygon

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.winder_geometry import (
    Segment,
    WinderLayout,
    clip_half_plane,
    line_intersection,
    polygon_ring,
    shifted_line,
)


def _inward_edges(polygon: Polygon):
    ring = polygon_ring(polygon)
    signed = sum(a[0] * b[1] - b[0] * a[1]
                 for a, b in zip(ring, (*ring[1:], ring[0]), strict=True))
    edges = []
    for a, b in zip(ring, (*ring[1:], ring[0]), strict=True):
        length = math.dist(a, b)
        sign = 1 if signed > 0 else -1
        normal = (-(b[1] - a[1]) / length * sign, (b[0] - a[0]) / length * sign)
        edges.append(((a, b), normal))
    return edges


def _offset_vertices(edges, widths):
    lines = [shifted_line(line, normal, width)
             for (line, normal), width in zip(edges, widths, strict=True)]
    return [line_intersection(lines[index - 1], line) for index, line in enumerate(lines)]


def _board(stair: Stair, key: str, polygon: Polygon, axis: Segment,
           base: float, top: float, ply_width: float) -> FramedMember:
    a, b = axis
    length = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    projections = [x * ux + y * uy for x, y in polygon.exterior.coords]
    return FramedMember(
        stair.uid, key, "landing_framing",
        f"{ply_width / .0254:g}x{(top - base) / .0254:g} rim",
        a, b, base, top, length, plan_outline=polygon_ring(polygon),
        cut_length_m=max(projections) - min(projections),
        stock_profile=stair.winder_framing.rim_profile)


def _rims(stair: Stair, index: int, polygon: Polygon, departing: Segment,
          base: float, top: float):
    ply = cross_section(stair.winder_framing.rim_profile).width_m
    edges = _inward_edges(polygon)
    depart_line = LineString(departing)
    plies = [stair.winder_framing.departing_rim_plies
             if depart_line.distance(LineString(line).interpolate(.5, normalized=True))
             < 1e-6 else 1 for line, _ in edges]
    inner = _offset_vertices(edges, [ply * count for count in plies])
    outer = [line[0] for line, _ in edges]
    interior = Polygon(inner)
    if not interior.is_valid or interior.area <= 1e-9:
        raise ValueError("winder box is too narrow for its rim stock")
    members = []
    for edge, ((line, normal), count) in enumerate(zip(edges, plies, strict=True)):
        following = (edge + 1) % len(edges)
        shape = Polygon((outer[edge], outer[following], inner[following], inner[edge]))
        for layer in range(count):
            lower = shifted_line(line, normal, layer * ply)
            upper = shifted_line(line, normal, (layer + 1) * ply)
            cut = clip_half_plane(clip_half_plane(shape, lower, normal), upper, normal, ahead=False)
            centre = shifted_line(line, normal, (layer + .5) * ply)
            axis = LineString(centre).intersection(cut)
            if not isinstance(axis, LineString) or axis.length <= 1e-7:
                raise ValueError("winder rim cannot be cut from its declared stock")
            key = f"landing-rim-winder{index}-{edge}" + (f"-ply{layer}" if count > 1 else "")
            members.append(_board(stair, key, cut, (axis.coords[0], axis.coords[-1]),
                                  base, top, ply))
    return members, interior


def _blocking(stair: Stair, index: int, interior: Polygon, lines: list[Segment],
              base: float, top: float):
    ply = cross_section(stair.winder_framing.rim_profile).width_m
    remaining = interior
    members = []
    for line in lines:
        band = LineString(line).buffer(ply / 2, cap_style="flat").intersection(remaining)
        pieces = [band] if isinstance(band, Polygon) else list(getattr(band, "geoms", ()))
        for piece in pieces:
            if not isinstance(piece, Polygon) or piece.area <= 1e-8:
                continue
            axis = LineString(line).intersection(piece)
            if not isinstance(axis, LineString) or axis.length <= 1e-7:
                raise ValueError("winder blocking cannot be cut from its declared stock")
            members.append(_board(stair, f"landing-joist-winder{index}-{len(members)}",
                                  piece, (axis.coords[0], axis.coords[-1]), base, top, ply))
        remaining = remaining.difference(band)
    return members


def departing_rim_members(members, layout: WinderLayout, tier: int,
                          plies: int, ply_width_m: float):
    """Select parallel rim plies, excluding adjacent boards that merely meet a corner."""
    departing = LineString(layout.riser_lines[-1])
    nx, ny = layout.normals[-1]
    return tuple(member for member in members
                 if member.child_key.startswith(f"landing-rim-winder{tier}-")
                 and abs((member.p1[0] - member.p0[0]) * nx
                         + (member.p1[1] - member.p0[1]) * ny) < 1e-7
                 and departing.distance(LineString((member.p0, member.p1)).interpolate(
                     .5, normalized=True)) < plies * ply_width_m + 1e-7)


def winder_box_framing(stair: Stair, layout: WinderLayout, z0: float,
                       riser: float, oak_thickness: float,
                       supporting_floor_m: float | None = None) -> list[FramedMember]:
    spec = stair.winder_framing
    plywood = spec.subdeck_thickness.meters
    riser_board = stair.riser_thickness.meters if stair.riser_thickness else 0.0
    stock = cross_section(spec.rim_profile)
    if plywood <= 0 or spec.support_spacing.meters <= stock.width_m:
        raise ValueError("winder plywood thickness and support spacing must be positive")
    if spec.departing_rim_plies < 1:
        raise ValueError("winder departing rim must have at least one ply")
    decks = [layout.subdeck(index, riser_board) for index in range(stair.winder_count)]
    minx, miny, maxx, maxy = layout.polygon.bounds
    seam = (miny + maxy) / 2
    support_ys = {seam}
    for lo, hi in zip((miny, seam), (seam, maxy), strict=True):
        divisions = max(1, math.ceil((hi - lo) / spec.support_spacing.meters))
        support_ys.update(lo + (hi - lo) * part / divisions for part in range(1, divisions))
    members = []
    for index, deck in enumerate(decks):
        walking_top = z0 + riser * (index + 1)
        deck_top = walking_top - oak_thickness
        frame_top = deck_top - plywood
        floor_top = z0 if supporting_floor_m is None else supporting_floor_m
        base = floor_top if index == 0 else z0 + riser * index - oak_thickness
        if frame_top <= base or frame_top - base > stock.depth_m + 1e-7:
            raise ValueError("winder tier height exceeds its rim stock or leaves no frame")
        rims, interior = _rims(stair, index, deck, layout.riser_lines[-1], base,
                               frame_top)
        members.extend(rims)
        supports = [((minx, y), (maxx, y)) for y in sorted(support_ys)]
        if index + 1 < len(decks):
            leading = shifted_line(layout.riser_lines[index + 1], layout.normals[index + 1],
                                    riser_board + stock.width_m / 2)
            a, b = leading
            dx, dy = b[0] - a[0], b[1] - a[1]
            supports.insert(0, ((a[0] - dx, a[1] - dy), (b[0] + dx, b[1] + dy)))
        members.extend(_blocking(stair, index, interior, supports, base, frame_top))
        seam_line = ((minx, seam), (maxx, seam))
        if deck.bounds[1] + 1e-7 < seam < deck.bounds[3] - 1e-7:
            parts = [clip_half_plane(deck, seam_line, (0.0, 1.0), ahead=False),
                     clip_half_plane(deck, seam_line, (0.0, 1.0))]
        else:
            parts = [deck]
        for part, outline in enumerate(parts):
            ring = polygon_ring(outline)
            axis = max(((a, b) for a, b in zip(ring, (*ring[1:], ring[0]), strict=True)),
                       key=lambda pair: math.dist(*pair))
            members.append(FramedMember(
                stair.uid, f"stair-subdeck-{index:03d}-{part}", "stair_subdeck",
                f"48x{plywood / .0254:g} panel", *axis, frame_top, deck_top,
                math.dist(*axis), material=spec.subdeck_material, plan_outline=ring,
                trade="framing"))
    return members
