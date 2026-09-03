"""The authored-connector guard, and every uplift rule that grades a **joint**.

The seam from ``takeoff/uplift.py`` is not arbitrary: what is left there derives hardware
along a *run* — a tie at every member that seats on a bearing line, a plate every four feet
along a bottom plate — while everything here answers a question about one point where two
named members meet. A
post and what it stands on; a beam end and the post under it; and, first, whether the plan
already authored a ``Connector`` at that point, which is the guard every rule in both files
asks before it bills anything.

The guard is here rather than in ``uplift.py`` so the import runs one way: this module knows
nothing about the run rules, and ``uplift.py`` imports what it needs from here.
"""

from __future__ import annotations

from collections import Counter

from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Beam, Connector, Post
from typehaus.resolve.assembly_material import (
    assembly_structure_material,
    solid_material_ref,
)
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    hardware_for_role,
    hardware_for_role_and_nominal,
    hardware_row,
    structural_hardware_catalog,
)
from typehaus.takeoff.hardware_config import UpliftTieRules

# --- the authored-connector guard ----------------------------------------------------



def _authored_connectors(model: ResolvedModel) -> list:
    return [element for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if isinstance(element, Connector)]


def tags_covered_by(model: ResolvedModel, kinds: frozenset) -> set:
    """Every element tag an authored connector of one of ``kinds`` already names.

    Tag-based rather than geometric on purpose: ``Connector.connects`` is the plan's own
    statement of which members the hardware joins, it is what
    ``emit/draw/roofframingplan.py`` reads for the tie schedule, and it survives a member
    being re-resolved at a slightly different coordinate.
    """
    covered: set = set()
    for element in _authored_connectors(model):
        if element.kind in kinds:
            covered.update(element.connects)
    return covered



def authored_joints(model: ResolvedModel, kinds: frozenset) -> set:
    """Every PAIR of tags one authored connector of ``kinds`` names together.

    The coarser :func:`tags_covered_by` answers "is this element mentioned at all", which is
    the right question for a post base (a post has exactly one) and the wrong one for a
    beam/post joint (a post carries several beams, and they are not all strapped).
    """
    joints: set = set()
    for element in _authored_connectors(model):
        if element.kind not in kinds:
            continue
        tags = list(element.connects)
        for index, left in enumerate(tags):
            for right in tags[index + 1:]:
                joints.add(frozenset({left, right}))
    return joints




# --- rules 2 and 3: post bases, their anchors, and beams landing on posts ---------



def catalogued_post_sizes() -> set:
    return {nominal for item in structural_hardware_catalog()
            if item.role == ROLE_POST_BASE for nominal in item.fits_nominal}


def _posts(model: ResolvedModel) -> list:
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


def post_base_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """A standoff base under every wood post that declares what it bears on.

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
    by_size: dict = {}
    for storey, post in _posts(model):
        if post.tag in covered or post.within_wall or not post.supported_by:
            continue
        if post.size not in stocked or is_squash_block(post, rules):
            continue
        entry = by_size.setdefault(post.size, {"by_storey": Counter(), "tags": []})
        entry["by_storey"][storey] += 1
        entry["tags"].append(post.tag)

    rows = []
    for size in sorted(by_size):
        entry = by_size[size]
        item = hardware_for_role_and_nominal(ROLE_POST_BASE, size)
        by_storey = entry["by_storey"]
        rows.append(hardware_row(
            item, scope="post base", count=int(sum(by_storey.values())), size=size,
            by_storey=dict(sorted(by_storey.items())),
            basis=(f"one per {size} post that declares what it bears on: "
                   + ", ".join(sorted(entry["tags"])))))
    return rows


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


def post_base_anchor_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """The cast-in bolt under every post base — authored or derived — that lands on concrete.

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

    Both halves of the population are counted here: the ten bases catlin authors as
    ``Connector`` elements *and* the ones ``post_base_rows`` derives. They are one order.
    """
    covered = tags_covered_by(model, frozenset({ConnectorKind.POST_BASE}))
    stocked = catalogued_post_sizes()
    by_storey: Counter = Counter()
    tags: list = []
    for storey, post in _posts(model):
        if post.within_wall or is_squash_block(post, rules):
            continue
        # The size gate comes FIRST, and it applies to the authored half too. The
        # breezeway's four ABU66SS ``Connector`` elements name both members of the joint —
        # ``connects=("PT-BW-1", "PR-BW-1")`` — so ``tags_covered_by`` returns the concrete
        # PIER as well as the wood post on it, and a rule that trusted that set billed four
        # anchor bolts for four sonotubes that have no base and want none.
        if post.size not in stocked:
            continue
        # A base is present if the plan authored one or ``post_base_rows`` can derive one;
        # the anchor follows the base, so the two populations are unioned rather than
        # chosen between.
        if not (post.tag in covered or post.supported_by):
            continue
        if not bears_on_concrete(model, post):
            continue
        by_storey[storey] += 1
        tags.append(post.tag)
    if not tags:
        return []
    item = hardware_for_role(ROLE_POST_BASE_ANCHOR)
    return [hardware_row(
        item, scope="post base anchor", count=len(tags),
        by_storey=dict(sorted(by_storey.items())),
        basis=("one per post base landing on concrete (a base on framing is fastened to it "
               "and those fixings are in the framing rate): " + ", ".join(sorted(tags))))]

# --- rule 3: post/beam straps --------------------------------------------------------


def post_beam_strap_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """A strap at every beam end that lands on a wood post.

    ``Beam.bearing_refs`` already names the post, so this counts declarations rather than
    searching for coincident geometry. One strap per beam end by default, not the matched
    pair: a pair only fits where the beam *stops* at the post, and a beam that runs past its
    post has one reachable face — the same lesson ``KneeBraceRules`` learned when a pair rule
    billed twelve unbuildable braces. A joint that wants two authors the second by hand.
    """
    stocked = catalogued_post_sizes()
    posts = {post.tag: post for _storey, post in _posts(model)}
    # A joint is covered only when one authored connector names BOTH its members. Matching
    # on either alone credits the wrong joint: the breezeway straps its two ROOF beams to
    # PT-BW-1..4, and a post-only test would hand those straps to the two FLOOR beams landing
    # on the same four posts, which carry nothing at all.
    covered = authored_joints(model, frozenset({ConnectorKind.HOLD_DOWN,
                                                ConnectorKind.POST_CAP,
                                                ConnectorKind.HURRICANE_TIE}))
    by_storey: Counter = Counter()
    joints: list = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Beam):
                continue
            for ref in element.bearing_refs:
                post = posts.get(ref)
                if post is None or post.size not in stocked:
                    continue
                if frozenset({element.tag, post.tag}) in covered:
                    continue
                by_storey[storey.tag] += rules.straps_per_post_beam_joint
                joints.append(f"{element.tag}->{post.tag}")
    if not joints:
        return []
    item = hardware_for_role(ROLE_BEAM_HOLD_DOWN)
    return [hardware_row(
        item, scope="beam on post", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())),
        basis=(f"{rules.straps_per_post_beam_joint} per beam end landing on a wood post "
               f"({len(joints)} joints: " + ", ".join(sorted(joints)) + ")"))]

