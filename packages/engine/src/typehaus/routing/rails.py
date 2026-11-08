"""Floor members a run may cross but never ride, as rails (``RoutingSpace.rails``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


def floor_rails(model: ResolvedModel, bbox: tuple[float, float, float, float]) -> list:
    """Every level, axis-aligned floor member in ``bbox``, as a rail — see ``rails``.

    ``mep.run_through_floor_member`` FAILs a leg "running along inside" a member, and the
    router laned catlin's kitchen vent along a truss line twice before this.
    """
    from typehaus.resolve.framing.profiles import cross_section

    minx, miny, maxx, maxy = bbox
    out = []
    for floor in model.floors:
        for member in floor.members:
            if member.z0_m is None or member.p0 == member.p1:
                continue
            (ax, ay), (bx, by) = member.p0, member.p1
            if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
                continue
            section = cross_section(member.profile)
            if section is None:
                continue
            axis = "x" if abs(bx - ax) > abs(by - ay) else "y"
            station = ay if axis == "x" else ax
            lo, hi = sorted((ax, bx) if axis == "x" else (ay, by))
            if (axis == "x" and not (miny <= station <= maxy and hi >= minx and lo <= maxx)) \
                    or (axis == "y" and not (minx <= station <= maxx
                                            and hi >= miny and lo <= maxy)):
                continue
            z1 = member.z1_m if member.z1_m is not None else member.z0_m + section.depth_m
            out.append((axis, station, lo, hi, section.width_m / 2.0, member.z0_m, z1,
                        floor.tag))
    return out
