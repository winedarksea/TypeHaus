"""Whether an authored MEP route is *buildable*, not whether it is the shortest.

The engine has no router and says so (``model/mep.py``): every pipe, duct and raceway is a
polyline somebody drew. That is a deliberate choice — an autorouter that does not know about
the trades' sequencing, the electrician's preference for a straight pull, or the fact that a
drain has to fall, would produce confident nonsense. But it leaves a gap: a drawn route is
graded by nothing at all, so the difference between "this is the only way round" and "this
was drawn on the wrong line" is invisible.

``mep.run_over_void`` closes the first and worst half of that gap. A run's plan polyline may
not cross a ``FloorSystem`` deck void — a stairwell, a chase, a two-storey space — unless the
crossing sub-segment lies inside a wall, where there is framing to strap to. Everywhere else
over a void there is nothing but air: no joist, no deck, no bay, and no way to hang the pipe
or reach it again once the drywall is up.

``deck_voids`` has been resolved since the stair work (``resolve/floors.py``) and consumed by
the stair and egress checks. Nothing in ``checks/mep/`` had ever asked, and nothing else could
have caught this: ``integrity.element_above_roof`` only looks up, ``mep.duct_joist_bay`` only
fires on ``JOIST_BAY`` routing, and a ``ConduitRun`` carries no ``floor_ref`` at all, so it
draws wherever it is authored.

Two design points, both learned from real data rather than reasoned from first principles:

**The void is buffered inward 1".** A run *along* a trimmer line shares its coordinate with
the void's edge, and an unbuffered test reads that as unsupported when the trimmer is exactly
the thing it straps to. An inch is smaller than any framing member and larger than any
coordinate noise.

**A run is matched to a floor by ELEVATION, not by storey.** ``resolve/mep.py``'s
``_containing_floor`` matches a duct to a floor on its own storey, which is right for asking
which joist bay it occupies and wrong here. A ``main``-storey run in the ceiling plane at
+9'-2" is inside the *second* storey's floor structure, whose deck tops out at +10'-0"; the
hole it can fall through is ``FS-S-WEST``'s, and ``FS-M-STAIR`` — filed on ``main``, decked at
+0'-0" — is nine feet below its feet.

Storey alone gets this wrong in both directions, and catlin has a live case of each. Grading
only the run's own storey misses ``CD-M-DATA-KITCH``. Grading its storey *and the one above*
overshoots: ``DU-M-ERV-R-KITCH`` sits at +9'-2" on ``second`` and would be measured against
``FS-ATTIC``'s stairwell eleven feet over its head, which is a finding about nothing. So the
test is the physical one — a segment is graded against a floor when its own z-range overlaps
that floor's structure: from the **bottom of that floor's own joists**, which the model
already carries, up to :data:`ON_DECK_FT` above its decking.

The lower edge is derived rather than dialled for a reason a constant got wrong. Catlin's
basement ceiling carries four runs at -1'-6" to -1'-7 3/8" that cross the stairwell in plan —
``CD-B-KITCHEN``, ``CD-B-DATA-MEDIA``, ``DU-B-ERV-R-PLAY``, ``DU-B-ERV-R-BATH``.
``FS-M-STAIR``'s joists stop at -0'-11 7/8", so those runs are *below* the floor, hanging in
the room. Whether a duct at that height fouls the stair's headroom is a real question and a
different one — this check has no per-room ceiling plane to answer it with, which is the same
reason ``run_route_efficiency`` refuses the "run through open volume" test — and a band
generous enough to catch them answers it badly, by calling every basement-ceiling run a
void-spanner. The joist line is where "in this floor" honestly stops.

The tier is ADVISORY, not CODE. No IRC section says "do not run conduit across a stairwell";
it is a buildability rule, and there is no citation to hang a ``PermitItemSpec`` on. But
``CheckReport.counts()`` counts any ``Result.FAIL`` regardless of severity, so an ADVISORY FAIL
still breaks a 0-FAIL gate — which is the intended weight.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import MultiLineString, Polygon

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

_M_TO_FT = 3.280839895013123

#: How far a deck void is shrunk before a run is tested against it. A run laid along the
#: trimmer that frames the opening shares the opening's own coordinate; without this it reads
#: as spanning air when it is in fact strapped to the member that makes the edge.
VOID_BUFFER_M = 0.0254  # 1 inch

#: Crossings shorter than this are not reported. A route that clips a void corner by an inch
#: is a rounding artifact of where the polyline's vertex landed, not a foot of unsupported
#: pipe, and a check that reports it teaches the reader to ignore the check.
MIN_SPAN_FT = 0.5

#: How far *above* the decking a run still counts as riding on this floor. The band's lower
#: edge is not a constant at all — it is the floor's own joists (see :func:`_voided_floors`),
#: because "in this floor's structure" is a fact the model already carries. Only the top needs
#: a number, and this is it: a raceway strapped to the deck sits an inch or two off it
#: (``CD-A-DATA-NE`` rides 6" above the attic floor), and a run more than a foot up is in the
#: room above, not on the deck.
ON_DECK_FT = 1.0


def _wall_cover(ctx: CheckContext, storeys: set[str]) -> Any:
    """The union of every wall layer polygon on the named storeys — "somewhere to strap to".

    Layer polygons rather than the axis, because the question is physical: is there framing
    under this foot of pipe. A 5 1/2" stud bay is 5 1/2" of support and the axis is a line
    with no width at all.

    Built through :mod:`typehaus.resolve.overlay` rather than a bare ``unary_union``: the
    published web app runs GEOS 3.12.1, where an overlay of many nearly-collinear wall
    polygons without a grid size is fatal rather than merely imprecise.
    """
    from typehaus.resolve.overlay import union_all

    polygons = [Polygon(layer.polygon)
                for wall in ctx.model.walls if wall.storey in storeys
                for layer in wall.layers
                if len(layer.polygon) >= 3]
    valid = [poly for poly in polygons if poly.is_valid and not poly.is_empty]
    return union_all(valid) if valid else None


def _voided_floors(ctx: CheckContext) -> list[tuple[Any, tuple[float, float], list[Any]]]:
    """Every floor that has a hole in it: ``(floor, (band low, band high), [void polygons])``.

    The voids are buffered inward — see :data:`VOID_BUFFER_M`. The band runs from the bottom
    of the floor's own joists to :data:`ON_DECK_FT` above its decking; a floor that resolved
    no members falls back to its deck, which is the conservative reading — nothing hangs below
    a structure the model does not describe.
    """
    out = []
    for floor in ctx.model.floors:
        shrunk = [poly for poly in
                  (Polygon(ring).buffer(-VOID_BUFFER_M)
                   for ring in (floor.deck_voids or ()) if len(ring) >= 3)
                  if not poly.is_empty]
        if not shrunk:
            continue
        joists = [member.z0_m for member in floor.members if member.z0_m is not None]
        low = min(joists) if joists else floor.deck_z0_m
        out.append((floor, (low, floor.deck_z1_m + ON_DECK_FT / _M_TO_FT), shrunk))
    return out


def _runs(ctx: CheckContext) -> list[tuple[str, str, tuple[tuple[float, float], ...],
                                           tuple[float, ...]]]:
    """Every routed thing, as ``(kind, tag, plan path, per-vertex z)``.

    No storey: which floor a run is *in* is decided by elevation here, not by filing (see the
    module note), so carrying the storey would only invite something to start reading it.

    Pipe, duct and raceway together: the void does not care which trade drew the line, and
    three near-identical loops would be three places for the rule to drift. A raceway's z is
    reconstructed by :func:`~typehaus.takeoff.runs.conduit_vertex_z`, which owns the one
    reading of "a ConduitRun rises at its last point".
    """
    from typehaus.takeoff.runs import conduit_vertex_z

    out = []
    for run in ctx.model.pipe_runs:
        z = tuple(run.z_m) if run.z_m and len(run.z_m) == len(run.path) else ()
        out.append(("pipe", run.tag, tuple(run.path), z))
    for duct in ctx.model.ducts:
        z = tuple(duct.z_m) if len(duct.z_m) == len(duct.path) else ()
        out.append(("duct", duct.tag, tuple(duct.path), z))
    for raceway in ctx.model.conduits:
        out.append(("conduit", raceway.tag, tuple(raceway.path), conduit_vertex_z(raceway)))
    return out


def _segments_in_band(path: tuple[tuple[float, float], ...], z: tuple[float, ...],
                      band: tuple[float, float]) -> list[list[tuple[float, float]]]:
    """The run's segments whose own z-range overlaps this floor's structure.

    Per segment, not per run: ``CD-A-DATA-NE`` runs 25 feet on the attic deck and then climbs
    3'-6" up a gable, and only the horizontal part of it rides the attic floor."""
    low, high = band
    out = []
    for index in range(len(path) - 1):
        a, b = z[index], z[index + 1]
        if min(a, b) <= high and max(a, b) >= low:
            out.append([path[index], path[index + 1]])
    return out


@check(Tier.ADVISORY, "mep.run_over_void")
def run_over_void(ctx: CheckContext) -> list[Finding]:
    """A run may not span a floor opening except where a wall runs under it."""
    cid = "mep.run_over_void"
    runs = _runs(ctx)
    if not runs:
        return [unknown(cid, "no pipe, duct or conduit run is modeled, so there is no "
                             "route to grade", ())]
    floors = _voided_floors(ctx)
    if not floors:
        return [passed(cid, f"{len(runs)} runs: no floor system in this model carries a "
                            "deck void, so no run can span one", ())]

    out: list[Finding] = []
    ungraded: list[str] = []
    # The wall union is the expensive half and there are a handful of storeys against a
    # hundred runs, so it is built once per storey and kept.
    covers: dict[str, Any] = {}

    for kind, tag, path, z in sorted(runs, key=lambda item: item[1]):
        if len(path) < 2:
            continue
        if len(z) != len(path):
            # Honest rather than silent: a run with no resolved elevations cannot be placed
            # in a floor's band, so it is not graded — and the reader is told which.
            ungraded.append(tag)
            continue
        for floor, band, voids in floors:
            segments = _segments_in_band(path, z, band)
            if not segments:
                continue
            if floor.storey not in covers:
                covers[floor.storey] = _wall_cover(ctx, {floor.storey})
            cover = covers[floor.storey]
            line = MultiLineString(segments)
            for void in voids:
                spanning = line.intersection(void)
                if spanning.is_empty:
                    continue
                if cover is not None:
                    spanning = spanning.difference(cover)
                span_ft = spanning.length * _M_TO_FT
                if span_ft < MIN_SPAN_FT:
                    continue
                out.append(advisory(
                    cid,
                    f"{kind} run {tag} spans {span_ft:.2f} ft of {floor.tag}'s deck void with "
                    "no wall under it — there is no joist, no deck and no bay to strap it to, "
                    "and nothing to reach it from once the opening is trimmed out",
                    (tag, floor.tag), Result.FAIL,
                    fix="route the run round the opening, or onto a line where a wall carries "
                        "it (a run inside a wall's own layer footprint is supported and "
                        "passes)"))
    if ungraded:
        out.append(unknown(cid, f"{len(ungraded)} run(s) carry no resolved elevation, so they "
                                "cannot be placed in a floor's structure and were not graded: "
                                + ", ".join(sorted(ungraded)[:8]),
                           tuple(sorted(ungraded))))
    if not any(finding.result is Result.FAIL for finding in out):
        out.append(passed(cid, f"{len(runs)} runs: every crossing of a floor opening is inside "
                               "a wall footprint, or there is no crossing", ()))
    return out


# --- how far a run goes to get where it is going --------------------------------------------

@check(Tier.ADVISORY, "mep.run_route_efficiency")
def run_route_efficiency(ctx: CheckContext) -> list[Finding]:
    """A run's developed length against the straight line between its own two ends.

    Report-only in spirit and a FAIL in fact — the threshold is set where a house's own worst
    honest route sits, so anything above it is genuinely a detour rather than a tight budget.
    Three things keep it from being noise:

    **The denominator is 3D.** A riser's endpoints coincide in plan; graded there, every one
    of them scores infinity. See :func:`~typehaus.takeoff.runs.run_schedule`, which is where
    the arithmetic lives and which prints the whole ranking under ``haus takeoff --runs``.

    **Short runs are not graded.** Under ``min_graded_run_ft`` there is nothing to save, and
    under a foot of straight length the ratio is arithmetic on noise —
    :data:`~typehaus.takeoff.runs.MIN_STRAIGHT_FT` — so those come back UNKNOWN rather than
    passing quietly.

    **A TRUNK is not a route.** ``PR-B-CW-TRUNK`` serves twenty-one fixtures: it is a
    distribution tree flattened into one polyline, and the distance between its first vertex
    and its last is not a path it could have taken instead. It scores 2.69 and there is
    nothing wrong with it. A run naming three or more terminals is excluded on that ground —
    stated as a rule rather than as a suppression, because it is a fact about what the
    geometry means and not a decision about this house.

    **What this deliberately does NOT do** is ask whether a run crosses a room's open volume.
    The model has no per-room ceiling plane, so it cannot separate a duct in a plenum from a
    duct across a living room, and a check that guessed would be wrong in the cases that
    matter most. ``mep.run_over_void`` answers the half of that question the model CAN
    answer.
    """
    from typehaus.takeoff.runs import MIN_STRAIGHT_FT, run_schedule

    cid = "mep.run_route_efficiency"
    rules = ctx.preferences.mep
    terminals = {run.tag: len(run.serves) for run in ctx.model.pipe_runs}
    rows = run_schedule(ctx.model)
    if not rows:
        return [unknown(cid, "no pipe, duct or conduit run is modeled", ())]
    out: list[Finding] = []
    graded = 0
    for row in rows:
        if terminals.get(str(row["tag"]), 0) >= 3:
            continue  # a trunk, not a route — see the note above
        if float(row["developed_ft"]) < rules.min_graded_run_ft:
            continue
        if row["ratio"] is None:
            out.append(unknown(
                cid,
                f"{row['kind']} run {row['tag']} is {row['developed_ft']:.1f} ft long but its "
                f"two ends are {row['straight_ft']:.2f} ft apart in 3D — under "
                f"{MIN_STRAIGHT_FT:.0f} ft the ratio is arithmetic on noise and this run is "
                "not graded", (str(row["tag"]),)))
            continue
        graded += 1
        if float(row["ratio"]) <= rules.max_run_developed_over_straight:
            continue
        out.append(advisory(
            cid,
            f"{row['kind']} run {row['tag']} develops {row['developed_ft']:.1f} ft to cover "
            f"{row['straight_ft']:.1f} ft of straight line — a ratio of {row['ratio']:.2f} "
            f"against this house's {rules.max_run_developed_over_straight:.2f}, with "
            f"{row['elbows']} elbow(s) on it",
            (str(row["tag"]),), Result.FAIL,
            fix="`haus takeoff --runs` ranks every run this way and splits each length into "
                "plan and rise, which is what says whether it wanders or climbs. A high ratio "
                "can be the only legal route — check what is in the way before shortening it"))
    if not any(finding.result is Result.FAIL for finding in out):
        out.append(passed(cid, f"{graded} runs of {rules.min_graded_run_ft:.0f} ft or more are "
                               f"within {rules.max_run_developed_over_straight:.2f}x their "
                               "straight-line length", ()))
    return out


# --- what a run goes THROUGH on its way ------------------------------------------------------

#: A run whose surface comes within this of a rough opening's edge is not reported. A raceway
#: strapped to a jack stud shares a coordinate with the opening it is beside, and grading that
#: as "through the window" would be wrong in exactly the case the trade does on purpose. Half
#: an inch is under any framing member and over any coordinate noise.
OPENING_EDGE_M = 0.0127
#: How much of an opening a run must actually cross before it is reported. Below this it is a
#: corner clip, which is a dimension to check rather than a route to redraw.
MIN_CROSSING_FT = 0.1


def _opening_prisms(ctx: CheckContext) -> list[tuple[str, bool, str, Any, float, float]]:
    """Every rough opening as ``(tag, is_door, host tag, plan footprint, z low, z high)``.

    The footprint is the opening's slice of its host wall through the WHOLE wall thickness,
    because that is the hole: a window buck runs the full depth of the assembly, and a run
    that crosses the opening's width anywhere in that depth is in it. The band is the host
    wall's own base plus the authored sill, which is how ``resolve`` places the buck.
    """
    import math

    walls = {wall.tag: wall for wall in ctx.model.walls}
    out = []
    for opening in ctx.model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None or len(wall.axis) < 2:
            continue
        (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
        length = math.dist((ax, ay), (bx, by))
        if length <= 0:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        half, depth = opening.width_m / 2.0, wall.thickness_m / 2.0
        near, far = opening.center_along_m - half, opening.center_along_m + half
        corners = [(ax + ux * s + nx * depth * side, ay + uy * s + ny * depth * side)
                   for s in (near, far) for side in (1, -1)]
        prism = Polygon([corners[0], corners[1], corners[3], corners[2]])
        prism = prism.buffer(-OPENING_EDGE_M)
        if prism.is_empty or not prism.is_valid:
            continue
        low = wall.z0_m + opening.sill_m
        out.append((opening.tag, bool(opening.is_door), wall.tag, prism,
                    low, low + opening.height_m))
    return out


def _crossing_band(segment: Any, za: float, zb: float, piece: Any) -> tuple[float, float]:
    """The run's own z range over just the part of the segment inside the opening.

    Banding the WHOLE segment is the tempting shortcut and it is wrong on exactly the runs
    this check exists for: ``CD-A-DATA-NE`` climbs 3'-6" across 21 ft of gable in one segment,
    so its segment band spans four feet of elevation and reads as inside every opening it
    passes under. Interpolating at the crossing is the difference between two real findings
    and five, three of which are arithmetic.
    """
    from shapely.geometry import Point

    length = segment.length
    if length <= 0:
        return (min(za, zb), max(za, zb))
    zs = [za + (zb - za) * (segment.project(Point(xy)) / length)
          for xy in piece.coords]
    return (min(zs), max(zs))


def _run_radii(ctx: CheckContext) -> dict[str, float]:
    """Half the outside dimension of each run, keyed by tag.

    A run is a centreline and an opening is a hole; whether the two meet is a question about
    the run's SURFACE. Six inches of duct with an inch of wrap either side is eight inches of
    obstruction, and grading its centreline alone under-reports by four. A raceway's trade
    size is a nominal bore rather than an outside diameter, but the error is under an eighth
    of an inch on 3/4" EMT and in the conservative direction.
    """
    radii: dict[str, float] = {}
    for run in ctx.model.pipe_runs:
        radii[run.tag] = (run.diameter_m or 0.0) / 2.0
    for duct in ctx.model.ducts:
        radii[duct.tag] = (duct.diameter_m or 0.0) / 2.0
    for raceway in ctx.model.conduits:
        radii[raceway.tag] = (raceway.trade_size_m or 0.0) / 2.0
    return radii


@check(Tier.ADVISORY, "mep.run_through_opening")
def run_through_opening(ctx: CheckContext) -> list[Finding]:
    """A pipe, duct or raceway may not pass through a window or door rough opening.

    This is the hole the trades leave for something else. A run drawn across it is not a
    clearance question to be resolved on site — there is nothing there to strap to, the leaf
    swings through it, and in a window it stands in front of the glass. It is also the single
    easiest defect to author, because a plan drawing shows a run crossing a wall and says
    nothing about whether it crossed at the header or at the opening.

    **Nothing else in the engine looks.** ``mep.duct_joist_bay`` grades the bay a duct is in
    and never asks what its riser stands in — on catlin it PASSED a 3" extract standing 78 1/2"
    inside ``D-S-PLANT``'s rough opening and printed the station twice in its own fire-blocking
    list. ``structural.member_interference`` is wood against wood. ``mep.run_over_void`` grades
    holes in floors, not holes in walls. Before this check the argument was made by hand, in a
    comment, when it was made at all (``houses/catlin/plan/electrical.py`` reasoned about one
    door head in prose and was right; two windows and three doors elsewhere were missed).

    Two cases, because a run meets an opening in two ways:

    **Crossing** — a segment whose plan line passes through the opening's footprint within its
    elevation band. The band is taken at the crossing, not over the whole segment; see
    :func:`_crossing_band` for why that distinction decides real findings from arithmetic.

    **Standing in it** — a riser, whose plan segment has no length at all, landing inside the
    footprint with its rise overlapping the band. This is the ``D-S-PLANT`` case and a
    crossing test alone cannot see it, because a riser crosses nothing.

    ADVISORY rather than CODE: no section says "do not draw a duct through a window", for the
    same reason no section says which side of a wall a light switch is on. It is a buildability
    rule, and its result is still ``FAIL`` so a clean house stays clean.
    """
    from shapely.geometry import LineString, Point

    cid = "mep.run_through_opening"
    runs = _runs(ctx)
    if not runs:
        return [unknown(cid, "no pipe, duct or conduit run is modeled, so there is no route "
                             "to grade", ())]
    prisms = _opening_prisms(ctx)
    if not prisms:
        return [passed(cid, f"{len(runs)} runs: this model resolves no rough opening, so no "
                            "run can pass through one", ())]

    radii = _run_radii(ctx)
    out: list[Finding] = []
    ungraded: list[str] = []

    for kind, tag, path, z in sorted(runs, key=lambda item: item[1]):
        if len(path) < 2:
            continue
        if len(z) != len(path):
            ungraded.append(tag)
            continue
        radius = radii.get(tag, 0.0)
        for index in range(len(path) - 1):
            a, b = path[index], path[index + 1]
            za, zb = z[index], z[index + 1]
            segment = LineString([a, b])
            standing = segment.length <= OPENING_EDGE_M
            for otag, is_door, host, prism, low, high in prisms:
                if standing:
                    if not prism.covers(Point(a)):
                        continue
                    band = (min(za, zb), max(za, zb))
                    if band[1] - band[0] <= OPENING_EDGE_M:
                        continue
                    overlap = min(band[1], high) - max(band[0], low)
                    if overlap <= OPENING_EDGE_M:
                        # A riser that merely touches the head or the sill passes the opening,
                        # it does not stand in it — and a run has to touch one of the two to
                        # get past. Only an overlap with real height is a finding.
                        continue
                    out.append(advisory(
                        cid,
                        f"{kind} run {tag} stands {overlap * 12 * _M_TO_FT:.0f}\" inside "
                        f"{otag}'s rough opening in {host} — a riser in a "
                        f"{'doorway' if is_door else 'window'} has nothing to strap to, and "
                        "the header above it is not borable",
                        (tag, otag), Result.FAIL,
                        fix="move the riser to a clear stud bay beside the opening; the "
                            "terminal it feeds usually has to move with it"))
                    continue
                piece = prism.intersection(segment)
                if piece.is_empty or piece.length <= 0:
                    continue
                crossed_ft = piece.length * _M_TO_FT
                if crossed_ft < MIN_CROSSING_FT:
                    continue
                pieces = (piece.geoms if isinstance(piece, MultiLineString) else [piece])
                for part in pieces:
                    lo, hi = _crossing_band(segment, za, zb, part)
                    if hi + radius < low or lo - radius > high:
                        continue
                    out.append(advisory(
                        cid,
                        f"{kind} run {tag} crosses {crossed_ft:.2f} ft of {otag}'s rough "
                        f"opening in {host}, at {(lo - low) * 12 * _M_TO_FT:.0f}\" above its "
                        f"sill — the opening is {(high - low) * 12 * _M_TO_FT:.0f}\" tall",
                        (tag, otag), Result.FAIL,
                        fix="carry the run over the header or under the sill, or take it to "
                            "the next stud bay; in a window there is no 'over' — the head is "
                            "usually the plate"))
                    break

    if not any(finding.result is Result.FAIL for finding in out):
        out.append(passed(cid, f"{len(runs)} runs against {len(prisms)} rough openings: no "
                               "run passes through one or stands in one", ()))
    if ungraded:
        out.append(unknown(cid, f"{len(ungraded)} run(s) carry no resolved elevations and are "
                                f"not graded: {', '.join(sorted(ungraded)[:6])}",
                           tuple(sorted(ungraded))))
    return out
