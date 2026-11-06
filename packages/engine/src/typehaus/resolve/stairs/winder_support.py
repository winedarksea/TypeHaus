"""Supporting floor datum for winder platforms and flights off a floating finish."""

from __future__ import annotations

from typehaus.model.floors import FloorSystem, Slab
from typehaus.model.spatial import Stair
from typehaus.resolve.model import FramedMember, ResolvedModel


def winder_supporting_floor(model: ResolvedModel, stair: Stair, finished_base: float,
                            xy: tuple[float, float] | None = None) -> float:
    """Seat the first platform on structural subfloor, keeping the oak step datum."""
    from shapely.geometry import Point, Polygon

    if xy is None and stair.start is not None:
        xy = stair.start.xy_m
    origin = Point(xy) if xy is not None else None
    source = model.plan.storey(stair.from_storey)
    candidates = []
    for element in model.plan.storey_elements(stair.from_storey):
        if isinstance(element, FloorSystem):
            if element.outline and origin is not None and not Polygon(
                    [p.xy_m for p in element.outline]).covers(origin):
                continue
            top = element.top_elevation.meters if element.top_elevation else source.elevation.meters
            plywood = element.subfloor.thickness.meters if element.subfloor else 0.0
            candidates.append(top + plywood)
        elif isinstance(element, Slab):
            candidates.append(element.top_elevation.meters if element.top_elevation
                              else source.elevation.meters)
    below = [top for top in candidates if top <= finished_base + 1e-7]
    return max(below) if below else finished_base


def _floats_at(model: ResolvedModel, storey: str, xy: tuple[float, float]) -> bool:
    """Whether the covering the authored rooms put at ``xy`` is a ``Material.floating`` one."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.rooms import claimed_room_faces

    point = Point(xy)
    room = next((room for room, face in claimed_room_faces(model.plan, storey)
                 if face.covers(point)), None)
    if room is None:
        return False
    ref = next((zone.material_ref for zone in reversed(room.finish_zones)
                if len(zone.outline) >= 3
                and Polygon([p.xy_m for p in zone.outline]).covers(point)), room.floor_finish)
    material = next((m for m in model.plan.library.materials if m.tag == ref), None)
    return bool(getattr(material, "floating", False))


def floating_support(model: ResolvedModel, stair: Stair, finished_base: float,
                     members: tuple[FramedMember, ...]) -> float:
    """A flight springing off a floating finish bears on the sheet beneath it (C1 E4).

    The finish is read under the first riser (or tread); treads keep their datum. A U-stair's
    well partition is untouched: it stacks on the flight below, over an opening, not a plank.
    """
    first = min((m for m in members if m.category in ("riser", "tread")),
                key=lambda m: m.z0_m, default=None)
    if first is None:
        return finished_base
    xy = ((first.p0[0] + first.p1[0]) / 2.0, (first.p0[1] + first.p1[1]) / 2.0)
    if not _floats_at(model, stair.from_storey, xy):
        return finished_base
    return winder_supporting_floor(model, stair, finished_base, xy)


def winder_members_fit_opening(members, outline) -> bool:
    """Keep the straight flight's treads inside the actual opening polygon.

    The turn's winders and subdecks may stand under intact deck; R311.7.2 grades the
    headroom over them (``resolve/stair_headroom.py``).
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint

    opening = Polygon(outline).buffer(1e-7)
    return all(opening.covers(Polygon(member_footprint(member)[0])) for member in members
               if member.category == "tread")
