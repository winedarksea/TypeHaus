"""Draw a trapeze's rods, struts and bridges as ``equipment_hanger`` solids, the way
``duct_part_solids`` draws a ``rod_trapeze``: derived, billed off the records."""

from __future__ import annotations

import math
from typing import Any

from typehaus.resolve.duct_part_solids import ROD_DIAMETER_M, Section, _box, _solid, loft
from typehaus.resolve.equipment_hangers import (
    ROD_TAIL_M,
    STRUT_SECTION_M,
    ResolvedEquipmentHanger,
)

CATEGORY = "equipment_hanger"
_UP = (0.0, 0.0, 1.0)


def hanger_solids(model: Any, rods: list[ResolvedEquipmentHanger]) -> None:
    uids = {o.tag: o.uid for o in model.canvas_objects}
    rod_section = Section(True, ROD_DIAMETER_M, ROD_DIAMETER_M)
    struts: dict[tuple[str, int], list[ResolvedEquipmentHanger]] = {}
    for rod in rods:
        struts.setdefault((rod.equipment_tag, rod.strut), []).append(rod)
        uid, tag = uids.get(rod.equipment_tag, rod.equipment_tag), rod.equipment_tag
        if rod.hangs_from is not None:
            bottom = rod.strut_top_z_m - STRUT_SECTION_M - ROD_TAIL_M
            mesh = loft((*rod.point, bottom), _UP, rod_section, rod_section, rod.rod_length_m)
            model.solids.append(_solid(f"{uid}-hanger-rod-{rod.rod}", f"{tag}-ROD-{rod.rod}",
                                       rod.storey, CATEGORY, mesh, rod.rod_product_ref, tag))
        if rod.bridge:
            model.solids.append(_solid(
                f"{uid}-hanger-bridge-{rod.rod}", f"{tag}-BRIDGE-{rod.rod}", rod.storey,
                CATEGORY, _bridge_mesh(rod), rod.strut_product_ref, tag))
    for (tag, strut), pair in sorted(struts.items()):
        a, b = pair[0].point, pair[-1].point
        across = _unit(b[0] - a[0], b[1] - a[1])
        centre = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0,
                  pair[0].strut_top_z_m - STRUT_SECTION_M / 2.0)
        mesh = _box(centre, ((*across, 0.0), (-across[1], across[0], 0.0), _UP),
                    (pair[0].strut_length_m, STRUT_SECTION_M, STRUT_SECTION_M))
        uid = uids.get(tag, tag)
        model.solids.append(_solid(f"{uid}-hanger-strut-{strut}", f"{tag}-STRUT-{strut}",
                                   pair[0].storey, CATEGORY, mesh,
                                   pair[0].strut_product_ref, tag))


def _unit(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _bridge_mesh(rod: ResolvedEquipmentHanger):
    """The bridge strut on (or under) the two joists' bottom flanges, through the rod."""
    (x0, y0), (x1, y1) = rod.bridge_ends
    along = _unit(x1 - x0, y1 - y0)
    centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, rod.bridge_z_m + STRUT_SECTION_M / 2.0)
    return _box(centre, ((*along, 0.0), (-along[1], along[0], 0.0), _UP),
                (rod.bridge_length_m, STRUT_SECTION_M, STRUT_SECTION_M))
