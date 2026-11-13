"""An I-joist's body binds a lane along it and a riser through it (``mep.run_in_joist_web``).

A leg ACROSS a joist is a bore, graded by ``routing/members`` on the hole ladder; it is
left alone here. A leg along the bay inside the member's plan takes its web or a flange,
neither of which any maker charts, so the whole section is hard to that edge.
"""

from __future__ import annotations

from typing import Any

_CATEGORIES = ("joist", "sister_joist", "blocking")


def ijoist_body_prisms(model: Any, inflate: float) -> list:
    """One prism per axis-aligned I-joist member, binding edges along it and in z."""
    from shapely.geometry import box

    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.routing.obstacles import HardPrism

    out = []
    for floor in model.floors:
        for member in floor.members:
            if member.category not in _CATEGORIES or member.z0_m is None:
                continue
            section = cross_section(member.profile)
            (ax, ay), (bx, by) = member.p0, member.p1
            along_x = abs(ay - by) < 1e-6
            if (section is None or section.shape != "i_joist" or member.p0 == member.p1
                    or not (along_x or abs(ax - bx) < 1e-6)):
                continue
            half = section.width_m / 2.0
            body = box(min(ax, bx) - half * (not along_x), min(ay, by) - half * along_x,
                       max(ax, bx) + half * (not along_x), max(ay, by) + half * along_x)
            z1 = member.z1_m if member.z1_m is not None else member.z0_m + section.depth_m
            out.append(HardPrism(tag=f"{floor.tag} {member.child_key}", kind="member",
                                 footprint=body.buffer(inflate),
                                 z0_m=member.z0_m - inflate, z1_m=z1 + inflate,
                                 applies=frozenset({"x" if along_x else "y", "z"})))
    return out
