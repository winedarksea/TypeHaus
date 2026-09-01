"""Sleeve penetrations — resolving one, and deciding where it should have been.

A sleeve is the hole a pipe is *allowed* to pass through concrete in, and it is cast on
pour day, so it has to be located before the pipe it serves exists. That makes this band
different in kind from the run resolvers next door: most of it is the derivation of an
*expected* point (from an authored fixture, from a routed pipe vertex, from a drain), so a
sleeve that drifted from what it serves can be reported rather than silently accepted.

Split out of ``mep.py`` for size. The dependency runs one way — ``mep`` imports this, never
the reverse — so the sleeve solid emitter here deliberately duplicates none of the run
emitter's code; it only matches its facet count so a run and the sleeve it threads read as
the same round section.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import Service
from typehaus.model.mep import SleevePenetration
from typehaus.model.placeables import MountKind
from typehaus.model.spatial import Appliance, Fixture
from typehaus.resolve.geometry import circle_outline, length, sub
from typehaus.resolve.framing.carriers import backing_wall
from typehaus.resolve.mep_queries import _CONCRETE_SOLID_CATEGORIES
from typehaus.resolve.model import (
    ResolvedModel,
    ResolvedSleeve,
    ResolvedSolid,
    Ring,
)
from typehaus.resolve.round_solids import PIPE_FACETS, round_run_bands


def _sleeve_host(model: ResolvedModel, host_ref: str):
    """A sleeve's concrete host: (footprint, z0, z1, category, tag) or None.

    A slab or footing is a ResolvedSolid; a foundation/concrete wall is a ResolvedWall
    whose structure layer supplies the footprint."""
    solid = next((s for s in model.solids
                  if s.tag == host_ref and s.category in _CONCRETE_SOLID_CATEGORIES), None)
    if solid is not None:
        return solid.outline, solid.z0_m, solid.z1_m, solid.category, solid.tag
    wall = model.wall(host_ref)
    if wall is not None:
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        outline = structure.polygon if structure is not None else ()
        if len(outline) >= 3:
            return outline, wall.z0_m, wall.z1_m, "wall", wall.tag
    return None


def _resolve_sleeve(model: ResolvedModel, sleeve: SleevePenetration,
                    storey_tag: str) -> list[Finding]:
    findings: list[Finding] = []
    host = _sleeve_host(model, sleeve.host_ref)
    if host is None:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.sleeve_host",
            message=(f"sleeve {sleeve.tag} references {sleeve.host_ref}, which is no "
                     "slab, footing, or concrete wall"),
            element_tags=(sleeve.tag,), result=Result.FAIL,
        )]
    outline, z0, z1, category, host_tag = host

    from shapely.geometry import Point, Polygon

    center = sleeve.position.xy_m
    point = Point(center)
    if not Polygon(outline).buffer(1e-6).contains(point):
        findings.append(Finding(
            severity=Severity.ERROR, check_id="integrity.sleeve_in_opening",
            message=f"sleeve {sleeve.tag} center falls outside its host {host_tag}",
            element_tags=(sleeve.tag, host_tag), result=Result.FAIL,
        ))
    if sleeve.axis == "horizontal":
        cz = sleeve.center_elevation.meters if sleeve.center_elevation is not None else None
        if cz is None:
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_host",
                message=f"horizontal sleeve {sleeve.tag} authors no center_elevation",
                element_tags=(sleeve.tag,), result=Result.FAIL))
        elif category == "footing" and cz < z0 - 1e-6:
            # An under-footing protection sleeve (IRC P2604): the pipe passes below the
            # bearing plane inside a sleeve/relieving arch, so the centerline is legal
            # below the footing's own extent. mep.footing_clearance requires it.
            pass
        elif not (z0 - 1e-6 <= cz <= z1 + 1e-6):
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_host",
                message=(f"horizontal sleeve {sleeve.tag} centerline {cz:.3f}m falls "
                         f"outside host {host_tag} extent {z0:.3f}–{z1:.3f}m"),
                element_tags=(sleeve.tag, host_tag), result=Result.FAIL))
    host_element = model.plan.by_tag(host_tag)
    for opening_tag in getattr(host_element, "openings", ()):
        opening = model.plan.by_tag(opening_tag)
        if opening is None or len(opening.outline) < 3:
            continue
        if Polygon([p.xy_m for p in opening.outline]).contains(point):
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_in_opening",
                message=f"sleeve {sleeve.tag} falls inside floor opening {opening_tag}",
                element_tags=(sleeve.tag, opening_tag), result=Result.FAIL,
            ))

    expected = _expected_sleeve_point(model, sleeve)
    offset = length(sub(center, expected)) if expected is not None else None
    resolved = ResolvedSleeve(
        uid=sleeve.uid, tag=sleeve.tag, storey=storey_tag, host_slab=host_tag,
        center=center, pipe_d_m=sleeve.pipe_diameter.meters,
        sleeve_d_m=sleeve.sleeve_diameter.meters, z0_m=z0, z1_m=z1,
        serves_fixture=sleeve.serves_fixture, expected_center=expected, offset_m=offset,
        axis=sleeve.axis, host_category=category,
        center_z_m=(sleeve.center_elevation.meters
                    if sleeve.center_elevation is not None else None),
        purpose=sleeve.purpose.value,
    )
    model.sleeves.append(resolved)
    _emit_sleeve_solid(model, resolved, outline, storey_tag)
    return findings


#: One category for every sleeve, whatever it carries. Unlike a run — where hot, cold, waste
#: and vent are four different things to find on a riser diagram — a block-out is a block-out:
#: the concrete crew sets the same forms for all of them, and what eventually threads it is
#: the *pipe's* business, not the hole's. Splitting by ``purpose`` would put four labels on one
#: pour-day operation. Plumbing trade, because sleeve coverage is a plumbing rough-in question
#: (``checks/mep/plumbing.py``), including for the raceways that share the pour.
_SLEEVE_CATEGORY = "pipe_sleeve"

#: Longer than any host is thick; the probe is clipped to the host footprint immediately.
_SLEEVE_BORE_PROBE_M = 100.0


def _emit_sleeve_solid(model: ResolvedModel, sleeve: ResolvedSleeve,
                       outline: Ring, storey_tag: str) -> None:
    """The cast-in block-out, drawn at ``sleeve_d_m`` — the hole, at the size it is formed.

    A *solid*, not a void: ``ResolvedSolid`` extrudes a plan outline and has no boolean, so
    what lands in the model is a short length of sleeve where the hole goes rather than an
    absence in the pour (subtracting it from the host is deferred work, → plans/TODO.md
    "boolean sleeve voids"). That is still the thing a pre-pour walk is looking for: a sleeve
    you can click, at the diameter that gets set, in the concrete it gets set in.

    Vertical (the slab drop) spans the host's full depth as a faceted cylinder. Horizontal
    (a foundation-wall crossing, or the under-footing protection sleeves of IRC P2604) is
    swept in chord bands along the host's normal, exactly as a horizontal pipe segment is
    (``_emit_run_solids``), so a run and the sleeve it threads read as the same round section.
    """
    # Suffixed, never the bare element uid: the IFC emitter derives a GlobalId from it, and
    # the ``SleevePenetration`` already exports under its own uid as an IfcBuildingElementProxy
    # — reusing it put two entities in the file with the same GUID and failed express-rule
    # IfcRoot.UR1 on every vertical sleeve.
    uid = f"{sleeve.uid or sleeve.tag}-sleeve"
    radius = sleeve.sleeve_d_m / 2.0
    if sleeve.axis != "horizontal":
        model.solids.append(ResolvedSolid(
            uid=uid, tag=sleeve.tag, storey=storey_tag, category=_SLEEVE_CATEGORY,
            outline=circle_outline(sleeve.center, radius, PIPE_FACETS),
            z0_m=sleeve.z0_m, z1_m=sleeve.z1_m))
        return
    if sleeve.center_z_m is None:
        return  # no centerline: already an integrity FAIL above, and nothing to draw it at
    bore = _sleeve_bore(model, sleeve, outline)
    if bore is None:
        return
    start, end = bore
    for band, (band_outline, band_z0, band_z1) in enumerate(
            round_run_bands(start, end, radius, sleeve.center_z_m)):
        model.solids.append(ResolvedSolid(
            uid=f"{uid}-b{band:02d}", tag=f"{sleeve.tag}-B{band + 1}", storey=storey_tag,
            category=_SLEEVE_CATEGORY, outline=band_outline, z0_m=band_z0, z1_m=band_z1))


def _sleeve_bore(model: ResolvedModel, sleeve: ResolvedSleeve,
                 outline: Ring) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """A horizontal sleeve's two plan endpoints: the host's normal, clipped to the host.

    A wall states its own normal — perpendicular to its axis. A footing has no axis (an
    under-footing crossing goes across a strip pour), so the direction comes off the shape
    instead: the short side of the footprint's minimum rotated rectangle, which is
    across-the-strip for the same reason the wall normal is across-the-wall. Clipping the
    probe to the footprint gives the bore the host's real thickness at that point rather
    than a nominal one, and because it is a plain intersection a stepped or chamfered pour
    needs no special case.
    """
    from shapely.geometry import LineString, Polygon

    footprint = Polygon(outline)
    direction = None
    if sleeve.host_category == "wall":
        wall = model.wall(sleeve.host_slab)
        if wall is not None:
            (x0, y0), (x1, y1) = wall.axis
            dx, dy = x1 - x0, y1 - y0
            norm = math.hypot(dx, dy)
            if norm > 1e-9:
                direction = (-dy / norm, dx / norm)
    if direction is None:
        direction = _short_axis(footprint)
    if direction is None:
        return None
    (cx, cy), (ux, uy) = sleeve.center, direction
    inside = footprint.intersection(LineString((
        (cx - ux * _SLEEVE_BORE_PROBE_M, cy - uy * _SLEEVE_BORE_PROBE_M),
        (cx + ux * _SLEEVE_BORE_PROBE_M, cy + uy * _SLEEVE_BORE_PROBE_M))))
    travel = [(x - cx) * ux + (y - cy) * uy
              for part in getattr(inside, "geoms", (inside,))
              for x, y in getattr(part, "coords", ())]
    if not travel or max(travel) - min(travel) < 1e-6:
        return None
    lo, hi = min(travel), max(travel)
    return (cx + ux * lo, cy + uy * lo), (cx + ux * hi, cy + uy * hi)


def _short_axis(footprint) -> tuple[float, float] | None:
    """The unit plan direction across a footprint's narrow dimension.

    This is the minimum-area bounding rectangle's shortest-edge direction, computed here
    by rotating calipers rather than by calling shapely's ``minimum_rotated_rectangle``.
    GEOS 3.13 emits a spurious ``RuntimeWarning: invalid value encountered in
    oriented_envelope`` for *any* convex hull carrying an axis-parallel edge — it takes an
    edge slope, so ``dy/dx`` is ±inf and ``inf - inf`` is NaN, setting the IEEE flag numpy
    then reports, even though the rectangle it returns is correct. These footprints are
    slab and footing outlines, so that fired on every load of ``houses/catlin``.

    Minimum *area*, not minimum *width*: the two agree for a rectangle but diverge for an
    L-shaped slab, and substituting one for the other moved real sleeve bores.

    Hulls here have a handful of vertices, so the O(n^2) sweep costs less than the second
    polygon GEOS was building.
    """
    hull = getattr(getattr(footprint, "convex_hull", None), "exterior", None)
    corners = list(hull.coords)[:-1] if hull is not None else []
    if len(corners) < 3:
        return None
    best: tuple[float, tuple[float, float], tuple[float, float], float, float] | None = None
    for index, (ax, ay) in enumerate(corners):
        bx, by = corners[(index + 1) % len(corners)]
        ex, ey = bx - ax, by - ay
        norm = math.hypot(ex, ey)
        if norm <= 1e-12:
            continue
        along = (ex / norm, ey / norm)
        across = (-along[1], along[0])
        us = [(x - ax) * along[0] + (y - ay) * along[1] for x, y in corners]
        vs = [(x - ax) * across[0] + (y - ay) * across[1] for x, y in corners]
        width, height = max(us) - min(us), max(vs) - min(vs)
        area = width * height
        if best is None or area < best[0]:
            best = (area, along, across, width, height)
    if best is None:
        return None
    _, along, across, width, height = best
    return along if width <= height else across


def _expected_sleeve_point(model: ResolvedModel,
                           sleeve: SleevePenetration) -> tuple[float, float] | None:
    """Where the sleeve should be, in a fixed precedence — three sources, most explicit
    first, so the answer never depends on what happens to be authored elsewhere:

    1. the fixture's authored ``drain_position`` (Decision 4) — a human saying *this* is
       where the waste leaves the fixture;
    2. the nearest vertex of a routed run serving that fixture — real geometry, but the
       resolver's reading of it;
    3. the fixture-convention projection — the old heuristic, a guess by fixture kind.

    Authored beats routed deliberately. If a ``drain_position`` and the routed run
    disagree, that disagreement is the defect, and ``mep.sleeve_alignment`` should say so;
    letting the run silently override the override is how a stale flange position hides
    (which is exactly what happened to SP-M-WC2 before its re-point).
    """
    authored = _authored_drain_point(model, sleeve.serves_fixture)
    if authored is not None:
        return authored
    pipe_point = _pipe_expected_point(model, sleeve)
    if pipe_point is not None:
        return pipe_point
    return _expected_drain_point(model, sleeve.serves_fixture)


_PIPE_SLEEVE_SNAP_M = 0.3  # a routed vertex within a foot of the sleeve claims it


def _pipe_expected_point(model: ResolvedModel,
                         sleeve: SleevePenetration) -> tuple[float, float] | None:
    """The nearest vertex of a routed run that *serves the sleeve's fixture*.

    The serves link is required, not just proximity — a collector bend passing near an
    unrelated sleeve must never claim its expectation. Runs that serve nothing (or a
    sleeve serving no fixture) fall through to the fixture-convention heuristic."""
    if sleeve.serves_fixture is None:
        return None
    center = sleeve.position.xy_m
    want_drain = sleeve.purpose == Service.DRAIN
    best: tuple[float, tuple[float, float]] | None = None
    for run in model.pipe_runs:
        if sleeve.serves_fixture not in run.serves:
            continue
        if want_drain != (run.system == "drain"):
            continue
        for vertex in run.path:
            d = length(sub(vertex, center))
            if d <= _PIPE_SLEEVE_SNAP_M and (best is None or d < best[0]):
                best = (d, vertex)
    return best[1] if best is not None else None


def _authored_drain_point(model: ResolvedModel,
                          fixture_tag: str | None) -> tuple[float, float] | None:
    """Just the authored override, with no fallback — the top of the precedence chain in
    `_expected_sleeve_point`, split out so "authored" can be distinguished from "derived"."""
    if fixture_tag is None:
        return None
    fixture = model.plan.by_tag(fixture_tag)
    if not isinstance(fixture, (Fixture, Appliance)):
        return None
    return fixture.drain_position.xy_m if fixture.drain_position is not None else None


def _expected_drain_point(model: ResolvedModel,
                          fixture_tag: str | None) -> tuple[float, float] | None:
    """Decision 4: authored ``drain_position`` wins; else convention by fixture kind."""
    if fixture_tag is None:
        return None
    fixture = model.plan.by_tag(fixture_tag)
    if not isinstance(fixture, (Fixture, Appliance)):
        return None
    if fixture.drain_position is not None:
        return fixture.drain_position.xy_m
    fixture_type = next((t for t in (*model.plan.library.fixture_types,
                                     *model.plan.library.appliance_types)
                         if t.tag == fixture.type_ref), None)
    if fixture_type is None:
        return None
    # A fixture whose type MOUNTS ON THE WALL and drains does not drop under its own
    # footprint: the waste turns down inside the wall, behind the body, in the carrier's
    # bay. The type says where — its DRAIN ``ServicePort`` is stated in the product's own
    # local frame — so read that and rotate it into the plan rather than making a human
    # restate it as a ``drain_position`` on every instance.
    #
    # This branch has to come FIRST. A wall-hung water closet has no hot connection either,
    # so the "no WATER_HOT" heuristic below would otherwise claim it and put the drop a
    # foot in front of where the pipe actually is.
    if fixture_type.mount.kind is MountKind.WALL:
        port = next((p for p in fixture_type.ports if p.service is Service.DRAIN), None)
        backing = backing_wall(model.plan, model, fixture, fixture_type)
        if port is not None:
            local = (port.position[0].meters, port.position[1].meters)
            point = _rotate_into_plan(fixture, local)
            # The port's set-back is a PRODUCT nominal, measured off the frame's own face:
            # "1 3/4" behind the frame" says nothing about how thick the gypsum in front of
            # it is, and the type cannot know. What is actually true of the pipe is that it
            # runs down the middle of the bay it stands in, so the nominal is projected onto
            # the host wall's axis — the same wall ``framing/carriers`` frames the bay in.
            # At catlin that is the difference between a 3" (3.5" OD) drop centred in a
            # 5 1/2" cavity and one poking an eighth of an inch out through the drywall.
            return point if backing is None else _project_onto_line(point, backing[0].axis)
    # A water closet is the only common fixture with no hot-water connection — the one
    # reliable signal in this schema that a fixture is floor-drained (drain at its own
    # footprint) rather than wall-drained (trap arm back to a wet-wall stack).
    if Service.WATER_HOT not in fixture_type.needs:
        return fixture.position.xy_m
    if fixture.wall_ref is None:
        return None
    wall = model.wall(fixture.wall_ref)
    if wall is None:
        return None
    return _project_onto_line(fixture.position.xy_m, wall.axis)


def _rotate_into_plan(fixture, local: tuple[float, float]) -> tuple[float, float]:
    """A point in the product's local frame, placed at the fixture's position/rotation.

    The same frame every placeable symbol is drawn in (``model/placeable_symbols/_frame``):
    origin at the footprint centre, ``+y`` toward the object's back.
    """
    radians = math.radians(_fixture_degrees(fixture))
    cos, sin = math.cos(radians), math.sin(radians)
    x, y = local
    px, py = fixture.position.xy_m
    return (px + x * cos - y * sin, py + x * sin + y * cos)


def _fixture_degrees(fixture) -> float:
    degrees = getattr(getattr(fixture, "rotation", None), "degrees", None)
    return float(degrees) if degrees is not None else 0.0


def _project_onto_line(
    point: tuple[float, float], axis: tuple[tuple[float, float], tuple[float, float]]
) -> tuple[float, float]:
    (x0, y0), (x1, y1) = axis
    dx, dy = x1 - x0, y1 - y0
    denom = dx * dx + dy * dy
    if denom < 1e-12:
        return (x0, y0)
    t = ((point[0] - x0) * dx + (point[1] - y0) * dy) / denom
    return (x0 + t * dx, y0 + t * dy)
