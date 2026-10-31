"""A framed ``Room.ceiling_lining`` layer, laid out as the sticks it is bought as.

Resolve draws a ceiling lining as one solid and frames none of it, so a layer that carries a
``FramingSpec`` (the sauna's 2x12 service cavity, a 1x4 or 2x4 furring) has no member to
bill. These are those members, derived for the order only: laid over the same carved
regions ``sheet_goods`` lines, at the spec's spacing, each spanning the region's SHORT plan
dimension (the span a ceiling member is framed across) and repeated along the long one.
``framing_takeoff`` bills them with the resolved members (category ``ceiling_furring``);
``sheet_goods`` skips the layer.
They never join ``model.all_members()``: the checks and drawings grade resolved framing.
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from typehaus.model.spatial import Room
from typehaus.resolve.ceiling_over import ceiling_regions
from typehaus.resolve.framing.furring import _module_stations
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import FramedMember, ResolvedModel

#: Its own category, so the order reads "ceiling furring" and not a wall's girt strapping.
CEILING_FURRING_CATEGORY = "ceiling_furring"


def ceiling_lining_members(model: ResolvedModel) -> list[FramedMember]:
    """Every framed ceiling-lining layer's sticks, room by room."""
    out: list[FramedMember] = []
    for room in model.rooms:
        plan_room = model.plan.by_tag(room.tag)
        if not isinstance(plan_room, Room) or len(room.clear_face) < 3:
            continue
        framed = [layer for layer in plan_room.ceiling_lining if layer.framing is not None]
        if not framed:
            continue
        regions = ceiling_regions(model.plan, room.storey, Polygon(room.clear_face),
                                  model.walls)
        for layer in framed:
            index = 0
            for region in regions:
                for p0, p1 in _runs(region.face, layer.framing):
                    out.append(FramedMember(
                        plan_room.uid, f"ceiling-{layer.name}-{index:03d}",
                        CEILING_FURRING_CATEGORY, layer.framing.member, p0, p1, 0.0, 0.0,
                        LineString((p0, p1)).length, material=layer.material_ref))
                    index += 1
    return out


def _runs(face, spec) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Members across ``face``'s short dimension, at ``spec.spacing`` along its long one."""
    parts = getattr(face, "geoms", (face,))
    face_m = cross_section(spec.member).depth_m  # laid flat: its wide face on the ceiling
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    out = []
    for part in parts:
        if part.is_empty or part.area <= 0.0:
            continue
        x0, y0, x1, y1 = part.bounds
        along_x = (x1 - x0) >= (y1 - y0)  # stations along the long side
        first, last = (x0, x1) if along_x else (y0, y1)
        lo, hi = (y0, y1) if along_x else (x0, x1)
        if last - first <= face_m:
            continue
        for station in _module_stations(first + face_m / 2.0, last - face_m / 2.0,
                                        spacing, face_m):
            line = (LineString(((station, lo), (station, hi))) if along_x
                    else LineString(((lo, station), (hi, station))))
            cut = part.intersection(line)
            for segment in getattr(cut, "geoms", (cut,)):
                if segment.geom_type == "LineString" and segment.length > face_m:
                    (ax, ay), (bx, by) = segment.coords[0], segment.coords[-1]
                    out.append(((ax, ay), (bx, by)))
    return out
