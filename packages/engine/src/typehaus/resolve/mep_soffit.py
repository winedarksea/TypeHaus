"""Does everything claiming this soffit actually fit inside it?

``JOIST_BAY`` routing has had a real validator since MEP Phase 3 — ``duct_bay_occupancy``
measures bay straddle, clear width, chord opening and bearing crossings. ``SOFFIT`` and
``CHASE`` had **nothing**: they were the flag that turned the joist check *off*
(``if crossed and routing not in (SOFFIT, CHASE)``), so declaring one stopped the checking
and nothing checked anything in return. Every clearance claim about a duct box in this
house therefore lived in a plan comment as hand arithmetic, unchecked and un-rerunnable.

This module is the other half. A run or a machine that names a modeled
:class:`~typehaus.model.floors.Soffit` is measured against that soffit's **derived** clear
section (→ ``framing/soffit.py::soffit_clear_section``): does it fit the cavity, and does
it fit *beside* whatever else is in the box at the same station, with a hanger gap?

``CHASE`` keeps its honest meaning — a framed shaft that is not modeled as a ``Soffit`` —
and stays a *declared* unchecked case rather than a silent one.

A query module, like ``mep_queries``: nothing here appends to the ``ResolvedModel``.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.soffit import SoffitClearSection, soffit_clear_section
from typehaus.resolve.model import ResolvedModel, ResolvedSoffit

#: Air between two things hung in the same box: strap hangers, a duct flange, a hand.
#: 2", the figure ``storeys/second.py`` widened SF-S-DUCT to 35" to buy — so the check
#: reproduces the decision it is replacing rather than quietly relaxing it.
HANGER_GAP_M = inch(2).meters


@dataclass(frozen=True)
class SoffitOccupant:
    """One thing inside a soffit, reduced to the three intervals that decide whether it fits.

    ``along`` is its extent down the box, ``across`` the band it takes up of the cavity's
    width, ``z`` its vertical band — all absolute, all project-frame, so two occupants can
    be compared directly instead of through a shared notion of "centre".

    ``vertical`` marks a riser — a leg whose travel is up, not along. Its ``z`` is its own
    two endpoints rather than a section depth about a mid-height, and it is *expected* to
    leave the box through the top or bottom, which is the whole point of a riser. The depth
    and z-band tests below are the ones that must not be applied to it; the width tests
    still are, because a riser too wide for the cavity is as real a fault as a branch too
    wide for it.
    """

    tag: str
    kind: str  # "duct" | "equipment" — the noun the message uses
    along: tuple[float, float]
    across: tuple[float, float]
    z: tuple[float, float]
    vertical: bool = False

    @property
    def across_width_m(self) -> float:
        return self.across[1] - self.across[0]

    @property
    def depth_m(self) -> float:
        return self.z[1] - self.z[0]


def _overlap(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Length the two intervals share. Zero for a touching pair — a trunk that starts at a
    machine's discharge collar meets it at a point, and a point is not a collision."""
    return min(a[1], b[1]) - max(a[0], b[0])


def _segment_band(a: tuple[float, float], b: tuple[float, float], width_m: float,
                  depth_m: float, riser_width_axis: str | None = None
                  ) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """The plan rectangle one duct segment sweeps, as ``((x0, x1), (y0, y1))``.

    Width lies perpendicular to travel, which is the whole reason this is per-segment: the
    same 10x8 branch is 10" wide in y where it runs east and 10" wide in x where it turns
    north. An oblique segment is not a case this house has, and squaring its bounding box
    would over-claim the cavity, so it returns None and the caller reports it rather than
    grading it on a made-up footprint.

    **A vertical leg needs both plan dimensions, and it used to get one.** For a horizontal
    segment ``depth_m`` is the section's *vertical* height, so the plan band only ever needs
    ``width_m``. Turn the duct up through an elbow and both dimensions become plan
    dimensions: the 10 stays where it was and the 6 rotates out of vertical into the
    direction the run was travelling. This returned ``width x width`` for that case, which
    is exactly right for a round duct — ``mep_ducts`` reports a diameter as *both* plan
    dimensions — and over-claims a rectangular riser by the difference, 10x10 for a 10x6.

    ``riser_width_axis`` names the plan axis the width lies along, inherited from the
    adjacent horizontal leg (see the caller). With no such leg to inherit from — a run that
    is *only* a riser, going nowhere — the section's orientation is genuinely unknown, so
    the fallback is a square of the larger dimension: over-claiming is the safe direction
    for a clearance test, and it is the behaviour this function already had.
    """
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    half = width_m / 2.0
    if dx <= 1e-9 and dy <= 1e-9:
        # A vertical leg: one plan point repeated at two elevations. Its plan footprint is
        # the section itself, and it competes for the box exactly as a horizontal leg does.
        if riser_width_axis == "x":
            return ((a[0] - half, a[0] + half),
                    (a[1] - depth_m / 2.0, a[1] + depth_m / 2.0))
        if riser_width_axis == "y":
            return ((a[0] - depth_m / 2.0, a[0] + depth_m / 2.0),
                    (a[1] - half, a[1] + half))
        square = max(width_m, depth_m) / 2.0
        return ((a[0] - square, a[0] + square), (a[1] - square, a[1] + square))
    if dy <= 1e-9:  # runs east-west
        return ((min(a[0], b[0]), max(a[0], b[0])), (a[1] - half, a[1] + half))
    if dx <= 1e-9:  # runs north-south
        return ((a[0] - half, a[0] + half), (min(a[1], b[1]), max(a[1], b[1])))
    return None


def _riser_width_axis(path: list[tuple[float, float]], index: int) -> str | None:
    """Which plan axis a riser's *width* lies along, inherited from its neighbours.

    An elbow does not twist the duct: the dimension that was perpendicular to travel stays
    where it is, and the one that was vertical rotates into the old direction of travel. So
    a riser off an east-west leg is ``width`` in y, and one off a north-south leg is
    ``width`` in x. The leg before is checked first, then the leg after; ``None`` means
    there is no horizontal leg to inherit from.
    """
    for other in (index - 1, index + 1):
        if other < 0 or other + 1 >= len(path):
            continue
        p, q = path[other], path[other + 1]
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        if dx > 1e-9 and dy <= 1e-9:      # neighbour runs east-west -> width lies in y
            return "y"
        if dy > 1e-9 and dx <= 1e-9:      # neighbour runs north-south -> width lies in x
            return "x"
    return None


def _project(band: tuple[tuple[float, float], tuple[float, float]],
             section: SoffitClearSection) -> tuple[tuple[float, float], tuple[float, float]]:
    """``(along, across)`` for a plan band, in the soffit's own axes."""
    x_band, y_band = band
    return (x_band, y_band) if section.long_axis == "x" else (y_band, x_band)


def duct_occupants(model: ResolvedModel, soffit: ResolvedSoffit,
                   section: SoffitClearSection) -> tuple[list[SoffitOccupant], list[str]]:
    """Every resolved duct naming this soffit, one occupant per segment inside it.

    Per segment rather than per run because a run turns: a branch that goes north down the
    box and then west out of it occupies two different bands, and its bounding box would
    claim a corner of the cavity it never touches.

    The ``along`` extent is clipped to the box; the ``across`` extent deliberately is not.
    A run leaving through the *end* of a soffit is ordinary (SF-S-SUITE abuts SF-S-DUCT and
    reads as one continuous box), so clipping along keeps that quiet; a run leaving through
    the *side* is a hole in a ladder rail, and that is worth saying out loud.
    """
    occupants: list[SoffitOccupant] = []
    problems: list[str] = []
    for duct in model.ducts:
        if duct.soffit_ref != soffit.tag:
            continue
        if not duct.z_m or len(duct.z_m) != len(duct.path):
            continue
        for index in range(len(duct.path) - 1):
            a, b = duct.path[index], duct.path[index + 1]
            vertical = (abs(b[0] - a[0]) <= 1e-9 and abs(b[1] - a[1]) <= 1e-9)
            band = _segment_band(a, b, duct.width_m, duct.depth_m,
                                 _riser_width_axis(duct.path, index) if vertical else None)
            if band is None:
                if abs(b[0] - a[0]) > 1e-9 and abs(b[1] - a[1]) > 1e-9:
                    problems.append(
                        f"duct {duct.tag} segment {index} runs obliquely inside soffit "
                        f"{soffit.tag}; its occupancy cannot be measured")
                continue
            along, across = _project(band, section)
            clipped = (max(along[0], section.along[0]), min(along[1], section.along[1]))
            if clipped[1] - clipped[0] <= 1e-9:
                continue  # this leg is outside the box entirely
            # A horizontal leg's z-band is its section about its own mid-height. A RISER's
            # is its two endpoints: it is travelling vertically, and `depth_m` describes a
            # plan dimension for it, not a vertical one. Banding a riser as `z_mid +/-
            # depth/2` put a 19" rise into a 6" band halfway up itself — halfway through the
            # deck for DU-S-HP-SOUTH-RISE, and nowhere near either end it actually reaches.
            z0, z1 = duct.z_m[index], duct.z_m[index + 1]
            if vertical:
                z_band = (min(z0, z1), max(z0, z1))
            else:
                z_mid = (z0 + z1) / 2.0
                z_band = (z_mid - duct.depth_m / 2.0, z_mid + duct.depth_m / 2.0)
            occupants.append(SoffitOccupant(
                tag=duct.tag, kind="duct", along=clipped, across=across,
                z=z_band, vertical=vertical))
    return occupants, problems


def _plan_ring_bbox(ring) -> tuple[tuple[float, float], tuple[float, float]]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (min(xs), max(xs)), (min(ys), max(ys))


def equipment_occupants(model: ResolvedModel, soffit: ResolvedSoffit,
                        section: SoffitClearSection) -> list[SoffitOccupant]:
    """Every placeable whose authored ``soffit_ref`` names this soffit.

    The footprint comes from the resolved canvas object, so a rotated case is measured
    where it actually lands; the height comes from its ``EquipmentType``. A type with no
    stated height contributes no vertical band — it is measured for width and left alone
    for depth, which is honest about what the catalog says rather than assuming a case
    fills the box.
    """
    heights = {t.tag: getattr(t, "height", None) for t in model.plan.library.equipment_types}
    refs = {el.tag: getattr(el, "soffit_ref", None)
            for el in model.plan.all_elements() if getattr(el, "soffit_ref", None)}
    occupants: list[SoffitOccupant] = []
    for obj in model.canvas_objects:
        if refs.get(obj.tag) != soffit.tag or not obj.footprint:
            continue
        band = _plan_ring_bbox(obj.footprint)
        along, across = _project(band, section)
        height = heights.get(obj.type_ref) if obj.type_ref else None
        height_m = height.meters if height is not None else 0.0
        occupants.append(SoffitOccupant(
            tag=obj.tag, kind="equipment", along=along, across=across,
            z=(obj.z_m, obj.z_m + height_m)))
    return occupants


def connected(model: ResolvedModel, machine: SoffitOccupant,
              duct_tag: str) -> bool:
    """Whether a duct runs *into* a machine rather than competing with it for the box.

    Public — with ``segment_meets_box`` below — because ``checks/mep/duct_connectivity.py``
    asks the same geometric question in the other direction. Here it *suppresses* a soffit
    clash ("these two overlap because they are plumbed together"); there it *requires* the
    connection ("this duct end lands on nothing"). One predicate, so the two can never
    disagree about what "connected" means.

    A return plenum stub lands in the air handler's bottom opening and a 2 kW duct heater
    sits in the supply plenum: both overlap the case they belong to, and both would be
    reported as a clash by any rule that only knows about rectangles. The test is
    geometric and needs no new authored field — if the duct's centreline enters the
    machine's footprint, the two are plumbed together.
    """
    duct = next((d for d in model.ducts if d.tag == duct_tag), None)
    if duct is None:
        return False
    obj = next((o for o in model.canvas_objects if o.tag == machine.tag), None)
    if obj is None or not obj.footprint:
        return False
    box = _plan_ring_bbox(obj.footprint)
    return any(segment_meets_box(a, b, box)
               for a, b in zip(duct.path[:-1], duct.path[1:], strict=False))


def segment_meets_box(a: tuple[float, float], b: tuple[float, float],
                      box: tuple[tuple[float, float], tuple[float, float]]) -> bool:
    """Whether the segment ``a``->``b`` enters the axis-aligned box. Liang-Barsky.

    Endpoints alone are not enough and the midpoint is not either: DU-S-HP-SUP is one
    281"-long segment from the air handler's discharge to the north end of the hall, and the
    duct heater it passes through sits 10" along it. A run *through* a machine is as plumbed
    as a run *into* one.
    """
    (x0, x1), (y0, y1) = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for delta, start, low, high in ((dx, a[0], x0, x1), (dy, a[1], y0, y1)):
        if abs(delta) < 1e-12:
            if start < low - 1e-9 or start > high + 1e-9:
                return False
            continue
        near, far = (low - start) / delta, (high - start) / delta
        if near > far:
            near, far = far, near
        t0, t1 = max(t0, near), min(t1, far)
        if t0 > t1:
            return False
    return True


def soffit_occupancy(model: ResolvedModel, soffit: ResolvedSoffit
                     ) -> tuple[list[str], SoffitClearSection | None]:
    """``(conflicts, section)`` for one soffit. An empty list with a section is a pass.

    ``section`` is None when the soffit has no framing to derive a cavity from, which the
    caller reports as UNKNOWN — an unframed box has no clear width, and inventing one from
    the finished dimension would credit 4 1/4" of gypsum and lumber as if it were air.
    """
    section = soffit_clear_section(soffit)
    if section is None:
        return [], None
    ducts, conflicts = duct_occupants(model, soffit, section)
    occupants = ducts + equipment_occupants(model, soffit, section)
    for item in occupants:
        if item.across_width_m > section.width_m + 1e-9:
            conflicts.append(
                f"{item.kind} {item.tag} is {item.across_width_m / M_PER_IN:.2f}\" across, "
                f"more than soffit {soffit.tag}'s {section.width_m / M_PER_IN:.2f}\" clear "
                "width")
        elif (item.across[0] < section.across[0] - 1e-9
              or item.across[1] > section.across[1] + 1e-9):
            conflicts.append(
                f"{item.kind} {item.tag} sits at {item.across[0]:.3f}..{item.across[1]:.3f}m "
                f"across soffit {soffit.tag}, outside its "
                f"{section.across[0]:.3f}..{section.across[1]:.3f}m clear cavity")
        if item.vertical:
            # A RISER IS NOT A DEPTH FAULT. It travels vertically, so it occupies the full
            # drop by construction and leaves through the top or the bottom on purpose —
            # that is what a riser is for. Grading it against the clear drop would report
            # every riser in the house, and grading its z-band against the cavity would
            # report every one that actually goes somewhere. What IS worth saying is a riser
            # that never reaches the cavity at all: it names this soffit and misses it.
            if item.z[1] < section.z[0] - 1e-9 or item.z[0] > section.z[1] + 1e-9:
                conflicts.append(
                    f"{item.kind} {item.tag} rises {item.z[0]:.3f}..{item.z[1]:.3f}m but "
                    f"soffit {soffit.tag}'s cavity is {section.z[0]:.3f}..{section.z[1]:.3f}m "
                    "— the riser names this soffit and never enters it")
        elif item.depth_m > section.drop_m + 1e-9:
            conflicts.append(
                f"{item.kind} {item.tag} is {item.depth_m / M_PER_IN:.2f}\" deep, more than "
                f"soffit {soffit.tag}'s {section.drop_m / M_PER_IN:.2f}\" clear drop")
        elif item.depth_m > 0 and (item.z[0] < section.z[0] - 1e-9
                                   or item.z[1] > section.z[1] + 1e-9):
            conflicts.append(
                f"{item.kind} {item.tag} spans {item.z[0]:.3f}..{item.z[1]:.3f}m vertically "
                f"in soffit {soffit.tag}, outside its {section.z[0]:.3f}..{section.z[1]:.3f}m "
                "clear cavity")
    for i, first in enumerate(occupants):
        for second in occupants[i + 1:]:
            if first.tag == second.tag:
                continue  # two legs of one run: it turns a corner, it does not meet itself
            if _overlap(first.along, second.along) <= 1e-9:
                continue
            if _pair_is_plumbed(model, first, second):
                continue
            gap = max(second.across[0] - first.across[1], first.across[0] - second.across[1])
            if gap < HANGER_GAP_M - 1e-9:
                conflicts.append(
                    f"{first.kind} {first.tag} and {second.kind} {second.tag} share "
                    f"{_overlap(first.along, second.along) / M_PER_IN:.1f}\" of soffit "
                    f"{soffit.tag} with {gap / M_PER_IN:.2f}\" between them — "
                    f"{HANGER_GAP_M / M_PER_IN:.0f}\" is needed for hangers and flanges")
    return conflicts, section


def _pair_is_plumbed(model: ResolvedModel, first: SoffitOccupant,
                     second: SoffitOccupant) -> bool:
    """Whether the pair is one connected assembly rather than two things sharing a box."""
    if first.kind == "equipment" and second.kind == "duct":
        return connected(model, first, second.tag)
    if second.kind == "equipment" and first.kind == "duct":
        return connected(model, second, first.tag)
    return False
