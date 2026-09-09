"""Authored backing bands, laid on a wall's stud face (→ ``model/backing.py``).

The counterpart to ``framing/backing.py``'s ``append_blocking_rows``, and deliberately a
different member. That one reads ``FramingSpec.blocking_heights`` and fits a flat course
*between* studs, one block per bay, for every wall of an assembly. This one reads a placed
``WallBacking`` and lays one continuous band *across* the studs over a stated run — which is
the whole point of backing, since a bar or a bracket lands wherever it lands and a band that
stops at each stud is not a target.

A band is authored, never derived. The engine will say a wall-mounted body has nothing
behind it (→ ``checks/advisory/backing.py``) and stops there, because backing placed only
where today's model's screws land pins the house to today's model forever — the reasoning
``houses/catlin/plan/fixture_types_wc.py`` already sets out.

**Elevation is measured from the wall's framing base**, ``ResolvedWall.base_ref_z_m``, the
same datum an opening's ``sill_m`` uses and the same one ``Mount.elevation`` means by "above
the storey datum". That is what makes the coverage check's comparison honest: a band and the
cabinet it backs are read off one datum rather than two that agree by luck.

A leaf: it imports ``model``/``resolve`` and is imported by ``framing/solver.py``, never the
other way round.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.backing import WallBacking
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember, ResolvedWall

__all__ = ["BackingBand", "backing_bands", "append_backing_members"]

_EPSILON = 1e-9
#: A surviving run shorter than this is a sliver, not a board — a band clipped by an opening
#: to half an inch is a cut nobody makes. One stud face wide.
_MIN_RUN_M = 1.5 * 0.0254


@dataclass(frozen=True)
class BackingBand:
    """One authored band, reduced to what the framing pass needs."""

    tag: str
    wall_ref: str
    face: str
    start_m: float | None   # None = the start of the wall
    length_m: float | None  # None = to the end of the wall
    elevation_m: float
    height_m: float
    profile: str
    material_ref: str
    purpose: str


def backing_bands(plan: PlanModel) -> dict[str, list[BackingBand]]:
    """``{wall_tag: [BackingBand, ...]}`` for every authored ``WallBacking``.

    Reads the plan, not the resolved model, for the same reason ``carrier_bands`` does: this
    runs *inside* wall resolution, so the walls it would consult are the ones being built.
    A band naming a wall that does not exist survives to ``checks/advisory/backing.py``,
    which reports it — dropping it silently here would delete a band on a typo (#32).
    """
    bands: dict[str, list[BackingBand]] = {}
    for element in plan.all_elements():
        if not isinstance(element, WallBacking):
            continue
        bands.setdefault(element.wall_ref, []).append(BackingBand(
            tag=element.tag,
            wall_ref=element.wall_ref,
            face=element.face,
            start_m=None if element.start is None else element.start.meters,
            length_m=None if element.length is None else element.length.meters,
            elevation_m=element.elevation.meters,
            height_m=element.height.meters,
            profile=element.profile,
            material_ref=element.material_ref,
            purpose=element.purpose,
        ))
    return bands


#: Members a band may not cross. A band is *meant* to run over studs, kings, jacks and
#: cripples — that is what backing is — but a header and a rough sill fill the wall depth,
#: so a board laid on the stud face lands inside them. A framer stops the board at the king.
_SOLID_CATEGORIES = frozenset({"header", "sill"})


def _station(point, direction, wall_start) -> float:
    """Where a plan point falls along the wall axis, in meters from the start node."""
    return ((point[0] - wall_start[0]) * direction[0]
            + (point[1] - wall_start[1]) * direction[1])


def _opening_breaks(members: list[FramedMember], parent_uid: str, band_bottom: float,
                    band_top: float, direction, wall_start,
                    openings: list[WallOpening], frame_base: float,
                    ) -> list[tuple[float, float]]:
    """The ``(start, end)`` stations a band cannot cross, sorted.

    Derived from the opening framing this wall has **already emitted**, not from the rough
    openings themselves, and that is the whole point: a rough opening's head is not the top
    of its framing. A band at 94" clears a 7'-0" door's head by ten inches and lands square
    in the 2x10 header above it, which is what ``structural.member_interference`` reported
    the first time this ran. Reading the members means the break follows whatever header the
    solver actually chose, at whatever depth, with no second table to keep in step.

    Two kinds of break, and a band needs both. The **void** of a rough opening is one: a
    board across the glass is a board spanning nothing. The **framing above and below** that
    void is the other, and it is the one that is easy to miss.

    Only openings the band runs *through*. A band at 34" is not interrupted by a window
    whose sill is at 42" — it passes under it, which is where a framer wants it to keep going.
    """
    breaks: list[tuple[float, float]] = []
    for opening in openings:
        sill = frame_base + opening.sill_m
        if sill + opening.height_m <= band_bottom + _EPSILON or sill >= band_top - _EPSILON:
            continue
        half = opening.width_m / 2.0
        breaks.append((opening.center_m - half, opening.center_m + half))
    for member in members:
        if member.parent_uid != parent_uid or member.category not in _SOLID_CATEGORIES:
            continue
        if member.z1_m <= band_bottom + _EPSILON or member.z0_m >= band_top - _EPSILON:
            continue
        low = _station(member.p0, direction, wall_start)
        high = _station(member.p1, direction, wall_start)
        breaks.append((min(low, high), max(low, high)))
    return sorted(breaks)


def _segments(start: float, end: float,
              breaks: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """``[start, end]`` less each break, dropping runs too short to be a board."""
    runs = [(start, end)]
    for b0, b1 in breaks:
        nxt: list[tuple[float, float]] = []
        for s0, s1 in runs:
            if b1 <= s0 or b0 >= s1:
                nxt.append((s0, s1))
                continue
            if s0 < b0:
                nxt.append((s0, min(b0, s1)))
            if s1 > b1:
                nxt.append((max(b1, s0), s1))
        runs = nxt
    return [(s0, s1) for s0, s1 in runs if s1 - s0 > _MIN_RUN_M]


def append_backing_members(members: list[FramedMember], rw: ResolvedWall,
                           bands: list[BackingBand], direction, wall_start,
                           frame_base: float, axis_len: float, top_at,
                           openings: list[WallOpening]) -> None:
    """Emit one member per surviving run of each band on this wall.

    Three things clip a band, and each of them is a real carpentry limit rather than a
    tidiness rule:

    * **The wall's ends.** A run authored past them is trimmed, not extended.
    * **An opening it passes through.** Split, never bridged — a band across a window is a
      board the framer cannot install. An opening it passes *under* or *over* does not
      interrupt it.
    * **A raking stud top.** ``top_at`` is the same callable the corner, opening, tee and
      blocking framing already take. Under a ``ToRoof`` top the studs rake, and a band
      authored at 6'-0" on a wall that is 4'-0" tall at its low end has nothing to fasten
      to there. Without this the board flies out through the roof, silently — the failure
      ``framing/backing.py`` records at catlin's ``W-A-SN``.
    """
    if not bands or axis_len <= _MIN_RUN_M:
        return
    for index, band in enumerate(sorted(bands, key=lambda b: (b.elevation_m, b.tag))):
        bottom = frame_base + band.elevation_m
        top = bottom + band.height_m
        start = max(0.0, band.start_m if band.start_m is not None else 0.0)
        end = axis_len if band.length_m is None else min(axis_len, start + band.length_m)
        if end - start <= _MIN_RUN_M:
            continue
        breaks = _opening_breaks(members, rw.uid, bottom, top, direction, wall_start,
                                 openings, frame_base)
        for ordinal, (s0, s1) in enumerate(_segments(start, end, breaks)):
            # The conservative end of a raking run: if the LOWER of the two stud tops cannot
            # reach the band's top, the run has bays with nothing behind it.
            if min(top_at(s0), top_at(s1)) < top - _EPSILON:
                continue
            a = add(wall_start, scale(direction, s0))
            b = add(wall_start, scale(direction, s1))
            members.append(FramedMember(
                rw.uid, f"backing-{index}-{ordinal:03d}", "blocking", band.profile,
                a, b, bottom, top, s1 - s0, material=band.material_ref,
            ))


def band_face_height_m(profile: str) -> float:
    """The band's face dimension — how tall the board reads on the wall.

    Authored ``height`` is what the coverage check grades, and this is what the section
    string says the board actually is. They should agree; ``advisory.wall_backing_ref``
    reports it when they do not, because a "0.75x12.0" band authored 4" tall is one of
    the two numbers being wrong and the engine cannot tell which.
    """
    return cross_section(profile).depth_m
