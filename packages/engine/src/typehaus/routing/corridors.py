"""The negative-cost half, and the reason this beats a generic router on a house.

A generic obstacle-avoiding router knows where it may not go. What makes a proposal
*buildable* is knowing where a trade would actually put the pipe, and a house states that
already: joist bays, soffits with section left, wall cavities, the plane under a slab.

Two things come out of a corridor and both matter:

* a **discount**, so a route that could ride a bay does rather than merely avoiding a
  joist — the difference between passing ``mep.duct_joist_bay`` and being aimed at it;
* a **candidate line**, seeded into :mod:`typehaus.routing.graph`, so the lattice has a
  node on the bay centre at all. A discount on a line the graph never built is worth
  nothing, and that is the failure mode this module exists to avoid.

Every derivation reads the resolved model's own queries — ``joist_line_stations``,
``clear_bay_width_m``, the soffit records — rather than re-deriving spacing from a
``JoistSpec``. ``houses/catlin/notes/mep_drain_routing_basis.md`` §3 is the hand-worked
oracle for the bay arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedFloor, ResolvedModel, ResolvedSoffit

#: The chord a floor truss's open web leaves. ``resolve/framing/profiles.open_web_opening_m``
#: owns the real number; this is the fraction of the member's depth that is chord, used only
#: when that helper cannot answer for a member — a 2x4 flat chord top and bottom.
_CHORD_M = 0.0381  # 1 1/2"


@dataclass(frozen=True)
class Corridor:
    """One channel a run may ride, cheaply.

    ``axis`` is ``"x"`` or ``"y"`` — the direction of travel, not the direction of the
    members. ``station`` is the constant coordinate on the other axis: a bay centreline at
    ``y = 8 + 16n`` is ``axis="x"``, ``station=8 + 16n``.

    ``z0_m``/``z1_m`` bound what may ride it. For a bay running WITH the members that is
    the full structural depth; for a run CROSSING them it is the web window, which is
    narrower and is the constraint a plan view hides (the note's §3).
    """

    tag: str
    kind: str  # "bay" | "soffit" | "wall" | "under-slab"
    axis: str
    station: float
    z0_m: float
    z1_m: float
    clear_width_m: float
    #: Plan extent along ``axis``; a bay does not run the width of the world.
    lo_m: float
    hi_m: float

    def admits(self, radius_m: float) -> bool:
        return 2.0 * radius_m <= self.clear_width_m + 1e-9

    def z_window(self, radius_m: float) -> tuple[float, float] | None:
        """The centreline band a run of this radius may occupy, or None if it cannot fit."""
        low, high = self.z0_m + radius_m, self.z1_m - radius_m
        return (low, high) if high >= low else None


def floor_corridors(model: ResolvedModel) -> list[Corridor]:
    """One corridor per joist/truss bay, on every resolved floor.

    The bay's own clear width comes from ``clear_bay_width_m``, which takes the MEDIAN
    line-to-line step and the WIDEST member — an end strip and a doubled line at an opening
    are both narrower than the field and neither is the bay a run rides in. Two consumers
    now read that one derivation instead of two.
    """
    from typehaus.resolve.mep_queries import clear_bay_width_m, joist_line_stations

    out: list[Corridor] = []
    for floor in model.floors:
        lines = joist_line_stations(floor)
        clear = clear_bay_width_m(floor)
        if len(lines) < 2 or clear is None or clear <= 0:
            continue
        members = [m for m in floor.members if m.z0_m is not None]
        if not members:
            continue
        low = min(m.z0_m for m in members)
        high = max(getattr(m, "z1_m", None) or floor.deck_z0_m for m in members)
        along = "x" if floor.direction == "x" else "y"
        span = _member_span(floor, along)
        if span is None:
            continue
        for index in range(len(lines) - 1):
            gap = lines[index + 1] - lines[index]
            if gap <= clear:
                continue  # a doubled pair or an end strip, not a field bay
            centre = (lines[index] + lines[index + 1]) / 2.0
            out.append(Corridor(
                tag=f"{floor.tag}:bay@{centre:.4f}", kind="bay", axis=along,
                station=centre, z0_m=low, z1_m=high, clear_width_m=clear,
                lo_m=span[0], hi_m=span[1]))
    return out


def crossing_window(model: ResolvedModel,
                    floor: ResolvedFloor) -> tuple[float, float] | None:
    """The z band a run may occupy while crossing this floor's members, or None.

    An open-web truss lets a service through its webs and an I-joist wants a bored hole;
    both come out here as a band, because what a route needs to know is the same either
    way. ``open_web_opening_m`` owns the truss reading — the note's §3 checks it by hand
    at 8 7/8" against an 11 7/8" truss — and a member it cannot answer for falls back to
    the depth less a chord at each face, which is the conservative direction.
    """
    members = [m for m in floor.members if m.z0_m is not None]
    if not members:
        return None
    low = min(m.z0_m for m in members)
    high = max(getattr(m, "z1_m", None) or floor.deck_z0_m for m in members)
    opening = _open_web_opening(members[0].profile)
    if opening is not None and opening > 0:
        margin = ((high - low) - opening) / 2.0
        return (low + margin, high - margin)
    return (low + _CHORD_M, high - _CHORD_M)


def _open_web_opening(profile: str) -> float | None:
    """The chord-to-chord opening of this member's section, or None if it has no web space.

    ``open_web_opening_m`` takes a ``CrossSection`` and a ``FramedMember.profile`` is the
    *string* that names one — a distinction that cost a silently dead branch: passing the
    string raised, the caller swallowed it, and the chord fallback happened to give the
    same 8 7/8" on catlin's truss. It answered right for the wrong reason on the one floor
    it was checked against and would have answered wrong on any other section.
    """
    from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m

    return open_web_opening_m(cross_section(profile))


def soffit_corridors(model: ResolvedModel) -> list[Corridor]:
    """One corridor per resolved soffit, along its own LONG plan dimension.

    A box's long axis is its axis — the same reading ``mep.duct_soffit_occupancy`` takes,
    and for the same reason: turn it the other way and a run's whole travel is graded as
    its "width". The clear section is what the box has LEFT, not what it started with, so
    a route into a full soffit is priced out rather than proposed.
    """
    out: list[Corridor] = []
    for soffit in model.soffits:
        bounds = _bounds(soffit.outline)
        if bounds is None:
            continue
        minx, miny, maxx, maxy = bounds
        wide = (maxx - minx) >= (maxy - miny)
        axis = "x" if wide else "y"
        station = (miny + maxy) / 2.0 if wide else (minx + maxx) / 2.0
        across = (maxy - miny) if wide else (maxx - minx)
        lo, hi = (minx, maxx) if wide else (miny, maxy)
        out.append(Corridor(tag=soffit.tag, kind="soffit", axis=axis, station=station,
                            z0_m=soffit.z0_m, z1_m=soffit.z1_m,
                            clear_width_m=max(across - _remaining_taken(model, soffit), 0.0),
                            lo_m=lo, hi_m=hi))
    return out


def wall_corridors(model: ResolvedModel) -> list[Corridor]:
    """One corridor per wall, on its axis, bounded by its structure cavity.

    A wall is a corridor and a soft obstacle at once, and that is not a contradiction:
    travelling ALONG a wall in its own cavity is what a wet wall is for, and travelling
    far along one is what bores every stud on the way. The discount is here; the penalty
    past one stud bay is :mod:`typehaus.routing.obstacles`' ``in_wall_travel_per_ft``.
    """
    out: list[Corridor] = []
    for wall in model.walls:
        if len(wall.axis) < 2:
            continue
        (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
        horizontal = abs(bx - ax) >= abs(by - ay)
        if min(abs(bx - ax), abs(by - ay)) > 1e-6:
            continue  # a raked or angled wall is not a rectilinear corridor
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        if structure is None:
            continue
        out.append(Corridor(
            tag=wall.tag, kind="wall", axis="x" if horizontal else "y",
            station=ay if horizontal else ax,
            z0_m=wall.z0_m, z1_m=wall.z1_m,
            clear_width_m=structure.thickness_m,
            lo_m=min(ax, bx) if horizontal else min(ay, by),
            hi_m=max(ax, bx) if horizontal else max(ay, by)))
    return out


def _member_span(floor: ResolvedFloor, along: str) -> tuple[float, float] | None:
    coords = [p[0] if along == "x" else p[1]
              for member in floor.members for p in (member.p0, member.p1)]
    return (min(coords), max(coords)) if coords else None


def _bounds(ring: Any) -> tuple[float, float, float, float] | None:
    if ring is None or len(ring) < 3:
        return None
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def _remaining_taken(model: ResolvedModel, soffit: ResolvedSoffit) -> float:
    """How much of a soffit's across-axis width is already spoken for.

    Ducts and pipes naming this soffit occupy it; the sum of their outside dimensions is
    what a new route cannot have. Deliberately a sum rather than a packing: the model
    gives each run one centreline per box, so it cannot say two things sit side by side —
    the same limit ``mep.duct_joist_bay_occupancy`` reports UNKNOWN about, inherited here
    rather than papered over.
    """
    taken = 0.0
    for duct in model.ducts:
        if getattr(duct, "soffit_ref", None) == soffit.tag:
            taken += duct.diameter_m or max(duct.width_m, duct.depth_m)
    for run in model.pipe_runs:
        if getattr(run, "soffit_ref", None) == soffit.tag:
            taken += run.diameter_m or 0.0
    return taken
