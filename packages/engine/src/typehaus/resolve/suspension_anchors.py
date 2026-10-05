"""A ``SuspensionAnchor``'s framing: one joist line at its station, in the floor plumb above.

The line is derived, never authored. Within 6" of a regular line, that line moves to the
station and takes the anchor's member; otherwise a line is added (key ``aNN``). Two anchors
on one station share one line. Members stay category ``"joist"``, so blocking, subfloor,
bay grading, glTF and take-off treat the line as the joist it is. Removing the anchor
leaves the floor exactly as authored.

A host that is not a plain joist field (open-web trusses, a deck) resolves no line and the
record carries the reason; ``structural.suspension_anchor`` reports it as UNKNOWN.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from shapely.geometry import Point, Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorSystem
from typehaus.model.suspension import SuspensionAnchor, suspension_anchors
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section

#: The 6" rule of ``resolve/floor_lines.py``: closer than this, two lines share one tie.
_SNAP_M = inch(6).meters
#: Two anchors this close across the joists hang from the same line.
_SHARE_M = inch(0.5).meters


@dataclass(frozen=True)
class ResolvedSuspensionAnchor:
    """Where an anchor landed, and what it framed. ``reason`` set means nothing was framed."""

    uid: str
    tag: str
    carries: str
    xy: tuple[float, float] | None = None
    floor: str | None = None
    member: str | None = None
    line_key: str | None = None
    perp_m: float | None = None    # the line's station across the joists
    along_m: float | None = None   # the load's station along the joist
    span_m: tuple[float, float] | None = None  # bearing axes either side of the load
    bearings: tuple[str | None, str | None] = (None, None)
    tributary_m: float | None = None  # floor width the line carries, half a bay each side
    reason: str | None = None


@dataclass(frozen=True)
class AnchorTarget:
    anchor: SuspensionAnchor
    xy: tuple[float, float]


def anchor_point(plan, anchor: SuspensionAnchor) -> tuple[tuple[float, float] | None, str]:
    """The anchor's plan point off its carried item's AUTHORED point, or None and why.

    Floors resolve before placeables, so this reads the source position, not ``placed_xy``.
    """
    carried = plan.by_tag(anchor.carries)
    if carried is None:
        return None, f"carries {anchor.carries}, which is not authored"
    location = getattr(carried, "location", None)
    position = getattr(carried, "position", None) or getattr(location, "position", None)
    if position is None:
        return None, f"{anchor.carries} is wall-attached; an anchor hangs a free-placed item"
    rotation = getattr(carried, "rotation", None) or getattr(location, "rotation", None)
    turn = math.radians(getattr(rotation, "degrees", 0.0) or 0.0)
    dx, dy = anchor.offset.xy_m
    x, y = position.xy_m
    return (x + dx * math.cos(turn) - dy * math.sin(turn),
            y + dx * math.sin(turn) + dy * math.cos(turn)), ""


def _storey_of(plan, element) -> object | None:
    return next((s for s in plan.storeys if element in plan.storey_elements(s.tag)), None)


def _host(plan, anchor: SuspensionAnchor, xy) -> tuple[FloorSystem | None, str]:
    """The floor system to frame in: ``floor_ref``, else the one plumb above on the next level."""
    if anchor.floor_ref is not None:
        host = plan.by_tag(anchor.floor_ref)
        if not isinstance(host, FloorSystem):
            return None, f"floor_ref {anchor.floor_ref} is not a FloorSystem"
        return host, ""
    storey = _storey_of(plan, plan.by_tag(anchor.carries))
    floor = storey.elevation.meters if storey is not None else math.inf
    # The lowest floor above whose outline covers the point; an unoutlined floor covers
    # its whole storey, so it answers only where no outlined one does.
    above = [(s.elevation.meters, el) for s in plan.storeys
             if s.elevation.meters > floor + 1e-6
             for el in plan.storey_elements(s.tag) if isinstance(el, FloorSystem)]
    hit = [(z, f) for z, f in above if f.outline and Polygon(
        [p.xy_m for p in f.outline]).buffer(1e-6).contains(Point(xy))]
    hit = hit or [(z, f) for z, f in above if not f.outline]
    if not hit:
        return None, "no FloorSystem plumb above it (a roof, a ceiling or open air)"
    return min(hit, key=lambda pair: pair[0])[1], ""


def anchor_targets(model) -> dict[str, list[AnchorTarget]]:
    """Group the plan's anchors by host floor tag; record the unhostable ones as they fall."""
    plan = model.plan
    targets: dict[str, list[AnchorTarget]] = {}
    for anchor in suspension_anchors(plan):
        xy, why = anchor_point(plan, anchor)
        host, why = (_host(plan, anchor, xy) if xy is not None else (None, why))
        if host is not None:
            why = _unframeable(host)
        if why:
            model.suspension_anchors.append(_record(anchor, xy, reason=why,
                                                    floor=host.tag if host else None))
            continue
        targets.setdefault(host.tag, []).append(AnchorTarget(anchor, xy))
    return targets


def _unframeable(host: FloorSystem) -> str:
    if host.service == "deck":
        return f"{host.tag} is an exterior deck, not an interior joist field"
    if host.joists.web_panel_pitch is not None:
        return (f"{host.tag} is open-web floor trusses: an added line is a truss order, "
                "not a field change")
    return ""


def _record(anchor: SuspensionAnchor, xy, **kw) -> ResolvedSuspensionAnchor:
    return ResolvedSuspensionAnchor(uid=anchor.uid, tag=anchor.tag, carries=anchor.carries,
                                    xy=xy, **kw)


def lay_anchor_lines(model, system: FloorSystem, targets, positions: list[float],
                     extra: list[float], perp0: float, perp1: float,
                     boundaries: list[float], refs_at: list[tuple[str, float]],
                     along_x: bool) -> tuple[list[float], dict[str, str], list[Finding]]:
    """Move or add one line per anchor station; ``positions`` is moved in place.

    Returns the added stations (keyed ``aNN`` in that order), the member each anchor line
    takes by line key, and refusals as ERROR findings.
    """
    added: list[float] = []
    members: dict[str, str] = {}
    findings: list[Finding] = []
    depth = cross_section(system.joists.member).depth_m
    for target in targets:
        anchor, (x, y) = target.anchor, target.xy
        perp, along = (y, x) if along_x else (x, y)
        why = _refusal(anchor, perp, along, perp0, perp1, boundaries, depth)
        key = None
        if not why:
            key, why = _line_for(perp, positions, extra, added, members, anchor)
        if why:
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.suspension_anchor_line",
                message=f"{anchor.tag}: {why}; no line is framed for it",
                element_tags=(anchor.tag, system.tag), result=Result.FAIL))
            model.suspension_anchors.append(_record(anchor, target.xy, floor=system.tag,
                                                    reason=why))
            continue
        members[key] = anchor.framing_member
        index = next(i for i, (a, b) in enumerate(zip(boundaries, boundaries[1:], strict=False))
                     if a - 1e-9 <= along <= b + 1e-9)
        span = (boundaries[index], boundaries[index + 1])
        model.suspension_anchors.append(_record(
            anchor, target.xy, floor=system.tag, member=anchor.framing_member, line_key=key,
            perp_m=perp, along_m=along, span_m=span,
            bearings=tuple(_bearing_at(refs_at, coord) for coord in span)))
    lines = sorted(positions + extra + added)
    model.suspension_anchors[:] = [_with_tributary(r, lines) if r.floor == system.tag
                                   and r.perp_m is not None else r
                                   for r in model.suspension_anchors]
    return added, members, findings


def _refusal(anchor, perp, along, perp0, perp1, boundaries, depth) -> str:
    if not perp0 - 1e-9 <= perp <= perp1 + 1e-9:
        return "its station lies outside the joist field"
    if not boundaries[0] - 1e-9 <= along <= boundaries[-1] + 1e-9:
        return "it lies past the outermost bearing (a cantilever is not graded)"
    if abs(cross_section(anchor.framing_member).depth_m - depth) > inch(1 / 16).meters:
        return (f"{anchor.framing_member} is not the field's {depth / inch(1).meters:.3f}\" "
                "depth, so it cannot replace a joist line")
    return ""


def _line_for(perp, positions, extra, added, members, anchor) -> tuple[str | None, str]:
    """The key of the line this station hangs from, moving or adding one as needed."""
    for index, at in enumerate(added):
        gap = abs(at - perp)
        if gap < _SHARE_M:
            key = f"a{index:02d}"
            return (key, "") if members[key] == anchor.framing_member else (
                None, f"shares a line framed in {members[key]}")
        if gap < _SNAP_M:
            return None, f"is {gap / inch(1).meters:.2f}\" from another anchor's line"
    nearest = min(range(len(positions)), key=lambda i: abs(positions[i] - perp))
    gap = abs(positions[nearest] - perp)
    key = f"{nearest:03d}"
    if gap < _SNAP_M and key in members:
        return (key, "") if gap < _SHARE_M and members[key] == anchor.framing_member else (
            None, f"is {gap / inch(1).meters:.2f}\" from another anchor's line")
    clash = min((abs(e - perp) for e in extra), default=math.inf)
    if gap < _SNAP_M and nearest in (0, len(positions) - 1) and gap > 1e-6:
        return None, "is within 6\" of the field's edge joist, which cannot move"
    if gap < _SNAP_M and clash >= _SNAP_M:
        if gap > 1e-9:  # an exact hit keeps the authored station's own float
            positions[nearest] = perp
        return key, ""
    if clash < _SNAP_M:
        return None, f"is {clash / inch(1).meters:.2f}\" from an authored extra line"
    added.append(perp)
    return f"a{len(added) - 1:02d}", ""


def _bearing_at(refs_at: list[tuple[str, float]], coord: float) -> str | None:
    return next((tag for tag, at in refs_at if abs(at - coord) < 1e-6), None)


def _with_tributary(record: ResolvedSuspensionAnchor, lines: list[float]):
    below = max((p for p in lines if p < record.perp_m - 1e-6), default=None)
    above = min((p for p in lines if p > record.perp_m + 1e-6), default=None)
    halves = [abs(record.perp_m - p) / 2 for p in (below, above) if p is not None]
    return replace(record, tributary_m=sum(halves))


def unframed(model, targets: dict[str, list[AnchorTarget]]) -> None:
    """Record every hosted anchor its floor never reached (a floor that framed nothing)."""
    seen = {record.tag for record in model.suspension_anchors}
    for tag, hosted in targets.items():
        model.suspension_anchors.extend(
            _record(t.anchor, t.xy, floor=tag, reason=f"{tag} framed no joist field")
            for t in hosted if t.anchor.tag not in seen)
