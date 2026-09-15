"""Post bases, their cast-in anchors, and the beam ends that land on posts.

**The predicates here are extracted, not rewritten.** Every guard below carried a written
reason in ``takeoff/uplift_joints.py`` and each is load-bearing: the size gate stands
*before* the ``covered`` test because ``tags_covered_by`` returns the concrete pier as well
as the wood post on it; ``within_wall`` is excused only for a post whose joint is *not*
already covered, because the breezeway's canopy columns stand in a stud line **and** on
authored bases over cast piers; the beam/post rule matches pairwise rather than by tag,
because a post-only test hands the roof beams' straps to the floor beams under them; and a
squash block bears and does nothing else. Reordering any of them changes a count.

What is new is only the shape of the answer: these functions return the *joints*, and the
row builders in ``takeoff/uplift_joints.py`` group them. The rule is one rule.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_POST_BASE,
    structural_hardware_catalog,
)
from typehaus.hardware.config import UpliftTieRules
from typehaus.joints.authored import (
    authored_joints,
    tags_covered_by,
    unanchored_post_tags,
)
from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Beam, Post
from typehaus.resolve.assembly_material import (
    assembly_structure_material,
    solid_material_ref,
)
from typehaus.resolve.model import ResolvedModel


def catalogued_post_sizes() -> set:
    return {nominal for item in structural_hardware_catalog()
            if item.role == ROLE_POST_BASE for nominal in item.fits_nominal}


def posts(model: ResolvedModel) -> list:
    return [(storey.tag, element) for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if isinstance(element, Post)]


def is_squash_block(post: Post, rules: UpliftTieRules) -> bool:
    """Is this ``Post`` a short block filling a bay, rather than a column?

    Asked of the height, because that is the only thing that separates them: both are a 4x4
    on concrete with the same section and the same bearing. A post with no authored height
    stands its storey and is a column.
    """
    return (post.height is not None
            and post.height.feet <= rules.blocking_max_height_ft)


def bears_on_concrete(model: ResolvedModel, post: Post) -> bool:
    """Is the thing this post declares it stands on a concrete pour?

    Asked of the *support*, through the same ``solid_material_ref`` /
    ``assembly_structure_material`` pair the section hatch and the glTF palette use, so a
    footing filed as concrete on the drawing is concrete here. A support with neither a
    solid nor a wall — catlin's case is ``FS-SG-PORCH``, the porch deck two balcony pillars
    stand on — is framing, and the answer is no.
    """
    support = post.supported_by
    if not support:
        return False
    for solid in model.solids:
        if solid.tag == support:
            return solid_material_ref(model.plan, solid) == "concrete"
    for wall in model.walls:
        if wall.tag == support:
            return assembly_structure_material(
                model.plan, getattr(wall, "assembly", None)) == "concrete"
    return False


def post_base_joints(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """``(storey, post)`` for every wood post that takes a derived standoff base.

    Three conditions are deliberately out of reach of this rule, and each is a real one
    rather than a rounding decision:

    * a post inside a wall (``within_wall``) is developed by the wall's own plates and studs,
      which the SP tie already bills — a base under it would be a second connection at a
      joint that already has one;
    * a post with no ``supported_by`` has nothing declared to fasten a base to;
    * a concrete column is not a section this catalog stocks a wood base for;
    * a post whose joint is already made another way — an authored ``POST_BASE`` *or* an
      authored ``TENSION_TIE``;
    * a **squash block** — a post under ``blocking_max_height_ft`` — bears and does nothing
      else. Buying it a base would be the same error the tie-plate rule makes on a sill:
      hardware at a joint whose connection is already made another way.

    All four are reported by ``structural.uplift_path_coverage`` rather than being quietly
    absent from the order.
    """
    stocked = catalogued_post_sizes()
    # A TENSION_TIE covers the joint too. A post bearing wood-on-wood does not take a
    # stirrup — it is held DOWN to the framing instead — so a set that only knew POST_BASE
    # would see no connector at PT-SG-BR2/BF2 and derive two ABU66 for joints that already
    # have their part. Same set as ``checks/structural/uplift_path.py``'s; they must agree.
    covered = tags_covered_by(
        model, frozenset({ConnectorKind.POST_BASE, ConnectorKind.TENSION_TIE}))
    found = []
    for storey, post in posts(model):
        if post.tag in covered or post.within_wall or not post.supported_by:
            continue
        if post.size not in stocked or is_squash_block(post, rules):
            continue
        found.append((storey, post))
    return found


def post_base_anchor_joints(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """``(storey, post)`` for every post base — authored or derived — landing on concrete.

    An ABU is a stirrup with a hole in it; Simpson's published uplift and lateral values are
    taken *through* a 5/8 in anchor the base does not include.

    This rule counts posts rather than bases because it is the JOINT that decides whether a
    bolt is needed. ``StructuralHardware.requires_role`` — the mechanism that already puts an
    S-5! clamp under every CanDuit ring — cannot express it: that field is a flat property of
    the part, and it would bill a cast-in bolt for any base landing on
    FRAMING rather than on a pour. A base on framing is through-bolted or screwed to it, and
    those fixings are inside the framing rate exactly as a joist hanger's nails are.
    (``PT-SG-BR2``/``BF2``'s ABU66SS standing on the porch DECK were the worked example
    until 2026-09-03, when both pillars went to wood-to-wood bearing with a ``TENSION_TIE``
    and stopped taking a base at all. The rule they motivated is unchanged.)

    Both halves of the population are counted here: the bases catlin authors as
    ``Connector`` elements *and* the ones :func:`post_base_joints` derives. They are one
    order.
    """
    covered = tags_covered_by(model, frozenset({ConnectorKind.POST_BASE}))
    unanchored = unanchored_post_tags(model)
    stocked = catalogued_post_sizes()
    found = []
    for storey, post in posts(model):
        # ``within_wall`` is geometric: it says the framer cuts the plates around this post.
        # It does NOT say the base joint is developed by the wall — the breezeway's canopy
        # columns stand in the screen panel's stud line *and* on authored ABU66SS bases over
        # cast piers. Key the exemption on the joint instead, or authoring the geometric
        # field deletes those bolts from the order.
        if (post.within_wall and post.tag not in covered) or is_squash_block(post, rules):
            continue
        # The size gate comes FIRST, and it applies to the authored half too. The
        # breezeway's four ABU66SS ``Connector`` elements name both members of the joint —
        # ``connects=("PT-BW-1", "PR-BW-1")`` — so ``tags_covered_by`` returns the concrete
        # PIER as well as the wood post on it, and a rule that trusted that set billed four
        # anchor bolts for four sonotubes that have no base and want none.
        if post.size not in stocked:
            continue
        # A base is present if the plan authored one or ``post_base_joints`` can derive one;
        # the anchor follows the base, so the two populations are unioned rather than
        # chosen between.
        if not (post.tag in covered or post.supported_by):
            continue
        if not bears_on_concrete(model, post):
            continue
        # A base the plan declares bearing-only has no bolt to buy: download crosses the
        # plate into the pour, and the joint gives up the uplift and lateral the bolt buys.
        if post.tag in unanchored:
            continue
        found.append((storey, post))
    return found


def post_beam_strap_joints(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """``(storey, beam, post)`` for every beam end that lands on a wood post.

    ``Beam.bearing_refs`` already names the post, so this counts declarations rather than
    searching for coincident geometry. One strap per beam end by default, not the matched
    pair: a pair only fits where the beam *stops* at the post, and a beam that runs past its
    post has one reachable face — the same lesson ``KneeBraceRules`` learned when a pair rule
    billed twelve unbuildable braces. A joint that wants two authors the second by hand.
    """
    stocked = catalogued_post_sizes()
    by_tag = {post.tag: post for _storey, post in posts(model)}
    # A joint is covered only when one authored connector names BOTH its members. Matching
    # on either alone credits the wrong joint: the breezeway straps its two ROOF beams to
    # PT-BW-1..4, and a post-only test would hand those straps to the two FLOOR beams landing
    # on the same four posts, which carry nothing at all.
    # JOIST_HANGER is here for the beam a author HANGS off a post's FACE rather than landing
    # on its top — catlin's BM-BW-SCSILL on PT-BW-CW/-CNW, where a 6x6 is wider than the seat
    # beam beside it and there is nowhere to land. A face-mount hanger is nailed into both
    # members, so it is the tie at that joint; the generic strap this module derives is a
    # knee brace (ROLE_BEAM_HOLD_DOWN -> KBS1Z) and would not even be buildable in the joist
    # plane. What the hanger does NOT settle is its uplift RATING: catalog `allowable` is
    # None for HU28-2Z, which means nobody has looked it up, not that it is zero.
    covered = authored_joints(model, frozenset({ConnectorKind.HOLD_DOWN,
                                                ConnectorKind.POST_CAP,
                                                ConnectorKind.HURRICANE_TIE,
                                                ConnectorKind.JOIST_HANGER}))
    found = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Beam):
                continue
            for ref in element.bearing_refs:
                post = by_tag.get(ref)
                if post is None or post.size not in stocked:
                    continue
                if frozenset({element.tag, post.tag}) in covered:
                    continue
                found.append((storey.tag, element, post))
    return found
