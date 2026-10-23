"""Cut obstructing sole plates after walking surfaces and product supports are known."""
from dataclasses import replace
from math import hypot

from typehaus.resolve.doorway import DOORWAY
from typehaus.resolve.geometry import wall_frame


def clear_doorway_sole_plates(model):
    openings = {}
    for opening in model.openings:
        if opening.doorway:
            openings.setdefault(opening.host_wall, []).append(opening)
    walls = []
    for wall in model.walls:
        origin, tangent, _, _ = wall_frame(wall)
        members = []
        for member in wall.members:
            # Structural mudsills and raised rough sills are separate load-bearing members.
            if (not member.child_key.startswith("plate-bottom")
                    or member.z0_m < wall.base_ref_z_m - DOORWAY.height_tolerance_m):
                members.append(member)
                continue
            segments = [(0.0, 1.0)]
            start = sum((member.p0[i] - origin[i]) * tangent[i] for i in (0, 1))
            end = sum((member.p1[i] - origin[i]) * tangent[i] for i in (0, 1))
            if abs(end - start) <= DOORWAY.height_tolerance_m:
                members.append(member)
                continue
            for opening in openings.get(wall.tag, ()):
                assembly = opening.doorway
                floors = assembly.adjacent_floors
                if any(f is None or f.surface_m is None for f in floors):
                    # Unknown floors cannot distinguish support from obstruction.
                    continue
                walking = min(f.surface_m for f in floors)
                if member.z1_m <= walking + DOORWAY.height_tolerance_m:
                    continue
                if assembly.rough_opening_z_m > member.z1_m + DOORWAY.height_tolerance_m:
                    continue
                if any(c.specification.role in ("sill", "track")
                       and c.base_z_m >= member.z1_m - DOORWAY.height_tolerance_m
                       for c in assembly.components):
                    continue
                lo = (opening.center_along_m - opening.width_m / 2 - start) / (end - start)
                hi = (opening.center_along_m + opening.width_m / 2 - start) / (end - start)
                lo, hi = sorted((lo, hi))
                trimmed = []
                for a, b in segments:
                    if hi <= a or lo >= b:
                        trimmed.append((a, b))
                    else:
                        if lo > a:
                            trimmed.append((a, lo))
                        if hi < b:
                            trimmed.append((hi, b))
                segments = trimmed
            if segments == [(0.0, 1.0)]:
                members.append(member)
                continue
            for index, (a, b) in enumerate(segments):
                p0 = tuple(member.p0[i] + a * (member.p1[i] - member.p0[i]) for i in (0, 1))
                p1 = tuple(member.p0[i] + b * (member.p1[i] - member.p0[i]) for i in (0, 1))
                remaining_length = hypot(p1[0] - p0[0], p1[1] - p0[1])
                if remaining_length <= DOORWAY.height_tolerance_m:
                    continue
                members.append(replace(member, child_key=f"{member.child_key}-passage-{index}",
                                       p0=p0, p1=p1, length_m=remaining_length))
        walls.append(replace(wall, members=tuple(members)))
    model.walls = walls
