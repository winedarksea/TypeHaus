"""Minn. R. 1309.0404 — the floor's connection to the top of a backfilled foundation wall.

Table R404.1(1) gives the reaction the floor must take off the wall's top. Subpart 1 wants
joists and blocking "connected to the sill plate ... with an approved connector with listed
capacity meeting the top of wall reaction"; footnote f puts the blocking in the first three
joist spaces of a PARALLEL floor, at the table's spacing, each station within 8" of an
anchor bolt. Two load paths, graded separately per wall:

* **perpendicular** — every seated end (``joints/bearing``) on the wall's sill carries
  reaction x joist spacing through its ``JoistSpec.sill_tie``s;
* **parallel** — every block station (``joints/wall_top``) carries reaction x its
  tributary length through the ``Connector``s authored at it.

Capacity is the tie's catalog lateral (the lesser of F1/F2, since a sill tie's orientation
is the installer's) times C_D 0.9 over the lowest duration its row holds at, times a
species factor for the joist side (see ``_species_factor``). Oracle: catlin
``notes/main_floor_truss_basis.md`` §4.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.soil import site_soil_class
from typehaus.checks.structural._mn_r404_1_table import SOIL_GROUP_PCF, top_of_wall_row
from typehaus.checks.structural.foundation import _unbalanced_fill_ft, _wall_height_ft
from typehaus.findings import Finding

_CID = "code.MN_1309_0404_wall_top"
_CODE = "Minn. R. 1309.0404"
_M_PER_IN = 0.0254
_M_PER_FT = 0.3048

#: NDS Table 2.3.2: lateral soil pressure is a permanent load.
_CD_SOIL = 0.9
#: Simpson C-C-2026 p. 310, SPF/HF over DF/SP: the A34 SD-screw rows (550/640, 425/495)
#: and the A35 joist-to-plate rows (510/590) all read 0.86. ESR-3096 §3.2.2 covers only
#: SG >= 0.50, so sawn joists and truss chords of unstated species take it.
_SPF_FACTOR = 0.86
#: C-C-2026 p. 310 fn. 6: A34/A35 "onto 1 1/4" LSL material will achieve 0.90 of the listed
#: F1 and F2 loads". No angle is listed on an I-joist flange; at a TJI the angle lands on
#: the LSL rim or blocking at the joist end, Weyerhaeuser's own end detail.
_LSL_FACTOR = 0.90
#: How far from a station point an authored connector still serves it.
_STATION_REACH_M = 18.0 * _M_PER_IN
#: Footnote f.
_ANCHOR_REACH_M = 8.0 * _M_PER_IN


def _species_factor(profile: str) -> float:
    from typehaus.resolve.framing.profiles import cross_section

    try:
        shape = cross_section(profile).shape
    except Exception:  # an unparsed profile reads as sawn
        return _SPF_FACTOR
    return _LSL_FACTOR if shape == "i_joist" else _SPF_FACTOR


def tie_capacity_lb(model: str, profile: str) -> tuple[float | None, str]:
    """One tie's sustained lateral allowable onto ``profile``, and why it is None."""
    from typehaus.hardware.catalog import hardware_by_model

    item = hardware_by_model(model)
    loads = getattr(item, "allowable", None)
    if item is None or loads is None:
        return None, f"{model} is not in the hardware catalog with published allowables"
    lateral = [v for v in (loads.lateral_f1_lb, loads.lateral_f2_lb) if v is not None]
    duration = loads.lowest_load_duration_factor or loads.load_duration_factor
    if not lateral or not duration:
        return None, f"{model}'s catalog record publishes no lateral value at a stated C_D"
    return min(lateral) * min(1.0, _CD_SOIL / duration) * _species_factor(profile), ""


def _floor_spacing_m(ctx: CheckContext) -> dict:
    out = {}
    for element in ctx.plan.all_elements():
        spacing = getattr(getattr(element, "joists", None), "spacing", None)
        if spacing is not None:
            out[element.tag] = spacing.meters
    return out


def _perpendicular(connections, reaction_plf, spacing_by_floor) -> tuple[list, list]:
    """``(ok lines, short lines)`` for the seated ends on one wall, per floor."""
    by_floor: dict = {}
    for c in connections:
        by_floor.setdefault((c.assembly_tag, c.member_profile, c.sill_tie, c.sill_ties),
                            []).append(c)
    ok, short = [], []
    for (floor, profile, tie, count), ends in sorted(by_floor.items(), key=str):
        spacing_ft = spacing_by_floor.get(floor, 0.0) / _M_PER_FT
        demand = reaction_plf * spacing_ft
        head = (f"{floor} ({len(ends)} {profile} ends at {spacing_ft * 12:.0f}\" o.c., "
                f"{demand:.0f} lb each)")
        if not tie:
            short.append(f"{head}: no JoistSpec.sill_tie, so toe-nails only")
            continue
        each, why = tie_capacity_lb(tie, profile)
        if each is None:
            return ok, short + [f"{head}: UNKNOWN — {why}"]
        line = (f"{head}: {count} {tie} x {each:.0f} lb = {count * each:.0f} lb, "
                f"d/c {demand / (count * each):.2f}")
        (ok if count * each >= demand - 1e-6 else short).append(line)
    return ok, short


def _tributaries(span, alongs) -> list:
    out = []
    for i, a in enumerate(alongs):
        lo = span[0] if i == 0 else (alongs[i - 1] + a) / 2.0
        hi = span[1] if i == len(alongs) - 1 else (a + alongs[i + 1]) / 2.0
        out.append(hi - lo)
    return out


def _parallel(ctx, run, reaction_plf, blocking_in, connectors, anchors) -> tuple[list, list]:
    """``(ok lines, short lines)`` for one parallel floor over the wall."""
    head = f"{run.floor_tag} parallel"
    if run.voids:
        cut = ", ".join(f"{a / _M_PER_FT:.1f}-{b / _M_PER_FT:.1f} ft" for a, b in run.voids)
        return [], [f"{head}: UNKNOWN — a floor opening fills the first three joist spaces "
                    f"along {cut}, so no footnote f blocking can stand there; the restraint "
                    "is an approved-equivalent design (the opening's edge framing)"]
    if not run.stations:
        return [], [f"{head}: no blocking stations (footnote f, {blocking_in}\" o.c.)"]
    limit_m = blocking_in * _M_PER_IN
    alongs = [s.along_m for s in run.stations]
    gaps = [b - a for a, b in zip(alongs, alongs[1:], strict=False)]
    ends = (alongs[0] - run.span_m[0], run.span_m[1] - alongs[-1])
    short: list = []
    # A wall end is a corner or the next segment's own run: footnote f's spacing is read
    # from it as from a station, while the end's tributary still lands on the last station.
    if max(gaps, default=0.0) > limit_m + 1e-3 or max(ends) > limit_m + 1e-3:
        short.append(f"{head}: stations {', '.join(f'{a / _M_PER_FT:.1f}' for a in alongs)} ft "
                     f"leave more than {blocking_in}\" between stations or to a wall end")
    profile = next((m.profile for f in ctx.model.floors if f.tag == run.floor_tag
                    for m in f.members if m.category == "joist"), "")
    worst = 0.0
    for station, trib in zip(run.stations, _tributaries(run.span_m, alongs), strict=True):
        where = f"{head} station at {station.along_m / _M_PER_FT:.1f} ft"
        if not {1, 2, 3} <= station.bays:
            short.append(f"{where}: blocks only joist space(s) {sorted(station.bays)}")
        demand = reaction_plf * trib / _M_PER_FT
        # The wall too: a collinear neighbour's ties are within reach of a station at its end.
        mine = [c for c in connectors if {run.floor_tag, run.wall_tag} <= set(c.connects)
                and math.dist(c.position.xy_m, station.point_m) <= _STATION_REACH_M]
        capacity = 0.0
        for c in mine:
            each, why = tie_capacity_lb(c.size, profile)
            if each is None:
                return [], short + [f"{where}: UNKNOWN — {why}"]
            capacity += each
        if capacity < demand - 1e-6:
            short.append(f"{where}: {demand:.0f} lb over {trib / _M_PER_IN:.0f}\" against "
                         f"{len(mine)} authored connector(s), {capacity:.0f} lb")
        else:
            worst = max(worst, demand / capacity)
        if not any(abs(along - station.along_m) <= _ANCHOR_REACH_M for along in anchors):
            short.append(f"{where}: no anchor bolt within 8\"")
    ok = [] if short else [f"{head}: {len(alongs)} stations, worst d/c {worst:.2f}"]
    return ok, short


@check(Tier.CODE, _CID)
def foundation_wall_top(ctx: CheckContext) -> list[Finding]:
    """Each backfilled foundation wall carrying a floor, against Table R404.1(1)."""
    from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as config
    from typehaus.joints.authored import authored_connectors
    from typehaus.joints.bearing import bearing_connections
    from typehaus.joints.sills import mudsill_anchor_stations
    from typehaus.joints.wall_top import along_wall, parallel_runs
    from typehaus.model.structure import FoundationWall

    walls = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, FoundationWall)}
    seats: dict = {}
    for c in bearing_connections(ctx.model, config.uplift):
        if c.support_tag in walls:
            seats.setdefault(c.support_tag, []).append(c)
    # Every perpendicular seat, tied or not: the bearing rule only reports tied ends.
    untied = _untied_seats(ctx, config, walls)
    for tag, ends in untied.items():
        seats.setdefault(tag, []).extend(ends)
    runs: dict = {}
    for run in parallel_runs(ctx.model):
        if run.wall_tag in walls:
            runs.setdefault(run.wall_tag, []).append(run)
    grade = ctx.plan.project.site.grade
    carrying = {t for t in (*seats, *runs)
                if grade is None or (_unbalanced_fill_ft(walls[t], grade.meters) or 0) > 0.05}
    if not carrying:
        return [_na(_CID, "no backfilled foundation wall carries a floor", (), _CODE)]
    soil = site_soil_class(ctx.plan, ctx.profile)
    pcf = SOIL_GROUP_PCF.get((soil or "").upper())
    if grade is None or pcf is None:
        return [_unknown(_CID, "no site grade or no soil class Table R404.1(1) lists, so no "
                               "top-of-wall reaction", tuple(sorted(carrying)), _CODE)]
    spacing = _floor_spacing_m(ctx)
    connectors = authored_connectors(ctx.model)
    anchors = mudsill_anchor_stations(ctx.model, config.sill_plate_anchors,
                                      config.sill_plate_takeoff_category)
    out: list[Finding] = []
    for tag in sorted(carrying):
        wall = walls[tag]
        height, fill = _wall_height_ft(wall) or 0.0, _unbalanced_fill_ft(wall, grade.meters)
        row = top_of_wall_row(height, fill, pcf)
        if row is None:
            out.append(_unknown(_CID, f"{tag}: {height:.1f}' wall, {fill:.1f}' fill is past "
                                      "Table R404.1(1); the restraint is a design", (tag,), _CODE))
            continue
        (row_h, row_b), (reaction, _bolt, blocking) = row
        ok, short = _perpendicular(seats.get(tag, ()), reaction, spacing)
        resolved = ctx.model.wall(tag)
        on_wall = [along_wall(resolved, a.point_m) for a in anchors]
        on_wall = [a for a, offset in on_wall if offset <= resolved.thickness_m]
        for run in runs.get(tag, ()):
            more_ok, more_short = _parallel(ctx, run, reaction, blocking, connectors, on_wall)
            ok, short = ok + more_ok, short + more_short
        head = (f"{tag} ({height:.1f}' wall, {fill:.1f}' fill, {soil}): Table R404.1(1) row "
                f"{row_h:g}'/{row_b:g}' gives {reaction} plf at the top")
        tags = (tag, *sorted({c.assembly_tag for c in seats.get(tag, ())}
                             | {r.floor_tag for r in runs.get(tag, ())}))
        unknown = [s for s in short if "UNKNOWN" in s]
        if unknown:
            out.append(_unknown(_CID, f"{head}; " + "; ".join(unknown), tags, _CODE))
        elif short:
            out.append(_fail(_CID, f"{head}; " + "; ".join(short), tags, _CODE))
        else:
            out.append(_pass(_CID, f"{head}; " + "; ".join(ok), _CODE))
    return out


def _untied_seats(ctx, config, walls) -> dict:
    """Seats on these walls of floors that name no ``sill_tie`` — the toe-nailed ends."""
    import dataclasses

    from typehaus.joints.bearing import bearing_connections

    every = dataclasses.replace(config.uplift, tie_floor_joists_on_walls=True)
    tied = {(c.support_tag, c.key_point) for c in bearing_connections(ctx.model, config.uplift)}
    out: dict = {}
    for c in bearing_connections(ctx.model, every):
        if c.support_tag in walls and (c.support_tag, c.key_point) not in tied:
            out.setdefault(c.support_tag, []).append(c)
    return out
