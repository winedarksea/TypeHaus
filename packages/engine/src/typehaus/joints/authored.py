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


def authored_connectors(model: ResolvedModel) -> list:
    """Every authored ``Connector`` in the plan."""
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
    for element in authored_connectors(model):
        if element.kind in kinds:
            covered.update(element.connects)
    return covered



def unanchored_post_tags(model: ResolvedModel) -> set:
    """Tags named by an authored POST_BASE that declares ``anchored=False``.

    A bearing-only base takes no cast-in bolt, so :func:`post_base_anchor_rows` must not
    bill one. See ``Connector.anchored`` for what the plan is claiming when it sets this.
    """
    unanchored: set = set()
    for element in authored_connectors(model):
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
    for element in authored_connectors(model):
        if element.kind not in kinds:
            continue
        tags = list(element.connects)
        for index, left in enumerate(tags):
            for right in tags[index + 1:]:
                joints.add(frozenset({left, right}))
    return joints


def hanger_specs(model: ResolvedModel) -> dict[tuple[str, str], str]:
    """Authored part per ``(carrier tag, floor tag)`` — see ``Connector.hanger_spec_pair``."""
    specs: dict[tuple[str, str], str] = {}
    for element in authored_connectors(model):
        pair = element.hanger_spec_pair(model.plan)
        if pair is not None and element.size:
            specs[pair] = element.size
    return specs


def hanger_part(connection, specs: dict[tuple[str, str], str]):
    """``(role, catalog item, part number)`` for one hung end.

    An authored spec for its (carrier, floor) wins and bills under its own catalog role.
    Otherwise the derived family: LSCZ for a stair stringer, LSSR sloped, LUS/LUSZ level by
    the carrier's treatment.
    """
    from typehaus.hardware.catalog import (
        EXPOSURE_DRY,
        EXPOSURE_TREATED,
        ROLE_FACE_MOUNT_JOIST_HANGER,
        ROLE_SCL_FACE_MOUNT_HANGER,
        ROLE_SLOPED_JOIST_HANGER,
        ROLE_STAIR_STRINGER_CONNECTOR,
        hardware_by_model,
        hardware_for_role,
        sized_hanger_model,
        structural_hardware_catalog,
    )

    authored = specs.get((connection.carrier_tag, connection.member_floor))
    if authored is not None and not connection.sloped:
        item = hardware_by_model(authored)
        if item is None:
            raise LookupError(f"authored hanger {authored!r} on {connection.carrier_tag} x "
                              f"{connection.member_floor} is not in the hardware catalog")
        return item.role, item, authored
    if connection.member_category == "stringer":
        item = hardware_for_role(ROLE_STAIR_STRINGER_CONNECTOR)
        return ROLE_STAIR_STRINGER_CONNECTOR, item, item.model
    if connection.sloped:
        item = hardware_for_role(ROLE_SLOPED_JOIST_HANGER)
        return ROLE_SLOPED_JOIST_HANGER, item, item.model
    exposure = EXPOSURE_TREATED if connection.carrier_treated else EXPOSURE_DRY
    # A multi-ply LVL (a floor-opening header) takes the part catalogued for its profile.
    scl = next((item for item in structural_hardware_catalog()
                if item.role == ROLE_SCL_FACE_MOUNT_HANGER
                and connection.member_profile in item.fits_nominal
                and item.exposure in (None, exposure)), None)
    if scl is not None:
        return ROLE_SCL_FACE_MOUNT_HANGER, scl, scl.model
    item = hardware_for_role(ROLE_FACE_MOUNT_JOIST_HANGER, exposure=exposure)
    return (ROLE_FACE_MOUNT_JOIST_HANGER, item,
            sized_hanger_model(item, connection.member_profile))
