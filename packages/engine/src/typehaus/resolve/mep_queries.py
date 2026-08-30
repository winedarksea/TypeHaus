"""Shared MEP derivations — the query API over an already-resolved model.

Not a resolver: nothing here appends to ``ResolvedModel``. These are the geometric
questions both the checks (``mep.wet_wall_occupancy``, ``mep.sleeve_coverage``,
``mep.pipe_sizing``) and the plumbing/HVAC takeoffs ask, split out of ``resolve/mep.py``
at the divider that already marked the seam so the reader and the finding can never
disagree (same invariant as takeoff/hvac.py heating_zones <-> checks/mep/hvac.py).

``resolve/mep.py`` imports from this module, never the other way round: the resolver is
the caller, so the dependency runs resolver -> queries and the ``checks`` <-> ``resolve``
cycle stays broken.
"""

from __future__ import annotations

from typehaus.model.enums import DuctRouting
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import (
    ResolvedConduitRun,
    ResolvedModel,
    ResolvedPipeRun,
    Ring,
)

#: Fallback breadth for a bay boundary whose profile the section reader cannot parse. It is
#: solid-sawn 2x, the narrowest thing a floor is ever framed in, so an unparsed profile errs
#: toward a WIDER clear bay and a quieter check rather than a confident false conflict.
_JOIST_BREADTH_FALLBACK_M = inch(1.5).meters
#: What actually bounds a joist bay. ``blocking`` sits BETWEEN joists and ``rim``/``header``
#: run around the perimeter, so none of the three is a bay edge; a ``trimmer`` or a
#: ``sister_joist`` is one, because both are a doubled joist at an opening.
_BAY_EDGE_CATEGORIES = ("joist", "trimmer", "sister_joist")
#: The concrete a sleeve can be cast into, and the solids ``concrete_crossings`` walks.
_CONCRETE_SOLID_CATEGORIES = ("slab", "footing")
_PIPE_CAVITY_CLEARANCE_M = inch(0.25).meters  # boring/annular allowance inside a stud bay
_STUD_BAY_TRAVEL_M = inch(16).meters  # one standard bay: horizontal in-wall travel note


def wet_wall_occupancy(run: ResolvedPipeRun, model: ResolvedModel) -> list[dict]:
    """Validate every in-wall segment of a routed run against its declared host wall.

    Returns plain-dict problems (kind, segment, wall, message) — the check turns them
    into findings, the takeoff lists them. Kinds: ``missing_wall`` (ref resolves to no
    wall), ``outside_wall`` (segment escapes the structure footprint), ``too_shallow``
    (cavity cannot take the pipe), ``long_horizontal`` (advisory: horizontal in-wall
    travel beyond one stud bay in a single-layout wall — a staggered wall's continuous
    cavity is exempt, that is its point)."""
    from shapely.geometry import LineString, Point, Polygon

    problems: list[dict] = []
    if not run.wall_refs:
        return problems
    for i in range(len(run.path) - 1):
        wall_tag = run.wall_refs[i] if i < len(run.wall_refs) else None
        if wall_tag is None:
            continue
        seg = (run.path[i], run.path[i + 1])
        wall = model.wall(wall_tag)
        if wall is None:
            problems.append(dict(
                kind="missing_wall", segment=i, wall=wall_tag,
                message=f"{run.tag} segment {i} names missing wall {wall_tag}"))
            continue
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        if structure is None or len(structure.polygon) < 3:
            problems.append(dict(
                kind="outside_wall", segment=i, wall=wall_tag,
                message=f"{run.tag} segment {i}: wall {wall_tag} has no structure layer"))
            continue
        radius = run.diameter_m / 2.0
        footprint = Polygon(structure.polygon)
        vertical = length(sub(seg[0], seg[1])) < 1e-6
        shape = (Point(seg[0]) if vertical else LineString(seg)).buffer(radius)
        if not footprint.buffer(1e-4).contains(shape):
            problems.append(dict(
                kind="outside_wall", segment=i, wall=wall_tag,
                message=(f"{run.tag} segment {i} (Ø{run.diameter_m / 0.0254:.1f}\") leaves "
                         f"the structure footprint of {wall_tag}")))
        cavity = structure.thickness_m - _PIPE_CAVITY_CLEARANCE_M
        if run.diameter_m > cavity + 1e-9:
            problems.append(dict(
                kind="too_shallow", segment=i, wall=wall_tag,
                message=(f"{run.tag} segment {i} Ø{run.diameter_m / 0.0254:.1f}\" exceeds "
                         f"{wall_tag}'s {structure.thickness_m / 0.0254:.1f}\" cavity "
                         f"less {_PIPE_CAVITY_CLEARANCE_M / 0.0254:.2f}\" clearance")))
        if vertical:
            if run.z_m is not None:
                lo, hi = sorted((run.z_m[i], run.z_m[i + 1]))
                if lo < wall.z0_m - 1e-6 or hi > wall.z1_m + 1e-6:
                    problems.append(dict(
                        kind="outside_wall", segment=i, wall=wall_tag,
                        message=(f"{run.tag} segment {i} drop {lo:.2f}–{hi:.2f}m exceeds "
                                 f"{wall_tag}'s extent {wall.z0_m:.2f}–{wall.z1_m:.2f}m")))
        else:
            layout = _wall_layout(model, wall)
            travel = length(sub(seg[0], seg[1]))
            if layout != "staggered" and travel > _STUD_BAY_TRAVEL_M + 1e-9:
                problems.append(dict(
                    kind="long_horizontal", segment=i, wall=wall_tag,
                    message=(f"{run.tag} segment {i} runs {travel / 0.3048:.1f}' "
                             f"horizontally inside single-layout wall {wall_tag} — "
                             "every stud on the way gets bored")))
    return problems


def _wall_layout(model: ResolvedModel, wall) -> str:
    """The wall's partition layout ("single" | "staggered" | "double") off its assembly."""
    assembly = model.plan.library.assembly(wall.assembly)
    if assembly is None:
        return "single"
    for layer in assembly.layers:
        spec = getattr(layer, "framing", None)
        if spec is not None and getattr(spec, "layout", None) is not None:
            return spec.layout.value
    return "single"


def _conduit_vertical_profile(run: ResolvedConduitRun) -> tuple[Ring, list[float]] | None:
    """A conduit's path and per-vertex z, in the same shape a ``PipeRun`` resolves to.

    A ``ConduitRun`` travels its plan polyline flat at ``z_start_m`` and rises vertically at
    its last point (→ model/mep.py ConduitRun), so the riser is expressed the way pipe runs
    express one: the final plan point repeated, carrying the two different elevations."""
    if run.z_start_m is None or run.z_end_m is None or len(run.path) < 2:
        return None
    path = list(run.path)
    z = [run.z_start_m] * len(path)
    if abs(run.z_end_m - run.z_start_m) > 1e-9:
        path.append(path[-1])
        z.append(run.z_end_m)
    return path, z


def concrete_crossings(model: ResolvedModel) -> list[dict]:
    """Every point where a routed pipe or raceway passes through concrete — the pour-day list.

    Walks each resolved run with vertical information against every concrete solid
    (slab/footing) and foundation wall. Returns plain dicts: run, host, host_category,
    point (plan), z_m, matched sleeve tag or None. A run with no z information cannot be
    walked and is skipped — the check reports those runs as UNKNOWN, never silently.

    Conduit is walked alongside pipe because the defect is identical and does not care which
    trade caused it: a raceway crossing a deck that cured without a sleeve gets cored just the
    same. Leaving conduit out is why ``CD-B-ATTIC-RISER`` and ``CD-B-KITCHEN`` punched through
    catlin's 9" ``SL-M-DECK`` unsleeved and unnoticed."""
    from shapely.geometry import LineString, Point, Polygon

    hosts = [(s.tag, s.category, Polygon(s.outline), s.z0_m, s.z1_m)
             for s in model.solids
             if s.category in _CONCRETE_SOLID_CATEGORIES and len(s.outline) >= 3]
    for wall in model.walls:
        if not wall.is_foundation:
            continue
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        if structure is not None and len(structure.polygon) >= 3:
            hosts.append((wall.tag, "wall", Polygon(structure.polygon),
                          wall.z0_m, wall.z1_m))

    # (tag, system label, outside diameter, path, per-vertex z) for both trades. A raceway's
    # "diameter" is its trade size, which is what a sleeve has to be sized around.
    walkable: list[tuple[str, str, float, Ring, list[float]]] = [
        (run.tag, run.system, run.diameter_m, run.path, run.z_m)
        for run in model.pipe_runs if run.z_m is not None
    ]
    for conduit in model.conduits:
        profile = _conduit_vertical_profile(conduit)
        if profile is None:
            continue
        path, z = profile
        walkable.append((conduit.tag, conduit.service or "spare",
                         conduit.trade_size_m, path, z))

    crossings: list[dict] = []
    for tag, system, diameter_m, path, z_m in walkable:
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            za, zb = z_m[i], z_m[i + 1]
            for host_tag, category, footprint, hz0, hz1 in hosts:
                hit = _segment_concrete_hit(a, b, za, zb, footprint, hz0, hz1,
                                            LineString, Point)
                if hit is None:
                    continue
                point, z_at = hit
                sleeve = _matching_sleeve(model, host_tag, system, point, z_at)
                crossings.append(dict(
                    run=tag, system=system, diameter_m=diameter_m,
                    host=host_tag, host_category=category, point=point, z_m=z_at,
                    sleeve=sleeve))
    return crossings


def _segment_concrete_hit(a, b, za, zb, footprint, hz0, hz1, LineString, Point):
    """Where (if anywhere) segment a→b at inverts za→zb passes through the host band."""
    plan_len = length(sub(a, b))
    lo, hi = sorted((za, zb))
    if hi < hz0 - 1e-6 or lo > hz1 + 1e-6:
        return None  # z ranges never meet
    if plan_len < 1e-6:
        # Vertical drop: crossing iff the drop spans the band and the point is inside.
        if lo <= hz0 + 1e-6 and hi >= hz1 - 1e-6 and footprint.buffer(1e-6).contains(Point(a)):
            return a, (hz0 + hz1) / 2.0
        return None
    # Sloped/horizontal: find where the invert crosses the band's mid-plane; a segment
    # running entirely inside the band (embedded in the pour) also counts at its midpoint
    # if the plan line enters the footprint.
    mid = (hz0 + hz1) / 2.0
    if abs(zb - za) > 1e-9 and min(za, zb) - 1e-6 <= mid <= max(za, zb) + 1e-6:
        t = (mid - za) / (zb - za)
        point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if footprint.buffer(1e-6).contains(Point(point)):
            return point, mid
        return None
    if lo >= hz0 - 1e-6 and hi <= hz1 + 1e-6:
        line = LineString((a, b))
        if line.intersects(footprint):
            inter = line.intersection(footprint)
            # Grazing a face is not a crossing: a run laid tight against a wall touches
            # its boundary with (near-)zero embedded length and casts no sleeve.
            if getattr(inter, "length", 0.0) < 0.02:
                return None
            c = inter.centroid
            if not c.is_empty:
                # Invert *at the crossing*, not the segment mean — a sloped drain's
                # invert at the wall is what the cast sleeve is set to.
                t = line.project(c) / max(line.length, 1e-9)
                return (c.x, c.y), za + t * (zb - za)
    return None


_SLEEVE_MATCH_TOL_M = 0.1  # a cast-in sleeve within 4" of the crossing claims it


#: Which ``SleevePenetration.purpose`` values a crossing of each system may claim. Proximity
#: alone is not enough: a 1" power raceway that happens to pass within 4" of a 3" drain
#: sleeve is not threading it, and letting it match reported a false PASS on the raceway
#: *and* stole the sleeve from the drain that really goes through it (which is how
#: ``mep.sewer_exit_invert`` came to grade CD-B-SPA as a drain). Systems are the ``PipeSystem``
#: values plus, for conduit, the ``Service`` the raceway carries or "spare" for a capped one.
_SLEEVE_PURPOSES_BY_SYSTEM = {
    "water_cold": {"water_cold"}, "water_hot": {"water_hot"},
    "drain": {"drain"}, "vent": {"vent"}, "radon": {"vent", "drain"}, "gas": {"gas"},
    # A raceway may share a sleeve with another raceway of any voltage — they are all
    # electrical work — but never with a plumbing one. A spare pipe is electrical too: it is
    # in the electrician's rough-in, whatever eventually goes through it.
    "power_120": {"power_120", "power_240"}, "power_240": {"power_120", "power_240"},
    "data": {"data"}, "spare": {"power_120", "power_240", "data"},
}


def _matching_sleeve(model: ResolvedModel, host_tag: str, system: str,
                     point: tuple[float, float], z_at: float) -> str | None:
    allowed = _SLEEVE_PURPOSES_BY_SYSTEM.get(system)
    best: tuple[float, str] | None = None
    for sleeve in model.sleeves:
        if sleeve.host_slab != host_tag:
            continue
        if allowed is not None and sleeve.purpose not in allowed:
            continue
        d = length(sub(sleeve.center, point))
        if d <= _SLEEVE_MATCH_TOL_M and (best is None or d < best[0]):
            best = (d, sleeve.tag)
    return best[1] if best is not None else None


def on_pipe_segment(point: tuple[float, float], start: tuple[float, float],
                    end: tuple[float, float], tol: float = 1e-6) -> bool:
    """True when ``point`` lies on the plan segment ``start``–``end`` (endpoints included)."""
    (px, py), (ax, ay), (bx, by) = point, start, end
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > tol:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    length_sq = (bx - ax) ** 2 + (by - ay) ** 2
    return -tol <= dot <= length_sq + tol


def pipe_invert_at(run, point: tuple[float, float], tol: float = 1e-6) -> float | None:
    """The run's invert where ``point`` sits on its plan path, or None if it doesn't.

    Takes the *deepest* match, not the first: a run's plan path can visit one point twice
    at two elevations (PR-B-MAIN-DRAIN passes (3', 15'-6") at the ceiling where the
    collector turns and again 9'-8" lower where the drop through the slab lands). The
    deeper leg is the one a buried branch actually ties into.
    """
    if run.z_m is None:
        return None
    candidates = []
    for index in range(len(run.path) - 1):
        start, end = run.path[index], run.path[index + 1]
        if not on_pipe_segment(point, start, end, tol):
            continue
        seg_len = length(sub(end, start))
        if seg_len <= tol:
            continue
        travelled = length(sub(point, start))
        fraction = travelled / seg_len
        candidates.append(run.z_m[index]
                          + (run.z_m[index + 1] - run.z_m[index]) * fraction)
    return min(candidates) if candidates else None


# Arrival may read slightly below the receiving invert at the matched vertex: authored
# inverts interpolate along whole segments, while the physical wye sits a little way
# downstream of a corner (catlin's kitchen branch arrives 0.43" under the main's invert
# at the (6', 16'-6") turn). One inch of slack keeps the *load* graph connected — grading
# slope/backflow is drain_slope's job, not the rollup's; a missed tie-in here silently
# under-sizes the pipe downstream, which is the worse failure.
_TIE_IN_INVERT_TOL_M = 0.0254


def drain_tie_ins(pipe_runs) -> dict[str, str]:
    """Child drain run tag → the drain run it discharges into, derived geometrically.

    ``PipeRun`` carries no upstream/downstream refs, so the connection is the geometry
    itself: a run ties into another when its *last* path vertex lies on a segment of the
    other's path and arrives at or above the other's invert there (a branch below the
    main it joins would not flow — the resolver-level gravity test pins the same
    relation). Runs without elevation data can't be judged and never tie in.

    A run never receives at its own terminal vertex: that point is where *it*
    discharges, so several branches all ending on one junction are siblings meeting at
    a wye on whatever continues downstream, not each other's parents (this is also what
    keeps the derivation acyclic on real junctions).
    """
    drains = [r for r in pipe_runs if r.system == "drain"]
    out: dict[str, str] = {}
    for child in drains:
        if child.z_m is None or not child.path:
            continue
        end_point, end_invert = child.path[-1], child.z_m[-1]
        best: tuple[float, str] | None = None
        for parent in drains:
            if parent.tag == child.tag or not parent.path:
                continue
            if length(sub(end_point, parent.path[-1])) <= 1e-6:
                continue  # the parent terminates here too — a sibling, not a receiver
            invert = pipe_invert_at(parent, end_point)
            if invert is None or end_invert < invert - _TIE_IN_INVERT_TOL_M:
                continue
            # Of several runs passing under the arrival point, the receiving pipe is
            # the one whose invert sits closest beneath the arrival.
            if best is None or invert > best[0]:
                best = (invert, parent.tag)
        if best is not None:
            out[child.tag] = best[1]
    return out


def accumulated_serves(pipe_runs) -> dict[str, tuple[str, ...]]:
    """Per drain run: the union of ``serves`` tags over its whole upstream subtree.

    Fixture tags are re-listed across runs by authoring convention (a fixture may appear
    on both its branch and the main), so the accumulation is a *union keyed by fixture
    tag* — summing per-branch loads would double-count. The result feeds
    ``branch_load``, which keeps its UNKNOWN-not-partial contract: one untabulated tag
    anywhere upstream makes the downstream run's load unknowable.
    """
    drains = [r for r in pipe_runs if r.system == "drain"]
    tie_ins = drain_tie_ins(drains)
    children: dict[str, list[str]] = {}
    for child_tag, parent_tag in tie_ins.items():
        children.setdefault(parent_tag, []).append(child_tag)
    by_tag = {r.tag: r for r in drains}

    def collect(tag: str, seen: set) -> set:
        if tag in seen:  # cycle guard: mutual geometric matches must not recurse forever
            return set()
        seen.add(tag)
        tags = set(by_tag[tag].serves)
        for child in children.get(tag, ()):
            tags |= collect(child, seen)
        return tags

    return {run.tag: tuple(sorted(collect(run.tag, set()))) for run in drains}


def is_parallel_to_floor(path: list[tuple[float, float]], floor) -> bool:
    """Whether every segment of ``path`` runs parallel to the floor's joist axis."""
    along_x = floor.direction == "x"
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        perp_a = a[1] if along_x else a[0]
        perp_b = b[1] if along_x else b[0]
        if abs(perp_a - perp_b) >= 1e-6:
            return False
    return True


def duct_bay_occupancy(path: list[tuple[float, float]], width_m: float, depth_m: float,
                       routing: DuctRouting, floor, bearing_walls: list,
                       spacing_m: float) -> tuple[list[str], list[tuple[float, float]], bool]:
    """Validate a duct path against one floor's joist bays and bearing lines.

    Returns ``(conflicts, crossings, depth_ok)``. Conflicts are structural FAILs (a
    parallel segment straddling a joist line, too wide for the clear bay, or a
    perpendicular/oblique segment crossing joist lines outside SOFFIT/CHASE routing).
    Bearing-line crossings are always legal (the resolver lays identical perp positions
    on both sides of a bearing line) — they become a drawing note, never a conflict.
    """
    along_x = floor.direction == "x"
    # Only the members that actually bound a bay. Reading every member manufactured phantom
    # bay edges out of blocking (which sits mid-bay by definition) and out of the rim, and a
    # phantom edge inside a bay is what turns a legal parallel run into a "straddles a joist
    # line" conflict.
    edges = [m for m in floor.members if m.category in _BAY_EDGE_CATEGORIES]
    joist_lines = sorted({(m.p0[1] if along_x else m.p0[0]) for m in edges})
    member_depth = max((m.z1_m - m.z0_m for m in floor.members), default=depth_m)
    depth_ok = depth_m <= member_depth + 1e-9
    # From a JOIST, not from ``members[0]``, which was whichever member the resolver happened
    # to emit first — a rim board on most floors, and a rim board is never an open web.
    opening_m = (open_web_opening_m(cross_section(edges[0].profile)) if edges else None)

    conflicts: list[str] = []
    crossings: list[tuple[float, float]] = []
    # ** THE BREADTH IS THE MEMBER'S, NOT A CONSTANT. ** This subtracted a hardcoded 1 1/2"
    # until 2026-08-30 — solid-sawn 2x breadth, applied to every floor whatever it is framed
    # in. An 11 7/8" floor truss has a 3 1/2" chord and an 11 7/8" I-joist a 2 1/2" flange, so
    # on 16" centres the check was crediting 14 1/2" of clear bay where a truss leaves 12 1/2"
    # and an I-joist 13 1/2". Two inches is the difference between a 12" duct fitting and not.
    breadths = {cross_section(m.profile).width_m for m in edges}
    clear_width_m = spacing_m - (max(breadths) if breadths else _JOIST_BREADTH_FALLBACK_M)
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        pa, pb = (a[1], b[1]) if along_x else (a[0], b[0])
        aa, ab = (a[0], b[0]) if along_x else (a[1], b[1])
        if abs(pa - pb) < 1e-6:
            c = pa
            lo, hi = c - width_m / 2, c + width_m / 2
            straddled = [jl for jl in joist_lines if lo + 1e-6 < jl < hi - 1e-6]
            if straddled:
                conflicts.append(
                    f"segment {i} centered at {c:.3f}m crosses joist line(s) at "
                    f"{[round(v, 3) for v in straddled]}"
                )
            if width_m > clear_width_m + 1e-9:
                conflicts.append(
                    f"segment {i} width {width_m:.3f}m exceeds the {clear_width_m:.3f}m "
                    f"clear bay at {spacing_m / M_PER_IN:.0f}\" o.c."
                )
        else:
            crossed = [jl for jl in joist_lines if min(pa, pb) < jl < max(pa, pb)]
            if crossed and routing not in (DuctRouting.SOFFIT, DuctRouting.CHASE):
                if opening_m is not None and depth_m <= opening_m + 1e-9:
                    # Legal: the run passes through the truss webs, same as a
                    # bearing-line crossing — a note, not a conflict.
                    for jl in crossed:
                        t = 0.0 if abs(pb - pa) < 1e-12 else (jl - pa) / (pb - pa)
                        along_at = aa + t * (ab - aa)
                        crossings.append((along_at, jl) if along_x else (jl, along_at))
                elif opening_m is not None:
                    conflicts.append(
                        f"segment {i} runs perpendicular/oblique across joist line(s) "
                        f"{[round(v, 3) for v in crossed]} — depth "
                        f"{depth_m / M_PER_IN:.1f}\" exceeds the {opening_m / M_PER_IN:.1f}\" "
                        "chord-to-chord opening"
                    )
                else:
                    conflicts.append(
                        f"segment {i} runs perpendicular/oblique across joist line(s) "
                        f"{[round(v, 3) for v in crossed]} — route in a soffit or chase"
                    )
        for wall in bearing_walls:
            (wx0, wy0), (wx1, wy1) = wall.axis
            wc = ((wx0 + wx1) / 2) if along_x else ((wy0 + wy1) / 2)
            if min(aa, ab) - 1e-6 <= wc <= max(aa, ab) + 1e-6:
                t = 0.0 if abs(ab - aa) < 1e-12 else (wc - aa) / (ab - aa)
                perp_at = pa + t * (pb - pa)
                crossings.append((wc, perp_at) if along_x else (perp_at, wc))
    return conflicts, crossings, depth_ok
