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
from dataclasses import dataclass

from typehaus.checks._authoring import passed, structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._asce_29_3_table import (
    GUST_EFFECT_RIGID,
    MAX_VERIFIED_CASE_AB,
    force_coefficient,
)
from typehaus.findings import Finding, Result
from typehaus.model.structure import KneeBrace, Post, Railing
from typehaus.model.trim import Fascia
from typehaus.takeoff.hardware_catalog import ROLE_KNEE_BRACE, allowable_for_model
from typehaus.wind import ASD_WIND_FACTOR, velocity_pressure_psf, wind_basis

_CID = "structural.lateral_racking"
_FT = 0.3048

#: Deck plank thickness contributes to the solid edge band. Read off the fascia's own top
#: elevation vs. the deck it faces would be better; the fascia's `depth` already covers the
#: joist ends and the plank edge, so nothing is added for the plank here — it would be
#: double counting. Recorded as a constant of zero so the decision is visible, not implied.
_PLANK_BAND_FT = 0.0


@dataclass(frozen=True)
class Band:
    """One horizontal strip of solid area the wind sees, and where it came from."""

    label: str
    depth_ft: float       # vertical dimension of the strip
    length_ft: float      # its plan run, perpendicular to the wind
    source: str           # the element tag it was derived from

    @property
    def area_sf(self) -> float:
        return self.depth_ft * self.length_ft


@dataclass(frozen=True)
class Demand:
    """The wind demand on one braced structure in one plan direction."""

    axis: str             # "x" (E-W wind) | "y" (N-S wind)
    q_h_psf: float
    height_ft: float      # top of the appurtenance above the ground beneath it
    bands: tuple[Band, ...]
    braces: tuple[KneeBrace, ...]

    @property
    def area_sf(self) -> float:
        return sum(b.area_sf for b in self.bands)

    def storey_shear_lb(self, c_f: float) -> float:
        """ASD storey shear at a given force coefficient: 0.6 · q_h · G · C_f · A_s."""
        return ASD_WIND_FACTOR * self.q_h_psf * GUST_EFFECT_RIGID * c_f * self.area_sf


# --- geometry ---------------------------------------------------------------------------


def _ft(length) -> float:
    return length.meters / _FT


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


def _solid_bands(ctx: CheckContext, axis: str, all_braces, fascia) -> tuple[Band, ...]:
    """The solid strips this deck presents to wind blowing along ``axis``.

    Derived, never authored. The fascia gives its own depth and the extent of the deck it
    wraps; the braces' ``connects`` name the members they rise into, and each one's section
    depth is another strip. A reader who deepens the fascia or retypes a rail moves the
    demand, which is the whole point of deriving rather than authoring an area.

    **The members are gathered from every brace, not from this direction's braces.** That
    reads backwards and is the correction to the obvious version: what presents a face to
    wind along ``x`` is the members running along ``y``, and those are exactly the ones the
    *other* direction's braces rise into. Scoping the search to this axis's own braces finds
    only members running along the wind, whose ends present nothing, and silently drops every
    rail and beam from the area — leaving the fascia to carry a demand it is not alone in.
    """
    tags = {t for brace in all_braces for t in brace.connects}
    bands: list[Band] = []

    if fascia is not None:
        xs = [p.xy_m[0] / _FT for p in fascia.path]
        ys = [p.xy_m[1] / _FT for p in fascia.path]
        # Wind along y meets the deck's E-W run; wind along x meets its N-S run.
        run = (max(xs) - min(xs)) if axis == "y" else (max(ys) - min(ys))
        bands.append(Band("fascia + deck edge", _ft(fascia.depth) + _PLANK_BAND_FT,
                          run, fascia.tag))

    # The rail or beam each brace rises into. Counted once per distinct member, at the
    # member's own length, because two braces on one continuous rail do not present the
    # strip twice.
    seen: set[str] = set()
    for tag in sorted(tags):
        element = ctx.plan.by_tag(tag)
        if element is None or tag in seen or isinstance(element, Post):
            continue
        depth = _member_depth_ft(ctx, tag)
        length = _member_length_ft(ctx, element)
        if depth is None or length is None:
            continue
        # Only members running perpendicular to the wind present their face to it.
        if _runs_along(ctx, element) == axis:
            continue
        seen.add(tag)
        bands.append(Band(f"{tag} section depth", depth, length, tag))
    return tuple(bands)


def _node_xy(ctx: CheckContext, tag: str):
    element = ctx.plan.by_tag(tag) if tag else None
    position = getattr(element, "position", None)
    return position.xy_m if position is not None else None


def _member_length_ft(ctx: CheckContext, element) -> float | None:
    start = _node_xy(ctx, getattr(element, "start_node", "") or "")
    end = _node_xy(ctx, getattr(element, "end_node", "") or "")
    if start is None or end is None:
        return None
    return math.dist(start, end) / _FT


def _runs_along(ctx: CheckContext, element) -> str | None:
    start = _node_xy(ctx, getattr(element, "start_node", "") or "")
    end = _node_xy(ctx, getattr(element, "end_node", "") or "")
    if start is None or end is None:
        return None
    return "x" if abs(end[0] - start[0]) >= abs(end[1] - start[1]) else "y"


def _member_depth_ft(ctx: CheckContext, tag: str) -> float | None:
    """A beam's section depth, from its authored nominal size.

    The dressed depth, not the nominal one: a "2x8" rail presents 7.25 inches to the wind,
    not 8. ``cross_section`` is the same resolver the framing solver uses, so this cannot
    drift from the member that actually gets built.
    """
    size = getattr(ctx.plan.by_tag(tag), "size", None)
    if not size:
        return None
    from typehaus.resolve.framing.profiles import cross_section

    try:
        return cross_section(size).depth_m / _FT
    except (KeyError, ValueError):
        return None


def _ground_below_ft(ctx: CheckContext) -> float:
    """The elevation of the ground under this structure, in the project frame.

    The sunken garden floor, not the site grade: this deck stands over an excavation, and
    z in ASCE 7's K_z is height above the ground *there*. Taking the site grade would shorten
    z by six feet and understate q_h, which is the wrong direction to be wrong in.
    """
    site = ctx.plan.project.site
    candidates = [_ft(spot.elevation) for spot in site.spot_elevations]
    if site.grade is not None:
        candidates.append(_ft(site.grade))
    return min(candidates) if candidates else 0.0


# --- the check ----------------------------------------------------------------------------


@check(Tier.STRUCTURAL, _CID)
def lateral_racking(ctx: CheckContext) -> list[Finding]:
    """One finding per braced direction, plus one for the unbraced posts and one for the rail."""
    braces = [e for e in ctx.plan.all_elements() if isinstance(e, KneeBrace)]
    if not braces:
        return []

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

    ground_ft = _ground_below_ft(ctx)
    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}
    fascia = _nearest(ctx, braces, Fascia)
    guard = _nearest(ctx, braces, Railing)
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
        demand = Demand(axis=axis, q_h_psf=q_h, height_ft=height_ft,
                        bands=_solid_bands(ctx, axis, braces, fascia), braces=here)
        out.extend(_grade_direction(demand, posts, basis))

    out.extend(_grade_unbraced_posts(ctx, braces, posts))
    return out


def _nearest(ctx: CheckContext, braces, kind):
    """The element of ``kind`` whose plan path actually belongs to this braced structure.

    A whole-plan ``next(... isinstance(e, kind) ...)`` is wrong and quietly so: catlin has
    thirteen ``Railing`` elements, and the first one found is a stair-head guard on the main
    floor. Reading its base elevation as the balcony's top put the appurtenance height at
    12.8' instead of 23.0' and understated q_h by 12 %. Nothing about the finding text would
    have looked wrong. So the element is chosen by proximity to the braces it is supposed to
    describe, which is the only relationship that holds when the plan grows.
    """
    xs = [b.position.xy_m[0] for b in braces]
    ys = [b.position.xy_m[1] for b in braces]
    cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
    best, best_d = None, None
    for element in ctx.plan.all_elements():
        if not isinstance(element, kind):
            continue
        path = getattr(element, "path", ())
        if len(path) < 3:
            continue
        px = sum(p.xy_m[0] for p in path) / len(path)
        py = sum(p.xy_m[1] for p in path) / len(path)
        d = math.dist((px, py), (cx, cy))
        if best_d is None or d < best_d:
            best, best_d = element, d
    return best


def _grade_direction(demand: Demand, posts, basis) -> list[Finding]:
    """Demand-to-capacity for every brace resisting wind along one axis."""
    axis_name = "E-W" if demand.axis == "x" else "N-S"
    tags = tuple(sorted(b.tag for b in demand.braces))
    if demand.area_sf <= 0:
        return [structural_advisory(
            _CID, f"{axis_name} bracing: no solid projected area could be derived from the "
                  f"modelled fascia and rail/beam bands, so no wind demand is computable",
            tags, Result.UNKNOWN,
            "check that the deck's Fascia and the members the braces connect to resolve")]

    band_text = "; ".join(f"{b.label} {b.depth_ft * 12:.1f}\" x {b.length_ft:.1f}' "
                          f"= {b.area_sf:.1f} sf ({b.source})" for b in demand.bands)
    out: list[Finding] = []
    for brace in sorted(demand.braces, key=lambda b: b.tag):
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

    n_braces = len(demand.braces)
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
    # storey column at all — catlin's twelve ``PT-SG-HP*`` are 12"-tall aluminium stand legs
    # under the heat pumps, sitting inside the balcony footprint and answering to
    # ``mep.deck_equipment_support``, not to a lateral system. Listing them here would bury
    # the two pillars this finding exists to name in ten that are not columns.
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
