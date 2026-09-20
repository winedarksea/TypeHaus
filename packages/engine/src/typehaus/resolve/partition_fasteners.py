"""Where a partition's top plate meets the structure over it — the joint, once.

``resolve/partition_top.py`` stops an interior partition's framing 3/4" clear of whatever
is above it. Two passes then have to say something about that gap and they must say the
same thing: ``takeoff/partition_fasteners.py`` bills the Simpson SDPW DEFLECTOR that spans
it, and ``checks/structural/partition_fasteners.py`` grades the screw's SPACING against the
manufacturer's published maximum. A check may not import ``takeoff/``, so the arithmetic
lives here — in ``resolve``, where both may reach it — rather than in either of them.

**What a joint records is measured, never assumed.** A rafter's underside is interpolated
along its own rake and the raked plate along the wall's, or every attic crossing would read
zero at one end and a foot at the other; the supporting member's section is read off the
resolved profile, so a guard about a flange thickness is answered by the model and not by a
comment. A gap outside the sleeve's published range yields no joint at all and a refusal
naming the wall — which is what stops a screw being billed across the -11 7/8" gap the
attic had before ``apply_partition_tops`` existed.

The three conditions and their counts are the fastener rule and are documented on
:class:`PartitionTopJoint`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

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

#: ``FramedMember.child_key`` prefix of the blocking ``resolve/floor_blocking.py`` lays for
#: these very screws. Named here because both modules must spell it the same way.
PARTITION_BLOCK_PREFIX = "partition-block-"

# ** A BEARING block IS structure over a partition and is deliberately still read. ** Only
# the blocking laid FOR these screws is excluded, and it has to be: ``floor_blocking`` lays
# it because the screw needs something to land in, so reading it back would turn every such
# wall into a perpendicular crossing and re-derive the count from its own answer. That pass
# runs the bearing course first for the same reason in reverse — it must ask this question
# of a deck that is otherwise finished, or it and the take-off would classify differently.

#: Member categories an end-distance rule is written for. A published minimum end distance
#: guards against splitting the CUT END of a long spanning member; a blocking piece is a
#: short cut-to-fit block and a rim is a board on the deck edge, and holding either to 6"
#: would refuse a joint nobody doubts.
SPANNING_CATEGORIES = ("joist", "rafter", "top_chord", "sister_joist", "trimmer")

#: The three conditions a partition top can be in, in the words the take-off bills them.
PERPENDICULAR = "partition top plate, perpendicular framing above"
UNDER_MEMBER = "partition top plate, under a parallel member"
BETWEEN_MEMBERS = "partition top plate, blocking between parallel members"

#: Simpson's own top-plate conditions, verbatim enough to look up in the table. These are
#: ``StructuralHardware.fits_nominal`` keys, so the catalog answers "which screw is this
#: joint's screw" and nothing here names a part number.
PLATE_SINGLE = "single 2x top plate"
PLATE_BUILT_UP = "built-up top plate to 2-1/4 in"
PLATE_DOUBLE = "double 2x top plate"


@dataclass(frozen=True)
class SupportSection:
    """The supporting member a screw lands in, as the resolved section describes it.

    ``flange_*`` are the i-joist flange or, on an open-web floor truss, the flat 2x chord
    (``framing/profiles.py`` reuses the fields for it deliberately). ``None`` where the
    profile parses to nothing, which is a gap the check reports rather than papers over.
    """

    profile: str
    shape: str | None
    #: Plan width and section depth, for a member the "flange" fields say nothing about —
    #: a solid rim board on edge is a screw target too, just an easier one.
    width_in: float | None
    depth_in: float | None
    flange_thickness_in: float | None
    flange_width_in: float | None


@dataclass(frozen=True)
class PartitionTopJoint:
    """One partition's top-plate joint with the structure over it.

    The count rule is one screw per crossing, never a pitch along the plate, because a
    screw has to land IN something — and that splits three ways:

    ==============  ======================================================================
    ``scope``       count
    ==============  ======================================================================
    PERPENDICULAR   one per resolved crossing of the framing above
    UNDER_MEMBER    a pitch along the shared run, fencepost both ends
    BETWEEN_MEMBERS one blocked bay per framing module, fencepost both ends
    ==============  ======================================================================
    """

    wall_tag: str
    storey: str
    scope: str
    count: int
    #: The on-centre spacing the count implies — what a published maximum-spacing table is
    #: read against.
    pitch_in: float
    #: Measured, at the member that reads widest.
    gap_in: float
    plate_in: float
    plate_condition: str
    #: The framing module of the deck or roof above, where it is readable.
    spacing_in: float | None
    run_in: float
    #: Framing top above the wall's own base: the wall HEIGHT a spacing row is indexed by.
    height_in: float
    #: Distinct sections of the members these screws land in.
    supports: tuple[SupportSection, ...]
    #: The end distance the model can hold this joint to: the crossing's own station
    #: where the wall fixes it, and the best a placement could reach where a pitch can
    #: slide. ``None`` where nothing spanning was hit — a block or a rim is a short piece
    #: cut to a bay, and an end-distance rule written for the cut end of a joist does not
    #: transfer to it.
    end_distance_in: float | None


def _unit(p0: tuple, p1: tuple) -> tuple[float, float, float]:
    """``(ux, uy, length)`` of ``p0``→``p1``; a degenerate segment reports length 0."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    run = math.hypot(dx, dy)
    return (0.0, 0.0, 0.0) if run < 1e-9 else (dx / run, dy / run, run)


def _lerp(start: float, end: float | None, fraction: float) -> float:
    """A member's own elevation at ``fraction`` along it; flat when it carries no second end."""
    return start if end is None else start + (end - start) * fraction


def plate_top_at(wall: Any, fraction: float) -> float:
    """The wall's FRAMING top at ``fraction`` along its axis.

    A raked partition's plate follows the rafters, so a single elevation is wrong for it by
    up to the wall's whole rise — 5'-0" on ``W-A-STU-N``.
    """
    if wall.top_z0_m is not None and wall.top_z1_m is not None:
        return _lerp(wall.top_z0_m, wall.top_z1_m, fraction)
    return framing_top_z_m(wall)


def top_plate_through_in(wall: Any) -> float | None:
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


def _section_of(member: Any) -> SupportSection:
    section = cross_section(member.profile)
    return SupportSection(
        profile=member.profile,
        shape=None if section is None else section.shape,
        width_in=None if section is None else section.width_m / M_PER_IN,
        depth_in=None if section is None else section.depth_m / M_PER_IN,
        flange_thickness_in=None if section is None or section.flange_thickness_m is None
        else section.flange_thickness_m / M_PER_IN,
        flange_width_in=None if section is None or section.flange_width_m is None
        else section.flange_width_m / M_PER_IN,
    )


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
                        if m.category in rules.screwable_floor_categories
                        and not m.child_key.startswith(PARTITION_BLOCK_PREFIX))
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


@dataclass(frozen=True)
class _Hit:
    """One member the wall meets: its measured gap, its section, its end distance."""

    gap_in: float
    section: SupportSection
    end_distance_in: float | None
    width_in: float


def classify(wall: Any, members: tuple, spacing_in: float | None,
             rules: PartitionDeflectionRules) -> tuple[list[_Hit], list[_Hit], list[_Hit]]:
    """``(crossings, over_plate, in_bay)`` over ``wall`` — each a measured hit.

    * **crossings** — members the wall runs ACROSS. One screw each.
    * **over_plate** — a PARALLEL member standing over the plate by at least
      ``minimum_member_overlap_in``. A pitch along the shared run.
    * **in_bay** — a parallel member within one framing module to the SIDE of the wall, so
      the wall runs BETWEEN members. Blocked bays. ``in_bay`` is a superset of
      ``over_plate``; the caller takes them in priority order.

    Every hit carries the gap MEASURED at that member, interpolated along the member's own
    rake and along the wall's. That measurement is also the elevation scope: this is handed
    every screwable member of every deck and roof whose footprint covers the wall, the decks
    UNDER it included, and it is the caller's ``[-tolerance, maximum_gap_in]`` window that
    picks out the structure actually overhead. Nothing here guesses at which deck is which.
    """
    (ax, ay), (bx, by) = wall.axis
    ux, uy, run = _unit(wall.axis[0], wall.axis[1])
    if run <= 0.0:
        return ([], [], [])
    plate_half_in = _plate_plan_width_in(wall) / 2.0
    bay_reach_in = plate_half_in + (spacing_in if spacing_in else 0.0)
    crossings: list[_Hit] = []
    over_plate: list[_Hit] = []
    in_bay: list[_Hit] = []
    for member in members:
        mx, my, member_run = _unit(member.p0, member.p1)
        if member_run <= 0.0:
            continue
        width_in = _member_plan_width_in(member)
        if abs(ux * my - uy * mx) > rules.parallel_axis_tolerance:
            hit = segment_crossing(member.p0, member.p1, (ax, ay), (bx, by))
            if hit is None:
                continue
            _point, along_member, along_wall = hit
            # The screw stands where the wall crosses: its distance to the nearer end of
            # the member it lands in is a real number the model can hand a guard.
            end_in = ((min(along_member, 1.0 - along_member) * member_run) / M_PER_IN
                      if member.category in SPANNING_CATEGORIES else None)
            crossings.append(_Hit(
                (_lerp(member.z0_m, member.z0_end_m, along_member)
                 - plate_top_at(wall, along_wall)) / M_PER_IN,
                _section_of(member), end_in, width_in))
            continue
        # Parallel. How much of it shares the wall's run, and how far off its line is it?
        stations = sorted(((point[0] - ax) * ux + (point[1] - ay) * uy)
                          for point in (member.p0, member.p1))
        lo, hi = max(stations[0], 0.0), min(stations[1], run)
        if hi - lo <= 1e-9:
            continue
        offset_in = abs(-uy * (member.p0[0] - ax) + ux * (member.p0[1] - ay)) / M_PER_IN
        half_in = width_in / 2.0
        if offset_in - half_in > bay_reach_in:
            continue
        centre_station = (lo + hi) / 2.0
        along_wall = centre_station / run
        centre = (ax + ux * centre_station, ay + uy * centre_station)
        along_member = min(abs((centre[0] - member.p0[0]) * mx
                               + (centre[1] - member.p0[1]) * my) / member_run, 1.0)
        gap_in = (_lerp(member.z0_m, member.z0_end_m, along_member)
                  - plate_top_at(wall, along_wall)) / M_PER_IN
        # A pitch along a shared run can SLIDE: where each screw lands is a placement the
        # installer makes, not a fact the model fixes. So what is reported here is the
        # BEST a screw in this member could do — half its own length — which distinguishes
        # a joint no placement can satisfy from one somebody has to place carefully. A
        # crossing above has no such freedom and reports the station itself.
        end_in = (member_run / 2.0 / M_PER_IN
                  if member.category in SPANNING_CATEGORIES else None)
        hit = _Hit(gap_in, _section_of(member), end_in, width_in)
        in_bay.append(hit)
        if plate_half_in + half_in - offset_in >= rules.minimum_member_overlap_in:
            over_plate.append(hit)
    return (crossings, over_plate, in_bay)


def in_range(gap_in: float, rules: PartitionDeflectionRules) -> bool:
    """Is this a deflection joint at all — or is it a deck under the wall, or a prop?"""
    return -rules.gap_search_tolerance_in <= gap_in <= rules.maximum_gap_in


def plate_condition(plate_in: float, rules: PartitionDeflectionRules) -> str | None:
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
        return PLATE_SINGLE
    if plate_in <= rules.built_up_plate_limit_in + 1e-9:
        return PLATE_BUILT_UP
    if plate_in <= 2.0 * rules.single_plate_in + 1e-9:
        return PLATE_DOUBLE
    return None


def partition_top_joints(
    model: ResolvedModel, rules: PartitionDeflectionRules,
) -> tuple[list[PartitionTopJoint], list[str]]:
    """Every partition-top deflection joint in the house, and the refusals beside them.

    A refusal is a sentence naming the wall and why nothing was read there. It is returned
    rather than dropped because silently billing nothing — and silently grading nothing — is
    the failure mode this whole pass exists to avoid.
    """
    bearing_refs = bearing_ref_tags(model.plan)
    joints: list[PartitionTopJoint] = []
    refusals: list[str] = []
    for wall in model.walls:
        if not takes_a_deflection_gap(model, wall, bearing_refs):
            continue
        run_in = _unit(wall.axis[0], wall.axis[1])[2] / M_PER_IN
        plate_in = top_plate_through_in(wall)
        if plate_in is None:
            refusals.append(f"{wall.tag}: frames no top plate to screw through")
            continue
        condition = plate_condition(plate_in, rules)
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
        crossings: list[_Hit] = []
        over_plate: list[_Hit] = []
        in_bay: list[_Hit] = []
        spacings: list[float] = []
        measured: list[float] = []
        for members, spacing_in in structures:
            hits = classify(wall, members, spacing_in, rules)
            measured.extend(hit.gap_in for group in hits for hit in group)
            crossings.extend(hit for hit in hits[0] if in_range(hit.gap_in, rules))
            over_plate.extend(hit for hit in hits[1] if in_range(hit.gap_in, rules))
            if spacing_in is not None:
                spacings.append(spacing_in)
                in_bay.extend(hit for hit in hits[2] if in_range(hit.gap_in, rules))
        module_in = min(spacings) if spacings else None
        if crossings:
            scope, chosen = PERPENDICULAR, crossings
            count = len(crossings) * rules.screws_per_crossing
            pitch_in = module_in if module_in is not None else run_in
            end_in: float | None = min((hit.end_distance_in for hit in crossings
                                        if hit.end_distance_in is not None), default=None)
        elif over_plate:
            scope, chosen = UNDER_MEMBER, over_plate
            count = int(run_in // rules.along_member_pitch_in) + 1
            pitch_in = rules.along_member_pitch_in
            end_in = min((hit.end_distance_in for hit in over_plate
                          if hit.end_distance_in is not None), default=None)
        elif in_bay:
            scope, chosen = BETWEEN_MEMBERS, in_bay
            count = int(run_in // module_in) + 1
            pitch_in = module_in
            # The screw lands in blocking cut between two members, and that blocking is a
            # framed piece this model DOES carry (``resolve/floor_blocking.py``) only over
            # a floor. Its end distance is half the clear bay, which is what a screw driven
            # on the bay's centre line has to the block's cut end.
            end_in = (module_in - max(hit.width_in for hit in in_bay)) / 2.0
        else:
            above = [gap for gap in measured if gap > 0.0]
            nearest = (f"the nearest wood above it is {min(above):.4g} in up"
                       if above else "no wood stands over it at all")
            refusals.append(
                f"{wall.tag}: {nearest}, so nothing reads a gap inside "
                f"[-{rules.gap_search_tolerance_in:g}, {rules.maximum_gap_in:g}] in of its "
                "top plate. A slab or SIP soffit is the usual reason and it is not an SDPW "
                "joint: catlin's SL-M-DECK is what stands over W-B-CE and W-B-BA-E")
            continue
        joints.append(PartitionTopJoint(
            wall_tag=wall.tag, storey=wall.storey, scope=scope, count=count,
            pitch_in=pitch_in, gap_in=max(hit.gap_in for hit in chosen),
            plate_in=plate_in, plate_condition=condition, spacing_in=module_in,
            run_in=run_in,
            height_in=(framing_top_z_m(wall) - wall.z0_m) / M_PER_IN,
            supports=tuple(dict.fromkeys(hit.section for hit in chosen)),
            end_distance_in=end_in))
    return joints, refusals
