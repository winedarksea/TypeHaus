"""Connected distribution of one ventilator: round runs by joints, rectangles only by anchor."""

from __future__ import annotations

import math

from typehaus.resolve.mep_envelopes import runs_are_joined, systems_join
from typehaus.resolve.model import ResolvedDuct


def _ends(duct: ResolvedDuct) -> list[tuple[tuple[float, float], float | None]]:
    z = duct.z_m if duct.z_m and len(duct.z_m) == len(duct.path) else None
    return [(duct.path[i], None if z is None else z[i]) for i in (0, -1)]


def ends_meet(first: ResolvedDuct, second: ResolvedDuct) -> bool:
    """Whether an END of one is at an END of the other (a neck into its trunk, not a tee).

    Within the engine's one duct joint tolerance, plan and (where both state it) elevation.
    """
    from typehaus.resolve.mep_envelopes import joint_tolerance_m

    tolerance = joint_tolerance_m()
    return any(math.dist(p, q) <= tolerance
               and (zp is None or zq is None or abs(zp - zq) <= tolerance)
               for p, zp in _ends(first) for q, zq in _ends(second))


def rectangular_chain(ducts: list[ResolvedDuct], anchored: dict[str, str]) -> dict[str, str]:
    """``anchored`` plus every materialled rectangular run joined end-to-end to one of them.

    Values (a plenum tag, say) propagate along the chain, so a neck off a plenum and the
    trunk that continues it both carry it. Only rectangle-to-rectangle on the same air
    side: a round run never pulls one in.
    """
    rect = {d.tag: d for d in ducts
            if d.diameter_m is None and d.material is not None and d.path}
    reached = {tag: value for tag, value in anchored.items() if tag in rect}
    frontier = sorted(reached)
    while frontier:
        current = rect[frontier.pop()]
        for tag, candidate in rect.items():
            if (tag not in reached
                    and systems_join(("duct", current.system), ("duct", candidate.system))
                    and ends_meet(current, candidate)):
                reached[tag] = reached[current.tag]
                frontier.append(tag)
    return reached


def connected_distribution(ducts: list[ResolvedDuct], seeds: set[str]) -> list[ResolvedDuct]:
    """Expand anchored runs through real compatible duct joints.

    A diameter change splits one physical header into several authored runs. A remote
    segment need not touch equipment to contribute its full pressure drop. Only endpoint
    joints establish membership: a crossing or the other air side cannot pull its own
    distribution into the ventilator's budget.

    **A rectangular run is a member only as a seed** (anchored on a plenum, or chained
    end-to-end to one: ``rectangular_chain``), never by walking a joint from a round run. So
    System 1's rectangular heat-pump trunks, which touch round runs, stay out; round runs
    joined to a seeded rectangle (the branches off a flat trunk) are walked in as usual.
    """
    eligible = {duct.tag: duct for duct in ducts
                if duct.material is not None and duct.path
                and (duct.diameter_m is not None or duct.tag in seeds)}
    reached = seeds & eligible.keys()
    frontier = sorted(reached)
    remaining = {tag: duct for tag, duct in eligible.items()
                 if tag not in reached and duct.diameter_m is not None}
    while frontier:
        current = eligible[frontier.pop()]
        connected = []
        for tag, candidate in remaining.items():
            if (systems_join(("duct", current.system), ("duct", candidate.system))
                    and runs_are_joined((current.path, current.z_m),
                                        (candidate.path, candidate.z_m))):
                connected.append(tag)
        for tag in connected:
            reached.add(tag)
            frontier.append(tag)
            del remaining[tag]
    return [duct for duct in ducts if duct.tag in reached]
