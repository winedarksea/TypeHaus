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
    # The door's own casing is cut at its head too (O2-109): jamb, reveal and casing read
    # together, as the TrimStandard derives them.
    owners = [(opening.uid, None),
              *((s.uid, None) for s in model.window_stools if s.window_ref == opening.tag),
              *((c.uid, "casing") for c in model.door_casings if c.opening_uid == opening.uid)]
    out = []
    for uid, label in owners:
        element = model.geometry.by_uid(uid)
        for part in element.parts if element is not None else ():
            if part.key.startswith("hardware"):
                continue
            for profile in slice_part(part, plane):
                out.append((label or part.key, part.material_key,
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


def _key_peers(model, derived, opening) -> list:
    """The openings this detail stands for: those keyed on it, of the drawn one's class (a
    passage riding a door key is on A-602's rough-opening table, not A-601)."""
    from typehaus.resolve.detail_keys import detail_keys

    tags = {tag for cond, key, _kind in detail_keys(model)
            if key == derived.key and cond.kind.value == "opening_perimeter"
            for tag in cond.element_tags}
    return [o for o in model.openings if o.tag in tags and o.is_door == opening.is_door
            and (o.kind == "window") == (opening.kind == "window")]


def _ro_range_note(model, derived, opening) -> list[str]:
    """O1-006: one detail stands for every opening keyed on it; say when they differ."""
    heights = sorted({round(o.height_m / M_PER_IN * 16) / 16
                      for o in _key_peers(model, derived, opening)})
    if len(heights) < 2:
        return []
    schedule = "A-601" if opening.is_door else "A-602"
    return [f"R.O. HEIGHTS IN THIS ASSEMBLY {dim_text(heights[0])}"
            f" – {dim_text(heights[-1])}: SEE {schedule}"]


def _casing_note(model, opening) -> list[str]:
    """The cut casing's stock and reveal, off its derived record and the TrimStandard."""
    casing = next((c for c in model.door_casings if c.opening_uid == opening.uid), None)
    standard = next(iter(model.plan.elements_of_kind("TrimStandard")), None)
    if casing is None or standard is None:
        return []
    return [f"CASING {dim_text(casing.thickness_m / M_PER_IN)} x "
            f"{dim_text(casing.casing_width_m / M_PER_IN)} {casing.material_ref}, "
            f"{dim_text(standard.reveal.meters / M_PER_IN)} REVEAL TO JAMB"]


def _outboard_leg(model, assembly: str) -> tuple:
    """(material, thickness) of an assembly's layers from its outermost stud outward."""
    found = model.plan.library.assembly(assembly)
    layers = list(getattr(found, "layers", ()))
    cores = [i for i, layer in enumerate(layers) if layer.function.value == "structure"]
    if not cores:
        return ()
    return tuple((layer.material_ref, round(layer.thickness.meters, 5))
                 for layer in layers[cores[-1]:])


def _exterior_reference(model, derived, host, opening) -> list[str]:
    """O5-104: a liner recipe (the plant room's) draws only the inside; its outboard leg is
    a standard wall's, so name that wall's enlarged head and sill, numbered from the set."""
    from typehaus.emit.draw.callouts import detail_sheet_numbers
    from typehaus.emit.draw.detail_components.geometry import condition_walls
    from typehaus.emit.draw.detail_enlarged import enlarged_details
    from typehaus.emit.draw.details import derive_detail_slices

    leg = _outboard_leg(model, host.assembly)
    if not leg or enlarged_details_apply(derived):
        return []
    for other in derive_detail_slices(model):
        drawn = condition_opening(model, other.condition)
        walls = condition_walls(model, other.condition)
        if (drawn is None or not walls or drawn.kind != opening.kind
                or not enlarged_details_apply(other)
                or _outboard_leg(model, walls[0].assembly) != leg):
            continue
        sheet = detail_sheet_numbers(model).get(other.key)
        parts = [f"{sheet}.{i} ({child.part.upper()})"
                 for i, child in enumerate(enlarged_details(model, other), start=1)]
        if sheet is not None and parts:
            return [f"EXTERIOR HEAD AND SILL AS {', '.join(parts)}"]
    return []


def _under_notes(lines: list[str], crop) -> list[IRNode]:
    """Notes under the drawing, beside its caption, one per line."""
    (cu0, cz0), (cu1, cz1) = crop
    u, z = min(cu0, cu1) / M_PER_IN, min(cz0, cz1) / M_PER_IN - 10.0
    return [Text(anchor=(u, z - 4.0 * index), content=line, height_pt=6.5,
                 layer="A-ANNO-DIMS") for index, line in enumerate(lines)]


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
    notes: list[str] = []
    if part is None:
        nodes.append(dim((out_u, sill), (out_u, head), 0.0,
                         f"{dim_text(head - sill)} R.O."))
        notes += [*_ro_range_note(model, derived, opening), *_casing_note(model, opening),
                  *_exterior_reference(model, derived, host, opening)]
    if frame is not None and (opening.kind == "window" or part == "head"):
        nodes += _window_strings(opening, host, frame, profiles, part, out_u, sign, sill,
                                 head, direction, station)
    # A door with an enlarged sill takes its threshold there, where 1" is legible.
    enlarged = part is None and enlarged_details_apply(derived)
    if opening.is_door and (part == "sill" or (part is None and not enlarged)):
        strings, said = _threshold_strings(opening, profiles, in_u, out_u,
                                           compact=part is None)
        nodes += strings
        notes += said
    return nodes + _under_notes(notes, crop)


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


def _threshold_strings(opening, profiles, in_u: float, out_u: float,
                       compact: bool = False) -> tuple[list[IRNode], list[str]]:
    """O3-010: threshold top above the landing and above the finished floor inside, and
    (``compact``) the note naming them."""
    tops = [z for key, _m, points in profiles if "threshold" in key for _u, z in points]
    doorway = opening.doorway
    placement = getattr(doorway, "exterior_placement", None)
    crest = getattr(placement, "threshold_crest_z_m", None)
    if not tops and crest is not None:  # a catalog sill (Endura): its nominal crest
        tops = [crest / M_PER_IN]
    if not tops or doorway is None or not doorway.adjacent_floors:
        return [], []
    top = max(tops)
    floors = sorted(doorway.adjacent_floors,
                    key=lambda f: f.deck_top_m + f.finish_in * M_PER_IN)
    nodes: list[IRNode] = []
    said: list[str] = []
    # Whole-opening: a column past the R.O. string, which it would overlap at the sill.
    step = (7.0 if out_u < in_u else -7.0) if compact else 0.0
    for floor, u in ((floors[0], out_u - step), (floors[-1], in_u)):
        finished = floor.deck_top_m / M_PER_IN + floor.finish_in
        if top - finished > 1.0 / 16.0:
            where = "landing" if floor is floors[0] else "fin. floor"
            text = dim_text(top - finished)
            said.append(f"{text} ABOVE {where.upper()}")
            # At the whole-opening scale a 7" string holds only its number; the note says
            # what it measures (O3-108). An enlarged sill has room for the words.
            nodes.append(dim((u, finished), (u, top), 0.0, text, along=3.0) if compact else
                         dim((u, finished), (u, top), 0.0, f"{text} thr. above {where}",
                             along=5.0))
    return nodes, (["THRESHOLD CREST " + ", ".join(said)] if compact and said else [])
