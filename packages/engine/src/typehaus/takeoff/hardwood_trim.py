"""Base and door casing in the milling schedule — custom-milled stock only.

A view, like the rest of ``hardwood``: the LF is billed in ``interior_trim`` and these rows
say so (``also_in_interior_trim``). Bought stock (a poplar 1x4) is the yard's, not the
sawyer's, and never appears here.

Both are bought as long boards and cut on site, so each is ONE lineal row per stock, like a
floor: the total LF, and the boards it takes. With ``TrimStandard.stock_length`` declared,
the cut pieces are packed first-fit-decreasing into boards that long (a base run longer
than a board is spliced); without it, boards are as long as the longest piece. Both are
ripped from the wide stack: the face is far under ``max_board_width``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from typehaus.model.millwork import TrimStandard
from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874
_ALSO = {"also_in_interior_trim": True}

#: Length lost per cut piece when packing into stock boards, in inches: squaring the board
#: end plus the miter or cope at each end of a trim piece.
_CUT_ALLOWANCE_IN = 1.0


def _boards_for(lengths_in: list[float], stock_in: float | None) -> tuple[int, float, int]:
    """``(boards, board length, splices)`` to cut ``lengths_in`` from."""
    if stock_in is None:
        longest = max(lengths_in)
        return math.ceil(sum(lengths_in) / longest - 1e-9), longest, 0
    cuts: list[float] = []
    splices = 0
    for length in lengths_in:
        # A run longer than a board is spliced from full boards plus a remainder.
        cut = length + _CUT_ALLOWANCE_IN
        whole = 0 if cut <= stock_in + 1e-9 else math.floor(length / stock_in)
        cuts.extend([stock_in] * whole)
        rest = cut - whole * stock_in
        if rest > _CUT_ALLOWANCE_IN + 1e-9:
            cuts.append(rest)
        splices += whole - (rest <= _CUT_ALLOWANCE_IN + 1e-9) if whole else 0
    remaining: list[float] = []
    for cut in sorted(cuts, reverse=True):
        slot = next((i for i, left in enumerate(remaining) if left >= cut - 1e-9), None)
        if slot is None:
            remaining.append(stock_in - cut)
        else:
            remaining[slot] -= cut
    return len(remaining), stock_in, splices


def _lineal_row(use: str, material_ref: str, profile: str, thickness: float, width: float,
                lengths_in: list[float], stock_in: float | None, tags: list[str],
                materials: Mapping[str, object],
                max_board_width_in: float | None, narrow: int = 0) -> dict[str, object]:
    from typehaus.takeoff.hardwood import _piece_row

    boards, board_in, splices = _boards_for(lengths_in, stock_in)
    total_in = sum(lengths_in)
    row = _piece_row(use, material_ref, materials, boards, thickness, width, board_in,
                     max_board_width_in, tags, _ALSO, profile=profile)
    spliced = f", {splices} spliced" if splices else ""
    ripped = f", {narrow} ripped narrower" if narrow else ""
    board = f'{board_in / 12.0:g}\' boards' if stock_in else f'{board_in:.1f}" boards'
    row.update({
        "total_length_ft": round(total_in / 12.0, 1),
        "site_cut_pieces": len(lengths_in),
        "stock_note": (f"run as lineal stock: {total_in / 12.0:.1f} LF in {boards} {board}, "
                       f"cut on site into {len(lengths_in)} pieces (longest "
                       f'{max(lengths_in):.1f}"{spliced}{ripped}); rip from the wide stack'),
    })
    return row


def trim_rows(model: ResolvedModel, materials: Mapping[str, object],
              max_board_width_in: float | None) -> list[dict[str, object]]:
    def milled(ref: str) -> bool:
        return bool(getattr(materials.get(ref), "requires_custom_milling", False))

    standard = next((el for el in model.plan.all_elements()
                     if isinstance(el, TrimStandard)), None)
    stock_in = (standard.stock_length.inches
                if standard is not None and standard.stock_length is not None else None)
    # A clipped casing leg is ripped on site from the full-width stock, not milled narrow.
    casing_in = round(standard.casing_width.inches, 3) if standard is not None else None

    # (use, material, profile, thickness, face width) -> (piece lengths, tags)
    groups: dict[tuple[str, str, str, float, float], tuple[list[float], list[str]]] = {}
    narrow: dict[tuple[str, str, str, float, float], int] = {}
    for run in getattr(model, "base_runs", ()):
        if run.kind != "trim" or not milled(run.material_ref):
            continue
        key = ("baseboard", run.material_ref, run.profile,
               round(run.thickness_m * _M_TO_IN, 3), round(run.height_m * _M_TO_IN, 3))
        lengths, tags = groups.setdefault(key, ([], []))
        lengths.append(run.length_m * _M_TO_IN)
        tags.append(run.room)
    for item in getattr(model, "door_casings", ()):
        if not milled(item.material_ref):
            continue
        for piece in item.pieces:
            width = round(piece.width_m * _M_TO_IN, 3)
            ripped = casing_in is not None and width < casing_in
            key = ("door casing", item.material_ref, item.profile,
                   round(item.thickness_m * _M_TO_IN, 3), casing_in if ripped else width)
            narrow[key] = narrow.get(key, 0) + ripped
            lengths, tags = groups.setdefault(key, ([], []))
            lengths.append(piece.length_m * _M_TO_IN)
            tags.append(item.opening_ref)
    return [_lineal_row(use, material_ref, profile, thickness, width, lengths, stock_in,
                        tags, materials, max_board_width_in, narrow.get(key, 0))
            for key, (lengths, tags) in groups.items()
            for use, material_ref, profile, thickness, width in (key,)]
