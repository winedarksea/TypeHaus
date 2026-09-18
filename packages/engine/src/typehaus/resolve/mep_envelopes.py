"""What a run actually OCCUPIES, and the one place that is derived.

Three consumers used to answer this three times. ``checks/mep/routing_geometry`` derived a
run's polyline and its real outside radius; ``checks/mep/routing_openings`` derived the
rough-opening prisms; and ``routing/obstacles`` derived both again, because the leaf rule
forbids a router importing a check. Two of the three readings disagreed — the router put
every opening at the wall's ``z0_m`` rather than its ``base_ref_z_m``, which is 13 7/16"
out on catlin's main-storey exterior walls, far enough to miss a run crossing one — and the
third had a defect nobody had written down.

``resolve`` is the layer **both** may import, so the derivations live here and each consumer
becomes a reader. That is what the leaf rule is for: it constrains direction, not
self-sufficiency.

**The defect, stated plainly.** ``routing/obstacles`` buffered a run's whole plan polyline
and banded it over ``min(z)..max(z)`` — one prism for the entire run. A branch that drops
six feet at one end therefore blocked a full-height wall along its whole length, which is
how a perfectly clear lane comes back as "every lane is blocked". An envelope here is **one
prism per segment, over that segment's own z range**.

**A rectangular duct is not its own diagonal.** ``routing/trades/duct.radius_m`` takes half
the LARGER plan dimension because it has no fitting model and must be conservative at a
turn. An envelope knows which way each leg runs, so it uses the real pair: ``width`` across
the run in plan, ``depth`` vertically. A 10x8 duct is 10" wide and 8" deep, not 10" cubed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: A run whose surface comes within this of a rough opening's edge is not reported by the
#: CHECK. A raceway strapped to a jack stud shares a coordinate with the opening beside it,
#: and grading that as "through the window" would be wrong in exactly the case the trade
#: does on purpose. **The router erodes by nothing**, and that is the whole difference
#: between the two readings: a check's tolerance is forgiveness after the fact, and a router
#: proposing a lane half an inch wide has nothing to forgive.
OPENING_EDGE_M = 0.0127


@dataclass(frozen=True)
class Prism:
    """One segment's occupied volume: a plan footprint and its own z band.

    ``footprint`` is a shapely polygon and is already inflated by whatever the caller asked
    for. ``z0_m``/``z1_m`` bound the run's SURFACE, not its centreline.
    """

    tag: str
    kind: str  # "pipe" | "duct" | "conduit"
    footprint: Any
    z0_m: float
    z1_m: float
    #: Index of the segment within the run, so a finding can say which leg.
    segment: int = 0


@dataclass(frozen=True)
class Envelope:
    """Every prism of one run, plus what could not be derived about it."""

    tag: str
    kind: str
    prisms: tuple[Prism, ...] = ()
    #: Sentences a consumer must print rather than swallow — an insulation spec with no
    #: readable thickness, a raceway whose profile is two endpoints and not a route.
    gaps: tuple[str, ...] = ()

    @property
    def z0_m(self) -> float:
        return min((p.z0_m for p in self.prisms), default=0.0)

    @property
    def z1_m(self) -> float:
        return max((p.z1_m for p in self.prisms), default=0.0)


#: ``1"``, ``1/2"``, ``1-1/2"`` at the head of an insulation spec. Deliberately narrow: a
#: spec that does not begin with a dimension gets no guess at all. "R-8 wrap" is about two
#: inches in the trade and this will not say so — an R-value is a thermal claim and an
#: envelope is a dimensional one, and inferring the second from the first is the kind of
#: confident nonsense that is worse than an UNKNOWN.
_THICKNESS = re.compile(r'^\s*(\d+)?\s*[-\s]?\s*(?:(\d+)\s*/\s*(\d+))?\s*(?:"|in\b)')


def insulation_thickness_m(spec: str | None) -> float | None:
    """The wall thickness a lagging spec states, or None when it states none."""
    if not spec:
        return 0.0
    match = _THICKNESS.match(spec)
    if match is None:
        return None
    whole, numerator, denominator = match.groups()
    inches = float(whole or 0)
    if numerator and denominator and float(denominator):
        inches += float(numerator) / float(denominator)
    return inches * M_PER_IN if inches else None


def run_radii(model: ResolvedModel) -> dict[str, float]:
    """Half the **real** outside dimension of each run, keyed by tag.

    A run is a centreline and an opening is a hole; whether the two meet is a question about
    the run's SURFACE. Six inches of duct with an inch of wrap either side is eight inches
    of obstruction, and grading its centreline alone under-reports by four.

    The nominal->outside conversion is :mod:`typehaus.resolve.pipe_sections`. The error it
    corrects is 0.172" on 3/4" EMT and half an inch on 3" DWV, and on catlin it was hiding
    two raceways bored into a chord.

    A duct's authored diameter **is** its outside dimension — sheet metal is specified by
    the size it measures, not by a nominal — so ducts pass through unconverted.
    """
    from typehaus.resolve.pipe_sections import (
        pipe_outside_diameter_m,
        raceway_outside_diameter_m,
    )

    radii: dict[str, float] = {}
    for run in model.pipe_runs:
        radii[run.tag] = pipe_outside_diameter_m(run.diameter_m or 0.0, run.material) / 2.0
    for duct in model.ducts:
        radii[duct.tag] = (duct.diameter_m or max(duct.width_m, duct.depth_m)) / 2.0
    for raceway in model.conduits:
        radii[raceway.tag] = raceway_outside_diameter_m(raceway.trade_size_m or 0.0) / 2.0
    for tag, _path, _z, diameter_m in vent_risers(model):
        radii[tag] = diameter_m / 2.0
    return radii


def vent_risers(model: ResolvedModel
                ) -> list[tuple[str, tuple[tuple[float, float], ...],
                                tuple[float, ...], float]]:
    """Every ``VentRun``'s bundled risers, as ``(tag, plan path, per-vertex z)``.

    A ``VentRun`` is a parametric chase riser, not a polyline, and so it used to resolve to
    ``ResolvedSolid``s alone: no envelope, nothing for ``mep.run_interference`` to grade,
    and — since ``routing/obstacles`` iterates envelopes — **not a router obstacle**. A
    campaign would lane a duct straight through the radon riser and call it clear.

    The derivation is :func:`typehaus.resolve.vent_termination.riser_polylines`, which
    ``resolve/accessories`` also reads to build the solids. One derivation, two readers.
    """
    from typehaus.model.mep import VentRun
    from typehaus.resolve.vent_termination import riser_polylines

    out = []
    for element in model.plan.all_elements():
        if not isinstance(element, VentRun):
            continue
        # A ``VentRun.diameter`` is the pipe as drawn — the solids are faceted circles of
        # exactly that radius — so unlike a ``PipeRun`` there is no nominal to convert.
        out.extend((tag, path, z, element.diameter.meters)
                   for tag, path, z in riser_polylines(model, element))
    return out


def run_polylines(model: ResolvedModel
                  ) -> list[tuple[str, str, tuple[tuple[float, float], ...],
                                  tuple[float, ...]]]:
    """Every routed thing, as ``(kind, tag, plan path, per-vertex z)``.

    No storey: which floor a run is *in* is decided by elevation, not by filing, so carrying
    the storey would only invite something to start reading it.

    Pipe, duct and raceway together: a hole in a deck, a rough opening and a room's air do
    not care which trade drew the line, and three near-identical loops would be three places
    for the rule to drift. A raceway's z comes from
    :func:`~typehaus.resolve.mep_queries.conduit_vertical_profile`, which owns the one
    reading a leaf can reach of "a ConduitRun rises at its last point" — and now prefers the
    run's own authored ``z_m`` where it has one.

    The z values are **centrelines**. Anything asking about the run's surface adds
    :func:`run_radii`.
    """
    from typehaus.resolve.mep_queries import conduit_vertical_profile

    out = []
    for run in model.pipe_runs:
        z = tuple(run.z_m) if run.z_m and len(run.z_m) == len(run.path) else ()
        out.append(("pipe", run.tag, tuple(run.path), z))
    for duct in model.ducts:
        z = tuple(duct.z_m) if len(duct.z_m) == len(duct.path) else ()
        out.append(("duct", duct.tag, tuple(duct.path), z))
    for raceway in model.conduits:
        profile = conduit_vertical_profile(raceway)
        if profile is None:
            out.append(("conduit", raceway.tag, tuple(raceway.path), ()))
            continue
        path, z = profile
        out.append(("conduit", raceway.tag, tuple(path), tuple(z)))
    # A ``VentRun`` is a chase riser rather than an authored polyline, and is trade "pipe"
    # because that is what it is: three storeys of 3" DWV standing in a chase.
    for tag, path, z, _diameter_m in vent_risers(model):
        out.append(("pipe", tag, path, z))
    return out


def run_sections(model: ResolvedModel) -> dict[str, tuple[float, float, str | None]]:
    """``tag -> (plan half-width, vertical half-height, insulation spec)``, surface not axis.

    The pair is what separates this from :func:`run_radii`. A round run's two numbers are
    equal and the distinction costs nothing; a 10x8 rectangular duct is 5" across and 4"
    tall, and calling it 5" in both directions over-reports its depth by a fifth.
    """
    radii = run_radii(model)
    out: dict[str, tuple[float, float, str | None]] = {}
    for run in model.pipe_runs:
        out[run.tag] = (radii[run.tag], radii[run.tag], run.insulation)
    for duct in model.ducts:
        if duct.diameter_m:
            out[duct.tag] = (radii[duct.tag], radii[duct.tag], duct.insulation)
        else:
            out[duct.tag] = (duct.width_m / 2.0, duct.depth_m / 2.0, duct.insulation)
    for raceway in model.conduits:
        out[raceway.tag] = (radii[raceway.tag], radii[raceway.tag], None)
    for tag, _path, _z, diameter_m in vent_risers(model):
        out[tag] = (diameter_m / 2.0, diameter_m / 2.0, None)
    return out


def run_envelope(kind: str, tag: str, path: Any, z: Any,
                 section: tuple[float, float, str | None], *,
                 inflate_m: float = 0.0) -> Envelope:
    """One prism per segment, banded over that segment's own z range.

    ``inflate_m`` is the caller's clearance and is applied in plan and in elevation alike.
    A router passes ``radius + clearance``; a check comparing two runs passes the gap it is
    grading against, or zero and compares the prisms.

    A **riser** — a repeated plan point at two elevations — has no plan length, so its
    footprint is the point buffered. It is still a prism: a vertical standing in a doorway
    is the defect ``mep.run_through_opening`` was written for, and a segment-length test
    would drop it.
    """
    from shapely.geometry import LineString, Point

    half_w, half_d, insulation = section
    lagging = insulation_thickness_m(insulation)
    gaps: list[str] = []
    if lagging is None:
        gaps.append(f"{tag}: its insulation spec ({insulation!r}) states no thickness, so "
                    "the envelope is the bare run — an R-value is a thermal claim and this "
                    "is a dimensional one")
        lagging = 0.0
    if len(path) < 2 or len(z) != len(path):
        return Envelope(tag=tag, kind=kind, gaps=(
            *gaps, f"{tag}: fewer than two vertices or no resolved elevations, so it has "
                   "no envelope — it is a schematic profile, not a placed run"))

    grow_plan = half_w + lagging + inflate_m
    grow_z = half_d + lagging + inflate_m
    prisms = []
    for index in range(len(path) - 1):
        a, b = path[index], path[index + 1]
        za, zb = z[index], z[index + 1]
        geometry = (Point(a) if a == b else LineString([a, b]))
        footprint = geometry.buffer(grow_plan)
        if footprint.is_empty:
            continue
        prisms.append(Prism(tag=tag, kind=kind, footprint=footprint,
                            z0_m=min(za, zb) - grow_z, z1_m=max(za, zb) + grow_z,
                            segment=index))
    return Envelope(tag=tag, kind=kind, prisms=tuple(prisms), gaps=tuple(gaps))


def envelopes(model: ResolvedModel, *, inflate_m: float = 0.0) -> list[Envelope]:
    """Every run's envelope, in ``run_polylines`` order."""
    sections = run_sections(model)
    return [run_envelope(kind, tag, path, z,
                         sections.get(tag, (0.0, 0.0, None)), inflate_m=inflate_m)
            for kind, tag, path, z in run_polylines(model)]


def opening_prisms(model: ResolvedModel, *, erode_m: float = OPENING_EDGE_M
                   ) -> list[tuple[str, bool, str, Any, float, float, tuple[str, ...]]]:
    """Each opening as ``(tag, is_door, host, footprint, z low, z high, penetration_for)``.

    The footprint is the opening's slice of its host wall through the WHOLE wall thickness,
    because that is the hole: a window buck runs the full depth of the assembly, and a run
    that crosses the opening's width anywhere in that depth is in it. The band is the host
    wall's FRAMING base plus the authored sill, which is how ``resolve`` places the buck.

    ``base_ref_z_m``, not ``z0_m``: a wall extended down over the rim keeps its floor where
    the framing is. Reading ``z0_m`` put every opening in catlin's main-storey exterior
    walls 13 7/16" below where it is built, which is exactly far enough to miss a run
    crossing it — and is what ``routing/obstacles`` was doing while the check beside it did
    not.

    ``erode_m`` is the whole difference between the check's reading and the router's, and it
    is a parameter rather than a second function so the two cannot drift: the check forgives
    half an inch at an opening's edge because a raceway strapped to a jack stud shares a
    coordinate with it; a router proposing that same lane has nothing to forgive and passes
    ``0.0``.

    **A door's swing is not modelled.** The swing is a hard obstacle in its own right and
    would need a reading of hinge side and hand; a route through a closed door's buck is
    already refused by the buck itself.
    """
    import math

    from shapely.geometry import Polygon

    walls = {wall.tag: wall for wall in model.walls}
    out = []
    for opening in model.openings:
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
        if erode_m:
            prism = prism.buffer(-erode_m)
        if prism.is_empty or not prism.is_valid:
            continue
        low = wall.base_ref_z_m + opening.sill_m
        out.append((opening.tag, bool(opening.is_door), wall.tag, prism,
                    low, low + opening.height_m, tuple(opening.penetration_for or ())))
    return out


#: How close two runs' ends have to be before they are a fitting rather than a clash. The
#: duct side of this is ``resolve/mep_soffit.DUCT_JOINT_TOLERANCE_M`` and this reuses it, so
#: "these two are plumbed together" means one thing across every trade.
def joint_tolerance_m() -> float:
    from typehaus.resolve.mep_soffit import DUCT_JOINT_TOLERANCE_M

    return DUCT_JOINT_TOLERANCE_M


def run_joints(first: tuple[Any, Any], second: tuple[Any, Any]
               ) -> tuple[tuple[tuple[float, float], float | None], ...]:
    """Where these two runs are plumbed together — each joint's ``(plan point, z)``.

    Only an END counts, which is the rule ``resolve/mep_soffit.ducts_are_joined`` already
    states for ducts and the reason it states it: two runs crossing mid-span are two runs
    crossing, and that is precisely the case an interference check exists to report.
    Generalised to every trade here because a 3" drain tee'd into a 4" main and a 6" branch
    tee'd into a trunk are the same geometry and should not be two rules.

    **Locations, not a bool.** A pair may be jointed at one end and cross two feet away, and
    a single bool exempted the whole pair — the crossing went unreported. A consumer gets
    the joints and decides for itself whether the contact it is looking at is one of them.
    """
    from typehaus.resolve.mep_soffit import duct_joint_index

    out: list[tuple[tuple[float, float], float | None]] = []
    for (near_path, near_z), (far_path, far_z) in ((first, second), (second, first)):
        if len(near_path) < 1 or len(far_path) < 2:
            continue
        for point, z in ((near_path[0], near_z[0] if near_z else None),
                         (near_path[-1], near_z[-1] if near_z else None)):
            if duct_joint_index(point, z, far_path, far_z) is not None \
                    and (point, z) not in out:
                out.append((point, z))
    return tuple(out)


def runs_are_joined(first: tuple[Any, Any], second: tuple[Any, Any]) -> bool:
    """Whether either run **ends on** the other — a wye, a tee, an elbow, a riser into a trunk.

    Each argument is ``(path, z)``. A thin reader of :func:`run_joints`, kept because
    ``checks/mep/duct_connectivity`` asks the yes/no question and means it: "are these two
    plumbed together at all" is a different question from "is THIS contact the fitting".
    """
    return bool(run_joints(first, second))
