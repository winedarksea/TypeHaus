"""Does the wind push this freestanding deck over sideways, and does its bracing hold?

Every other structural check in this package grades a member against a prescriptive table.
This one computes a **load** — the first place in the model that turns
``Site.design_wind_speed_mph`` into pounds — and compares it against a connector's published
allowable. It exists because the balcony is the one structure here with no shear walls at
all: six posts on pinned ``ABU66SS`` standoff bases carrying a deck at storey height, with
knee braces as the entire lateral system. Simpson say so in their own report language, which
``plans/TODO.md`` already quotes: post bases "do not provide adequate resistance to prevent
members from rotating about the base."

**What it computes, exactly.**

1. ``q_h`` at the top of the appurtenance, ASCE 7-16 §26.10, from the site's own basis via
   ``typehaus.wind``. Exposure comes from ``Site.wind_exposure`` — B here — and the height
   is measured from the **sunken garden floor**, the ground actually beneath this structure,
   not from the site grade six feet higher. That is the conservative reading and it is the
   physical one.
2. ``A_s`` per plan direction, derived from the modelled fascia, deck edge and rail/beam
   bands. Nothing authored: change the fascia depth and the demand moves.
3. ``F = q_h · G · C_f · A_s`` (§29.3, eq. 29.3-1), then ``0.6 F`` for ASD (§2.4.1), split
   to the braced bays.
4. The brace's axial force from the post free body, and the connector's allowable from
   ``takeoff/hardware_catalog``'s transcribed reports.

**Why it never returns a bare PASS.** Two independent reasons, and either alone is enough.

*The missing coefficient.* ``C_f`` comes from ASCE 7-16 Fig. 29.3-1, a copyrighted table
this repository holds only three verified cells of (see ``_asce_29_3_table``). So the check
inverts: it reports the **critical C_f** at which each joint reaches capacity, and compares
that against the largest coefficient Cases A and B are known to produce. A joint whose
critical C_f clears that bound is adequate for *any* legitimate reading of the figure —
which is a stronger statement than a demand computed off one guessed cell, and an honest one.

*The severity contract.* Even fully decided, a screening calculation is not a stamped
design, and this house's convention (``notes/catlin_truss_engineering.md``,
``notes/uplift_load_path.md``) is that hand-worked engineering is offered for review and
never flips a check green on its own strength. So: UNKNOWN when the numbers are comfortable,
UNKNOWN with the ratio named when they are not, and PASS **only** against an authored
``KneeBrace.engineering_spec`` — the identical escape hatch
``checks/structural/foundation.py::_grade_one`` gives ``FoundationWall.engineering_spec``.

It also never returns FAIL, and that is deliberate rather than timid. ``scripts/verify.sh``
holds catlin to zero FAIL, so a FAIL here is a build-breaking assertion that a real structure
is inadequate — a claim this calculation, with one input it could not source, has no standing
to make. Where the numbers are genuinely bad the UNKNOWN says so in its own text and names
the ratio, which is what a reader acts on.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import engineered, passed, structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._asce_29_3_table import (
    GUST_EFFECT_RIGID,
    MAX_VERIFIED_CASE_AB,
    force_coefficient,
)
from typehaus.engineering.balcony_wind import (
    Demand,
    ground_below_ft,
    nearest,
    solid_bands,
)
from typehaus.engineering.item import item_id
from typehaus.findings import Finding, Result
from typehaus.model.structure import KneeBrace, Post, Railing
from typehaus.model.trim import Fascia
from typehaus.takeoff.hardware_catalog import ROLE_KNEE_BRACE, allowable_for_model
from typehaus.wind import ASD_WIND_FACTOR, velocity_pressure_psf, wind_basis

_CID = "structural.lateral_racking"
_FT = 0.3048


def _ft(length) -> float:
    return length.meters / _FT


# --- geometry ---------------------------------------------------------------------------
#
# ``Band``, ``Demand``, the solid-area walk, the ground datum and the nearest-element search
# were hoisted into ``engineering/balcony_wind.py`` on 2026-09-03, when the balcony's
# lateral system became four fixed concrete columns and ``engineering/deck_post.py`` needed
# the same wind demand this check computes. They are imported back rather than reimplemented
# **so this check's numbers cannot move**: ``tests/test_lateral_racking.py`` pins the band
# areas and the critical coefficients on the landed house.


def _brace_axial_per_unit_shear(post_height_ft: float, leg_ft: float) -> float | None:
    """Axial force in one 45-degree knee brace per pound of shear at the post top.

    The post is a free body: pinned at its base (an ``ABU66SS`` is a standoff stirrup, not a
    moment base — Simpson state that plainly), a horizontal shear ``V`` delivered at the beam
    at height ``h``, and the brace meeting the post ``a`` below that. Moments about the base,
    with the brace at 45 degrees so its horizontal component is ``P·cos45``::

        V · h = P · cos45 · (h - a)      ->      P = V · h · sqrt(2) / (h - a)

    The brace's vertical component acts along the post axis and takes no moment about the
    base, which is why it does not appear. ``None`` where the brace is as long as the post —
    the free body degenerates and no finite force resists the shear.
    """
    lever = post_height_ft - leg_ft
    if lever <= 0.1:
        return None
    return post_height_ft * math.sqrt(2.0) / lever


# --- the check ----------------------------------------------------------------------------


@check(Tier.STRUCTURAL, _CID)
def lateral_racking(ctx: CheckContext) -> list[Finding]:
    """One finding per braced direction, plus one for the unbraced posts and one for the rail."""
    braces = [e for e in ctx.plan.all_elements() if isinstance(e, KneeBrace)]
    if not braces:
        return _grade_moment_columns(ctx)

    basis = wind_basis(ctx.plan.project.site)
    tags = tuple(sorted(b.tag for b in braces))
    if basis is None:
        return [structural_advisory(
            _CID,
            f"{len(braces)} knee brace(s) carry the whole lateral resistance of a "
            f"freestanding structure, and no wind demand can be computed: the site authors "
            f"no complete design wind basis",
            tags, Result.UNKNOWN,
            "author Site.design_wind_speed_mph, wind_exposure and risk_category")]

    ground_ft = ground_below_ft(ctx.plan)
    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}
    fascia = nearest(ctx.plan, braces, Fascia)
    guard = nearest(ctx.plan, braces, Railing)
    # h is the height to the top of the whole appurtenance (§29.3 evaluates q at h). The
    # guard is the top of it even though the guard itself contributes no solid area — a
    # porous rail still sets where the structure ends, and taking the deck instead would
    # shorten z and understate q_h.
    top_ft = (_ft(guard.base_elevation) + _ft(guard.height)) if guard is not None else \
        max(_ft(b.soffit_elevation) for b in braces)
    height_ft = top_ft - ground_ft
    q_h = velocity_pressure_psf(basis, height_ft)

    out: list[Finding] = []
    for axis in ("x", "y"):
        here = tuple(b for b in braces if b.axis == axis)
        if not here:
            continue
        # Every brace's ``connects``, not just this direction's — see ``solid_bands``.
        member_tags = {t for brace in braces for t in brace.connects}
        demand = Demand(axis=axis, q_h_psf=q_h, height_ft=height_ft,
                        bands=solid_bands(ctx.plan, axis, member_tags, fascia),
                        members=here)
        out.extend(_grade_direction(demand, posts, basis))

    out.extend(_grade_unbraced_posts(ctx, braces, posts))
    return out


def _grade_direction(demand: Demand, posts, basis) -> list[Finding]:
    """Demand-to-capacity for every brace resisting wind along one axis."""
    axis_name = "E-W" if demand.axis == "x" else "N-S"
    tags = tuple(sorted(b.tag for b in demand.members))
    if demand.area_sf <= 0:
        return [structural_advisory(
            _CID, f"{axis_name} bracing: no solid projected area could be derived from the "
                  f"modelled fascia and rail/beam bands, so no wind demand is computable",
            tags, Result.UNKNOWN,
            "check that the deck's Fascia and the members the braces connect to resolve")]

    band_text = "; ".join(f"{b.label} {b.depth_ft * 12:.1f}\" x {b.length_ft:.1f}' "
                          f"= {b.area_sf:.1f} sf ({b.source})" for b in demand.bands)
    out: list[Finding] = []
    for brace in sorted(demand.members, key=lambda b: b.tag):
        out.append(_grade_brace(brace, demand, axis_name, band_text, posts, basis))
    return out


def _grade_brace(brace: KneeBrace, demand: Demand, axis_name: str, band_text: str,
                 posts, basis) -> Finding:
    """One brace: shear share -> axial force -> connector allowable -> critical C_f."""
    tags = (brace.tag, *brace.connects)

    # An authored engineer's design IS the design. Same contract as FoundationWall's.
    if brace.engineering_spec:
        return passed(_CID, f"{brace.tag} — engineered lateral design authored: "
                            f"{brace.engineering_spec}", tags)

    post = posts.get(next((t for t in brace.connects if t in posts), ""))
    if post is None or getattr(post, "height", None) is None:
        return structural_advisory(
            _CID, f"{brace.tag} cannot be graded: it names no Post whose height resolves, so "
                  f"the free body that turns storey shear into brace axial force is undefined",
            tags, Result.UNKNOWN,
            "name the braced post in KneeBrace.connects")

    post_h = _ft(post.height)
    ratio = _brace_axial_per_unit_shear(post_h, _ft(brace.leg))
    if ratio is None:
        return structural_advisory(
            _CID, f"{brace.tag}: its {_ft(brace.leg):.1f}' leg leaves no lever against a "
                  f"{post_h:.2f}' post, so the knee-brace free body degenerates",
            tags, Result.UNKNOWN, "shorten the brace leg relative to the post height")

    n_braces = len(demand.members)
    # By role as well as by model: the KBS1Z is catalogued twice, once as a beam-to-post
    # cap and once as a knee-brace stabilizer, and the two carry different rows of
    # ER-280 Table 7. This joint is a knee brace, so it must read the knee-brace row.
    allowable = allowable_for_model(brace.connector, role=ROLE_KNEE_BRACE)
    capacity = allowable.lateral_f1_lb if allowable is not None else None
    species = allowable.species if allowable is not None else None

    common = (f"{axis_name} wind on the balcony: q_h {demand.q_h_psf:.1f} psf at "
              f"{demand.height_ft:.1f}' above the ground beneath ({basis.describe()}, "
              f"K_zt 1.0, G {GUST_EFFECT_RIGID}); solid area {demand.area_sf:.1f} sf "
              f"[{band_text}]; ASCE 7-16 §29.3 F = q_h G C_f A_s at 0.6 W (§2.4.1), shared "
              f"equally by {n_braces} brace(s); {brace.tag} on a {post_h:.2f}' post with a "
              f"{_ft(brace.leg):.1f}' leg carries {ratio:.2f} lb axial per lb of storey shear")

    lap_text = _lapped_foot_text(brace)

    if capacity is None:
        why = (allowable.citation if allowable is not None
               else f"no allowable-load record exists for {brace.connector}")
        return structural_advisory(
            _CID,
            f"{common}. **The connector has no published lateral capacity**, so no ratio can "
            f"be formed: {why}{lap_text}",
            tags, Result.UNKNOWN,
            "substitute a connector with a published brace-angle rating (the KBS1Z is the "
            "only one in this catalog: IAPMO UES ER-280 Table 7), or author "
            "KneeBrace.engineering_spec once an engineer has designed this joint")

    # Invert: at what C_f does this brace exactly reach its allowable?
    per_lb = ASD_WIND_FACTOR * demand.q_h_psf * GUST_EFFECT_RIGID * demand.area_sf \
        / n_braces * ratio
    critical_c_f = capacity / per_lb if per_lb > 0 else float("inf")

    b_over_s, s_over_h = _table_ratios(demand)
    cell = force_coefficient(b_over_s, s_over_h)
    lookup = (f"; Fig. 29.3-1 at B/s {b_over_s:.1f}, s/h {s_over_h:.2f} is not a cell this "
              f"model holds (see checks/structural/_asce_29_3_table.py)" if cell is None
              else f"; Fig. 29.3-1 gives C_f {cell.c_f:.2f} here ({cell.citation})")

    verdict = (f"adequate for any C_f up to {critical_c_f:.2f}, which exceeds the "
               f"{MAX_VERIFIED_CASE_AB:.2f} ceiling Cases A and B are known to reach — so "
               f"this joint clears for every value Fig. 29.3-1 can hold"
               if critical_c_f > MAX_VERIFIED_CASE_AB else
               f"**reaches its allowable at C_f {critical_c_f:.2f}, below the "
               f"{MAX_VERIFIED_CASE_AB:.2f} ceiling Cases A and B can reach** — this joint "
               f"is not demonstrably adequate and wants the real table cell or a redesign")

    return structural_advisory(
        _CID,
        f"{common}. Connector {brace.connector} allowable F1 {capacity:.0f} lbf "
        f"({species}); {verdict}{lookup}{lap_text}. Screening only — a stamped design is "
        f"what turns this into a PASS",
        tags, Result.UNKNOWN,
        "author KneeBrace.engineering_spec with a licensed engineer's lateral design")


def _lapped_foot_text(brace: KneeBrace) -> str:
    """What the connector allowable does and does not cover on a face-lapped brace.

    A lapped brace has two different joints at its two ends, and one published number cannot
    describe both. The HEAD still butts and is strapped, so the catalogued F1 is its number.
    The FOOT lies flat on the post face and is bolted through it — no connector, no product
    rating, an NDS Ch. 12 bolt-group calculation instead. Reporting the strap value alone
    would name the end that is *not* in question, which is the failure mode this whole check
    exists to avoid, so the text says which end each number belongs to.
    """
    if brace.foot_lap is None:
        return ""
    return (
        f". **Only the head is a connector joint.** The foot laps the post face for "
        f"{_ft(brace.foot_lap) * 12:.1f}\" and is through-bolted, because the brace's plane "
        f"is offset from the post's (KneeBrace.plane_offset) and no post material stands in "
        f"front of the end to bear on; its capacity is an NDS Ch. 12 bolt-group calculation "
        f"that no product rating covers. Two things make the number above conservative "
        f"rather than optimistic even so: the head butts an EQUAL-WIDTH member, which reads "
        f"ER-280's connection type 1 row and not the type 2 recorded here, and the free body "
        f"takes the brace as meeting the post at the face when the bolt group that delivers "
        f"the force sits half a lap lower, on a longer lever"
    )


def _table_ratios(demand: Demand) -> tuple[float, float]:
    """``(B/s, s/h)`` for the Fig. 29.3-1 lookup this check reports but cannot perform.

    ``s`` is the solid band's own vertical dimension — the summed band depths, not the guard
    height, because the guard is far too porous for §29.3's opening reduction to reach (see
    ``_asce_29_3_table.opening_reduction``). ``B`` is the run perpendicular to the wind and
    ``h`` the height to the top of the whole appurtenance.
    """
    s = sum(b.depth_ft for b in demand.bands) or 1.0
    b = max((band.length_ft for band in demand.bands), default=0.0)
    return (b / s, s / demand.height_ft)


def _grade_moment_columns(ctx: CheckContext) -> list[Finding]:
    """A freestanding deck with NO knee brace at all: is it braced by fixed columns instead?

    Added 2026-09-03, when catlin's balcony traded eight knee braces for four cast concrete
    columns fixed at the base. Returning ``[]`` for that structure would have been the worst
    possible answer — the check that exists precisely because this deck has no shear walls
    going silent on the day its whole lateral system changed — but it is also exactly what
    the brace-shaped code above did.

    **The finding is ENGINEERED, not computed here.** A fixed-base column's lateral
    adequacy is a base moment against a section's phiMn, and that is
    ``engineering/deck_post.py``'s arithmetic, keyed on the same ``deck_post/<tag>`` item the
    axial check already uses. One design, one stamp, two checks — the pattern
    ``structural.frost_depth`` and ``structural.foundation_unbalanced_fill`` share on a
    retaining wall. It is **not** ``defer``red, because unlike frost depth this check's own
    subject IS one of the limit states that calculation grades.

    **The no-braces-no-columns case still returns ``[]``.** A deck on wood posts with
    neither braces nor a moment base is a different (and worse) finding, and inventing it
    here would put this check in the business of grading structures it was never scoped to.

    **A deck with a WALL under any of its beams is skipped, and that gate is load-bearing.**
    catlin's porch deck lands its four beams into W-SG-W1/E1, two 12" concrete retaining
    walls — it is braced by shear walls in both directions and has no lateral question at
    all. Without the gate the two porch columns would each be reported as "the lateral
    system", which is a false claim about a real structure, and one that would then read as
    a PASS the moment their axial record came back OK.
    """
    from typehaus.model.floors import FloorSystem
    from typehaus.resolve.assembly_material import assembly_structure_material

    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}
    out: list[Finding] = []
    for deck in sorted((e for e in ctx.plan.all_elements()
                        if isinstance(e, FloorSystem) and e.service == "deck"),
                       key=lambda d: d.tag):
        if _bears_on_a_wall(ctx, deck):
            continue
        for tag in sorted(_deck_bearing_posts(ctx, deck)):
            post = posts.get(tag)
            if post is None:
                continue
            if assembly_structure_material(ctx.plan, post.assembly) != "concrete":
                continue
            out.append(engineered(
                ctx, _CID, item_id("deck_post", tag),
                f"deck {deck.tag} carries no knee brace and no shear wall: its lateral "
                f"system is the cast concrete column {tag}, fixed at its base. A fixed-base "
                f"column resists storey shear by BENDING, which no prescriptive table in "
                f"IRC R507 grades",
                (deck.tag, tag),
                fix=f"seal `deck_post/{tag}` in engineering.toml"))
    return out


def _bears_on_a_wall(ctx: CheckContext, deck) -> bool:
    """Does any beam under this deck land in a wall? Then the deck is not freestanding.

    A shear wall under a deck edge answers the lateral question outright, and this check
    has nothing to add to it. Cheap and structural: a beam whose ``bearing_refs`` names a
    ``Wall`` is hung into masonry or concrete, which is a fixed support in both directions.
    """
    from typehaus.model.elements import Wall
    from typehaus.model.structure import Beam

    for ref in deck.joists.bearing_refs or ():
        beam = ctx.plan.by_tag(ref)
        if not isinstance(beam, Beam):
            continue
        if any(isinstance(ctx.plan.by_tag(b), Wall) for b in beam.bearing_refs or ()):
            return True
    return False


def _deck_bearing_posts(ctx: CheckContext, deck) -> set[str]:
    """The posts under a deck, through the beams its joists bear on.

    Same walk ``engineering/pier_basis._deck_tributaries`` makes, and for the same reason:
    a deck names beams, and beams name the posts. Restated rather than imported because
    ``engineering`` may not import ``checks`` and the dependency the other way would drag a
    tributary calculation into a lateral check that has no use for one.
    """
    from typehaus.model.structure import Beam

    out: set[str] = set()
    for ref in deck.joists.bearing_refs or ():
        beam = ctx.plan.by_tag(ref)
        if not isinstance(beam, Beam):
            continue
        for bearing in beam.bearing_refs or ():
            if isinstance(ctx.plan.by_tag(bearing), Post):
                out.add(bearing)
    return out


def _grade_unbraced_posts(ctx: CheckContext, braces, posts) -> list[Finding]:
    """The posts carrying no brace at all — a real question, not a formality.

    ``plans/TODO.md`` has carried "do not author bracing here" for the two centre pillars
    since before the model had any wind number to check it against. Now that it has one,
    the entry's premise is testable, and this finding is what tests it: it names the posts,
    says they take no share in this calculation's distribution, and leaves the decision where
    the TODO leaves it — with the consultant, not with the model.
    """
    braced = {t for brace in braces for t in brace.connects}
    # The shortest braced post sets the bar. Below roughly half of it a "post" is not a
    # storey column at all — catlin's eight ``PT-SG-HP*`` are 18"-tall aluminium stand legs
    # under the two heat pumps, standing on their own pad beside the porch and answering to
    # the manufacturer's bolt-down instruction, not to a lateral system. Listing them here
    # would bury the pillars this finding exists to name in six that are not columns.
    braced_heights = [_ft(posts[t].height) for t in braced
                      if t in posts and getattr(posts[t], "height", None) is not None]
    floor = 0.5 * min(braced_heights) if braced_heights else 0.0
    lonely = sorted(tag for tag, post in posts.items()
                    if tag not in braced and _shares_a_bearing(post, braces)
                    and getattr(post, "height", None) is not None
                    and _ft(post.height) >= floor)
    if not lonely:
        return []
    return [structural_advisory(
        _CID,
        f"{len(lonely)} post(s) in the braced structure carry no knee brace "
        f"({', '.join(lonely)}): they are leaning columns, and every pound of shear "
        f"distributed above was given to the braced bays on the assumption that the deck "
        f"and the continuous brace rails collect it and deliver it there. That assumption "
        f"is a diaphragm claim this model does not check",
        tuple(lonely), Result.UNKNOWN,
        "have the lateral consultant confirm the collector path, or brace these posts too")]


def _shares_a_bearing(post, braces) -> bool:
    """Is this post part of the same braced structure as the braces? Same plan neighbourhood."""
    if not braces:
        return False
    xs = [b.position.xy_m[0] for b in braces]
    ys = [b.position.xy_m[1] for b in braces]
    px, py = post.position.xy_m
    pad = 2.0  # metres of slack around the braced footprint
    return (min(xs) - pad <= px <= max(xs) + pad
            and min(ys) - pad <= py <= max(ys) + pad)
