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
never says the hardware is big enough. ``Site`` carries a design wind speed, but *this*
check still derives no demand from it: it knows no tributary area, no force coefficient, and
no share of the storey shear for any joint it walks, and a connector schedule without a load
is a drawing, not a calculation. ``wind.py`` owns the wording, so the site's actual basis is
quoted rather than a stale absence claim.

**The rule is named for what it grades, and passes when it passes.** A covered link is a
PASS of the coverage rule that actually runs; it never claims the joint is adequate (#64).
That capacity question is ``structural.uplift_capacity``, at the foot of this module, and
since 2026-09-14 it is not an engineered item for any roof: a rafter-framed roof reads IRC
Table R802.11 for the demand and the connector's published allowable for the capacity, and a
trussed roof folds into the ``rafter/<tag>`` deferral its fabricator already seals.
``checks/structural/lateral_racking.py`` is the one place that computes a wind demand from
first principles, and it covers the balcony's braced bays only.

An **uncovered** link is a FAIL. A joint with no connector at all is not a judgement call.

Coverage is read from the same functions the take-off bills from — ``takeoff/uplift.py`` and
``takeoff/anchors.py`` — plus the plan's own ``Connector`` elements. That is deliberate: a
check with its own second opinion about which joints are connected would drift from the BOM
within a month, and then two files would be wrong instead of one.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import not_applicable
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.published import graded_against_published_capacity
from typehaus.findings import Finding, Result, Severity
from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
from typehaus.joints.authored import (
    authored_joints,
    tags_covered_by,
    unanchored_post_tags,
)
from typehaus.joints.bearing import bearing_connections, bearing_line_tags
from typehaus.joints.gable import gable_end_ties
from typehaus.joints.hung import hung_connections
from typehaus.joints.posts import catalogued_post_sizes, is_squash_block
from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Beam, Post
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.takeoff.anchors import coil_strap_rows, mudsill_anchor_rows
from typehaus.wind import capacity_caveat
from typehaus.wind_tables import (
    R802_11_CITATION,
    R802_11_CONDITIONS,
    uplift_connection_force_lb,
)

#: The id names what the rule grades: whether every joint in the chain is *covered*, a
#: narrower claim than "the load path is adequate". A covered joint is an honest PASS under
#: this name, and the capacity question is tracked separately in the engineering register
#: (see ``uplift_capacity_items`` below).
_CHECK_ID = "structural.uplift_path_coverage"

# ** THERE IS NO ``_CAPACITY_KIND`` ANY MORE (2026-09-14). ** It held "lateral_uplift", the
# kind this module minted one item of per roof, and the kind is retired — see
# ``uplift_capacity_items`` below for where the two halves of that question went, and the
# dated NOTE in ``engineering/deferred.py`` for why neither half needed a seal.
#: Feet per metre, for the plan extents R802.11's span is read off.
_M_PER_FT = 0.3048
_CONFIG = DEFAULT_HARDWARE_TAKEOFF_CONFIG
_RULES = _CONFIG.uplift

#: The connector kinds that make a seated end's uplift connection. A plan that authors one
#: of these naming a roof or floor owns that assembly's uplift, and the derived rule stands
#: down — the same hand-off ``takeoff/uplift.py`` makes, read from the same field.
_SEATED_UPLIFT_KINDS = frozenset({ConnectorKind.HURRICANE_TIE, ConnectorKind.HOLD_DOWN})
#: What can make a beam-to-post connection. HURRICANE_TIE belongs here with the strap and
#: the cap: an HGAM10 gusset on a bearing plane is an uplift connection (catlin's balcony
#: corner seats, CN-SG-SEAT-*).
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
    #: Why this joint is outside what a *connector-coverage* rule governs at all — as
    #: opposed to ``not_evaluable``, which is "I could not look". They are different
    #: sentences: a post that never declares what it stands on is a hole in the model
    #: somebody can fill, while a cast column on a cast footing has no connector by design
    #: and never will. The first is UNKNOWN; the second is NOT_APPLICABLE, which is a verdict
    #: about the building.
    not_governed: str | None = None


def _finding(link: Link, site) -> Finding:
    """Covered -> PASS, uncovered -> FAIL, outside the rule -> N/A. See the docstring."""
    if link.not_governed is not None:
        # N/A, and it is earned rather than assumed: a cast column on a cast footing is
        # joined by a doweled lap into the column's own bar cage, so it has no connector by
        # design and never will. A connector-coverage rule does not govern it — a verdict
        # about the building, not a confession that an input is missing.
        return not_applicable(
            _CHECK_ID,
            f"[advisory, not engineering] {link.name} is outside what a connector-coverage "
            f"rule governs: {link.not_governed}",
            link.tags)
    if link.not_evaluable is not None:
        # Still UNKNOWN, and the contrast with the branch above is the whole point: this is
        # a hole in the model somebody can fill, not a joint the rule does not reach.
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
    # PASS, of a rule named for what it grades: "there is hardware here" is never mistaken
    # for "this joint is adequate" (#64), because that question is one named ENGINEERED item
    # per roof, which a signoff has to cover and `haus engineering` lists.
    return Finding(
        severity=Severity.WARN, check_id=_CHECK_ID, result=Result.PASS,
        message=(f"[advisory, not engineering] {link.name} is connected by {link.hardware} "
                 f"— the joint is covered; its CAPACITY is not graded here and belongs to "
                 f"`structural.uplift_capacity`, which reads it off IRC Table R802.11 and "
                 f"the connector's own published allowable where the roof authors them, "
                 f"and defers it to `rafter/<roof>` where the roof is trussed "
                 f"({capacity_caveat(site)})"),
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
    # Support tags carrying ANY tie. Not per assembly: two decks meeting over one plate share
    # one tie per joint (``key_point``), and it is filed under whichever came last.
    tied_supports: set = set()
    for connection in bearing_connections(ctx.model, _RULES):
        ties_by_assembly[connection.assembly_tag] = \
            ties_by_assembly.get(connection.assembly_tag, 0) + 1
        tied_supports.add(connection.support_tag)
    pairs = authored_joints(ctx.model, _SEATED_UPLIFT_KINDS)
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
        # A floor on wall plates is toe-nailed, not tied; the wall above holds it down and the
        # band's straps carry the storey below (link 3).
        nailed = set()
        if noun == "floor" and not _RULES.tie_floor_joists_on_walls:
            nailed = {ref for ref in refs if ctx.model.wall(ref) is not None}
        hung = sum(count for tag, count in hangers_by_carrier.items()
                   if tag in line or tag in refs)
        covers = []
        if tied:
            covers.append(f"{tied} derived uplift ties")
        if hung:
            covers.append(f"{hung} hangers")
        if nailed:
            covers.append("toe-nails to the wall plates (IRC Table R602.3(1))")
        # Name only the categories this assembly actually framed. A rafter roof and a truss
        # roof share one rule and one category set, and printing both at every roof told the
        # reader the house had truss heels in its cathedral ceiling.
        present = sorted({m.category for m in seated})
        # A total is not coverage: catlin's balcony tied its centre beam eight times and its
        # two cantilevered edge beams not at all, and the count read as covered. Each
        # declared line has to carry something of its own.
        for ref in refs if covers else ():  # nothing at all is the one link below
            if ref in nailed:
                continue
            ref_line = bearing_line_tags(ctx.model, (ref,), _RULES) or {ref}
            if (ref_line & tied_supports
                    or ref_line & hangers_by_carrier.keys()
                    or any(frozenset({tag, resolved.tag}) in pairs for tag in ref_line)):
                continue
            links.append(Link(f"{noun} {resolved.tag}'s bearing line {ref}",
                              (resolved.tag, ref), None))
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
    # And a third, for the same reason: a wood post bearing directly on a wood BEAM takes
    # neither a stirrup nor a gasketed lag — it is held down to the framing by a tension
    # tie. Without this set PT-SG-BR2/BF2 fall past to ``is_squash_block`` and out to
    # ``not_evaluable``, and ``haus print --sealed`` gates on an UNKNOWN at a joint that in
    # fact has its part.
    tied = tags_covered_by(ctx.model, frozenset({ConnectorKind.TENSION_TIE}))
    # A base the plan declares bearing-only is a stirrup with an empty anchor hole. It is
    # still a base, so it must not fall past to ``is_squash_block`` on a 2 ft post — but
    # reporting it as a covered uplift joint would be the reverse error, and a louder one:
    # ``Connector.anchored=False`` is the plan SAYING no uplift is developed here.
    bearing_only = unanchored_post_tags(ctx.model)
    based = stirruped | anchored | tied
    topped = authored_joints(ctx.model, _POST_TOP_KINDS)
    posts = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Post)}

    links: list = []
    for tag in sorted(posts):
        post = posts[tag]
        # ``within_wall`` is geometric — the framer cuts the plates around the post — so it
        # cannot on its own say the base joint is made. A post standing in a stud line on an
        # authored base (the breezeway canopy columns) still has that base graded.
        if post.within_wall and tag not in based:
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
                not_governed=("it is cast concrete on concrete — a doweled lap into the "
                               "column's own bar cage, not a connector, and this model "
                               "carries no rebar to point at (the steel is inside the "
                               "column's own $/cy rate, not missing from the order)")))
        elif tag in bearing_only:
            links.append(Link(
                f"post {tag} to {post.supported_by or 'its bearing'}", (tag,), None,
                not_governed=("its base is authored bearing-only (Connector.anchored is "
                              "False) — no cast-in bolt, so download crosses the plate into "
                              "the pour and the joint claims NO uplift and NO lateral. There "
                              "is no connector here for a coverage rule to find, by design. "
                              "Whether the DEMAND is in fact nil is a separate statement, "
                              "and this rule derives no demand")))
        elif tag in based:
            # Named, not generalised to "a base": printing "an authored post base" against a
            # gasketed lag would be the same misreport in prose that the shared
            # ``ConnectorKind`` was in the BOM. A post named by both keeps the base, which
            # is the stronger claim about the joint.
            if tag in stirruped:
                how = "an authored post base"
            elif tag in anchored:
                how = "an authored equipment anchor"
            else:
                how = "an authored tension tie"
            links.append(Link(
                f"post {tag} to {post.supported_by or 'its bearing'}", (tag,), how))
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
    # A beam hung off a post that stands on its seat: the hanger is the uplift joint, and the
    # standing post's own base carries it on down (catlin's porch beams off PT-SG-B*2).
    hung = authored_joints(ctx.model, _POST_TOP_KINDS | {ConnectorKind.JOIST_HANGER})
    for beam in beams:
        for ref in beam.bearing_refs:
            seat = posts.get(ref)
            if seat is None:
                continue  # bears on a wall, which is links 1-4's business
            carrier = next((t for t, p in sorted(posts.items())
                            if p.supported_by == ref and frozenset({beam.tag, t}) in hung),
                           None)
            if frozenset({beam.tag, ref}) in topped:
                hardware = "an authored strap or cap"
            elif carrier is not None:
                hardware = f"an authored hanger off {carrier}, which stands on {ref}"
            elif seat.size in stocked and not _is_concrete(ctx, seat):
                hardware = "a derived KBS1Z strap"
            else:
                hardware = None
            links.append(Link(f"beam {beam.tag} where it lands on {ref}",
                              (beam.tag, ref), hardware))
    return links


# --- link 5: the gable end -----------------------------------------------------------


def _gable_links(ctx: CheckContext) -> list:
    """One link per gable-end wall, and the reason this leg was missing for so long.

    Every other link in this chain hangs off a member that BEARS on something. A gable end
    bears nothing — no rafter, no truss, no joist lands on it — so it was invisible to a rule
    built out of bearings, while being the wall that takes the largest out-of-plane wind
    pressure in the house. A chain with five sound legs and this one absent is not five-sixths
    connected; it is a chain with a gap at the end everybody photographs after a storm.

    Earned N/A when a house has no gable roof at all: the condition this leg grades does not
    exist, which is a verdict about the building rather than a silent absence.
    """
    ends = gable_end_ties(ctx.model, _CONFIG.gable_end_ties)
    if not ends:
        if not any(roof.form == "gable" for roof in ctx.model.roofs):
            return [Link("the gable-end wall ties", (), None,
                         not_governed="no roof in this model is a gable, so there is no "
                                      "gable end to tie")]
        # Gable roofs but no gable-end wall found under any of them — catlin's breezeway
        # canopy is the case, a gable bearing on two beams with no wall across its span.
        # That is a real answer and not a failure to look.
        return [Link("the gable-end wall ties", (), None,
                     not_governed="every gable roof here bears on beams, with no wall "
                                  "across the end of its span to tie")]
    authored = tags_covered_by(ctx.model, _SEATED_UPLIFT_KINDS)
    links: list = []
    for end in sorted(ends, key=lambda e: e.wall_tag):
        tags = (end.wall_tag, end.roof_tag)
        if end.wall_tag in authored:
            links.append(Link(f"gable-end wall {end.wall_tag} to {end.roof_tag}", tags,
                              "an authored Connector naming it"))
            continue
        ties = len(end.stations_m)
        links.append(Link(
            f"gable-end wall {end.wall_tag} to {end.roof_tag} over "
            f"{end.length_m * 3.28084:.1f} ft of top plate",
            tags, (f"{ties} derived LTP4 tying {end.gable_truss}" if end.gable_truss
                   else f"{ties} derived gable-end ties") if ties else None))
    return links


@check(Tier.STRUCTURAL, _CHECK_ID)
def uplift_path_coverage(ctx: CheckContext) -> list[Finding]:
    """Every joint in the roof-to-footing chain, covered or broken."""
    site = ctx.plan.project.site
    return [_finding(link, site) for link in (
        *_seated_links(ctx),
        *_stack_and_sill_links(ctx),
        *_post_links(ctx),
        *_gable_links(ctx),
    )]


@check(Tier.STRUCTURAL, "structural.uplift_capacity")
def uplift_capacity_items(ctx: CheckContext) -> list[Finding]:
    """The question ``uplift_path_coverage`` deliberately does not answer, named per roof.

    One row per roof rather than one per joint, and that is the whole design. A connector
    schedule is sized as a system against a storey's share of the wind demand; a per-joint
    item would invite 59 seals for one calculation, and the register's identity rule
    (one item per element) would then be working against the thing being sealed. A roof is
    the smallest unit an uplift design is actually done for.

    ** AND AS OF 2026-09-14 NO ROOF RAISES A ``lateral_uplift`` ITEM AT ALL. ** There were
    three, all UNKNOWN, all waiting on a seal; they split two ways and neither way was a
    calculation this engine started doing.

    * **A roof that authors ``published_uplift`` is a prescriptive read.** The DEMAND is
      IRC Table R802.11 — adopted law, indexed by exposure, spacing, span, speed and pitch,
      and the reason this check could never derive one was never that the number was
      unknowable, only that it was not computable from first principles here. The CAPACITY
      is the connector manufacturer's published allowable. Both sides are documents a
      reviewer opens, so the comparison mints nothing for the register
      (``checks/structural/published.graded_against_published_capacity``).
    * **A trussed roof folds into ``rafter/<tag>``.** It resolves no rafter member, so no
      R802.11 row describes it — the table is indexed by a rafter/truss spacing and span
      this engine cannot read off a roof it did not frame. The fabricator who seals the
      component design is already the person who publishes its uplift reactions, and
      ``engineering/deferred.py`` says so in that deferral's own deliverable. Two items
      naming one designer and one document was the redundancy; the finding still blocks,
      still UNKNOWN, and now points at the item somebody is actually going to seal.

    The third case — a rafter-framed roof that authors no row — is an **UNKNOWN with the
    authoring hint**, and pointedly NOT an item of its own. ``lateral_uplift`` is a retired
    kind: nothing registers it any more, so minting one would produce exactly the bare
    "no calculation is registered for this kind" record ``engineering/deferred.py``'s own
    docstring calls true and useless. A roof nobody has read the table for is a roof nobody
    has read the table for — the finding says so and says which two documents to open.
    """
    from typehaus.engineering import item_id

    out: list[Finding] = []
    for roof in sorted(ctx.model.roofs, key=lambda r: r.tag):
        if not any(member.category == "rafter" for member in roof.members):
            out.append(_engineered(
                ctx, "structural.uplift_capacity", item_id("rafter", roof.tag),
                f"the uplift connection schedule over {roof.tag} is covered joint by joint "
                f"(structural.uplift_path_coverage) but its CAPACITY is not evaluated: the "
                f"roof resolves no rafter or truss member, so IRC Table R802.11 — which is "
                f"indexed by a truss span and spacing — does not describe it, and the "
                f"uplift REACTIONS are part of the component design its fabricator seals",
                (roof.tag,), code="IRC R802.11 / R802.10.2",
                fix=f"seal `rafter/{roof.tag}` in engineering.toml — its deliverable "
                    f"covers the uplift reactions and the connector schedule under them"))
            continue

        out.extend(_published_uplift_findings(ctx, roof, _authored_uplift(ctx, roof.tag)))
    return out


def _authored_uplift(ctx: CheckContext, tag: str) -> tuple:
    """The ``PublishedCapacity`` rows off the AUTHORED element, as ``snow.py`` reads spans."""
    source = ctx.plan.by_tag(tag) if ctx.plan is not None else None
    return tuple(getattr(source, "published_uplift", ()) or ())


def _published_uplift_findings(ctx: CheckContext, roof, published: tuple) -> list[Finding]:
    """One finding per authored joint, demand from R802.11 and capacity from the row.

    **The demand is looked up, not computed, and that is the point.** R802.11 publishes a
    required resistance per connection for exactly the five inputs a roof has — exposure,
    spacing, span, ultimate wind speed and whether the pitch reaches 5:12. A reviewer reads
    the same cell. Where any of those falls outside the table the answer is UNKNOWN naming
    the lookup, never the nearest cell.
    """
    rafters = [member for member in roof.members if member.category == "rafter"]
    site = getattr(getattr(ctx.plan, "project", None), "site", None)
    exposure = getattr(site, "wind_exposure", None)
    speed = getattr(site, "design_wind_speed_mph", None)
    # `snow.py` derives the spacing the rafter-span row is indexed by; R802.11 is indexed
    # by the same number, and two derivations of one spacing would drift.
    from typehaus.checks.structural.snow import _spacing_in

    spacing_in = round(_spacing_in(roof, rafters), 1) if rafters else None
    element = ctx.plan.by_tag(roof.tag) if ctx.plan is not None else None
    span_ft = _roof_span_ft(roof, rafters, element)
    pitch = _pitch_rise_per_12(element)

    missing = [name for name, value in (("wind exposure", exposure),
                                        ("design wind speed", speed),
                                        ("rafter spacing", spacing_in),
                                        ("roof span", span_ft),
                                        ("roof pitch", pitch)) if value is None]
    demand_lb = None if missing else uplift_connection_force_lb(
        exposure, spacing_in, span_ft, speed, pitch)

    if demand_lb is None:
        why = (f"the model does not declare {', '.join(missing)}" if missing else
               f"no IRC Table R802.11 row reaches exposure {exposure}, "
               f"{spacing_in:g} in o.c., a {span_ft:.1f} ft span at {speed:g} mph")
        return [_advisory_unknown(
            f"roof {roof.tag} authors a published uplift capacity but its DEMAND cannot be "
            f"read: {why}", (roof.tag,))]

    if not published:
        # No row authored. ``graded_against_published_capacity`` owns this sentence already —
        # it is the same "nothing authored" UNKNOWN every published-table check gives — and
        # crucially it names no engineering item, which is what keeps the retired
        # ``lateral_uplift`` kind retired.
        return [graded_against_published_capacity(
            "structural.uplift_capacity", f"the uplift connections over {roof.tag}",
            (roof.tag,), demand_lb, None, None,
            fix=f"author Roof.published_uplift on {roof.tag}: IRC Table R802.11 requires "
                f"{demand_lb:,.0f} lb per connection here, and each connector's own "
                f"published allowable is the other half of the read")]

    out: list[Finding] = []
    for row in published:
        out.append(graded_against_published_capacity(
            "structural.uplift_capacity",
            _joint_subject(roof.tag, row),
            (roof.tag,), demand_lb, row, row.member,
            spacing_in=spacing_in, wind_speed_mph=speed, exposure=exposure,
            fix="re-read IRC Table R802.11 and the connector's own allowable at this "
                "roof's condition, and re-author Roof.published_uplift"))
    out.append(Finding(
        severity=Severity.WARN, check_id="structural.uplift_capacity", result=Result.PASS,
        message=(f"[advisory, not engineering] {roof.tag}'s uplift demand is a published "
                 f"read: {demand_lb:,.0f} lb per connection at exposure {exposure}, "
                 f"{spacing_in:g} in o.c., {span_ft:.0f} ft span, {speed:g} mph, pitch "
                 f"{pitch:g}:12 — {R802_11_CITATION}. Conditions this engine does not "
                 f"check: {R802_11_CONDITIONS}"),
        element_tags=(roof.tag,)))
    return out


def _joint_subject(tag: str, row) -> str:
    """"the H2.5A at RF-HOUSE's eave tie" — the row names which joint it is for.

    A ``PublishedCapacity.table`` on a roof leads with the joint ("the eave tie; H2.5A,
    ...") because one roof authors several and a finding that said only "H2.5A at RF-HOUSE"
    would not say which of them. Falls back to the part alone where a row names no joint.
    """
    joint = row.table.split(";")[0].strip() if ";" in row.table else ""
    if joint.lower().startswith("the "):
        joint = joint[4:]
    return f"the {row.member} at {tag}'s {joint}" if joint else f"the {row.member} at {tag}"


def _advisory_unknown(message: str, tags: tuple) -> Finding:
    return Finding(severity=Severity.WARN, check_id="structural.uplift_capacity",
                   result=Result.UNKNOWN, message=message, element_tags=tags)


def _roof_span_ft(roof, rafters, element) -> float | None:
    """The roof's eave-to-eave SPAN, which is what R802.11 is indexed by.

    Not the rafter run and not its sloped length: the table's "roof span" is the building
    dimension the roof covers, so a gable's two runs are one span. Taken as the rafters' own
    plan extent ACROSS the ridge, which needs no gable-vs-shed classification — a shed's
    single slope and a gable's two give the right answer from the same measurement, and a
    roof whose two runs are unequal is measured rather than assumed symmetric.
    """
    if not rafters:
        return None
    ridge = (getattr(element, "ridge_direction", None) or "").strip().lower()
    if ridge not in ("x", "y"):
        return None
    # The ridge runs along one axis, so the span is the extent along the OTHER one.
    axis = 0 if ridge == "y" else 1
    values = [point[axis] for member in rafters for point in (member.p0, member.p1)]
    if not values:
        return None
    return (max(values) - min(values)) / _M_PER_FT


def _pitch_rise_per_12(element) -> float | None:
    """Rise per 12 of run, off the AUTHORED roof — ``ResolvedRoof`` carries no pitch."""
    pitch = getattr(element, "pitch", None)
    rise, run = getattr(pitch, "rise", None), getattr(pitch, "run", None)
    if rise is None or not run:
        return None
    return float(rise) * 12.0 / float(run)
