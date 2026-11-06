"""A-605: the stair and guard schedule (S1-103, S3-107), every number off the resolved model.

Risers, goings, nosings, widths and landings are the stair's own members; headroom is the
measure ``code.R311_7_2_stair_headroom`` makes; rail heights are the resolver's own
``rail_rises``; the largest opening is ``code.R312_1_3``'s drawn-geometry measure.
"""

from __future__ import annotations

import math
from collections import defaultdict
from types import SimpleNamespace

from typehaus.emit.draw.schedules.paged_tables import (
    PagedTable,
    continuation_number,
    draw_page,
    wrap_cells,
)
from typehaus.emit.draw.sheet_writer import schedule_sheet
from typehaus.emit.draw.typography import feet_inches_8th
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.railing_hardware import inch_text


def _ft(length_m: float) -> str:
    return feet_inches_8th(length_m / M_PER_IN, 16)


def _in(length_m: float) -> str:
    return inch_text(round(length_m / M_PER_IN * 16) / 16)


def _flights(stair) -> list[int]:
    """Tread count per straight flight, in key order (``tread-lower-*``, ``tread-upper-*``)."""
    counts: dict[str, int] = defaultdict(int)
    for member in stair.members:
        if member.category == "tread":
            counts[member.child_key.rsplit("-", 1)[0]] += 1
    return [counts[key] for key in sorted(counts)]


def _landings(stair) -> list:
    return sorted((m for m in stair.members if m.category == "landing"),
                  key=lambda m: (m.z1_m, m.child_key))


def _headroom(model: ResolvedModel, stair, overhead) -> tuple[float, str] | None:
    """The worst plumb clearance over the walking line and what sets it: the samples, index
    and run clearances ``code.R311_7_2_stair_headroom`` grades."""
    from typehaus.checks.code.mn_residential.stairs import _walk_samples
    from typehaus.resolve.stair_headroom import run_clearances
    from typehaus.resolve.stairs.walkline import headroom_stations

    worst: tuple[float, str] | None = None
    for stations in headroom_stations(stair).values():
        for x, y, z in _walk_samples(stations):
            lowest = overhead.lowest_above(x, y, z)
            if lowest is not None and (worst is None or lowest.z_m - z < worst[0]):
                worst = (lowest.z_m - z, lowest.tag)
    for tag, (clearance, _xy) in run_clearances(model, stair).items():
        if worst is None or clearance < worst[0]:
            worst = (clearance, tag)
    return worst


def stair_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    from typehaus.resolve.overhead import OverheadIndex

    overhead = OverheadIndex(model)
    railings = list(model.plan.elements_of_kind("Railing"))
    rows = []
    for stair in model.stairs:
        base = (stair.base_elevation_m if stair.base_elevation_m is not None
                else model.plan.storey(stair.storey).elevation.meters)
        top = (stair.arrival_elevation_m if stair.arrival_elevation_m is not None
               else model.plan.storey(stair.to_storey).elevation.meters)
        flights = _flights(stair)
        treads = " + ".join(str(n) for n in flights) + f" @ {_in(stair.going_depth_m)}"
        if stair.winder_count:
            treads += f" + {stair.winder_count} winders"
        width = max((m.length_m for m in stair.members if m.category == "tread"), default=0)
        levels = len({round(m.z1_m, 4) for m in _landings(stair)})
        headroom = _headroom(model, stair, overhead)
        rails = [r.tag for r in railings if r.serves_stair == stair.tag
                 and r.role in ("handrail", "guard_and_handrail")]
        rows.append((
            stair.tag,
            f"{stair.storey} > {stair.to_storey}" if stair.storey != stair.to_storey
            else f"{stair.storey} step",
            stair.layout.replace("_", " "),
            f"{stair.riser_count} @ {_in(stair.riser_height_m)}",
            f"{_ft(top - base)} ({_ft(base)} to {_ft(top)})",
            treads,
            f"{_in(stair.tread_depth_m)} / {_in(stair.nosing_depth_m)}",
            " + ".join(_ft(n * stair.going_depth_m) for n in flights)
            + (" + winders" if stair.winder_count else ""),
            _ft(width),
            str(levels) if levels else "—",
            f"{_ft(headroom[0])} under {headroom[1]}" if headroom else "open above",
            ", ".join(rails) or "—",
        ))
    return tuple(rows)


def landing_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    return tuple(
        (stair.tag, member.child_key, _ft(member.z1_m), _ft(member.length_m),
         _ft(cross_section(member.profile).width_m))
        for stair in model.stairs for member in _landings(stair))


def _rail_faces(model: ResolvedModel, railing) -> tuple[float, float | None, float]:
    """(top of top rail, underside of bottom rail or None, authored height) above the datum,
    from the inputs ``resolve_railing`` hands ``rail_rises``."""
    from typehaus.resolve.railings.frame import rail_rises
    from typehaus.resolve.railings.parts import railing_type, resolve_parts

    stair = railing.serves_stair is not None
    rail_h = (railing.top_height if stair and railing.top_height is not None
              else railing.height).meters
    product = railing_type(model.plan.library, railing)
    fascia = product.fascia_mount if product is not None and railing.mount == "fascia" else None
    surface = product.surface_mount if product is not None and railing.surface_post_mounts \
        else None
    detailed = fascia or surface
    bottom = detailed.bottom_clearance.meters if detailed else 0.0
    if surface is not None and stair:
        bottom = surface.stair_bottom_clearance.meters
    parts = resolve_parts(model, railing)
    rises = rail_rises(railing, parts, rail_h, bottom, detailed is not None)
    half = parts.rail_section_m / 2
    return rises[0] + half, (rises[-1] - half if len(rises) > 1 else None), rail_h


def _largest_opening(model: ResolvedModel, railing, guards) -> float | None:
    from typehaus.checks.code.mn_residential.fall_protection import _largest_drawn_opening_m

    guard = guards.get(railing.tag)
    if guard is None or railing.infill is None or railing.role == "handrail":
        return None
    return _largest_drawn_opening_m(SimpleNamespace(model=model, plan=model.plan), guard)


def guard_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    from typehaus.checks.guard_lines import guard_lines
    from typehaus.resolve.railings import guard_post_stations

    guards = {g.tag: g for g in guard_lines(model.plan)}
    posts: dict[str, int] = defaultdict(int)
    for solid in model.solids:
        if solid.category == "railing" and solid.host_ref and "-POST" in solid.tag:
            posts[solid.host_ref] += 1
    rows = []
    for railing in sorted(model.plan.elements_of_kind("Railing"), key=lambda r: r.tag):
        top, bottom, height = _rail_faces(model, railing)
        stations = guard_post_stations(model.plan.library, railing)
        pitch = max((math.dist(a, b) for a, b in zip(stations, stations[1:], strict=False)),
                    default=None)
        opening = _largest_opening(model, railing, guards)
        ends = {str(getattr(t, "value", t)).replace("_", " ") if t else "—"
                for t in (railing.start_termination, railing.end_termination)}
        rows.append((
            railing.tag,
            railing.role.replace("_and_", " + "),
            railing.serves_stair or "—",
            (railing.type_ref or "—").removeprefix("RAILING-"),
            railing.mount,
            "nosings" if railing.serves_stair else "deck plane" if railing.fascia_ref
            else _ft(railing.base_elevation.meters),
            _in(height),
            f"{_in(top)} / {_in(bottom) if bottom is not None else '—'}",
            str(posts.get(railing.tag, 0)) if posts.get(railing.tag) else "—",
            _ft(pitch) if pitch else "—",
            "panel" if railing.infill == "panel"
            else _in(opening) if opening else "—",
            " / ".join(sorted(ends)),
        ))
    return tuple(rows)


_NOTES = (
    ("Total rise is finished floor to finished floor; risers are equal over it (R311.7.5.1).",),
    ("Going is nosing to nosing; tread is the board depth; run is goings per flight.",),
    ("Width is the tread board; R311.7.1 clear widths past rails are graded in the check.",),
    ("Headroom: lowest plumb clearance over the nosing line and landings (R311.7.2).",),
    ("Guard height above the walking surface (R312.1.2); handrail above nosings (R311.7.8.1).",),
    ("Rail top / bottom: top of top rail / underside of bottom rail as drawn, same datum.",),
    ("Max c/c: supports along the plan path. Max opening: widest drawn gap (R312.1.3, 4\").",),
    ("Mounting hardware: S-602 guard and handrail table. Typical bays: A-606.",),
)


def stair_schedule_tables(model: ResolvedModel) -> list[PagedTable]:
    return [
        PagedTable("STAIRS",
                   ("Stair", "Levels", "Layout", "Risers", "Total rise", "Treads",
                    "Tread / nosing", "Run", "Width", "Landings", "Min headroom",
                    "Handrails"),
                   wrap_cells(stair_rows(model), {11: 36})),
        PagedTable("LANDINGS", ("Stair", "Landing", "Deck top EL", "Depth (travel)", "Width"),
                   landing_rows(model)),
        PagedTable("GUARDS AND HANDRAILS",
                   ("Railing", "Role", "Serves", "Type", "Mount", "Datum", "Height",
                    "Rail top / bottom", "Posts", "Max c/c", "Max opening", "Ends"),
                   guard_rows(model)),
        PagedTable("NOTES", ("Note",), _NOTES),
    ]


def has_stair_schedule(model: ResolvedModel) -> bool:
    return bool(model.stairs)


def write_stair_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                         page: int = 0) -> None:
    """A-605 (and its continuations)."""
    base = number if page == 0 else number.rsplit(".", 1)[0]
    with schedule_sheet(pdf, model, number, name) as fig:
        draw_page(fig, stair_schedule_tables(model), tuple(fig.get_size_inches()), page,
                  continuation_number(base, page + 1))
