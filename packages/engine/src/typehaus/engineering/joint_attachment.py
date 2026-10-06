"""Installed axial strap capacity and the wood/deck attachment on each side."""

import math

from typehaus.engineering.blocking_geometry import nailing_margins, top_at
from typehaus.engineering.item import LimitState
from typehaus.engineering.nail_yield import nail_single_shear_lb
from typehaus.quantities import M_PER_IN
from typehaus.resolve.roof_geometry import roof_height_at

# LSTA24's outermost hole, from the strap centre. Field-verify on the delivered strap with
# the six-outer-hole inset; neither is printed in the catalog.
STRAP_LAST_NAIL_IN = 11.4375
STRAP_NAIL_ROW_HALF_WIDTH_IN = 0.5
STRAP_NAIL_LENGTH_IN = 2.5
STRAP_MINIMUM_END_DISTANCE_IN = 2.375
STRAP_MINIMUM_EDGE_DISTANCE_IN = 0.75
# The SPF/HF column of Simpson's LSTA table (C-C-2021 p.269): LSTA24 1,235 lb in both
# columns, and the 12-nail LSTA15 955 lb SPF/HF, so 1,235 x 12/18 = 823 lb never
# overstates a 12-nail group in SPF.
MINIMUM_STRAP_WOOD_SPECIFIC_GRAVITY = 0.42
FACE_TOLERANCE_M = 1e-4
MAXIMUM_CREDITED_BOUNDARY_NAIL_SPACING_IN = 6.0
#: NDS Table 2.3.2, wind: the load this transfer carries.
WIND_LOAD_DURATION = 1.6


def installed_strap_capacity(delivery, rated_capacity):
    capacity = rated_capacity
    recipe = delivery.joint_nailing
    if capacity is not None and recipe is not None:
        capacity *= min(recipe.strap_nails_each_end / recipe.rated_strap_nails_each_end, 1.0)
    return capacity


def _gravity(ctx, tag):
    material = ctx.plan.library.material(tag) if tag else None
    return getattr(material, "specific_gravity", None)


def _backing(ctx, roof, recipe, centre, sign, index, across):
    """The first blocking member that seats this strap leg's whole nail group."""
    for block in roof.members:
        gravity = _gravity(ctx, block.material)
        if (block.category != "blocking" or gravity is None
                or gravity < MINIMUM_STRAP_WOOD_SPECIFIC_GRAVITY):
            continue
        fits = True
        for offset in (recipe.nail_group_inset.meters, STRAP_LAST_NAIL_IN * M_PER_IN):
            for side in (-1, 1):
                point = list(centre)
                point[across] += sign * offset
                point[index] += side * STRAP_NAIL_ROW_HALF_WIDTH_IN * M_PER_IN
                end, edge = nailing_margins(block, point)
                top = top_at(block, point)
                if (end < max(recipe.minimum_end_distance.meters,
                              STRAP_MINIMUM_END_DISTANCE_IN * M_PER_IN) - FACE_TOLERANCE_M
                        or edge < max(recipe.minimum_edge_distance.meters,
                                      STRAP_MINIMUM_EDGE_DISTANCE_IN * M_PER_IN)
                        or top is None
                        or abs(top - roof_height_at(roof, point)) > FACE_TOLERANCE_M
                        or top - block.z0_m < STRAP_NAIL_LENGTH_IN * M_PER_IN):
                    fits = False
        if fits:
            return block, gravity
    return None, None


def joint_attachment_rows(ctx, rows, element, joints, along, demand):
    delivery = element.diaphragm.delivers_to
    recipe = delivery.joint_nailing
    if recipe is None:
        rows.missing.append(f"joint attachment for {element.tag}: longitudinal nailing "
                            "members and their installed fastening schedule")
        return
    gravity = _gravity(ctx, recipe.material)
    if gravity is None or gravity < MINIMUM_STRAP_WOOD_SPECIFIC_GRAVITY:
        rows.missing.append(f"joint attachment for {element.tag}: {recipe.material} "
                            "nailing wood with published specific gravity >=0.42")
    if not recipe.fastening or not recipe.source:
        rows.missing.append(f"joint attachment for {element.tag}: deck and strap fastening basis")
    if not 0 < recipe.deck_nail_spacing.inches <= MAXIMUM_CREDITED_BOUNDARY_NAIL_SPACING_IN:
        rows.missing.append(f"joint attachment for {element.tag}: deck nailing at no more "
                            "than 6in for the credited row")
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
            block, wood = (_backing(ctx, roof, recipe, centre, sign, index, across)
                           if roof is not None else (None, None))
            if block is None:
                rows.missing.append(f"{joint.tag}: {tag} longitudinal nailing member with "
                                    "deck contact, full nail penetration and end/edge distances")
                continue
            deck = _deck(ctx, tag)
            if deck is None:
                rows.missing.append(f"{joint.tag}: {tag}'s declared diaphragm sheathing layer "
                                    "with a thickness and a published specific gravity")
                continue
            thickness_in, deck_gravity = deck
            main_in = recipe.deck_nail_length.inches - thickness_in
            z, mode = nail_single_shear_lb(recipe.deck_nail_diameter.inches, thickness_in,
                                           main_in, deck_gravity, wood,
                                           recipe.deck_nail_fyb_psi)
            # ONE row credited of the declared rows: the other adds nails, not capacity here.
            usable_in = block.length_m / M_PER_IN - 2 * recipe.deck_edge_distance.inches
            nails = math.ceil(usable_in / recipe.deck_nail_spacing.inches - 1e-6) + 1
            rows.states.append(LimitState(
                f"{joint.tag} {tag} nailer into deck", demand,
                nails * z * WIND_LOAD_DURATION, "lb",
                f"{recipe.source}; {nails} nails in one row over {usable_in:.3f}in at "
                f"{recipe.deck_nail_spacing.inches:g}in, NDS 2018 12.3.1 Z = {z:.2f} lb "
                f"(mode {mode}: {recipe.deck_nail_diameter.inches:g}in nail, "
                f"{thickness_in:g}in deck G={deck_gravity:.2f}, {main_in:g}in into G={wood:.2f}) "
                f"x C_D {WIND_LOAD_DURATION}; {recipe.fastening}. Across-joint share plus the "
                "larger of the two readings of the same couple"))


def _deck(ctx, tag):
    """(thickness in, specific gravity) of the roof's declared diaphragm sheathing."""
    roof = ctx.plan.by_tag(tag)
    spec = getattr(roof, "diaphragm", None)
    assembly = ctx.plan.library.assembly(getattr(roof, "assembly", "") or "")
    layer = next((ly for ly in getattr(assembly, "layers", ())
                  if spec is not None and ly.name == spec.sheathing_layer), None)
    gravity = _gravity(ctx, layer.material_ref) if layer is not None else None
    if layer is None or gravity is None:
        return None
    return layer.thickness.inches, gravity
