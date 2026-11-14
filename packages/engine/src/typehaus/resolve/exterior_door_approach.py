"""Cut decking back locally around a door approach; never cut its joists or a slab."""
from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.resolve.geometry import opening_center, wall_frame


def clear_exterior_door_approaches(model):
    floors = {floor.tag: floor for floor in model.floors}
    openings = []
    for opening in model.openings:
        assembly = opening.doorway
        placement = assembly.exterior_placement if assembly else None
        # An approach that rests on its landing (``ApproachBearing``) cuts back only what its
        # bridge asked for: the deck clear of the pan's drip, or off the member a pad sits on.
        bearing = placement.specification.approach_bearing if placement else None
        report = (placement.installation_report or {}) if placement else {}
        if (placement is None
                or placement.sill_design_status not in ("SCHEMATIC", "CATALOG_DESIGN")
                or (bearing is not None and report.get("deck_cut_depth_m") is None)):
            openings.append(opening)
            continue
        sign = placement.outward_sign
        landing = assembly.adjacent_floors[0 if sign < 0 else 1]
        floor = floors.get(landing.deck_tag) if landing else None
        if floor is None:
            openings.append(opening)
            continue
        wall = model.wall(opening.host_wall)
        center = opening_center(wall, opening)
        _, tangent, normal, _ = wall_frame(wall)
        catalog = placement.specification.catalog_installation
        design = placement.specification.sill_design
        if bearing is not None:
            front, clearance = report["deck_cut_depth_m"], 0.0
        else:
            nose_name = "ariddek-stock-profile-trim" if catalog else "approach-drip-nosing"
            nose = next(s for s in placement.sections if s.name == nose_name)
            front = max(sign * n for n, _ in nose.polygon_m)
            clearance = placement.specification.drainage_gap.meters
        half = opening.width_m / 2 + (
            placement.specification.drainage_gap.meters if catalog
            else design.side_clearance.meters)
        inner = sign * placement.frame_inner_m
        ring = tuple((center[0] + tangent[0] * along + normal[0] * sign * depth,
                      center[1] + tangent[1] * along + normal[1] * sign * depth)
                     for along, depth in ((-half, inner), (half, inner),
                                          (half, front + clearance), (-half, front + clearance)))
        cover = Polygon(floor.deck_outline, holes=list(floor.deck_voids))
        notch = Polygon(ring)
        if cover.intersection(notch).area <= 1e-10:
            openings.append(opening)
            continue
        remaining = cover.difference(notch)
        if remaining.geom_type != "Polygon" or remaining.is_empty:
            assembly = replace(assembly, conflicts=(*assembly.conflicts,
                "door approach cutback would disconnect the exterior decking"))
        else:
            floors[floor.tag] = replace(floor,
                deck_outline=tuple(remaining.exterior.coords)[:-1],
                deck_voids=tuple(tuple(h.coords)[:-1] for h in remaining.interiors))
            if bearing is None:
                assembly = replace(assembly, unknown=(*assembly.unknown,
                    "landing decking cut back locally for open pan discharge; "
                    "board-end blocking and approach support need a structural detail"))
        openings.append(replace(opening, doorway=assembly))
    model.floors = [floors[f.tag] for f in model.floors]
    model.openings = openings
