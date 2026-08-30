"""Pour-day plumbing checks — every joint nobody can move after the concrete cures.

Sleeve alignment against the fixture's expected drain point, sleeve coverage of every
routed concrete crossing, under-slab bedding cover, footing influence-line clearance, and
the building drain's invert at its exit sleeve. All of them are CODE-tier: an unsleeved
crossing or a mislocated sleeve gets cored after the pour, which is the defect this whole
band exists to prevent.

The geometry derivations live in ``resolve/mep_queries.py`` (``concrete_crossings``); this
module only turns them into findings.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.plumbing_common import _M_TO_FT
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Service
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedSolid

_ALIGNMENT_TOLERANCE_M = 0.0127  # 1/2"
_UNDER_SLAB_COVER_M = 0.0254  # pipe crown clears the slab underside by >= 1" bedding
_SEWER_INVERT_TOLERANCE_M = 0.0127  # 1/2" — cast-in, like the sleeve alignment gate


@check(Tier.CODE, "mep.sleeve_alignment")
def sleeve_alignment(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for sleeve in ctx.model.sleeves:
        if sleeve.serves_fixture is None:
            # A supply riser, a wall crossing, a condensate drop: no fixture, so there is no
            # flange for the sleeve to line up under and nothing here to grade. Their
            # positions are not unchecked — `mep.sleeve_coverage` holds every one of them to
            # a routed run actually passing through it, which is the stronger contract.
            continue
        if sleeve.expected_center is None:
            out.append(_unknown(
                "mep.sleeve_alignment",
                f"sleeve {sleeve.tag} has no resolvable expected drain point "
                f"(serves_fixture={sleeve.serves_fixture})", (sleeve.tag,),
            ))
            continue
        if sleeve.offset_m <= _ALIGNMENT_TOLERANCE_M:
            out.append(_pass(
                "mep.sleeve_alignment",
                f"sleeve {sleeve.tag} is {sleeve.offset_m / M_PER_IN:.2f}\" from its "
                "expected drain point (<= 1/2\" tolerance)", (sleeve.tag,),
            ))
            continue
        dx = (sleeve.expected_center[0] - sleeve.center[0]) / M_PER_IN
        dy = (sleeve.expected_center[1] - sleeve.center[1]) / M_PER_IN
        axis, delta = ("x", dx) if abs(dx) >= abs(dy) else ("y", dy)
        sign = "+" if delta >= 0 else "-"
        out.append(_fail(
            "mep.sleeve_alignment",
            f"sleeve {sleeve.tag} is {sleeve.offset_m / M_PER_IN:.2f}\" off its expected "
            f"drain point — move sleeve {abs(delta):.1f}\" {sign}{axis}", (sleeve.tag,),
        ))
    out.extend(_missing_sleeve_findings(ctx))
    return out


def _is_non_concrete_slab(ctx: CheckContext, solid: ResolvedSolid) -> bool:
    """A ``Slab`` whose assembly is demonstrably not concrete — a deck, not a pour.

    ``Slab`` is the model's only horizontal-sheet element that can sit off its storey datum,
    so it carries laid decking as well as concrete: the porch and breezeway composite decks
    and, since 2026-08-29, RM-M-BATH2's 3/4" plywood tub-deck cap. A **cast-in sleeve is a
    concrete concept** — the whole point of this family is that a sleeve more than 1/2" out
    moves *before the pour*, and there is no pour in a sheet of plywood. Grading a fixture
    over one as needing a sleeve is a FAIL that can only be silenced by authoring a sleeve
    through decking, which would be a lie in the model.

    Deliberately conservative on the unknown case: a slab with **no** authored assembly
    stays in scope. ``SL-SG-FLOOR`` and ``SL-G-STEP-0`` are both like that today, and an
    unassembled slab is far more likely to be an undescribed pour than an undescribed deck.
    """
    if not solid.assembly:
        return False
    assembly = next((a for a in ctx.plan.library.assemblies
                     if a.tag == solid.assembly), None)
    if assembly is None:
        return False
    stack = list(assembly.default_lining) + list(assembly.layers)
    return not any(layer.material_ref == "concrete" for layer in stack)


def _missing_sleeve_findings(ctx: CheckContext) -> list[Finding]:
    """A storey tag alone isn't enough: multiple freestanding structures can share one
    (catlin's sunken-garden balcony slab is also tagged "second") — a fixture only needs a
    sleeve through the specific slab its footprint actually sits on."""
    from shapely.geometry import Point, Polygon

    out: list[Finding] = []
    slabs = [solid for solid in ctx.model.solids
             if solid.category == "slab" and not _is_non_concrete_slab(ctx, solid)]
    served = {(sleeve.serves_fixture, sleeve.host_slab) for sleeve in ctx.model.sleeves
             if sleeve.serves_fixture is not None}
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    for storey in ctx.plan.storeys:
        storey_slabs = [solid for solid in slabs if solid.storey == storey.tag]
        if not storey_slabs:
            continue
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.DRAIN not in fixture_type.needs:
                continue
            point = Point(fixture.position.xy_m)
            host = next((s for s in storey_slabs if Polygon(s.outline).contains(point)), None)
            if host is None:
                continue  # fixture isn't over a structural slab at all
            if (fixture.tag, host.tag) not in served:
                out.append(_fail(
                    "mep.sleeve_alignment",
                    f"drain fixture {fixture.tag} sits above structural slab {host.tag} "
                    "with no sleeve serving it", (fixture.tag, host.tag),
                ))
    return out


@check(Tier.CODE, "mep.sleeve_coverage")
def sleeve_coverage(ctx: CheckContext) -> list[Finding]:
    """Every concrete crossing of a routed pipe must land in a cast-in sleeve, and every
    sleeve must have a crossing (or, pre-routing, a served fixture) to justify it.

    An unsleeved crossing is the pour-day defect this whole pass exists to prevent: the
    concrete cures and the run gets cored. A sleeve with no routed run near it is graded
    UNKNOWN rather than FAIL while its plumbing is not yet routed — the fixture-convention
    ``mep.sleeve_alignment`` still guards its position."""
    from typehaus.resolve.mep import concrete_crossings

    cid = "mep.sleeve_coverage"
    out: list[Finding] = []
    crossings = concrete_crossings(ctx.model)
    claimed: set[str] = set()
    for crossing in crossings:
        if crossing["sleeve"] is not None:
            claimed.add(crossing["sleeve"])
            out.append(_pass(
                cid, f"run {crossing['run']} crosses {crossing['host']} through sleeve "
                     f"{crossing['sleeve']}", (crossing["run"], crossing["sleeve"])))
        else:
            x, y = crossing["point"]
            out.append(_fail(
                cid, f"run {crossing['run']} (Ø{crossing['diameter_m'] / M_PER_IN:.1f}\") "
                     f"passes through {crossing['host_category']} {crossing['host']} at "
                     f"({x * _M_TO_FT:.1f}', {y * _M_TO_FT:.1f}') with no cast-in sleeve "
                     "— it gets cored after the pour",
                (crossing["run"], crossing["host"])))
    # A sleeve is only "stale" against a routed run of its own purpose family — a cold
    # supply serving FX-1 says nothing about where FX-1's *drain* sleeve belongs.
    purpose_systems = {"drain": ("drain",), "vent": ("vent",),
                       "water_cold": ("water_cold",), "water_hot": ("water_hot",)}
    routed_by_system: dict[str, set[str]] = {}
    for run in ctx.model.pipe_runs:
        if run.z_m is not None:
            routed_by_system.setdefault(run.system, set()).update(run.serves)
    for sleeve in ctx.model.sleeves:
        if sleeve.tag in claimed:
            continue
        if (sleeve.host_category == "footing" and sleeve.center_z_m is not None
                and sleeve.center_z_m < sleeve.z0_m - 1e-6):
            # An under-footing protection sleeve (IRC P2604): the pipe passes *below* the
            # bearing plane, so `concrete_crossings` — which walks through-crossings of a
            # solid's own z-band — structurally cannot ever claim it, and reporting UNKNOWN
            # here would be permanent noise. `mep.footing_clearance` is the check that
            # requires these and matches run against sleeve; it owns them.
            continue
        routed_serves: set[str] = set()
        for system in purpose_systems.get(sleeve.purpose, ()):
            routed_serves |= routed_by_system.get(system, set())
        if sleeve.serves_fixture is not None and sleeve.serves_fixture in routed_serves:
            out.append(_fail(
                cid, f"sleeve {sleeve.tag} is cast into {sleeve.host_slab} but the routed "
                     f"run serving {sleeve.serves_fixture} never passes through it — a "
                     "stale sleeve position or a mis-routed run",
                (sleeve.tag, sleeve.host_slab)))
        else:
            out.append(_unknown(
                cid, f"sleeve {sleeve.tag} has no routed run to check against yet "
                     f"(serves {sleeve.serves_fixture})", (sleeve.tag,)))
    return out


@check(Tier.CODE, "mep.under_slab_burial")
def under_slab_burial(ctx: CheckContext) -> list[Finding]:
    """A drain running under a slab must actually clear its underside — a crown poured
    into the bottom inch of the slab is a void former, not a pipe with bedding."""
    from shapely.geometry import LineString, Polygon

    cid = "mep.under_slab_burial"
    # Only slabs bearing on grade: below a slab-on-grade is soil, and a pipe there is
    # buried with bedding. Below a suspended structural deck is a room — a ceiling-hung
    # pipe under it needs no cover. A slab is suspended when any resolved room of a lower
    # storey overlaps its footprint.
    storey_elevation = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    room_polys = [(storey_elevation.get(room.storey, 0.0), Polygon(room.clear_face))
                  for room in ctx.model.rooms if len(room.clear_face) >= 3]
    slabs = []
    for s in ctx.model.solids:
        if s.category != "slab" or len(s.outline) < 3:
            continue
        footprint = Polygon(s.outline)
        suspended = any(elev < s.z0_m - 0.1 and poly.intersects(footprint)
                        for elev, poly in room_polys)
        if not suspended:
            slabs.append((s, footprint))
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system != "drain" or run.z_m is None:
            continue
        worst: tuple[float, str] | None = None
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            if ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 < 1e-6:
                continue  # vertical drops are the sleeved crossings
            crown = max(run.z_m[i], run.z_m[i + 1]) + run.diameter_m / 2.0
            for slab, footprint in slabs:
                if not LineString((a, b)).intersects(footprint):
                    continue
                if crown >= slab.z1_m - 1e-6:
                    continue  # above the slab — not an under-slab segment
                gap = slab.z0_m - crown
                if worst is None or gap < worst[0]:
                    worst = (gap, slab.tag)
        if worst is None:
            continue  # this run has no under-slab segment; nothing here to grade
        gap, slab_tag = worst
        if gap >= _UNDER_SLAB_COVER_M - 1e-9:
            out.append(_pass(
                cid, f"run {run.tag}'s crown clears {slab_tag}'s underside by "
                     f"{gap / M_PER_IN:.1f}\" (>= {_UNDER_SLAB_COVER_M / M_PER_IN:.0f}\")",
                (run.tag, slab_tag)))
        else:
            out.append(_fail(
                cid, f"run {run.tag}'s crown sits {gap / M_PER_IN:.1f}\" below "
                     f"{slab_tag}'s underside — under the "
                     f"{_UNDER_SLAB_COVER_M / M_PER_IN:.0f}\" bedding cover it needs",
                (run.tag, slab_tag)))
    return out


class _Pour:
    """One continuous concrete pour: the footings that touch, measured as one."""

    def __init__(self, members):
        self.tags = frozenset(m.tag for m in members)
        self.tag = " + ".join(sorted(self.tags))
        # The shallowest bearing plane in the group governs: it is the one a pipe below the
        # group is closest to, and the one whose influence line reaches furthest.
        self.z0_m = min(m.z0_m for m in members)


def _footing_pours(solids, polygon_type):
    """Group footing solids into pours, unioning the footprints that abut.

    Same bearing elevation and touching in plan is the test — two footings at different
    depths meeting at a step are two pours, and each keeps its own edge.
    """
    from shapely.ops import unary_union

    remaining = [(s, polygon_type(s.outline)) for s in solids]
    pours = []
    while remaining:
        seed, seed_poly = remaining.pop()
        members, shapes = [seed], [seed_poly]
        grew = True
        while grew:
            grew = False
            for candidate in list(remaining):
                solid, poly = candidate
                if abs(solid.z0_m - seed.z0_m) > 1e-6:
                    continue
                if any(poly.distance(shape) <= 1e-6 for shape in shapes):
                    members.append(solid)
                    shapes.append(poly)
                    remaining.remove(candidate)
                    grew = True
        pours.append((_Pour(members), unary_union(shapes)))
    return pours


def _threading_sleeve(ctx: CheckContext, footing, run, index: int, seg):
    """The protection sleeve `run`'s segment `index` actually passes through, or None.

    A sleeve is the hole a pipe goes through, so "protected" has to mean *this* pipe is in
    *that* hole — in plan and in section both. Proximity alone is not the test and used to
    be: the check asked only that some sleeve on the pour sit within 0.3 m of the segment,
    which let SP-GF-W-HYD grade a PASS for a run that never came nearer than 8" to it and
    ran parallel to the footing rather than across it. The bore it drew went through
    concrete with nothing in it (→ houses/catlin/plan/mep.py, deleted 2026-08-15).

    Two conditions, both cheap:

    * plan — the segment passes within the sleeve's own radius of its centre, i.e. the pipe
      is inside the formed hole rather than beside it. The radius is the honest tolerance
      here because it is the physical one; 0.3 m was a guess an inch-scale defect hid in.
    * section — the sleeve's cast centreline is within a sleeve diameter of the run's
      elevation at that station, interpolated along the segment. A sleeve at the right plan
      point but the wrong depth is the other way a block-out misses its pipe, and it is the
      failure `mep.sewer_exit_invert` exists to grade precisely; catching it grossly here
      costs nothing.

    Footings abutting at one bearing elevation are measured as one pour, so a sleeve
    authored on any member of `footing.tags` is a sleeve in this concrete.
    """
    from shapely.geometry import Point

    a, b = run.path[index], run.path[index + 1]
    z_a, z_b = run.z_m[index], run.z_m[index + 1]
    for sleeve in ctx.model.sleeves:
        if sleeve.host_slab not in footing.tags or sleeve.center_z_m is None:
            continue
        centre = Point(sleeve.center)
        if seg.distance(centre) > sleeve.sleeve_d_m / 2.0 + 1e-9:
            continue
        # The run's elevation where the sleeve sits: project the centre onto the segment and
        # interpolate. A repeated vertex (a vertical drop) has no length to project along,
        # so it takes the deeper of its two ends — the same reading `invert` uses above.
        span = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        if span <= 1e-12:
            z_at = min(z_a, z_b)
        else:
            t = ((sleeve.center[0] - a[0]) * (b[0] - a[0])
                 + (sleeve.center[1] - a[1]) * (b[1] - a[1])) / span
            t = min(1.0, max(0.0, t))
            z_at = z_a + (z_b - z_a) * t
        # One sleeve diameter of slack: the block-out is formed two pipe sizes over, so a
        # pipe genuinely inside it is within a fraction of this, and the slack absorbs the
        # invert/centreline half-diameter that separates a run's authored z from the
        # sleeve's without admitting a sleeve at a different depth entirely.
        if abs(z_at - sleeve.center_z_m) <= sleeve.sleeve_d_m:
            return sleeve
    return None


def _near_miss(ctx: CheckContext, footing, run, index: int, seg) -> str:
    """A clause naming the nearest sleeve on this pour that failed to thread the run.

    Without it a defective sleeve reads as a missing one, and the two want opposite fixes:
    an absent sleeve gets authored, a misaligned one gets moved or deleted. Empty when the
    pour carries no sleeve at all — then "no protection sleeve" is already the whole story.
    """
    from shapely.geometry import Point

    nearest = min(
        (s for s in ctx.model.sleeves if s.host_slab in footing.tags),
        key=lambda s: seg.distance(Point(s.center)), default=None)
    if nearest is None:
        return ""
    gap = seg.distance(Point(nearest.center))
    return (f" — sleeve {nearest.tag} is on this pour but the run passes "
            f"{gap / M_PER_IN:.0f}\" from its bore, so it protects nothing")


@check(Tier.CODE, "mep.footing_clearance")
def footing_clearance(ctx: CheckContext) -> list[Finding]:
    """A pipe deeper than a footing's bearing plane must stay outside its 45° influence
    line: lateral offset >= how far below the footing bottom the pipe sits. A crossing
    *through* the footing is legal only via a sleeve (mep.sleeve_coverage owns that).

    Abutting footings at the same bearing elevation are measured as one pour
    (``_footing_pours``). A strip footing is split into several ``Footing`` elements
    wherever the wall above it is — at a stem gap under a door, say — and the joints that
    creates are construction joints in continuous concrete, not free edges. Measuring the
    influence line off one would fail a pipe for being near the middle of a footing.
    """
    from shapely.geometry import LineString, Polygon

    cid = "mep.footing_clearance"
    footings = _footing_pours([s for s in ctx.model.solids
                               if s.category == "footing" and len(s.outline) >= 3], Polygon)
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.z_m is None:
            continue
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            seg = LineString((a, b)) if ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) > 1e-12 \
                else LineString((a, (a[0] + 1e-9, a[1])))
            invert = min(run.z_m[i], run.z_m[i + 1])
            for footing, footprint in footings:
                depth_below = footing.z0_m - invert
                if depth_below <= 1e-9:
                    continue  # pipe is above the bearing plane — no influence
                if seg.intersects(footprint):
                    # Passing under (or through) the footing: legal per IRC P2604 only
                    # inside a protection sleeve / relieving arch authored on the footing.
                    sleeve = _threading_sleeve(ctx, footing, run, i, seg)
                    if sleeve is not None:
                        out.append(_pass(
                            cid, f"run {run.tag} passes under footing {footing.tag} "
                                 f"through protection sleeve {sleeve.tag} (IRC P2604)",
                            (run.tag, footing.tag, sleeve.tag)))
                    else:
                        out.append(_fail(
                            cid, f"run {run.tag} segment {i} passes under footing "
                                 f"{footing.tag} {depth_below / M_PER_IN:.0f}\" below its "
                                 "bearing plane with no protection sleeve (IRC P2604)"
                                 + _near_miss(ctx, footing, run, i, seg),
                            (run.tag, footing.tag)))
                    continue
                # ``.boundary``, not ``.exterior``: a pour is a union, which can come back as
                # a MultiPolygon when two footings meet at a corner only, and that has no
                # ``exterior``. The boundary is also the more correct edge — a hole through a
                # pour is as much an edge as its outside is.
                distance = seg.distance(footprint.boundary)
                if distance + 1e-9 < depth_below:
                    sleeve = _threading_sleeve(ctx, footing, run, i, seg)
                    if sleeve is not None:
                        out.append(_pass(
                            cid, f"run {run.tag} encroaches on footing {footing.tag}'s "
                                 f"influence line inside protection sleeve {sleeve.tag} "
                                 "(IRC P2604)", (run.tag, footing.tag, sleeve.tag)))
                        continue
                    out.append(_fail(
                        cid, f"run {run.tag} segment {i} sits "
                             f"{depth_below / M_PER_IN:.0f}\" below footing "
                             f"{footing.tag}'s bearing plane only "
                             f"{distance / M_PER_IN:.0f}\" away — inside its 45° "
                             "influence line; deepen the footing or move the run"
                             + _near_miss(ctx, footing, run, i, seg),
                        (run.tag, footing.tag)))
    if not out:
        routed = [r for r in ctx.model.pipe_runs if r.z_m is not None]
        if routed:
            out.append(_pass(cid, f"{len(routed)} routed runs all clear every footing's "
                                  "45° influence line", ()))
    return out


@check(Tier.CODE, "mep.sewer_exit_invert")
def sewer_exit_invert(ctx: CheckContext) -> list[Finding]:
    """The building drain's invert at every cast-in horizontal sleeve must match the
    centerline cast there — the one joint nobody can move after the pour.

    Two kinds of crossing qualify, because the foundation's own geometry decides which one a
    house gets. Where the drain leaves *through* concrete, `concrete_crossings` finds it. But
    where the sewer connection sits below the slab — deep, as cold climates bury them — the
    walls have already stopped at the slab and the drain leaves *under* a footing inside a
    protection sleeve (IRC P2604). That is not a through-crossing, so it has to be matched by
    proximity instead, with the invert interpolated along the run at the sleeve's plan point.
    """
    from typehaus.resolve.mep import concrete_crossings

    cid = "mep.sewer_exit_invert"
    out: list[Finding] = []
    exits = [s for s in ctx.model.sleeves
             if s.axis == "horizontal" and s.purpose == "drain"]
    if not exits:
        return []
    # Drain crossings only. ``concrete_crossings`` walks raceways too, and a dict keyed on
    # sleeve tag lets whichever crossing comes last win — so a power conduit passing near a
    # sewer sleeve could replace the drain that actually threads it and be graded as one.
    crossings_by_sleeve = {c["sleeve"]: c for c in concrete_crossings(ctx.model)
                           if c["sleeve"] is not None and c["system"] == "drain"}
    for sleeve in exits:
        if sleeve.center_z_m is None:
            out.append(_unknown(cid, f"horizontal sleeve {sleeve.tag} authors no "
                                     "center_elevation", (sleeve.tag,)))
            continue
        crossing = crossings_by_sleeve.get(sleeve.tag)
        if crossing is None:
            crossing = _under_footing_crossing(ctx, sleeve)
        if crossing is None:
            out.append(_unknown(cid, f"no routed drain run reaches exit sleeve "
                                     f"{sleeve.tag} yet", (sleeve.tag,)))
            continue
        run_tag = crossing["run"]
        # The crossing's z is the pipe *invert* at the wall; the sleeve is set to the
        # pipe centerline, half a diameter above it.
        z_at = crossing["z_m"] + crossing["diameter_m"] / 2.0
        delta = z_at - sleeve.center_z_m
        if abs(delta) <= _SEWER_INVERT_TOLERANCE_M:
            out.append(_pass(
                cid, f"drain {run_tag} meets exit sleeve {sleeve.tag} within "
                     f"{abs(delta) / M_PER_IN:.2f}\" of its cast centerline",
                (run_tag, sleeve.tag)))
        else:
            out.append(_fail(
                cid, f"drain {run_tag} arrives {abs(delta) / M_PER_IN:.1f}\" "
                     f"{'above' if delta > 0 else 'below'} exit sleeve {sleeve.tag}'s "
                     "cast centerline", (run_tag, sleeve.tag)))
    return out


def _under_footing_crossing(ctx: CheckContext, sleeve) -> dict | None:
    """Match an under-footing protection sleeve to the drain run threading it.

    Mirrors how `mep.footing_clearance` claims the same sleeve — nearest drain segment whose
    plan line passes within the sleeve's own radius of its center — and interpolates the
    run's invert to that point so the comparison is against the pipe where the sleeve is,
    not at whichever vertex happens to be closest.
    """
    from shapely.geometry import LineString, Point

    if sleeve.host_category != "footing" or sleeve.center_z_m is None:
        return None
    center = Point(sleeve.center)
    reach = max(sleeve.sleeve_d_m, 0.05)
    best: tuple[float, dict] | None = None
    for run in ctx.model.pipe_runs:
        if run.system != "drain" or run.z_m is None:
            continue
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            span = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            if span < 1e-9:
                continue  # a vertical drop threads no horizontal sleeve
            seg = LineString((a, b))
            gap = seg.distance(center)
            if gap > reach or (best is not None and gap >= best[0]):
                continue
            t = min(1.0, max(0.0, seg.project(center) / span))
            z_at = run.z_m[i] + (run.z_m[i + 1] - run.z_m[i]) * t
            best = (gap, dict(run=run.tag, host=sleeve.host_slab, host_category="footing",
                              point=sleeve.center, z_m=z_at,
                              diameter_m=run.diameter_m, sleeve=sleeve.tag))
    return best[1] if best is not None else None
