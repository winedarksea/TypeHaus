"""A framing size as the yard sells it: one line per stock length, counted by the piece.

A lumberyard prices, pulls and tickets by the stick, so "2x6, 7,202 LF ordered" is not an
order and "134 pc 2x6 8'" is. A built-up member is bought as its plies: a ``2-2x8`` header
row is 2x8 sticks at twice its member count. Every stick is a ``framing_bom_by_size``
bucket, so nothing is recounted here.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from typehaus.takeoff.labels import role_label

_PLIES = re.compile(r"(\d+)-(.+)")


@dataclass(frozen=True)
class StockLine:
    profile: str  # one ply: ``2x8``, ``1.75x16 LVL``, ``2x12:kdat``
    stock: str  # ``16'``, ``104 5/8" PET``
    pieces: int
    ordered_lf: float
    application: str  # what the sticks frame, for the delivery ticket


def stock_lines(row: Mapping[str, Any]) -> tuple[StockLine, ...]:
    """The sticks one ``framing_bom_by_size`` row is bought as, shortest first."""
    profile = str(row.get("profile") or "")
    built_up = _PLIES.fullmatch(profile)
    plies, ply = (int(built_up.group(1)), built_up.group(2)) if built_up else (1, profile)
    lines = []
    for stick in row.get("stock") or ():
        roles = ", ".join(role_label(str(t)) for t in stick.get("types") or ())
        count = int(stick["count"]) * plies
        lines.append(StockLine(
            profile=ply, stock=str(stick["label"]), pieces=count,
            ordered_lf=round(count * float(stick["length_ft"]), 1),
            application=f"{roles} ({plies}-ply)" if plies > 1 else roles))
    return tuple(lines)
