"""The stock a wall's stud line is cut from, when the wall says so.

A ``Wall.layer_materials`` override on the framed STRUCTURE layer (catlin's main storey:
``stud`` -> ``lsl``) is a purchasing fact about the sticks, so it is stamped on every
vertical member of the stud line — studs, kings, jacks, cripples, corner and tee packs.
Plates, headers, sills and blocking keep ``material=None`` and bill as ordinary lumber —
except a raised exterior door's rough sill (``stamp_exterior_door_sills``).
A wall with no such override is returned unchanged, so no other BOM row moves.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from typehaus.resolve.framing.short_members import STUD_LINE_CATEGORIES
from typehaus.resolve.model import FramedMember, ResolvedWall

_STOCKED = STUD_LINE_CATEGORIES | {"corner"}


def stamp_stud_stock(members: tuple[FramedMember, ...], rw: ResolvedWall,
                     authored: object | None) -> tuple[FramedMember, ...]:
    overrides = {lm.layer: lm.material for lm in getattr(authored, "layer_materials", ())}
    stock = next((overrides[layer.name] for layer in rw.layers
                  if layer.function == "structure" and not layer.is_cavity
                  and layer.name in overrides), None)
    if stock is None:
        return members
    return tuple(replace(m, material=stock)
                 if m.category in _STOCKED and m.material is None else m
                 for m in members)


def stamp_exterior_door_sills(members: tuple[FramedMember, ...], openings: Sequence[object],
                              stock: str | None) -> tuple[FramedMember, ...]:
    """A raised exterior door's rough sill and its cripples, cut from ``stock``
    (``FramingSpec.exterior_door_sill_material_ref``). ``openings`` is the list the solver
    enumerated, so its index is the one in ``sill-{i}`` / ``cripple-sill-{i}-NN``."""
    if stock is None:
        return members
    keys = {f"sill-{i}" for i, op in enumerate(openings)
            if getattr(op, "is_door", False) and getattr(op, "exterior", False)}
    if not keys:
        return members

    def wet(member: FramedMember) -> bool:
        key = member.child_key
        return key in keys or (key.startswith("cripple-sill-")
                               and key.rsplit("-", 1)[0].removeprefix("cripple-") in keys)

    return tuple(replace(m, material=stock) if m.material is None and wet(m) else m
                 for m in members)
