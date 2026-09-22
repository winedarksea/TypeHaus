"""``haus route --fixture X --sweep N``: would this route if the drain point moved?

The router's answer to a fixture it cannot serve is a refusal naming what is in the way. The
next question belongs to the other side of the two-way street: **the fixture's own position
is a design variable too**, and a WC that will not route at its drawn station may route four
inches along the same wall. Nobody should have to discover that by editing the plan six
times.

So this walks the derived drain point along the fixture's ``wall_ref`` in fixed steps,
searches at each, and prints what each station buys: feasible or not, the route's price, its
bends, and — for a gravity run — the head it had left. The best station comes back as a
``Fixture(...)`` constructor to paste, with ``drain_position`` set and everything else
unchanged.

**Three things it deliberately does not do.**

* **It does not move anything.** Like every other proposal in this package it prints source
  and writes nothing. Moving a fixture is a design decision with a room, a tile layout and a
  person attached to it.
* **It sweeps the DRAIN POINT, not the fixture.** ``Fixture.drain_position`` is the
  contractor override the model already has for exactly this — where the waste actually
  drops, which on a wall-hung WC or a vanity is not the fixture's centre and never was.
  Moving ``position`` instead would move the china, which is a much larger claim.
* **It does not grade the new position.** Whether the moved drain still clears its trap arm,
  its clearance zone and the stud it now sits over is the checks' question, asked properly
  by ``haus trial`` once the move is on a branch. A station this prints as feasible is
  feasible *to route*, which is one of the several things it has to be.

Stations are clamped to the wall's own extent and skipped where the point would land inside
a stud, because a drain does not drop through framing — the same ``resolve/mep_bores``
reading ``mep.run_through_stud`` grades against.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost

#: How far apart the stations are. Two inches is the resolution a plumber actually sets a
#: closet flange to, and a finer sweep prices a precision the trade does not work at.
STEP_IN = 2.0

#: Stations either way of the drawn one, before ``--sweep`` narrows it. Twenty-four inches
#: covers a fixture sliding within its own alcove; past that it is a different design.
MAX_REACH_IN = 24.0


@dataclass(frozen=True)
class Station:
    """One candidate drain point and what routing to it would cost."""

    offset_in: float
    x_m: float
    y_m: float
    feasible: bool
    cost_in: float | None = None
    bends: int | None = None
    #: Head left at the tightest constraint, inches. None where the run does not fall.
    slack_in: float | None = None
    note: str = ""

    def row(self) -> str:
        where = f"{self.offset_in:+6.1f}\""
        if not self.feasible:
            return f"  {where}  infeasible  {self.note}"
        slack = "" if self.slack_in is None else f"  slack {self.slack_in:+.2f}\""
        return (f"  {where}  ok          {self.cost_in:8.0f}\" equivalent  "
                f"{self.bends} bend(s){slack}")

    def payload(self) -> dict:
        return {"offset_in": self.offset_in, "x_m": self.x_m, "y_m": self.y_m,
                "feasible": self.feasible, "cost_in": self.cost_in,
                "bends": self.bends, "slack_in": self.slack_in, "note": self.note}


def wall_axis(model: ResolvedModel, wall_ref: str | None
              ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None:
    """``(unit vector, lo point, hi point)`` for the fixture's wall, or None.

    A raked wall is refused rather than swept along its chord: the drain point would leave
    the wall plane, and a station that is not in the wall is not a station.
    """
    wall = next((w for w in model.walls if w.tag == wall_ref), None)
    if wall is None or len(wall.axis) < 2:
        return None
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    dx, dy = bx - ax, by - ay
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 1e-9 or min(abs(dx), abs(dy)) > 1e-6:
        return None
    return (dx / length, dy / length), (ax, ay), (bx, by)


def stations(model: ResolvedModel, fixture_tag: str, origin: tuple[float, float, float],
             reach_in: float) -> list[tuple[float, tuple[float, float]]]:
    """``(offset, point)`` for every legal station within ``reach_in`` of the drawn one.

    Clamped to the wall's extent and skipped where the point stands in a stud. A sweep that
    offered a station inside framing would be offering one the very next check refuses.
    """
    element = next((e for e in model.plan.all_elements()
                    if getattr(e, "tag", None) == fixture_tag), None)
    axis = wall_axis(model, getattr(element, "wall_ref", None)) if element else None
    if axis is None:
        return []
    (ux, uy), lo, hi = axis
    # **Clamped ALONG the wall, never across it.** The derived drain point stands off the
    # wall face by the fixture's own offset — a WC's flange is a foot and a half into the
    # room — so testing the point against the wall's plan box refuses every station,
    # including the drawn one. What has to stay on the wall is the station, which is the
    # projection onto the wall's own direction.
    along = ux if abs(ux) > abs(uy) else uy
    lo_s = min(lo[0], hi[0]) if abs(ux) > abs(uy) else min(lo[1], hi[1])
    hi_s = max(lo[0], hi[0]) if abs(ux) > abs(uy) else max(lo[1], hi[1])
    base = origin[0] if abs(ux) > abs(uy) else origin[1]

    out: list[tuple[float, tuple[float, float]]] = []
    steps = int(min(reach_in, MAX_REACH_IN) // STEP_IN)
    for index in range(-steps, steps + 1):
        offset_m = index * STEP_IN * M_PER_IN
        point = (origin[0] + ux * offset_m, origin[1] + uy * offset_m)
        station = base + along * offset_m
        if not (lo_s - 1e-6 <= station <= hi_s + 1e-6):
            continue  # past the end of its own wall
        if _in_a_stud(model, getattr(element, "wall_ref", None), point):
            continue
        out.append((index * STEP_IN, point))
    return out


def _in_a_stud(model: ResolvedModel, wall_ref: str | None,
               point: tuple[float, float]) -> bool:
    """Whether a drain dropped here would land in framing rather than a bay.

    Read off the wall's own resolved members through ``resolve/mep_bore_geometry``'s
    plan shapes — the same geometry ``mep.run_through_stud`` grades a bore against, so a
    station this offers cannot be one that check then refuses.
    """
    from shapely.geometry import Point

    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.mep_bore_geometry import member_plan_shape

    wall = next((w for w in model.walls if w.tag == wall_ref), None)
    if wall is None:
        return False
    probe = Point(point)
    for member in getattr(wall, "members", ()) or ():
        if member.category not in ("stud", "king", "jack", "post"):
            continue
        shape = member_plan_shape(member, cross_section(member.profile))
        if shape is not None and shape.covers(probe):
            return True
    return False


def sweep(model: ResolvedModel, fixture_tag: str, ends: Any, *, reach_in: float,
          margin_ft: float, band: tuple[float, float] | None, avoid: frozenset[str],
          cost: RouteCost, slope: float | None, search_for) -> list[Station]:
    """Search from every legal station and report what each one buys.

    ``search_for`` is ``cmd_route._search_for`` passed in rather than imported, so this
    module does not reach back into the one that drives it and the drain's gravity search
    is the one actually used for a drain.
    """
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space

    out: list[Station] = []
    for offset_in, point in stations(model, fixture_tag, ends.origin, reach_in):
        moved = replace(ends, origin=(point[0], point[1], ends.origin[2]))
        terminals = [moved.origin, moved.root]
        try:
            space = build_space(model, radius_m=moved.radius_m, terminals=terminals,
                                margin_ft=margin_ft, avoid=avoid, touch=moved.touch,
                                cost=cost, z_band=band)
            levels = [moved.root[2]] if moved.falls else None
            graph = build_graph(space, terminals, levels)
        except RoutingSpaceTooLarge as exc:
            out.append(Station(offset_in, point[0], point[1], False,
                               note=f"space too large: {exc}"))
            continue
        from typehaus.cli.route_support import _nearest, _root_nodes

        start = _nearest(graph, moved.origin)
        goals = _root_nodes(graph, moved.root, with_z=not moved.falls)
        if start is None or not goals:
            out.append(Station(offset_in, point[0], point[1], False,
                               note="no lattice node at the origin or the root"))
            continue
        run, report = search_for(model, graph, moved, slope)
        found = run(graph, space, start, goals)
        if found is None:
            tight = getattr(report, "tightest", None) if report is not None else None
            out.append(Station(offset_in, point[0], point[1], False,
                               note=report.sentence() if tight is not None
                               else "no route from this station"))
            continue
        out.append(Station(offset_in, point[0], point[1], True, found.cost, found.bends,
                           _slack_in(report)))
    return out


def _slack_in(report: Any) -> float | None:
    """Head left at the tightest constraint, in inches, where the run falls."""
    tight = getattr(report, "tightest", None) if report is not None else None
    if tight is None:
        return None
    slack = getattr(tight, "slack_m", None)
    return None if slack is None else slack / M_PER_IN


def render(fixture_tag: str, found: list[Station], model: ResolvedModel) -> list[str]:
    """The sweep table, and the best station as a ``Fixture(...)`` to paste."""
    if not found:
        return [f"{fixture_tag}: no legal station to sweep — the fixture names no "
                "rectilinear wall_ref, or every station is off the wall or in a stud"]
    lines = [f"[bold]sweep {fixture_tag}[/bold] — {len(found)} station(s), "
             f"{STEP_IN:.0f}\" apart along its wall:"]
    lines.extend(station.row() for station in found)

    feasible = [s for s in found if s.feasible and s.cost_in is not None]
    if not feasible:
        lines.append(f"{fixture_tag}: NO station on this wall routes. Moving the drain "
                     "point alone does not solve it, which is itself the answer — the "
                     "obstruction is not where the fixture stands.")
        return lines
    best = min(feasible, key=lambda s: (s.cost_in, abs(s.offset_in)))
    drawn = next((s for s in found if abs(s.offset_in) < 1e-9), None)
    if best is drawn or abs(best.offset_in) < 1e-9:
        lines.append(f"{fixture_tag}: the drawn station is already the cheapest that "
                     "routes. Nothing to move.")
        return lines
    saved = ("" if drawn is None or not drawn.feasible or drawn.cost_in is None
             else f" — {drawn.cost_in - best.cost_in:.0f}\" cheaper than the drawn station")
    lines.append("")
    lines.append("# --- PROPOSED, NOT WRITTEN -----------------------------------------")
    lines.append(f"# {fixture_tag} routes best {best.offset_in:+.0f}\" along its "
                 f"wall{saved}.")
    lines.append("# This moves the DRAIN POINT, not the fixture.")
    lines.append("# It is NOT a graded position: paste it on a branch and run "
                 "`haus trial` to")
    lines.append("# find out what the clearance and trap-arm checks make of it.")
    lines.extend(_constructor(model, fixture_tag, best))
    return lines


def _constructor(model: ResolvedModel, fixture_tag: str, best: Station) -> list[str]:
    """The ``Fixture(...)`` line to paste — ``drain_position`` set, nothing else touched."""
    element = next((e for e in model.plan.all_elements()
                    if getattr(e, "tag", None) == fixture_tag), None)
    if element is None:
        return [f"# (no authored Fixture {fixture_tag} to print)"]
    keys = [f'tag="{fixture_tag}"', f'type_ref="{getattr(element, "type_ref", "")}"']
    room = getattr(element, "room", None)
    if room:
        keys.append(f'room="{room}"')
    position = getattr(element, "position", None)
    if position is not None:
        # ``to_source`` rather than a re-derivation: the authored position is not being
        # changed by this proposal, and re-rounding it onto the 1/16" grid would quietly
        # move the china to make a drain move printable.
        keys.append(f"position={position.to_source()}")
    wall_ref = getattr(element, "wall_ref", None)
    if wall_ref:
        keys.append(f'wall_ref="{wall_ref}"')
    keys.append(f"drain_position={_pt(best.x_m, best.y_m)}")
    return ["Fixture(" + ",\n        ".join(keys) + "),"]


def _pt(x_m: float, y_m: float) -> str:
    """A plan point as the dialect spells one: ``pt(ft(f, i), ft(f, i))``, 1/16" grid."""
    return f"pt({_ft(x_m)}, {_ft(y_m)})"


def _ft(value_m: float) -> str:
    total_in = round(value_m / M_PER_IN * 16.0) / 16.0
    feet, inches = divmod(total_in, 12.0)
    if abs(inches) < 1e-9:
        return f"ft({feet:.0f})"
    return f"ft({feet:.0f}, {inches:g})"
