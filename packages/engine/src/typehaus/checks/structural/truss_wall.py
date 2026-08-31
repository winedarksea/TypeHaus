"""Does a truss wall's outie window actually land on wood? (→ 12, → 11 §Framing)

Its own module rather than a function in ``checks.py`` for the reason that file's siblings
already exist: one question, one file, and ``checks.py`` is at its 500-line limit.

The question is narrow and the answer is a fact about the resolved model, not about the
authored plan: an outie window sits in the truss plane with its nailing flange bearing on the
outriggers and on the head/sill blocking between them, and nowhere else. A rough-opening jamb
with no wood within a flange's width of it is a window screwed to four inches of foam.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable
from typehaus.resolve.framing.tables import DEFAULT_SPACING

#: A girt course's height on the wall — a 2x4 laid flat. The same 3-1/2" ``GirtFrame``
#: derives from the member's own cross-section; named here so this module does not have to
#: build a frame to ask where the courses are.
_GIRT_FACE_M = 3.5 * 0.0254


@check(Tier.STRUCTURAL, "structural.truss_wall_opening_support")
def truss_wall_opening_support(ctx: CheckContext) -> list[Finding]:
    """Every rough-opening jamb in a truss wall must reach an outrigger its flange can bear on.

    An outie window sits in the truss plane, not the stud plane: its nailing flange lands on
    the outriggers and on the head/sill blocking between them, and nowhere else. So a jamb
    with no wood within a flange's width of it is a window screwed to 4" of foam.

    ``resolve/framing/truss_wall.py`` already ADDS a jamb outrigger wherever the 16" field
    grid misses — this check is not a duplicate of that, it is what keeps the answer true.
    It reads the resolved members, so it fails if the emitter ever declines to add one (a
    band too short to hold the pack, a jamb outside the mitred extent), and it is the
    difference between a table in a plan somebody read once and a fact the build re-derives.

    Advisory, like everything else in this module: a flange bearing is a fastening detail,
    not an engineered connection.
    """
    from typehaus.resolve.framing.truss_wall import (
        FLANGE_BEARING,
        nearest_bearing_gap,
        truss_kind,
        truss_layer_name,
    )

    bearing_m = FLANGE_BEARING.meters
    out: list[Finding] = []
    supported: list[str] = []
    for wall in ctx.model.walls:
        layer_name = truss_layer_name(ctx.plan, wall.assembly)
        if layer_name is None:
            continue
        openings = [op for op in ctx.model.openings if op.host_wall == wall.tag]
        if not openings:
            continue
        spans = _truss_stations(wall, layer_name,
                                truss_kind(ctx.plan, wall.assembly) == "girt")
        if spans is None:
            continue
        for opening in openings:
            half = opening.width_m / 2.0
            z0 = wall.base_ref_z_m + opening.sill_m
            z1 = z0 + opening.height_m
            gaps = [nearest_bearing_gap(opening.center_along_m + side * half, spans, z0, z1)
                    for side in (-1.0, 1.0)]
            worst = max((found[0] for found in gaps if found is not None), default=None)
            if worst is None or worst > bearing_m + 1e-9:
                out.append(_advisory(
                    "structural.truss_wall_opening_support",
                    f"outie window {opening.tag} in truss wall {wall.tag}: an RO jamb is "
                    f"{(worst / 0.0254) if worst is not None else float('inf'):.2f}\" from "
                    f"the nearest outrigger face, past the "
                    f"{FLANGE_BEARING.inches:.2f}\" its nailing flange bears over",
                    (opening.tag, wall.tag), Result.FAIL,
                    fix_hint=("move the RO onto the 16\" outrigger grid, or check why "
                              "resolve/framing/truss_wall.py declined to add a jamb "
                              "outrigger over the jack at this opening"),
                ))
            else:
                supported.append(opening.tag)
    if supported:
        out.append(_advisory(
            "structural.truss_wall_opening_support",
            f"{len(supported)} outie window/door jamb pair(s) in truss walls bear on an "
            f"outrigger within {FLANGE_BEARING.inches:.2f}\"",
            tuple(sorted(supported)), Result.PASS,
        ))
    return out


@check(Tier.STRUCTURAL, "structural.girt_course_spacing")
def girt_course_spacing(ctx: CheckContext) -> list[Finding]:
    """No realised gap between two girt courses may exceed the band's own authored spacing.

    Pure internal consistency, and that is exactly why it is worth having: the courses are
    not a list somebody typed, they are a module plus three edge rules
    (``resolve/framing/furring.course_elevations``), and an edge rule is where a layout
    silently opens a bay. The 32" module went in with a +3" phase candidate that left one
    35" bay on one wall, in a band authored at 32" — nothing in the model would have said
    so, because every course was where the algorithm meant to put it.

    Read off the RESOLVED courses, not re-derived from the spec, so it grades what was
    framed. The cladding fastener schedule is what cares: a PBR panel is screwed to these
    courses and its purlin-span table is read at the band's authored spacing.

    Advisory, like the rest of this module: a nailer spacing is a fastening detail against a
    manufacturer's table, not an engineered connection.
    """
    from typehaus.resolve.framing.furring import course_elevations
    from typehaus.resolve.framing.truss_wall import truss_girt_bands

    out: list[Finding] = []
    graded: list[str] = []
    for wall in ctx.model.walls:
        bands = truss_girt_bands(ctx.plan, wall.assembly)
        if bands is None:
            continue
        spec = bands[1].framing
        if spec is None:  # unreachable: truss_girt_bands reads the spec to select the band
            continue
        spacing = (spec.spacing or DEFAULT_SPACING).meters
        elevations = course_elevations(wall, spec, _GIRT_FACE_M)
        worst = max(((b - a, a) for a, b in zip(elevations, elevations[1:], strict=False)),
                    default=(0.0, 0.0))
        if worst[0] > spacing + 1e-6:
            out.append(_advisory(
                "structural.girt_course_spacing",
                f"girt wall {wall.tag}: {worst[0] / 0.0254:.2f}\" between the course at "
                f"{(worst[1] - wall.z0_m) / 0.0254:.2f}\" above the wall base and the one "
                f"over it, in a band authored at {spacing / 0.0254:.0f}\" o.c.",
                (wall.tag,), Result.FAIL,
                fix_hint=("adjust the band's course_offset — an edge rule (the starter, the "
                          "top course, the rake clearance) has opened a bay wider than the "
                          "module")))
        else:
            graded.append(wall.tag)
    if not graded and not out:
        return [not_applicable(
            "structural.girt_course_spacing",
            "no wall in the plan carries a girt band (a pair of FURRING layers with "
            'standoff="block"), so there are no nailer courses to space')]
    if graded:
        out.append(_advisory(
            "structural.girt_course_spacing",
            f"{len(graded)} girt wall(s): every course-to-course gap is within the band's "
            "own authored spacing",
            tuple(sorted(graded)), Result.PASS))
    return out


def _truss_stations(wall: object, layer_name: str, girt: bool = False
                    ) -> list[tuple[float, float, float, float]] | None:
    """Plan spans of everything in one truss wall's band a window flange can bear on.

    Measured off the band's own centreline, the same datum the emitter placed the members
    on, so the check cannot drift from the geometry by re-deriving it from the wall axis.
    Each span carries its elevation band too, so a member cut around the very opening being
    measured is not counted as wood at that opening's jamb.

    **What counts differs by which truss the wall is**, and only by that.

    On a Swinburne wall the field outriggers themselves are jamb bearing — they are vertical,
    16" o.c., and a window lands on whichever two it falls between — so the field prefix,
    the jamb outriggers and the jamb fillers all count, each at its OWN width: a two-ply
    filler is 3" of wood and reading it as 1-1/2" would report a gap that is not there.

    On a girt wall the field courses are HORIZONTAL and cannot bear a jamb at all — they run
    across the wall, are cut a post's width clear of every RO, and a window falls *between*
    two of them, not beside them. The bearing there is the pair of jamb POSTS the girt frame
    stands at each RO edge, in the OUTER band, which is the mount plane. The outer band's
    head and sill courses are read too, and cost nothing either way: they sit entirely above
    the head and below the sill, so ``nearest_bearing_gap``'s elevation filter drops them
    from every jamb measurement it is actually asked to make.

    And the width is read off the right axis for each: an outrigger stands ON EDGE, so its
    plan width is the 1-1/2" face; a girt jamb post is laid FLAT, so its plan width is the
    3-1/2" one. Taking ``width_m`` for both would report a 3-1/2" post as 1-1/2" of wood and
    fail an opening that is fully supported.
    """
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.framing.solver import band_axis
    from typehaus.resolve.framing.truss_wall import (
        FILLER_CATEGORY,
        JAMB_PREFIX,
        LADDER_CATEGORY,
    )
    from typehaus.resolve.geometry import length, sub, unit

    band = next((layer for layer in wall.layers  # type: ignore[attr-defined]
                 if layer.name == layer_name and layer.polygon), None)
    if band is None:
        return None
    start, end = band_axis(wall.axis, band.polygon)  # type: ignore[attr-defined]
    if length(sub(end, start)) <= 1e-9:
        return None
    direction = unit(sub(end, start))
    jamb_prefix = f"{JAMB_PREFIX}{layer_name}-" if girt else JAMB_PREFIX
    ladder_prefix = f"ladder-head-{layer_name}-", f"ladder-sill-{layer_name}-"
    spans: list[tuple[float, float, float, float]] = []
    for member in wall.members:  # type: ignore[attr-defined]
        if girt:
            bears = (member.child_key.startswith(jamb_prefix)
                     or (member.category == LADDER_CATEGORY
                         and member.child_key.startswith(ladder_prefix)))
        else:
            bears = (member.child_key.startswith(f"strapping-{layer_name}-")
                     or member.child_key.startswith(jamb_prefix)
                     or member.category == FILLER_CATEGORY)
        if not bears:
            continue
        station = ((member.p0[0] - start[0]) * direction[0]
                   + (member.p0[1] - start[1]) * direction[1])
        if member.p0 != member.p1:
            # A head or sill course runs ALONG the wall, so its plan span is its own two
            # ends and not a cross-section about ``p0``. Reading it the vertical way put a
            # phantom 3-1/2" of wood at one RO corner and none at the other.
            far = ((member.p1[0] - start[0]) * direction[0]
                   + (member.p1[1] - start[1]) * direction[1])
            spans.append((min(station, far), max(station, far),
                          member.z0_m, member.z1_m))
            continue
        section = cross_section(member.profile)
        half = (section.depth_m if girt else section.width_m) / 2.0
        spans.append((station - half, station + half, member.z0_m, member.z1_m))
    return sorted(spans) or None
