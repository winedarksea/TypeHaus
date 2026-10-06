"""End angles and nails for the declared, resolved roof blocking and joint nailers."""

import math
from collections import Counter

from typehaus.hardware.catalog import (
    ROLE_DIAPHRAGM_BLOCKING_END_TIE,
    hardware_by_model,
    hardware_for_role,
)
from typehaus.model import Roof
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.roof_diaphragm import (
    DIAPHRAGM_BLOCK_CONNECTION,
    GEOMETRY_TOLERANCE_M,
    JOINT_NAILER_CONNECTION,
    PANEL_EDGE_BLOCK_CONNECTION,
)
from typehaus.takeoff.hardware_row import hardware_row

CONNECTOR_NAILS_PER_ANGLE = 6
LAMINATION_END_NAILS = 2
LAMINATION_END_INSET_M = 0.0508
DECK_NAIL = "8d common 0.131x2.5"


def _backs_joint_station(model, roof, member, tags):
    axis = 0 if roof.ridge_direction == "x" else 1
    across = 1 - axis
    for tag in tags:
        connector = model.plan.by_tag(tag)
        if connector is None:
            continue
        position = connector.position.xy_m
        if (member.p0[axis] - GEOMETRY_TOLERANCE_M <= position[axis]
                <= member.p1[axis] + GEOMETRY_TOLERANCE_M
                and abs(position[across] - member.p0[across])
                <= member.plan_width_m / 2 + GEOMETRY_TOLERANCE_M):
            return True
    return False


def _deck_nail_count(member, recipe):
    usable = member.length_m - 2 * recipe.deck_edge_distance.meters
    # Exact multiples of spacing should not gain a nail from floating-point roundoff.
    return recipe.deck_nail_rows * (
        math.ceil((usable - GEOMETRY_TOLERANCE_M) / recipe.deck_nail_spacing.meters) + 1)


def _lamination_nail_count(member, recipe):
    """Two nails near each end of a multi-ply nailer and the spacing between."""
    if cross_section(recipe.stock).plies < 2:
        return 0
    between = member.length_m - 2 * LAMINATION_END_INSET_M
    return 2 * LAMINATION_END_NAILS + max(
        0, math.ceil((between - GEOMETRY_TOLERANCE_M) / recipe.lamination_spacing.meters) - 1)


def _panel_recipes(model):
    """Each roof's panel-edge recipe, by the tag its block keys carry."""
    return {element.tag: element.diaphragm.panel_edge_blocking
            for element in model.plan.all_elements()
            if isinstance(element, Roof) and element.diaphragm
            and element.diaphragm.panel_edge_blocking}


def diaphragm_attachment_rows(model):
    counts = Counter()
    nails = Counter()
    owners = {}
    for element in model.plan.all_elements():
        if (isinstance(element, Roof) and element.diaphragm
                and element.diaphragm.delivers_to
                and element.diaphragm.delivers_to.joint_nailing):
            for tag in element.diaphragm.delivers_to.joint_refs:
                owners[tag] = element.diaphragm.delivers_to.joint_nailing
    panels = _panel_recipes(model)
    for roof in model.roofs:
        element = model.plan.by_tag(roof.tag)
        spec = element.diaphragm if isinstance(element, Roof) else None
        for member in roof.members:
            if member.connection == DIAPHRAGM_BLOCK_CONNECTION and spec:
                recipe = next((r for r in spec.collector_blocking
                               if r.collector in member.child_key), None)
                if recipe:
                    counts[(recipe.end_tie, roof.storey)] += 2 * recipe.end_ties_each_end
                delivery = spec.delivers_to
                if (delivery and delivery.joint_nailing
                        and _backs_joint_station(model, roof, member, delivery.joint_refs)):
                    # The end straps reuse collector blocks as their south nailers.
                    nails["deck"] += _deck_nail_count(member, delivery.joint_nailing)
            if member.connection == JOINT_NAILER_CONNECTION:
                recipe = next((recipe for tag, recipe in owners.items()
                               if member.child_key.startswith(f"joint-nailer-{tag}-")), None)
                if recipe:
                    counts[(recipe.end_tie, roof.storey)] += 2
                    nails["deck"] += _deck_nail_count(member, recipe)
                    nails["lamination"] += _lamination_nail_count(member, recipe)
            if member.connection == PANEL_EDGE_BLOCK_CONNECTION:
                owner = member.child_key.removeprefix("panel-block-").rsplit("-", 2)[0]
                recipe = panels.get(owner)
                if recipe:
                    nails["toenail"] += 2 * recipe.toenails_each_end
        if spec and spec.delivers_to and spec.delivers_to.joint_nailing:
            recipe = spec.delivers_to.joint_nailing
            nails["strap"] += len(spec.delivers_to.joint_refs) * 2 * recipe.strap_nails_each_end
    rows = [hardware_row(
        hardware_for_role(ROLE_DIAPHRAGM_BLOCKING_END_TIE),
        scope="diaphragm blocking end angles", count=count,
        part_number=part, by_storey={storey: count},
        basis="one angle per collector-block or longitudinal nailer end; "
              "six 0.148x1.5in HDG nails per LS30Z, three per leg, direct to side-grain wood")
            for (part, storey), count in sorted(counts.items())]
    for part, count, scope, basis in (
        ("0.148x1.5 connector nail", sum(counts.values()) * CONNECTOR_NAILS_PER_ANGLE,
         "diaphragm blocking angle nails", "six per resolved LS30Z end angle, three per leg"),
        # One part, one bid line; the basis keeps the three uses apart.
        (DECK_NAIL, nails["deck"] + nails["lamination"] + nails["toenail"],
         "diaphragm 8d nails",
         f"{nails['deck']} deck-to-nailer along the declared rows (shared collector blocks "
         f"included), {nails['lamination']} laminating the two-ply nailers, "
         f"{nails['toenail']} panel-edge block toenails"),
        ("10d short common 0.148x2.5", nails["strap"], "diaphragm joint strap nails",
         "six outermost nails per leg; 12 per LSTA24, reduced installed capacity"),
    ):
        if count:
            rows.append(hardware_row(hardware_by_model(part), scope=scope, count=count,
                                     part_number=part, basis=basis))
    return rows
