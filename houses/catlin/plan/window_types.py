"""Catlin's window types: the chosen products (2026-10-21, NOT editable: a catalog).

Redefines every window tag the house hangs; `plan/manifest.py` drops the library preset of
the same tag, so the presets themselves stay untouched for other houses. Catalog-only sizes
stay presets. Owner's selection, notes/window_and_door_procurement.md §2:

- Drutex IGLO Energy Alucover (aluminium-capped uPVC, black outside, white inside) for every
  tilt-turn, fixed and tilt-only unit.
- Andersen 400 casement, egress hinge, for the nine R310 escape windows, whose narrow
  bearing RO no Euro sightline clears. R310 applies Andersen's deductions to the unit the
  seat resolves: the flashed opening less 1/2" (Andersen's minimum RO allowance), rounded
  down to the 1/8" custom-size step.

Width/height stay the ROUGH OPENING (the framing module grades it); frame size comes from
the resolved buck, pan, membranes and installation gaps. U/SHGC/VT are the whole-window
NFRC CPD rows cited in each ``source`` (read
2026-10-21 at search.nfrc.org). A tempered twin carries its parent's row: tempering does not
change the rating, and the 16 CFR 1201 mark is an order item.
"""

from __future__ import annotations

from typehaus import WindowType, u_us
from typehaus.quantities import ft, inch

from plan.opening_products import (
    ANDERSEN_400_CASEMENT, DRUTEX_ALUCOVER_FIX, DRUTEX_ALUCOVER_TILT, DRUTEX_ALUCOVER_TT,
)

_DRUTEX_DEPTH = inch(93 / 25.4)  # 93 mm installation depth, Drutex's Alucover data
# Not published to us for the basic unit; the preset's 3 1/4" stays until the dealer's
# section is in hand.
_ANDERSEN_DEPTH = inch(3.25)

_TT = ("NFRC DRU-K-24-00001: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2 (4/4/4) 48mm IG, "
       "U 0.16, SHGC 0.33, VT 0.47.")
_FIX = ("NFRC DRU-K-23-00001: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2 (4/4/4) 48mm IG, "
        "U 0.15, SHGC 0.39, VT 0.57. Fixed in frame.")
_FIX_HP = ("NFRC DRU-K-23-00010: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2Lami (152PVB) 48mm IG, "
           "U 0.14, SHGC 0.39, VT 0.56. The plant room's glazing_dew_point needs U <= 0.14.")
_TILT = ("NFRC DRU-K-26-00001: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2 (4/4/4) 48mm IG, "
         "U 0.18, SHGC 0.24, VT 0.35. Inward bottom-hinged tilt only, modelled as awning "
         "(no hopper operation); the 14\" width is under every outward awning's minimum.")
_AND = ("NFRC AND-N-1-04162: LowE(180/180/i89) triple, argon, U 0.20, SHGC 0.40, VT 0.51. "
        "Andersen sells 400 triple in the Northeast only; if a Twin Cities dealer cannot, "
        "the HeatLock double AND-N-1-03559 is U 0.24.")
_SIZE = "Frame size follows the resolved flashed opening; supplier confirmation pending."
# Andersen 400 custom sizes: 1/8" steps, RO >= unit + 1/2" each way (opening specifications).
_ANDERSEN_STEP, _ANDERSEN_ALLOWANCE = inch(0.125), inch(0.5)


def _drutex(tag, width, height, operation, row, product, *, tempered=False,
            u=0.16, shgc=0.33, vt=0.47) -> WindowType:
    return WindowType(
        tag=tag, width=width, height=height, operation=operation, tempered=tempered,
        u_factor=u_us(u), shgc=shgc, vt=vt, frame_depth=_DRUTEX_DEPTH,
        product_ref=product.tag, source=f"{row} {_SIZE}")


def _tt(tag, width, height, *, tempered=False) -> WindowType:
    return _drutex(tag, width, height, "tilt_turn", _TT, DRUTEX_ALUCOVER_TT,
                   tempered=tempered)


def _fix(tag, width, height, *, tempered=False) -> WindowType:
    return _drutex(tag, width, height, "fixed", _FIX, DRUTEX_ALUCOVER_FIX, tempered=tempered,
                   u=0.15, shgc=0.39, vt=0.57)


def _hp(tag, width, height) -> WindowType:
    return _drutex(tag, width, height, "fixed", _FIX_HP, DRUTEX_ALUCOVER_FIX,
                   u=0.14, shgc=0.39, vt=0.56)


def _egress(tag, width, height, height_deduction, *, tempered=False) -> WindowType:
    # Andersen 400 widest-clear-opening hinge (§7): clear width = unit - 5.81".
    return WindowType(
        tag=tag, width=width, height=height, operation="casement", tempered=tempered,
        u_factor=u_us(0.20), shgc=0.40, vt=0.51, frame_depth=_ANDERSEN_DEPTH,
        net_clear_width_deduction=inch(5.81), net_clear_height_deduction=height_deduction,
        frame_size_increment=_ANDERSEN_STEP, minimum_rough_opening_allowance=_ANDERSEN_ALLOWANCE,
        product_ref=ANDERSEN_400_CASEMENT.tag, source=f"{_AND} {_SIZE}")


# Clear height = unit - 4.43" for a 28 3/8"-31 1/2" wide, 40 13/16"-48" tall unit, else
# unit - 4.85" (Andersen 400 opening specifications, 2025-26). The narrow escape types take
# the full 27 1/2" between jacks (preferences.toml's bearing rung): a 27" RO nets a 25 5/8"
# unit and 19.8" clear; 27 1/2" nets 26 1/8" and 20.3" (notes/window_and_door_procurement.md §7).
WINDOW_TYPES = (
    _drutex("WT-1424", inch(14), ft(2), "awning", _TILT, DRUTEX_ALUCOVER_TILT,
            u=0.18, shgc=0.24, vt=0.35),
    _fix("WT-1424-FIX", inch(14), ft(2)),
    _fix("WT-1424-FIX-T", inch(14), ft(2), tempered=True),
    _fix("WT-2736-FIX", inch(27.5), ft(3)),
    _fix("WT-2736-FIX-T", inch(27.5), ft(3), tempered=True),
    _fix("WT-2748-FIX-T", inch(27.5), ft(4), tempered=True),
    _fix("WT-6348-FIX", inch(63), ft(4)),  # WIN-M-DINING-E, untempered at a 33" sill
    _tt("WT-2736-TT", inch(27.5), ft(3)),
    _tt("WT-2748-TT", inch(27.5), ft(4)),
    _tt("WT-2748-TT-T", inch(27.5), ft(4), tempered=True),
    _tt("WT-3048-TT", inch(30), ft(4)),
    _tt("WT-3048-TT-T", inch(30), ft(4), tempered=True),
    _hp("WT-2754-HP", inch(27.5), ft(4, 6)),
    _hp("WT-3048-HP", inch(30), ft(4)),
    _egress("WT-2748", inch(27.5), ft(4), inch(4.85)),
    _egress("WT-2748-T", inch(27.5), ft(4), inch(4.85), tempered=True),
    _egress("WT-2754", inch(27.5), ft(4, 6), inch(4.85)),
    _egress("WT-3048", inch(30), ft(4), inch(4.43)),
)

HOUSE_WINDOW_TAGS = frozenset(t.tag for t in WINDOW_TYPES)
