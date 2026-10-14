"""Connected round-product distribution, including remote diameter transitions."""

from __future__ import annotations

from typehaus.resolve.mep_envelopes import runs_are_joined, systems_join
from typehaus.resolve.model import ResolvedDuct


def connected_distribution(ducts: list[ResolvedDuct], seeds: set[str]) -> list[ResolvedDuct]:
    """Expand anchored runs through real compatible duct joints.

    A diameter change splits one physical header into several authored runs. A remote
    segment need not touch equipment to contribute its full pressure drop. Only endpoint
    joints establish membership: a crossing, the other air side, or an untyped System 1
    trunk cannot pull its own distribution into the ventilator's budget.
    """
    eligible = {duct.tag: duct for duct in ducts if duct.material is not None and duct.path}
    reached = seeds & eligible.keys()
    frontier = sorted(reached)
    remaining = {tag: duct for tag, duct in eligible.items() if tag not in reached}
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
