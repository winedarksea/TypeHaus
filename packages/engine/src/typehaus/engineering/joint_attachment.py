"""Installed axial strap capacity and the wood/deck attachment on each side."""

from typehaus.engineering.blocking_geometry import nailing_margins, top_at
from typehaus.engineering.item import LimitState
from typehaus.quantities import M_PER_IN
from typehaus.resolve.roof_geometry import roof_height_at

STRAP_LAST_NAIL_IN = 11.4375
STRAP_NAIL_ROW_HALF_WIDTH_IN = 0.5
STRAP_NAIL_LENGTH_IN = 2.5
STRAP_MINIMUM_END_DISTANCE_IN = 2.375
STRAP_MINIMUM_EDGE_DISTANCE_IN = 0.75
MINIMUM_STRAP_WOOD_SPECIFIC_GRAVITY = 0.50
FACE_TOLERANCE_M = 1e-4
MAXIMUM_CREDITED_BOUNDARY_NAIL_SPACING_IN = 6.0


def installed_strap_capacity(delivery, rated_capacity):
    capacity = rated_capacity
    recipe = delivery.joint_nailing
    if capacity is not None and recipe is not None:
        capacity *= min(recipe.strap_nails_each_end / recipe.rated_strap_nails_each_end, 1.0)
    return capacity


def joint_attachment_rows(ctx, rows, element, joints, along, demand):
    delivery = element.diaphragm.delivers_to
    recipe = delivery.joint_nailing
    if recipe is None:
        rows.missing.append(f"joint attachment for {element.tag}: longitudinal nailing "
                            "members and their installed fastening schedule")
        return
    material = ctx.plan.library.material(recipe.material)
    gravity = getattr(material, "specific_gravity", None)
    if gravity is None or gravity < MINIMUM_STRAP_WOOD_SPECIFIC_GRAVITY:
        rows.missing.append(f"joint attachment for {element.tag}: {recipe.material} "
                            "nailing wood with published specific gravity >=0.50")
    if not recipe.fastening or not recipe.source:
        rows.missing.append(f"joint attachment for {element.tag}: deck and strap fastening basis")
    if not 0 < recipe.deck_nail_spacing.inches <= MAXIMUM_CREDITED_BOUNDARY_NAIL_SPACING_IN:
        rows.missing.append(f"joint attachment for {element.tag}: deck nailing at no more "
                            "than 6in for the credited boundary row")
    if not recipe.continuous_deck:
        rows.missing.append(f"joint attachment for {element.tag}: continuous deck panels "
                            "across the receiving gable for along-joint shear; the axial "
                            "strap rating supplies no transverse shear capacity")
    index = 0 if along == "x" else 1
    across = 1 - index
    roofs = {r.tag: r for r in ctx.model.roofs}
    for joint in joints:
        if joint.size != "LSTA24" or recipe.rated_strap_nails_each_end != 9:
            rows.missing.append(f"{joint.tag}: supported LSTA24 nine-nail-per-end rating")
            continue
        if recipe.strap_nails_each_end != 6 or recipe.nail_group_inset.inches < 4.5:
            rows.missing.append(f"{joint.tag}: six outer nail holes per end, starting >=4.5in "
                                "from the strap centre to clear the gable and wood ends")
            continue
        centre = joint.position.xy_m
        for tag, sign in ((element.tag, -1), (delivery.roof, 1)):
            roof = roofs.get(tag)
            supported = None
            if roof is not None:
                for block in roof.members:
                    if block.category != "blocking" or block.material != recipe.material:
                        continue
                    fits = True
                    for offset in (recipe.nail_group_inset.meters,
                                   STRAP_LAST_NAIL_IN * M_PER_IN):
                        for side in (-1, 1):
                            point = list(centre)
                            point[across] += sign * offset
                            point[index] += side * STRAP_NAIL_ROW_HALF_WIDTH_IN * M_PER_IN
                            end, edge = nailing_margins(block, point)
                            top = top_at(block, point)
                            if (end < max(recipe.minimum_end_distance.meters,
                                          STRAP_MINIMUM_END_DISTANCE_IN * M_PER_IN)
                                    - FACE_TOLERANCE_M
                                    or edge < max(recipe.minimum_edge_distance.meters,
                                                  STRAP_MINIMUM_EDGE_DISTANCE_IN * M_PER_IN)
                                    or top is None
                                    or abs(top - roof_height_at(roof, point)) > FACE_TOLERANCE_M
                                    or top - block.z0_m < STRAP_NAIL_LENGTH_IN * M_PER_IN):
                                fits = False
                    if fits:
                        supported = block
                        break
            if supported is None:
                rows.missing.append(f"{joint.tag}: {tag} longitudinal nailing member with "
                                    "deck contact, full nail penetration and end/edge distances")
                continue
            # Only one 6in boundary row is credited; the detailed two 3in rows provide
            # extra nails without multiplying a tabulated diaphragm capacity.
            length_ft = (supported.length_m - 2 * recipe.deck_edge_distance.meters) / 0.3048
            rows.states.append(LimitState(
                f"{joint.tag} {tag} nailer into deck", demand,
                length_ft * element.diaphragm.unit_shear_asd_plf, "lb",
                f"{recipe.source}; {length_ft:.4f}ft of deck boundary nailing at "
                f"{element.diaphragm.unit_shear_asd_plf:g}plf; {recipe.fastening}. "
                "Across-joint share plus the larger of the two readings of the same couple; "
                "one boundary row credited"))
