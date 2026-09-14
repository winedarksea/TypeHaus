"""The authored-connector guard: what the plan has already made by hand.

Every derivation in this package asks this first. An authored ``Connector`` is the plan
stating that a joint is made, and a rule that billed one anyway would be the same
double-billing error ``Material.exposed_fastener`` exists to prevent — the sunken garden
and the breezeway author twenty connectors between them.

Two grains, and the difference is load-bearing. :func:`tags_covered_by` asks "is this
element mentioned at all", which is the right question for a post base (a post has exactly
one) and the wrong one for a beam/post joint: a post carries several beams and they are not
all strapped. :func:`authored_joints` is the pairwise answer, and a support stands a rule
down only when one connector names the support and the thing bearing on it *together*.
"""

from __future__ import annotations

from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Connector
from typehaus.resolve.model import ResolvedModel


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



def unanchored_post_tags(model: ResolvedModel) -> set:
    """Tags named by an authored POST_BASE that declares ``anchored=False``.

    A bearing-only base takes no cast-in bolt, so :func:`post_base_anchor_rows` must not
    bill one. See ``Connector.anchored`` for what the plan is claiming when it sets this.
    """
    unanchored: set = set()
    for element in _authored_connectors(model):
        if element.kind is ConnectorKind.POST_BASE and not getattr(element, "anchored", True):
            unanchored.update(element.connects)
    return unanchored


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
