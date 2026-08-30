"""Is the uplift load path continuous, link by link (→ 12 §checks/structural)?

Every other structural check here grades a *member*: can this joist span that far, is that
footing wide enough. None of them asks the question a wind event asks, which is about the
**joints between** members — whether there is an unbroken chain of hardware from the roof
down to the footings, or whether the chain has a link that is only gravity and nails.

The chain this check walks, top down:

1. roof  -> its bearing walls   — a tie at every rafter or truss heel that seats
2. floor -> its bearing walls   — a tie at every joist that seats
3. wall  -> the wall below      — strapping across the floor band, corners and runs
4. sill  -> foundation          — mudsill anchors along every plate on concrete
5. beam  -> post                — a cap or a strap at every beam end landing on a post
6. post  -> what it stands on   — a base under every post

**It grades coverage, not capacity.** A finding says a joint has hardware or has none; it
never says the hardware is big enough. Until 2026-08-30 the reason was that nothing in this
model carried a design wind speed at all; ``Site`` now carries one, and the reason has
narrowed rather than gone away — *this* check still derives no demand from it. It knows no
tributary area, no force coefficient, and no share of the storey shear for any joint it
walks, and a connector schedule without a load is a drawing, not a calculation. ``wind.py``
owns the wording, so the site's actual basis is quoted rather than a stale absence claim.
So a covered link is reported UNKNOWN, not PASS, for the same reason ``cantilever.py``
refuses to pass a mitigated cantilever: "there is hardware here" is a different claim from
"this joint is adequate", and folding the first into a PASS would retire a question an
engineer still has to answer. ``checks/structural/lateral_racking.py`` is the one place that
does compute a wind demand, and it covers the balcony's braced bays only.

An **uncovered** link is a FAIL. A joint with no connector at all is not a judgement call.

Coverage is read from the same functions the take-off bills from — ``takeoff/uplift.py`` and
``takeoff/anchors.py`` — plus the plan's own ``Connector`` elements. That is deliberate: a
check with its own second opinion about which joints are connected would drift from the BOM
within a month, and then two files would be wrong instead of one.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Beam, Post
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.takeoff.anchors import coil_strap_rows, mudsill_anchor_rows
from typehaus.takeoff.hangers import hung_connections
from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
from typehaus.takeoff.uplift import bearing_connections, bearing_line_tags
from typehaus.wind import capacity_caveat
from typehaus.takeoff.uplift_joints import (
    authored_joints,
    catalogued_post_sizes,
    is_squash_block,
    tags_covered_by,
)

_CHECK_ID = "structural.uplift_load_path"
_CONFIG = DEFAULT_HARDWARE_TAKEOFF_CONFIG
_RULES = _CONFIG.uplift

#: The connector kinds that make a seated end's uplift connection. A plan that authors one
#: of these naming a roof or floor owns that assembly's uplift, and the derived rule stands
#: down — the same hand-off ``takeoff/uplift.py`` makes, read from the same field.
_SEATED_UPLIFT_KINDS = frozenset({ConnectorKind.HURRICANE_TIE, ConnectorKind.HOLD_DOWN})
#: What can make a beam-to-post connection. HURRICANE_TIE belongs here with the strap and
#: the cap: on the sunken garden's two cast columns an H2.5A on the bearing plane IS the
#: uplift connection (``CN-SG-TIE-COL`` / ``CN-SG-TIE-FCOL``), and a set that named only
#: the strap reported four connected joints as breaks.
_POST_TOP_KINDS = frozenset({ConnectorKind.HOLD_DOWN, ConnectorKind.POST_CAP,
                             ConnectorKind.HURRICANE_TIE})


@dataclass(frozen=True)
class Link:
    """One joint in the chain: what it joins, and what (if anything) connects it."""

    name: str             # human description of the joint
    tags: tuple           # element tags a reader should look at
    hardware: str | None  # what covers it, or None when nothing does
    #: Why this joint cannot be graded at all. A FAIL says "I looked at this joint and there
    #: is no hardware"; this says "I could not look". The distinction is the whole point of
    #: the tri-state (#32): a post that never declares what it stands on is not evidence of a
    #: missing connector, and reporting it as one would put a modelling gap in the same
    #: column as a real break — and take ``haus check`` to exit 1 over it.
    not_evaluable: str | None = None


def _finding(link: Link, site) -> Finding:
    """Covered -> UNKNOWN, uncovered -> FAIL, un-gradeable -> UNKNOWN. See the docstring."""
    if link.not_evaluable is not None:
        return Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.UNKNOWN,
            message=(f"[advisory, not engineering] {link.name} cannot be graded: "
                     f"{link.not_evaluable}"),
            element_tags=link.tags)
    if link.hardware is None:
        return Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.FAIL,
            message=(f"[advisory, not engineering] no uplift hardware connects {link.name}; "
                     "the load path has a break here"),
            element_tags=link.tags,
            fix_hint=("declare the joint so a rule can derive it (a Roof/FloorSystem "
                      "bearing_ref, a Post.supported_by, a Beam.bearing_ref), or author a "
                      "Connector naming both members"))
    return Finding(
        severity=Severity.WARN, check_id=_CHECK_ID, result=Result.UNKNOWN,
        message=(f"[advisory, not engineering] {link.name} is connected by {link.hardware}; "
                 f"coverage only — {capacity_caveat(site)}"),
        element_tags=link.tags)


# --- links 1 and 2: roof and floor bearings ------------------------------------------


def _bearing_assemblies(ctx: CheckContext):
    """``(resolved, declared bearing tags, tied categories, noun)`` per roof and floor."""
    elements = {e.tag: e for e in ctx.plan.all_elements()}
    for roof in ctx.model.roofs:
        element = elements.get(roof.tag)
        yield (roof, tuple(getattr(element, "bearing_refs", ()) or ()),
               _RULES.tied_roof_categories, "roof")
    for floor in ctx.model.floors:
        joists = getattr(elements.get(floor.tag), "joists", None)
        yield (floor, tuple(getattr(joists, "bearing_refs", ()) or ()),
               _RULES.tied_floor_categories, "floor")


def _seated_links(ctx: CheckContext) -> list:
    """One link per roof/floor, comparing seated member ends against ties derived for them.

    The shortfall this exists to surface is quiet by construction: a floor that declares two
    of its three bearing lines still resolves, still frames, still passes every span check,
    and ties two thirds of its joists. Only counting the seated ends against the ties finds
    it.
    """
    authored = tags_covered_by(ctx.model, _SEATED_UPLIFT_KINDS)
    # Keyed on the ASSEMBLY, not the support: FS-M-WEST and FS-M-MECH both bear on W-B-W1,
    # and summing that wall's ties credited each of them with the other's, which read as 51
    # ties on an eighteen-joist floor.
    ties_by_assembly: dict = {}
    for connection in bearing_connections(ctx.model, _RULES):
        ties_by_assembly[connection.assembly_tag] = \
            ties_by_assembly.get(connection.assembly_tag, 0) + 1
    # A member end either bears on its support or hangs in it, and BOTH are connected: the
    # hung ones by the LUS/LSSR/HUCQ hangers ``takeoff/hangers.py`` bills. Counting only the
    # ties reported the breezeway deck — whose four 2x8 joists are framed flush into their
    # beams and every one of which carries a hanger — as a break in the load path.
    hangers_by_carrier: dict = {}
    for hung in hung_connections(ctx.model, _CONFIG.hanger_detection):
        carrier = hung.carrier_tag.split(":")[-1]
        hangers_by_carrier[carrier] = hangers_by_carrier.get(carrier, 0) + 1

    links: list = []
    for resolved, refs, categories, noun in _bearing_assemblies(ctx):
        seated = [m for m in resolved.members if m.category in categories]
        if not seated:
            continue  # nothing of this kind bears here — a slab deck, a roof with no rafters
        if resolved.tag in authored:
            links.append(Link(f"{noun} {resolved.tag} to its bearings", (resolved.tag, *refs),
                              "an authored Connector naming it"))
            continue
        if not refs:
            links.append(Link(
                f"{noun} {resolved.tag}'s {len(seated)} seated members to their bearings",
                (resolved.tag,), None))  # declares none: nothing to derive a tie against
            continue
        line = bearing_line_tags(ctx.model, refs, _RULES)
        tied = ties_by_assembly.get(resolved.tag, 0)
        hung = sum(count for tag, count in hangers_by_carrier.items()
                   if tag in line or tag in refs)
        covers = []
        if tied:
            covers.append(f"{tied} derived uplift ties")
        if hung:
            covers.append(f"{hung} hangers")
        # Name only the categories this assembly actually framed. A rafter roof and a truss
        # roof share one rule and one category set, and printing both at every roof told the
        # reader the house had truss heels in its cathedral ceiling.
        present = sorted({m.category for m in seated})
        links.append(Link(
            f"{len(seated)} {'/'.join(present)} members of {noun} "
            f"{resolved.tag} bearing on {', '.join(refs)}",
            (resolved.tag, *refs),
            " and ".join(covers) if covers else None))
    return links


# --- links 3 and 4: the floor band and the sill --------------------------------------


def _stack_and_sill_links(ctx: CheckContext) -> list:
    """The two wall-to-what-is-under-it joints, read off the rules ``anchors.py`` bills."""
    links: list = []
    stacked = sorted({edge.upper_wall for edge in ctx.model.stack_edges})
    if stacked:
        straps = coil_strap_rows(ctx.model, _CONFIG.wall_ties)
        links.append(Link(
            f"the {len(stacked)} stacked wall lines across their floor bands",
            tuple(stacked),
            f"{straps[0]['coils']} coil(s) of CS16 strapping" if straps else None))

    sills = [r for r in ctx.model.construction_returns
             if r.takeoff_category == _CONFIG.sill_plate_takeoff_category]
    if sills:
        anchors = mudsill_anchor_rows(ctx.model, _CONFIG.sill_plate_anchors,
                                      _CONFIG.sill_plate_takeoff_category)
        links.append(Link(
            f"the {len(sills)} sill plate runs to the concrete under them",
            tuple(sorted({r.storey for r in sills})),
            f"{anchors[0]['count']} MASA mudsill anchors" if anchors else None))
    return links


# --- links 5 and 6: beams on posts, posts on their bearings ---------------------------


def _is_concrete(ctx: CheckContext, post: Post) -> bool:
    """Is this "post" a cast column? Asked of the assembly, which is where the answer lives.

    Not asked of the section string: "12 round" is a shape, and a 12" round wood column is a
    perfectly ordinary thing. ``assembly_structure_material`` is the same function
    ``takeoff/framing.py`` splits its concrete and timber solid rows on, so a column filed as
    concrete in the BOM is filed as concrete here.
    """
    return assembly_structure_material(ctx.plan, post.assembly) == "concrete"


def _post_links(ctx: CheckContext) -> list:
    """A base under every post, and a strap or cap at every beam end that lands on one.

    The three conditions ``takeoff/uplift.py::post_base_rows`` cannot bill all surface here,
    which is the division of labour its docstring promises: the take-off orders what it can
    order, and this says out loud what it could not — a post with no declared bearing, and a
    concrete column no wood base fits.
    """
    stocked = catalogued_post_sizes()
    # Two kinds satisfy "this post is held down to what it stands on", and the second is not
    # a variant of the first. An ``EQUIPMENT_ANCHOR`` is a gasketed lag through a deck rather
    # than a formed stirrup, and it exists precisely because a bracket is the wrong part
    # there — but the joint it makes is the same joint, so the load path is developed and
    # this must say so. Omitting it does not merely mislabel: a 12" equipment stand leg falls
    # past this branch to ``is_squash_block`` and is reported as blocking whose "joint IS the
    # bearing", which is exactly backwards for a leg whose governing load is uplift.
    anchored = tags_covered_by(ctx.model, frozenset({ConnectorKind.EQUIPMENT_ANCHOR}))
    stirruped = tags_covered_by(ctx.model, frozenset({ConnectorKind.POST_BASE}))
    based = stirruped | anchored
    topped = authored_joints(ctx.model, _POST_TOP_KINDS)
    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}

    links: list = []
    for tag in sorted(posts):
        post = posts[tag]
        if post.within_wall:
            continue  # developed by the wall's own plates and studs; the SP tie bills that
        if _is_concrete(ctx, post):
            # A cast column on a cast footing is joined by a doweled lap into the column's
            # own bar cage. There is no connector to specify, so grading it against a post
            # base would report a break at a joint that has none and hand the reader an ABU
            # that does not fit a 12" round pour. Nor is the joint unpriced: a house's
            # [concrete] column rate is struck including the cage. What is missing is rebar
            # as an ELEMENT, which is why this is un-gradeable rather than covered.
            links.append(Link(
                f"column {tag} ({post.size}) to {post.supported_by or 'its footing'}",
                (tag,), None,
                not_evaluable=("it is cast concrete on concrete — a doweled lap into the "
                               "column's own bar cage, not a connector, and this model "
                               "carries no rebar to point at (the steel is inside the "
                               "column's own $/cy rate, not missing from the order)")))
        elif tag in based:
            # Named, not generalised to "a base": printing "an authored post base" against a
            # gasketed lag would be the same misreport in prose that the shared
            # ``ConnectorKind`` was in the BOM. A post named by both keeps the base, which
            # is the stronger claim about the joint.
            links.append(Link(
                f"post {tag} to {post.supported_by or 'its bearing'}", (tag,),
                "an authored equipment anchor"
                if tag in anchored and tag not in stirruped else "an authored post base"))
        elif is_squash_block(post, _RULES):
            # Short enough that it is blocking, not a column (see blocking_max_height_ft).
            # Its joint IS the bearing, so it is covered rather than un-gradeable — the
            # take-off skips it for the same reason and the two must agree.
            links.append(Link(
                f"block {tag} ({post.height.inches:.0f} in) to "
                f"{post.supported_by or 'its bearing'}", (tag,),
                "direct bearing — under 2 ft it is a squash block, and a block needs no "
                "base to bear through"))
        elif not post.supported_by:
            # Not a FAIL: a post that never says what it stands on is a modelling gap, not
            # evidence of a missing connector, and the two must not share a column.
            links.append(Link(
                f"post {tag} to whatever it stands on", (tag,), None,
                not_evaluable="it declares no `supported_by`, so there is no joint to grade"))
        elif post.size not in stocked:
            links.append(Link(
                f"post {tag} ({post.size}) to {post.supported_by}",
                (tag, post.supported_by), None,
                not_evaluable="no catalogued post base is published for that section"))
        else:
            links.append(Link(f"post {tag} to {post.supported_by}",
                              (tag, post.supported_by), "a derived standoff post base"))

    beams = sorted((e for e in ctx.plan.all_elements() if isinstance(e, Beam)),
                   key=lambda e: e.tag)
    for beam in beams:
        for ref in beam.bearing_refs:
            seat = posts.get(ref)
            if seat is None:
                continue  # bears on a wall, which is links 1-4's business
            if frozenset({beam.tag, ref}) in topped:
                hardware = "an authored strap or cap"
            elif seat.size in stocked and not _is_concrete(ctx, seat):
                hardware = "a derived KBS1Z strap"
            else:
                hardware = None
            links.append(Link(f"beam {beam.tag} where it lands on {ref}",
                              (beam.tag, ref), hardware))
    return links


@check(Tier.STRUCTURAL, _CHECK_ID)
def uplift_load_path(ctx: CheckContext) -> list[Finding]:
    """Every joint in the roof-to-footing chain, covered or broken."""
    site = ctx.plan.project.site
    return [_finding(link, site) for link in (
        *_seated_links(ctx),
        *_stack_and_sill_links(ctx),
        *_post_links(ctx),
    )]
