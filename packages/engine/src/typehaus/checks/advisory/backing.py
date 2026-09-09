"""Wall backing: is there anything behind the thing that hangs on the wall?

Two checks, and the split is the usual one — a ref that resolves to nothing is an ERROR,
because a typo must not silently delete a band; whether a band *covers* what hangs in front
of it is ADVISORY, because outside one case no residential code requires backing at all.

**What the code actually says.** A handrail or guard carries IRC **Table R301.5**'s 200 lb
concentrated load applied in any direction at any point along the top — adopted by Minnesota
via Minn. Rules ch. 1309 — and the IRC prescribes no attachment detail whatsoever, so the
blocking is discretionary in form and mandatory in effect. Everything else here has no code
behind it: ADA does not reach a private residence, the IRC sets no grab-bar load, and the
250 lb figure people quote is IBC 1607.7, whose one-and-two-family exception drops it back to
the 200 lb handrail case. The best-written spec worth borrowing is California's CRC
R328.1.1 — 2x8 nominal minimum, 32" to 39-1/4" above the floor, flush with the framing — and
borrowing it is a house's decision, not this engine's.

So the verdict here is ADVISORY and the message says whose number it is. This engine does
not dress a preference as code.

**This check grades coverage, not capacity.** Whether a 3/4" plywood band carries a grab bar
is an engineering question and belongs to a named register item (#65), not to a check that
has no load to compute against. The same discipline ``mep.deck_equipment_support`` keeps.

Read off ``framing/carriers.backing_wall``, the same derivation the framing pass uses, so the
wall a band is framed in and the wall a body is graded against cannot drift apart.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, failed, not_applicable, passed
from typehaus.model.placeables import Mount, MountKind
from typehaus.model.spatial import Appliance, Fixture, Furniture
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.backing_panels import (
    BackingBand,
    backing_bands,
    band_face_height_m,
)
from typehaus.resolve.framing.carriers import backing_wall
from typehaus.resolve.model import ResolvedWall

#: How far a fastener may miss the band and still land in it. A bracket hole is drilled to a
#: hole in a plate, not to a laser line, and an authored elevation is a nominal.
_REACH_M = 1.0 * M_PER_IN


#: The three placed-body families that can hang on a wall. Each carries ``type_ref``,
#: ``position`` and ``rotation``; ``Element`` itself declares none of them.
WallMountedBody = Furniture | Fixture | Appliance


def _bodies_and_types(
        ctx: CheckContext) -> Iterator[tuple[WallMountedBody, object, Mount]]:
    """Every wall-mounted body in the plan, with the type that gives it a footprint."""
    catalogs = (
        (Furniture, {item.tag: item for item in ctx.plan.library.furniture_types}),
        (Fixture, {item.tag: item for item in ctx.plan.library.fixture_types}),
        (Appliance, {item.tag: item for item in ctx.plan.library.appliance_types}),
    )
    for storey_tag in ctx.plan.elements:
        for element in ctx.plan.storey_elements(storey_tag):
            for kind, types in catalogs:
                if not isinstance(element, kind):
                    continue
                body_type = types.get(element.type_ref)
                if body_type is None:
                    continue
                mount = element.mount or getattr(body_type, "mount", None)
                if mount is None or mount.kind is not MountKind.WALL:
                    continue
                yield element, body_type, mount


#: Categories that prove a wall was actually framed with a stud cavity.
_STUD_CATEGORIES = frozenset({"stud", "corner", "king", "jack", "cripple"})


def _is_framed(wall: ResolvedWall) -> bool:
    """Whether this wall has a stud cavity a band could be let into.

    Read off the members the framing pass *emitted*, not off the assembly's layer list. A
    body on an 8" concrete wall takes an anchor, not blocking, and reporting "no backing"
    against it would be noise the reader learns to scroll past — but the inverse mistake is
    worse, and this check made it first: an over-eager test called every framed wall in the
    kitchen solid and turned twenty real findings into twenty N/As. ``Result.NOT_APPLICABLE``
    has to be earned from positive evidence, and a wall that emitted no stud is that
    evidence.
    """
    return any(member.category in _STUD_CATEGORIES for member in wall.members)


@check(Tier.ADVISORY, "advisory.wall_backing_present")
def wall_backing_present(ctx: CheckContext) -> list[Finding]:
    """A wall-mounted body wants a band behind it at the height it hangs."""
    bodies = list(_bodies_and_types(ctx))
    if not bodies:
        return [not_applicable(
            "advisory.wall_backing_present",
            "nothing in this plan mounts on a wall, so no body is hanging off one")]
    bands = backing_bands(ctx.plan)
    out: list[Finding] = []
    for body, body_type, mount in bodies:
        found = backing_wall(ctx.plan, ctx.model, body, body_type)
        if found is None:
            # Never a silent skip. ``backing_wall`` matches a body to the wall its back
            # faces within a face tolerance, and a body whose type footprint is its *stand*
            # rather than its hung depth — a 98" display 16 1/2" deep, a curtain rod on
            # 4" returns — squares onto nothing. That is a gap in the evidence, not a
            # verdict, and reporting it is how the gap stays visible.
            out.append(advisory(
                "advisory.wall_backing_present",
                f"{body.tag} mounts on a wall, but no wall in the plan squares onto its "
                f"back within a face of it, so there is no wall to grade backing against",
                (body.tag,), Result.UNKNOWN,
                fix=f"check {body.type_ref}'s footprint depth against how {body.tag} "
                    f"actually hangs, or move it onto its wall"))
            continue
        wall, station = found
        tags = (body.tag, wall.tag)
        if getattr(body_type, "carrier_bay_width", None) is not None:
            # A wall-hung bowl bolts to the steel frame standing in the bay, which carries
            # the whole seated load and is framed by ``framing/carriers.py``. Backing behind
            # it would be a board nothing fastens to.
            out.append(not_applicable(
                "advisory.wall_backing_present",
                f"{body.tag} hangs on an in-wall carrier frame in {wall.tag}, which is what "
                f"carries it — a backing band is not the load path here", tags))
            continue
        if not _is_framed(wall):
            out.append(not_applicable(
                "advisory.wall_backing_present",
                f"{body.tag} hangs on {wall.tag}, which has no framed cavity — a body on a "
                f"solid wall takes an anchor, not blocking", tags))
            continue
        if mount.elevation is None:
            out.append(advisory(
                "advisory.wall_backing_present",
                f"{body.tag} mounts on {wall.tag} but states no mount elevation, so there "
                f"is no height to put a band at", tags, Result.UNKNOWN,
                fix=f"set Mount.elevation on {body.tag}"))
            continue
        low = mount.elevation.meters
        covering = [b for b in bands.get(wall.tag, ())
                    if b.elevation_m - _REACH_M <= low <= b.elevation_m + b.height_m + _REACH_M
                    and _covers_station(b, station, wall)]
        if covering:
            names = ", ".join(sorted(b.tag for b in covering))
            out.append(passed(
                "advisory.wall_backing_present",
                f"{body.tag} hangs at {low / M_PER_IN:.0f}\" on {wall.tag}, backed by "
                f"{names}", tags))
        else:
            out.append(advisory(
                "advisory.wall_backing_present",
                f"{body.tag} hangs at {low / M_PER_IN:.0f}\" on {wall.tag} with no backing "
                f"band behind it. Nothing in the IRC requires one; this is the irreversible "
                f"item, since after the drywall closes it is a demolition", tags, Result.FAIL,
                fix=f"author a WallBacking on {wall.tag} spanning "
                    f"{low / M_PER_IN:.0f}\" above the floor"))
    return out


def _covers_station(band: BackingBand, station: float, wall: ResolvedWall) -> bool:
    """Whether the band's run reaches the station the body sits at."""
    start: float = band.start_m or 0.0
    if band.length_m is None:
        (x0, y0), (x1, y1) = wall.axis
        end = float(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)
    else:
        end = start + band.length_m
    return start - _REACH_M <= station <= end + _REACH_M


@check(Tier.INTEGRITY, "integrity.wall_backing_ref")
def wall_backing_ref(ctx: CheckContext) -> list[Finding]:
    """A band must name a real wall, fit inside it, and mean its own section string."""
    bands = backing_bands(ctx.plan)
    if not bands:
        return [not_applicable("integrity.wall_backing_ref",
                               "this plan authors no WallBacking, so no band names a wall")]
    out: list[Finding] = []
    for wall_tag, wall_bands in sorted(bands.items()):
        wall = ctx.model.wall(wall_tag)
        for band in sorted(wall_bands, key=lambda b: b.tag):
            tags = (band.tag, wall_tag)
            if wall is None:
                out.append(failed(
                    "integrity.wall_backing_ref",
                    f"backing {band.tag} names no wall {wall_tag!r}: the band would be "
                    f"silently dropped and the wall closed with nothing in it", tags))
                continue
            (x0, y0), (x1, y1) = wall.axis
            axis_len = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            start = band.start_m or 0.0
            if start >= axis_len - 1e-9:
                out.append(failed(
                    "integrity.wall_backing_ref",
                    f"backing {band.tag} starts at {start / M_PER_IN:.1f}\" along "
                    f"{wall_tag}, which is only {axis_len / M_PER_IN:.1f}\" long", tags))
                continue
            if band.elevation_m + band.height_m > wall.z1_m - wall.z0_m + 1e-9:
                out.append(failed(
                    "integrity.wall_backing_ref",
                    f"backing {band.tag} tops out at "
                    f"{(band.elevation_m + band.height_m) / M_PER_IN:.1f}\" on a "
                    f"{(wall.z1_m - wall.z0_m) / M_PER_IN:.1f}\" wall", tags))
                continue
            stated = band_face_height_m(band.profile)
            if abs(stated - band.height_m) > 0.5 * M_PER_IN:
                out.append(failed(
                    "integrity.wall_backing_ref",
                    f"backing {band.tag} is authored {band.height_m / M_PER_IN:.1f}\" tall "
                    f"but its {band.profile!r} section is {stated / M_PER_IN:.1f}\" — one of "
                    f"the two is wrong, and an unparsed section falls back to a 2x6 silently",
                    tags))
                continue
            out.append(passed(
                "integrity.wall_backing_ref",
                f"backing {band.tag} on {wall_tag}: {band.height_m / M_PER_IN:.1f}\" of "
                f"{band.profile} at {band.elevation_m / M_PER_IN:.0f}\" above the floor"
                + (f" ({band.purpose})" if band.purpose else ""), tags))
    return out
