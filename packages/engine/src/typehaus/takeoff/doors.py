"""The door-hardware rows of the bill of materials.

For most doors the ``finish-door-*`` lump-sum allowance is defensible — a lockset is a
lockset. For a pocket door it is not: the frame kit *is* the pocket (split studs, head
track, hangers, guides), bought one per door, and which one you buy is decided by the leaf
width. A lump sum cannot tell you the 4'-0" leaf needs a different frame from the 3'-0" one.

Only pocket kits are derived here so far. The resolved model is enough to do it without
reaching back to the plan: ``ResolvedOpening.pocket_run_m`` is non-zero for exactly the
pocket doors, and ``width_m`` is what selects the kit.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_POCKET_DOOR_FRAME_KIT,
    hardware_for_role_and_nominal,
)
from typehaus.resolve.framing.tables import POCKET_SPLIT_STUD_2X6_MIN_DEPTH
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

_M_TO_IN = 39.3700787401575


def door_hardware_rows(model: ResolvedModel) -> list[dict]:
    """One frame kit per pocket door, grouped by leaf width.

    A width with no catalogued kit is a real finding, not a blank line: it means the plan
    authored a pocket wider than any published frame serves. ``hardware_for_role_and_nominal``
    raises there rather than billing nothing, on the same principle as every other role —
    a BOM line without a part is not a bill of materials.
    """
    widths: dict[tuple[int, str], list[str]] = {}
    for opening in model.openings:
        if not opening.pocket_run_m:
            continue
        width = round(opening.width_m * _M_TO_IN)
        wall = model.wall(opening.host_wall)
        structure = next((layer for layer in wall.layers
                          if layer.function == "structure"), None) if wall else None
        # The 1560 kit supports a 2x6 wall face to face; the 1500PF is a 2x4 kit.
        nominal = f"{width}-2x6" if width == 36 and structure and \
            structure.thickness_m >= POCKET_SPLIT_STUD_2X6_MIN_DEPTH.meters \
            else str(width)
        widths.setdefault((width, nominal), []).append(opening.tag)

    rows: list[dict] = []
    for (width, nominal), tags in sorted(widths.items()):
        item = hardware_for_role_and_nominal(ROLE_POCKET_DOOR_FRAME_KIT, nominal)
        rows.append(hardware_row(
            item, scope="pocket door frame kit", count=len(tags),
            part_number=item.part_number_by_length_in.get(width),
            size=f'{width}" door',
            basis=f"one kit per pocket door at {width}\" leaf: {', '.join(sorted(tags))}",
        ))
    return rows
