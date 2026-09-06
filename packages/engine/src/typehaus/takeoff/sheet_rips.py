"""Panel-profile members ordered as SHEETS, by ripping then crosscutting.

A ``"<width>x<thickness>[ <label>] panel"`` profile (``resolve/framing/profiles.py``) is a
sheet good swept as a member — a window buck, an I-joist web stiffener, a plywood furring
rip. ``framing_takeoff`` used to bill every one of them on the dimensional-lumber ladder:
156 window bucks came out as 62 eight-foot *sticks* of ``6x0.375``, with a board-foot
figure, which is an order no yard can fill and a unit no plywood is sold in.

The right model is **rip, then crosscut**, and it is not ``_bucket_cut_lengths``: that packs
1-D cuts onto 1-D stock, and a sheet is 2-D. A 4x8 sheet is first ripped into strips of the
panel's own ``width``, and only then are the pieces crosscut out of each 8-ft strip. The rip
yield is a floor, not a ratio — a 13 5/8" soffit board takes **3** strips out of 48", not
3.52 — and the blade takes its kerf on every rip, so 4" strips yield 11 from a sheet and not
the 12 that 48/4 promises.

Only a member that really is cut from a wood structural panel comes here. A metal coil trim
band, a spray-foam eave return and a KDAT furring stick are all spelled as ``panel``
profiles too (the profile grammar describes a swept rectangle, not a product), and every one
of them is genuinely bought by the lineal foot. :data:`SHEET_RIP_MATERIALS` is the
allowlist that separates the two, and it names ``library/materials.py`` tags rather than
guessing from substrings in them — "plywood" appears in ``plywood-subfloor`` and in nothing
that would tell you ``osb`` is the same kind of purchase.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.resolve.framing.profiles import _RE_PANEL

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import FramedMember

#: Sheet stock everything here is ripped from: 4 ft x 8 ft, the only size a residential
#: panel order is placed in. A house that buys 5x10 industrial stock would state it.
SHEET_WIDTH_IN = 48.0
SHEET_LENGTH_FT = 8.0

#: Saw kerf, in inches — 1/8", the same framing blade ``takeoff/framing._KERF_FT`` charges
#: on a crosscut. Stated here in inches because a rip is measured across the sheet.
_KERF_IN = 0.125
_KERF_FT = _KERF_IN / 12.0

#: Nominal thicknesses a wood structural panel is sold in. A member whose profile thickness
#: is an integer multiple of one of these is that many **plies** of it: the roof's beveled
#: web stiffener is authored 1 7/16" thick precisely because one member stands for the PAIR
#: of 23/32" plies that straddle the I-joist web (``resolve/framing/roof._STIFFENER_PROFILE``),
#: and ordering it as one 1 7/16" sheet would be ordering a product that does not exist.
_SHEET_THICKNESS_IN: tuple[float, ...] = (
    0.25, 0.3125, 0.375, 0.4375, 0.46875, 0.5, 0.59375, 0.625, 0.71875, 0.75, 1.0, 1.125,
)
#: The most plies a panel member is read as. Four 3/4" plies is a 3" block; past that the
#: thickness is a stated dimension, not a lamination, and the member bills at its own
#: thickness rather than inventing a build-up nobody drew.
_MAX_PLIES = 4

#: Materials whose panel-profile members are cut from a 4x8 sheet, by ``library/materials.py``
#: tag. Everything else that wears a ``panel`` profile — ``metal-dark-exterior`` coil trim,
#: ``closed-cell-spray-foam`` eave returns, ``pvc-cellular`` soffit, ``kdat`` furring,
#: ``board-batten-24``/``pbr-panel-26`` cladding bands — is bought by the lineal foot or the
#: square foot and stays on the lineal ladder where its price row already is.
#:
#: It is an ALLOWLIST, and deliberately: routing a member here changes the section it bills
#: in and therefore the price table it joins, so a material has to be *known* to be sheet
#: stock, not merely un-recognised.
SHEET_RIP_MATERIALS = frozenset({
    "struct-1-plywood",
    "cdx-plywood",
    "osb",
    "zip-sheathing",
    "zip-r",
    "plywood-subfloor",
    "plywood-underlayment-sanded",
})


@dataclass(frozen=True)
class RipStock:
    """The sheet one panel-profile member is cut from: material, thickness, plies, width."""

    material: str
    sheet_thickness_in: float
    plies: int
    width_in: float


def rip_stock(profile: str, material: str | None) -> RipStock | None:
    """The sheet a panel member is ripped from, or ``None`` if it is not a sheet good.

    ``None`` is the answer for every non-panel profile and for a panel profile whose
    material is not in :data:`SHEET_RIP_MATERIALS` — the coil, the foam and the treated
    stick, each of which orders by the foot.
    """
    if not material or material not in SHEET_RIP_MATERIALS:
        return None
    match = _RE_PANEL.match(profile)
    if match is None:
        return None
    width_in = float(match["width"])
    thickness_in = float(match["thickness"])
    if width_in <= 0.0 or thickness_in <= 0.0 or width_in > SHEET_WIDTH_IN:
        return None
    plies, sheet_thickness_in = _plies(thickness_in)
    return RipStock(material, sheet_thickness_in, plies, width_in)


def _plies(thickness_in: float) -> tuple[int, float]:
    """``(plies, sheet thickness)`` for an authored panel thickness.

    Fewest plies first, so a 3/4" member is one 3/4" sheet rather than two 3/8" ones. A
    thickness that is no multiple of any stock sheet is taken at face value: the model said
    a dimension, and inventing a lamination to explain it would be a guess.
    """
    for plies in range(1, _MAX_PLIES + 1):
        each = thickness_in / plies
        for stock in _SHEET_THICKNESS_IN:
            if abs(each - stock) <= 1e-6:
                return plies, stock
    return 1, thickness_in


def rips_per_sheet(width_in: float) -> int:
    """Strips of ``width_in`` a 48"-wide sheet yields, blade kerf included.

    ``floor(48 / width)`` is the yield a zero-width blade would give, and it is wrong exactly
    where the width divides 48 evenly: twelve 4" strips need eleven kerfs, 1 3/8" of sheet
    that is not there. Charging the kerf makes that 11 and changes nothing for a width that
    already left a margin — a 13 5/8" soffit board is 3 strips either way.
    """
    if width_in <= 0.0 or width_in > SHEET_WIDTH_IN:
        return 0
    return int((SHEET_WIDTH_IN + _KERF_IN) / (width_in + _KERF_IN) + 1e-9)


def strips_for_cuts(lengths_ft: list[float]) -> int:
    """8-ft strips a set of crosscut lengths takes, first-fit-decreasing with kerf.

    A cut longer than the strip is not an error and not a special order: a nailed-on rip is
    butted end to end over its support, so it consumes whole strips plus a remainder that
    goes back in the pool with everything else. Kerf is charged once per crosscut, which is
    the same convention ``takeoff/framing._bucket_cut_lengths`` uses.
    """
    whole = 0
    remainders: list[float] = []
    for cut_ft in lengths_ft:
        full, rest = divmod(cut_ft, SHEET_LENGTH_FT)
        whole += int(full)
        if rest > 1e-9:
            remainders.append(rest)
    offcuts: list[float] = []
    for cut_ft in sorted(remainders, reverse=True):
        need = cut_ft + _KERF_FT
        for index, left in enumerate(offcuts):
            if left >= need - 1e-9:
                offcuts[index] = left - need
                break
        else:
            offcuts.append(SHEET_LENGTH_FT - need)
    return whole + len(offcuts)


def rip_sheet_rows(
    members: Iterable[tuple[FramedMember, RipStock, float]],
) -> list[dict[str, object]]:
    """Sheet rows for every panel member ripped from stock, one per (scope, sheet).

    ``scope`` is the member CATEGORY — "buck rip", "bearing stiffener rip" — because that is
    what an estimator has to see to know a sheet is being cut up rather than hung: the sheets
    are the same product as the wall sheathing and the labour is nothing like it.

    Rows carry exactly the field set ``sheet_goods_takeoff`` emits, so the price join
    (``cli/prices.ESTIMATE_PLANS``: key ``material``, quantity ``sheets_4x8``) reads them
    with no change. Sheets are summed as FRACTIONS across the rip widths inside one row and
    rounded up once — a framer ripping a 6" buck strip and a 4" stiffener strip off the same
    3/8" sheet is what actually happens, and rounding each width up on its own would order a
    sheet per width for a house that uses two.
    """
    # (scope, material, sheet thickness) -> {rip width -> cut lengths}
    groups: dict[tuple[str, str, float], dict[float, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    for member, stock, length_ft in members:
        scope = f"{member.category.replace('_', ' ')} rip"
        key = (scope, stock.material, stock.sheet_thickness_in)
        # One member is ``plies`` identical pieces: the pair of web stiffeners is two.
        groups[key][stock.width_in].extend([length_ft] * stock.plies)

    rows: list[dict[str, object]] = []
    for (scope, material, thickness_in), by_width in sorted(groups.items()):
        sheets = 0.0
        area_sqft = 0.0
        for width_in, lengths in sorted(by_width.items()):
            per_sheet = rips_per_sheet(width_in)
            strips = strips_for_cuts(lengths)
            sheets += strips / per_sheet if per_sheet else strips
            area_sqft += sum(lengths) * width_in / 12.0
        rows.append({
            "scope": scope,
            "material": material,
            "thickness_in": round(thickness_in, 3),
            # The area of STRIP the cuts actually consume, not the sheet it came off. The
            # gap between this and ``sheets_4x8`` x 32 is the rip waste, and on a narrow
            # strip out of a wide sheet that gap is most of the sheet — which is the honest
            # reading, because the offcut is a pile of plywood ribbons nobody re-uses.
            "net_area_sqft": round(area_sqft, 1),
            "sheets_4x8": math.ceil(sheets - 1e-9),
        })
    return rows
