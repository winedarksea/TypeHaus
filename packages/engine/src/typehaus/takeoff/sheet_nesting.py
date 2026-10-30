"""Cut pieces nested onto whole sheets: how many cover panels an order actually needs.

A sheet product (``Product.stock_width`` x ``stock_length``, a FÖRBÄTTRA cover panel) is cut
on site with a straight saw, so each piece is a crosscut strip: one face dimension stands
across the sheet's width, the other is spent along its length. Strip nesting is exact for
that cut and needs no 2D search. First-fit decreasing by length spent, ties by tag, so the
result is deterministic; a kerf is spent before every piece after a sheet's first.

A piece is a placed type whose ``product_ref`` is a sheet (its face is the two larger of
footprint and height) or a ``ProductPart.cut``. A sheet-product part without a ``cut`` is a
whole sheet, as authored. Oracle: ``houses/catlin/notes/ikea_sektion_order.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.labels import _fraction_in
from typehaus.takeoff.placeables import _placeable_types

#: A track-saw blade, spent between two pieces on one sheet.
KERF_M = inch(0.125).meters
_TOL_M = 1e-6
_M_PER_IN = 0.0254


@dataclass(frozen=True)
class Piece:
    tag: str
    face_m: tuple[float, float] | None  # None: a whole sheet, uncut

    def label(self) -> str:
        if self.face_m is None:
            return f"{self.tag} (whole)"
        a, b = (_fraction_in(round(v / _M_PER_IN, 6)).rstrip('"') for v in self.face_m)
        return f'{self.tag} {a} x {b}"'


@dataclass
class Sheet:
    pieces: list[Piece] = field(default_factory=list)
    used_m: float = 0.0


def _along(face: tuple[float, float], width_m: float, length_m: float) -> float | None:
    """Length a piece spends along the sheet, its other side across; None if it fits no way."""
    fits = [along for across, along in (face, face[::-1])
            if across <= width_m + _TOL_M and along <= length_m + _TOL_M]
    return min(fits) if fits else None


def nest(pieces: list[Piece], width_m: float, length_m: float) -> tuple[list[Sheet],
                                                                        list[Piece]]:
    """``(sheets, oversize)``: each cut piece on the first sheet it fits, longest first."""
    sheets = [Sheet([piece]) for piece in sorted(pieces, key=lambda p: p.tag)
              if piece.face_m is None]
    cut = [(along, piece) for piece in pieces if piece.face_m is not None
           and (along := _along(piece.face_m, width_m, length_m)) is not None]
    oversize = [piece for piece in pieces if piece.face_m is not None
                and _along(piece.face_m, width_m, length_m) is None]
    open_sheets: list[Sheet] = []
    for along, piece in sorted(cut, key=lambda item: (-item[0], item[1].tag)):
        sheet = next((s for s in open_sheets
                      if s.used_m + KERF_M + along <= length_m + _TOL_M), None)
        if sheet is None:
            sheet = Sheet()
            open_sheets.append(sheet)
            sheet.used_m = along
        else:
            sheet.used_m += KERF_M + along
        sheet.pieces.append(piece)
    return open_sheets + sheets, oversize


def _face(entry: object) -> tuple[float, float]:
    dims = sorted([entry.footprint[0].meters, entry.footprint[1].meters, entry.height.meters])
    return dims[1], dims[2]


def sheet_pieces(model: ResolvedModel) -> dict[str, list[Piece]]:
    """Every piece cut from each sheet product, by product tag."""
    library = model.plan.library
    types = _placeable_types(model)

    def is_sheet(tag: str | None) -> bool:
        product = library.product(tag) if tag else None
        return bool(product and product.stock_width and product.stock_length)

    out: dict[str, list[Piece]] = {}
    for item in model.canvas_objects:
        if item.domain == "opening":
            continue
        entry = types.get(item.type_ref or "")
        if entry is None:
            continue
        ref = getattr(entry, "product_ref", None)
        if is_sheet(ref):
            out.setdefault(ref, []).append(Piece(item.tag, _face(entry)))
        for part in getattr(entry, "parts", ()):
            if not is_sheet(part.product_ref):
                continue
            face = (part.cut[0].meters, part.cut[1].meters) if part.cut else None
            out.setdefault(part.product_ref, []).extend(
                Piece(item.tag, face) for _ in range(part.quantity))
    return out


def cut_list(sheets: list[Sheet]) -> str:
    """``1: A 24 x 34" + B 24 x 34"; 2: C (whole)`` — which pieces come off which sheet."""
    return "; ".join(f"{index}: " + " + ".join(piece.label() for piece in sheet.pieces)
                     for index, sheet in enumerate(sheets, 1))
