"""Cut obstructing sole plates after walking surfaces and product supports are known."""
from dataclasses import replace
from math import hypot

from typehaus.resolve.doorway import DOORWAY
from typehaus.resolve.geometry import wall_frame


def _pocket_cavity(model, opening):
    """``(wall, low, high)`` stations of a pocket's cavity, mouth outward, clipped to its run."""
    from typehaus.resolve.framing.pockets import pocket_segments

    if not opening.pocket_run_m:
        return []
    segments, _shortfall = pocket_segments(model.plan, model, opening)
    remaining, cuts = opening.pocket_run_m, []
    for segment in segments:  # past the run is the closed-end jamb pack, which keeps its plate
        take = min(remaining, segment.high_m - segment.low_m)
        if take <= 0:
            break
        # The leaf enters a segment at its low end when it travels up that wall's axis.
        mouth_low = (opening.pocket_sign > 0 if segment.wall_tag == opening.host_wall
                     else segment.low_m <= 1e-9)
        cuts.append((segment.wall_tag, segment.low_m, segment.low_m + take) if mouth_low
                    else (segment.wall_tag, segment.high_m - take, segment.high_m))
        remaining -= take
    return cuts


def clear_doorway_sole_plates(model):
    # Each cut is (opening, low, high) in its wall's axis stations. A pocket's leaf travels
    # its whole cavity at the undercut, so the cassette's RO is cut, not only the mouth.
    openings = {}
    for opening in model.openings:
        if opening.doorway:
            openings.setdefault(opening.host_wall, []).append(
                (opening, opening.center_along_m - opening.width_m / 2,
                 opening.center_along_m + opening.width_m / 2))
            for wall_tag, low, high in _pocket_cavity(model, opening):
                openings.setdefault(wall_tag, []).append((opening, low, high))
    walls = []
    for wall in model.walls:
        origin, tangent, _, _ = wall_frame(wall)
        members = []
        for member in wall.members:
            # Structural mudsills and raised rough sills are separate load-bearing members.
            if (not member.child_key.startswith("plate-bottom")
                    or member.z0_m < wall.frame_base_z_m - DOORWAY.height_tolerance_m):
                members.append(member)
                continue
            segments = [(0.0, 1.0)]
            start = sum((member.p0[i] - origin[i]) * tangent[i] for i in (0, 1))
            end = sum((member.p1[i] - origin[i]) * tangent[i] for i in (0, 1))
            if abs(end - start) <= DOORWAY.height_tolerance_m:
                members.append(member)
                continue
            for opening, low, high in openings.get(wall.tag, ()):
                assembly = opening.doorway
                floors = assembly.adjacent_floors
                known_surfaces = [f.surface_m for f in floors
                                  if f is not None and f.surface_m is not None]
                if not known_surfaces:
                    continue
                # One known floor proves a sole plate obstructs a floor-level passage.
                # Raised access openings and documented sill bearings are preserved below.
                walking = min(known_surfaces)
                if member.z1_m <= walking + DOORWAY.height_tolerance_m:
                    continue
                if assembly.rough_opening_z_m > member.z1_m + DOORWAY.height_tolerance_m:
                    continue
                if any(c.specification.role in ("sill", "track")
                       and c.base_z_m >= member.z1_m - DOORWAY.height_tolerance_m
                       for c in assembly.components):
                    continue
                lo = (low - start) / (end - start)
                hi = (high - start) / (end - start)
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
        walls.append(replace(wall, members=_seat_split_studs(wall, members, origin, tangent)))
    model.walls = _seat_overhanging_split_studs(model.walls, walls)


def _plate_at(walls, member):
    """A sole plate of any wall whose top carries ``member``'s foot (a cavity runs on)."""
    tol, reach = DOORWAY.height_tolerance_m, 0.1
    x, y = member.p0[0], member.p0[1]
    for wall in walls:
        for p in wall.members:
            if not p.child_key.startswith("plate-bottom") or abs(p.z1_m - member.z0_m) > tol:
                continue
            dx, dy = p.p1[0] - p.p0[0], p.p1[1] - p.p0[1]
            run = hypot(dx, dy)
            if run <= tol:
                continue
            along = ((x - p.p0[0]) * dx + (y - p.p0[1]) * dy) / run
            across = abs((x - p.p0[0]) * dy - (y - p.p0[1]) * dx) / run
            if -tol <= along <= run + tol and across <= reach:  # foot centre over the plate
                return p
    return None


def _seat_overhanging_split_studs(before, after):
    """A split stud past its host wall's end stood on a colinear neighbour's cut plate."""
    out = []
    for wall in after:
        members = []
        for member in wall.members:
            cut = (member.child_key.startswith("pocketsplit")
                   and _plate_at(after, member) is None and _plate_at(before, member))
            if cut:
                member = replace(member, z0_m=cut.z0_m,
                                 length_m=member.length_m + member.z0_m - cut.z0_m)
            members.append(member)
        out.append(replace(wall, members=tuple(members)))
    return out


def _seat_split_studs(wall, members, origin, tangent):
    """A pocket kit's split studs stood on the plate just cut away; drop them to its bottom."""
    def station(point):
        return sum((point[i] - origin[i]) * tangent[i] for i in (0, 1))

    tol = DOORWAY.height_tolerance_m

    def plate_under(member, plates):
        at = station(member.p0)
        return next((p for p in plates
                     if abs(p.z1_m - member.z0_m) <= tol
                     and min(station(p.p0), station(p.p1)) - tol <= at
                     <= max(station(p.p0), station(p.p1)) + tol), None)

    before = [m for m in wall.members if m.child_key.startswith("plate-bottom")]
    after = [m for m in members if m.child_key.startswith("plate-bottom")]
    out = []
    for member in members:
        cut = (member.child_key.startswith("pocketsplit")
               and plate_under(member, after) is None and plate_under(member, before))
        if cut:
            drop = member.z0_m - cut.z0_m
            member = replace(member, z0_m=cut.z0_m, length_m=member.length_m + drop)
        out.append(member)
    return tuple(out)
