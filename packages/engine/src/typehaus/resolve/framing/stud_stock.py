"""The stock a wall's stud line is cut from, when the wall says so.

A ``Wall.layer_materials`` override on the framed STRUCTURE layer (catlin's main storey:
``stud`` -> ``lsl``) is a purchasing fact about the sticks, so it is stamped on every
vertical member of the stud line — studs, kings, jacks, cripples, corner and tee packs.
Plates, headers, sills and blocking keep ``material=None`` and bill as ordinary lumber.
A wall with no such override is returned unchanged, so no other BOM row moves.
"""

from __future__ import annotations

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
