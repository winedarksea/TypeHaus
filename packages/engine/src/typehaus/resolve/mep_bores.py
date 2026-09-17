"""What a trade may cut out of a framing member, and what it may not.

IRC R502.8 (joists) and R602.6 / R602.6.1 (studs and plates) are the two sections this
engine's jurisdiction profile has carried on its **not-covered** list since the profile was
written. That was honest — nothing graded them — and it is also the largest hole a routing
proposal can fall into: a search that finds a lane through a wall has proposed boring every
stud on the way, and until now nothing at all said whether the holes were legal.

The rules are stated here as **data plus predicates**, in ``resolve`` rather than in
``checks``, for the same reason ``mep_envelopes`` is: a router must aim at the same rule the
check grades it by, and the leaf rule forbids the router reaching into ``checks``.

**Three things this module refuses to do.**

* **It never invents a rule for an engineered member.** An LVL, an I-joist, an open-web
  truss and an LSL rim are cut to the *fabricator's* chart and no code table describes them.
  A verdict for one of those is ``None`` — UNKNOWN — and a consumer prints that rather than
  applying R502.8 to a product R502.8 has never governed. A generic "open webs are borable"
  is not evidence that THIS hole is.
* **It never proposes a repair.** R602.6.1's 16 ga tie is stated as the *condition under
  which a cut plate is acceptable*, not as something an engine adds to a model. Introducing
  a strap to make a route legal is a structural redesign, and those belong to a person.
* **It grades what is authored as well as what is proposed.** A notch somebody drew is the
  same question as a notch somebody is about to propose, and a module that only answered the
  second would be a router's private opinion rather than a rule about the house.

``houses/catlin/notes/framing_bore_limits.md`` is the hand-worked oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import FramedMember, ResolvedWall

#: R502.8.1: a bored hole in a solid-sawn joist keeps 2" clear of top and bottom, and is no
#: nearer than 2" to any other hole or notch.
JOIST_EDGE_CLEAR_IN = 2.0
JOIST_HOLE_SPACING_IN = 2.0
#: R502.8.1: hole <= D/3; notch <= D/6 and not in the middle third of the span; an END notch
#: (within D of the bearing) <= D/4; a notch no longer than D/3.
JOIST_HOLE_FRACTION = 1.0 / 3.0
JOIST_NOTCH_FRACTION = 1.0 / 6.0
JOIST_END_NOTCH_FRACTION = 1.0 / 4.0
JOIST_NOTCH_LENGTH_FRACTION = 1.0 / 3.0

#: R602.6: fractions of the stud's DEPTH (its 5 1/2" dimension on a 2x6 wall).
STUD_NOTCH_BEARING = 0.25
STUD_BORE_BEARING = 0.40
STUD_NOTCH_NONBEARING = 0.40
STUD_BORE_NONBEARING = 0.60
#: R602.6: a doubled stud may be bored to 60%, **and no more than two successive** doubled
#: studs may be so bored. The count is the caller's to track; this module states the limit.
STUD_BORE_DOUBLED = 0.60
STUD_BORE_DOUBLED_MAX_SUCCESSIVE = 2
#: R602.6: the edge of a bore or notch stays 5/8" from the edge of the stud.
STUD_EDGE_CLEAR_IN = 0.625

#: R602.6.1: a top plate cut or notched more than 50% of its width needs a galvanized metal
#: tie **16 ga (0.054") x 1 1/2"** across and 6" past the opening each way, fastened with
#: eight 10d nails each side.
PLATE_CUT_FRACTION = 0.50
PLATE_TIE_GAUGE_IN = 0.054
PLATE_TIE_WIDTH_IN = 1.5
PLATE_TIE_LAP_IN = 6.0
PLATE_TIE_NAILS_EACH_SIDE = 8

#: Section shapes no code table governs. A verdict about one of these is UNKNOWN, always.
ENGINEERED_SHAPES = frozenset({"i_joist", "floor_truss", "roof_truss"})

#: Products whose section resolves as a plain rectangle and which R502.8 still does not
#: govern. ``cross_section`` reads ``1.75x11.875 LVL`` as a ``rect``, because for framing
#: geometry it IS one — but a laminated veneer member is cut to Weyerhaeuser's chart and
#: applying a solid-sawn table to it is exactly the mistake this module refuses to make.
#: Matched on the profile string, which is where the product name lives.
ENGINEERED_MARKERS = ("lvl", "lsl", "psl", "glulam", "i-joist", "truss", "rim")


@dataclass(frozen=True)
class BoreVerdict:
    """One cut, graded. ``ok is None`` means **no published rule reaches this member**.

    ``limit_in`` is the number the rule allows and ``actual_in`` what was asked for, so a
    consumer can print the margin rather than the verdict alone — "0.44" over" is actionable
    and "FAIL" is not.
    """

    ok: bool | None
    kind: str  # "bore" | "notch" | "plate_cut"
    actual_in: float
    limit_in: float | None
    basis: str
    #: What a person has to do for an otherwise-illegal cut to become legal. Stated, never
    #: applied: introducing a strap to make a route legal is a structural redesign.
    remedy: str | None = None

    @property
    def unknown(self) -> bool:
        return self.ok is None


def _engineered(section: Any, profile: str, what: str) -> BoreVerdict | None:
    if section is None:
        return BoreVerdict(None, what, 0.0, None,
                           f"{profile!r} resolves no cross-section, so nothing can be "
                           "measured against it")
    text = profile.lower()
    if (section.shape in ENGINEERED_SHAPES
            or any(marker in text for marker in ENGINEERED_MARKERS)):
        return BoreVerdict(
            None, what, 0.0, None,
            f"{profile} is an engineered member: it is cut to the fabricator's chart and "
            "no IRC table describes it. This engine does not hold that chart, and a "
            "generic 'open webs are borable' is not evidence that THIS hole is",
            remedy="get the hole's diameter and its allowable zone along the span from the "
                   "manufacturer's literature and author it")
    return None


def joist_bore(profile: str, diameter_in: float, *, edge_clear_in: float | None = None,
               nearest_cut_in: float | None = None) -> BoreVerdict:
    """IRC R502.8.1 on a bored hole in a solid-sawn joist.

    Three separate limits and the report names which one bit. A check that collapsed them
    into one boolean would say "illegal" about a 1" hole that is merely too close to its
    neighbour, which is a different thing to fix.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "bore")
    if engineered is not None:
        return engineered
    depth_in = section.depth_m / M_PER_IN
    limit = depth_in * JOIST_HOLE_FRACTION
    if diameter_in > limit + 1e-9:
        return BoreVerdict(False, "bore", diameter_in, limit,
                           f"IRC R502.8.1: a bored hole in a {profile} may not exceed D/3 = "
                           f'{limit:.2f}" and this is {diameter_in:.2f}"')
    if edge_clear_in is not None and edge_clear_in < JOIST_EDGE_CLEAR_IN - 1e-9:
        return BoreVerdict(False, "bore", edge_clear_in, JOIST_EDGE_CLEAR_IN,
                           f'IRC R502.8.1: a hole stays 2" clear of the top and bottom of a '
                           f'{profile} and this leaves {edge_clear_in:.2f}"')
    if nearest_cut_in is not None and nearest_cut_in < JOIST_HOLE_SPACING_IN - 1e-9:
        return BoreVerdict(False, "bore", nearest_cut_in, JOIST_HOLE_SPACING_IN,
                           f'IRC R502.8.1: a hole stays 2" from any other hole or notch and '
                           f'this is {nearest_cut_in:.2f}" from one')
    return BoreVerdict(True, "bore", diameter_in, limit,
                       f'IRC R502.8.1: {diameter_in:.2f}" in a {profile} against the D/3 = '
                       f'{limit:.2f}" limit, 2" clear of both edges')


def joist_notch(profile: str, depth_of_notch_in: float, *, length_in: float | None = None,
                at_end: bool = False, in_middle_third: bool = False) -> BoreVerdict:
    """IRC R502.8.1 on a notch. The middle third is the one a table cannot express."""
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "notch")
    if engineered is not None:
        return engineered
    depth_in = section.depth_m / M_PER_IN
    if in_middle_third:
        return BoreVerdict(False, "notch", depth_of_notch_in, 0.0,
                           f"IRC R502.8.1: no notch at all in the middle third of a "
                           f"{profile}'s span — that is where the bending moment is")
    limit = depth_in * (JOIST_END_NOTCH_FRACTION if at_end else JOIST_NOTCH_FRACTION)
    where = "at the bearing" if at_end else "in the outer thirds"
    if depth_of_notch_in > limit + 1e-9:
        return BoreVerdict(False, "notch", depth_of_notch_in, limit,
                           f"IRC R502.8.1: a notch {where} in a {profile} may not exceed "
                           f'{"D/4" if at_end else "D/6"} = {limit:.2f}" and this is '
                           f'{depth_of_notch_in:.2f}"')
    length_limit = depth_in * JOIST_NOTCH_LENGTH_FRACTION
    if length_in is not None and length_in > length_limit + 1e-9:
        return BoreVerdict(False, "notch", length_in, length_limit,
                           f"IRC R502.8.1: a notch in a {profile} may be no longer than "
                           f'D/3 = {length_limit:.2f}" and this is {length_in:.2f}"')
    return BoreVerdict(True, "notch", depth_of_notch_in, limit,
                       f'IRC R502.8.1: {depth_of_notch_in:.2f}" {where} in a {profile}, '
                       f'against the {limit:.2f}" limit')


def stud_bore(profile: str, diameter_in: float, *, bearing: bool = True,
              doubled: bool = False) -> BoreVerdict:
    """IRC R602.6 on a bored hole through a stud.

    ``bearing`` is the wall's own property and the caller must know it: the difference
    between 40% and 60% of a 2x6 is nearly an inch of pipe, which is the whole question for
    a 2" branch.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "bore")
    if engineered is not None:
        return engineered
    # A stud's DEPTH is the wall's thickness dimension — the 5 1/2" of a 2x6 — and that is
    # what R602.6's percentages are of. `cross_section` puts the larger face in depth_m.
    depth_in = max(section.depth_m, section.width_m) / M_PER_IN
    if diameter_in >= depth_in - 1e-9:
        # **Wider than the stud: this is not a bore at all.** A 6" duct does not go
        # THROUGH a 2x6, it goes through a framed opening with a header over it, and
        # R602.6 has nothing to say about that — the section is about holes drilled in
        # members that stay whole. Reporting "a 6" bore exceeds 60% of 5 1/2"" is
        # arithmetic about a hole nobody would drill. Nothing in this engine grades a
        # header over a duct penetration, so the honest answer is UNKNOWN and the reason.
        return BoreVerdict(
            None, "bore", diameter_in, None,
            f'a {diameter_in:.2f}" penetration is wider than the {depth_in:.2f}" depth of '
            f"a {profile}, so it is a framed opening with a header over it and not a bore. "
            "IRC R602.6 governs holes drilled in members that stay whole and does not "
            "reach this; nothing in this engine grades the header either",
            remedy="draw the opening and its header, or take the run through a floor bay "
                   "instead of across the wall")
    fraction = (STUD_BORE_DOUBLED if doubled
                else STUD_BORE_BEARING if bearing else STUD_BORE_NONBEARING)
    limit = depth_in * fraction
    edge = (depth_in - diameter_in) / 2.0
    label = ("a doubled stud" if doubled
             else "a bearing-wall stud" if bearing else "a non-bearing stud")
    extra = (f"; no more than {STUD_BORE_DOUBLED_MAX_SUCCESSIVE} successive doubled studs "
             "may be bored to this" if doubled else "")
    if diameter_in > limit + 1e-9:
        return BoreVerdict(False, "bore", diameter_in, limit,
                           f"IRC R602.6: a bore in {label} ({profile}) may not exceed "
                           f'{fraction:.0%} of {depth_in:.2f}" = {limit:.2f}" and this is '
                           f'{diameter_in:.2f}"{extra}',
                           remedy=None if bearing else "none needed on a non-bearing wall "
                                                       "beyond moving the run to a clear bay")
    if edge < STUD_EDGE_CLEAR_IN - 1e-9:
        return BoreVerdict(False, "bore", edge, STUD_EDGE_CLEAR_IN,
                           f'IRC R602.6: 5/8" of stud must remain either side of a bore in '
                           f'a {profile} and this leaves {edge:.3f}"')
    return BoreVerdict(True, "bore", diameter_in, limit,
                       f'IRC R602.6: {diameter_in:.2f}" through {label} ({profile}), '
                       f'against the {fraction:.0%} = {limit:.2f}" limit, {edge:.3f}" of '
                       f"stud either side{extra}")


def stud_notch(profile: str, depth_of_notch_in: float, *,
               bearing: bool = True) -> BoreVerdict:
    """IRC R602.6 on a notch cut into the face of a stud."""
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "notch")
    if engineered is not None:
        return engineered
    depth_in = max(section.depth_m, section.width_m) / M_PER_IN
    fraction = STUD_NOTCH_BEARING if bearing else STUD_NOTCH_NONBEARING
    limit = depth_in * fraction
    label = "a bearing-wall stud" if bearing else "a non-bearing stud"
    ok = depth_of_notch_in <= limit + 1e-9
    return BoreVerdict(
        ok, "notch", depth_of_notch_in, limit,
        f"IRC R602.6: a notch in {label} ({profile}) may not exceed {fraction:.0%} of "
        f'{depth_in:.2f}" = {limit:.2f}" and this is {depth_of_notch_in:.2f}"'
        if not ok else
        f'IRC R602.6: {depth_of_notch_in:.2f}" notched from {label} ({profile}), against '
        f'the {fraction:.0%} = {limit:.2f}" limit',
        remedy=None if ok else "bore rather than notch, or take the run to a clear bay")


def top_plate_cut(profile: str, cut_in: float) -> BoreVerdict:
    """IRC R602.6.1 on a cut or notched top plate.

    **Over 50% is not illegal, it is conditional**, and that distinction is the whole value
    of this function: a cut plate with the tie on it is built every day. The condition is
    reported as a ``remedy`` the person applies; nothing here adds a strap to a model.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "plate_cut")
    if engineered is not None:
        return engineered
    width_in = max(section.depth_m, section.width_m) / M_PER_IN
    limit = width_in * PLATE_CUT_FRACTION
    if cut_in <= limit + 1e-9:
        return BoreVerdict(True, "plate_cut", cut_in, limit,
                           f'IRC R602.6.1: {cut_in:.2f}" out of a {profile} top plate, '
                           f'under the {limit:.2f}" (50%) line that triggers a tie')
    return BoreVerdict(
        True, "plate_cut", cut_in, limit,
        f'IRC R602.6.1: {cut_in:.2f}" out of a {profile} top plate is more than 50% of its '
        f'{width_in:.2f}" width, which is permitted WITH a tie and not without one',
        remedy=(f"fasten a galvanized metal tie {PLATE_TIE_GAUGE_IN:.3f}\" (16 ga) x "
                f"{PLATE_TIE_WIDTH_IN:g}\" across the cut, lapping {PLATE_TIE_LAP_IN:g}\" "
                f"past the opening each way, with {PLATE_TIE_NAILS_EACH_SIDE} 10d nails "
                "each side"))


@dataclass(frozen=True)
class MemberCut:
    """One place a run's leg meets one wall member, and what it would have to cut.

    ``through`` is the dimension the run has to get through — a stud's depth for a bore
    across the wall, a plate's thickness for a riser — and ``diameter_in`` is the hole the
    run's own outside needs.
    """

    member_key: str
    category: str  # "stud" | "plate" | "king" | "jack" | "cripple" | "sill"
    profile: str
    station: tuple[float, float]
    z_m: float
    diameter_in: float


def leg_crossings(wall: ResolvedWall, a: tuple[float, float], b: tuple[float, float],
                  za: float, zb: float, radius_m: float) -> list[MemberCut]:
    """Every stud and plate of ``wall`` this one leg of a run would have to cut.

    **The actual stud positions, never "the wall is empty".** A staggered wall is the case
    this exists for: its studs alternate between two rows, so a run down the middle of a
    2x6 plate misses half of them and bores the other half, and a rule applied to "the
    wall" cannot express that. ``ResolvedWall.members`` already carries each stud's own
    plan point and its ``orient``, so the question is answered against the framing that
    resolved rather than against a spacing.

    A member is crossed when the run's inflated plan line meets the member's own plan
    rectangle AND the run's elevation there is inside the member's z band. Both, for the
    same reason ``mep_crossings.leg_crossings`` needs both: a run passing over a wall's
    plate is not boring it.
    """
    from shapely.geometry import LineString, Point

    from typehaus.resolve.framing.profiles import cross_section

    swept = (Point(a) if a == b else LineString([a, b])).buffer(radius_m)
    out: list[MemberCut] = []
    for member in wall.members:
        if member.category not in ("stud", "king", "jack", "cripple", "plate", "sill"):
            continue
        shape = _member_plan_shape(member, cross_section(member.profile))
        if shape is None or not swept.intersects(shape):
            continue
        centre = shape.centroid
        z = _z_at(a, b, za, zb, (centre.x, centre.y))
        top = member.z1_m if member.z1_m is not None else wall.z1_m
        if not (member.z0_m - radius_m <= z <= top + radius_m):
            continue
        out.append(MemberCut(member_key=member.child_key, category=member.category,
                             profile=member.profile, station=(centre.x, centre.y),
                             z_m=z, diameter_in=2.0 * radius_m / M_PER_IN))
    return out


def _member_plan_shape(member: FramedMember, section: Any) -> Any:
    """A framing member's own plan rectangle, from its axis and its section.

    A stud is a vertical: ``p0 == p1``, and its ``orient`` is the wall direction, so the
    rectangle is its 1 1/2" thickness ALONG the wall by its 5 1/2" depth ACROSS it. A plate
    is horizontal and its axis is the wall run, so the rectangle is its length by its width.
    """
    from shapely.geometry import LineString, Polygon

    if section is None:
        return None
    if member.p0 == member.p1:
        orient = member.orient or (1.0, 0.0)
        norm = (orient[0] ** 2 + orient[1] ** 2) ** 0.5 or 1.0
        ux, uy = orient[0] / norm, orient[1] / norm
        nx, ny = -uy, ux
        # `width_m` is the member's 1 1/2" face and `depth_m` its 5 1/2" — the convention
        # `cross_section` documents — so along the wall is the width and across is the depth.
        half_along, half_across = section.width_m / 2.0, section.depth_m / 2.0
        cx, cy = member.p0
        corners = [(cx + ux * sa * half_along + nx * sc * half_across,
                    cy + uy * sa * half_along + ny * sc * half_across)
                   for sa, sc in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        return Polygon(corners)
    return LineString([member.p0, member.p1]).buffer(
        max(section.width_m, section.depth_m) / 2.0, cap_style=2)


def _z_at(a: tuple[float, float], b: tuple[float, float], za: float, zb: float,
          point: tuple[float, float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = dx * dx + dy * dy
    if span <= 0:
        return (za + zb) / 2.0
    t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / span))
    return za + t * (zb - za)
