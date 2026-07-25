"""Recover furniture groups — a table and the chairs tucked under it — from clearance zones.

A recommended clearance is a planning zone the designer wants kept clear *of intruders*, but
some objects are the zone's whole reason to exist: a dining chair standing in its table's
chair-use zone is the arrangement working, and a desk chair in the desk's pull-out zone is
the desk being usable. Without a notion of a group the conflict check reports the correct
arrangement, which trains the reader to ignore it.

Nothing in a house source file declares "these chairs belong to that table", and requiring it
would make every furniture drop a two-step edit. Instead the *product type* declares what its
zone accommodates (``ClearanceZone.occupant_types``), and the group is resolved from geometry:
the zone owner anchors the group, and every placeable of a listed type standing in the zone
joins it. A sofa parked in the dining clearance is not a listed type, stays ungrouped, and
still reports — which is the conflict worth reading.

Groups are formed only from RECOMMENDED zones. A code-required clearance (an electrical
working space, an accessible approach) is never "for" whatever happens to be standing in it,
so it must never be silenced by furniture arrangement.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from shapely.geometry import Polygon

from typehaus.resolve.model import ResolvedCanvasObject, Ring

# Shapely areas are exact for these polygons; this only rejects the zero-area touch of two
# objects sharing an edge, which is adjacency rather than occupancy.
_OCCUPANCY_AREA_TOLERANCE_M2 = 1e-8


@dataclass(frozen=True)
class PlacementGroupAnchorZone:
    """One resolved recommended-clearance zone that names the types it accommodates."""

    anchor_uid: str
    anchor_tag: str
    storey: str
    zone_polygon: Ring
    occupant_types: frozenset[str]


def assign_placement_groups(
    objects: list[ResolvedCanvasObject],
    anchor_zones: list[PlacementGroupAnchorZone],
) -> list[ResolvedCanvasObject]:
    """Re-stamp ``objects`` with the group each belongs to; order and identity are preserved.

    An anchor only joins a group once it has actually claimed an occupant — a dining table
    standing on its own is not a group of one, and marking it as such would tell a UI there
    is a set to drag when there is not.
    """
    if not anchor_zones:
        return objects
    group_tag_by_uid = _claim_occupants(objects, anchor_zones)
    if not group_tag_by_uid:
        return objects
    claimed_anchor_tags = set(group_tag_by_uid.values())
    for anchor in anchor_zones:
        if anchor.anchor_tag in claimed_anchor_tags:
            group_tag_by_uid[anchor.anchor_uid] = anchor.anchor_tag
    return [replace(item, placement_group=group_tag_by_uid[item.uid])
            if item.uid in group_tag_by_uid else item
            for item in objects]


def _claim_occupants(
    objects: list[ResolvedCanvasObject],
    anchor_zones: list[PlacementGroupAnchorZone],
) -> dict[str, str]:
    """Occupant uid -> anchor tag, resolving overlapping zones by greatest occupied area.

    A chair standing between two tables can only belong to one set; awarding it to the zone it
    sits deepest inside matches what a reader sees on the plan, and keeps the answer
    independent of authoring order.
    """
    claim_by_uid: dict[str, tuple[float, str]] = {}
    for anchor in anchor_zones:
        zone_shape = Polygon(anchor.zone_polygon)
        if zone_shape.is_empty or not zone_shape.is_valid:
            continue
        for item in objects:
            if (item.storey != anchor.storey or item.uid == anchor.anchor_uid
                    or item.type_ref not in anchor.occupant_types):
                continue
            occupied_area = zone_shape.intersection(Polygon(item.footprint)).area
            if occupied_area <= _OCCUPANCY_AREA_TOLERANCE_M2:
                continue
            best = claim_by_uid.get(item.uid)
            if best is None or occupied_area > best[0]:
                claim_by_uid[item.uid] = (occupied_area, anchor.anchor_tag)
    return {uid: anchor_tag for uid, (_area, anchor_tag) in claim_by_uid.items()}
