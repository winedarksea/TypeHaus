"""Bend degrees between pull points — NEC 358.26 / 352.26 / 344.26 / 342.26 / 362.26.

Every raceway article says the same thing: no more than the equivalent of four quarter
bends (360° total) between pull points. This module measures it; ``checks/mep/
conduit_bends.py`` grades it, and it lives in ``resolve`` so a router may read it too.

**What a pull point is.** A run's two ends, and every vertex it authors in
``ConduitRun.pull_points``. One exception: when exactly one run ends at a 3D point and
exactly one other run starts there, the two are one raceway drawn as two polylines (a
``ConduitRun`` could once rise only at its last point), so they CHAIN and the joint's angle
counts. Several runs leaving one point (the panel) or a run starting mid-way along another
(a tee) is a box. A tee does not split its host: nothing authored a box on the host there,
and assuming one would hide the very overage this measures — author the pull point.

**Angles are 3D** (``sweep.path_turns``): a riser off a horizontal leg is the 90° a
bender puts in it, and a 2" dodge over a beam is two small bends that count. A bend AT a
pull point is not counted — the box or conduit body takes it.

A run without authored per-vertex ``elevations`` has a reconstructed profile; its section
is reported with ``schematic_tags`` and must not be graded as placed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.geometry_ir import Vec3
from typehaus.resolve.mep_queries import conduit_vertical_profile
from typehaus.resolve.mep_soffit import DUCT_JOINT_TOLERANCE_M
from typehaus.resolve.model import ResolvedConduitRun
from typehaus.resolve.sweep import path_turns

#: The equivalent of four quarter bends, the same figure in every raceway article.
MAX_BEND_DEG_BETWEEN_PULLS = 360.0

#: Consecutive vertices closer than this are one vertex (a repeated plan point at one z).
_SAME_VERTEX_M = 1e-6


@dataclass(frozen=True)
class Bend:
    run_tag: str
    vertex: int  # authored path index on ``run_tag``; a chain joint is the feeding run's last
    degrees: float


@dataclass(frozen=True)
class PullSection:
    """One pull-to-pull stretch of raceway, possibly spanning chained runs."""

    run_tags: tuple[str, ...]
    starts_at: str
    ends_at: str
    bends: tuple[Bend, ...]
    schematic_tags: tuple[str, ...] = ()  # runs whose z is reconstructed, not authored

    @property
    def total_deg(self) -> float:
        return sum(bend.degrees for bend in self.bends)

    @property
    def gradable(self) -> bool:
        return not self.schematic_tags


@dataclass(frozen=True)
class _Vertex:
    point: Vec3
    run_tag: str
    index: int
    pull: bool
    schematic: bool


def _profile(run: ResolvedConduitRun) -> tuple[list[Vec3], list[int], bool] | None:
    """``(points, authored index per point, schematic)``, or None with no z at all."""
    if run.z_m is not None and len(run.z_m) == len(run.path) >= 2:
        points = [(p[0], p[1], z) for p, z in zip(run.path, run.z_m, strict=True)]
        return points, list(range(len(points))), False
    rebuilt = conduit_vertical_profile(run)
    if rebuilt is None:
        return None
    path, z = rebuilt
    last = len(run.path) - 1
    points = [(p[0], p[1], zz) for p, zz in zip(path, z, strict=True)]
    return points, [min(i, last) for i in range(len(points))], True


def _near(a: Vec3, b: Vec3) -> bool:
    return (math.hypot(a[0] - b[0], a[1] - b[1]) <= DUCT_JOINT_TOLERANCE_M
            and abs(a[2] - b[2]) <= DUCT_JOINT_TOLERANCE_M)


def _chains(runs: list[ResolvedConduitRun],
            profiles: dict[str, tuple[list[Vec3], list[int], bool]]) -> list[list[str]]:
    """Runs grouped into raceways: one-in/one-out end->start joints chain, nothing else."""
    tags = [run.tag for run in runs if run.tag in profiles]
    starts = {tag: profiles[tag][0][0] for tag in tags}
    ends = {tag: profiles[tag][0][-1] for tag in tags}
    following: dict[str, str] = {}
    for tag in tags:
        leaving = [other for other in tags if other != tag and _near(starts[other], ends[tag])]
        arriving = [other for other in tags if _near(ends[other], ends[tag])]
        if len(leaving) == 1 and arriving == [tag]:
            following[tag] = leaving[0]
    fed = set(following.values())
    chains: list[list[str]] = []
    seen: set[str] = set()
    # Heads first; whatever is left is a loop, broken at its first run in model order.
    for tag in [t for t in tags if t not in fed] + tags:
        if tag in seen:
            continue
        chain = []
        while tag is not None and tag not in seen:
            seen.add(tag)
            chain.append(tag)
            tag = following.get(tag)
        chains.append(chain)
    return chains


def _vertices(chain: list[str], by_tag: dict[str, ResolvedConduitRun],
              profiles: dict[str, tuple[list[Vec3], list[int], bool]]) -> list[_Vertex]:
    out: list[_Vertex] = []
    for position, tag in enumerate(chain):
        points, indices, schematic = profiles[tag]
        pulls = set(by_tag[tag].pull_points)
        for j, (point, index) in enumerate(zip(points, indices, strict=True)):
            if position > 0 and j == 0:
                continue  # the joint is the feeding run's last vertex
            end = ((position == 0 and j == 0)
                   or (position == len(chain) - 1 and j == len(points) - 1))
            vertex = _Vertex(point, tag, index, end or index in pulls, schematic)
            if out and math.dist(out[-1].point, point) <= _SAME_VERTEX_M:
                if vertex.pull and not out[-1].pull:
                    out[-1] = _Vertex(out[-1].point, out[-1].run_tag, out[-1].index,
                                      True, out[-1].schematic)
                continue
            out.append(vertex)
    return out


def _label(vertex: _Vertex, first: bool, last: bool) -> str:
    if first:
        return f"{vertex.run_tag} start"
    if last:
        return f"{vertex.run_tag} end"
    return f"{vertex.run_tag} pull point at vertex {vertex.index}"


def _sections(chain: list[str], by_tag: dict[str, ResolvedConduitRun],
              profiles: dict[str, tuple[list[Vec3], list[int], bool]]) -> list[PullSection]:
    vertices = _vertices(chain, by_tag, profiles)
    if len(vertices) < 2:
        return []
    angles = {turn.index: turn.angle_deg
              for turn in path_turns([v.point for v in vertices])}
    sections: list[PullSection] = []
    head = 0
    tags: list[str] = []
    schematic: list[str] = []
    bends: list[Bend] = []
    for i in range(1, len(vertices)):
        owner = vertices[i].run_tag  # a segment belongs to the run it arrives on
        if owner not in tags:
            tags.append(owner)
        if vertices[i].schematic and owner not in schematic:
            schematic.append(owner)
        last = i == len(vertices) - 1
        if not (vertices[i].pull or last):
            if i in angles:
                bends.append(Bend(vertices[i].run_tag, vertices[i].index, angles[i]))
            continue
        sections.append(PullSection(
            run_tags=tuple(tags), starts_at=_label(vertices[head], head == 0, False),
            ends_at=_label(vertices[i], False, last), bends=tuple(bends),
            schematic_tags=tuple(schematic)))
        head, tags, schematic, bends = i, [], [], []
    return sections


def pull_sections(runs: list[ResolvedConduitRun]) -> list[PullSection]:
    """Every pull-to-pull section of every raceway, in model order."""
    by_tag = {run.tag: run for run in runs}
    profiles = {run.tag: prof for run in runs if (prof := _profile(run)) is not None}
    out: list[PullSection] = []
    for chain in _chains(list(runs), profiles):
        out.extend(_sections(chain, by_tag, profiles))
    for run in runs:
        if run.tag not in profiles:
            out.append(PullSection(run_tags=(run.tag,), starts_at=f"{run.tag} start",
                                   ends_at=f"{run.tag} end", bends=(),
                                   schematic_tags=(run.tag,)))
    return out
