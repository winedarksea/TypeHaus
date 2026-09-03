"""A wood post bearing on FRAMING — ``post_bearing/<Post tag>``.

Every other bearing rule in this engine is about a post landing on a pour.
``engineering/pier_basis.py`` grades a cast pier and says so at its own scope: "a post on a
floor or on a WOOD post is somebody else's rule". Until 2026-09-03 there was no somebody
else. ``structural.landing_post_bearing`` is scoped to resolver-generated stair landing
posts (``checks/structural/stairs.py``), so an authored ``Post`` standing on a
``FloorSystem`` was graded by nothing at all, at 0 FAIL.

**What the joint actually is.** catlin's two centre balcony pillars, ``PT-SG-BR2`` and
``PT-SG-BF2``, are 6x6s standing on the porch deck. Everything they carry crosses the grain
twice on its way down: once where the post's end grain lands on the flat of the joist ply
pack, and once where those joists land on the beam. Both are compression perpendicular to
grain, NDS §3.10.2, and both are computed here.

**Two things that make this different from a hand check done casually.**

* **Wet service.** These joists stand outdoors under an open deck, so NDS Table 4.3.1's
  ``C_M`` of 0.67 on Fc-perp applies. The house's own comments graded this joint against a
  DRY 425 psi while ``glulam_beam.py`` was applying wet service to the glulam bearing on
  the same post at the same instant. 425 psi and 285 psi are different answers to the same
  question, and one of them was wrong.
* **No load duration factor.** §3.10.2 takes none. Fc-perp is a deformation limit, not a
  strength one, and C_D does not apply to it — which is the single most common way a hand
  check of this joint comes out 15% optimistic.

**Oracle.** ``houses/catlin/notes/centre_pillar_bearing.md``, hand-worked term by term in a
separate pass; ``tests/test_post_bearing.py`` reproduces it.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys

KIND = "post_bearing"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = "AWC NDS 2018 §3.10 (compression perpendicular to grain), IRC R507.1 loads"

#: AWC NDS 2018 Supplement Table 4A, Fc-perp for spruce-pine-fir — the softest of the
#: species a deck frame around here is actually built from, and therefore the safe one to
#: grade against when the model records a nominal section rather than a species. Southern
#: pine publishes 565 psi and Douglas fir-larch 625; a frame that passes at 425 passes at
#: either. If a house ever records species on the member, read it here instead of assuming.
SAWN_FC_PERP_PSI = 425.0

#: AWC NDS 2018 Table 4.3.1 — the wet-service factor on Fc-perp for sawn lumber. 0.67, not
#: the 0.53 ``glulam_beam.py`` applies: glulam and sawn lumber have different tables, and
#: borrowing one member's factor for the other is a real error in both directions.
WET_FC_PERP = 0.67

#: AWC NDS 2018 §3.10.4 — the bearing area factor, which credits the fibres just outside a
#: short bearing for carrying some of the load. It applies only to a bearing at least
#: ``END_DISTANCE_IN`` from the member's end and shorter than ``CB_MAX_LENGTH_IN``; a
#: bearing AT the end gets nothing, because there are no fibres beyond it to help.
CB_MAX_LENGTH_IN = 6.0
END_DISTANCE_IN = 3.0

_M_PER_FT = 0.3048
_M_PER_IN = 0.0254
_TOL_M = 1e-6


def _bearing_area_factor(length_in: float, at_member_end: bool) -> float:
    """``C_b`` per NDS §3.10.4: ``(l_b + 0.375) / l_b``, and 1.0 at a member end."""
    if at_member_end or length_in <= 0.0 or length_in >= CB_MAX_LENGTH_IN:
        return 1.0
    return (length_in + 0.375) / length_in


def _floor_systems(ctx: EngineeringContext) -> dict[str, Any]:
    from typehaus.model.floors import FloorSystem

    return {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, FloorSystem)}


def _posts_on_framing(ctx: EngineeringContext) -> list[tuple[Any, Any]]:
    """``(post, the FloorSystem it stands on)`` for every authored post bearing on framing.

    Exactly the population ``pier_basis.cast_piers`` hands off: a post whose ``supported_by``
    names a floor rather than a footing, a pad or a foundation wall. The two modules must not
    both claim one post, and this predicate is the seam.
    """
    from typehaus.model.structure import Post

    floors = _floor_systems(ctx)
    out: list[tuple[Any, Any]] = []
    for element in sorted((e for e in ctx.plan.all_elements() if isinstance(e, Post)),
                          key=lambda e: e.tag):
        if element.within_wall or not element.supported_by:
            continue
        deck = floors.get(element.supported_by)
        if deck is not None:
            out.append((element, deck))
    return out


def _section_in(size: str | None) -> tuple[float, float] | None:
    """``(width in, depth in)`` of a nominal or true section, or ``None``."""
    from typehaus.resolve.framing.profiles import cross_section

    try:
        profile = cross_section(size or "")
    except (KeyError, ValueError):
        return None
    return (float(profile.width_m) / _M_PER_IN, float(profile.depth_m) / _M_PER_IN)


def _node_xy(ctx: EngineeringContext) -> dict[str, tuple[float, float]]:
    return {e.tag: e.position.xy_m for e in ctx.plan.all_elements()
            if e.element_kind == "Node"}


def _beam_reaction_lb(ctx: EngineeringContext, beam: Any, post: Any,
                      load_plf: float) -> float | None:
    """What ``beam`` delivers to ``post``, in pounds, under a uniform ``load_plf``.

    Two supports is the case every deck beam here is, and it is solved exactly rather than
    approximated: an overhang past a support does not merely add its own weight to that
    support, it *levers load off* the far one, and on ``BM-SG-BLC`` — 20" over the rear
    pillar and 15" past the front one — the difference between the exact reactions and an
    even split is 300 lb, about 13%. Guessing it in the safe direction at both ends would
    add 600 lb of load to a frame that does not have it.

    Three or more supports is statically indeterminate and this engine does not solve one, so
    it falls back to the tributary length along the beam — half the distance to each
    neighbouring support, running out to the beam's own ends.
    """
    nodes = _node_xy(ctx)
    p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
    if p0 is None or p1 is None:
        return None
    length_m = math.dist(p0, p1)
    if length_m <= _TOL_M:
        return None
    ux = ((p1[0] - p0[0]) / length_m, (p1[1] - p0[1]) / length_m)

    def station(point: tuple[float, float]) -> float:
        return (point[0] - p0[0]) * ux[0] + (point[1] - p0[1]) * ux[1]

    supports: list[tuple[float, str]] = []
    for ref in beam.bearing_refs or ():
        element = ctx.plan.by_tag(ref)
        position = getattr(element, "position", None)
        if position is None:
            return None  # a wall bearing — no station to place it at, so decline
        supports.append((station(position.xy_m) / _M_PER_FT, ref))
    supports.sort()
    if not any(ref == post.tag for _s, ref in supports):
        return None
    length_ft = length_m / _M_PER_FT
    total_lb = load_plf * length_ft

    if len(supports) == 2:
        (s0, tag0), (s1, _tag1) = supports
        if abs(s1 - s0) <= 1e-9:
            return None
        near = load_plf * length_ft * (s1 - length_ft / 2.0) / (s1 - s0)
        return near if tag0 == post.tag else total_lb - near
    if len(supports) == 1:
        return total_lb
    # Indeterminate: tributary length along the beam, ends inclusive.
    stations = [s for s, _ref in supports]
    out = 0.0
    for index, (s, ref) in enumerate(supports):
        lo = 0.0 if index == 0 else (stations[index - 1] + s) / 2.0
        hi = length_ft if index == len(supports) - 1 else (stations[index + 1] + s) / 2.0
        if ref == post.tag:
            out += load_plf * max(hi - lo, 0.0)
    return out


def _reaction_lb(ctx: EngineeringContext, post: Any) -> tuple[float | None, tuple[str, ...]]:
    """The total load this post carries, and the beams it came from.

    Every beam that names the post in ``bearing_refs`` and belongs to a deck, under that
    deck's own ``50 psf x joist span`` line load — the same strip ``glulam_beam.py`` puts
    under its own record, so the post's demand and the beam's are the same number seen from
    two ends. A beam that belongs to no deck is a load this module cannot size, and it makes
    the record INCOMPLETE rather than quietly under-reporting.
    """
    from typehaus.engineering.glulam_beam import DECK_TOTAL_LOAD_PSF, _joist_span_ft
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam

    carried: list[tuple[Any, float]] = []
    for deck in sorted((e for e in ctx.plan.all_elements()
                        if isinstance(e, FloorSystem) and e.service == "deck"),
                       key=lambda d: d.tag):
        strip_ft = _joist_span_ft(ctx, deck)
        if strip_ft is None:
            continue
        for ref in sorted(deck.joists.bearing_refs or ()):
            beam = ctx.plan.by_tag(ref)
            if isinstance(beam, Beam) and post.tag in (beam.bearing_refs or ()):
                carried.append((beam, DECK_TOTAL_LOAD_PSF * strip_ft))
    if not carried:
        return None, ()
    total = 0.0
    tags: list[str] = []
    for beam, load_plf in carried:
        reaction = _beam_reaction_lb(ctx, beam, post, load_plf)
        if reaction is None:
            return None, tuple(sorted(tags))
        total += reaction
        tags.append(beam.tag)
    return total, tuple(sorted(tags))


def _ply_width_in(ctx: EngineeringContext, deck: Any, post: Any) -> tuple[float, int]:
    """``(width of joist stock under the post's footprint, member count)``, in inches.

    Read off the RESOLVED members, not off ``JoistReinforcement.plies``. The resolver lays
    the extra plies to ONE side of the authored line (``resolve/floors.py``: the cluster
    straddles the load, and a load exactly on the line resolves ``+1`` deterministically), so
    a 3-ply cluster under a 5-1/2" post does not necessarily give the post 4-1/2" of wood —
    it gives it whatever the overlap actually is. Counting the authored plies instead is how
    a bearing check comes out right on paper and wrong in the field.
    """
    from typehaus.resolve.framing.profiles import cross_section

    resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
    section = _section_in(post.size)
    if resolved is None or section is None:
        return 0.0, 0
    along_x = (deck.joists.direction or "x") == "x"
    perp = 1 if along_x else 0  # the axis a joist's WIDTH is measured along
    half_post_m = section[perp] / 2.0 * _M_PER_IN
    centre = post.position.xy_m[perp]
    lo, hi = centre - half_post_m, centre + half_post_m

    total_m = 0.0
    count = 0
    for member in resolved.members:
        if member.category not in ("joist", "sister_joist"):
            continue
        try:
            width_m = float(cross_section(member.profile).width_m)
        except (KeyError, ValueError):
            continue
        line = member.p0[perp]
        overlap = min(hi, line + width_m / 2.0) - max(lo, line - width_m / 2.0)
        if overlap > _TOL_M:
            total_m += overlap
            count += 1
    return total_m / _M_PER_IN, count


def _post_on_field_in(ctx: EngineeringContext, deck: Any,
                     post: Any) -> tuple[float, bool] | None:
    """``(the post's bearing length ALONG the joists, is it at the field's end)``, in inches.

    Clipped to the joist field, and that clip is the whole reason this is a function rather
    than a call to ``cross_section``. ``PT-SG-BF2`` stands on the porch's front beam axis,
    which is where the joists STOP — half its 5-1/2" footprint is over the deck edge with no
    joist under it. Crediting the full section there would hand the joint twice the bearing
    area it has, at the one post where this rule was written to find exactly that error.

    The clip also decides ``C_b``: a bearing that reaches the joist's end has no fibres
    beyond it, and §3.10.4 credits nothing.
    """
    resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
    section = _section_in(post.size)
    if resolved is None or section is None:
        return None
    along_x = (deck.joists.direction or "x") == "x"
    axis = 0 if along_x else 1
    joists = [m for m in resolved.members if m.category == "joist"]
    if not joists:
        return None
    field_lo = min(min(m.p0[axis], m.p1[axis]) for m in joists)
    field_hi = max(max(m.p0[axis], m.p1[axis]) for m in joists)
    half_m = section[axis] / 2.0 * _M_PER_IN
    centre = post.position.xy_m[axis]
    lo, hi = max(field_lo, centre - half_m), min(field_hi, centre + half_m)
    if hi - lo <= _TOL_M:
        return None
    at_end = (centre - half_m < field_lo - _TOL_M or centre + half_m > field_hi + _TOL_M)
    return (hi - lo) / _M_PER_IN, at_end


def _beam_bearing_in(ctx: EngineeringContext, deck: Any,
                     post: Any) -> tuple[float, str, bool] | None:
    """``(bearing length in, beam tag, is an end bearing)`` where the joists meet the beam.

    The length is the geometric OVERLAP of the beam's plan width with the joist field's own
    extent — not the beam's width, and not the post's position over it. A joist that crosses
    a 4-1/2" beam bears on all of it; a joist that STOPS on that beam's axis bears on half.
    catlin's porch is one of each, on the same deck: the back beam is crossed and the front
    one is landed on with 2-1/4", and reading the beam's width at both would overstate the
    front joint by a factor of two. The post's own station does not enter it — what bears
    here is the joist, and its contact area is whatever the two members share.
    """
    from typehaus.model.structure import Beam

    resolved = next((f for f in ctx.model.floors if f.tag == deck.tag), None)
    if resolved is None:
        return None
    along_x = (deck.joists.direction or "x") == "x"
    axis = 0 if along_x else 1  # the axis a joist RUNS along
    joists = [m for m in resolved.members if m.category == "joist"]
    if not joists:
        return None
    field_lo = min(min(m.p0[axis], m.p1[axis]) for m in joists)
    field_hi = max(max(m.p0[axis], m.p1[axis]) for m in joists)

    nodes = _node_xy(ctx)
    best: tuple[float, str, bool] | None = None
    best_distance = float("inf")
    for ref in deck.joists.bearing_refs or ():
        beam = ctx.plan.by_tag(ref)
        if not isinstance(beam, Beam):
            continue
        section = _section_in(beam.size)
        p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
        if section is None or p0 is None or p1 is None:
            continue
        band_centre = (p0[axis] + p1[axis]) / 2.0
        half_m = section[0] / 2.0 * _M_PER_IN
        overlap_m = (min(field_hi, band_centre + half_m)
                     - max(field_lo, band_centre - half_m))
        if overlap_m <= _TOL_M:
            continue
        distance = abs(band_centre - post.position.xy_m[axis])
        if distance < best_distance:
            # An END bearing is one where the joist field stops inside the beam's width:
            # there is no wood beyond the bearing to earn C_b.
            at_end = (band_centre + half_m > field_hi + _TOL_M
                      or band_centre - half_m < field_lo - _TOL_M)
            best, best_distance = (overlap_m / _M_PER_IN, beam.tag, at_end), distance
    return best


def _one(ctx: EngineeringContext, post: Any, deck: Any) -> EngineeringRecord:
    tags = (post.tag, deck.tag)
    incomplete = []
    section = _section_in(post.size)
    reaction_lb, from_beams = _reaction_lb(ctx, post)
    ply_width_in, ply_count = _ply_width_in(ctx, deck, post)
    on_field = _post_on_field_in(ctx, deck, post)
    beam_bearing = _beam_bearing_in(ctx, deck, post)

    if section is None:
        incomplete.append(
            f"a resolvable cross-section for {post.tag}. `Post.size` is {post.size!r}; "
            f"write a true section like '5.5x5.5' rather than a nominal one that resolves "
            f"through LUMBER_ACTUAL to something else")
    if reaction_lb is None:
        incomplete.append(
            f"the load {post.tag} carries. No deck beam names it in `bearing_refs` under a "
            f"resolvable joist span, or one that does bears partly on a WALL and has no "
            f"station to take moments about — author the beam's supports, or seal the item")
    if on_field is None:
        incomplete.append(
            f"joist field under {post.tag}'s footprint along the joist run on {deck.tag}. "
            f"The post's plan rectangle lies entirely past the joists' own extent — it is "
            f"standing on the deck's edge, not on it")
    if ply_width_in <= 0.0:
        incomplete.append(
            f"joist stock under {post.tag}'s footprint on {deck.tag}. The post's plan "
            f"rectangle overlaps no resolved joist or sister — check that it stands over the "
            f"joist field rather than past its edge")
    if beam_bearing is None:
        incomplete.append(
            f"a beam under {deck.tag}'s joists whose width overlaps the joist field, to take "
            f"the second bearing against — `JoistSpec.bearing_refs` names none that resolves")
    if incomplete:
        return EngineeringRecord(
            item_id=item_id(KIND, post.tag), kind=KIND, key=post.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=(f"{post.tag}: bearing on {post.supported_by} cannot be computed — "
                     f"{len(incomplete)} input(s) missing"),
            inputs=(), limit_states=(), missing=tuple(incomplete),
            notes=(), element_tags=tags)

    assert (section is not None and reaction_lb is not None
            and beam_bearing is not None and on_field is not None)
    post_w_in, post_d_in = section
    beam_len_in, beam_tag, beam_at_end = beam_bearing
    # The post's dimension ALONG the joist is the length of its bearing on the joist top —
    # clipped to the field, so a post at the deck edge is credited only with what is under it.
    post_along_in, post_at_end = on_field

    fc_perp = SAWN_FC_PERP_PSI * WET_FC_PERP
    cb_top = _bearing_area_factor(post_along_in, at_member_end=post_at_end)
    cb_beam = _bearing_area_factor(beam_len_in, at_member_end=beam_at_end)

    area_top = ply_width_in * post_along_in
    area_beam = ply_width_in * beam_len_in
    top_psi = reaction_lb / area_top
    beam_psi = reaction_lb / area_beam

    states = (
        LimitState(
            "bearing on the joist top, under the post", top_psi, fc_perp * cb_top, "psi",
            f"AWC NDS 2018 §3.10.2 — Fc-perp {SAWN_FC_PERP_PSI:,.0f} psi (SPF, Supplement "
            f"Table 4A) x C_M {WET_FC_PERP:.2f} (Table 4.3.1, wet service) x C_b "
            f"{cb_top:.3f} "
            f"({'an END bearing, §3.10.4 credits nothing' if post_at_end else '§3.10.4'} "
            f"over {post_along_in:.2f}\"), NO C_D (§3.10.2 takes none) — on "
            f"{ply_width_in:.2f}\" of joist stock"),
        LimitState(
            f"bearing where the joists land on {beam_tag}", beam_psi, fc_perp * cb_beam,
            "psi",
            f"AWC NDS 2018 §3.10.2 — Fc-perp {SAWN_FC_PERP_PSI:,.0f} psi x C_M "
            f"{WET_FC_PERP:.2f} x C_b {cb_beam:.3f} "
            f"({'an END bearing, §3.10.4 credits nothing' if beam_at_end else '§3.10.4'}) "
            f"over {beam_len_in:.2f}\" of contact"),
    )
    over = any(not state.ok for state in states)
    worst = max(states, key=lambda s: s.ratio)

    return EngineeringRecord(
        item_id=item_id(KIND, post.tag), kind=KIND, key=post.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{post.tag}: a {post.size} standing on {deck.tag} delivers "
                 f"{reaction_lb:,.0f} lb into {ply_width_in:.2f}\" of joist — d/c "
                 f"{worst.ratio:.2f}, governed by {worst.name}"),
        inputs=(
            Quantity("post_width", post_w_in, "in", 0.0625),
            Quantity("post_depth", post_d_in, "in", 0.0625),
            Quantity("reaction", reaction_lb, "lb", 1.0),
            Quantity("joist_stock_width", ply_width_in, "in", 0.0625),
            Quantity("joist_plies", float(ply_count), "members", None),
            Quantity("beam_bearing_length", beam_len_in, "in", 0.0625),
            Quantity("Fc_perp_adjusted", fc_perp, "psi", 1.0),
        ),
        limit_states=states,
        notes=(
            f"LOAD: {reaction_lb:,.0f} lb, the reaction of "
            f"{', '.join(from_beams) or 'no beam'} at this post, taken by statics on the "
            f"beam's own overhangs rather than split evenly between its supports. It is the "
            f"same line load `deck_beam/{from_beams[0] if from_beams else '...'}` reports, "
            f"read at the other end of the joint.",
            f"WET SERVICE IS APPLIED. C_M {WET_FC_PERP:.2f} takes Fc-perp to "
            f"{fc_perp:,.0f} psi from {SAWN_FC_PERP_PSI:,.0f}. An open deck frame graded "
            f"against the dry value is overstated by half again, and the same joint's glulam "
            f"has been graded wet (C_M 0.53) since this engine first computed it.",
            "NO LOAD DURATION FACTOR. §3.10.2 takes none on Fc-perp: it is a deformation "
            "limit rather than a strength one. A hand check that applies C_D here comes out "
            "optimistic by whatever factor it borrowed.",
            f"TWO PLANES, NOT ONE. The post's end grain on the joist top "
            f"({area_top:.2f} in2) and the joists' flat on {beam_tag} ({area_beam:.2f} in2) "
            f"are different areas under the same load, and the second is usually the "
            f"smaller. Grading only the one under the base is how this joint passes on paper.",
            "SCREENING: no uplift, no eccentricity from the post standing off the beam's "
            "centreline, no fastener capacity in the tie that holds it down, and no "
            "long-term deformation limit beyond the Fc-perp value itself. A stamped design "
            "is what closes those.",
        ),
        element_tags=tags)


@keys(KIND)
def enumerate_posts(ctx: EngineeringContext) -> list[str]:
    return [post.tag for post, _deck in _posts_on_framing(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, post, deck) for post, deck in _posts_on_framing(ctx)]
