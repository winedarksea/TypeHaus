"""The per-panel half of IRC R602.10: what a panel has to BE, not how much of it there is.

``braced_wall.py`` grades the length on a line. These are the rules a single panel either
meets or does not, and they are the ones a braced-wall inspection actually walks:

* **R602.10.5** — a run under the tabulated minimum length is not a panel. It is reported,
  and ``bracing_eval`` gives it zero contributing length, so it can never be quietly
  counted.
* **R602.10.7** — each end of a continuously sheathed line meets one of Figure R602.10.7's
  five end conditions. A 24" return corner is measured from the perpendicular wall's own
  sheathing, not from an authored designation; a hold-down is a real ``Connector`` of kind
  HOLD_DOWN whose catalogued part publishes at least 800 lb. **A device with no published
  allowable is named and refused** — an unrated part is exactly what this rule exists to
  catch (``library/hardware.py``'s CS16 comment is the long version).
* **R602.10.2.2 / .2.3** — a panel begins within 10 ft of each end of the line, adjacent
  panel edges are not more than 20 ft apart, and a line over 16 ft carries at least two.
* **R602.10.2** — a panel is a FULL-HEIGHT section of wall, so a door or window inside one
  is an authoring error, not a shorter panel.
* **R602.10.9** — a panel is supported: something below stands under it in plan.

R602.10.8's connection rules (rim joist or blocking along the panel, the fastening
schedule) and CS-PF's portal-frame geometry are printed as conditions of the PASS, not
graded: nothing in this model carries a nail schedule, and a rule that cannot see its own
input does not get to pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.bracing_eval import evaluate_line
from typehaus.checks.structural.bracing_tables import (
    END_CONDITIONS,
    END_PANEL_ALONE_IN,
    MAX_BETWEEN_PANELS_FT,
    MAX_PANEL_END_DISTANCE_FT,
    MIN_END_HOLDOWN_LB,
    MIN_RETURN_CORNER_IN,
    MIN_TWO_PANELS_OVER_FT,
)
from typehaus.findings import Finding, failed, not_applicable, passed
from typehaus.hardware.catalog import allowable_for_model
from typehaus.model.enums import ConnectorKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.braced_walls import (
    KIND_BRACED,
    braced_wall_lines,
    line_openings,
    resolved_braced_wall_panels,
)

_ID = "structural.braced_wall_panel_rules"

#: How close a panel edge has to be to the end of the line to count as "at the end".
_AT_END_IN = 0.25
#: How far a wall below may sit off the line and still be what the panel stands on. A wall
#: below is a different assembly at a different thickness, so its axis is not the one above.
_SUPPORT_OFFSET_IN = 12.0
#: How much of a panel has to have something under it (R602.10.9 is about support, and a
#: panel whose last inch oversails a rim is supported).
_SUPPORT_COVERAGE = 0.95

#: R602.10.8, printed on the PASS rather than graded — the model carries no nail schedule.
CONNECTION_CONDITIONS = (
    "R602.10.8: a rim joist, band joist or blocking runs the full length of each panel "
    "where joists are perpendicular, a parallel framing member or full-depth blocking at "
    "16 in o.c. where they are parallel, and the plate fastening is Table R602.3(1); "
    "connections to concrete are R403.1.6. None of that is modelled and none of it is "
    "graded here"
)


@dataclass(frozen=True)
class EndCondition:
    """One end of one line: which of Figure R602.10.7's five conditions it meets."""

    line_tag: str
    end: str            #: "start" or "end" of the line
    condition: int | None
    detail: str


@check(Tier.STRUCTURAL, _ID)
def braced_wall_panel_rules(ctx: CheckContext) -> list[Finding]:
    findings: list[Finding] = []
    graded = 0
    for storey in [s.tag for s in ctx.model.plan.storeys]:
        lines = braced_wall_lines(ctx.model, storey)
        if not lines:
            continue
        panels, unplaced = resolved_braced_wall_panels(ctx.model, storey, lines)
        for panel in unplaced:
            findings.append(failed(
                _ID, f"{storey}: braced wall panel {panel.tag} {panel.reason} "
                     f"(wall_ref={panel.wall_ref!r})", (panel.tag,), code="IRC R602.10.2",
                fix="name a wall that stands on a braced wall line, or delete the panel"))
        for line in lines:
            mine = [p for p in panels if p.line_tag == line.tag]
            if line.kind != KIND_BRACED or not mine:
                continue
            graded += len(mine)
            findings += _line_findings(ctx, storey, line, lines, mine, panels)
    if not graded and not findings:
        return [not_applicable(
            _ID, "no braced wall panel is authored in this plan, so there is no panel to "
                 "grade — `structural.braced_wall_panels` is where that absence is "
                 "reported", code="IRC R602.10.2")]
    if not findings:
        return [passed(_ID, f"{graded} braced wall panel(s) meet R602.10.5's minimum "
                            f"length, R602.10.7's end conditions, R602.10.2.2's spacing and "
                            f"R602.10.9's support. {CONNECTION_CONDITIONS}",
                       code="IRC R602.10")]
    return findings


def _line_findings(ctx, storey, line, lines, mine, panels) -> list[Finding]:
    out: list[Finding] = []
    evaluation = evaluate_line(ctx.model, line, lines, panels)
    for grade in evaluation.panels:
        if grade.minimum is not None and grade.contributes_in <= 0.0:
            out.append(failed(
                _ID, f"{storey}: {'/'.join(grade.panel.tags)} on {line.tag} is "
                     f"{grade.panel.length_in:.1f} in — {grade.reason} ({grade.minimum.row})",
                grade.panel.tags, code="IRC R602.10.5",
                fix="lengthen the panel, or delete it and let the line stand on the rest"))
        if grade.panel.contains_opening:
            out.append(failed(
                _ID, f"{storey}: {'/'.join(grade.panel.tags)} on {line.tag} runs across "
                     f"{', '.join(grade.panel.contains_opening)} — R602.10.2 makes a panel a "
                     f"FULL-HEIGHT section of wall",
                grade.panel.tags + grade.panel.contains_opening, code="IRC R602.10.2",
                fix="split the panel at the opening"))
    out += _location_findings(storey, line, mine)
    out += _support_findings(ctx, storey, line, mine)
    for end in _end_conditions(ctx, storey, line, lines, panels):
        if end.condition is None:
            out.append(failed(
                _ID, f"{storey}: the {end.end} of {line.tag} meets none of Figure "
                     f"R602.10.7's end conditions — {end.detail}",
                (line.tag,), code="IRC R602.10.7",
                fix=f"a {MIN_RETURN_CORNER_IN:.0f} in sheathed return at the corner, a "
                    f"{END_PANEL_ALONE_IN:.0f} in panel at the end, or a "
                    f"{MIN_END_HOLDOWN_LB:.0f} lb hold-down named by the end panel's "
                    f"hold_down_ref"))
    return out


def _location_findings(storey, line, mine) -> list[Finding]:
    out: list[Finding] = []
    runs = sorted(mine, key=lambda p: p.u0_m)
    length_ft = line.length_ft
    first = runs[0].u0_m / M_PER_IN / 12.0
    last = (line.length_m - runs[-1].u1_m) / M_PER_IN / 12.0
    for where, distance in (("start", first), ("end", last)):
        if distance > MAX_PANEL_END_DISTANCE_FT + 1e-6:
            out.append(failed(
                _ID, f"{storey}: the first panel from the {where} of {line.tag} begins "
                     f"{distance:.1f}' in, past R602.10.2.2's {MAX_PANEL_END_DISTANCE_FT:.0f}'",
                (line.tag,), code="IRC R602.10.2.2",
                fix="add a panel within 10 ft of that end"))
    for a, b in zip(runs, runs[1:], strict=False):
        gap = (b.u0_m - a.u1_m) / M_PER_IN / 12.0
        if gap > MAX_BETWEEN_PANELS_FT + 1e-6:
            out.append(failed(
                _ID, f"{storey}: {'/'.join(a.tags)} and {'/'.join(b.tags)} on {line.tag} "
                     f"have {gap:.1f}' between their adjacent edges, over R602.10.2.2's "
                     f"{MAX_BETWEEN_PANELS_FT:.0f}'", a.tags + b.tags,
                code="IRC R602.10.2.2", fix="add a panel between them"))
    if length_ft > MIN_TWO_PANELS_OVER_FT and len(runs) < 2:
        out.append(failed(
            _ID, f"{storey}: {line.tag} is {length_ft:.1f}' long and carries one panel — "
                 f"R602.10.2.3 asks a line over {MIN_TWO_PANELS_OVER_FT:.0f}' for not less "
                 f"than two", (line.tag, *runs[0].tags), code="IRC R602.10.2.3",
            fix="designate the sheathed length as two panels"))
    return out


def _support_findings(ctx, storey, line, mine) -> list[Finding]:
    """R602.10.9 — what stands under the panel on the storey below."""
    here = ctx.model.plan.storey(storey)
    if here is None:
        return []
    below = [s.tag for s in ctx.model.plan.storeys
             if s.building == here.building and s.elevation.meters < here.elevation.meters]
    if not below:
        return []   # the lowest storey of its building bears on its own foundation
    supports = []
    for wall in ctx.model.walls:
        if wall.storey not in below:
            continue
        (ax, ay), (bx, by) = wall.axis
        if abs(_across(line, (ax, ay))) > _SUPPORT_OFFSET_IN * M_PER_IN or \
                abs(_across(line, (bx, by))) > _SUPPORT_OFFSET_IN * M_PER_IN:
            continue
        supports.append(sorted((line.station_m((ax, ay)), line.station_m((bx, by)))))
    out = []
    for panel in mine:
        covered = _covered(panel.u0_m, panel.u1_m, supports)
        span = panel.u1_m - panel.u0_m
        if span > 0 and covered / span < _SUPPORT_COVERAGE:
            out.append(failed(
                _ID, f"{storey}: {'/'.join(panel.tags)} on {line.tag} has "
                     f"{(span - covered) / M_PER_IN:.1f} in of its length with no wall under "
                     f"it on {', '.join(sorted(below))} — R602.10.9 asks what supports a "
                     f"braced wall panel", panel.tags, code="IRC R602.10.9",
                fix="carry the panel on a wall, a beam designed for it, or move the panel"))
    return out


def _across(line, point) -> float:
    ux, uy = (line.p1[0] - line.p0[0]) / line.length_m, (line.p1[1] - line.p0[1]) / line.length_m
    dx, dy = point[0] - line.p0[0], point[1] - line.p0[1]
    return -dx * uy + dy * ux


def _covered(u0: float, u1: float, spans) -> float:
    """How much of ``[u0, u1]`` the (possibly overlapping) spans cover."""
    pieces = sorted((max(u0, a), min(u1, b)) for a, b in spans if b > u0 and a < u1)
    total, edge = 0.0, u0
    for a, b in pieces:
        a = max(a, edge)
        if b > a:
            total += b - a
            edge = b
    return total


def _end_conditions(ctx, storey, line, lines, panels) -> list[EndCondition]:
    """Figure R602.10.7, both ends of one continuously sheathed line."""
    mine = sorted([p for p in panels if p.line_tag == line.tag], key=lambda p: p.u0_m)
    if not mine:
        return []
    out = []
    for where, panel, distance_m in (("start", mine[0], mine[0].u0_m),
                                     ("end", mine[-1], line.length_m - mine[-1].u1_m)):
        point = line.p0 if where == "start" else line.p1
        at_end = distance_m <= _AT_END_IN * M_PER_IN
        if at_end and panel.length_in >= END_PANEL_ALONE_IN - 1e-6:
            out.append(EndCondition(line.tag, where, 3, (
                f"end condition 3: {END_CONDITIONS[3]} ({panel.length_in:.1f} in)")))
            continue
        return_in, return_tag = _corner_return(ctx, storey, line, lines, point)
        device = _hold_down(ctx, panel)
        if return_in >= MIN_RETURN_CORNER_IN - 1e-6:
            condition = 1 if at_end else 4
            out.append(EndCondition(line.tag, where, condition, (
                f"end condition {condition}: {END_CONDITIONS[condition]} "
                f"({return_in:.1f} in on {return_tag})")))
            continue
        if device[0]:
            condition = 2 if at_end else 5
            out.append(EndCondition(line.tag, where, condition, (
                f"end condition {condition}: {END_CONDITIONS[condition]} ({device[1]})")))
            continue
        out.append(EndCondition(line.tag, where, None, (
            f"the nearest panel {'/'.join(panel.tags)} begins "
            f"{distance_m / M_PER_IN:.1f} in from the end; the corner return is "
            f"{return_in:.1f} in against {MIN_RETURN_CORNER_IN:.0f} in"
            + (f"; {device[1]}" if device[1] else "; no hold_down_ref is authored on it"))))
    return out


def _corner_return(ctx, storey, line, lines, corner) -> tuple[float, str]:
    """The sheathed return at this corner, measured on the perpendicular line's own wall.

    A return is a fact about the building — 24 inches of full-height sheathing around the
    corner — so it is measured from that wall's first opening, not from whether somebody
    designated a panel there.
    """
    best, tag = 0.0, "no perpendicular braced wall line at this corner"
    for other in lines:
        if other.direction == line.direction:
            continue
        for end in (other.p0, other.p1):
            if abs(end[0] - corner[0]) > 2.0 * MIN_RETURN_CORNER_IN * M_PER_IN or \
                    abs(end[1] - corner[1]) > 2.0 * MIN_RETURN_CORNER_IN * M_PER_IN:
                continue
            station = other.station_m(end)
            openings = line_openings(ctx.model, other)
            if station <= _AT_END_IN * M_PER_IN:
                nearest = min((o.u0_m for o in openings), default=other.length_m)
                clear = nearest
            else:
                nearest = max((o.u1_m for o in openings), default=0.0)
                clear = other.length_m - nearest
            if clear > best:
                best, tag = clear / M_PER_IN, other.tag
    return best, tag


def _hold_down(ctx, panel) -> tuple[bool, str]:
    """``(qualifies, the sentence)`` for the panel's authored ``hold_down_ref``."""
    if not panel.hold_down_refs:
        return False, ""
    for ref in panel.hold_down_refs:
        element = ctx.model.plan.by_tag(ref)
        if element is None or getattr(element, "kind", None) is not ConnectorKind.HOLD_DOWN:
            return False, f"hold_down_ref {ref!r} is not a Connector of kind HOLD_DOWN"
        allowable = allowable_for_model(element.size)
        if allowable is None or allowable.uplift_lb is None:
            return False, (f"{ref} is a {element.size or 'part with no model'} and this "
                           f"catalog publishes no allowable tension for it — an unrated "
                           f"device is refused, never counted")
        if allowable.uplift_lb < MIN_END_HOLDOWN_LB:
            return False, (f"{ref} ({element.size}) publishes {allowable.uplift_lb:.0f} lb "
                           f"against the {MIN_END_HOLDOWN_LB:.0f} lb Figure R602.10.7 asks "
                           f"for")
        return True, (f"{ref} ({element.size}) publishes {allowable.uplift_lb:.0f} lb "
                      f"against the {MIN_END_HOLDOWN_LB:.0f} lb required")
    return False, ""
