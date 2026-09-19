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
    #: Sentences a consumer must print rather than swallow — what the clear width was
    #: derived from and what that derivation cannot see.
    gaps: tuple[str, ...] = ()
    #: The elevation of the GOVERNING TIER, where the channel already has an occupant —
    #: ``mep_packing.Packing.z_m``. ``None`` for an empty channel, and the distinction is
    #: what ``graph.candidate_levels`` branches on: an empty channel's midpoint is the only
    #: plane worth nominating, and an occupied one's is the plane already taken.
    occupied_z: float | None = None
    #: Tags already in this channel's governing tier, so a proposal can say what it rode
    #: beside rather than only that it fitted.
    occupants: tuple[str, ...] = ()

    def admits(self, radius_m: float) -> bool:
        return 2.0 * radius_m <= self.clear_width_m + 1e-9

    def z_window(self, radius_m: float) -> tuple[float, float] | None:
        """The centreline band a run of this radius may occupy, or None if it cannot fit."""
        low, high = self.z0_m + radius_m, self.z1_m - radius_m
        return (low, high) if high >= low else None


def floor_corridors(model: ResolvedModel) -> list[Corridor]:
    """One corridor per joist/truss bay, on every resolved floor.

    The bay's own STRUCTURAL clear width comes from ``clear_bay_width_m``, which takes the
    MEDIAN line-to-line step and the WIDEST member — an end strip and a doubled line at an
    opening are both narrower than the field and neither is the bay a run rides in. Two
    consumers now read that one derivation instead of two.

    **What is already in the bay is then subtracted**, through the same
    ``resolve/mep_packing.pack`` tier sweep ``soffit_corridors`` and ``chase_corridors``
    read. A floor bay's width was the purely structural figure, so ``admits`` answered "does
    this fit the bay" rather than "is the bay free" — and a campaign would lay a fourteenth
    ERV radial into the one truss bay that already holds thirteen at one elevation, which is
    the class of defect ``mep.run_interference`` reports at 4.00" on catlin's ``FS-S-WEST``.
    """
    from typehaus.resolve.mep_envelopes import run_polylines
    from typehaus.resolve.mep_packing import run_occupants
    from typehaus.resolve.mep_queries import clear_bay_width_m, joist_line_stations

    # Derived ONCE for the whole house, not once per bay: a floor has a hundred-odd bays and
    # this reading now walks every VentRun's roof geometry as well.
    lines_by_tag = {tag: path for _kind, tag, path, _z in run_polylines(model)}
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
        # Once per FLOOR, not once per bay: ``run_occupants`` re-derives every run's
        # section, and a floor has a hundred-odd bays.
        occupants = run_occupants(model, channel_ref=floor.tag, attr="floor_ref")
        along = "x" if floor.direction == "x" else "y"
        span = _member_span(floor, along)
        if span is None:
            continue
        for index in range(len(lines) - 1):
            gap = lines[index + 1] - lines[index]
            if gap <= clear:
                continue  # a doubled pair or an end strip, not a field bay
            centre = (lines[index] + lines[index + 1]) / 2.0
            taken, gaps, packing = _bay_taken(floor, occupants, lines_by_tag, along,
                                              centre, clear)
            out.append(Corridor(
                tag=f"{floor.tag}:bay@{centre:.4f}", kind="bay", axis=along,
                station=centre, z0_m=low, z1_m=high,
                clear_width_m=max(clear - taken, 0.0),
                lo_m=span[0], hi_m=span[1], gaps=gaps,
                occupied_z=packing.z_m if packing is not None and packing.tier else None,
                occupants=packing.tier if packing is not None else ()))
    return out


def _bay_taken(floor: ResolvedFloor, occupants: list[Any],
               lines_by_tag: dict[str, Any], along: str, station: float,
               clear_m: float) -> tuple[float, tuple[str, ...]]:
    """How much of THIS bay is already occupied, and what that reading cannot see.

    ``floor_ref`` names the floor, not the bay, and a floor holds many: summing every
    occupant of ``FS-S-WEST`` into each of its bays would price a clear bay out of existence
    because a different bay is full. So the occupants are narrowed to the runs whose plan
    polyline actually comes within half a bay of this station on the cross axis, and only
    those are packed.

    Two limits are **disclosed rather than papered over**, both inherited from
    ``mep_packing.run_occupants``:

    * a run presents ONE band, its mean z plus or minus half its depth — not one band per
      segment — so a run that drops through the bay is banded where its average is;
    * a ``ConduitRun`` is not an occupant at all, because it names no ``floor_ref``.
    """
    from typehaus.resolve.mep_packing import pack

    if not occupants:
        return 0.0, (), None
    cross = 1 if along == "x" else 0
    present = [o for o in occupants
               if any(abs(point[cross] - station) <= clear_m / 2.0
                      for point in lines_by_tag.get(o.tag, ()))]
    if not present:
        return 0.0, (), None
    packing = pack(clear_m, present)
    return packing.taken_m, (
        f"{floor.tag} bay @{station:.4f}: {len(present)} run(s) already in it take "
        f"{packing.taken_m / 0.0254:.2f}\" at the tightest tier. Each is banded at its MEAN "
        "elevation +/- half its depth, one band per run rather than one per segment, so a "
        "run that drops through the bay is priced where its average is; and a ConduitRun "
        "names no floor_ref and is not an occupant here at all.",), packing


def crossing_window(model: ResolvedModel,
                    floor: ResolvedFloor) -> tuple[float, float] | None:
    """The z band a run may occupy while crossing this floor's members, or None.

    A three-line delegation to :func:`~typehaus.resolve.mep_crossings.member_window`, which
    is now the one place the truss / I-joist / solid-sawn readings live. What stood here
    was two of the three plus a hardcoded 1 1/2" chord fallback, reached because
    ``open_web_opening_m`` takes a ``CrossSection`` and was handed a ``profile`` *string*:
    the call raised, the caller swallowed it, and the fallback happened to give the same
    8 7/8" on catlin's truss. Its own docstring recorded that it "answered right for the
    wrong reason on the one floor it was checked against".

    Importing ``resolve.mep_queries``' neighbour is the same direction this module already
    takes ``clear_bay_width_m`` in, and for the same reason: the leaf rule is about
    *direction* — routing may read resolve, nothing reads routing — not self-sufficiency.
    The ``(model, floor)`` signature stays so the routing oracle compiles unchanged.
    """
    from typehaus.resolve.mep_crossings import member_window

    window = member_window(floor)
    return None if window is None else (window.z0_m, window.z1_m)


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

    What stood here was a **sum** of every occupant's outside dimension, with a comment
    admitting it: the model gives each run one centreline per box, so it "cannot say two
    things sit side by side". That is true and it is not a reason to sum. Summing makes a
    2'-8" box full once the air handler's case and three branches are in it, even where the
    branches run over the top of the case and never share an elevation with it, and a full
    box is a corridor the router prices out of existence.

    ``resolve/mep_packing`` answers it properly and both readers now share the answer: the
    width taken is the widest TIER — the largest total over any one elevation — so runs that
    stack cost the box nothing. See that module for what the reading still declines to
    claim.
    """
    from typehaus.resolve.mep_packing import pack, run_occupants

    return pack(0.0, run_occupants(model, channel_ref=soffit.tag)).taken_m


def chase_corridors(model: ResolvedModel) -> list[Corridor]:
    """One corridor per ``FloorOpening(purpose=CHASE)`` — a lane, not merely a hole.

    A chase already reached the router, as a *void*: ``obstacles`` declines to block it, so
    a run may pass through. That is only half of what a chase is. A chase is where a trade
    PUTS a riser, and a lane nothing discounts is a lane the search takes only when it is
    also the shortest — which is how a route ends up boring a plate eighteen inches from an
    open shaft built for it.

    The corridor runs on the opening's LONG plan axis, the same reading a soffit takes, and
    its clear width is what the chase has left once the risers already in it are packed
    (``mep_packing``). ``z0_m``/``z1_m`` span the floor it pierces, because that is the
    extent over which the hole is a hole; a riser continuing above or below is travelling in
    a wall or a bay and is priced there.
    """
    out: list[Corridor] = []
    for floor in model.floors:
        for tag, ring in getattr(floor, "chases", ()) or ():
            bounds = _bounds(ring)
            if bounds is None:
                continue
            minx, miny, maxx, maxy = bounds
            wide = (maxx - minx) >= (maxy - miny)
            axis = "x" if wide else "y"
            across = (maxy - miny) if wide else (maxx - minx)
            lo, hi = (minx, maxx) if wide else (miny, maxy)
            out.append(Corridor(
                tag=tag, kind="chase", axis=axis,
                station=(miny + maxy) / 2.0 if wide else (minx + maxx) / 2.0,
                z0_m=_floor_low(floor), z1_m=floor.deck_z0_m,
                clear_width_m=max(across - _chase_taken(model, tag), 0.0),
                lo_m=lo, hi_m=hi))
    return out


def _chase_taken(model: ResolvedModel, tag: str) -> float:
    """The widest tier of runs naming this chase, through either ref a run may use."""
    from typehaus.resolve.mep_packing import Occupant, pack, run_occupants

    seen: dict[str, Occupant] = {}
    for attr in ("chase_ref", "soffit_ref", "floor_ref"):
        for occupant in run_occupants(model, channel_ref=tag, attr=attr):
            seen[occupant.tag] = occupant
    return pack(0.0, list(seen.values())).taken_m


def _floor_low(floor: ResolvedFloor) -> float:
    placed = [m.z0_m for m in floor.members if m.z0_m is not None]
    return min(placed) if placed else floor.deck_z0_m
