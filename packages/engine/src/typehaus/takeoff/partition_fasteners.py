"""The SDPW DEFLECTOR screws at every interior partition's top plate.

``resolve/partition_top.py`` stops a partition's framing 3/4" clear of the structure over
it; this bills the screw that spans that gap. Its own module rather than a fifth derivation
in ``takeoff/fasteners.py``, which is 491 lines against AGENTS.md's 500.

**The count is one screw per crossing, never a pitch along the plate**, because a screw has
to land IN something. That splits three ways, and coding only the last would call for
blocking in bays that already have a joist in them:

============================================  =======================================
condition                                     count
============================================  =======================================
partition PERPENDICULAR to the framing above  one per resolved crossing
partition UNDER a parallel member             a pitch along the shared run, both ends
partition BETWEEN parallel members            one blocked bay per framing module
============================================  =======================================

**The gap is measured, never assumed.** A rafter's underside is interpolated along its own
rake and the raked plate along the wall's, or every attic crossing would read zero at one
end and a foot at the other. A measured gap outside ``[-tolerance, maximum_gap_in]`` bills
**nothing** and is reported as a refusal — which is also what stops this billing a screw
across the -11 7/8" gap the attic had before ``apply_partition_tops`` existed, and is why
Part 1 of that change is a hard precondition for this one.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from typehaus.hardware.catalog import (
    ROLE_PARTITION_DEFLECTION_SCREW,
    hardware_for_role_and_nominal,
)
from typehaus.hardware.config import PartitionDeflectionRules
from typehaus.hardware.plan_geometry import point_in_ring, segment_crossing
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.partition import (
    bearing_ref_tags,
    framing_top_z_m,
    takes_a_deflection_gap,
)
from typehaus.resolve.roof_geometry import roof_structure_framing
from typehaus.takeoff.hardware_row import hardware_row

_PERPENDICULAR = "partition top plate, perpendicular framing above"
_UNDER_MEMBER = "partition top plate, under a parallel member"
_BETWEEN_MEMBERS = "partition top plate, blocking between parallel members"

#: Simpson's own top-plate conditions, verbatim enough to look up in the table. These are
#: ``StructuralHardware.fits_nominal`` keys, so the catalog answers "which screw is this
#: joint's screw" and this module never names a part number.
_PLATE_SINGLE = "single 2x top plate"
_PLATE_BUILT_UP = "built-up top plate to 2-1/4 in"
_PLATE_DOUBLE = "double 2x top plate"


def _unit(p0: tuple, p1: tuple) -> tuple[float, float, float]:
    """``(ux, uy, length)`` of ``p0``→``p1``; a degenerate segment reports length 0."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    run = math.hypot(dx, dy)
    return (0.0, 0.0, 0.0) if run < 1e-9 else (dx / run, dy / run, run)


def _lerp(start: float, end: float | None, fraction: float) -> float:
    """A member's own elevation at ``fraction`` along it; flat when it carries no second end."""
    return start if end is None else start + (end - start) * fraction


def _plate_top_at(wall: Any, fraction: float) -> float:
    """The wall's FRAMING top at ``fraction`` along its axis.

    A raked partition's plate follows the rafters, so a single elevation is wrong for it by
    up to the wall's whole rise — 5'-0" on ``W-A-STU-N``.
    """
    if wall.top_z0_m is not None and wall.top_z1_m is not None:
        return _lerp(wall.top_z0_m, wall.top_z1_m, fraction)
    return framing_top_z_m(wall)


def _top_plate_through_in(wall: Any) -> float | None:
    """How much plate a screw crosses before it reaches the member above.

    Read off the wall's OWN resolved plate members rather than assumed to be 3": a house
    that later sets ``advanced_framing=True`` frames a single top plate and follows this
    rule without the rule knowing. ``None`` where the wall frames no top plate at all.
    """
    courses = [member for member in wall.members
               if member.category in ("plate", "raked_plate")
               and not member.child_key.endswith("bottom")]
    return sum(member.z1_m - member.z0_m for member in courses) / M_PER_IN if courses else None


def _plate_plan_width_in(wall: Any) -> float:
    """The plate's width across the wall. A plate lies FLAT, so that is its section DEPTH."""
    for member in wall.members:
        if member.category in ("plate", "raked_plate"):
            section = cross_section(member.profile)
            if section is not None:
                return section.depth_m / M_PER_IN
    return wall.thickness_m / M_PER_IN


def _member_plan_width_in(member: Any) -> float:
    """The member's width in plan. A joist or rafter stands on edge, so that is its WIDTH."""
    section = cross_section(member.profile)
    return 0.0 if section is None else section.width_m / M_PER_IN


def _structures_over(model: ResolvedModel, wall: Any,
                     rules: PartitionDeflectionRules) -> list[tuple]:
    """``(members, spacing_in)`` for each framed deck or roof standing over ``wall``.

    Scoped by ``point_in_ring`` on the wall's plan midpoint as well as by elevation. Without
    the plan gate ``W-A-SN`` "crosses" members in the garage, which is a separate building.
    """
    (x0, y0), (x1, y1) = wall.axis
    midpoint = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    out: list[tuple] = []
    for floor in model.floors:
        if not floor.deck_outline or not point_in_ring(midpoint, floor.deck_outline):
            continue
        members = tuple(m for m in floor.members
                        if m.category in rules.screwable_floor_categories)
        out.append((members, _spacing_in(getattr(model.plan.by_tag(floor.tag),
                                                 "joists", None))))
    for roof in model.roofs:
        if not roof.footprint or not point_in_ring(midpoint, roof.footprint):
            continue
        members = tuple(m for m in roof.members
                        if m.category in rules.screwable_roof_categories)
        out.append((members, _spacing_in(roof_structure_framing(model, roof))))
    return [entry for entry in out if entry[0]]


def _spacing_in(spec: Any) -> float | None:
    """The framing module of the deck or roof above, in inches, or ``None`` if unreadable.

    **No fallback.** A blocked-bay count derived from a guessed spacing is a quantity
    nobody can check, and the refusal in the caller says so by name instead.
    """
    spacing = getattr(spec, "spacing", None)
    return None if spacing is None else spacing.meters / M_PER_IN


def _classify(wall: Any, members: tuple, spacing_in: float | None,
              rules: PartitionDeflectionRules) -> tuple:
    """``(crossings, over_plate, in_bay)`` over ``wall`` — each entry a measured gap, inches.

    Three readings, because the screw's count rule is three rules:

    * **crossings** — members the wall runs ACROSS. One screw each.
    * **over_plate** — a PARALLEL member standing over the plate by at least
      ``minimum_member_overlap_in``. A pitch along the shared run.
    * **in_bay** — a parallel member within one framing module to the SIDE of the wall, so
      the wall runs BETWEEN members. Blocked bays. ``in_bay`` is a superset of
      ``over_plate``; the caller takes them in priority order.

    Every entry carries the gap MEASURED at that member, interpolated along the member's own
    rake and along the wall's. That measurement is also the elevation scope: this is handed
    every screwable member of every deck and roof whose footprint covers the wall, the decks
    UNDER it included, and it is the caller's ``[-tolerance, maximum_gap_in]`` window that
    picks out the structure actually overhead. Nothing here guesses at which deck is which.
    """
    (ax, ay), (bx, by) = wall.axis
    ux, uy, run = _unit(wall.axis[0], wall.axis[1])
    if run <= 0.0:
        return ((), (), ())
    plate_half_in = _plate_plan_width_in(wall) / 2.0
    bay_reach_in = plate_half_in + (spacing_in if spacing_in else 0.0)
    crossings: list[float] = []
    over_plate: list[float] = []
    in_bay: list[float] = []
    for member in members:
        mx, my, member_run = _unit(member.p0, member.p1)
        if member_run <= 0.0:
            continue
        if abs(ux * my - uy * mx) > rules.parallel_axis_tolerance:
            hit = segment_crossing(member.p0, member.p1, (ax, ay), (bx, by))
            if hit is None:
                continue
            _point, along_member, along_wall = hit
            crossings.append((_lerp(member.z0_m, member.z0_end_m, along_member)
                              - _plate_top_at(wall, along_wall)) / M_PER_IN)
            continue
        # Parallel. How much of it shares the wall's run, and how far off its line is it?
        stations = sorted(((point[0] - ax) * ux + (point[1] - ay) * uy)
                          for point in (member.p0, member.p1))
        lo, hi = max(stations[0], 0.0), min(stations[1], run)
        if hi - lo <= 1e-9:
            continue
        offset_in = abs(-uy * (member.p0[0] - ax) + ux * (member.p0[1] - ay)) / M_PER_IN
        half_in = _member_plan_width_in(member) / 2.0
        if offset_in - half_in > bay_reach_in:
            continue
        centre_station = (lo + hi) / 2.0
        along_wall = centre_station / run
        centre = (ax + ux * centre_station, ay + uy * centre_station)
        along_member = min(abs((centre[0] - member.p0[0]) * mx
                               + (centre[1] - member.p0[1]) * my) / member_run, 1.0)
        gap_in = (_lerp(member.z0_m, member.z0_end_m, along_member)
                  - _plate_top_at(wall, along_wall)) / M_PER_IN
        in_bay.append(gap_in)
        if plate_half_in + half_in - offset_in >= rules.minimum_member_overlap_in:
            over_plate.append(gap_in)
    return (tuple(crossings), tuple(over_plate), tuple(in_bay))


def _in_range(gap_in: float, rules: PartitionDeflectionRules) -> bool:
    """Is this a deflection joint at all — or is it a deck under the wall, or a prop?"""
    return -rules.gap_search_tolerance_in <= gap_in <= rules.maximum_gap_in


def _plate_condition(plate_in: float, rules: PartitionDeflectionRules) -> str | None:
    """Which of Simpson's published TOP-PLATE conditions this wall frames, or ``None``.

    **The plate decides the part, before any length arithmetic does**, and getting that
    round the wrong way is how a house ends up billing a screw published for a different
    joint. C-F-2025TECHSUP p. 101: the SDPW14500's allowables and spacing "may be used for
    the built-up top plate (maximum thickness 2-1/4 in) as well as the single nominal 2x
    top plate", while the SDPW19600's are the ones published "for the double 2x top plate
    and thinner top plates". Catlin frames a double 2x — 3" — on all eleven of its interior
    assemblies, so the 5" screw is the wrong part for it however comfortably 5" reaches.

    Above a double 2x nothing is published, and this returns ``None`` rather than
    extrapolating off the end of the table.
    """
    if plate_in <= rules.single_plate_in + 1e-9:
        return _PLATE_SINGLE
    if plate_in <= rules.built_up_plate_limit_in + 1e-9:
        return _PLATE_BUILT_UP
    if plate_in <= 2.0 * rules.single_plate_in + 1e-9:
        return _PLATE_DOUBLE
    return None


def partition_deflection_screw_rows(model: ResolvedModel,
                                    rules: PartitionDeflectionRules) -> list:
    """One row per (condition, part, required length) — plus a refusal row where one is due.

    Grouped on ``(scope, part number, required length)`` and carrying a ``by_storey``
    Counter, the shape ``fasteners.truss_wall_block_screw_rows`` already bills screws in.
    """
    bearing_refs = bearing_ref_tags(model.plan)
    groups: dict = {}
    refusals: list[str] = []
    for wall in model.walls:
        if not takes_a_deflection_gap(model, wall, bearing_refs):
            continue
        run_in = _unit(wall.axis[0], wall.axis[1])[2] / M_PER_IN
        plate_in = _top_plate_through_in(wall)
        if plate_in is None:
            refusals.append(f"{wall.tag}: frames no top plate to screw through")
            continue
        condition = _plate_condition(plate_in, rules)
        if condition is None:
            refusals.append(f"{wall.tag}: {plate_in:.3g} in of top plate is thicker than "
                            "any published SDPW top-plate condition")
            continue
        structures = _structures_over(model, wall, rules)
        if not structures:
            # A slab or SIP soffit has no wood in it — catlin's ``SL-M-DECK`` over
            # ``W-B-CE`` — and a screw into one is a different part on a different rule.
            refusals.append(f"{wall.tag}: no framed structure over it")
            continue
        crossings: list[float] = []
        over_plate: list[float] = []
        in_bay: list[float] = []
        spacings: list[float] = []
        measured: list[float] = []
        for members, spacing_in in structures:
            hits = _classify(wall, members, spacing_in, rules)
            measured.extend(g for group in hits for g in group)
            crossings.extend(g for g in hits[0] if _in_range(g, rules))
            over_plate.extend(g for g in hits[1] if _in_range(g, rules))
            if spacing_in is not None:
                spacings.append(spacing_in)
                in_bay.extend(g for g in hits[2] if _in_range(g, rules))
        if crossings:
            scope = _PERPENDICULAR
            count = len(crossings) * rules.screws_per_crossing
            gap_in = max(crossings)
        elif over_plate:
            scope = _UNDER_MEMBER
            count = int(run_in // rules.along_member_pitch_in) + 1
            gap_in = max(over_plate)
        elif in_bay:
            scope = _BETWEEN_MEMBERS
            count = int(run_in // min(spacings)) + 1
            gap_in = max(in_bay)
        else:
            above = [g for g in measured if g > 0.0]
            nearest = (f"the nearest wood above it is {min(above):.4g} in up"
                       if above else "no wood stands over it at all")
            refusals.append(
                f"{wall.tag}: {nearest}, so nothing reads a gap inside "
                f"[-{rules.gap_search_tolerance_in:g}, {rules.maximum_gap_in:g}] in of its "
                "top plate. A slab or SIP soffit is the usual reason and it is not an SDPW "
                "joint: catlin's SL-M-DECK is what stands over W-B-CE and W-B-BA-E")
            continue
        required_in = gap_in + plate_in + rules.minimum_embedment_in
        item = hardware_for_role_and_nominal(ROLE_PARTITION_DEFLECTION_SCREW, condition)
        reaching = [n for n in item.available_lengths_in if n + 1e-9 >= required_in]
        if not reaching:
            refusals.append(f"{wall.tag}: no {item.model} length reaches "
                            f"{required_in:.2f} in")
            continue
        length_in = min(reaching)
        group = groups.setdefault(
            (scope, item.part_number_by_length_in[length_in], round(required_in, 3)), {
                "item": item, "length_in": length_in,
                "part_number": item.part_number_by_length_in[length_in],
                "scope": scope, "count": 0, "by_storey": Counter(),
                "required_in": required_in, "gap_in": gap_in, "plate_in": plate_in,
                "condition": condition,
                "spacing_in": min(spacings) if spacings else None, "walls": [],
            })
        group["count"] += count
        group["by_storey"][wall.storey] += count
        group["walls"].append(wall.tag)

    # A refusal rides on the BASIS of the rows that were billed, not on a row of its own.
    # A zero-count line with no part number is not a bill of materials: it reaches the
    # per-trade RFQ and the drawing schedule as an order line for nothing. The fact still
    # has to be carried — silently billing nothing is the failure — so every SDPW row says
    # which partition tops got none and why. The standalone row is the degenerate case
    # where NOTHING was billed and there is no basis to ride on.
    note = ("" if not refusals else
            " NOT BILLED at " + "; ".join(sorted(refusals)) + ".")
    rows = [hardware_row(
        group["item"], scope=group["scope"], count=int(group["count"]),
        part_number=group["part_number"], size=f"{group['length_in']:g} in",
        by_storey=dict(sorted(group["by_storey"].items())),
        basis=_basis(group, rules) + note,
    ) for _key, group in sorted(groups.items())]
    if refusals and not rows:
        rows.append(hardware_row(
            None, scope="partition top plate, NOT BILLED", count=0,
            basis=("no SDPW is billed at any partition top, and the reason is recorded "
                   "rather than absorbed:" + note),
        ))
    return rows


def _basis(group: dict, rules: PartitionDeflectionRules) -> str:
    """The rule that produced the count — and, for the blocked bays, what is NOT billed."""
    length = (f"{group['gap_in']:.3g} in gap + {group['plate_in']:.3g} in top plate + "
              f"{rules.minimum_embedment_in:g} in embedment = {group['required_in']:.2f} in "
              "required")
    walls = f"{len(group['walls'])} partition(s)"
    if group["scope"] == _PERPENDICULAR:
        rule = (f"{rules.screws_per_crossing} screw per resolved crossing of the framing "
                f"above, across {walls}")
    elif group["scope"] == _UNDER_MEMBER:
        rule = (f"{rules.along_member_pitch_in:g} in o.c. along {walls} running under a "
                "parallel member, fencepost at both ends")
    else:
        rule = (f"one blocked bay per {group['spacing_in']:g} in framing module along "
                f"{walls} running BETWEEN parallel members, fencepost at both ends. "
                "**The blocking itself is billed nowhere**: it is a required framing "
                "condition this model does not carry — ``resolve/floor_blocking.py`` blocks "
                "a bearing line UNDER a wall, which is the mirror joint, not this one")
    return (f"{rule}. {length}, at the {group['condition']} this wall frames — the "
            "condition the part's own published row is for. A SCHEDULE, not a design: "
            "nothing here grades a demand, because this engine carries no "
            "interior-partition out-of-plane load to grade. Every count above sits inside "
            "the 42 in / 36 in worst case of Simpson's own maximum-spacing table, and the "
            "members these land in are engineered products (TJI rafters, I-joists, "
            "open-web floor trusses) whose own fastener rules have not been read")
