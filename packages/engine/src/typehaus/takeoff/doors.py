"""The door-hardware rows of the bill of materials.

For most doors the ``finish-door-*`` lump-sum allowance is defensible — a lockset is a
lockset. For a pocket door it is not: the frame kit *is* the pocket (split studs, head
track, hangers, guides), bought one per door, and which one you buy is decided by the leaf
width, the host wall's depth and the type's ``pocket_frame`` family.

Authored type hardware replaces the generic allowance; doorway components and pocket kits
retain their own procurement paths. ``ResolvedOpening.pocket_run_m`` is non-zero for
exactly the pocket doors, and ``width_m`` is what selects the kit.
"""

from __future__ import annotations

from typehaus.hardware.catalog import pocket_frame_kit
from typehaus.resolve.framing.tables import pocket_wall_is_deep
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

_M_TO_IN = 39.3700787401575


def door_hardware_rows(model: ResolvedModel) -> list[dict]:
    """One frame kit per pocket door, grouped by kit and leaf width.

    A width with no catalogued kit is a real finding, not a blank line: it means the plan
    authored a pocket wider than any published frame serves, and ``pocket_frame_kit`` raises
    rather than billing nothing.
    """
    plan = getattr(model, "plan", None)
    families = {t.tag: t.pocket_frame for t in (plan.library.door_types if plan else ())}
    kits: dict[tuple[str, int], tuple] = {}
    for opening in model.openings:
        if not opening.pocket_run_m:
            continue
        width = round(opening.width_m * _M_TO_IN)
        wall = model.wall(opening.host_wall)
        item = pocket_frame_kit(families.get(opening.type_ref or ""), width,
                                pocket_wall_is_deep(wall.layers if wall else ()))
        entry = kits.setdefault((item.tag, width), (item, []))
        entry[1].append(opening.tag)

    rows: list[dict] = []
    for (_tag, width), (item, tags) in sorted(kits.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        rows.append(hardware_row(
            item, scope="pocket door frame kit", count=len(tags),
            part_number=item.part_number_by_length_in.get(width),
            size=f'{width}" door',
            basis=f"one kit per pocket door at {width}\" leaf: {', '.join(sorted(tags))}",
        ))
    from typehaus.takeoff.door_hardening import authored_hardware_rows

    return rows + doorway_purchase_rows(model) + authored_hardware_rows(model)


def door_installation_rows(model):
    """Site-built boards are measured separately from factory-included door components."""
    rows = []
    for opening in model.openings:
        placement = opening.doorway.exterior_placement if opening.doorway else None
        if placement is None:
            continue
        for board in placement.boards:
            if board.role != "door_installation":
                # Skins and isolation belong to the cladding/flashing allowances.
                continue
            dimensions = board.cut_dimensions_m
            row = dict(kind="exterior door casing" if "casing" in board.name
                       else "door jamb extension", room=None, material=board.material_ref,
                       item=board.material_ref, pieces=1,
                       description=f"{opening.tag}: {board.name}; painted site-built board",
                       length_ft=dimensions[2] / .3048, tags=[opening.tag],
                       inside_corners=0, outside_corners=0,
                       cut_pieces=[dict(thickness_in=dimensions[0] / .0254,
                                        width_in=dimensions[1] / .0254,
                                        length_in=dimensions[2] / .0254)],
                       volume_m3=board.width_m * board.height_m * board.depth_m)
            rows.append(row)
        for section in placement.sections:
            if section.purchase != "site":
                continue
            from shapely.geometry import Polygon

            profile = Polygon(section.polygon_m)
            rows.append(dict(kind="exterior door approach", room=None,
                material=section.material_ref, item=section.material_ref, pieces=1,
                description=f"{opening.tag}: {section.name}; schematic, support design pending",
                length_ft=section.span_m / .3048, tags=[opening.tag],
                inside_corners=0, outside_corners=0, cut_pieces=[],
                volume_m3=profile.area * section.span_m))
    return rows


def doorway_purchase_rows(model):
    """One installed cut length per separately purchased component; factory/kit items excluded."""
    grouped = {}
    for opening in model.openings:
        if opening.doorway is None:
            continue
        for component in opening.doorway.components:
            spec = component.specification
            if spec.purchase != "separate":
                continue
            key = (spec.product_ref, spec.variant, spec.source_url, spec.source_drawing)
            grouped.setdefault(key, []).append((opening.tag, component.span_m))
    rows = []
    for (product, variant, source, drawing), entries in sorted(grouped.items()):
        row = hardware_row(None, scope="doorway transition / hardware", count=len(entries),
                           part_number=product, size=variant,
                           length_ft=sum(length for _, length in entries) / 0.3048,
                           basis="one cut component per doorway: "
                           + ", ".join(t for t, _ in entries),
                           tags=[t for t, _ in entries])
        row.update(hardware_tag=product, description=f"{product} — {variant}",
                   source=f"{source} — {drawing}")
        rows.append(row)
    return rows
