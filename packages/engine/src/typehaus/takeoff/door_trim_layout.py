"""Deterministic lengthwise strip layouts for door trim cut from selected sheet stock.

One board per strip preserves the selected finish direction. This is a feasible cutting
layout, not an optimal nesting claim; short offcuts are left available to the shop.
"""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TrimSheetStock:
    description: str
    finish: str
    thickness_in: float
    width_in: float
    length_in: float
    saw_kerf_in: float

    def __post_init__(self):
        dimensions = (self.thickness_in, self.width_in, self.length_in, self.saw_kerf_in)
        if any(not isfinite(v) or v <= 0 for v in dimensions):
            raise ValueError("trim sheet dimensions and saw kerf must be finite and positive")


def layout_trim_strips(pieces, stock: TrimSheetStock):
    """First-fit decreasing rip widths, with explicit cuts and one kerf per strip."""
    sheets = []
    for piece in sorted(
        pieces, key=lambda p: (-p["width_in"], -p["length_in"], p["door"], p["part"])
    ):
        width, length, thickness = (piece[k] for k in ("width_in", "length_in", "thickness_in"))
        if any(not isfinite(v) or v <= 0 for v in (width, length, thickness)):
            raise ValueError("trim cuts must be finite and positive")
        if abs(thickness - stock.thickness_in) > 1e-6:
            raise ValueError(f"{piece['door']}/{piece['part']} thickness differs from sheet stock")
        required_width = width + stock.saw_kerf_in
        if required_width > stock.width_in + 1e-6 or length > stock.length_in + 1e-6:
            raise ValueError(f"{piece['door']}/{piece['part']} exceeds selected trim sheet stock")
        sheet = next(
            (s for s in sheets if s["used_width_in"] + required_width <= stock.width_in + 1e-6),
            None,
        )
        if sheet is None:
            sheet = dict(
                stock=stock.description,
                finish=stock.finish,
                sheet_width_in=stock.width_in,
                sheet_length_in=stock.length_in,
                saw_kerf_in=stock.saw_kerf_in,
                pieces=[],
                used_width_in=0,
                maximum_length_in=0,
            )
            sheets.append(sheet)
        sheet["pieces"].append(dict(piece, rip_offset_in=sheet["used_width_in"]))
        sheet["used_width_in"] += required_width
        sheet["maximum_length_in"] = max(sheet["maximum_length_in"], length)
    return sheets


def door_trim_sheet_layouts(model, stock_by_material: dict[str, TrimSheetStock]):
    """Derive selected material layouts from resolved installation boards, across doors."""
    pieces_by_material = {material: [] for material in stock_by_material}
    for opening in model.openings:
        placement = opening.doorway.exterior_placement if opening.doorway else None
        if placement is None:
            continue
        for board in placement.boards:
            if board.role != "door_installation" or board.material_ref not in stock_by_material:
                continue
            thickness, width, length = board.cut_dimensions_m
            pieces_by_material[board.material_ref].append(
                dict(
                    door=opening.tag,
                    part=board.name,
                    thickness_in=thickness / 0.0254,
                    width_in=width / 0.0254,
                    length_in=length / 0.0254,
                )
            )
    return [
        dict(sheet, material=material)
        for material, stock in sorted(stock_by_material.items())
        for sheet in layout_trim_strips(pieces_by_material[material], stock)
    ]
