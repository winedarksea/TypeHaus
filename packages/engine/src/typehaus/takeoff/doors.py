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

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_POCKET_DOOR_FRAME_KIT,
    hardware_for_role_and_nominal,
    hardware_row,
)

_M_TO_IN = 39.3700787401575


def door_hardware_rows(model: ResolvedModel) -> list[dict]:
    """One frame kit per pocket door, grouped by leaf width.

    A width with no catalogued kit is a real finding, not a blank line: it means the plan
    authored a pocket wider than any published frame serves. ``hardware_for_role_and_nominal``
    raises there rather than billing nothing, on the same principle as every other role —
    a BOM line without a part is not a bill of materials.
    """
    widths: dict[str, list[str]] = {}
    for opening in model.openings:
        if not opening.pocket_run_m:
            continue
        widths.setdefault(f"{round(opening.width_m * _M_TO_IN)}", []).append(opening.tag)

    rows: list[dict] = []
    for nominal, tags in sorted(widths.items(), key=lambda item: int(item[0])):
        item = hardware_for_role_and_nominal(ROLE_POCKET_DOOR_FRAME_KIT, nominal)
        rows.append(hardware_row(
            item, scope="pocket door frame kit", count=len(tags),
            part_number=item.part_number_by_length_in.get(int(nominal)),
            size=f'{nominal}" door',
            basis=f"one kit per pocket door at {nominal}\" leaf: {', '.join(sorted(tags))}",
        ))
    return rows
