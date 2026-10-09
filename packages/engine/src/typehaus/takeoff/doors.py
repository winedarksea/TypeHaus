"""The door-hardware rows of the bill of materials.

For most doors the ``finish-door-*`` lump-sum allowance is defensible — a lockset is a
lockset. For a pocket door it is not: the frame kit *is* the pocket (split studs, head
track, hangers, guides), bought one per door, and which one you buy is decided by the leaf
width, the host wall's depth and the type's ``pocket_frame`` family.

Only pocket kits are derived here so far. ``ResolvedOpening.pocket_run_m`` is non-zero for
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
    return rows
