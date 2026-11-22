"""Head and sill cripples step aside for a wall register's box.

A sidewall grille over a door sits in the cripple field above its header, and its box is
wider than a cripple bay is guaranteed to be. A framer lays that cripple beside the box
rather than notching it, so the solver does too: each wall-hosted register whose type has
a ``neck`` claims its box's span along the wall, and a cripple landing in it moves to the
nearer side, ``CLEARANCE_M`` off the box. One with no room on either side stays put, and
``mep.terminal_neck_fit`` reports the clash.

Read off the plan, because framing runs before placeables: the attachment's station is
already in framing coordinates (``_framing_axis`` keeps along-wall distances), and the
mount height only has to say head or sill. A leaf, imported by ``framing/solver.py``.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.model.mep import Register
from typehaus.model.placeables import MountKind, WallAttachment
from typehaus.model.plan import PlanModel
from typehaus.quantities import M_PER_IN

__all__ = ["CLEARANCE_M", "attach_terminal_spans", "clear_of_spans"]

#: Cripple face to box side: room for the boot's seams and a screw.
CLEARANCE_M = 0.5 * M_PER_IN

Span = tuple[float, float]


def _register_boxes(plan: PlanModel) -> dict[str, list[tuple[float, float, float]]]:
    """``{wall_tag: [(low_m, high_m, mid_height_m), ...]}``: each hosted box's span along
    its wall, and its centre above the floor."""
    types = {t.tag: t for t in plan.library.register_types}
    out: dict[str, list[tuple[float, float, float]]] = {}
    for element in plan.all_elements():
        if not isinstance(element, Register):
            continue
        attachment = getattr(element.location, "attachment", None)
        catalog = types.get(element.type_ref)
        neck = getattr(catalog, "neck", None)
        if (not isinstance(attachment, WallAttachment) or neck is None or neck.components
                or element.mount.kind is not MountKind.WALL or element.mount.elevation is None):
            continue
        station, half = attachment.distance_from_start.meters, neck.width.meters / 2.0
        mid = element.mount.elevation.meters + catalog.height.meters / 2.0
        out.setdefault(attachment.wall_ref, []).append((station - half, station + half, mid))
    return out


def attach_terminal_spans(plan: PlanModel, by_host: dict[str, list]) -> None:
    """Give each opening the box spans over its head and under its sill, in place."""
    boxes = _register_boxes(plan)
    for wall_tag, openings in by_host.items():
        for i, opening in enumerate(openings):
            low = opening.center_m - opening.width_m / 2.0
            high = opening.center_m + opening.width_m / 2.0
            over = [box for box in boxes.get(wall_tag, ()) if box[0] < high and box[1] > low]
            head = tuple((lo, hi) for lo, hi, mid in over
                         if mid > opening.sill_m + opening.height_m)
            sill = tuple((lo, hi) for lo, hi, mid in over if mid < opening.sill_m)
            if head or sill:
                openings[i] = replace(opening, head_box_spans=head, sill_box_spans=sill)


def clear_of_spans(stations: list[tuple[int, float]], spans: tuple[Span, ...],
                   thickness: float, low: float, high: float) -> list[tuple[int, float]]:
    """``stations`` with any cripple inside a span moved to its nearer side.

    A move must stay off the jacks (``low``/``high`` are the rough opening's edges); one that
    lands on a neighbouring cripple is dropped, since that cripple already stands there.
    """
    if not spans:
        return stations
    reach = thickness / 2.0 + CLEARANCE_M
    moved: list[tuple[int, float]] = []
    for index, station in stations:
        for lo, hi in spans:
            if lo - reach < station < hi + reach:
                sides = [s for s in (lo - reach, hi + reach)
                         if low + thickness / 2.0 <= s <= high - thickness / 2.0]
                if sides:
                    station = min(sides, key=lambda s: abs(s - station))
                break
        moved.append((index, station))
    kept: list[tuple[int, float]] = []
    for index, station in sorted(moved, key=lambda item: item[1]):
        if kept and station - kept[-1][1] < thickness:
            continue
        kept.append((index, station))
    return kept
