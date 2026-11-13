"""A chase lid: the fireblock sheet carried on ledgers, so the hole reads as floor.

``FloorOpening.lid`` names the ledger stock. A ledger goes on every edge whose face a
trimmer or header of the opening's own framing stands on (found by geometry), top under
the sheet; the long edges run corner to corner and the short ones fit between, since the
sheet spans the short way. Each is cut round the runs exactly as the sheet is, so a
rerouted riser moves its gap with no plan edit. The deck already reads the lid as
walkable (``ResolvedFloor.lids``); once the run holes are known this cuts them from the
finish the rooms laid across it.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import Polygon, box

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.overlay import difference, union_all

_CARRIERS = ("trimmer", "header")
_FACE_TOLERANCE_M = 1e-4


def lid_ledgers(floor, opening, rect: Polygon, sheet_bottom_m: float,
                holes_in_band) -> tuple[list[FramedMember], Polygon | None]:
    """``(ledgers, their plan footprint)``; ``holes_in_band(z0, z1)`` -> run tag -> hole."""
    section = cross_section(opening.lid.ledger_profile)
    width, z1 = section.width_m, sheet_bottom_m
    z0 = z1 - section.depth_m
    holes = list(holes_in_band(z0, z1).values())
    minx, miny, maxx, maxy = rect.bounds
    edges = {  # name -> (band inside the hole, runs along x)
        "south": (box(minx, miny, maxx, miny + width), True),
        "north": (box(minx, maxy - width, maxx, maxy), True),
        "west": (box(minx, miny, minx + width, maxy), False),
        "east": (box(maxx - width, miny, maxx, maxy), False),
    }
    framed = [name for name in edges if _carried(floor, rect, name)]
    framed.sort(key=lambda name: -edges[name][0].length)
    members, taken = [], []
    for name in framed:
        band, along_x = edges[name]
        bx0, by0, bx1, by1 = band.bounds
        gaps = [box(h.bounds[0], by0, h.bounds[2], by1) if along_x
                else box(bx0, h.bounds[1], bx1, h.bounds[3])
                for h in holes if h.intersects(band) and h.intersection(band).area > 1e-9]
        # A stick is not notched: a run clipping the band gaps the ledger across its width.
        cut = difference(band, union_all(taken + gaps)) if taken or gaps else band
        parts = [g for g in getattr(cut, "geoms", [cut])
                 if g.geom_type == "Polygon" and g.area > 1e-9]
        for index, part in enumerate(sorted(parts, key=lambda g: g.bounds)):
            x0, y0, x1, y1 = part.bounds
            p0, p1 = (((x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)) if along_x
                      else (((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)))
            members.append(FramedMember(
                floor.uid, f"ledger-{opening.tag}-{name}-{index}", "ledger",
                opening.lid.ledger_profile, p0, p1, z0, z1,
                (x1 - x0) if along_x else (y1 - y0)))
        taken.append(band)
    footprint = union_all(taken) if taken else None
    return members, footprint


def _carried(floor, rect: Polygon, edge: str) -> bool:
    """Whether a trimmer/header of this deck has its inner face on ``edge`` of ``rect``."""
    minx, miny, maxx, maxy = rect.bounds
    for member in floor.members:
        if member.category not in _CARRIERS:
            continue
        (ax, ay), (bx, by) = member.p0, member.p1
        half = cross_section(member.profile).width_m / 2.0
        if edge in ("south", "north") and abs(ay - by) < 1e-9:
            line = miny - half if edge == "south" else maxy + half
            overlap = min(max(ax, bx), maxx) - max(min(ax, bx), minx)
            if abs(ay - line) < _FACE_TOLERANCE_M and overlap > 1e-6:
                return True
        if edge in ("west", "east") and abs(ax - bx) < 1e-9:
            line = minx - half if edge == "west" else maxx + half
            overlap = min(max(ay, by), maxy) - max(min(ay, by), miny)
            if abs(ax - line) < _FACE_TOLERANCE_M and overlap > 1e-6:
                return True
    return False


def add_ledgers(model, floor_tag: str, opening_tag: str, ledgers: list[FramedMember]) -> None:
    """Set the opening's ledgers on its deck (``ResolvedFloor`` is frozen); re-runnable."""
    index = next(i for i, floor in enumerate(model.floors) if floor.tag == floor_tag)
    floor = model.floors[index]
    kept = tuple(m for m in floor.members if not (
        m.category == "ledger" and m.child_key.startswith(f"ledger-{opening_tag}-")))
    model.floors[index] = replace(floor, members=kept + tuple(ledgers))


def cut_run_holes_from_finish(model, storey: str, rect: Polygon, holes: list) -> None:
    """Take the lid's run holes out of every room finish laid across it."""
    from typehaus.resolve.room_finish import finish_parts

    if not holes:
        return
    cut = union_all(holes)

    def net(parts):
        whole = union_all([Polygon(outline, holes=list(inner)) for outline, inner in parts])
        trimmed = difference(whole, cut)
        return finish_parts(trimmed), trimmed.area

    for index, room in enumerate(model.rooms):
        if room.storey != storey or len(room.clear_face) < 3 \
                or not Polygon(room.clear_face).intersects(rect):
            continue
        field, area = net(room.field_finish) if room.field_finish else ((), 0.0)
        zones = []
        for zone in room.finish_zones:
            parts, zone_area = net(zone.parts) if zone.parts else ((), 0.0)
            zones.append(replace(zone, parts=parts, area_m2=zone_area))
        model.rooms[index] = replace(room, field_finish=field, field_area_m2=area,
                                     finish_zones=tuple(zones))
