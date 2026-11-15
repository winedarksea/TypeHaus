"""Catlin's window types: the chosen products (2026-10-21, NOT editable: a catalog).

Redefines every window tag the house hangs; `plan/manifest.py` drops the library preset of
the same tag, so the presets themselves stay untouched for other houses. Catalog-only sizes
stay presets. Owner's selection, notes/window_and_door_procurement.md §2:

- Drutex IGLO Energy Alucover (aluminium-capped uPVC, black outside, white inside) for every
  non-escape 27"+ tilt-turn and every fixed unit.
- Aliplast Max Light Modern (thermally broken aluminium, 35 mm frame + 35 mm sash) for the
  three 14x24 tilt-turns, where Drutex's 125 mm operable sightline leaves little glass, and
  for the nine R310 escape windows since 2026-11-13 (Andersen 400 retired: two Polish
  brands). R310 applies a turn-sash deduction to the unit the seat resolves.

Width/height stay the ROUGH OPENING (the framing module grades it); frame size comes from
the resolved buck, pan, membranes and installation gaps. U/SHGC/VT are the whole-window
NFRC CPD rows cited in each ``source`` (read
2026-10-21 at search.nfrc.org). A tempered twin carries its parent's row: tempering does not
change the rating, and the 16 CFR 1201 mark is an order item.
"""

from __future__ import annotations

from plan.opening_products import (
    ALIPLAST_MAXLIGHT_TT,
    DRUTEX_ALUCOVER_FIX,
    DRUTEX_ALUCOVER_TT,
)
from typehaus import WindowType, u_us
from typehaus.quantities import ft, inch, mm

_DRUTEX_DEPTH = mm(93)
# Fensterblick's Alucover 70001 / 70013 section (2026-11-07). An operable unit's envelope
# includes the 30 mm sill adaptor (54123): on the bare frame its stool, under the 38 mm
# inward sash, pierced the sill pan's 1 1/2" back dam (notes/window_profile_measurements.md §1).
_DRUTEX_FRAME, _DRUTEX_SASH = mm(74), mm(50)
_DRUTEX_SILL_ADAPTOR = mm(30)
_DRUTEX_INWARD_SASH_BOTTOM = mm(38 + 30)
# Fixed-section face width includes glazing details, not a measured stool-bearing rail.
# Keep the previous stool basis explicit so the face correction does not move counters.
_DRUTEX_FIXED_STOOL_RAIL = mm(75)
_DRUTEX_FACES = ("Alucover frame 70001, 74 mm exterior face. "
                 "Operable units include a 30 mm sill adaptor (54123); DAKAM to confirm. "
                 "Sources: notes/window_profile_measurements.md.")
_MAXLIGHT_DEPTH = inch(75 / 25.4)  # frame ML010 depth; sash 84 mm
_MAXLIGHT_FACE = inch(35 / 25.4)   # 35 mm frame, 35 mm sash (Aliplast Max Light Modern)
# PROVISIONAL: Drutex's 54123 figure, pending Slowinscy's sill section. Lifts the stool clear
# of the sill pan's 1 1/2" back dam; the sash is drawn above it, so the inward swing clears.
_MAXLIGHT_SILL_ADAPTOR = mm(30)
# Turn-sash clear opening, ESTIMATED (no published figure; Slowinscy's written one replaces
# it): width = unit - two 35 mm frames - the 84 mm sash standing at 90 deg on the hinge side;
# height = unit - two 35 mm frames - the 30 mm sill adaptor. 26.21" unit -> 20.15" clear.
_MAXLIGHT_CLEAR_W = mm(2 * 35 + 84)
_MAXLIGHT_CLEAR_H = mm(2 * 35 + 30)

_TT = ("NFRC DRU-K-24-00001: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2 (4/4/4) 48mm IG, "
       "U 0.16, SHGC 0.33, VT 0.47.")
_FIX = ("NFRC DRU-K-23-00001: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2 (4/4/4) 48mm IG, "
        "U 0.15, SHGC 0.39, VT 0.57. Fixed in frame.")
_FIX_HP = ("NFRC DRU-K-23-00010: CGPrem2/ARG90/ExtraClr/ARG90/CGPrem2Lami (152PVB) 48mm IG, "
           "U 0.14, SHGC 0.39, VT 0.56. The plant room's glazing_dew_point needs U <= 0.14.")
_MAXLIGHT = ("NFRC STO-M-20 (Slowinscy, MAXLIGHT Tilt Turn, frame ML010 / sash ML020): "
             "CGPrem2/Arg/Clr/Arg/CGPrem2 48 mm triple, U 0.20, SHGC 0.40, VT 0.58, CR 69; "
             "Plastixal PLX-K-17 carries the same row (CR 66). Faces 35 mm frame + 35 mm sash "
             "(Aliplast Max Light Modern fiche). Inward tilt-turn. "
             "Sill adaptor 30 mm PROVISIONAL (supplier section pending).")
_SIZE = "Frame size follows the resolved flashed opening; supplier confirmation pending."


def _drutex(tag, width, height, operation, row, product, *, tempered=False,
            u=0.16, shgc=0.33, vt=0.47) -> WindowType:
    profile_detail = ("Fixed in frame; interior stool rail remains provisionally 75 mm."
                      if operation == "fixed" else
                      "Sash 70013 adds 50 mm face; inward bottom 68 mm above the adaptor.")
    return WindowType(
        tag=tag, width=width, height=height, operation=operation, tempered=tempered,
        u_factor=u_us(u), shgc=shgc, vt=vt, frame_depth=_DRUTEX_DEPTH,
        frame_face_width=_DRUTEX_FRAME,
        frame_sill_face_width=_DRUTEX_FRAME + _DRUTEX_SILL_ADAPTOR if operation != "fixed"
        else None,
        sash_face_width=_DRUTEX_SASH if operation != "fixed" else inch(0),
        inward_sash_bottom_height=_DRUTEX_INWARD_SASH_BOTTOM if operation != "fixed" else None,
        sill_rail_height=_DRUTEX_FIXED_STOOL_RAIL if operation == "fixed" else None,
        frame_material_ref="drutex-alucover-cap",
        product_ref=product.tag, source=f"{row} {_DRUTEX_FACES} {profile_detail} {_SIZE}")


def _maxlight(tag, width, height, *, tempered=False, egress=False) -> WindowType:
    clear = ({"net_clear_width_deduction": _MAXLIGHT_CLEAR_W,
              "net_clear_height_deduction": _MAXLIGHT_CLEAR_H} if egress else {})
    note = (" R310 escape: turn-sash clear opening ESTIMATED (unit - 154 mm W, - 100 mm H); "
            "fabricator's written figure pending (notes/egress_window_review.md)."
            if egress else "")
    return WindowType(
        tag=tag, width=width, height=height, operation="tilt_turn", tempered=tempered,
        u_factor=u_us(0.20), shgc=0.40, vt=0.58, frame_depth=_MAXLIGHT_DEPTH,
        frame_face_width=_MAXLIGHT_FACE, sash_face_width=_MAXLIGHT_FACE,
        frame_sill_face_width=_MAXLIGHT_FACE + _MAXLIGHT_SILL_ADAPTOR,
        frame_material_ref="aliplast-maxlight-powder", **clear,
        product_ref=ALIPLAST_MAXLIGHT_TT.tag, source=f"{_MAXLIGHT}{note} {_SIZE}")


def _tt(tag, width, height, *, tempered=False) -> WindowType:
    return _drutex(tag, width, height, "tilt_turn", _TT, DRUTEX_ALUCOVER_TT,
                   tempered=tempered)


def _fix(tag, width, height, *, tempered=False) -> WindowType:
    return _drutex(tag, width, height, "fixed", _FIX, DRUTEX_ALUCOVER_FIX, tempered=tempered,
                   u=0.15, shgc=0.39, vt=0.57)


def _hp(tag, width, height) -> WindowType:
    return _drutex(tag, width, height, "fixed", _FIX_HP, DRUTEX_ALUCOVER_FIX,
                   u=0.14, shgc=0.39, vt=0.56)


# The nine R310 escape units take the full 27 1/2" between jacks (preferences.toml's bearing
# rung); WT-3048 is the nonbearing 30" (notes/egress_window_review.md).
WINDOW_TYPES = (
    _maxlight("WT-1424-TT", inch(14), ft(2)),  # kitchen pair
    _maxlight("WT-1424-TT-T", inch(14), ft(2), tempered=True),  # WIN-M-BATH1-W
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
    _maxlight("WT-2748", inch(27.5), ft(4), egress=True),
    _maxlight("WT-2748-T", inch(27.5), ft(4), tempered=True, egress=True),
    _maxlight("WT-2754", inch(27.5), ft(4, 6), egress=True),
    _maxlight("WT-3048", inch(30), ft(4), egress=True),
)

HOUSE_WINDOW_TAGS = frozenset(t.tag for t in WINDOW_TYPES)
