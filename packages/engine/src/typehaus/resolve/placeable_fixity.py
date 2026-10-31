"""Which placeables are fixed to the building and which move with the owner.

Fixed: casework (a declared ``work_surface``, or any furniture hung on a wall), a fixture
with a basin body (it needs hot water: a tub, a vanity; not a floor WC, whose pedestal the
base runs behind) or hung on a wall, and an appliance. Trim stops at a fixed thing
(``interior_trim_scope``); ``print3d`` prints it in the house and the rest as furniture.
"""

from __future__ import annotations

from typing import NamedTuple

from typehaus.model.enums import Service


class FixityTypes(NamedTuple):
    furniture: dict
    fixtures: dict


def fixity_types(plan) -> FixityTypes:
    return FixityTypes({t.tag: t for t in plan.library.furniture_types},
                       {t.tag: t for t in plan.library.fixture_types})


def is_fixed(item, types: FixityTypes) -> bool:
    hung = item.attachment_wall is not None
    if item.kind == "Furniture":
        ftype = types.furniture.get(item.type_ref or "")
        # A curtain hangs in front of the trim; its envelope is cloth, not casework.
        return ftype is not None and ftype.curtain_track is None and (
            ftype.work_surface is not None or hung)
    if item.kind == "Fixture":
        ftype = types.fixtures.get(item.type_ref or "")
        return ftype is not None and (Service.WATER_HOT in ftype.needs or hung)
    return item.kind == "Appliance"
