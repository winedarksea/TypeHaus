"""Base and door casing in the milling schedule — custom-milled stock only.

A view, like the rest of ``hardwood``: the LF is billed in ``interior_trim`` and these rows
say so (``also_in_interior_trim``). Bought stock (a poplar 1x4) is the yard's, not the
sawyer's, and never appears here.

Casing is cut to length, so it groups by finished size like a stool. Base is not: it is run
as long boards and cut on site, so it is ONE lineal row per stock: boards as long as the
longest piece, enough of them to cover the total run, through ``_piece_row``'s yield
constants. Both are ripped from the wide stack: the face is far under ``max_board_width``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874
_ALSO = {"also_in_interior_trim": True}


def trim_rows(model: ResolvedModel, materials: Mapping[str, object],
              max_board_width_in: float | None) -> list[dict[str, object]]:
    from typehaus.takeoff.hardwood import _piece_row

    def milled(ref: str) -> bool:
        return bool(getattr(materials.get(ref), "requires_custom_milling", False))

    rows: list[dict[str, object]] = []
    base: dict[tuple[str, str, float, float], list] = {}
    for run in getattr(model, "base_runs", ()):
        if run.kind != "trim" or not milled(run.material_ref):
            continue
        key = (run.material_ref, run.profile, round(run.thickness_m * _M_TO_IN, 3),
               round(run.height_m * _M_TO_IN, 3))
        base.setdefault(key, []).append(run)
    for (material_ref, profile, thickness, height), runs in base.items():
        total_in = sum(run.length_m for run in runs) * _M_TO_IN
        longest_in = max(run.length_m for run in runs) * _M_TO_IN
        # Boards as long as the longest piece, enough to cover the run: what a sawyer cuts.
        boards = math.ceil(total_in / longest_in - 1e-9)
        row = _piece_row("baseboard", material_ref, materials, boards, thickness, height,
                         longest_in, max_board_width_in, [run.room for run in runs], _ALSO,
                         profile=profile)
        row.update({
            "total_length_ft": round(total_in / 12.0, 1),
            "site_cut_pieces": len(runs),
            "stock_note": (f"run as lineal stock: {total_in / 12.0:.1f} LF cut on site into "
                           f"{len(runs)} pieces; rip from the wide stack"),
        })
        rows.append(row)

    casing: dict[tuple[str, str, float, float, float], list[str]] = {}
    for item in getattr(model, "door_casings", ()):
        if not milled(item.material_ref):
            continue
        for piece in item.pieces:
            key = (item.material_ref, item.profile, round(item.thickness_m * _M_TO_IN, 3),
                   round(piece.width_m * _M_TO_IN, 3), round(piece.length_m * _M_TO_IN, 2))
            casing.setdefault(key, []).append(item.opening_ref)
    for (material_ref, profile, thickness, width, length), tags in casing.items():
        rows.append(_piece_row("door casing", material_ref, materials, len(tags), thickness,
                               width, length, max_board_width_in, tags, _ALSO,
                               profile=profile))
    return rows
