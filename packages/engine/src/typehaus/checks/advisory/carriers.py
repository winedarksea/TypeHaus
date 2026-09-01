"""In-wall fixture carriers: is the wall deep enough, and is the bay actually free?

``advisory.wet_wall_depth`` grades the wall a fixture's ``wall_ref`` names, and in this repo
that is the *wet* wall a fixture plumbs into — the wall its trap arm and vent reach, which
for a wall-hung bowl is routinely a different wall from the one its carrier stands in. So
the host wall's depth, which is the one dimension that decides whether a frame can be
bought at all, went ungraded. These two checks close that, off the same
``framing/carriers`` walk the framing solver uses, so the wall the bay is framed in and the
wall the depth is measured on cannot drift apart.

Both are ADVISORY: nothing in the IRC or the MN Plumbing Code sizes a proprietary carrier
frame. What is cited here is the manufacturers' own published rough-in, which is what the
``FixtureType.source`` on a wall-hung type already states.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable, passed
from typehaus.model.enums import Service
from typehaus.model.spatial import Fixture
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.carriers import backing_wall, carrier_bays

# Geberit and TOTO both publish a 2x4 wall as the absolute minimum for an in-wall WC frame,
# and both need their 2x4 outlet kit to hit it: 3" DWV is 3.5" OD and 90 mm HDPE is 3.54",
# so at 3 1/2" the pipe is as wide as the cavity and there is no room for an offset. 5 1/2"
# is the detail they design for and the only one that takes a horizontal offset connector.
_ABSOLUTE_MINIMUM_IN = 3.5
_WANTED_IN = 5.5

# In-wall services. A fixture needing none of these has nothing to route through the bay.
_IN_WALL_SERVICES = frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN,
                               Service.VENT})


@check(Tier.ADVISORY, "advisory.carrier_bay_depth")
def carrier_bay_depth(ctx: CheckContext) -> list[Finding]:
    """The wall a carrier stands in has to be deep enough to hold one, and long enough."""
    bays = carrier_bays(ctx.plan, ctx.model)
    if not bays:
        return [not_applicable("advisory.carrier_bay_depth",
                               "no fixture in this plan declares an in-wall carrier "
                               "(FixtureType.carrier_bay_width), so no wall hosts a frame")]
    out: list[Finding] = []
    for bay in bays:
        wall = ctx.model.wall(bay.wall_tag)
        if wall is None:  # pragma: no cover - the bay was located ON this wall
            continue
        structure = next((layer for layer in wall.layers if layer.function == "structure"),
                         None)
        actual = 0.0 if structure is None else structure.thickness_m / M_PER_IN
        tags = (bay.fixture_tag, bay.wall_tag)
        if actual + 1e-9 < _ABSOLUTE_MINIMUM_IN:
            out.append(advisory(
                "advisory.carrier_bay_depth",
                f"{bay.fixture_tag}'s carrier stands in {bay.wall_tag}, whose structure is "
                f"{actual:.1f}\" — under the {_ABSOLUTE_MINIMUM_IN:.1f}\" every in-wall WC "
                f"frame publishes as its absolute minimum. No frame is buyable for this "
                f"wall", tags, Result.FAIL,
                fix=f"deepen {bay.wall_tag} to {_WANTED_IN:.1f}\", or use a floor-mounted "
                    f"fixture type"))
        elif actual + 1e-9 < _WANTED_IN:
            out.append(advisory(
                "advisory.carrier_bay_depth",
                f"{bay.fixture_tag}'s carrier stands in {bay.wall_tag} at {actual:.1f}\" of "
                f"structure — buildable, but it needs the manufacturer's 2x4 outlet kit and "
                f"leaves no room for an offset connector ({_WANTED_IN:.1f}\" is the detail "
                f"they design for)", tags, Result.PASS))
        else:
            out.append(passed(
                "advisory.carrier_bay_depth",
                f"{bay.fixture_tag}'s carrier stands in {bay.wall_tag}: {actual:.1f}\" of "
                f"structure against the {_WANTED_IN:.1f}\" its frame wants", tags))
        axis_len = _axis_length(wall)
        if bay.low_m < -1e-9 or bay.high_m > axis_len + 1e-9:
            out.append(advisory(
                "advisory.carrier_bay_depth",
                f"{bay.fixture_tag}'s {bay.half_m * 2 / M_PER_IN:.2f}\" carrier bay runs "
                f"past the end of {bay.wall_tag} ({axis_len / M_PER_IN:.1f}\" long): the "
                f"frame has nowhere to be framed", tags, Result.FAIL,
                fix="move the fixture along the wall, or host it on a longer one"))
    return out


@check(Tier.ADVISORY, "advisory.carrier_bay_conflict")
def carrier_bay_conflict(ctx: CheckContext) -> list[Finding]:
    """Another fixture's in-wall services must not need the cavity the frame is filling.

    A carrier frame occupies its bay floor-to-head across the *whole* structure depth of a
    2x4 wall. Anything else that has to get a pipe into that same band of that same wall —
    from either face; a plumbing wall is served from both — is competing for cavity that is
    no longer there.

    Whether that is a defect depends on the wall, which is why this check reads the depth
    the sibling check grades. In a 5 1/2" wall the frame is a 2x4-class product with ~2" of
    cavity behind it, and a 1/2" supply crossing behind the frame is an ordinary detail —
    reported, because a plumber has to be told, but not a fault. In a 3 1/2" wall the frame
    fills the cavity and there is nothing to cross through.
    """
    bays = carrier_bays(ctx.plan, ctx.model)
    if not bays:
        return [not_applicable("advisory.carrier_bay_conflict",
                               "no fixture in this plan declares an in-wall carrier, so no "
                               "bay is reserved and nothing can compete for one")]
    types = {item.tag: item for item in ctx.plan.library.fixture_types}
    out: list[Finding] = []
    for bay in bays:
        wall = ctx.model.wall(bay.wall_tag)
        structure = next((layer for layer in wall.layers if layer.function == "structure"),
                         None) if wall is not None else None
        deep = structure is not None and structure.thickness_m / M_PER_IN + 1e-9 >= _WANTED_IN
        crowding: list[tuple[str, float]] = []
        for element in ctx.plan.all_elements():
            if not isinstance(element, Fixture) or element.tag == bay.fixture_tag:
                continue
            fixture_type = types.get(element.type_ref)
            if fixture_type is None or not (fixture_type.needs & _IN_WALL_SERVICES):
                continue
            found = backing_wall(ctx.plan, ctx.model, element, fixture_type)
            if found is None or found[0].tag != bay.wall_tag:
                continue
            half = fixture_type.footprint[0].meters / 2.0
            overlap = (min(found[1] + half, bay.high_m)
                       - max(found[1] - half, bay.low_m))
            if overlap > 1e-9:
                crowding.append((element.tag, overlap))
        tags = (bay.fixture_tag, bay.wall_tag, *(tag for tag, _ in crowding))
        if not crowding:
            out.append(passed(
                "advisory.carrier_bay_conflict",
                f"{bay.fixture_tag}'s carrier bay in {bay.wall_tag} "
                f"({bay.low_m / M_PER_IN:.1f}\"-{bay.high_m / M_PER_IN:.1f}\" along the "
                f"wall) has the cavity to itself", tags))
            continue
        listed = ", ".join(f"{tag} (by {overlap / M_PER_IN:.1f}\")"
                           for tag, overlap in sorted(crowding))
        message = (f"{bay.fixture_tag}'s carrier bay in {bay.wall_tag} "
                   f"({bay.low_m / M_PER_IN:.1f}\"-{bay.high_m / M_PER_IN:.1f}\" along the "
                   f"wall) is overlapped by {listed}, whose services have to reach the same "
                   f"cavity")
        if deep:
            out.append(advisory(
                "advisory.carrier_bay_conflict",
                f"{message} — the wall is {structure.thickness_m / M_PER_IN:.1f}\" deep, so "
                f"they cross BEHIND the frame; say so on the rough-in drawing",
                tags, Result.PASS))
        else:
            out.append(advisory(
                "advisory.carrier_bay_conflict",
                f"{message}, and at {0.0 if structure is None else structure.thickness_m / M_PER_IN:.1f}\" "
                f"of structure the frame fills it — there is nothing to cross through",
                tags, Result.FAIL,
                fix="move one centreline clear of the bay, deepen the wall, or serve the "
                    "other fixture from a different wall"))
    return out


def _axis_length(wall) -> float:
    (x0, y0), (x1, y1) = wall.axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
