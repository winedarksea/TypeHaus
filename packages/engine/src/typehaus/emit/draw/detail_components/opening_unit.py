"""The unit in an opening detail, and the strings that place it (C7-E4, O4-004, O3-010).

The wall cut stops at the rough opening; the product standing in it is the opening's own
resolved geometry (frame, glass, leaf, sill, casing) and its stool, sliced at the detail's
station exactly as the 3D model builds them. The strings read the same pieces: R.O.,
frame height and sill rise off ``WindowSeat``, the threshold off the doorway's floors.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.geometry import (
    closed_region,
    condition_opening,
    outboard_is_high,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.detail_components.stack_dimensions import dim, dim_text
from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.scene import IRNode, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, slice_part

#: Drawn fill per product material key; anything else draws as the dark exterior trim.
_PATTERN = {"glass": ("glass", "glass"), "door_frame": ("spf", "lumber"),
            "door_leaf": ("spf", "lumber"), "lumber": ("spf", "lumber")}


def unit_profiles(model, opening, direction: str, station: float) -> list[tuple]:
    """``(key, material_key, outline_in)`` for every product piece the cut crosses."""
    if model.geometry is None:
        return []
    plane = CutPlane(axis=direction, station_m=station)
    owners = [opening.uid, *(s.uid for s in model.window_stools if s.window_ref == opening.tag)]
    out = []
    for uid in owners:
        element = model.geometry.by_uid(uid)
        for part in element.parts if element is not None else ():
            if part.key.startswith("hardware"):
                continue
            for profile in slice_part(part, plane):
                out.append((part.key, part.material_key,
                            [(u / M_PER_IN, z / M_PER_IN) for u, z in profile.outline]))
    return out


def _clipped(points, crop) -> list:
    """The profile's rings inside the crop: a door leaf runs the full R.O., a crop does not."""
    from shapely.geometry import Polygon, box

    (cu0, cz0), (cu1, cz1) = crop
    window = box(min(cu0, cu1) / M_PER_IN, min(cz0, cz1) / M_PER_IN,
                 max(cu0, cu1) / M_PER_IN, max(cz0, cz1) / M_PER_IN)
    shape = Polygon(points)
    if not shape.is_valid:
        shape = shape.buffer(0)
    piece = shape.intersection(window)
    parts = getattr(piece, "geoms", [piece])
    return [list(g.exterior.coords)[:-1] for g in parts
            if g.geom_type == "Polygon" and not g.is_empty]


def unit_nodes(model, opening, crop, direction: str, station: float) -> list[IRNode]:
    """The product cut: frame and casing dark, glass blue, a door's wood leaf and stool."""
    nodes: list[IRNode] = []
    for key, material, points in unit_profiles(model, opening, direction, station):
        fill, pattern = _PATTERN.get(material, ("metal-dark", "metal"))
        for ring in _clipped(points, crop):
            nodes += closed_region(ring, f"opening-unit-{key.split(':')[0]}", fill, pattern,
                                   lineweight=PROFILE)
    return nodes


def _bounds(profiles, keys) -> tuple[float, float, float, float] | None:
    pts = [p for key, _m, points in profiles if key.split(":")[0] in keys for p in points]
    if not pts:
        return None
    return (min(u for u, _z in pts), min(z for _u, z in pts),
            max(u for u, _z in pts), max(z for _u, z in pts))


def _ro_range_note(model, opening, host, at) -> list[IRNode]:
    """O1-006: one detail stands for every opening in this assembly; say when they differ."""
    heights = sorted({round(o.height_m / M_PER_IN * 8) / 8 for o in model.openings
                      if o.kind == opening.kind and (w := model.wall(o.host_wall)) is not None
                      and w.assembly == host.assembly})
    if len(heights) < 2:
        return []
    schedule = "A-601" if opening.is_door else "A-602"
    return [Text(anchor=at, content=f"R.O. HEIGHTS IN THIS ASSEMBLY {dim_text(heights[0])}"
                 f" – {dim_text(heights[-1])}: SEE {schedule}", height_pt=6.5,
                 layer="A-ANNO-DIMS")]


def opening_strings(model, derived, host, crop, direction: str, station: float,
                    part: str | None = None) -> list[IRNode]:
    """R.O. outboard; frame and sill rise (window) or threshold (door) inboard.

    ``part`` is ``"head"``/``"sill"`` on an enlarged child, which takes only its own end.
    """
    opening = condition_opening(model, derived.condition)
    lo, hi = wall_cut_bounds_m(host, direction, station) if host is not None else (None, None)
    if opening is None or hi is None:
        return []
    lo, hi = lo / M_PER_IN, hi / M_PER_IN
    sill = (host.base_ref_z_m + opening.sill_m) / M_PER_IN
    head = sill + opening.height_m / M_PER_IN
    high = outboard_is_high(host, direction, station)
    out_u, in_u = (hi + 3.0, lo - 3.0) if high is not False else (lo - 3.0, hi + 3.0)
    profiles = unit_profiles(model, opening, direction, station)
    frame = _bounds(profiles, {"frame"})
    sign = 1.0 if high is not False else -1.0  # outboard
    nodes: list[IRNode] = []
    if part is None:
        nodes.append(dim((out_u, sill), (out_u, head), 0.0,
                         f"{dim_text(head - sill)} R.O."))
        (cu0, cz0), (cu1, cz1) = crop
        nodes += _ro_range_note(model, opening, host,
                                (min(cu0, cu1) / M_PER_IN, min(cz0, cz1) / M_PER_IN - 10.0))
    if frame is not None and (opening.kind == "window" or part == "head"):
        nodes += _window_strings(opening, host, frame, profiles, part, out_u, sign, sill,
                                 head, direction, station)
    # A door with an enlarged sill takes its threshold there, where 1" is legible.
    enlarged = part is None and enlarged_details_apply(derived)
    if opening.is_door and (part == "sill" or (part is None and not enlarged)):
        nodes += _threshold_strings(opening, profiles, in_u, out_u)
    return nodes


#: How far a short string's label slides off it, model inches (3" = 1'-0"): into the open
#: R.O. (down from a head, up from a sill), clear of the wall the layer ladder labels.
_SLIDE_IN = 4.5


def _window_strings(opening, host, frame, profiles, part, out_u, sign, sill, head,
                    direction, station) -> list[IRNode]:
    """Frame height on the whole opening; shim/rise, frame depth and mount plane enlarged.

    Enlarged strings sit in the glass zone (below a head frame, above a sill frame), the
    one place in the crop with no wall to print over."""
    from typehaus.emit.draw.detail_components.geometry import (
        face_of,
        layer_intervals,
        outermost_with_function,
    )

    f_lo, f_bot, f_hi, f_top = frame
    if part is None:
        u = out_u + sign * 7.0
        return [dim((u, f_bot), (u, f_top), 0.0, f"{dim_text(f_top - f_bot)} frame")]
    if part == "head" and head - f_top < 1.0 / 16.0 and opening.is_door:
        # The leaf hangs below the head frame: the label slides outboard, off the leaf.
        z = f_bot - 2.5
        return [dim((f_lo, z), (f_hi, z), 0.0, f"{dim_text(f_hi - f_lo)} frame",
                    along=sign * ((f_hi - f_lo) / 2.0 + _SLIDE_IN))]
    mid = (sill + head) / 2.0
    end = [p for _k, _m, points in profiles if _k.startswith("frame")
           and (sum(z for _u, z in points) / len(points) > mid) == (part == "head")
           for p in points]
    if not end:
        return []
    f_lo, f_hi = min(u for u, _z in end), max(u for u, _z in end)
    f_bot, f_top = min(z for _u, z in end), max(z for _u, z in end)
    if part == "head":
        nodes = [dim((out_u, f_top), (out_u, head), 0.0,
                     f"{dim_text(head - f_top)} head shim", along=-_SLIDE_IN)]
        z = f_bot - 2.5
    else:
        nodes = [dim((out_u, sill), (out_u, f_bot), 0.0,
                     f"{dim_text(f_bot - sill)} sill rise", along=_SLIDE_IN)]
        z = f_top + 2.0
    nodes.append(dim((f_lo, z), (f_hi, z), 0.0, f"{dim_text(f_hi - f_lo)} frame"))
    seat = opening.window_seat
    sheath = outermost_with_function(layer_intervals(host, direction, station), "sheathing")
    if seat is not None and seat.outer_m is not None and sheath is not None:
        mount = f_hi if sign > 0 else f_lo
        face = face_of(sheath, sign > 0, outer=True)
        zz = z - 3.0 if part == "head" else z + 2.5
        nodes.append(dim((mount, zz), (face, zz), 0.0,
                         f"{dim_text(abs(face - mount))} mount plane to sheathing"))
    return nodes


def enlarged_details_apply(derived) -> bool:
    from typehaus.emit.draw.detail_enlarged import ENLARGED_OVERLAYS

    return getattr(derived.transition, "overlay", None) in ENLARGED_OVERLAYS


def _threshold_strings(opening, profiles, in_u: float, out_u: float) -> list[IRNode]:
    """O3-010: threshold top above the landing and above the finished floor inside."""
    tops = [z for key, _m, points in profiles if "threshold" in key for _u, z in points]
    doorway = opening.doorway
    if not tops or doorway is None or not doorway.adjacent_floors:
        return []
    top = max(tops)
    floors = sorted(doorway.adjacent_floors,
                    key=lambda f: f.deck_top_m + f.finish_in * M_PER_IN)
    nodes: list[IRNode] = []
    for floor, u in ((floors[0], out_u), (floors[-1], in_u)):
        finished = floor.deck_top_m / M_PER_IN + floor.finish_in
        if top - finished > 1.0 / 16.0:
            where = "landing" if floor is floors[0] else "fin. floor"
            nodes.append(dim((u, finished), (u, top), 0.0,
                             f"{dim_text(top - finished)} thr. above {where}", along=5.0))
    return nodes
